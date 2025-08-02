"""Add authentication tables

Revision ID: 20241228_0900_0002
Revises: 20241227_1800_0001
Create Date: 2024-12-28 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20241228_0900_0002'
down_revision = '20241227_1800_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajouter les tables d'authentification"""
    
    # Table users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('role', sa.Enum('user', 'premium', 'admin', name='userrole'), nullable=False, default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), default='Europe/Paris', nullable=True),
        sa.Column('language', sa.String(10), default='fr', nullable=True),
        
        sa.Index('ix_users_email', 'email'),
        sa.Index('ix_users_username', 'username'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    
    # Table oauth_accounts
    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('provider_email', sa.String(255), nullable=True),
        sa.Column('provider_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider', 'provider_user_id'),
    )
    
    # Table refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_refresh_tokens_token_hash', 'token_hash'),
        sa.UniqueConstraint('token_hash'),
    )
    
    # Table user_preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('default_location', sa.String(200), nullable=True),
        sa.Column('preferred_job_types', sa.Text(), nullable=True),
        sa.Column('preferred_keywords', sa.Text(), nullable=True),
        sa.Column('salary_range_min', sa.Integer(), nullable=True),
        sa.Column('salary_range_max', sa.Integer(), nullable=True),
        sa.Column('remote_work_only', sa.Boolean(), default=False),
        sa.Column('theme', sa.String(20), default='light'),
        sa.Column('results_per_page', sa.Integer(), default=20),
        sa.Column('email_notifications', sa.Boolean(), default=True),
        sa.Column('push_notifications', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id'),
    )
    
    # Table search_alerts
    op.create_table(
        'search_alerts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('search_query', sa.String(500), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('job_types', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(20), default='daily'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sent', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Table saved_searches
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('search_params', sa.Text(), nullable=False),
        sa.Column('results_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Table email_verifications
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_used', sa.Boolean(), default=False),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_email_verifications_token_hash', 'token_hash'),
        sa.UniqueConstraint('token_hash'),
    )
    
    # Table password_resets
    op.create_table(
        'password_resets',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_used', sa.Boolean(), default=False),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_password_resets_token_hash', 'token_hash'),
        sa.UniqueConstraint('token_hash'),
    )


def downgrade() -> None:
    """Supprimer les tables d'authentification"""
    
    op.drop_table('password_resets')
    op.drop_table('email_verifications')
    op.drop_table('saved_searches')
    op.drop_table('search_alerts')
    op.drop_table('user_preferences')
    op.drop_table('refresh_tokens')
    op.drop_table('oauth_accounts')
    op.drop_table('users')
    
    # Supprimer l'enum
    op.execute("DROP TYPE IF EXISTS userrole")