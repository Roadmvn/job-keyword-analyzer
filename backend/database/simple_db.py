"""
Base de données SQLite simple pour l'API minimale
Persistance des données scrapées sans la complexité d'Alembic
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from contextlib import contextmanager

from services.scraping_service import JobData


class SimpleJobDB:
    """Base de données SQLite simple pour les offres d'emploi"""
    
    def __init__(self, db_path: str = "jobs_simple.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialiser la base de données avec les tables nécessaires"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des offres d'emploi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    salary TEXT,
                    keywords TEXT,  -- JSON array
                    source TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des statistiques de scraping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    location TEXT,
                    jobs_found INTEGER DEFAULT 0,
                    sources TEXT,  -- JSON array
                    scraped_at TEXT NOT NULL,
                    execution_time REAL DEFAULT 0.0
                )
            """)
            
            # Index pour performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager pour la connexion SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        try:
            yield conn
        finally:
            conn.close()
    
    def save_job(self, job: JobData) -> int:
        """Sauvegarder une offre d'emploi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO jobs (title, company, location, description, url, salary, keywords, source, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.title,
                job.company,
                job.location,
                job.description,
                job.url,
                job.salary,
                json.dumps(job.keywords),
                job.source,
                job.scraped_at
            ))
            
            job_id = cursor.lastrowid
            conn.commit()
            return job_id
    
    def save_jobs_batch(self, jobs: List[JobData]) -> List[int]:
        """Sauvegarder plusieurs offres d'emploi en batch"""
        job_ids = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for job in jobs:
                cursor.execute("""
                    INSERT INTO jobs (title, company, location, description, url, salary, keywords, source, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    job.salary,
                    json.dumps(job.keywords),
                    job.source,
                    job.scraped_at
                ))
                job_ids.append(cursor.lastrowid)
            
            conn.commit()
        
        return job_ids
    
    def get_jobs(self, limit: int = 50, offset: int = 0, source: Optional[str] = None) -> List[Dict]:
        """Récupérer les offres d'emploi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM jobs"
            params = []
            
            if source:
                query += " WHERE source = ?"
                params.append(source)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                job = dict(row)
                job['keywords'] = json.loads(job['keywords']) if job['keywords'] else []
                jobs.append(job)
            
            return jobs
    
    def search_jobs(self, query: str, location: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Rechercher des offres d'emploi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            sql_query = """
                SELECT * FROM jobs 
                WHERE (title LIKE ? OR description LIKE ? OR keywords LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
            
            if location:
                sql_query += " AND location LIKE ?"
                params.append(f"%{location}%")
            
            sql_query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                job = dict(row)
                job['keywords'] = json.loads(job['keywords']) if job['keywords'] else []
                jobs.append(job)
            
            return jobs
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Récupérer une offre d'emploi par ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            
            if row:
                job = dict(row)
                job['keywords'] = json.loads(job['keywords']) if job['keywords'] else []
                return job
            
            return None
    
    def get_stats(self) -> Dict:
        """Récupérer les statistiques globales"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) as total FROM jobs")
            total_jobs = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(DISTINCT source) as sources FROM jobs")
            total_sources = cursor.fetchone()['sources']
            
            cursor.execute("SELECT COUNT(DISTINCT company) as companies FROM jobs")
            total_companies = cursor.fetchone()['companies']
            
            # Top entreprises
            cursor.execute("""
                SELECT company, COUNT(*) as count 
                FROM jobs 
                GROUP BY company 
                ORDER BY count DESC 
                LIMIT 5
            """)
            top_companies = [dict(row) for row in cursor.fetchall()]
            
            # Top sources
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM jobs 
                GROUP BY source 
                ORDER BY count DESC
            """)
            sources_stats = [dict(row) for row in cursor.fetchall()]
            
            # Top mots-clés (approximatif)
            cursor.execute("SELECT keywords FROM jobs WHERE keywords IS NOT NULL")
            all_keywords = []
            for row in cursor.fetchall():
                try:
                    keywords = json.loads(row['keywords'])
                    all_keywords.extend(keywords)
                except:
                    continue
            
            # Compter les mots-clés
            keyword_count = {}
            for keyword in all_keywords:
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
            
            top_keywords = [
                {"keyword": k, "count": v} 
                for k, v in sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            return {
                "total_jobs": total_jobs,
                "total_sources": total_sources,
                "total_companies": total_companies,
                "top_companies": top_companies,
                "sources_stats": sources_stats,
                "top_keywords": top_keywords
            }
    
    def save_scraping_session(self, query: str, location: str, jobs_found: int, sources: List[str], execution_time: float = 0.0):
        """Sauvegarder une session de scraping"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraping_stats (query, location, jobs_found, sources, scraped_at, execution_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query,
                location,
                jobs_found,
                json.dumps(sources),
                datetime.now().isoformat(),
                execution_time
            ))
            
            conn.commit()
    
    def clear_old_data(self, days: int = 30):
        """Nettoyer les anciennes données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Supprimer les jobs anciens
            cursor.execute("""
                DELETE FROM jobs 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            # Supprimer les stats anciennes
            cursor.execute("""
                DELETE FROM scraping_stats 
                WHERE scraped_at < datetime('now', '-{} days')
            """.format(days))
            
            conn.commit()


# Instance globale
job_db = SimpleJobDB()