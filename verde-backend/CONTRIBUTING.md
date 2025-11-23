# 기여 가이드

Verde 프로젝트에 기여해 주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 목차

- [행동 강령](#행동-강령)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일 가이드](#코드-스타일-가이드)
- [커밋 메시지 규칙](#커밋-메시지-규칙)
- [Pull Request 가이드](#pull-request-가이드)
- [이슈 리포팅](#이슈-리포팅)

## 행동 강령

- 모든 기여자를 존중하고 건설적인 피드백을 제공합니다
- 다양한 관점과 경험을 환영합니다
- 커뮤니티에 긍정적인 환경을 조성합니다

## 기여 방법

### 1. 이슈 확인

기여하기 전에 먼저 [Issues](https://github.com/your-username/verde-backend/issues)를 확인하세요:
- 버그 리포트
- 기능 요청
- 문서 개선

### 2. Fork & Clone

```bash
# 저장소 Fork
# GitHub에서 Fork 버튼 클릭

# 로컬에 Clone
git clone https://github.com/your-username/verde-backend.git
cd verde-backend

# Upstream 설정
git remote add upstream https://github.com/original/verde-backend.git
```

### 3. 브랜치 생성

```bash
# 최신 main 브랜치로 업데이트
git checkout main
git pull upstream main

# 새 브랜치 생성
git checkout -b feature/your-feature-name
```

## 개발 환경 설정

### 필수 요구사항

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (권장)

### 로컬 개발 환경

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 의존성

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 수정

# 4. 데이터베이스 마이그레이션
alembic upgrade head

# 5. 개발 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Docker 개발 환경

```bash
docker-compose up -d
docker-compose exec app alembic upgrade head
```

## 코드 스타일 가이드

### Python 코드 스타일

#### 기본 규칙

- **PEP 8** 준수
- **Black** 포매터 사용 (line-length: 88)
- **isort**로 import 정렬
- **Type hints** 필수

#### 예시

```python
# Good
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.species import Species
from app.schemas.species import SpeciesCreate, SpeciesResponse


router = APIRouter(prefix="/species", tags=["species"])


async def get_species_by_id(
    species_id: int,
    db: Session = Depends(get_db)
) -> Optional[Species]:
    """
    ID로 종 정보를 조회합니다.

    Args:
        species_id: 종 ID
        db: 데이터베이스 세션

    Returns:
        Species 객체 또는 None
    """
    return db.query(Species).filter(Species.id == species_id).first()
```

#### Import 순서

```python
# 1. 표준 라이브러리
import json
from datetime import datetime
from typing import List, Optional

# 2. 서드파티 라이브러리
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. 로컬 모듈
from app.database import get_db
from app.models import Species
```

### 네이밍 규칙

| 종류 | 규칙 | 예시 |
|------|------|------|
| 변수/함수 | snake_case | `species_count`, `get_species_list()` |
| 클래스 | PascalCase | `Species`, `SpeciesResponse` |
| 상수 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE`, `CACHE_TTL` |
| 파일명 | snake_case | `species_service.py` |

### 문서화

#### Docstring 형식

```python
def search_species(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> List[Species]:
    """
    종을 검색합니다.

    Args:
        query: 검색어
        category: 카테고리 필터 (선택)
        limit: 최대 결과 수

    Returns:
        검색 결과 Species 리스트

    Raises:
        ValueError: 검색어가 비어있는 경우

    Example:
        >>> results = search_species("호랑이", category="동물")
        >>> len(results)
        5
    """
```

### API 엔드포인트 규칙

```python
@router.get(
    "/{species_id}",
    response_model=SpeciesResponse,
    summary="종 상세 조회",
    description="ID로 특정 종의 상세 정보를 조회합니다.",
    responses={
        200: {"description": "성공"},
        404: {"description": "종을 찾을 수 없음"}
    }
)
async def get_species(
    species_id: int = Path(..., description="종 ID", ge=1),
    db: Session = Depends(get_db)
):
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
```

### 테스트 코드 규칙

```python
import pytest
from httpx import AsyncClient

class TestSpeciesAPI:
    """Species API 테스트"""

    @pytest.mark.asyncio
    async def test_get_species_list_success(
        self,
        client: AsyncClient,
        sample_species: dict
    ):
        """종 목록 조회 성공 테스트"""
        # Given
        # (sample_species fixture로 데이터 준비)

        # When
        response = await client.get("/api/v1/species")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
```

## 커밋 메시지 규칙

### 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

| Type | 설명 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `style` | 코드 포맷팅 (기능 변경 없음) |
| `refactor` | 코드 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 파일 수정 |
| `perf` | 성능 개선 |

### Scope (선택)

- `species` - 종 관련
- `search` - 검색 관련
- `region` - 지역 관련
- `cache` - 캐싱 관련
- `db` - 데이터베이스 관련
- `api` - API 전반

### 예시

```bash
# 기능 추가
feat(species): 종 검색 자동완성 기능 추가

검색어 입력 시 실시간으로 추천 검색어를 제공합니다.
- Redis Sorted Set을 활용한 실시간 랭킹
- 최대 10개 추천어 반환

Closes #123

# 버그 수정
fix(cache): Redis 연결 타임아웃 문제 해결

연결 풀 설정을 조정하여 타임아웃 오류를 방지합니다.

# 문서 수정
docs: API 엔드포인트 문서 업데이트

# 리팩토링
refactor(search): 검색 서비스 코드 정리

중복 코드를 제거하고 함수를 분리했습니다.
```

## Pull Request 가이드

### PR 생성 전 체크리스트

- [ ] 코드가 스타일 가이드를 따르는지 확인
- [ ] 모든 테스트가 통과하는지 확인 (`pytest`)
- [ ] 새 기능에 대한 테스트 추가
- [ ] 문서 업데이트 (필요한 경우)
- [ ] 커밋 메시지 규칙 준수

### PR 템플릿

```markdown
## 변경 사항
<!-- 이 PR에서 변경한 내용을 설명하세요 -->

## 관련 이슈
<!-- 관련 이슈가 있다면 링크하세요 -->
Closes #이슈번호

## 테스트 방법
<!-- 변경 사항을 테스트하는 방법을 설명하세요 -->

## 체크리스트
- [ ] 테스트 추가/수정
- [ ] 문서 업데이트
- [ ] 코드 리뷰 요청
```

### 코드 리뷰

- 최소 1명의 리뷰어 승인 필요
- 모든 CI 테스트 통과 필수
- 리뷰어의 피드백에 응답

## 이슈 리포팅

### 버그 리포트

```markdown
## 버그 설명
<!-- 버그에 대해 간단히 설명하세요 -->

## 재현 방법
1. '...'로 이동
2. '...' 클릭
3. '...' 스크롤
4. 에러 발생

## 예상 동작
<!-- 예상했던 동작을 설명하세요 -->

## 스크린샷
<!-- 해당되는 경우 스크린샷을 추가하세요 -->

## 환경
- OS: [예: macOS 14.0]
- Python: [예: 3.11.5]
- 브라우저: [예: Chrome 120]
```

### 기능 요청

```markdown
## 기능 설명
<!-- 원하는 기능을 설명하세요 -->

## 사용 사례
<!-- 이 기능이 필요한 이유를 설명하세요 -->

## 대안
<!-- 고려한 대안이 있다면 설명하세요 -->
```

## 개발 도구

### 권장 도구

- **IDE**: VS Code, PyCharm
- **포매터**: Black
- **린터**: Flake8, pylint
- **타입 체커**: mypy

### VS Code 설정

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### pre-commit 설정

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

## 질문이 있으신가요?

- [GitHub Issues](https://github.com/your-username/verde-backend/issues)에 질문을 남겨주세요
- 이메일: contact@verde.app

---

Verde 팀은 모든 기여를 환영합니다!
