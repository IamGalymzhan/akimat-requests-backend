"""create_user_status_enum

Revision ID: 7610fb8ae5f7
Revises: add_user_registration_fields
Create Date: 2025-03-11 23:45:08.071030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7610fb8ae5f7'
down_revision = 'add_user_registration_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing enum type if it exists
    op.execute('DROP TYPE IF EXISTS user_status CASCADE')
    
    # Create the enum type with lowercase values
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'pending', 'inactive')")
    
    # Add the status column if it doesn't exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='status'
        ) THEN
            ALTER TABLE users ADD COLUMN status user_status NOT NULL DEFAULT 'pending';
        END IF;
    END$$;
    """)

def downgrade():
    # Drop the column if it exists
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='status'
        ) THEN
            ALTER TABLE users DROP COLUMN status;
        END IF;
    END$$;
    """)
    
    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS user_status')
