"""
Modèle de liaison entre offres d'emploi et mots-clés
"""

from sqlalchemy import Column, BigInteger, DECIMAL, TIMESTAMP, Index, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class ExtractionMethod(str, enum.Enum):
    """Méthodes d'extraction des mots-clés"""
    NLP = "NLP"
    REGEX = "REGEX"
    MANUAL = "MANUAL"


class JobOfferKeyword(Base):
    """
    Table de liaison entre offres d'emploi et mots-clés
    """
    __tablename__ = "job_offer_keywords"

    # Clé primaire
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Clés étrangères
    job_offer_id = Column(BigInteger, ForeignKey('job_offers.id'), nullable=False)
    keyword_id = Column(BigInteger, ForeignKey('keywords.id'), nullable=False)
    
    # Métadonnées de la relation
    relevance_score = Column(DECIMAL(3, 2), default=0.00, comment="Score de pertinence du mot-clé pour cette offre")
    extraction_method = Column(
        Enum(ExtractionMethod), 
        default=ExtractionMethod.NLP,
        comment="Méthode d'extraction utilisée"
    )
    
    # Timestamp
    created_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        comment="Date de création de l'association"
    )
    
    # Relations
    job_offer = relationship("JobOffer", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="job_offers")
    
    # Index
    __table_args__ = (
        Index('idx_job_offer', 'job_offer_id'),
        Index('idx_keyword', 'keyword_id'),
        Index('idx_relevance', 'relevance_score'),
        Index('unique_job_keyword', 'job_offer_id', 'keyword_id', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<JobOfferKeyword(job_offer_id={self.job_offer_id}, keyword_id={self.keyword_id}, score={self.relevance_score})>"
    
    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'job_offer_id': self.job_offer_id,
            'keyword_id': self.keyword_id,
            'relevance_score': float(self.relevance_score) if self.relevance_score else None,
            'extraction_method': self.extraction_method.value if self.extraction_method else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        } 