"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Explicit table creation for initial migration
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email', name='uq_users_email')
    )

    op.create_table(
        'words',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('lemma', sa.String(), nullable=False),
        sa.Column('pos', sa.String(length=32), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('pronunciation', sa.Text(), nullable=True),
        sa.Column('example', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('lemma', name='uq_words_lemma')
    )

    op.create_table(
        'uploads',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('filename', sa.Text(), nullable=True),
        sa.Column('storage_path', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'ocr_results',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('upload_id', sa.String(), sa.ForeignKey('uploads.id', ondelete='CASCADE')),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.Column('plain_text', sa.Text(), nullable=True),
        sa.Column('words_extracted', sa.Text(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'user_words',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('word_id', sa.String(), sa.ForeignKey('words.id', ondelete='CASCADE')),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_review_at', sa.DateTime(), nullable=True),
        sa.Column('next_review_at', sa.DateTime(), nullable=True),
        sa.Column('ease_factor', sa.Float(), nullable=True, server_default='2.5'),
        sa.Column('interval_hours', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('performance_history', sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table('user_words')
    op.drop_table('ocr_results')
    op.drop_table('uploads')
    op.drop_table('words')
    op.drop_table('users')
