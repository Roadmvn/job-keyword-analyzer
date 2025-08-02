"""
Schémas Pydantic pour l'authentification
Validation et sérialisation des données d'auth
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from models.user import UserRole


# ===================================
# SCHÉMAS DE BASE
# ===================================

class UserBase(BaseModel):
    """Schéma de base pour un utilisateur"""
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schéma pour créer un utilisateur"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validation basique du mot de passe"""
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not any(c.islower() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validation du nom d'utilisateur"""
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, _ et -')
        return v


class UserUpdate(BaseModel):
    """Schéma pour modifier un utilisateur"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = None
    language: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, _ et -')
        return v


class UserResponse(UserBase):
    """Schéma de réponse pour un utilisateur"""
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    display_name: str


class UserProfile(UserResponse):
    """Schéma de profil utilisateur complet"""
    preferences: Optional['UserPreferencesResponse'] = None
    search_alerts_count: int = 0
    saved_searches_count: int = 0


# ===================================
# SCHÉMAS D'AUTHENTIFICATION
# ===================================

class Token(BaseModel):
    """Schéma de réponse pour les tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Secondes


class TokenRefresh(BaseModel):
    """Schéma pour rafraîchir un token"""
    refresh_token: str


class LoginRequest(BaseModel):
    """Schéma de requête de connexion"""
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Schéma de réponse de connexion"""
    user: UserResponse
    tokens: Token
    message: str = "Connexion réussie"


# ===================================
# SCHÉMAS DE GESTION DES MOTS DE PASSE
# ===================================

class PasswordChange(BaseModel):
    """Schéma pour changer de mot de passe"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le nouveau mot de passe doit contenir au moins 8 caractères')
        return v


class PasswordResetRequest(BaseModel):
    """Schéma pour demander une réinitialisation de mot de passe"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schéma pour confirmer une réinitialisation de mot de passe"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ===================================
# SCHÉMAS OAUTH
# ===================================

class OAuthProvider(BaseModel):
    """Schéma pour les providers OAuth"""
    name: str
    client_id: str
    authorization_url: str


class OAuthCallback(BaseModel):
    """Schéma pour le callback OAuth"""
    code: str
    state: Optional[str] = None
    provider: str


class OAuthAccountResponse(BaseModel):
    """Schéma de réponse pour un compte OAuth"""
    id: int
    provider: str
    provider_email: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===================================
# SCHÉMAS DE PRÉFÉRENCES UTILISATEUR
# ===================================

class UserPreferencesCreate(BaseModel):
    """Schéma pour créer des préférences utilisateur"""
    default_location: Optional[str] = None
    preferred_job_types: Optional[List[str]] = None
    preferred_keywords: Optional[List[str]] = None
    salary_range_min: Optional[int] = Field(None, ge=0)
    salary_range_max: Optional[int] = Field(None, ge=0)
    remote_work_only: bool = False
    theme: str = Field("light", regex="^(light|dark|auto)$")
    results_per_page: int = Field(20, ge=10, le=100)
    email_notifications: bool = True
    push_notifications: bool = False
    
    @validator('salary_range_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_range_min' in values and values['salary_range_min'] is not None:
            if v < values['salary_range_min']:
                raise ValueError('Le salaire maximum doit être supérieur au minimum')
        return v


class UserPreferencesUpdate(UserPreferencesCreate):
    """Schéma pour modifier des préférences utilisateur"""
    pass


class UserPreferencesResponse(UserPreferencesCreate):
    """Schéma de réponse pour les préférences utilisateur"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===================================
# SCHÉMAS D'ALERTES DE RECHERCHE
# ===================================

class SearchAlertCreate(BaseModel):
    """Schéma pour créer une alerte de recherche"""
    name: str = Field(..., max_length=200)
    search_query: str = Field(..., max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    job_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    frequency: str = Field("daily", regex="^(instant|daily|weekly)$")


class SearchAlertUpdate(BaseModel):
    """Schéma pour modifier une alerte de recherche"""
    name: Optional[str] = Field(None, max_length=200)
    search_query: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    job_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    frequency: Optional[str] = Field(None, regex="^(instant|daily|weekly)$")
    is_active: Optional[bool] = None


class SearchAlertResponse(SearchAlertCreate):
    """Schéma de réponse pour une alerte de recherche"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sent: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===================================
# SCHÉMAS DE RECHERCHES SAUVEGARDÉES
# ===================================

class SavedSearchCreate(BaseModel):
    """Schéma pour créer une recherche sauvegardée"""
    name: str = Field(..., max_length=200)
    search_params: dict  # Paramètres de recherche en JSON


class SavedSearchUpdate(BaseModel):
    """Schéma pour modifier une recherche sauvegardée"""
    name: Optional[str] = Field(None, max_length=200)
    search_params: Optional[dict] = None


class SavedSearchResponse(SavedSearchCreate):
    """Schéma de réponse pour une recherche sauvegardée"""
    id: int
    user_id: int
    results_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===================================
# SCHÉMAS D'ADMINISTRATION
# ===================================

class UserAdminUpdate(BaseModel):
    """Schéma pour modifier un utilisateur (admin)"""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None


class UserList(BaseModel):
    """Schéma pour la liste des utilisateurs"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ===================================
# SCHÉMAS DE VÉRIFICATION
# ===================================

class EmailVerificationRequest(BaseModel):
    """Schéma pour demander une vérification d'email"""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Schéma pour confirmer une vérification d'email"""
    token: str


# ===================================
# MISE À JOUR DES RÉFÉRENCES FORWARD
# ===================================

UserProfile.model_rebuild()