"""Add users table and performance indexes

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User Role Enum
    user_role_enum = postgresql.ENUM('user', 'admin', name='user_role_enum', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Users 테이블 생성
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('role', postgresql.ENUM('user', 'admin', name='user_role_enum', create_type=False), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_key', sa.String(length=64), nullable=True),
        sa.Column('api_key_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Users 테이블 인덱스
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_api_key', 'users', ['api_key'], unique=True)

    # 성능 최적화 인덱스 추가

    # Species 테이블 추가 인덱스
    # 복합 인덱스: 카테고리 + 국가 필터링
    op.create_index(
        'ix_species_category_country',
        'species',
        ['category', 'country'],
        unique=False
    )

    # 복합 인덱스: 보전 상태 + 검색 수
    op.create_index(
        'ix_species_conservation_search',
        'species',
        ['conservation_status', 'search_count'],
        unique=False
    )

    # 부분 인덱스: 멸종위기종만 (PostgreSQL 전용)
    op.execute("""
        CREATE INDEX ix_species_endangered
        ON species (region, search_count DESC)
        WHERE conservation_status IN ('멸종위기', '취약')
    """)

    # 텍스트 검색을 위한 GIN 인덱스 (PostgreSQL 전용)
    op.execute("""
        CREATE INDEX ix_species_name_trgm
        ON species
        USING gin (name gin_trgm_ops)
    """)

    op.execute("""
        CREATE INDEX ix_species_scientific_name_trgm
        ON species
        USING gin (scientific_name gin_trgm_ops)
    """)

    # SearchQuery 테이블 인덱스
    op.create_index(
        'ix_search_query_count_desc',
        'search_queries',
        [sa.text('search_count DESC')],
        unique=False
    )

    # RegionBiodiversity 복합 인덱스
    op.create_index(
        'ix_region_country_species',
        'region_biodiversity',
        ['country', 'total_species_count'],
        unique=False
    )


def downgrade() -> None:
    # 인덱스 삭제
    op.drop_index('ix_region_country_species', table_name='region_biodiversity')
    op.drop_index('ix_search_query_count_desc', table_name='search_queries')

    op.execute('DROP INDEX IF EXISTS ix_species_scientific_name_trgm')
    op.execute('DROP INDEX IF EXISTS ix_species_name_trgm')
    op.execute('DROP INDEX IF EXISTS ix_species_endangered')

    op.drop_index('ix_species_conservation_search', table_name='species')
    op.drop_index('ix_species_category_country', table_name='species')

    # Users 테이블 인덱스 삭제
    op.drop_index('ix_users_api_key', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')

    # Users 테이블 삭제
    op.drop_table('users')

    # Enum 삭제
    op.execute('DROP TYPE IF EXISTS user_role_enum')
