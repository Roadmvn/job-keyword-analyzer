"""
Modèle pour les statistiques quotidiennes
"""

from sqlalchemy import Column, BigInteger, Date, Integer, DECIMAL, String, TIMESTAMP, Index
from sqlalchemy.sql import func
from .database import Base


class DailyStats(Base):
    """
    Modèle pour les statistiques quotidiennes
    """
    __tablename__ = "daily_stats"

    # Clé primaire
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Date de référence
    date = Column(Date, nullable=False, unique=True, comment="Date de référence")
    
    # Statistiques générales
    total_offers = Column(Integer, default=0, comment="Nombre total d'offres à cette date")
    new_offers = Column(Integer, default=0, comment="Nouvelles offres ajoutées ce jour")
    unique_companies = Column(Integer, default=0, comment="Nombre d'entreprises uniques")
    unique_keywords = Column(Integer, default=0, comment="Nombre de mots-clés uniques")
    
    # Statistiques financières
    avg_salary = Column(DECIMAL(10, 2), nullable=True, comment="Salaire moyen")
    
    # Top éléments du jour
    top_keyword = Column(String(100), nullable=True, comment="Mot-clé le plus fréquent")
    top_company = Column(String(255), nullable=True, comment="Entreprise avec le plus d'offres")
    top_location = Column(String(255), nullable=True, comment="Localisation avec le plus d'offres")
    
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
    
    # Index
    __table_args__ = (
        Index('idx_date', 'date'),
    )
    
    def __repr__(self) -> str:
        return f"<DailyStats(date={self.date}, total_offers={self.total_offers})>"
    
    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_offers': self.total_offers,
            'new_offers': self.new_offers,
            'unique_companies': self.unique_companies,
            'unique_keywords': self.unique_keywords,
            'avg_salary': float(self.avg_salary) if self.avg_salary else None,
            'top_keyword': self.top_keyword,
            'top_company': self.top_company,
            'top_location': self.top_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        } 