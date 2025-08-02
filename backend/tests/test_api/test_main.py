"""
Tests pour l'API principale FastAPI
"""

import pytest
from fastapi.testclient import TestClient


class TestMainAPI:
    """Tests pour les endpoints principaux de l'API"""
    
    def test_health_check(self, client: TestClient):
        """Test du endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test du endpoint racine"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_stats_endpoint_empty_db(self, client: TestClient):
        """Test du endpoint stats avec une base vide"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_jobs" in data
        assert "total_keywords" in data
        assert data["total_jobs"] == 0
        assert data["total_keywords"] == 0
    
    def test_stats_endpoint_with_data(self, client: TestClient, test_db_session, db_utils):
        """Test du endpoint stats avec des données"""
        # Créer des données de test
        job1 = db_utils.create_job_offer(test_db_session, title="Python Developer")
        job2 = db_utils.create_job_offer(test_db_session, title="JavaScript Developer", external_id="test_456")
        keyword1 = db_utils.create_keyword(test_db_session, name="Python", frequency=10)
        keyword2 = db_utils.create_keyword(test_db_session, name="JavaScript", frequency=5)
        
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_jobs"] == 2
        assert data["total_keywords"] == 2
    
    def test_jobs_endpoint_empty(self, client: TestClient):
        """Test du endpoint jobs avec une base vide"""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_jobs_endpoint_with_limit(self, client: TestClient, test_db_session, db_utils):
        """Test du endpoint jobs avec limite"""
        # Créer 5 jobs de test
        for i in range(5):
            db_utils.create_job_offer(
                test_db_session, 
                title=f"Job {i}", 
                external_id=f"test_{i}"
            )
        
        # Test avec limite
        response = client.get("/api/jobs?limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        
        # Vérifier la structure des données
        job = data[0]
        assert "id" in job
        assert "title" in job
        assert "company" in job
        assert "created_at" in job
    
    def test_keywords_endpoint_empty(self, client: TestClient):
        """Test du endpoint keywords avec une base vide"""
        response = client.get("/api/keywords")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_keywords_endpoint_with_data(self, client: TestClient, test_db_session, db_utils):
        """Test du endpoint keywords avec des données"""
        # Créer des mots-clés triés par fréquence
        keyword1 = db_utils.create_keyword(test_db_session, name="Python", frequency=100)
        keyword2 = db_utils.create_keyword(test_db_session, name="JavaScript", frequency=80)
        keyword3 = db_utils.create_keyword(test_db_session, name="Java", frequency=60)
        
        response = client.get("/api/keywords?limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Vérifier l'ordre (par fréquence décroissante)
        assert data[0]["name"] == "Python"
        assert data[0]["frequency"] == 100
        assert data[1]["name"] == "JavaScript"
        assert data[1]["frequency"] == 80
    
    def test_populate_test_data(self, client: TestClient):
        """Test du endpoint de population des données de test"""
        response = client.post("/api/test/populate")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "jobs_created" in data
        assert "keywords_created" in data
    
    def test_cors_headers(self, client: TestClient):
        """Test des headers CORS"""
        response = client.options("/api/stats")
        assert response.status_code == 200
        
        # Vérifier les headers CORS (si configurés)
        headers = response.headers
        # Note: Ajuster selon votre configuration CORS


class TestErrorHandling:
    """Tests pour la gestion d'erreurs"""
    
    def test_404_endpoint(self, client: TestClient):
        """Test d'un endpoint inexistant"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_limit_parameter(self, client: TestClient):
        """Test avec un paramètre limit invalide"""
        response = client.get("/api/jobs?limit=invalid")
        # Dépend de votre validation - peut être 422 ou 400
        assert response.status_code in [400, 422]
    
    def test_negative_limit_parameter(self, client: TestClient):
        """Test avec un paramètre limit négatif"""
        response = client.get("/api/jobs?limit=-1")
        # La validation devrait rejeter les valeurs négatives
        assert response.status_code in [400, 422]


class TestAPIAuthentication:
    """Tests pour l'authentification API (si implémentée)"""
    
    @pytest.mark.skip(reason="Authentification pas encore implémentée")
    def test_protected_endpoint_without_auth(self, client: TestClient):
        """Test d'un endpoint protégé sans authentification"""
        response = client.post("/api/admin/reset")
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Authentification pas encore implémentée")
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test d'un endpoint protégé avec token invalide"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/admin/reset", headers=headers)
        assert response.status_code == 401


class TestAPIPerformance:
    """Tests de performance basiques"""
    
    def test_response_time_health_check(self, client: TestClient):
        """Test du temps de réponse du health check"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Moins d'1 seconde
    
    def test_concurrent_requests(self, client: TestClient):
        """Test de requêtes concurrentes simples"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Exécuter 10 requêtes en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # Toutes les requêtes doivent réussir
        for response in responses:
            assert response.status_code == 200