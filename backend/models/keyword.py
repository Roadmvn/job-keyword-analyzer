"""
Modèle pour les mots-clés
"""

from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, TIMESTAMP, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class KeywordCategory(str, enum.Enum):
    """Catégories de mots-clés"""
    LANGUAGE = "LANGUAGE"
    FRAMEWORK = "FRAMEWORK"
    TOOL = "TOOL"
    SKILL = "SKILL"
    DOMAIN = "DOMAIN"
    OTHER = "OTHER"


class Keyword(Base):
    """
    Modèle pour un mot-clé extrait
    """
    __tablename__ = "keywords"

    # Clé primaire
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Informations du mot-clé
    keyword = Column(String(100), nullable=False, unique=True, comment="Le mot-clé lui-même")
    category = Column(
        Enum(KeywordCategory), 
        default=KeywordCategory.OTHER,
        comment="Catégorie du mot-clé"
    )
    confidence = Column(DECIMAL(3, 2), default=0.00, comment="Score de confiance NLP")
    frequency = Column(Integer, default=1, comment="Fréquence globale d'apparition")
    
    # Timestamps
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
    
    # Relations
    job_offers = relationship(
        "JobOfferKeyword", 
        back_populates="keyword",
        cascade="all, delete-orphan"
    )
    
    # Index
    __table_args__ = (
        Index('idx_keyword', 'keyword'),
        Index('idx_category', 'category'),
        Index('idx_frequency', 'frequency'),
    )
    
    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', category='{self.category}')>"
    
    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'category': self.category.value if self.category else None,
            'confidence': float(self.confidence) if self.confidence else None,
            'frequency': self.frequency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        } 