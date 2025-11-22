"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types using PostgreSQL-specific ENUM
    category_enum = postgresql.ENUM('식물', '동물', '곤충', '해양생물', name='category_enum', create_type=False)
    conservation_status_enum = postgresql.ENUM('멸종위기', '취약', '준위협', '관심대상', '안전', name='conservation_status_enum', create_type=False)

    # Create the enum types in database first
    category_enum.create(op.get_bind(), checkfirst=True)
    conservation_status_enum.create(op.get_bind(), checkfirst=True)

    # Create species table
    op.create_table(
        'species',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, comment='한글명'),
        sa.Column('scientific_name', sa.String(length=200), nullable=True, comment='학명'),
        sa.Column('category', category_enum, nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False, comment='지역'),
        sa.Column('country', sa.String(length=100), nullable=False, comment='국가'),
        sa.Column('description', sa.Text(), nullable=True, comment='설명'),
        sa.Column('characteristics', sa.JSON(), nullable=True, comment='특징 리스트'),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('conservation_status', conservation_status_enum, nullable=True),
        sa.Column('search_count', sa.Integer(), nullable=False, server_default='0', comment='조회수'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Species indexes
    op.create_index(op.f('ix_species_id'), 'species', ['id'], unique=False)
    op.create_index(op.f('ix_species_name'), 'species', ['name'], unique=False)
    op.create_index(op.f('ix_species_category'), 'species', ['category'], unique=False)
    op.create_index(op.f('ix_species_region'), 'species', ['region'], unique=False)
    op.create_index(op.f('ix_species_country'), 'species', ['country'], unique=False)
    op.create_index('ix_species_country_category', 'species', ['country', 'category'], unique=False)
    op.create_index('ix_species_region_category', 'species', ['region', 'category'], unique=False)
    op.create_index('ix_species_conservation_status', 'species', ['conservation_status'], unique=False)

    # Create search_queries table
    op.create_table(
        'search_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(length=200), nullable=False),
        sa.Column('search_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_searched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Search queries indexes
    op.create_index(op.f('ix_search_queries_id'), 'search_queries', ['id'], unique=False)
    op.create_index(op.f('ix_search_queries_query_text'), 'search_queries', ['query_text'], unique=False)
    op.create_index(op.f('ix_search_queries_category'), 'search_queries', ['category'], unique=False)
    op.create_index(op.f('ix_search_queries_region'), 'search_queries', ['region'], unique=False)
    op.create_index('ix_search_queries_query_category', 'search_queries', ['query_text', 'category'], unique=False)
    op.create_index('ix_search_queries_search_count', 'search_queries', ['search_count'], unique=False)

    # Create region_biodiversity table
    op.create_table(
        'region_biodiversity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('region_name', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('total_species_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('endangered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('plant_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('animal_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('insect_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('marine_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('region_name')
    )

    # Region biodiversity indexes
    op.create_index(op.f('ix_region_biodiversity_id'), 'region_biodiversity', ['id'], unique=False)
    op.create_index(op.f('ix_region_biodiversity_region_name'), 'region_biodiversity', ['region_name'], unique=False)
    op.create_index('ix_region_biodiversity_country', 'region_biodiversity', ['country'], unique=False)
    op.create_index('ix_region_biodiversity_coords', 'region_biodiversity', ['latitude', 'longitude'], unique=False)


def downgrade() -> None:
    # Drop region_biodiversity
    op.drop_index('ix_region_biodiversity_coords', table_name='region_biodiversity')
    op.drop_index('ix_region_biodiversity_country', table_name='region_biodiversity')
    op.drop_index(op.f('ix_region_biodiversity_region_name'), table_name='region_biodiversity')
    op.drop_index(op.f('ix_region_biodiversity_id'), table_name='region_biodiversity')
    op.drop_table('region_biodiversity')

    # Drop search_queries
    op.drop_index('ix_search_queries_search_count', table_name='search_queries')
    op.drop_index('ix_search_queries_query_category', table_name='search_queries')
    op.drop_index(op.f('ix_search_queries_region'), table_name='search_queries')
    op.drop_index(op.f('ix_search_queries_category'), table_name='search_queries')
    op.drop_index(op.f('ix_search_queries_query_text'), table_name='search_queries')
    op.drop_index(op.f('ix_search_queries_id'), table_name='search_queries')
    op.drop_table('search_queries')

    # Drop species
    op.drop_index('ix_species_conservation_status', table_name='species')
    op.drop_index('ix_species_region_category', table_name='species')
    op.drop_index('ix_species_country_category', table_name='species')
    op.drop_index(op.f('ix_species_country'), table_name='species')
    op.drop_index(op.f('ix_species_region'), table_name='species')
    op.drop_index(op.f('ix_species_category'), table_name='species')
    op.drop_index(op.f('ix_species_name'), table_name='species')
    op.drop_index(op.f('ix_species_id'), table_name='species')
    op.drop_table('species')

    # Drop enum types
    postgresql.ENUM(name='conservation_status_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='category_enum').drop(op.get_bind(), checkfirst=True)
