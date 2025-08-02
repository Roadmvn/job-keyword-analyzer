"""
Service OAuth pour l'authentification avec Google, LinkedIn, etc.
Gestion des flux OAuth2 et récupération des données utilisateur
"""

import httpx
import urllib.parse
from typing import Dict, Any, Optional, List
from loguru import logger

from core.config import settings


class OAuthService:
    """Service centralisé pour l'authentification OAuth"""
    
    # Configuration des providers OAuth
    PROVIDERS = {
        "google": {
            "name": "Google",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
            "client_id_setting": "GOOGLE_CLIENT_ID",
            "client_secret_setting": "GOOGLE_CLIENT_SECRET",
            "redirect_uri_setting": "GOOGLE_REDIRECT_URI"
        },
        "linkedin": {
            "name": "LinkedIn",
            "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
            "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
            "userinfo_url": "https://api.linkedin.com/v2/people/~",
            "email_url": "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            "scopes": ["r_liteprofile", "r_emailaddress"],
            "client_id_setting": "LINKEDIN_CLIENT_ID",
            "client_secret_setting": "LINKEDIN_CLIENT_SECRET",
            "redirect_uri_setting": "LINKEDIN_REDIRECT_URI"
        },
        "github": {
            "name": "GitHub",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "email_url": "https://api.github.com/user/emails",
            "scopes": ["user:email"],
            "client_id_setting": "GITHUB_CLIENT_ID",
            "client_secret_setting": "GITHUB_CLIENT_SECRET",
            "redirect_uri_setting": "GITHUB_REDIRECT_URI"
        }
    }
    
    @classmethod
    def get_available_providers(cls) -> List[Dict[str, str]]:
        """Récupérer la liste des providers OAuth disponibles"""
        available = []
        
        for provider_key, provider_config in cls.PROVIDERS.items():
            client_id = getattr(settings, provider_config["client_id_setting"], None)
            if client_id:
                available.append({
                    "name": provider_key,
                    "display_name": provider_config["name"],
                    "client_id": client_id,
                    "authorization_url": cls.get_authorization_url(provider_key)
                })
        
        return available
    
    @classmethod
    def get_authorization_url(cls, provider: str, state: str = None) -> Optional[str]:
        """Générer l'URL d'autorisation OAuth"""
        if provider not in cls.PROVIDERS:
            logger.error(f"Provider OAuth non supporté: {provider}")
            return None
        
        provider_config = cls.PROVIDERS[provider]
        client_id = getattr(settings, provider_config["client_id_setting"], None)
        redirect_uri = getattr(settings, provider_config["redirect_uri_setting"], None)
        
        if not client_id or not redirect_uri:
            logger.error(f"Configuration OAuth incomplète pour {provider}")
            return None
        
        # Paramètres de base
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(provider_config["scopes"]),
            "response_type": "code"
        }
        
        # Paramètres spécifiques par provider
        if provider == "google":
            params.update({
                "access_type": "offline",
                "include_granted_scopes": "true"
            })
        elif provider == "linkedin":
            params["response_type"] = "code"
        elif provider == "github":
            params["allow_signup"] = "true"
        
        # Ajouter l'état si fourni
        if state:
            params["state"] = state
        
        # Construire l'URL
        base_url = provider_config["authorize_url"]
        query_string = urllib.parse.urlencode(params)
        
        return f"{base_url}?{query_string}"
    
    @classmethod
    async def exchange_code_for_token(cls, provider: str, code: str, state: str = None) -> Dict[str, Any]:
        """Échanger le code d'autorisation contre un token d'accès"""
        if provider not in cls.PROVIDERS:
            raise ValueError(f"Provider OAuth non supporté: {provider}")
        
        provider_config = cls.PROVIDERS[provider]
        client_id = getattr(settings, provider_config["client_id_setting"], None)
        client_secret = getattr(settings, provider_config["client_secret_setting"], None)
        redirect_uri = getattr(settings, provider_config["redirect_uri_setting"], None)
        
        if not all([client_id, client_secret, redirect_uri]):
            raise ValueError(f"Configuration OAuth incomplète pour {provider}")
        
        # Préparer les données pour l'échange
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Échanger le code contre un token
                headers = {"Accept": "application/json"}
                response = await client.post(
                    provider_config["token_url"],
                    data=token_data,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                token_response = response.json()
                
                # Récupérer les informations utilisateur
                access_token = token_response["access_token"]
                user_data = await cls._get_user_info(provider, access_token)
                
                return user_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP lors de l'échange OAuth {provider}: {e}")
            raise ValueError(f"Erreur d'authentification {provider}")
        except Exception as e:
            logger.error(f"Erreur lors de l'échange OAuth {provider}: {e}")
            raise ValueError(f"Erreur inattendue lors de l'authentification {provider}")
    
    @classmethod
    async def _get_user_info(cls, provider: str, access_token: str) -> Dict[str, Any]:
        """Récupérer les informations utilisateur depuis l'API du provider"""
        provider_config = cls.PROVIDERS[provider]
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            if provider == "google":
                return await cls._get_google_user_info(client, headers, provider_config)
            elif provider == "linkedin":
                return await cls._get_linkedin_user_info(client, headers, provider_config)
            elif provider == "github":
                return await cls._get_github_user_info(client, headers, provider_config)
            else:
                raise ValueError(f"Provider non implémenté: {provider}")
    
    @classmethod
    async def _get_google_user_info(cls, client: httpx.AsyncClient, headers: dict, config: dict) -> Dict[str, Any]:
        """Récupérer les informations utilisateur Google"""
        try:
            response = await client.get(config["userinfo_url"], headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return {
                "id": data["id"],
                "email": data["email"],
                "name": data.get("name"),
                "first_name": data.get("given_name"),
                "last_name": data.get("family_name"),
                "picture": data.get("picture"),
                "verified_email": data.get("verified_email", False),
                "locale": data.get("locale"),
                "provider": "google",
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Erreur récupération données utilisateur Google: {e}")
            raise
    
    @classmethod
    async def _get_linkedin_user_info(cls, client: httpx.AsyncClient, headers: dict, config: dict) -> Dict[str, Any]:
        """Récupérer les informations utilisateur LinkedIn"""
        try:
            # Récupérer le profil
            profile_response = await client.get(
                config["userinfo_url"] + ":(id,firstName,lastName,profilePicture(displayImage~:playableStreams))",
                headers=headers
            )
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Récupérer l'email
            email_response = await client.get(config["email_url"], headers=headers)
            email_response.raise_for_status()
            email_data = email_response.json()
            
            # Extraire les données
            first_name = None
            last_name = None
            if "firstName" in profile_data:
                first_name = profile_data["firstName"]["localized"].get("fr_FR") or \
                            profile_data["firstName"]["localized"].get("en_US") or \
                            list(profile_data["firstName"]["localized"].values())[0]
            
            if "lastName" in profile_data:
                last_name = profile_data["lastName"]["localized"].get("fr_FR") or \
                           profile_data["lastName"]["localized"].get("en_US") or \
                           list(profile_data["lastName"]["localized"].values())[0]
            
            name = f"{first_name} {last_name}".strip() if first_name and last_name else None
            
            email = None
            if "elements" in email_data and email_data["elements"]:
                email = email_data["elements"][0]["handle~"]["emailAddress"]
            
            picture = None
            if "profilePicture" in profile_data and "displayImage~" in profile_data["profilePicture"]:
                images = profile_data["profilePicture"]["displayImage~"]["elements"]
                if images:
                    picture = images[-1]["identifiers"][0]["identifier"]
            
            return {
                "id": profile_data["id"],
                "email": email,
                "name": name,
                "first_name": first_name,
                "last_name": last_name,
                "picture": picture,
                "verified_email": True,  # LinkedIn emails sont vérifiés
                "provider": "linkedin",
                "raw_data": {
                    "profile": profile_data,
                    "email": email_data
                }
            }
        except Exception as e:
            logger.error(f"Erreur récupération données utilisateur LinkedIn: {e}")
            raise
    
    @classmethod
    async def _get_github_user_info(cls, client: httpx.AsyncClient, headers: dict, config: dict) -> Dict[str, Any]:
        """Récupérer les informations utilisateur GitHub"""
        try:
            # Récupérer le profil
            profile_response = await client.get(config["userinfo_url"], headers=headers)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Récupérer les emails
            email_response = await client.get(config["email_url"], headers=headers)
            email_response.raise_for_status()
            email_data = email_response.json()
            
            # Trouver l'email principal
            primary_email = None
            verified_email = False
            
            for email_info in email_data:
                if email_info.get("primary", False):
                    primary_email = email_info["email"]
                    verified_email = email_info.get("verified", False)
                    break
            
            if not primary_email and email_data:
                # Fallback sur le premier email
                primary_email = email_data[0]["email"]
                verified_email = email_data[0].get("verified", False)
            
            # Parser le nom complet
            name = profile_data.get("name", "")
            first_name = None
            last_name = None
            
            if name:
                name_parts = name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else None
            
            return {
                "id": str(profile_data["id"]),
                "email": primary_email,
                "name": name,
                "first_name": first_name,
                "last_name": last_name,
                "picture": profile_data.get("avatar_url"),
                "verified_email": verified_email,
                "provider": "github",
                "raw_data": {
                    "profile": profile_data,
                    "emails": email_data
                }
            }
        except Exception as e:
            logger.error(f"Erreur récupération données utilisateur GitHub: {e}")
            raise
    
    @classmethod
    def validate_oauth_config(cls) -> Dict[str, bool]:
        """Valider la configuration OAuth pour tous les providers"""
        results = {}
        
        for provider_key, provider_config in cls.PROVIDERS.items():
            client_id = getattr(settings, provider_config["client_id_setting"], None)
            client_secret = getattr(settings, provider_config["client_secret_setting"], None)
            redirect_uri = getattr(settings, provider_config["redirect_uri_setting"], None)
            
            is_configured = bool(client_id and client_secret and redirect_uri)
            results[provider_key] = is_configured
            
            if is_configured:
                logger.info(f"Provider OAuth {provider_key} configuré")
            else:
                logger.warning(f"Provider OAuth {provider_key} non configuré")
        
        return results
    
    @classmethod
    async def revoke_token(cls, provider: str, access_token: str) -> bool:
        """Révoquer un token d'accès OAuth"""
        revoke_urls = {
            "google": "https://oauth2.googleapis.com/revoke",
            "github": "https://api.github.com/applications/{client_id}/token",
            # LinkedIn ne supporte pas la révocation de tokens
        }
        
        if provider not in revoke_urls:
            logger.warning(f"Révocation de token non supportée pour {provider}")
            return True  # Considérer comme succès
        
        try:
            async with httpx.AsyncClient() as client:
                if provider == "google":
                    response = await client.post(
                        revoke_urls[provider],
                        data={"token": access_token}
                    )
                elif provider == "github":
                    client_id = getattr(settings, "GITHUB_CLIENT_ID")
                    client_secret = getattr(settings, "GITHUB_CLIENT_SECRET")
                    
                    response = await client.delete(
                        revoke_urls[provider].format(client_id=client_id),
                        json={"access_token": access_token},
                        auth=(client_id, client_secret)
                    )
                
                return response.status_code in [200, 204]
                
        except Exception as e:
            logger.error(f"Erreur lors de la révocation du token {provider}: {e}")
            return False
    
    @classmethod
    def get_provider_login_url(cls, provider: str, state: str = None) -> str:
        """Générer une URL de connexion pour le frontend"""
        auth_url = cls.get_authorization_url(provider, state)
        if not auth_url:
            raise ValueError(f"Provider {provider} non configuré")
        
        return auth_url
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Récupérer la liste des providers supportés"""
        return list(cls.PROVIDERS.keys())


# Validation de la configuration OAuth au démarrage
if not settings.is_testing:
    oauth_status = OAuthService.validate_oauth_config()
    enabled_providers = [p for p, enabled in oauth_status.items() if enabled]
    
    if enabled_providers:
        logger.info(f"Providers OAuth activés: {', '.join(enabled_providers)}")
    else:
        logger.warning("Aucun provider OAuth configuré")


class OAuthError(Exception):
    """Exception personnalisée pour les erreurs OAuth"""
    
    def __init__(self, provider: str, message: str, details: dict = None):
        self.provider = provider
        self.message = message
        self.details = details or {}
        super().__init__(f"Erreur OAuth {provider}: {message}")


class OAuthProviderNotSupportedError(OAuthError):
    """Exception pour les providers non supportés"""
    
    def __init__(self, provider: str):
        super().__init__(provider, f"Provider '{provider}' non supporté")


class OAuthConfigurationError(OAuthError):
    """Exception pour les erreurs de configuration OAuth"""
    
    def __init__(self, provider: str, missing_settings: List[str]):
        message = f"Configuration incomplète. Paramètres manquants: {', '.join(missing_settings)}"
        super().__init__(provider, message, {"missing_settings": missing_settings})