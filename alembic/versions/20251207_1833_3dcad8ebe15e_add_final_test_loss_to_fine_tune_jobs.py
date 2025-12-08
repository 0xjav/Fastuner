"""add_final_test_loss_to_fine_tune_jobs

Revision ID: 3dcad8ebe15e
Revises: 8ce190d90605
Create Date: 2025-12-07 18:33:24.418715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dcad8ebe15e'
down_revision = '8ce190d90605'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add final_test_loss column to fine_tune_jobs table
    op.add_column('fine_tune_jobs', sa.Column('final_test_loss', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove final_test_loss column from fine_tune_jobs table
    op.drop_column('fine_tune_jobs', 'final_test_loss')
