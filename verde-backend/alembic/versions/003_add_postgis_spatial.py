"""Add PostGIS spatial support

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostGIS 확장 활성화
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # species 테이블에 위도/경도 컬럼 추가
    op.add_column('species', sa.Column('latitude', sa.Float(), nullable=True, comment='위도'))
    op.add_column('species', sa.Column('longitude', sa.Float(), nullable=True, comment='경도'))

    # 공간 데이터 컬럼 추가 (Geography 타입)
    op.add_column('species', sa.Column(
        'location',
        Geography(geometry_type='POINT', srid=4326),
        nullable=True,
        comment='공간 좌표 (PostGIS)'
    ))

    # 기존 위도/경도 데이터가 있으면 location 컬럼 업데이트
    op.execute("""
        UPDATE species
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)

    # 공간 인덱스 생성 (GIST)
    op.create_index(
        'idx_species_location_gist',
        'species',
        ['location'],
        postgresql_using='gist'
    )

    # 위도/경도 인덱스 (B-tree)
    op.create_index('ix_species_latitude', 'species', ['latitude'])
    op.create_index('ix_species_longitude', 'species', ['longitude'])

    # 복합 공간 인덱스 (국가별 공간 검색 최적화)
    op.create_index(
        'idx_species_country_location',
        'species',
        ['country', 'location'],
        postgresql_using='gist'
    )


def downgrade() -> None:
    # 인덱스 제거
    op.drop_index('idx_species_country_location', table_name='species')
    op.drop_index('ix_species_longitude', table_name='species')
    op.drop_index('ix_species_latitude', table_name='species')
    op.drop_index('idx_species_location_gist', table_name='species')

    # 컬럼 제거
    op.drop_column('species', 'location')
    op.drop_column('species', 'longitude')
    op.drop_column('species', 'latitude')

    # PostGIS 확장은 다른 곳에서 사용될 수 있으므로 제거하지 않음
