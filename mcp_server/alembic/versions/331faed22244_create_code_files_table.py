"""create_code_files_table

Revision ID: 331faed22244
Revises: 
Create Date: 2025-06-19 12:25:38.217113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '331faed22244'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'code_files',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('file_path', sa.Text(), nullable=False, unique=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('parent_directory', sa.Text(), nullable=False),
        sa.Column('project_root', sa.Text(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('last_modified_at_fs', sa.DateTime(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at_db', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at_db', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_code_files_file_name'), 'code_files', ['file_name'], unique=False)
    op.create_index(op.f('ix_code_files_file_path'), 'code_files', ['file_path'], unique=True)
    op.create_index(op.f('ix_code_files_id'), 'code_files', ['id'], unique=False)
    op.create_index(op.f('ix_code_files_parent_directory'), 'code_files', ['parent_directory'], unique=False)
    op.create_index(op.f('ix_code_files_project_root'), 'code_files', ['project_root'], unique=False)
    op.create_index('ix_code_files_project_root_file_path', 'code_files', ['project_root', 'file_path'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_code_files_project_root_file_path', table_name='code_files')
    op.drop_index(op.f('ix_code_files_project_root'), table_name='code_files')
    op.drop_index(op.f('ix_code_files_parent_directory'), table_name='code_files')
    op.drop_index(op.f('ix_code_files_id'), table_name='code_files')
    op.drop_index(op.f('ix_code_files_file_path'), table_name='code_files')
    op.drop_index(op.f('ix_code_files_file_name'), table_name='code_files')
    op.drop_table('code_files')
