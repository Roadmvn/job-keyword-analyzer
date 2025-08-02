"""
Endpoints d'authentification JWT avec OAuth2
Routes pour inscription, connexion, gestion des tokens, etc.
"""

from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User, UserRole
from auth import crud as auth_crud
from auth.schemas import (
    UserCreate, UserResponse, UserUpdate, UserProfile, UserList,
    LoginRequest, LoginResponse, Token, TokenRefresh,
    PasswordChange, PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest, EmailVerificationConfirm,
    UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse,
    SearchAlertCreate, SearchAlertUpdate, SearchAlertResponse,
    SavedSearchCreate, SavedSearchUpdate, SavedSearchResponse,
    OAuthCallback, OAuthProvider
)
from auth.security import (
    JWTManager, verify_password, get_password_hash, generate_secure_token,
    create_email_verification_token, create_password_reset_token,
    verify_email_token, verify_password_reset_token, validate_password_strength
)
from auth.dependencies import (
    get_current_user, get_current_active_user, get_current_verified_user,
    require_admin, auth_rate_limit, api_rate_limit
)
from services.email_service import EmailService
from services.oauth_service import OAuthService
from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ===================================
# INSCRIPTION ET CONNEXION
# ===================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    _: Any = Depends(auth_rate_limit)
):
    """
    Inscription d'un nouvel utilisateur
    """
    # Vérifier si l'email existe déjà
    if auth_crud.get_user_by_email(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Vérifier si le nom d'utilisateur existe déjà
    if user_create.username and auth_crud.get_user_by_username(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà utilisé"
        )
    
    # Valider la force du mot de passe
    is_valid, errors = validate_password_strength(user_create.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mot de passe trop faible: {', '.join(errors)}"
        )
    
    # Créer l'utilisateur
    try:
        db_user = auth_crud.create_user(db, user_create)
        
        # Envoyer l'email de vérification
        if settings.SEND_VERIFICATION_EMAILS:
            verification_token = create_email_verification_token(db_user.id)
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            
            background_tasks.add_task(
                EmailService.send_verification_email,
                db_user.email,
                db_user.display_name,
                verification_url
            )
        
        return db_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
    _: Any = Depends(auth_rate_limit)
):
    """
    Connexion avec email/username et mot de passe
    """
    # Récupérer l'utilisateur
    user = auth_crud.get_user_by_email_or_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier le mot de passe
    if not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Créer les tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = JWTManager.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = JWTManager.create_refresh_token(user.id)
    
    # Sauvegarder le refresh token
    device_info = request.headers.get("User-Agent") if request else None
    ip_address = request.client.host if request and request.client else None
    auth_crud.create_refresh_token(db, user.id, refresh_token, device_info, ip_address)
    
    # Mettre à jour la dernière connexion
    auth_crud.update_last_login(db, user.id)
    
    return LoginResponse(
        user=user,
        tokens=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_refresh: TokenRefresh,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Rafraîchir un token d'accès
    """
    # Vérifier le refresh token
    db_token = auth_crud.get_refresh_token(db, token_refresh.refresh_token)
    if not db_token or not db_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur
    user = auth_crud.get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou inactif",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer un nouveau token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = JWTManager.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Créer un nouveau refresh token
    new_refresh_token = JWTManager.create_refresh_token(user.id)
    
    # Révoquer l'ancien refresh token
    auth_crud.revoke_refresh_token(db, token_refresh.refresh_token)
    
    # Sauvegarder le nouveau refresh token
    device_info = request.headers.get("User-Agent") if request else None
    ip_address = request.client.host if request and request.client else None
    auth_crud.create_refresh_token(db, user.id, new_refresh_token, device_info, ip_address)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    token_refresh: TokenRefresh,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déconnexion (révoque le refresh token)
    """
    # Révoquer le refresh token
    auth_crud.revoke_refresh_token(db, token_refresh.refresh_token)
    
    return {"message": "Déconnexion réussie"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déconnexion de tous les appareils
    """
    count = auth_crud.revoke_all_user_tokens(db, current_user.id)
    
    return {"message": f"Déconnecté de {count} appareils"}


# ===================================
# GESTION DU PROFIL UTILISATEUR
# ===================================

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer le profil de l'utilisateur actuel
    """
    # Enrichir avec les préférences et stats
    preferences = auth_crud.get_user_preferences(db, current_user.id)
    alerts_count = len(auth_crud.get_user_search_alerts(db, current_user.id))
    searches_count = len(auth_crud.get_user_saved_searches(db, current_user.id))
    
    profile_data = current_user.to_dict()
    profile_data.update({
        "preferences": preferences,
        "search_alerts_count": alerts_count,
        "saved_searches_count": searches_count,
        "display_name": current_user.display_name
    })
    
    return profile_data


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le profil de l'utilisateur actuel
    """
    updated_user = auth_crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    return updated_user


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer le compte de l'utilisateur actuel
    """
    if auth_crud.delete_user(db, current_user.id):
        return {"message": "Compte supprimé avec succès"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du compte"
        )


# ===================================
# GESTION DES MOTS DE PASSE
# ===================================

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Changer le mot de passe de l'utilisateur actuel
    """
    # Valider le nouveau mot de passe
    is_valid, errors = validate_password_strength(password_change.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nouveau mot de passe trop faible: {', '.join(errors)}"
        )
    
    # Changer le mot de passe
    if auth_crud.change_password(db, current_user.id, password_change.current_password, password_change.new_password):
        # Révoquer tous les tokens pour forcer une reconnexion
        auth_crud.revoke_all_user_tokens(db, current_user.id)
        return {"message": "Mot de passe modifié avec succès"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )


@router.post("/forgot-password")
async def forgot_password(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: Any = Depends(auth_rate_limit)
):
    """
    Demander une réinitialisation de mot de passe
    """
    user = auth_crud.get_user_by_email(db, request_data.email)
    
    # Toujours retourner succès pour éviter l'énumération d'emails
    if user and user.is_active:
        reset_token = generate_secure_token()
        auth_crud.create_password_reset(db, user.id, reset_token)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        background_tasks.add_task(
            EmailService.send_password_reset_email,
            user.email,
            user.display_name,
            reset_url
        )
    
    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Réinitialiser le mot de passe avec un token
    """
    # Valider le nouveau mot de passe
    is_valid, errors = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nouveau mot de passe trop faible: {', '.join(errors)}"
        )
    
    # Utiliser le token de réinitialisation
    if auth_crud.use_password_reset_token(db, reset_data.token, reset_data.new_password):
        return {"message": "Mot de passe réinitialisé avec succès"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide ou expiré"
        )


# ===================================
# VÉRIFICATION EMAIL
# ===================================

@router.post("/send-verification")
async def send_verification_email(
    request_data: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: Any = Depends(auth_rate_limit)
):
    """
    Renvoyer un email de vérification
    """
    user = auth_crud.get_user_by_email(db, request_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà vérifié"
        )
    
    verification_token = generate_secure_token()
    auth_crud.create_email_verification(db, user.id, verification_token)
    
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    background_tasks.add_task(
        EmailService.send_verification_email,
        user.email,
        user.display_name,
        verification_url
    )
    
    return {"message": "Email de vérification envoyé"}


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """
    Vérifier l'email avec un token
    """
    if auth_crud.use_email_verification_token(db, verification_data.token):
        return {"message": "Email vérifié avec succès"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification invalide ou expiré"
        )


# ===================================
# PRÉFÉRENCES UTILISATEUR
# ===================================

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les préférences de l'utilisateur
    """
    preferences = auth_crud.get_user_preferences(db, current_user.id)
    if not preferences:
        preferences = auth_crud.create_default_preferences(db, current_user.id)
    
    return preferences


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les préférences de l'utilisateur
    """
    preferences_data = preferences_update.dict(exclude_unset=True)
    updated_preferences = auth_crud.update_user_preferences(db, current_user.id, preferences_data)
    
    return updated_preferences


# ===================================
# ALERTES DE RECHERCHE
# ===================================

@router.get("/alerts", response_model=List[SearchAlertResponse])
async def get_search_alerts(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les alertes de recherche de l'utilisateur
    """
    return auth_crud.get_user_search_alerts(db, current_user.id)


@router.post("/alerts", response_model=SearchAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_search_alert(
    alert_create: SearchAlertCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle alerte de recherche
    """
    alert_data = alert_create.dict()
    return auth_crud.create_search_alert(db, current_user.id, alert_data)


@router.put("/alerts/{alert_id}", response_model=SearchAlertResponse)
async def update_search_alert(
    alert_id: int,
    alert_update: SearchAlertUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une alerte de recherche
    """
    update_data = alert_update.dict(exclude_unset=True)
    updated_alert = auth_crud.update_search_alert(db, alert_id, current_user.id, update_data)
    
    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte introuvable"
        )
    
    return updated_alert


@router.delete("/alerts/{alert_id}")
async def delete_search_alert(
    alert_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une alerte de recherche
    """
    if auth_crud.delete_search_alert(db, alert_id, current_user.id):
        return {"message": "Alerte supprimée"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte introuvable"
        )


# ===================================
# RECHERCHES SAUVEGARDÉES
# ===================================

@router.get("/saved-searches", response_model=List[SavedSearchResponse])
async def get_saved_searches(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les recherches sauvegardées
    """
    return auth_crud.get_user_saved_searches(db, current_user.id)


@router.post("/saved-searches", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    search_create: SavedSearchCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle recherche sauvegardée
    """
    return auth_crud.create_saved_search(
        db, current_user.id, search_create.name, search_create.search_params
    )


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une recherche sauvegardée
    """
    if auth_crud.delete_saved_search(db, search_id, current_user.id):
        return {"message": "Recherche supprimée"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recherche introuvable"
        )


# ===================================
# OAUTH PROVIDERS
# ===================================

@router.get("/oauth/providers", response_model=List[OAuthProvider])
async def get_oauth_providers():
    """
    Récupérer la liste des providers OAuth disponibles
    """
    return OAuthService.get_available_providers()


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(provider: str):
    """
    Redirection vers le provider OAuth
    """
    auth_url = OAuthService.get_authorization_url(provider)
    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider OAuth non supporté"
        )
    
    return {"authorization_url": auth_url}


@router.post("/oauth/{provider}/callback", response_model=LoginResponse)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Traiter le callback OAuth
    """
    try:
        # Échanger le code contre un token
        oauth_user_data = await OAuthService.exchange_code_for_token(provider, callback_data.code)
        
        # Rechercher un compte OAuth existant
        oauth_account = auth_crud.get_oauth_account(db, provider, oauth_user_data["id"])
        
        if oauth_account:
            # Utilisateur existant
            user = oauth_account.user
        else:
            # Vérifier si un utilisateur avec cet email existe
            user = auth_crud.get_user_by_email(db, oauth_user_data["email"])
            
            if not user:
                # Créer un nouvel utilisateur
                user_create_data = {
                    "email": oauth_user_data["email"],
                    "first_name": oauth_user_data.get("first_name"),
                    "last_name": oauth_user_data.get("last_name"),
                    "full_name": oauth_user_data.get("name"),
                    "is_verified": True  # OAuth emails sont considérés vérifiés
                }
                
                # Créer l'utilisateur sans mot de passe (OAuth only)
                user = User(**user_create_data)
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Créer les préférences par défaut
                auth_crud.create_default_preferences(db, user.id)
            
            # Créer le lien OAuth
            auth_crud.create_oauth_account(
                db, user.id, provider, oauth_user_data["id"], 
                oauth_user_data["email"], oauth_user_data
            )
        
        # Vérifier que l'utilisateur est actif
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé"
            )
        
        # Créer les tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = JWTManager.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        refresh_token = JWTManager.create_refresh_token(user.id)
        
        # Sauvegarder le refresh token
        device_info = request.headers.get("User-Agent")
        ip_address = request.client.host if request.client else None
        auth_crud.create_refresh_token(db, user.id, refresh_token, device_info, ip_address)
        
        # Mettre à jour la dernière connexion
        auth_crud.update_last_login(db, user.id)
        
        return LoginResponse(
            user=user,
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            message="Connexion OAuth réussie"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur OAuth: {str(e)}"
        )


# ===================================
# ADMINISTRATION (Admin uniquement)
# ===================================

@router.get("/admin/users", response_model=UserList)
async def get_users_admin(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    role: UserRole = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des utilisateurs (admin)
    """
    users, total = auth_crud.get_users_list(db, skip, limit, search, role)
    pages = (total + limit - 1) // limit
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=pages
    )


@router.get("/admin/stats")
async def get_user_stats_admin(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Récupérer les statistiques des utilisateurs (admin)
    """
    return auth_crud.get_user_stats(db)


@router.put("/admin/users/{user_id}/role")
async def update_user_role_admin(
    user_id: int,
    new_role: UserRole,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Modifier le rôle d'un utilisateur (admin)
    """
    updated_user = auth_crud.update_user_role(db, user_id, new_role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    return {"message": f"Rôle mis à jour vers {new_role.value}", "user": updated_user}


@router.post("/admin/users/{user_id}/deactivate")
async def deactivate_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Désactiver un utilisateur (admin)
    """
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de se désactiver soi-même"
        )
    
    deactivated_user = auth_crud.deactivate_user(db, user_id)
    if not deactivated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    return {"message": "Utilisateur désactivé", "user": deactivated_user}