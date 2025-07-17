"""
Modèle pour les tâches de scraping
"""

from sqlalchemy import Column, BigInteger, String, Integer, Text, TIMESTAMP, Index, Enum
from sqlalchemy.sql import func
from .database import Base
import enum


class JobStatus(str, enum.Enum):
    """États d'une tâche de scraping"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScrapingJob(Base):
    """
    Modèle pour une tâche de scraping
    """
    __tablename__ = "scraping_jobs"

    # Clé primaire
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identifiant unique dans Redis/RQ
    job_id = Column(String(100), nullable=False, unique=True, comment="ID unique du job dans Redis")
    
    # Paramètres du scraping
    source = Column(String(100), nullable=False, comment="Source à scraper (indeed, linkedin, etc.)")
    search_query = Column(String(255), nullable=True, comment="Requête de recherche")
    location = Column(String(255), nullable=True, comment="Localisation de recherche")
    max_pages = Column(Integer, default=1, comment="Nombre maximum de pages à scraper")
    
    # État et progression
    status = Column(
        Enum(JobStatus), 
        default=JobStatus.PENDING,
        comment="État actuel du job"
    )
    progress = Column(Integer, default=0, comment="Pourcentage de completion (0-100)")
    total_offers_found = Column(Integer, default=0, comment="Nombre total d'offres trouvées")
    offers_processed = Column(Integer, default=0, comment="Nombre d'offres traitées")
    error_message = Column(Text, nullable=True, comment="Message d'erreur en cas d'échec")
    
    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True, comment="Date de début d'exécution")
    completed_at = Column(TIMESTAMP, nullable=True, comment="Date de fin d'exécution")
    created_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        comment="Date de création"
    )
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Date de dernière modification"
    )
    
    # Index
    __table_args__ = (
        Index('idx_job_id', 'job_id'),
        Index('idx_status', 'status'),
        Index('idx_source', 'source'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingJob(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"
    
    @property
    def duration(self) -> int | None:
        """Durée d'exécution en secondes"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'source': self.source,
            'search_query': self.search_query,
            'location': self.location,
            'max_pages': self.max_pages,
            'status': self.status.value if self.status else None,
            'progress': self.progress,
            'total_offers_found': self.total_offers_found,
            'offers_processed': self.offers_processed,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'duration': self.duration,
        } 