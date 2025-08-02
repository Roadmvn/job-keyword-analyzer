"""Initial migration - create tables

Revision ID: 0001
Revises: 
Create Date: 2024-12-27 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applique les changements de migration"""
    
    # Créer la table keywords
    op.create_table('keywords',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Nom du mot-clé'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='Catégorie (langage, framework, etc.)'),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='0', comment='Nombre d\'occurrences totales'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Score de confiance NLP'),
        sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='Date de création'),
        sa.Column('updated_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='Date de modification'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='Table des mots-clés extraits'
    )
    op.create_index('idx_keywords_name', 'keywords', ['name'])
    op.create_index('idx_keywords_category', 'keywords', ['category'])
    op.create_index('idx_keywords_frequency', 'keywords', ['frequency'])

    # Créer la table scraping_jobs
    op.create_table('scraping_jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False, comment='ID unique du job dans Redis'),
        sa.Column('source', sa.String(length=100), nullable=False, comment='Source à scraper (indeed, linkedin, etc.)'),
        sa.Column('search_query', sa.String(length=255), nullable=True, comment='Requête de recherche'),
        sa.Column('location', sa.String(length=255), nullable=True, comment='Localisation de recherche'),
        sa.Column('max_pages', sa.Integer(), nullable=True, server_default='1', comment='Nombre maximum de pages à scraper'),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='jobstatus'), nullable=True, comment='État actuel du job'),
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0', comment='Pourcentage de completion (0-100)'),
        sa.Column('total_offers_found', sa.Integer(), nullable=True, server_default='0', comment='Nombre total d\'offres trouvées'),
        sa.Column('offers_processed', sa.Integer(), nullable=True, server_default='0', comment='Nombre d\'offres traitées'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Message d\'erreur en cas d\'échec'),
        sa.Column('started_at', mysql.TIMESTAMP(), nullable=True, comment='Date de début d\'exécution'),
        sa.Column('completed_at', mysql.TIMESTAMP(), nullable=True, comment='Date de fin d\'exécution'),
        sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='Date de création'),
        sa.Column('updated_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='Date de modification'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id'),
        comment='Table des tâches de scraping'
    )
    op.create_index('idx_job_id', 'scraping_jobs', ['job_id'])
    op.create_index('idx_status', 'scraping_jobs', ['status'])
    op.create_index('idx_source', 'scraping_jobs', ['source'])
    op.create_index('idx_created_at', 'scraping_jobs', ['created_at'])

    # Créer la table job_offers
    op.create_table('job_offers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True, comment='ID externe de l\'offre'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='Titre du poste'),
        sa.Column('company', sa.String(length=255), nullable=False, comment='Nom de l\'entreprise'),
        sa.Column('location', sa.String(length=255), nullable=True, comment='Localisation du poste'),
        sa.Column('description', sa.Text(), nullable=True, comment='Description complète du poste'),
        sa.Column('requirements', sa.Text(), nullable=True, comment='Exigences et qualifications'),
        sa.Column('salary_min', sa.Integer(), nullable=True, comment='Salaire minimum'),
        sa.Column('salary_max', sa.Integer(), nullable=True, comment='Salaire maximum'),
        sa.Column('salary_currency', sa.String(length=10), nullable=True, server_default='EUR', comment='Devise du salaire'),
        sa.Column('job_type', sa.String(length=50), nullable=True, comment='Type d\'emploi (CDI, CDD, etc.)'),
        sa.Column('contract_type', sa.String(length=50), nullable=True, comment='Type de contrat'),
        sa.Column('experience_level', sa.String(length=50), nullable=True, comment='Niveau d\'expérience requis'),
        sa.Column('remote_work', sa.Boolean(), nullable=True, server_default='0', comment='Télétravail possible'),
        sa.Column('url', sa.Text(), nullable=False, comment='URL de l\'offre'),
        sa.Column('apply_url', sa.Text(), nullable=True, comment='URL de candidature'),
        sa.Column('source', sa.String(length=100), nullable=False, comment='Source du scraping (indeed, linkedin, etc.)'),
        sa.Column('posted_date', sa.String(length=50), nullable=True, comment='Date de publication'),
        sa.Column('scraped_at', sa.String(length=50), nullable=True, comment='Date de scraping'),
        sa.Column('content_hash', sa.String(length=64), nullable=True, comment='Hash MD5 du contenu'),
        sa.Column('scraping_job_id', sa.String(length=100), nullable=True, comment='ID du job de scraping parent'),
        sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='Date de création'),
        sa.Column('updated_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='Date de modification'),
        sa.PrimaryKeyConstraint('id'),
        comment='Table des offres d\'emploi scrapées'
    )
    op.create_index('idx_job_offers_external_id', 'job_offers', ['external_id'])
    op.create_index('idx_job_offers_source', 'job_offers', ['source'])
    op.create_index('idx_job_offers_company', 'job_offers', ['company'])
    op.create_index('idx_job_offers_location', 'job_offers', ['location'])
    op.create_index('idx_job_offers_content_hash', 'job_offers', ['content_hash'])
    op.create_index('idx_job_offers_created_at', 'job_offers', ['created_at'])

    # Créer la table job_offer_keywords (relation many-to-many)
    op.create_table('job_offer_keywords',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('job_offer_id', sa.BigInteger(), nullable=False, comment='ID de l\'offre d\'emploi'),
        sa.Column('keyword_id', sa.BigInteger(), nullable=False, comment='ID du mot-clé'),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1', comment='Nombre d\'occurrences dans cette offre'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Score de confiance pour cette association'),
        sa.Column('context', sa.Text(), nullable=True, comment='Contexte d\'extraction du mot-clé'),
        sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='Date de création'),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_offer_id', 'keyword_id'),
        comment='Association entre offres d\'emploi et mots-clés'
    )
    op.create_index('idx_job_offer_id', 'job_offer_keywords', ['job_offer_id'])
    op.create_index('idx_keyword_id', 'job_offer_keywords', ['keyword_id'])
    op.create_index('idx_frequency', 'job_offer_keywords', ['frequency'])

    # Créer la table daily_stats
    op.create_table('daily_stats',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False, comment='Date des statistiques'),
        sa.Column('total_jobs', sa.Integer(), nullable=False, server_default='0', comment='Nombre total d\'offres'),
        sa.Column('new_jobs', sa.Integer(), nullable=False, server_default='0', comment='Nouvelles offres du jour'),
        sa.Column('total_keywords', sa.Integer(), nullable=False, server_default='0', comment='Nombre total de mots-clés'),
        sa.Column('new_keywords', sa.Integer(), nullable=False, server_default='0', comment='Nouveaux mots-clés du jour'),
        sa.Column('scraping_jobs_run', sa.Integer(), nullable=False, server_default='0', comment='Jobs de scraping exécutés'),
        sa.Column('scraping_jobs_successful', sa.Integer(), nullable=False, server_default='0', comment='Jobs de scraping réussis'),
        sa.Column('top_keywords', sa.JSON(), nullable=True, comment='Top 10 des mots-clés du jour'),
        sa.Column('source_breakdown', sa.JSON(), nullable=True, comment='Répartition par source'),
        sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='Date de création'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date'),
        comment='Statistiques quotidiennes'
    )
    op.create_index('idx_daily_stats_date', 'daily_stats', ['date'])


def downgrade() -> None:
    """Annule les changements de migration"""
    
    # Supprimer les tables dans l'ordre inverse
    op.drop_table('daily_stats')
    op.drop_table('job_offer_keywords')
    op.drop_table('job_offers')
    op.drop_table('scraping_jobs')
    op.drop_table('keywords')
    
    # Supprimer l'enum
    op.execute("DROP TYPE IF EXISTS jobstatus")