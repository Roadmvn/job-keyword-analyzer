"""
Configuration des tests pytest pour Job Keywords Analyzer
Fixtures globales et configuration de base
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import redis
from elasticsearch import Elasticsearch

# Import des modèles et de l'app
from models.database import Base, get_db
from models.user import User, UserRole
from api.main import app
from auth.security import get_password_hash
from auth import crud as auth_crud


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Créer une base de données SQLite en mémoire pour les tests"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True  # Pour debug
    )
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Nettoyage
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Session de base de données pour chaque test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Client de test FastAPI avec dépendances mockées"""
    
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Nettoyage des overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis pour les tests"""
    mock_redis_client = MagicMock(spec=redis.Redis)
    
    # Configuration des retours par défaut
    mock_redis_client.ping.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.delete.return_value = 1
    mock_redis_client.exists.return_value = False
    
    return mock_redis_client


@pytest.fixture(scope="function")
def mock_elasticsearch():
    """Mock Elasticsearch pour les tests"""
    mock_es = MagicMock(spec=Elasticsearch)
    
    # Configuration des retours par défaut
    mock_es.ping.return_value = True
    mock_es.index.return_value = {"_id": "test_id", "result": "created"}
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 0},
            "hits": []
        }
    }
    mock_es.indices.exists.return_value = True
    
    return mock_es


# ===================================
# FIXTURES POUR LES UTILISATEURS
# ===================================

@pytest.fixture(scope="function")
def sample_user_data():
    """Données d'exemple pour un utilisateur"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePass123!",
        "is_active": True,
        "is_verified": False,
        "role": UserRole.USER
    }


@pytest.fixture(scope="function")
def authenticated_user(client: TestClient, test_db_session, db_utils):
    """Utilisateur authentifié avec tokens"""
    # Créer l'utilisateur
    user = db_utils.create_user(
        test_db_session,
        email="auth@example.com",
        password="SecurePass123!",
        username="authuser",
        is_verified=False
    )
    
    # Se connecter pour obtenir les tokens
    login_data = {
        "username": "auth@example.com",
        "password": "SecurePass123!"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    
    tokens = response.json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    return user, headers


@pytest.fixture(scope="function")
def verified_user(client: TestClient, test_db_session, db_utils):
    """Utilisateur vérifié et authentifié"""
    # Créer l'utilisateur vérifié
    user = db_utils.create_user(
        test_db_session,
        email="verified@example.com",
        password="SecurePass123!",
        username="verifieduser",
        is_verified=True
    )
    
    # Se connecter
    login_data = {
        "username": "verified@example.com",
        "password": "SecurePass123!"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    tokens = response.json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    return user, headers


@pytest.fixture(scope="function")
def premium_user(client: TestClient, test_db_session, db_utils):
    """Utilisateur premium authentifié"""
    user = db_utils.create_user(
        test_db_session,
        email="premium@example.com",
        password="SecurePass123!",
        username="premiumuser",
        is_verified=True,
        role=UserRole.PREMIUM
    )
    
    login_data = {
        "username": "premium@example.com",
        "password": "SecurePass123!"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    tokens = response.json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    return user, headers


@pytest.fixture(scope="function")
def admin_user(client: TestClient, test_db_session, db_utils):
    """Utilisateur administrateur authentifié"""
    user = db_utils.create_user(
        test_db_session,
        email="admin@example.com",
        password="AdminPass123!",
        username="adminuser",
        is_verified=True,
        role=UserRole.ADMIN
    )
    
    login_data = {
        "username": "admin@example.com",
        "password": "AdminPass123!"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    tokens = response.json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    return user, headers


# ===================================
# FIXTURES GÉNÉRALES
# ===================================

@pytest.fixture(scope="function")
def sample_job_offer_data():
    """Données d'exemple pour une offre d'emploi"""
    return {
        "external_id": "test_job_123",
        "title": "Développeur Python Senior",
        "company": "TechCorp",
        "location": "Paris, France",
        "description": "Nous recherchons un développeur Python expérimenté avec FastAPI et PostgreSQL.",
        "requirements": "5+ ans d'expérience en Python, FastAPI, PostgreSQL, Docker",
        "salary_min": 50000,
        "salary_max": 70000,
        "salary_currency": "EUR",
        "job_type": "CDI",
        "contract_type": "Temps plein",
        "experience_level": "Senior",
        "remote_work": True,
        "url": "https://example.com/job/123",
        "apply_url": "https://example.com/apply/123",
        "source": "indeed",
        "posted_date": "2024-01-15",
        "scraped_at": "2024-01-16T10:00:00",
        "content_hash": "abc123hash",
        "scraping_job_id": "job_456"
    }


@pytest.fixture(scope="function")
def sample_keyword_data():
    """Données d'exemple pour un mot-clé"""
    return {
        "name": "Python",
        "category": "langage",
        "frequency": 150,
        "confidence": 0.95
    }


@pytest.fixture(scope="function")
def sample_scraping_job_data():
    """Données d'exemple pour un job de scraping"""
    return {
        "job_id": "scraping_job_789",
        "source": "indeed",
        "search_query": "développeur python",
        "location": "Paris",
        "max_pages": 5,
        "status": "PENDING",
        "progress": 0,
        "total_offers_found": 0,
        "offers_processed": 0
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Réinitialise l'environnement avant chaque test"""
    import os
    
    # Variables d'environnement de test
    os.environ.update({
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",  # DB Redis séparée pour les tests
        "ELASTICSEARCH_URL": "http://localhost:9200",
        "SECRET_KEY": "test-secret-key-very-secure-for-testing-only-do-not-use-in-prod",
        "DEBUG": "true",
        "SEND_VERIFICATION_EMAILS": "false",  # Désactiver les emails en test
        "SEND_NOTIFICATION_EMAILS": "false"
    })
    
    yield
    
    # Nettoyage si nécessaire


# Fixtures pour les tests de scraping
@pytest.fixture(scope="function")
def mock_scrapy_response():
    """Mock d'une réponse Scrapy pour les tests"""
    from scrapy.http import HtmlResponse
    
    html_content = """
    <html>
        <body>
            <div class="job-card" data-jk="123456">
                <h2 class="jobTitle">
                    <a href="/viewjob?jk=123456">
                        <span>Développeur Python</span>
                    </a>
                </h2>
                <span class="companyName">TechCorp</span>
                <div class="companyLocation">Paris</div>
                <div class="salary">45k - 55k €</div>
                <div class="summary">Nous recherchons un développeur Python...</div>
            </div>
        </body>
    </html>
    """
    
    response = HtmlResponse(
        url="https://fr.indeed.com/jobs?q=python",
        body=html_content.encode('utf-8'),
        encoding='utf-8'
    )
    
    return response


# Fixtures pour les tests NLP
@pytest.fixture(scope="function")
def sample_job_description():
    """Description d'emploi d'exemple pour les tests NLP"""
    return """
    Nous recherchons un développeur Python senior pour rejoindre notre équipe.
    
    Compétences requises :
    - Python 3.8+
    - FastAPI ou Django
    - PostgreSQL ou MySQL
    - Docker et Kubernetes
    - Git et CI/CD
    - Tests unitaires avec pytest
    
    Expérience souhaitée :
    - 5+ ans en développement Python
    - Connaissance d'AWS ou GCP
    - Expérience avec React.js
    - Méthodes agiles (Scrum)
    """


# Utilities pour les tests
class DatabaseTestUtils:
    """Utilitaires pour les tests de base de données"""
    
    @staticmethod
    def create_job_offer(session, **kwargs):
        """Crée une offre d'emploi de test"""
        from models.job_offer import JobOffer
        
        default_data = {
            "external_id": "test_123",
            "title": "Test Job",
            "company": "Test Company",
            "url": "https://test.com/job",
            "source": "test"
        }
        default_data.update(kwargs)
        
        job = JobOffer(**default_data)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    
    @staticmethod
    def create_keyword(session, **kwargs):
        """Crée un mot-clé de test"""
        from models.keyword import Keyword
        
        default_data = {
            "name": "Test Keyword",
            "frequency": 1
        }
        default_data.update(kwargs)
        
        keyword = Keyword(**default_data)
        session.add(keyword)
        session.commit()
        session.refresh(keyword)
        return keyword
    
    @staticmethod
    def create_user(session, **kwargs):
        """Crée un utilisateur de test"""
        default_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_verified": False,
            "role": UserRole.USER
        }
        default_data.update(kwargs)
        
        # Extraire le mot de passe et le hasher
        password = default_data.pop("password", None)
        if password:
            default_data["hashed_password"] = get_password_hash(password)
        
        user = User(**default_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Créer les préférences par défaut
        auth_crud.create_default_preferences(session, user.id)
        
        return user


@pytest.fixture(scope="function")
def db_utils():
    """Utilitaires de base de données"""
    return DatabaseTestUtils