"""
Dépendances FastAPI pour l'authentification
Middleware et utilitaires de protection des routes
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from functools import wraps

from models.database import get_db
from models.user import User, UserRole
from auth.security import JWTManager, TokenBlacklist
from auth import crud as auth_crud


# Configuration OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scopes={
        "read": "Lecture des données",
        "write": "Écriture des données", 
        "admin": "Administration"
    }
)

# Configuration HTTPBearer pour les tokens personnalisés
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance pour obtenir l'utilisateur actuel depuis le token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Vérifier et décoder le token
        payload = JWTManager.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        # Vérifier si le token est dans la blacklist
        token_jti = payload.get("jti")
        if token_jti and TokenBlacklist.is_blacklisted(token_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token révoqué",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Récupérer l'utilisateur en base
        user = auth_crud.get_user_by_id(db, int(user_id))
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dépendance pour s'assurer que l'utilisateur actuel est actif
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Utilisateur inactif"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dépendance pour s'assurer que l'utilisateur actuel est vérifié
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié. Veuillez vérifier votre email."
        )
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """
    Décorateur pour exiger certains rôles
    Usage: @require_roles([UserRole.ADMIN, UserRole.PREMIUM])
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions insuffisantes"
            )
        return current_user
    return role_checker


def require_permission(required_role: UserRole):
    """
    Décorateur pour exiger un niveau de permission minimum
    Usage: @require_permission(UserRole.PREMIUM)
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle {required_role.value} ou supérieur requis"
            )
        return current_user
    return permission_checker


# Alias pour les dépendances communes
require_user = Depends(get_current_verified_user)
require_premium = Depends(require_permission(UserRole.PREMIUM))
require_admin = Depends(require_permission(UserRole.ADMIN))


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dépendance pour obtenir l'utilisateur actuel de manière optionnelle
    Utile pour les endpoints qui peuvent fonctionner avec ou sans auth
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = JWTManager.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if user_id:
            user = auth_crud.get_user_by_id(db, int(user_id))
            if user and user.is_active:
                return user
    except:
        # En cas d'erreur, on retourne None au lieu de lever une exception
        pass
    
    return None


class RateLimiter:
    """
    Rate limiter simple pour prévenir les abus
    En production, utiliser Redis avec des TTL
    """
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 15):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self._requests = {}  # En production, utiliser Redis
    
    def is_allowed(self, identifier: str) -> bool:
        """Vérifier si une requête est autorisée"""
        import time
        from collections import deque
        
        now = time.time()
        window_start = now - (self.window_minutes * 60)
        
        if identifier not in self._requests:
            self._requests[identifier] = deque()
        
        # Nettoyer les anciennes requêtes
        requests = self._requests[identifier]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Vérifier la limite
        if len(requests) >= self.max_requests:
            return False
        
        # Ajouter la nouvelle requête
        requests.append(now)
        return True


def rate_limit(max_requests: int = 100, window_minutes: int = 15):
    """
    Décorateur de rate limiting
    """
    limiter = RateLimiter(max_requests, window_minutes)
    
    def rate_limit_dependency(request: Request):
        # Utiliser l'IP comme identifiant
        client_ip = request.client.host if request.client else "unknown"
        
        if not limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop de requêtes. Veuillez réessayer plus tard."
            )
        
        return True
    
    return Depends(rate_limit_dependency)


# Rate limiters prédéfinis
auth_rate_limit = rate_limit(max_requests=10, window_minutes=15)  # Pour auth
api_rate_limit = rate_limit(max_requests=1000, window_minutes=60)  # Pour API générale


async def verify_api_key(
    api_key: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Vérifier une clé API (pour l'accès programmatique)
    """
    if not api_key:
        return None
    
    # En production, stocker les API keys en base avec hash
    # Pour l'instant, système simple
    if api_key.startswith("sk-"):
        # Logique de vérification API key
        pass
    
    return None


def get_user_context(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Contexte utilisateur enrichi pour les endpoints
    """
    return {
        "user": current_user,
        "user_id": current_user.id,
        "role": current_user.role,
        "permissions": {
            "can_access_premium": current_user.has_permission(UserRole.PREMIUM),
            "is_admin": current_user.has_permission(UserRole.ADMIN),
            "is_verified": current_user.is_verified
        },
        "db": db
    }


# Middleware d'authentification pour WebSocket
class WebSocketAuthMiddleware:
    """Middleware d'authentification pour les WebSockets"""
    
    def __init__(self, websocket):
        self.websocket = websocket
    
    async def authenticate(self, token: str) -> Optional[User]:
        """Authentifier un utilisateur WebSocket"""
        try:
            payload = JWTManager.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if user_id:
                # Récupérer l'utilisateur (nécessite une session DB)
                # En production, utiliser une injection de dépendance appropriée
                return None  # Placeholder
        except:
            return None
        
        return None