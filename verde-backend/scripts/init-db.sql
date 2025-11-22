-- =============================================================================
-- Verde Database Initialization Script
-- =============================================================================

-- UTF-8 설정
SET client_encoding = 'UTF8';

-- 확장 설치 (필요시)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기본 메시지
DO $$
BEGIN
    RAISE NOTICE 'Verde database initialized successfully';
END $$;
