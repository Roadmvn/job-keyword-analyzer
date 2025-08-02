"""
Opérations CRUD pour l'authentification et la gestion des utilisateurs
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.user import (
    User, UserRole, OAuthAccount, RefreshToken, UserPreferences,
    SearchAlert, SavedSearch, EmailVerification, PasswordReset
)
from auth.security import get_password_hash, verify_password, generate_secure_token, hash_token
from auth.schemas import UserCreate, UserUpdate, UserPreferencesCreate


# ===================================
# GESTION DES UTILISATEURS
# ===================================

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Récupérer un utilisateur par son ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Récupérer un utilisateur par son email"""
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Récupérer un utilisateur par son nom d'utilisateur"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email_or_username(db: Session, identifier: str) -> Optional[User]:
    """Récupérer un utilisateur par email ou nom d'utilisateur"""
    return db.query(User).filter(
        or_(User.email == identifier.lower(), User.username == identifier)
    ).first()


def create_user(db: Session, user_create: UserCreate) -> User:
    """Créer un nouvel utilisateur"""
    # Hacher le mot de passe
    hashed_password = get_password_hash(user_create.password)
    
    # Générer le nom complet si pas fourni
    full_name = user_create.first_name
    if user_create.first_name and user_create.last_name:
        full_name = f"{user_create.first_name} {user_create.last_name}"
    
    # Créer l'utilisateur
    db_user = User(
        email=user_create.email.lower(),
        username=user_create.username,
        hashed_password=hashed_password,
        first_name=user_create.first_name,
        last_name=user_create.last_name,
        full_name=full_name,
        role=UserRole.USER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Créer les préférences par défaut
    create_default_preferences(db, db_user.id)
    
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Mettre à jour un utilisateur"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Mise à jour des champs
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    # Recalculer le nom complet si nécessaire
    if 'first_name' in update_data or 'last_name' in update_data:
        if db_user.first_name and db_user.last_name:
            db_user.full_name = f"{db_user.first_name} {db_user.last_name}"
        elif db_user.first_name:
            db_user.full_name = db_user.first_name
    
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_role(db: Session, user_id: int, new_role: UserRole) -> Optional[User]:
    """Mettre à jour le rôle d'un utilisateur (admin uniquement)"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.role = new_role
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_user_email(db: Session, user_id: int) -> Optional[User]:
    """Marquer l'email d'un utilisateur comme vérifié"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)
    return db_user


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Désactiver un utilisateur"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Supprimer un utilisateur (soft delete)"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    # Anonymiser les données au lieu de supprimer complètement
    db_user.email = f"deleted_{user_id}@example.com"
    db_user.username = f"deleted_user_{user_id}"
    db_user.first_name = None
    db_user.last_name = None
    db_user.full_name = "Utilisateur supprimé"
    db_user.is_active = False
    db_user.hashed_password = None
    
    db.commit()
    return True


def update_last_login(db: Session, user_id: int) -> None:
    """Mettre à jour la date de dernière connexion"""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.last_login = datetime.now(timezone.utc)
        db.commit()


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """Changer le mot de passe d'un utilisateur"""
    db_user = get_user_by_id(db, user_id)
    if not db_user or not db_user.hashed_password:
        return False
    
    # Vérifier l'ancien mot de passe
    if not verify_password(current_password, db_user.hashed_password):
        return False
    
    # Mettre à jour avec le nouveau mot de passe
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def reset_password(db: Session, user_id: int, new_password: str) -> bool:
    """Réinitialiser le mot de passe (sans vérification de l'ancien)"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


# ===================================
# GESTION DES TOKENS DE RAFRAÎCHISSEMENT
# ===================================

def create_refresh_token(db: Session, user_id: int, token: str, device_info: str = None, ip_address: str = None) -> RefreshToken:
    """Créer un token de rafraîchissement"""
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # 7 jours
    
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """Récupérer un token de rafraîchissement"""
    token_hash = hash_token(token)
    return db.query(RefreshToken).filter(
        and_(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    ).first()


def revoke_refresh_token(db: Session, token: str) -> bool:
    """Révoquer un token de rafraîchissement"""
    db_token = get_refresh_token(db, token)
    if not db_token:
        return False
    
    db_token.is_revoked = True
    db.commit()
    return True


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Révoquer tous les tokens d'un utilisateur"""
    count = db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
    ).update({"is_revoked": True})
    db.commit()
    return count


def cleanup_expired_tokens(db: Session) -> int:
    """Nettoyer les tokens expirés"""
    count = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()
    return count


# ===================================
# GESTION OAUTH
# ===================================

def create_oauth_account(db: Session, user_id: int, provider: str, provider_user_id: str, provider_email: str = None, provider_data: dict = None) -> OAuthAccount:
    """Créer un compte OAuth"""
    db_oauth = OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=provider_email,
        provider_data=json.dumps(provider_data) if provider_data else None
    )
    
    db.add(db_oauth)
    db.commit()
    db.refresh(db_oauth)
    return db_oauth


def get_oauth_account(db: Session, provider: str, provider_user_id: str) -> Optional[OAuthAccount]:
    """Récupérer un compte OAuth"""
    return db.query(OAuthAccount).filter(
        and_(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        )
    ).first()


def get_user_oauth_accounts(db: Session, user_id: int) -> List[OAuthAccount]:
    """Récupérer tous les comptes OAuth d'un utilisateur"""
    return db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id).all()


# ===================================
# PRÉFÉRENCES UTILISATEUR
# ===================================

def create_default_preferences(db: Session, user_id: int) -> UserPreferences:
    """Créer les préférences par défaut pour un utilisateur"""
    db_prefs = UserPreferences(user_id=user_id)
    db.add(db_prefs)
    db.commit()
    db.refresh(db_prefs)
    return db_prefs


def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """Récupérer les préférences d'un utilisateur"""
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


def update_user_preferences(db: Session, user_id: int, preferences_data: dict) -> Optional[UserPreferences]:
    """Mettre à jour les préférences d'un utilisateur"""
    db_prefs = get_user_preferences(db, user_id)
    if not db_prefs:
        db_prefs = create_default_preferences(db, user_id)
    
    # Mettre à jour les champs
    for field, value in preferences_data.items():
        if hasattr(db_prefs, field):
            # Convertir les listes en JSON si nécessaire
            if field in ['preferred_job_types', 'preferred_keywords'] and isinstance(value, list):
                value = json.dumps(value)
            setattr(db_prefs, field, value)
    
    db.commit()
    db.refresh(db_prefs)
    return db_prefs


# ===================================
# ALERTES DE RECHERCHE
# ===================================

def create_search_alert(db: Session, user_id: int, alert_data: dict) -> SearchAlert:
    """Créer une alerte de recherche"""
    # Convertir les listes en JSON
    if 'job_types' in alert_data and isinstance(alert_data['job_types'], list):
        alert_data['job_types'] = json.dumps(alert_data['job_types'])
    if 'keywords' in alert_data and isinstance(alert_data['keywords'], list):
        alert_data['keywords'] = json.dumps(alert_data['keywords'])
    
    db_alert = SearchAlert(user_id=user_id, **alert_data)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_user_search_alerts(db: Session, user_id: int) -> List[SearchAlert]:
    """Récupérer toutes les alertes d'un utilisateur"""
    return db.query(SearchAlert).filter(SearchAlert.user_id == user_id).all()


def get_search_alert(db: Session, alert_id: int, user_id: int) -> Optional[SearchAlert]:
    """Récupérer une alerte spécifique"""
    return db.query(SearchAlert).filter(
        and_(SearchAlert.id == alert_id, SearchAlert.user_id == user_id)
    ).first()


def update_search_alert(db: Session, alert_id: int, user_id: int, update_data: dict) -> Optional[SearchAlert]:
    """Mettre à jour une alerte de recherche"""
    db_alert = get_search_alert(db, alert_id, user_id)
    if not db_alert:
        return None
    
    for field, value in update_data.items():
        if hasattr(db_alert, field):
            # Convertir les listes en JSON si nécessaire
            if field in ['job_types', 'keywords'] and isinstance(value, list):
                value = json.dumps(value)
            setattr(db_alert, field, value)
    
    db.commit()
    db.refresh(db_alert)
    return db_alert


def delete_search_alert(db: Session, alert_id: int, user_id: int) -> bool:
    """Supprimer une alerte de recherche"""
    db_alert = get_search_alert(db, alert_id, user_id)
    if not db_alert:
        return False
    
    db.delete(db_alert)
    db.commit()
    return True


# ===================================
# RECHERCHES SAUVEGARDÉES
# ===================================

def create_saved_search(db: Session, user_id: int, name: str, search_params: dict) -> SavedSearch:
    """Créer une recherche sauvegardée"""
    db_search = SavedSearch(
        user_id=user_id,
        name=name,
        search_params=json.dumps(search_params)
    )
    
    db.add(db_search)
    db.commit()
    db.refresh(db_search)
    return db_search


def get_user_saved_searches(db: Session, user_id: int) -> List[SavedSearch]:
    """Récupérer toutes les recherches sauvegardées d'un utilisateur"""
    return db.query(SavedSearch).filter(SavedSearch.user_id == user_id).order_by(desc(SavedSearch.last_used)).all()


def get_saved_search(db: Session, search_id: int, user_id: int) -> Optional[SavedSearch]:
    """Récupérer une recherche sauvegardée spécifique"""
    return db.query(SavedSearch).filter(
        and_(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
    ).first()


def update_saved_search_usage(db: Session, search_id: int, user_id: int) -> bool:
    """Mettre à jour la date d'utilisation d'une recherche sauvegardée"""
    db_search = get_saved_search(db, search_id, user_id)
    if not db_search:
        return False
    
    db_search.last_used = datetime.now(timezone.utc)
    db.commit()
    return True


def delete_saved_search(db: Session, search_id: int, user_id: int) -> bool:
    """Supprimer une recherche sauvegardée"""
    db_search = get_saved_search(db, search_id, user_id)
    if not db_search:
        return False
    
    db.delete(db_search)
    db.commit()
    return True


# ===================================
# VÉRIFICATION EMAIL
# ===================================

def create_email_verification(db: Session, user_id: int, token: str) -> EmailVerification:
    """Créer un token de vérification d'email"""
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Supprimer les anciens tokens non utilisés
    db.query(EmailVerification).filter(
        and_(
            EmailVerification.user_id == user_id,
            EmailVerification.is_used == False
        )
    ).delete()
    
    db_verification = EmailVerification(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(db_verification)
    db.commit()
    db.refresh(db_verification)
    return db_verification


def verify_email_token(db: Session, token: str) -> Optional[EmailVerification]:
    """Vérifier un token d'email"""
    token_hash = hash_token(token)
    return db.query(EmailVerification).filter(
        and_(
            EmailVerification.token_hash == token_hash,
            EmailVerification.is_used == False,
            EmailVerification.expires_at > datetime.now(timezone.utc)
        )
    ).first()


def use_email_verification_token(db: Session, token: str) -> bool:
    """Utiliser un token de vérification d'email"""
    db_verification = verify_email_token(db, token)
    if not db_verification:
        return False
    
    db_verification.is_used = True
    db_verification.verified_at = datetime.now(timezone.utc)
    
    # Vérifier l'utilisateur
    verify_user_email(db, db_verification.user_id)
    
    db.commit()
    return True


# ===================================
# RÉINITIALISATION MOT DE PASSE
# ===================================

def create_password_reset(db: Session, user_id: int, token: str) -> PasswordReset:
    """Créer un token de réinitialisation de mot de passe"""
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    
    # Supprimer les anciens tokens non utilisés
    db.query(PasswordReset).filter(
        and_(
            PasswordReset.user_id == user_id,
            PasswordReset.is_used == False
        )
    ).delete()
    
    db_reset = PasswordReset(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(db_reset)
    db.commit()
    db.refresh(db_reset)
    return db_reset


def verify_password_reset_token(db: Session, token: str) -> Optional[PasswordReset]:
    """Vérifier un token de réinitialisation de mot de passe"""
    token_hash = hash_token(token)
    return db.query(PasswordReset).filter(
        and_(
            PasswordReset.token_hash == token_hash,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.now(timezone.utc)
        )
    ).first()


def use_password_reset_token(db: Session, token: str, new_password: str) -> bool:
    """Utiliser un token de réinitialisation de mot de passe"""
    db_reset = verify_password_reset_token(db, token)
    if not db_reset:
        return False
    
    # Réinitialiser le mot de passe
    if not reset_password(db, db_reset.user_id, new_password):
        return False
    
    db_reset.is_used = True
    db_reset.used_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ===================================
# STATISTIQUES ET LISTES
# ===================================

def get_users_list(db: Session, skip: int = 0, limit: int = 50, search: str = None, role: UserRole = None) -> tuple[List[User], int]:
    """Récupérer la liste des utilisateurs avec pagination et filtres"""
    query = db.query(User)
    
    # Filtres de recherche
    if search:
        search_filter = or_(
            User.email.contains(search),
            User.username.contains(search),
            User.first_name.contains(search),
            User.last_name.contains(search),
            User.full_name.contains(search)
        )
        query = query.filter(search_filter)
    
    if role:
        query = query.filter(User.role == role)
    
    # Compter le total
    total = query.count()
    
    # Appliquer pagination et tri
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    return users, total


def get_user_stats(db: Session) -> dict:
    """Récupérer les statistiques des utilisateurs"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # Répartition par rôle
    role_stats = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    role_distribution = {role.value: count for role, count in role_stats}
    
    # Utilisateurs récents (dernières 24h)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent_users = db.query(User).filter(User.created_at >= recent_cutoff).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "role_distribution": role_distribution,
        "recent_users_24h": recent_users
    }