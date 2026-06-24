"""Initial migration.

Revision ID: 001
Revises:
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('capacity_kw', sa.Float(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('contact_name', sa.String(length=50), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_stations_code'), 'stations', ['code'], unique=True)
    op.create_index(op.f('ix_stations_id'), 'stations', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stations_id'), table_name='stations')
    op.drop_index(op.f('ix_stations_code'), table_name='stations')
    op.drop_table('stations')
