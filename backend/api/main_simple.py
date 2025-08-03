"""
Version simplifiée de l'API sans authentification
Pour test rapide de l'application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sys
import os

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scraping_service import ScrapingService, JobData, scraping_service
from database.simple_db import job_db

# Configuration simple
app = FastAPI(
    title="Job Keywords Analyzer - Version Simple",
    description="API simplifiée pour test rapide",
    version="1.0.0-simple"
)

# CORS pour le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic simples
class JobOffer(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    description: str
    keywords: List[str] = []
    source: str = "test"

class SearchRequest(BaseModel):
    query: str
    location: Optional[str] = None

# Données de test
SAMPLE_JOBS = [
    JobOffer(
        id=1,
        title="Développeur Python Senior",
        company="TechCorp",
        location="Paris",
        description="Recherche développeur Python expérimenté avec FastAPI, Django, PostgreSQL",
        keywords=["python", "fastapi", "django", "postgresql", "senior"],
        source="test"
    ),
    JobOffer(
        id=2,
        title="Data Scientist",
        company="DataLab",
        location="Lyon",
        description="Poste de Data Scientist avec expertise en Machine Learning, Python, Pandas",
        keywords=["python", "data science", "machine learning", "pandas", "sql"],
        source="test"
    ),
    JobOffer(
        id=3,
        title="Frontend Developer React",
        company="WebStudio",
        location="Remote",
        description="Développeur React.js avec TypeScript, Redux, CSS3",
        keywords=["react", "typescript", "redux", "css3", "frontend"],
        source="test"
    )
]

# Endpoints API
@app.get("/")
async def root():
    return {
        "message": "Job Keywords Analyzer - API Simple",
        "status": "✅ Fonctionnel",
        "version": "1.0.0-simple",
        "endpoints": {
            "jobs": "/api/jobs",
            "search": "/api/search",
            "stats": "/api/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "job-analyzer-simple"}



@app.get("/api/jobs/{job_id}", response_model=JobOffer)
async def get_job(job_id: int):
    """Récupérer une offre d'emploi spécifique"""
    for job in SAMPLE_JOBS:
        if job.id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")

@app.post("/api/search", response_model=List[JobOffer])
async def search_jobs(search_req: SearchRequest):
    """Rechercher des offres d'emploi"""
    query = search_req.query.lower()
    location = search_req.location.lower() if search_req.location else None
    
    results = []
    for job in SAMPLE_JOBS:
        # Recherche dans le titre, description et mots-clés
        if (query in job.title.lower() or 
            query in job.description.lower() or 
            any(query in keyword for keyword in job.keywords)):
            
            # Filtre par localisation si spécifié
            if location is None or (job.location and location in job.location.lower()):
                results.append(job)
    
    return results

@app.get("/api/stats")
async def get_stats():
    """Statistiques complètes avec base de données"""
    # Stats de la base de données
    db_stats = job_db.get_stats()
    
    # Ajouter les jobs de test
    sample_count = len(SAMPLE_JOBS)
    
    return {
        "total_jobs": db_stats["total_jobs"] + sample_count,
        "db_jobs": db_stats["total_jobs"],
        "sample_jobs": sample_count,
        "total_sources": db_stats["total_sources"],
        "total_companies": db_stats["total_companies"],
        "top_companies": db_stats["top_companies"],
        "sources_stats": db_stats["sources_stats"],
        "top_keywords": db_stats["top_keywords"]
    }

@app.get("/api/keywords")
async def get_top_keywords(limit: int = 10):
    """Top mots-clés - Format compatible frontend"""
    all_keywords = []
    
    # Mélanger données statiques et scrapées
    for job in SAMPLE_JOBS:
        all_keywords.extend(job.keywords)
    
    for job in scraping_service.get_cached_jobs():
        all_keywords.extend(job.keywords)
    
    # Compter les occurrences
    keyword_count = {}
    for keyword in all_keywords:
        keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
    
    # Trier par popularité
    sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
    
    # Format compatible frontend
    return [
        {
            "id": i + 1,
            "keyword": k, 
            "frequency": v,  # Frontend attend 'frequency'
            "category": "tech"  # Frontend attend 'category'
        } 
        for i, (k, v) in enumerate(sorted_keywords[:limit])
    ]

# ===================================
# ENDPOINTS DE SCRAPING
# ===================================

@app.post("/api/scrape")
async def start_scraping(query: str = "développeur", location: str = "France"):
    """Démarrer le scraping des offres d'emploi"""
    try:
        import time
        start_time = time.time()
        
        # Scraper les données
        jobs = await scraping_service.scrape_all_sources(query, location)
        
        # Sauvegarder en base de données
        if jobs:
            job_db.save_jobs_batch(jobs)
        
        # Statistiques de la session
        execution_time = time.time() - start_time
        sources = list(set(job.source for job in jobs))
        job_db.save_scraping_session(query, location, len(jobs), sources, execution_time)
        
        return {
            "message": "Scraping terminé avec succès",
            "jobs_found": len(jobs),
            "sources": sources,
            "query": query,
            "location": location,
            "execution_time": round(execution_time, 2),
            "saved_to_db": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de scraping: {str(e)}")

@app.get("/api/scraped-jobs", response_model=List[JobData])
async def get_scraped_jobs():
    """Récupérer les offres d'emploi scrapées"""
    return scraping_service.get_cached_jobs()

@app.get("/api/scraping/stats")
async def get_scraping_stats():
    """Statistiques de scraping"""
    return scraping_service.get_scraping_stats()

# ===================================
# ENDPOINTS BASE DE DONNÉES
# ===================================

@app.get("/api/db/jobs")
async def get_db_jobs(limit: int = 20, offset: int = 0, source: Optional[str] = None):
    """Récupérer les offres d'emploi depuis la base de données"""
    return job_db.get_jobs(limit=limit, offset=offset, source=source)

@app.get("/api/db/jobs/{job_id}")
async def get_db_job(job_id: int):
    """Récupérer une offre d'emploi spécifique depuis la base de données"""
    job = job_db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    return job

@app.post("/api/db/search")
async def search_db_jobs(search_req: SearchRequest):
    """Rechercher dans la base de données"""
    return job_db.search_jobs(search_req.query, search_req.location)

# ===================================
# ENDPOINTS COMPATIBILITÉ FRONTEND
# ===================================

@app.post("/api/test/populate")
async def populate_test_data():
    """Endpoint pour compatibilité frontend - Lance un scraping"""
    try:
        # Lancer un scraping automatique
        jobs = await scraping_service.scrape_all_sources("développeur", "France")
        
        # Sauvegarder en base
        if jobs:
            job_db.save_jobs_batch(jobs)
        
        return {
            "message": "Données de test ajoutées avec succès",
            "jobs_added": len(jobs),
            "sources": list(set(job.source for job in jobs))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/jobs")
async def get_jobs_compatible(limit: int = 10):
    """Jobs compatibles frontend - Mélange test + DB"""
    
    # Récupérer jobs de la DB
    db_jobs = job_db.get_jobs(limit=limit//2)
    
    # Convertir au format JobOffer
    all_jobs = []
    
    # Ajouter jobs de test
    for job in SAMPLE_JOBS[:limit//2]:
        all_jobs.append(job)
    
    # Ajouter jobs de la DB convertis
    for i, db_job in enumerate(db_jobs):
        job_offer = JobOffer(
            id=len(SAMPLE_JOBS) + i + 1,
            title=db_job["title"],
            company=db_job["company"],
            location=db_job["location"],
            description=db_job["description"],
            keywords=db_job["keywords"],
            source=db_job["source"]
        )
        all_jobs.append(job_offer)
    
    return all_jobs[:limit]

@app.get("/api/jobs/combined", response_model=List[JobOffer])
async def get_combined_jobs(limit: int = 20):
    """Récupérer les offres d'emploi combinées (test + scrapées)"""
    
    # Convertir les jobs scrapés au format JobOffer
    scraped_jobs = []
    for i, job in enumerate(scraping_service.get_cached_jobs()[:limit//2], len(SAMPLE_JOBS) + 1):
        scraped_job = JobOffer(
            id=i,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            keywords=job.keywords,
            source=job.source
        )
        scraped_jobs.append(scraped_job)
    
    # Combiner avec les données de test
    combined = SAMPLE_JOBS[:limit//2] + scraped_jobs
    return combined[:limit]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)