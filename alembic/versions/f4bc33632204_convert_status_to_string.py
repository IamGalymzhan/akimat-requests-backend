"""convert_status_to_string

Revision ID: f4bc33632204
Revises: 7610fb8ae5f7
Create Date: 2025-03-12 00:30:09.302287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f4bc33632204'
down_revision = '7610fb8ae5f7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'status',
               existing_type=postgresql.ENUM('active', 'pending', 'inactive', name='user_status'),
               type_=sa.String(),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'::user_status"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'status',
               existing_type=sa.String(),
               type_=postgresql.ENUM('active', 'pending', 'inactive', name='user_status'),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'::user_status"))
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
