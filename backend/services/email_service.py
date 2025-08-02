"""
Service d'envoi d'emails
Gestion des emails de vérification, notifications, etc.
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import smtplib
import ssl
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger

from core.config import settings


class EmailService:
    """Service centralisé pour l'envoi d'emails"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.use_ssl = settings.SMTP_SSL
        
        # Configuration Jinja2 pour les templates
        template_dir = Path(__file__).parent.parent / settings.EMAIL_TEMPLATES_DIR
        template_dir.mkdir(exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def _get_smtp_connection(self):
        """Créer une connexion SMTP"""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            return server
        except Exception as e:
            logger.error(f"Erreur connexion SMTP: {e}")
            raise
    
    def _render_template(self, template_name: str, context: dict) -> tuple[str, str]:
        """Rendre un template email (HTML et text)"""
        try:
            # Template HTML
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**context)
            
            # Template texte (optionnel)
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**context)
            except:
                # Fallback: extraire le texte du HTML
                import re
                text_content = re.sub('<[^<]+?>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return html_content, text_content
        except Exception as e:
            logger.error(f"Erreur rendu template {template_name}: {e}")
            raise
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        from_email: str = None,
        from_name: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Envoyer un email
        
        Args:
            to_email: Email destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML
            text_content: Contenu texte (optionnel)
            from_email: Email expéditeur (par défaut: settings.EMAIL_FROM)
            from_name: Nom expéditeur (par défaut: settings.EMAIL_FROM_NAME)
            cc: Liste emails en copie
            bcc: Liste emails en copie cachée
            attachments: Liste des pièces jointes
        """
        if not settings.SEND_VERIFICATION_EMAILS:
            logger.info(f"Email désactivé: {subject} -> {to_email}")
            return True
        
        try:
            # Configuration par défaut
            from_email = from_email or settings.EMAIL_FROM
            from_name = from_name or settings.EMAIL_FROM_NAME
            
            # Créer le message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Ajouter le contenu texte
            if text_content:
                text_part = MimeText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Ajouter le contenu HTML
            html_part = MimeText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Ajouter les pièces jointes
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Préparer la liste des destinataires
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Envoyer l'email
            with self._get_smtp_connection() as server:
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Email envoyé: {subject} -> {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email {subject} -> {to_email}: {e}")
            return False
    
    def _add_attachment(self, msg: MimeMultipart, attachment: Dict[str, Any]):
        """Ajouter une pièce jointe au message"""
        try:
            if 'content' in attachment:
                # Contenu en mémoire
                part = MimeBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
            elif 'filepath' in attachment:
                # Fichier sur disque
                with open(attachment['filepath'], 'rb') as f:
                    part = MimeBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
            else:
                raise ValueError("Pièce jointe invalide: 'content' ou 'filepath' requis")
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.get("filename", "attachment")}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Erreur ajout pièce jointe: {e}")
    
    def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        **kwargs
    ) -> bool:
        """Envoyer un email basé sur un template"""
        try:
            html_content, text_content = self._render_template(template_name, context)
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Erreur envoi template {template_name}: {e}")
            return False
    
    # ===================================
    # EMAILS PRÉDÉFINIS
    # ===================================
    
    @classmethod
    def send_verification_email(
        cls,
        user_email: str,
        user_name: str,
        verification_url: str
    ) -> bool:
        """Envoyer un email de vérification"""
        service = cls()
        
        context = {
            'user_name': user_name,
            'verification_url': verification_url,
            'app_name': settings.PROJECT_NAME,
            'app_url': settings.FRONTEND_URL
        }
        
        return service.send_template_email(
            to_email=user_email,
            subject=f"Vérifiez votre email - {settings.PROJECT_NAME}",
            template_name="verification",
            context=context
        )
    
    @classmethod
    def send_password_reset_email(
        cls,
        user_email: str,
        user_name: str,
        reset_url: str
    ) -> bool:
        """Envoyer un email de réinitialisation de mot de passe"""
        service = cls()
        
        context = {
            'user_name': user_name,
            'reset_url': reset_url,
            'app_name': settings.PROJECT_NAME,
            'app_url': settings.FRONTEND_URL
        }
        
        return service.send_template_email(
            to_email=user_email,
            subject=f"Réinitialisation de mot de passe - {settings.PROJECT_NAME}",
            template_name="password_reset",
            context=context
        )
    
    @classmethod
    def send_welcome_email(
        cls,
        user_email: str,
        user_name: str
    ) -> bool:
        """Envoyer un email de bienvenue"""
        service = cls()
        
        context = {
            'user_name': user_name,
            'app_name': settings.PROJECT_NAME,
            'app_url': settings.FRONTEND_URL,
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'support_email': settings.ADMIN_EMAIL
        }
        
        return service.send_template_email(
            to_email=user_email,
            subject=f"Bienvenue sur {settings.PROJECT_NAME} !",
            template_name="welcome",
            context=context
        )
    
    @classmethod
    def send_job_alert_email(
        cls,
        user_email: str,
        user_name: str,
        alert_name: str,
        jobs: List[dict],
        alert_url: str
    ) -> bool:
        """Envoyer une alerte d'emploi"""
        service = cls()
        
        context = {
            'user_name': user_name,
            'alert_name': alert_name,
            'jobs': jobs,
            'jobs_count': len(jobs),
            'alert_url': alert_url,
            'app_name': settings.PROJECT_NAME,
            'app_url': settings.FRONTEND_URL
        }
        
        return service.send_template_email(
            to_email=user_email,
            subject=f"Nouvelles offres d'emploi - {alert_name}",
            template_name="job_alert",
            context=context
        )
    
    @classmethod
    def send_account_deactivation_email(
        cls,
        user_email: str,
        user_name: str,
        reason: str = None
    ) -> bool:
        """Envoyer un email de désactivation de compte"""
        service = cls()
        
        context = {
            'user_name': user_name,
            'reason': reason,
            'app_name': settings.PROJECT_NAME,
            'support_email': settings.ADMIN_EMAIL
        }
        
        return service.send_template_email(
            to_email=user_email,
            subject=f"Compte désactivé - {settings.PROJECT_NAME}",
            template_name="account_deactivation",
            context=context
        )
    
    @classmethod
    def send_admin_notification(
        cls,
        subject: str,
        message: str,
        data: dict = None
    ) -> bool:
        """Envoyer une notification aux administrateurs"""
        service = cls()
        
        context = {
            'message': message,
            'data': data,
            'app_name': settings.PROJECT_NAME,
            'app_url': settings.BACKEND_URL
        }
        
        return service.send_template_email(
            to_email=settings.ADMIN_EMAIL,
            subject=f"[ADMIN] {subject}",
            template_name="admin_notification",
            context=context
        )
    
    # ===================================
    # EMAILS BATCH
    # ===================================
    
    @classmethod
    async def send_bulk_emails(
        cls,
        emails: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[bool]:
        """
        Envoyer plusieurs emails en parallèle
        
        Args:
            emails: Liste de dictionnaires avec les paramètres d'email
            max_concurrent: Nombre maximum d'emails envoyés en parallèle
        """
        service = cls()
        
        async def send_single_email(email_params):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                service.send_email, 
                **email_params
            )
        
        # Créer un semaphore pour limiter la concurrence
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_with_semaphore(email_params):
            async with semaphore:
                return await send_single_email(email_params)
        
        # Exécuter tous les envois
        tasks = [send_with_semaphore(email) for email in emails]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        success_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erreur email {i}: {result}")
                success_results.append(False)
            else:
                success_results.append(result)
        
        return success_results
    
    # ===================================
    # UTILITAIRES
    # ===================================
    
    @classmethod
    def validate_email_config(cls) -> bool:
        """Valider la configuration email"""
        if not all([
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.EMAIL_FROM
        ]):
            return False
        
        # Test de connexion SMTP
        try:
            service = cls()
            with service._get_smtp_connection() as server:
                logger.info("Configuration email validée")
                return True
        except Exception as e:
            logger.error(f"Configuration email invalide: {e}")
            return False
    
    @classmethod
    def create_default_templates(cls):
        """Créer les templates d'email par défaut"""
        template_dir = Path(__file__).parent.parent / settings.EMAIL_TEMPLATES_DIR
        template_dir.mkdir(exist_ok=True)
        
        # Template de vérification
        verification_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vérification email</title>
</head>
<body>
    <h1>Bonjour {{ user_name }},</h1>
    <p>Merci de vous être inscrit sur {{ app_name }} !</p>
    <p>Pour terminer votre inscription, veuillez cliquer sur le lien ci-dessous :</p>
    <a href="{{ verification_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
        Vérifier mon email
    </a>
    <p>Ce lien expire dans 24 heures.</p>
    <p>Si vous n'avez pas demandé cette inscription, ignorez cet email.</p>
    <hr>
    <p><small>{{ app_name }} - <a href="{{ app_url }}">{{ app_url }}</a></small></p>
</body>
</html>
        """
        
        (template_dir / "verification.html").write_text(verification_html, encoding="utf-8")
        
        # Template de réinitialisation
        reset_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Réinitialisation mot de passe</title>
</head>
<body>
    <h1>Bonjour {{ user_name }},</h1>
    <p>Vous avez demandé une réinitialisation de votre mot de passe sur {{ app_name }}.</p>
    <p>Cliquez sur le lien ci-dessous pour choisir un nouveau mot de passe :</p>
    <a href="{{ reset_url }}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
        Réinitialiser mon mot de passe
    </a>
    <p>Ce lien expire dans 2 heures.</p>
    <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
    <hr>
    <p><small>{{ app_name }} - <a href="{{ app_url }}">{{ app_url }}</a></small></p>
</body>
</html>
        """
        
        (template_dir / "password_reset.html").write_text(reset_html, encoding="utf-8")
        
        logger.info(f"Templates par défaut créés dans {template_dir}")


# Créer les templates par défaut au démarrage
EmailService.create_default_templates()