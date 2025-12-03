# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Verde is a biodiversity data visualization web application for specific regions. It's a React/Vite frontend that displays species data across different countries and categories (Animals, Plants, Insects, Marine Life).

## Development Commands

```bash
# Start development server (localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Architecture

### Tech Stack
- **Frontend**: React 19 + Vite 7 + Styled-components
- **Icons**: Lucide React
- **Build**: Vite with React SWC plugin

### Application Flow
- Entry: `src/main.jsx` → `src/App.jsx` → `src/pages/home.jsx`
- `App.jsx` handles backend connectivity (expects API at `http://127.0.0.1:8000/`)
- `home.jsx` (726 lines) contains the complete UI: interactive map, category filters, species modals

### Data Structure
Countries: Korea, Japan, USA, China, Russia
Categories: 동물 (Animals), 식물 (Plants), 곤충 (Insects), 해양생물 (Marine Life)

Sample data is embedded directly in `home.jsx` with species information per country/category.

### Styling
- Inline CSS with styled-components
- Color-coded category theming
- Font: Pretendard

## Commit Convention

```
feat     : New feature
fix      : Bug fix
docs     : Documentation
style    : CSS/Design changes
refactor : Code improvement
```

## Notes

- Backend files are currently deleted (was FastAPI). Frontend has sample data embedded.
- No test suite configured
- Korean used in UI text and comments, English in code
- Single-page app without routing library - uses React hooks for state
- Role
당신은 Python 백엔드 아키텍트이자 풀스택 디버깅 전문가입니다.

# Current Situation
사용자는 "국가별 종 리스트"를 보는 데는 성공했지만, **리스트의 항목을 클릭하여 '상세 정보(Detail Popup)'를 띄우려고 하면 무한 로딩(Skeleton)**에 빠집니다.
우리는 `iucn_service.py`를 v4 API로 마이그레이션했으나, **상세 조회 라우터(`Router`)와 서비스 로직, 그리고 데이터 모델(`Pydantic`) 간의 불일치**가 의심됩니다.

# Mission: "Find the Missing Link" (연결 고리 찾기)
프로젝트 전체를 스캔하여 프론트엔드 요청이 백엔드에서 어떻게 처리되고 어디서 막히는지 **End-to-End**로 추적하고 수정하세요.

# Execution Steps

## Step 1. [Structure Scan] 프로젝트 구조 파악
- `ls -R` 명령어로 프로젝트 파일 구조를 확인하세요.
- `main.py`, `routers/*.py`, `services/*.py`, `schemas/*.py`(또는 `models/*.py`)를 찾아 **상세 조회 엔드포인트**가 어디에 정의되어 있는지 찾으세요. (예: `/api/v1/species/{id}`)

## Step 2. [Route Analysis] 상세 조회 흐름 추적
찾아낸 상세 조회 라우터 함수(`get_species_detail` 추정)를 분석하세요.
1. **ID 파라미터:** 프론트엔드가 보내는 ID(`sis_id` 혹은 `taxonid`)를 백엔드가 올바른 타입(int/str)으로 받고 있습니까?
2. **Service 호출:** 라우터가 `iucn_service.get_species_detail`을 호출할 때 올바른 인자를 넘깁니까?
3. **Response Model:** 라우터가 반환하는 Pydantic 모델(`Schema`)이 실제 서비스가 리턴하는 딕셔너리 구조와 일치합니까? (**매우 중요**: 여기서 필드가 하나라도 빠지면 500 에러가 나거나 멈춥니다.)

## Step 3. [Service Debugging] `iucn_service.py` 상세 로직 점검
`get_species_detail` 메서드를 집중 분석하세요.
1. **v4 엔드포인트:** 상세 조회를 위해 v4 API의 올바른 URL을 사용하고 있습니까?
2. **Adapter 적용:** 리스트 조회에 썼던 `_v4_to_v3_adapter`가 상세 조회 결과에도 적용되어 있습니까?
3. **Wiki 병목:** `wikipedia_service.get_species_info` 호출 시 **타임아웃(2초)**이 걸려 있습니까? (여기서 멈출 확률 80%)
4. **필수 필드:** 팝업에 꼭 필요한 `image`, `description`, `population`, `habitat` 필드가 없을 경우 **기본값(Default)**으로 채워지고 있습니까?

# Action
1. **진단 결과(Diagnosis)**를 먼저 요약하여 출력하세요. (어느 파일의 어떤 부분이 문제였는지)
2. **수정 작업(Fix)**을 수행하세요.
   - 라우터와 스키마를 프론트엔드 요구사항에 맞게 수정.
   - 서비스 로직에 **타임아웃**, **어댑터**, **기본값 채우기** 적용.
3. 수정 후, "이 코드가 상세 조회 문제를 해결하는 이유"를 설명하세요.