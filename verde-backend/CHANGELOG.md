# Changelog

이 프로젝트의 모든 주요 변경 사항을 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### 예정
- 사용자 인증 시스템
- 즐겨찾기 기능
- 종 이미지 갤러리
- 다국어 지원

---

## [1.0.0] - 2024-01-XX

### Added (추가)

#### Core Features
- **종(Species) 관리 API**
  - 종 목록 조회 (페이지네이션, 필터링, 정렬)
  - 종 상세 조회
  - 오늘의 랜덤 종 (24시간 캐시)
  - 인기 종 목록 (30분 캐시)
  - 종 CRUD 작업

- **검색 시스템**
  - 실시간 검색어 랭킹 (Redis Sorted Set)
  - 검색어 자동완성
  - 인기 검색어 Top 10
  - 카테고리별 검색

- **지역별 통계**
  - 지역 목록 조회
  - 지역별 종 목록
  - 지역별 생물 다양성 통계 (1시간 캐시)

- **멸종위기종 API**
  - 멸종위기종 목록 (멸종위기, 취약)
  - 가장 많이 조회된 멸종위기종 Top 10
  - 보전 상태별 통계
  - 지역별 멸종위기종

#### Infrastructure
- **데이터베이스**
  - PostgreSQL 15 지원
  - SQLAlchemy 2.0 ORM
  - Alembic 마이그레이션
  - 연결 풀링 (pool_size=10, max_overflow=20)

- **캐싱 시스템**
  - Redis 7 연동
  - 다양한 TTL 설정 (5분 ~ 24시간)
  - Sorted Set을 활용한 실시간 랭킹
  - 패턴 기반 캐시 무효화

- **API 서버**
  - FastAPI 0.115
  - Pydantic 2.0 검증
  - CORS 설정
  - Swagger UI / ReDoc 문서

- **배포**
  - Docker 멀티스테이지 빌드
  - docker-compose 구성 (nginx, app, db, redis)
  - Nginx 리버스 프록시
  - Railway 배포 지원

#### Documentation
- README.md 작성
- CONTRIBUTING.md 작성
- API 문서 자동 생성 (Swagger UI)
- 환경변수 가이드 (.env.example)

#### Testing
- pytest 테스트 프레임워크
- 92개 테스트 케이스
- 비동기 테스트 지원 (pytest-asyncio)
- Mock Redis 지원

### Security
- 비root 사용자로 Docker 컨테이너 실행
- Rate limiting (API: 10r/s, Search: 5r/s)
- HTTPS/TLS 지원
- 보안 헤더 설정 (HSTS, X-Frame-Options, etc.)
- SQL Injection 방지 (SQLAlchemy ORM)

---

## [0.1.0] - 2024-01-XX

### Added
- 프로젝트 초기 설정
- 기본 프로젝트 구조 생성
- FastAPI 애플리케이션 스캐폴딩
- 데이터베이스 모델 정의
- 초기 API 엔드포인트 구현

---

## 버전 관리 규칙

### 버전 번호

`MAJOR.MINOR.PATCH`

- **MAJOR**: 하위 호환성이 없는 API 변경
- **MINOR**: 하위 호환성 있는 기능 추가
- **PATCH**: 하위 호환성 있는 버그 수정

### 변경 사항 유형

- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련 수정

---

## 기여자

모든 기여자분들께 감사드립니다!

<!-- Contributors will be listed here -->

---

[Unreleased]: https://github.com/your-username/verde-backend/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-username/verde-backend/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/your-username/verde-backend/releases/tag/v0.1.0
