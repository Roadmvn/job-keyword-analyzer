"""
Service de recherche simplifié
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.job_offer import JobOffer
from models.keyword import Keyword

class SearchService:
    """Service de recherche d'offres d'emploi"""
    
    def search_jobs(
        self, 
        db: Session, 
        query: str = None, 
        location: str = None,
        limit: int = 20
    ) -> List[JobOffer]:
        """Rechercher des offres d'emploi"""
        
        query_obj = db.query(JobOffer)
        
        if query:
            query_obj = query_obj.filter(
                JobOffer.title.contains(query) | 
                JobOffer.description.contains(query)
            )
        
        if location:
            query_obj = query_obj.filter(JobOffer.location.contains(location))
        
        return query_obj.limit(limit).all()
    
    def search_keywords(
        self, 
        db: Session, 
        query: str = None,
        limit: int = 20
    ) -> List[Keyword]:
        """Rechercher des mots-clés"""
        
        query_obj = db.query(Keyword)
        
        if query:
            query_obj = query_obj.filter(Keyword.name.contains(query))
        
        return query_obj.order_by(Keyword.frequency.desc()).limit(limit).all()

# Instance globale
search_service = SearchService()