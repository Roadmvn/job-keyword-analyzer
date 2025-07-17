"""
Application FastAPI principale - Job Keywords Analyzer
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
import os

# Imports locaux
from models.database import get_db, init_db
from models.job_offer import JobOffer
from models.keyword import Keyword
from models.scraping_job import ScrapingJob
from models.job_offer_keyword import JobOfferKeyword
from services.nlp_analyzer import nlp_analyzer
from services.search_service import search_service

# Configuration
app = FastAPI(
    title="Job Keywords Analyzer API",
    description="API pour analyser les mots-clés des offres d'emploi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    try:
        init_db()
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"❌ Erreur d'initialisation DB: {e}")

# ===================================
# ENDPOINTS DE BASE
# ===================================

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🚀 Job Keywords Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "service": "job-keywords-analyzer-api",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("DEBUG", "development")
    }

# ===================================
# ENDPOINTS DES OFFRES D'EMPLOI
# ===================================

@app.get("/api/jobs", response_model=List[Dict[str, Any]])
async def get_jobs(
    skip: int = 0,
    limit: int = 10,
    company: str = None,
    location: str = None,
    db: Session = Depends(get_db)
):
    """Récupérer les offres d'emploi avec filtres optionnels"""
    query = db.query(JobOffer)
    
    if company:
        query = query.filter(JobOffer.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobOffer.location.ilike(f"%{location}%"))
    
    jobs = query.offset(skip).limit(limit).all()
    return [job.to_dict() for job in jobs]

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Récupérer une offre d'emploi spécifique"""
    job = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    return job.to_dict()

@app.post("/api/jobs")
async def create_job(job_data: dict, db: Session = Depends(get_db)):
    """Créer une nouvelle offre d'emploi (pour tests)"""
    try:
        job = JobOffer(
            title=job_data.get("title", "Titre test"),
            company=job_data.get("company", "Entreprise test"),
            location=job_data.get("location", "Paris"),
            description=job_data.get("description", "Description test"),
            source=job_data.get("source", "manual"),
            source_id=f"manual_{datetime.now().timestamp()}"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return {"message": "Offre créée", "job": job.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS DES MOTS-CLÉS
# ===================================

@app.get("/api/keywords")
async def get_keywords(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Récupérer les mots-clés les plus fréquents"""
    query = db.query(Keyword).order_by(Keyword.frequency.desc())
    
    if category:
        query = query.filter(Keyword.category == category.upper())
    
    keywords = query.offset(skip).limit(limit).all()
    return [keyword.to_dict() for keyword in keywords]

@app.post("/api/keywords")
async def create_keyword(keyword_data: dict, db: Session = Depends(get_db)):
    """Créer un nouveau mot-clé (pour tests)"""
    try:
        keyword = Keyword(
            keyword=keyword_data.get("keyword"),
            category=keyword_data.get("category", "OTHER"),
            frequency=keyword_data.get("frequency", 1)
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        return {"message": "Mot-clé créé", "keyword": keyword.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS DE STATISTIQUES
# ===================================

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Statistiques générales"""
    try:
        total_jobs = db.query(JobOffer).count()
        total_keywords = db.query(Keyword).count()
        total_companies = db.query(JobOffer.company).distinct().count()
        
        # Top 5 entreprises
        top_companies = db.query(
            JobOffer.company,
            db.func.count(JobOffer.id).label('count')
        ).group_by(JobOffer.company).order_by(
            db.func.count(JobOffer.id).desc()
        ).limit(5).all()
        
        # Top 5 mots-clés
        top_keywords = db.query(Keyword).order_by(
            Keyword.frequency.desc()
        ).limit(5).all()
        
        return {
            "total_jobs": total_jobs,
            "total_keywords": total_keywords,
            "total_companies": total_companies,
            "top_companies": [{"name": comp, "count": count} for comp, count in top_companies],
            "top_keywords": [kw.to_dict() for kw in top_keywords],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_jobs": 0,
            "total_keywords": 0,
            "total_companies": 0,
            "top_companies": [],
            "top_keywords": []
        }

# ===================================
# ENDPOINTS DE SCRAPING
# ===================================

@app.get("/api/scraping/jobs")
async def get_scraping_jobs(db: Session = Depends(get_db)):
    """Liste des tâches de scraping"""
    jobs = db.query(ScrapingJob).order_by(ScrapingJob.created_at.desc()).limit(10).all()
    return [job.to_dict() for job in jobs]

@app.post("/api/scraping/start")
async def start_scraping(scraping_data: dict):
    """Démarrer une tâche de scraping (simulation)"""
    # Pour l'instant, on simule juste
    return {
        "message": "Scraping démarré (simulation)",
        "job_id": f"job_{datetime.now().timestamp()}",
        "source": scraping_data.get("source", "indeed"),
        "query": scraping_data.get("query", "python"),
        "status": "pending"
    }

# ===================================
# ENDPOINT DE TEST
# ===================================

@app.post("/api/test/populate")
async def populate_test_data(db: Session = Depends(get_db)):
    """Ajouter des données de test"""
    try:
        # Ajouter quelques offres de test
        test_jobs = [
            {
                "title": "Développeur Python Senior",
                "company": "TechCorp",
                "location": "Paris",
                "description": "Développement d'applications Python avec Django et FastAPI",
                "source": "test",
                "source_id": "test_1"
            },
            {
                "title": "Data Scientist",
                "company": "DataLab",
                "location": "Lyon",
                "description": "Analyse de données avec Python, pandas, scikit-learn",
                "source": "test",
                "source_id": "test_2"
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudTech",
                "location": "Marseille",
                "description": "Infrastructure cloud AWS, Docker, Kubernetes",
                "source": "test",
                "source_id": "test_3"
            }
        ]
        
        # Ajouter quelques mots-clés
        test_keywords = [
            {"keyword": "Python", "category": "LANGUAGE", "frequency": 10},
            {"keyword": "Django", "category": "FRAMEWORK", "frequency": 5},
            {"keyword": "FastAPI", "category": "FRAMEWORK", "frequency": 3},
            {"keyword": "Docker", "category": "TOOL", "frequency": 8},
            {"keyword": "AWS", "category": "TOOL", "frequency": 6}
        ]
        
        # Insérer les données
        for job_data in test_jobs:
            job = JobOffer(**job_data)
            db.add(job)
        
        for kw_data in test_keywords:
            keyword = Keyword(**kw_data)
            db.add(keyword)
        
        db.commit()
        
        return {
            "message": "✅ Données de test ajoutées",
            "jobs_added": len(test_jobs),
            "keywords_added": len(test_keywords)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS DE RECHERCHE INTELLIGENTE
# ===================================

@app.get("/api/search")
async def smart_search(
    q: str = "",
    location: str = None,
    company: str = None,
    contract_type: str = None,
    experience_level: str = None,
    remote_work: bool = None,
    salary_min: float = None,
    salary_max: float = None,
    limit: int = 10,
    offset: int = 0
):
    """Recherche intelligente avec correction d'erreurs de frappe"""
    try:
        # Construire les filtres
        filters = {}
        if location:
            filters["location"] = location
        if company:
            filters["company"] = company
        if contract_type:
            filters["contract_type"] = contract_type
        if experience_level:
            filters["experience_level"] = experience_level
        if remote_work is not None:
            filters["remote_work"] = remote_work
        if salary_min:
            filters["salary_min"] = salary_min
        if salary_max:
            filters["salary_max"] = salary_max
        
        # Exécuter la recherche
        results = search_service.smart_search(
            query=q,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de recherche: {str(e)}")

@app.get("/api/search/suggestions")
async def get_search_suggestions(q: str):
    """Obtenir des suggestions de recherche"""
    try:
        suggestions = search_service.autocomplete(q)
        return {"query": q, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur suggestions: {str(e)}")

@app.get("/api/search/popular")
async def get_popular_searches():
    """Obtenir les recherches populaires"""
    try:
        popular = search_service.get_popular_searches()
        return popular
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS D'ANALYSE NLP
# ===================================

@app.post("/api/analyze/job/{job_id}")
async def analyze_job(job_id: int, db: Session = Depends(get_db)):
    """Analyser les mots-clés d'une offre d'emploi spécifique"""
    try:
        # Récupérer l'offre
        job = db.query(JobOffer).filter(JobOffer.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
        
        # Analyser avec NLP
        analysis = nlp_analyzer.analyze_job_requirements(
            description=job.description or "",
            requirements=job.requirements or ""
        )
        
        # Sauvegarder les mots-clés extraits
        for keyword_data in analysis['keywords']:
            # Vérifier si le mot-clé existe déjà
            keyword = db.query(Keyword).filter(
                Keyword.keyword == keyword_data['keyword']
            ).first()
            
            if not keyword:
                # Créer nouveau mot-clé
                keyword = Keyword(
                    keyword=keyword_data['keyword'],
                    category=keyword_data['category'],
                    confidence=keyword_data['confidence'],
                    frequency=1
                )
                db.add(keyword)
                db.flush()  # Pour obtenir l'ID
            else:
                # Mettre à jour la fréquence
                keyword.frequency += 1
                keyword.confidence = max(keyword.confidence, keyword_data['confidence'])
            
            # Créer la liaison offre-mot-clé
            job_keyword = db.query(JobOfferKeyword).filter(
                JobOfferKeyword.job_offer_id == job_id,
                JobOfferKeyword.keyword_id == keyword.id
            ).first()
            
            if not job_keyword:
                job_keyword = JobOfferKeyword(
                    job_offer_id=job_id,
                    keyword_id=keyword.id,
                    relevance_score=keyword_data['confidence'],
                    extraction_method="NLP"
                )
                db.add(job_keyword)
        
        db.commit()
        
        # Indexer dans Elasticsearch
        job_data = job.to_dict()
        job_data['keywords'] = [kw['keyword'] for kw in analysis['keywords']]
        search_service.index_job(job_data)
        
        return {
            "job_id": job_id,
            "analysis": analysis,
            "message": "✅ Analyse terminée et mots-clés sauvegardés"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur d'analyse: {str(e)}")

@app.post("/api/analyze/text")
async def analyze_text(data: dict):
    """Analyser un texte libre (pour tester l'extraction de mots-clés)"""
    try:
        text = data.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Texte requis")
        
        # Extraire les mots-clés
        keywords = nlp_analyzer.extract_keywords(text)
        
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "keywords": [
                {
                    "keyword": kw.keyword,
                    "category": kw.category,
                    "confidence": kw.confidence,
                    "frequency": kw.frequency
                }
                for kw in keywords
            ],
            "total_keywords": len(keywords)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS DE SUGGESTIONS CV
# ===================================

@app.post("/api/cv/suggestions")
async def get_cv_suggestions(data: dict, db: Session = Depends(get_db)):
    """Obtenir des suggestions d'amélioration de CV"""
    try:
        user_skills = data.get("skills", [])
        if not user_skills:
            raise HTTPException(status_code=400, detail="Liste de compétences requise")
        
        # Récupérer les mots-clés populaires du marché
        market_keywords = db.query(Keyword).order_by(
            Keyword.frequency.desc()
        ).limit(50).all()
        
        # Convertir en format pour l'analyseur
        market_kw_objects = []
        for kw in market_keywords:
            market_kw_objects.append(type('KeywordResult', (), {
                'keyword': kw.keyword,
                'category': kw.category.value if kw.category else 'OTHER',
                'frequency': kw.frequency,
                'confidence': float(kw.confidence) if kw.confidence else 0.0
            })())
        
        # Générer les suggestions
        suggestions = nlp_analyzer.suggest_cv_improvements(
            user_skills=user_skills,
            market_keywords=market_kw_objects
        )
        
        return {
            "user_skills": user_skills,
            "suggestions": suggestions,
            "market_analysis": {
                "total_market_keywords": len(market_keywords),
                "user_coverage": f"{suggestions['total_coverage']:.1f}%"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

@app.get("/api/trends/keywords")
async def get_keyword_trends(
    category: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Obtenir les tendances des mots-clés par catégorie"""
    try:
        query = db.query(Keyword).order_by(Keyword.frequency.desc())
        
        if category:
            query = query.filter(Keyword.category == category.upper())
        
        keywords = query.limit(limit).all()
        
        return {
            "category": category or "ALL",
            "trends": [
                {
                    "keyword": kw.keyword,
                    "category": kw.category.value if kw.category else None,
                    "frequency": kw.frequency,
                    "confidence": float(kw.confidence) if kw.confidence else None
                }
                for kw in keywords
            ],
            "total": len(keywords)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

# ===================================
# ENDPOINTS DE CORRESPONDANCE
# ===================================

@app.post("/api/match/job")
async def match_job_skills(data: dict, db: Session = Depends(get_db)):
    """Calculer la correspondance entre les compétences utilisateur et une offre"""
    try:
        job_id = data.get("job_id")
        user_skills = data.get("skills", [])
        
        if not job_id or not user_skills:
            raise HTTPException(status_code=400, detail="job_id et skills requis")
        
        # Récupérer l'offre et ses mots-clés
        job = db.query(JobOffer).filter(JobOffer.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Récupérer les mots-clés de l'offre
        job_keywords = db.query(
            Keyword.keyword,
            JobOfferKeyword.relevance_score,
            Keyword.category
        ).join(JobOfferKeyword).filter(
            JobOfferKeyword.job_offer_id == job_id
        ).all()
        
        # Calculer les correspondances
        user_skills_lower = [skill.lower() for skill in user_skills]
        matching_skills = []
        missing_skills = []
        
        for kw, relevance, category in job_keywords:
            if kw.lower() in user_skills_lower:
                matching_skills.append({
                    "skill": kw,
                    "category": category.value if category else None,
                    "relevance": float(relevance) if relevance else 0.0
                })
            else:
                missing_skills.append({
                    "skill": kw,
                    "category": category.value if category else None,
                    "relevance": float(relevance) if relevance else 0.0,
                    "priority": "HIGH" if (relevance and float(relevance) > 0.8) else "MEDIUM"
                })
        
        # Calculer le score de correspondance
        total_relevance = sum(float(rel) for _, rel, _ in job_keywords)
        matching_relevance = sum(skill["relevance"] for skill in matching_skills)
        match_score = (matching_relevance / total_relevance * 100) if total_relevance > 0 else 0
        
        return {
            "job": {
                "id": job.id,
                "title": job.title,
                "company": job.company
            },
            "match_score": round(match_score, 1),
            "matching_skills": matching_skills,
            "missing_skills": missing_skills[:10],  # Top 10 missing
            "total_job_requirements": len(job_keywords),
            "skills_matched": len(matching_skills),
            "recommendation": "Excellent match!" if match_score >= 80 else "Good match" if match_score >= 60 else "Needs improvement"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 