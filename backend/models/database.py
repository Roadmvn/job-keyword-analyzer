"""
Configuration de la base de données SQLAlchemy
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# URL de connexion à la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://app_user:apppassword@mysql:3306/job_analyzer"
)

# Créer le moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Mettre à True pour voir les requêtes SQL
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    pool_recycle=300,  # Recycler les connexions toutes les 5 minutes
    pool_size=10,  # Nombre de connexions dans le pool
    max_overflow=20  # Connexions supplémentaires autorisées
)

# Créer la factory de sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base pour les modèles ORM
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Générateur de session de base de données pour FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialiser la base de données
    Créer toutes les tables si elles n'existent pas
    """
    # Import tous les modèles pour que SQLAlchemy les connaisse
    from . import job_offer, keyword, job_offer_keyword, scraping_job, daily_stats
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine) 