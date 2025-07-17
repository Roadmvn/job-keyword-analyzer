"""
Modèle pour les offres d'emploi
"""

from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, Enum, Boolean, TIMESTAMP, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class ContractType(str, enum.Enum):
    """Types de contrat"""
    CDI = "CDI"
    CDD = "CDD" 
    FREELANCE = "FREELANCE"
    STAGE = "STAGE"
    APPRENTISSAGE = "APPRENTISSAGE"
    OTHER = "OTHER"


class ExperienceLevel(str, enum.Enum):
    """Niveaux d'expérience"""
    JUNIOR = "JUNIOR"
    INTERMEDIATE = "INTERMEDIATE"
    SENIOR = "SENIOR"
    EXPERT = "EXPERT"
    ANY = "ANY"


class JobOffer(Base):
    """
    Modèle pour une offre d'emploi
    """
    __tablename__ = "job_offers"

    # Clé primaire
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Informations de base
    title = Column(String(255), nullable=False, comment="Titre du poste")
    company = Column(String(255), nullable=False, comment="Nom de l'entreprise")
    location = Column(String(255), nullable=True, comment="Lieu de travail")
    
    # Contenu de l'offre
    description = Column(Text, nullable=False, comment="Description complète du poste")
    requirements = Column(Text, nullable=True, comment="Exigences et compétences requises")
    
    # Informations financières
    salary_min = Column(DECIMAL(10, 2), nullable=True, comment="Salaire minimum")
    salary_max = Column(DECIMAL(10, 2), nullable=True, comment="Salaire maximum")
    
    # Catégorisation
    contract_type = Column(
        Enum(ContractType), 
        default=ContractType.OTHER,
        comment="Type de contrat"
    )
    experience_level = Column(
        Enum(ExperienceLevel), 
        default=ExperienceLevel.ANY,
        comment="Niveau d'expérience requis"
    )
    remote_work = Column(Boolean, default=False, comment="Télétravail possible")
    
    # Métadonnées de scraping
    source = Column(String(100), nullable=False, comment="Source du scraping (indeed, linkedin, etc.)")
    source_url = Column(String(500), nullable=True, comment="URL de l'offre originale")
    source_id = Column(String(255), nullable=True, comment="ID unique chez la source")
    
    # Timestamps
    scraped_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        comment="Date de scraping"
    )
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
    keywords = relationship(
        "JobOfferKeyword", 
        back_populates="job_offer",
        cascade="all, delete-orphan"
    )
    
    # Index
    __table_args__ = (
        Index('idx_company', 'company'),
        Index('idx_location', 'location'),
        Index('idx_source', 'source'),
        Index('idx_scraped_at', 'scraped_at'),
        Index('idx_contract_type', 'contract_type'),
        Index('idx_experience_level', 'experience_level'),
        Index('unique_source_offer', 'source', 'source_id', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<JobOffer(id={self.id}, title='{self.title}', company='{self.company}')>"
    
    @property
    def avg_salary(self) -> float | None:
        """Calcule le salaire moyen si min et max sont définis"""
        if self.salary_min and self.salary_max:
            return float((self.salary_min + self.salary_max) / 2)
        return None
    
    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'requirements': self.requirements,
            'salary_min': float(self.salary_min) if self.salary_min else None,
            'salary_max': float(self.salary_max) if self.salary_max else None,
            'contract_type': self.contract_type.value if self.contract_type else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'remote_work': self.remote_work,
            'source': self.source,
            'source_url': self.source_url,
            'source_id': self.source_id,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        } 