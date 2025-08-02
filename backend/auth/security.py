"""
Utilitaires de sécurité pour l'authentification
Gestion des mots de passe, JWT tokens, etc.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import ValidationError

from core.config import settings


# Configuration du hachage de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration JWT
ALGORITHM = "HS256"


class SecurityUtils:
    """Utilitaires de sécurité centralisés"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifier un mot de passe contre son hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Générer le hash d'un mot de passe"""
        return pwd_context.hash(password)

    @staticmethod
    def generate_secure_token() -> str:
        """Générer un token sécurisé aléatoire"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hasher un token pour le stockage en base"""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Valider la force d'un mot de passe
        Retourne (is_valid, liste_erreurs)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not any(c.isupper() for c in password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not any(c.islower() for c in password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if not any(c.isdigit() for c in password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        # Vérifier contre les mots de passe communs
        common_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890"
        ]
        if password.lower() in common_passwords:
            errors.append("Ce mot de passe est trop commun")
        
        return len(errors) == 0, errors


class JWTManager:
    """Gestionnaire des tokens JWT"""

    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Créer un token d'accès JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        to_encode.update({"iat": datetime.now(timezone.utc)})
        to_encode.update({"type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """
        Créer un token de rafraîchissement
        """
        data = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        }
        
        encoded_jwt = jwt.encode(
            data, 
            settings.SECRET_KEY, 
            algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """
        Vérifier et décoder un token JWT
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            
            # Vérifier le type de token
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token de type invalide. Attendu: {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Vérifier l'expiration
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token sans date d'expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expiré",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token invalide: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token malformé",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_user_id_from_token(token: str, token_type: str = "access") -> int:
        """
        Extraire l'ID utilisateur d'un token
        """
        payload = JWTManager.verify_token(token, token_type)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sans identifiant utilisateur",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            return int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiant utilisateur invalide dans le token",
                headers={"WWW-Authenticate": "Bearer"},
            )


class TokenBlacklist:
    """
    Gestion de la liste noire des tokens (pour la déconnexion)
    En production, utiliser Redis pour la performance
    """
    
    _blacklisted_tokens = set()
    
    @classmethod
    def add_token(cls, token_jti: str):
        """Ajouter un token à la liste noire"""
        cls._blacklisted_tokens.add(token_jti)
    
    @classmethod
    def is_blacklisted(cls, token_jti: str) -> bool:
        """Vérifier si un token est dans la liste noire"""
        return token_jti in cls._blacklisted_tokens
    
    @classmethod
    def clear_expired_tokens(cls):
        """Nettoyer les tokens expirés de la liste noire"""
        # Implémentation basique - en production, utiliser une TTL Redis
        pass


def create_email_verification_token(user_id: int) -> str:
    """Créer un token de vérification d'email"""
    data = {
        "sub": str(user_id),
        "type": "email_verification",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user_id: int) -> str:
    """Créer un token de réinitialisation de mot de passe"""
    data = {
        "sub": str(user_id),
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_email_token(token: str) -> int:
    """Vérifier un token de vérification d'email"""
    payload = JWTManager.verify_token(token, "email_verification")
    return int(payload["sub"])


def verify_password_reset_token(token: str) -> int:
    """Vérifier un token de réinitialisation de mot de passe"""
    payload = JWTManager.verify_token(token, "password_reset")
    return int(payload["sub"])


# Aliases pour faciliter l'utilisation
verify_password = SecurityUtils.verify_password
get_password_hash = SecurityUtils.get_password_hash
generate_secure_token = SecurityUtils.generate_secure_token
validate_password_strength = SecurityUtils.validate_password_strength

create_access_token = JWTManager.create_access_token
create_refresh_token = JWTManager.create_refresh_token
verify_token = JWTManager.verify_token
get_user_id_from_token = JWTManager.get_user_id_from_token