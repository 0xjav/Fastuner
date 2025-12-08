"""seed_default_tenant

Revision ID: 8ce190d90605
Revises: 463073b81d4f
Create Date: 2025-12-07 17:18:19.142154

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '8ce190d90605'
down_revision = '463073b81d4f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert default tenant
    op.execute(
        """
        INSERT INTO tenants (id, name, cognito_user_pool_id, created_at, updated_at)
        VALUES ('default-tenant', 'Default Tenant', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
    )


def downgrade() -> None:
    # Remove default tenant
    op.execute(
        """
        DELETE FROM tenants WHERE id = 'default-tenant'
        """
    )
