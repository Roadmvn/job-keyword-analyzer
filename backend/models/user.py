"""
Modèles pour la gestion des utilisateurs et de l'authentification
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class UserRole(str, Enum):
    """Rôles disponibles pour les utilisateurs"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class User(Base):
    """Modèle utilisateur principal"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Informations d'authentification
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable pour OAuth
    
    # Informations personnelles
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    
    # Statut et rôle
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Métadonnées
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="Europe/Paris", nullable=True)
    language = Column(String(10), default="fr", nullable=True)
    
    # Relations
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    user_preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    search_alerts = relationship("SearchAlert", back_populates="user", cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def to_dict(self):
        """Convertir en dictionnaire pour les réponses API"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "language": self.language
        }

    @property
    def display_name(self):
        """Nom d'affichage préféré"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]

    def has_permission(self, required_role: UserRole) -> bool:
        """Vérifier si l'utilisateur a le rôle requis ou supérieur"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.PREMIUM: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)


class OAuthAccount(Base):
    """Comptes OAuth liés (Google, LinkedIn, etc.)"""
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Informations OAuth
    provider = Column(String(50), nullable=False)  # 'google', 'linkedin', etc.
    provider_user_id = Column(String(255), nullable=False)  # ID chez le provider
    provider_email = Column(String(255), nullable=True)
    
    # Métadonnées du provider
    provider_data = Column(Text, nullable=True)  # JSON avec infos supplémentaires
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="oauth_accounts")

    def __repr__(self):
        return f"<OAuthAccount(user_id={self.user_id}, provider='{self.provider}')>"


class RefreshToken(Base):
    """Tokens de rafraîchissement pour maintenir les sessions"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    
    # Métadonnées
    device_info = Column(String(500), nullable=True)  # User-Agent, etc.
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Statut
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relations
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self):
        """Vérifier si le token est expiré"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Vérifier si le token est valide"""
        return not self.is_revoked and not self.is_expired


class UserPreferences(Base):
    """Préférences utilisateur pour la recherche et l'interface"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Préférences de recherche
    default_location = Column(String(200), nullable=True)
    preferred_job_types = Column(Text, nullable=True)  # JSON array
    preferred_keywords = Column(Text, nullable=True)  # JSON array
    salary_range_min = Column(Integer, nullable=True)
    salary_range_max = Column(Integer, nullable=True)
    remote_work_only = Column(Boolean, default=False)
    
    # Préférences d'interface
    theme = Column(String(20), default="light")  # 'light', 'dark', 'auto'
    results_per_page = Column(Integer, default=20)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="user_preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"


class SearchAlert(Base):
    """Alertes de recherche pour notifier les nouveaux jobs"""
    __tablename__ = "search_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Configuration de l'alerte
    name = Column(String(200), nullable=False)
    search_query = Column(String(500), nullable=False)
    location = Column(String(200), nullable=True)
    job_types = Column(Text, nullable=True)  # JSON array
    keywords = Column(Text, nullable=True)  # JSON array
    
    # Fréquence et statut
    frequency = Column(String(20), default="daily")  # 'daily', 'weekly', 'instant'
    is_active = Column(Boolean, default=True)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="search_alerts")

    def __repr__(self):
        return f"<SearchAlert(user_id={self.user_id}, name='{self.name}')>"


class SavedSearch(Base):
    """Recherches sauvegardées par l'utilisateur"""
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Détails de la recherche
    name = Column(String(200), nullable=False)
    search_params = Column(Text, nullable=False)  # JSON avec tous les paramètres
    
    # Métadonnées
    results_count = Column(Integer, default=0)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="saved_searches")

    def __repr__(self):
        return f"<SavedSearch(user_id={self.user_id}, name='{self.name}')>"


class EmailVerification(Base):
    """Tokens de vérification email"""
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statut
    is_used = Column(Boolean, default=False)

    def __repr__(self):
        return f"<EmailVerification(user_id={self.user_id})>"

    @property
    def is_expired(self):
        """Vérifier si le token est expiré"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Vérifier si le token est valide"""
        return not self.is_used and not self.is_expired


class PasswordReset(Base):
    """Tokens de réinitialisation de mot de passe"""
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statut
    is_used = Column(Boolean, default=False)

    def __repr__(self):
        return f"<PasswordReset(user_id={self.user_id})>"

    @property
    def is_expired(self):
        """Vérifier si le token est expiré"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Vérifier si le token est valide"""
        return not self.is_used and not self.is_expired