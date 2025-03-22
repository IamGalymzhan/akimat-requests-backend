"""add IIN to user

Revision ID: add_iin_to_user
Revises: 8a82052370fa
Create Date: 2023-11-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_iin_to_user'
down_revision = '8a82052370fa'  # Update this to your actual last migration
branch_labels = None
depends_on = None


def upgrade():
    # Add the IIN column to the users table
    op.add_column('users', sa.Column('iin', sa.String(12), nullable=True))
    op.create_index(op.f('ix_users_iin'), 'users', ['iin'], unique=True)


def downgrade():
    # Remove the IIN column from the users table
    op.drop_index(op.f('ix_users_iin'), table_name='users')
    op.drop_column('users', 'iin') 