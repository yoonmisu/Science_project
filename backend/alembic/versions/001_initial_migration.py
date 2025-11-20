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
    # Create category enum
    category_enum = postgresql.ENUM(
        '식물', '동물', '곤충', '해양생물',
        name='categoryenum',
        create_type=True
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    # Create conservation status enum
    conservation_enum = postgresql.ENUM(
        '멸종위기', '취약', '준위협', '관심대상', '안전',
        name='conservationstatusenum',
        create_type=True
    )
    conservation_enum.create(op.get_bind(), checkfirst=True)

    # Create species table
    op.create_table(
        'species',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('scientific_name', sa.String(200), nullable=True),
        sa.Column('category', category_enum, nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('characteristics', sa.JSON(), nullable=True),
        sa.Column('conservation_status', conservation_enum, nullable=True, server_default='안전'),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('search_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for species
    op.create_index('ix_species_id', 'species', ['id'], unique=False)
    op.create_index('ix_species_name', 'species', ['name'], unique=False)
    op.create_index('ix_species_scientific_name', 'species', ['scientific_name'], unique=False)
    op.create_index('ix_species_category', 'species', ['category'], unique=False)
    op.create_index('ix_species_region', 'species', ['region'], unique=False)
    op.create_index('ix_species_country', 'species', ['country'], unique=False)
    op.create_index('ix_species_conservation_status', 'species', ['conservation_status'], unique=False)
    op.create_index('ix_species_search_count', 'species', ['search_count'], unique=False)
    op.create_index('ix_species_category_country', 'species', ['category', 'country'], unique=False)
    op.create_index('ix_species_country_region', 'species', ['country', 'region'], unique=False)
    op.create_index('ix_species_conservation_category', 'species', ['conservation_status', 'category'], unique=False)

    # Create search_queries table
    op.create_table(
        'search_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(200), nullable=False),
        sa.Column('search_count', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('last_searched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for search_queries
    op.create_index('ix_search_queries_id', 'search_queries', ['id'], unique=False)
    op.create_index('ix_search_queries_query_text', 'search_queries', ['query_text'], unique=False)
    op.create_index('ix_search_query_count', 'search_queries', ['search_count'], unique=False)
    op.create_index('ix_search_query_text_category', 'search_queries', ['query_text', 'category'], unique=False)

    # Create region_biodiversity table
    op.create_table(
        'region_biodiversity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('total_species_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('endangered_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('plant_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('animal_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('insect_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('marine_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('region_name')
    )

    # Create indexes for region_biodiversity
    op.create_index('ix_region_biodiversity_id', 'region_biodiversity', ['id'], unique=False)
    op.create_index('ix_region_biodiversity_region_name', 'region_biodiversity', ['region_name'], unique=False)
    op.create_index('ix_region_country', 'region_biodiversity', ['country'], unique=False)
    op.create_index('ix_region_coords', 'region_biodiversity', ['latitude', 'longitude'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('region_biodiversity')
    op.drop_table('search_queries')
    op.drop_table('species')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS conservationstatusenum')
    op.execute('DROP TYPE IF EXISTS categoryenum')
