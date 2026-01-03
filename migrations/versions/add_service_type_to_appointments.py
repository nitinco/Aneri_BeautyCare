"""
Add service_type column to appointments table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_service_type_to_appointments'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('appointment', sa.Column('service_type', sa.String(length=10), nullable=False, server_default='salon'))

def downgrade():
    op.drop_column('appointment', 'service_type')