"""
Remove category_id from services table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_category_id_from_services'
down_revision = 'add_service_type_to_appointments'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('service', 'category_id')

def downgrade():
    op.add_column('service', sa.Column('category_id', sa.Integer(), nullable=True))
    # Note: This downgrade won't restore the foreign key constraint or data