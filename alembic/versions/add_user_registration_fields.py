"""add user registration fields

Revision ID: add_user_registration_fields
Revises: add_iin_to_user
Create Date: 2023-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_registration_fields'
down_revision = 'add_iin_to_user'  # Update this to match your actual last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create user_status enum type
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'pending', 'inactive')")
    
    # Add new columns to the users table
    op.add_column('users', sa.Column('status', sa.Enum('active', 'pending', 'inactive', name='user_status'), nullable=False, server_default='pending'))
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('organization', sa.String(), nullable=True))
    op.add_column('users', sa.Column('position', sa.String(), nullable=True))


def downgrade():
    # Remove the columns
    op.drop_column('users', 'status')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'organization')
    op.drop_column('users', 'position')
    
    # Drop the enum type
    op.execute("DROP TYPE user_status") 