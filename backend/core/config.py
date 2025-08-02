"""
Configuration centralisée de l'application
Variables d'environnement et paramètres globaux
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, AnyHttpUrl, validator


class Settings(BaseSettings):
    """Configuration principale de l'application"""
    
    # ===================================
    # CONFIGURATION GÉNÉRALE
    # ===================================
    PROJECT_NAME: str = "Job Keywords Analyzer"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Application d'analyse des mots-clés d'offres d'emploi avec IA"
    
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # URLs
    API_V1_STR: str = "/api"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # ===================================
    # SÉCURITÉ JWT
    # ===================================
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 jours
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY doit contenir au moins 32 caractères")
        return v
    
    # ===================================
    # BASE DE DONNÉES
    # ===================================
    DATABASE_URL: str = "mysql+pymysql://job_user:job_password@localhost:3306/job_analyzer"
    DATABASE_ECHO: bool = False  # Log SQL queries
    
    # Pool de connexions
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # ===================================
    # REDIS
    # ===================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Cache TTL (secondes)
    CACHE_TTL_SHORT: int = 300    # 5 minutes
    CACHE_TTL_MEDIUM: int = 1800  # 30 minutes  
    CACHE_TTL_LONG: int = 3600    # 1 heure
    
    # ===================================
    # ELASTICSEARCH
    # ===================================
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    ELASTICSEARCH_INDEX_PREFIX: str = "job_analyzer"
    
    # ===================================
    # EMAIL
    # ===================================
    SEND_VERIFICATION_EMAILS: bool = True
    SEND_NOTIFICATION_EMAILS: bool = True
    
    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    
    # Email addresses
    EMAIL_FROM: str = "noreply@job-analyzer.com"
    EMAIL_FROM_NAME: str = "Job Keywords Analyzer"
    ADMIN_EMAIL: str = "admin@job-analyzer.com"
    
    # Templates
    EMAIL_TEMPLATES_DIR: str = "templates/emails"
    
    # ===================================
    # OAUTH PROVIDERS
    # ===================================
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/oauth/google/callback"
    
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/auth/oauth/linkedin/callback"
    
    # GitHub OAuth (bonus)
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # ===================================
    # SCRAPING
    # ===================================
    SCRAPING_USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    SCRAPING_DELAY_MIN: float = 1.0
    SCRAPING_DELAY_MAX: float = 3.0
    SCRAPING_CONCURRENT_REQUESTS: int = 16
    SCRAPING_DOWNLOAD_TIMEOUT: int = 180
    
    # Rate limiting
    SCRAPING_RATE_LIMIT_ENABLED: bool = True
    SCRAPING_REQUESTS_PER_MINUTE: int = 60
    
    # ===================================
    # NLP
    # ===================================
    SPACY_MODEL: str = "fr_core_news_md"
    NLP_BATCH_SIZE: int = 100
    NLP_MAX_TEXT_LENGTH: int = 1000000  # 1MB
    
    # ===================================
    # API RATE LIMITING
    # ===================================
    RATE_LIMIT_ENABLED: bool = True
    
    # Limits per minute
    RATE_LIMIT_AUTH: int = 10      # Auth endpoints
    RATE_LIMIT_API: int = 1000     # General API
    RATE_LIMIT_SEARCH: int = 100   # Search endpoints
    RATE_LIMIT_ADMIN: int = 200    # Admin endpoints
    
    # ===================================
    # CORS
    # ===================================
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000"
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # ===================================
    # LOGGING
    # ===================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "detailed"  # simple, detailed, json
    LOG_FILE: Optional[str] = None
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # ===================================
    # PERFORMANCE
    # ===================================
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Upload limits
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # Background tasks
    TASK_QUEUE_BROKER: str = "redis://localhost:6379/1"
    TASK_RESULT_BACKEND: str = "redis://localhost:6379/2"
    TASK_WORKER_CONCURRENCY: int = 4
    
    # ===================================
    # MONITORING
    # ===================================
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_TIMEOUT: int = 30
    
    # Sentry (Error tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    
    # Prometheus
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    # ===================================
    # FEATURES FLAGS
    # ===================================
    FEATURE_USER_REGISTRATION: bool = True
    FEATURE_OAUTH_LOGIN: bool = True
    FEATURE_EMAIL_VERIFICATION: bool = True
    FEATURE_SEARCH_ALERTS: bool = True
    FEATURE_PREMIUM_FEATURES: bool = True
    FEATURE_ADMIN_PANEL: bool = True
    
    # ===================================
    # BUSINESS LOGIC
    # ===================================
    
    # Limits for free users
    FREE_USER_SEARCHES_PER_DAY: int = 50
    FREE_USER_SAVED_SEARCHES: int = 5
    FREE_USER_ALERTS: int = 2
    
    # Limits for premium users
    PREMIUM_USER_SEARCHES_PER_DAY: int = 1000
    PREMIUM_USER_SAVED_SEARCHES: int = 50
    PREMIUM_USER_ALERTS: int = 20
    
    # Job scraping
    MAX_JOBS_PER_SCRAPING_SESSION: int = 1000
    JOB_DUPLICATE_CHECK_DAYS: int = 30
    JOB_DATA_RETENTION_DAYS: int = 365
    
    # ===================================
    # DÉVELOPPEMENT
    # ===================================
    
    # Test configuration
    TESTING: bool = False
    TEST_DATABASE_URL: Optional[str] = None
    
    # Development tools
    RELOAD_ON_CHANGE: bool = False
    PROFILING_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    # ===================================
    # PROPRIÉTÉS CALCULÉES
    # ===================================
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.TESTING or self.ENVIRONMENT == "test"
    
    @property
    def database_url_sync(self) -> str:
        """URL de base de données synchrone"""
        return self.DATABASE_URL
    
    @property
    def database_url_async(self) -> str:
        """URL de base de données asynchrone"""
        return self.DATABASE_URL.replace("mysql+pymysql://", "mysql+aiomysql://")
    
    def get_cors_origins(self) -> List[str]:
        """Récupérer les origines CORS autorisées"""
        origins = [str(origin) for origin in self.CORS_ORIGINS]
        
        if self.is_development:
            # Ajouter des origines de développement par défaut
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]
            origins.extend(dev_origins)
        
        return list(set(origins))  # Supprimer les doublons
    
    def get_allowed_hosts(self) -> List[str]:
        """Récupérer les hosts autorisés"""
        if self.is_development:
            return ["*"]
        
        return [
            "localhost",
            "127.0.0.1",
            "job-analyzer.com",
            "www.job-analyzer.com",
            "api.job-analyzer.com"
        ]


# Instance globale des paramètres
settings = Settings()


# ===================================
# CONFIGURATION PAR ENVIRONNEMENT
# ===================================

def get_environment_config():
    """Configuration spécifique à l'environnement"""
    if settings.is_development:
        return {
            "reload": True,
            "debug": True,
            "log_level": "DEBUG",
            "workers": 1
        }
    elif settings.is_production:
        return {
            "reload": False,
            "debug": False,
            "log_level": "INFO",
            "workers": 4
        }
    else:  # staging
        return {
            "reload": False,
            "debug": False,
            "log_level": "INFO",
            "workers": 2
        }


# ===================================
# VALIDATION CONFIGURATION
# ===================================

def validate_configuration():
    """Valider la configuration au démarrage"""
    errors = []
    
    # Vérifications critiques
    if settings.is_production:
        if settings.SECRET_KEY == "your-super-secret-key-change-in-production":
            errors.append("SECRET_KEY doit être changé en production")
        
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            errors.append("Configuration SMTP requise en production")
        
        if not settings.DATABASE_URL.startswith("mysql"):
            errors.append("Base de données MySQL requise en production")
    
    # Vérifications OAuth
    if settings.FEATURE_OAUTH_LOGIN:
        if not settings.GOOGLE_CLIENT_ID and not settings.LINKEDIN_CLIENT_ID:
            errors.append("Au moins un provider OAuth doit être configuré")
    
    # Vérifications base de données
    if "localhost" in settings.DATABASE_URL and settings.is_production:
        errors.append("Base de données locale non recommandée en production")
    
    if errors:
        error_msg = "Erreurs de configuration:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)


# Valider au démarrage si pas en mode test
if not settings.is_testing:
    try:
        validate_configuration()
    except ValueError as e:
        if settings.is_production:
            raise e
        else:
            print(f"⚠️  Configuration warnings: {e}")


# ===================================
# HELPERS
# ===================================

def get_database_url(async_driver: bool = False) -> str:
    """Récupérer l'URL de base de données"""
    if settings.is_testing and settings.TEST_DATABASE_URL:
        return settings.TEST_DATABASE_URL
    
    url = settings.database_url_async if async_driver else settings.database_url_sync
    return url


def get_redis_config() -> dict:
    """Configuration Redis"""
    return {
        "url": settings.REDIS_URL,
        "password": settings.REDIS_PASSWORD,
        "db": settings.REDIS_DB,
        "decode_responses": True,
        "health_check_interval": 30
    }


def get_email_config() -> dict:
    """Configuration email"""
    return {
        "hostname": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "use_tls": settings.SMTP_TLS,
        "use_ssl": settings.SMTP_SSL
    }