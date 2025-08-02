"""
Configuration Alembic pour Job Keywords Analyzer
Gestion des migrations de base de données
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Ajouter le répertoire backend au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Charger les variables d'environnement
load_dotenv()

# Configuration Alembic
config = context.config

# Configuration du logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importer les modèles pour l'auto-génération
from models import Base  # Import du Base de SQLAlchemy
from models.job_offer import JobOffer
from models.keyword import Keyword
from models.job_offer_keyword import JobOfferKeyword
from models.scraping_job import ScrapingJob
from models.daily_stats import DailyStats

# Métadonnées cible pour l'auto-génération
target_metadata = Base.metadata

# URL de base de données depuis les variables d'environnement
def get_database_url():
    """Récupère l'URL de la base de données"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Configuration par défaut pour le développement
        mysql_user = os.getenv('MYSQL_USER', 'app_user')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'apppassword')
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_database = os.getenv('MYSQL_DATABASE', 'job_analyzer')
        
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    
    return database_url

def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline'."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Nécessaire pour MySQL
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online'."""
    
    # Configuration de la connexion
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Nécessaire pour MySQL
            # Options spécifiques à MySQL
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()