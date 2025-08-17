"""
Base de données SQLite simple pour l'API minimale
Persistance des données scrapées sans la complexité d'Alembic
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from contextlib import contextmanager

from services.scraping_service import JobData

# Support optionnel MySQL
try:
    import pymysql
except Exception:  # pymysql non installé ou indisponible
    pymysql = None


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


class MySQLJobDB:
    """Implémentation MySQL légère avec PyMySQL.
    Utilise des colonnes TEXT pour rester compatible avec SQLite (keywords JSON sérialisé).
    """

    def __init__(self, url: str):
        # url: mysql://user:pass@host:port/db
        self.cfg = self._parse_mysql_url(url)
        self.init_database()

    def _parse_mysql_url(self, url: str):
        assert url.startswith("mysql://"), "URL MySQL invalide"
        body = url[len("mysql://"):]
        creds, hostdb = body.split("@", 1)
        user, password = creds.split(":", 1)
        if "/" not in hostdb:
            raise ValueError("URL MySQL sans base de données")
        hostport, database = hostdb.split("/", 1)
        if ":" in hostport:
            host, port = hostport.split(":", 1)
            port = int(port)
        else:
            host, port = hostport, 3306
        return {
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "database": database,
            "charset": "utf8mb4",
        }

    def get_connection(self):
        conn = pymysql.connect(
            host=self.cfg["host"],
            port=self.cfg["port"],
            user=self.cfg["user"],
            password=self.cfg["password"],
            database=self.cfg["database"],
            charset=self.cfg["charset"],
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn

    def init_database(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Tables
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description LONGTEXT,
                    url TEXT,
                    salary TEXT,
                    keywords TEXT,
                    source VARCHAR(64) NOT NULL,
                    scraped_at VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scraping_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    query TEXT NOT NULL,
                    location TEXT,
                    jobs_found INT DEFAULT 0,
                    sources TEXT,
                    scraped_at VARCHAR(64) NOT NULL,
                    execution_time DOUBLE DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            # Index (ignorer erreurs si existent déjà)
            try:
                cur.execute("CREATE INDEX idx_jobs_source ON jobs(source)")
            except Exception:
                pass
            try:
                cur.execute("CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at)")
            except Exception:
                pass
            try:
                cur.execute("CREATE INDEX idx_jobs_company ON jobs(company)")
            except Exception:
                pass
            conn.commit()

    # Méthodes similaires à SQLite mais avec placeholders %s
    def save_job(self, job: JobData) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO jobs (title, company, location, description, url, salary, keywords, source, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    job.salary,
                    json.dumps(job.keywords),
                    job.source,
                    job.scraped_at,
                ),
            )
            conn.commit()
            return cur.lastrowid

    def save_jobs_batch(self, jobs: List[JobData]) -> List[int]:
        ids = []
        with self.get_connection() as conn:
            cur = conn.cursor()
            for job in jobs:
                cur.execute(
                    """
                    INSERT INTO jobs (title, company, location, description, url, salary, keywords, source, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job.title,
                        job.company,
                        job.location,
                        job.description,
                        job.url,
                        job.salary,
                        json.dumps(job.keywords),
                        job.source,
                        job.scraped_at,
                    ),
                )
                ids.append(cur.lastrowid)
            conn.commit()
        return ids

    def get_jobs(self, limit: int = 50, offset: int = 0, source: Optional[str] = None) -> List[Dict]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            q = "SELECT * FROM jobs"
            params: List = []
            if source:
                q += " WHERE source = %s"
                params.append(source)
            q += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cur.execute(q, params)
            rows = cur.fetchall()
            for r in rows:
                r["keywords"] = json.loads(r["keywords"]) if r.get("keywords") else []
            return rows

    def search_jobs(self, query: str, location: Optional[str] = None, limit: int = 20) -> List[Dict]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            q = "SELECT * FROM jobs WHERE (title LIKE %s OR description LIKE %s OR keywords LIKE %s)"
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
            if location:
                q += " AND location LIKE %s"
                params.append(f"%{location}%")
            q += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            rows = cur.fetchall()
            for r in rows:
                r["keywords"] = json.loads(r["keywords"]) if r.get("keywords") else []
            return rows

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            r = cur.fetchone()
            if not r:
                return None
            r["keywords"] = json.loads(r["keywords"]) if r.get("keywords") else []
            return r

    def get_stats(self) -> Dict:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM jobs")
            total_jobs = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(DISTINCT source) AS sources FROM jobs")
            total_sources = cur.fetchone()["sources"]
            cur.execute("SELECT COUNT(DISTINCT company) AS companies FROM jobs")
            total_companies = cur.fetchone()["companies"]
            cur.execute(
                "SELECT company, COUNT(*) AS count FROM jobs GROUP BY company ORDER BY count DESC LIMIT 5"
            )
            top_companies = cur.fetchall()
            cur.execute(
                "SELECT source, COUNT(*) AS count FROM jobs GROUP BY source ORDER BY count DESC"
            )
            sources_stats = cur.fetchall()
            cur.execute("SELECT keywords FROM jobs WHERE keywords IS NOT NULL")
            all_keywords = []
            for row in cur.fetchall():
                try:
                    all_keywords.extend(json.loads(row["keywords"]))
                except Exception:
                    continue
            counts = {}
            for k in all_keywords:
                counts[k] = counts.get(k, 0) + 1
            top_keywords = [{"keyword": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]]
            return {
                "total_jobs": total_jobs,
                "total_sources": total_sources,
                "total_companies": total_companies,
                "top_companies": top_companies,
                "sources_stats": sources_stats,
                "top_keywords": top_keywords,
            }

    def save_scraping_session(self, query: str, location: str, jobs_found: int, sources: List[str], execution_time: float = 0.0):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO scraping_stats (query, location, jobs_found, sources, scraped_at, execution_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    query,
                    location,
                    jobs_found,
                    json.dumps(sources),
                    datetime.now().isoformat(),
                    execution_time,
                ),
            )
            conn.commit()

    def clear_old_data(self, days: int = 30):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM jobs WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
                (days,),
            )
            cur.execute(
                "DELETE FROM scraping_stats WHERE scraped_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
                (days,),
            )
            conn.commit()


# Choix dynamique de la DB
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("mysql://") and pymysql is not None:
    job_db = MySQLJobDB(DATABASE_URL)
else:
    # Fallback: SQLite
    job_db = SimpleJobDB()