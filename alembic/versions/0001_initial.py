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
    # Use models' metadata to create tables (simple approach for initial migration)
    from backend.app.models import Base
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    from backend.app.models import Base
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
