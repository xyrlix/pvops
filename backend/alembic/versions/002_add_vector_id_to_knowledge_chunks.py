"""add vector_id to knowledge_chunks.

Revision ID: 002
Revises: 001
Create Date: 2026-06-24

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_chunks", sa.Column("vector_id", sa.String(length=64), nullable=True))
    op.create_index(
        op.f("ix_knowledge_chunks_vector_id"), "knowledge_chunks", ["vector_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_chunks_vector_id"), table_name="knowledge_chunks")
    op.drop_column("knowledge_chunks", "vector_id")
