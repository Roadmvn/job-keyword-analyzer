"""
Tests pour les endpoints d'authentification
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from auth.schemas import UserCreate
from auth import crud as auth_crud


class TestAuthRegistration:
    """Tests pour l'inscription"""
    
    def test_register_success(self, client: TestClient, test_db_session):
        """Test d'inscription réussie"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "hashed_password" not in data  # Ne doit pas être exposé
    
    def test_register_duplicate_email(self, client: TestClient, test_db_session, db_utils):
        """Test d'inscription avec email déjà existant"""
        # Créer un utilisateur existant
        existing_user = db_utils.create_user(
            test_db_session, 
            email="existing@example.com",
            username="existing_user"
        )
        
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "username": "newuser"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "email existe déjà" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, test_db_session, db_utils):
        """Test d'inscription avec nom d'utilisateur déjà existant"""
        existing_user = db_utils.create_user(
            test_db_session,
            email="existing@example.com", 
            username="existing_user"
        )
        
        user_data = {
            "email": "new@example.com",
            "password": "SecurePass123!",
            "username": "existing_user"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "nom d'utilisateur" in response.json()["detail"]
    
    def test_register_weak_password(self, client: TestClient):
        """Test d'inscription avec mot de passe faible"""
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Trop faible
            "username": "testuser"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "mot de passe" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """Test d'inscription avec email invalide"""
        user_data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "username": "testuser"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422  # Validation Pydantic


class TestAuthLogin:
    """Tests pour la connexion"""
    
    def test_login_success(self, client: TestClient, test_db_session, db_utils):
        """Test de connexion réussie"""
        # Créer un utilisateur
        user = db_utils.create_user(
            test_db_session,
            email="test@example.com",
            password="SecurePass123!",
            username="testuser"
        )
        
        login_data = {
            "username": "test@example.com",  # Peut être email ou username
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["tokens"]["access_token"]
        assert data["tokens"]["refresh_token"]
        assert data["tokens"]["token_type"] == "bearer"
    
    def test_login_with_username(self, client: TestClient, test_db_session, db_utils):
        """Test de connexion avec nom d'utilisateur"""
        user = db_utils.create_user(
            test_db_session,
            email="test@example.com",
            password="SecurePass123!",
            username="testuser"
        )
        
        login_data = {
            "username": "testuser",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
    
    def test_login_wrong_password(self, client: TestClient, test_db_session, db_utils):
        """Test de connexion avec mauvais mot de passe"""
        user = db_utils.create_user(
            test_db_session,
            email="test@example.com",
            password="SecurePass123!"
        )
        
        login_data = {
            "username": "test@example.com",
            "password": "WrongPassword!"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test de connexion avec utilisateur inexistant"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client: TestClient, test_db_session, db_utils):
        """Test de connexion avec utilisateur désactivé"""
        user = db_utils.create_user(
            test_db_session,
            email="test@example.com",
            password="SecurePass123!"
        )
        
        # Désactiver l'utilisateur
        user.is_active = False
        test_db_session.commit()
        
        login_data = {
            "username": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 403
        assert "désactivé" in response.json()["detail"]


class TestTokenRefresh:
    """Tests pour le rafraîchissement de tokens"""
    
    def test_refresh_token_success(self, client: TestClient, test_db_session, db_utils):
        """Test de rafraîchissement de token réussi"""
        # Créer un utilisateur et se connecter
        user = db_utils.create_user(test_db_session, email="test@example.com")
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "SecurePass123!"
        })
        tokens = login_response.json()["tokens"]
        
        # Rafraîchir le token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]  # Nouveau token
        assert data["refresh_token"] != tokens["refresh_token"]  # Nouveau refresh token
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test de rafraîchissement avec token invalide"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401


class TestUserProfile:
    """Tests pour la gestion du profil utilisateur"""
    
    def test_get_current_user_profile(self, client: TestClient, test_db_session, authenticated_user):
        """Test de récupération du profil utilisateur"""
        user, headers = authenticated_user
        
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert "preferences" in data
        assert "search_alerts_count" in data
        assert "saved_searches_count" in data
    
    def test_update_current_user(self, client: TestClient, test_db_session, authenticated_user):
        """Test de mise à jour du profil"""
        user, headers = authenticated_user
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "timezone": "Europe/London"
        }
        
        response = client.put("/api/auth/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["timezone"] == "Europe/London"
    
    def test_get_profile_unauthorized(self, client: TestClient):
        """Test d'accès au profil sans authentification"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestPasswordManagement:
    """Tests pour la gestion des mots de passe"""
    
    def test_change_password_success(self, client: TestClient, test_db_session, authenticated_user):
        """Test de changement de mot de passe réussi"""
        user, headers = authenticated_user
        
        change_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = client.post("/api/auth/change-password", json=change_data, headers=headers)
        assert response.status_code == 200
        assert "modifié avec succès" in response.json()["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, authenticated_user):
        """Test de changement avec mauvais mot de passe actuel"""
        user, headers = authenticated_user
        
        change_data = {
            "current_password": "WrongPassword!",
            "new_password": "NewSecurePass456!"
        }
        
        response = client.post("/api/auth/change-password", json=change_data, headers=headers)
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]
    
    def test_forgot_password(self, client: TestClient, test_db_session, db_utils):
        """Test de demande de réinitialisation de mot de passe"""
        user = db_utils.create_user(test_db_session, email="test@example.com")
        
        with patch('services.email_service.EmailService.send_password_reset_email') as mock_email:
            reset_data = {"email": "test@example.com"}
            response = client.post("/api/auth/forgot-password", json=reset_data)
            
            assert response.status_code == 200
            assert "lien de réinitialisation" in response.json()["message"]
            mock_email.assert_called_once()
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test de demande avec email inexistant"""
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/api/auth/forgot-password", json=reset_data)
        
        # Doit retourner succès pour éviter l'énumération d'emails
        assert response.status_code == 200
        assert "lien de réinitialisation" in response.json()["message"]


class TestEmailVerification:
    """Tests pour la vérification d'email"""
    
    def test_send_verification_email(self, client: TestClient, test_db_session, db_utils):
        """Test d'envoi d'email de vérification"""
        user = db_utils.create_user(test_db_session, email="test@example.com", is_verified=False)
        
        with patch('services.email_service.EmailService.send_verification_email') as mock_email:
            request_data = {"email": "test@example.com"}
            response = client.post("/api/auth/send-verification", json=request_data)
            
            assert response.status_code == 200
            mock_email.assert_called_once()
    
    def test_send_verification_already_verified(self, client: TestClient, test_db_session, db_utils):
        """Test d'envoi pour un email déjà vérifié"""
        user = db_utils.create_user(test_db_session, email="test@example.com", is_verified=True)
        
        request_data = {"email": "test@example.com"}
        response = client.post("/api/auth/send-verification", json=request_data)
        
        assert response.status_code == 400
        assert "déjà vérifié" in response.json()["detail"]


class TestSearchAlerts:
    """Tests pour les alertes de recherche"""
    
    def test_create_search_alert(self, client: TestClient, verified_user):
        """Test de création d'alerte de recherche"""
        user, headers = verified_user
        
        alert_data = {
            "name": "Jobs Python",
            "search_query": "python développeur",
            "location": "Paris",
            "frequency": "daily"
        }
        
        response = client.post("/api/auth/alerts", json=alert_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == alert_data["name"]
        assert data["search_query"] == alert_data["search_query"]
        assert data["is_active"] is True
    
    def test_get_search_alerts(self, client: TestClient, verified_user):
        """Test de récupération des alertes"""
        user, headers = verified_user
        
        # Créer une alerte d'abord
        alert_data = {
            "name": "Jobs Python", 
            "search_query": "python",
            "frequency": "daily"
        }
        client.post("/api/auth/alerts", json=alert_data, headers=headers)
        
        # Récupérer les alertes
        response = client.get("/api/auth/alerts", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_create_alert_unverified_user(self, client: TestClient, authenticated_user):
        """Test de création d'alerte avec utilisateur non vérifié"""
        user, headers = authenticated_user
        
        alert_data = {
            "name": "Jobs Python",
            "search_query": "python"
        }
        
        response = client.post("/api/auth/alerts", json=alert_data, headers=headers)
        assert response.status_code == 403  # Utilisateur non vérifié


class TestOAuth:
    """Tests pour l'authentification OAuth"""
    
    def test_get_oauth_providers(self, client: TestClient):
        """Test de récupération des providers OAuth"""
        response = client.get("/api/auth/oauth/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Le contenu dépend de la configuration
    
    def test_oauth_authorize_invalid_provider(self, client: TestClient):
        """Test d'autorisation avec provider invalide"""
        response = client.get("/api/auth/oauth/invalid_provider/authorize")
        assert response.status_code == 400
    
    @patch('services.oauth_service.OAuthService.exchange_code_for_token')
    def test_oauth_callback_new_user(self, mock_exchange, client: TestClient, test_db_session):
        """Test de callback OAuth pour nouvel utilisateur"""
        # Mock des données utilisateur OAuth
        mock_exchange.return_value = {
            "id": "google_123",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "first_name": "OAuth",
            "last_name": "User",
            "verified_email": True
        }
        
        callback_data = {
            "code": "oauth_code_123",
            "state": "random_state"
        }
        
        response = client.post("/api/auth/oauth/google/callback", json=callback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "oauth@example.com"
        assert data["user"]["is_verified"] is True


class TestAdminEndpoints:
    """Tests pour les endpoints d'administration"""
    
    def test_get_users_admin(self, client: TestClient, admin_user):
        """Test de récupération des utilisateurs (admin)"""
        user, headers = admin_user
        
        response = client.get("/api/auth/admin/users", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["users"], list)
    
    def test_get_users_non_admin(self, client: TestClient, authenticated_user):
        """Test d'accès admin avec utilisateur normal"""
        user, headers = authenticated_user
        
        response = client.get("/api/auth/admin/users", headers=headers)
        assert response.status_code == 403
    
    def test_update_user_role_admin(self, client: TestClient, admin_user, test_db_session, db_utils):
        """Test de modification de rôle utilisateur (admin)"""
        admin, headers = admin_user
        
        # Créer un utilisateur normal
        normal_user = db_utils.create_user(test_db_session, email="normal@example.com")
        
        response = client.put(
            f"/api/auth/admin/users/{normal_user.id}/role?new_role=premium",
            headers=headers
        )
        assert response.status_code == 200
        
        # Vérifier que le rôle a été mis à jour
        test_db_session.refresh(normal_user)
        assert normal_user.role.value == "premium"
    
    def test_get_user_stats_admin(self, client: TestClient, admin_user):
        """Test de récupération des statistiques (admin)"""
        user, headers = admin_user
        
        response = client.get("/api/auth/admin/stats", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "role_distribution" in data