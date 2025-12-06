# Verde 배포 가이드

이 문서는 Verde 애플리케이션을 AWS에 배포하는 방법을 설명합니다.

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                           사용자 (Users)                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CloudFront CDN (글로벌 배포)                       │
│  - SSL/TLS 인증서                                                    │
│  - 정적 콘텐츠 캐싱 (이미지, CSS, JS)                                    │
│  - DDoS 보호                                                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
┌───────────────────────────────┐   ┌─────────────────────────┐
│     정적 콘텐츠 (S3)             │   │   API 요청 (ALB)         │
│  - React 빌드 파일               │   │  - 로드 밸런싱             │
│  - 이미지 파일                   │   │  - 헬스 체크              │
└───────────────────────────────┘   └─────────────────────────┘
                                                │
                            ┌───────────────────┴───────────────────┐
                            │                                       │
                            ▼                                       ▼
                ┌──────────────────────┐              ┌──────────────────────┐
                │   ECS Fargate Task 1 │              │   ECS Fargate Task 2 │
                │   (FastAPI)          │              │   (FastAPI)          │
                │  - CPU: 0.5 vCPU     │              │  - CPU: 0.5 vCPU     │
                │  - RAM: 1 GB         │              │  - RAM: 1 GB         │
                └──────────────────────┘              └──────────────────────┘
                            │                                       │
                            └───────────────────┬───────────────────┘
                                                │
                ┌───────────────────────────────┼───────────────────────────┐
                │                               │                           │
                ▼                               ▼                           ▼
    ┌──────────────────────┐      ┌──────────────────────┐    ┌──────────────────────┐
    │  RDS PostgreSQL      │      │  ElastiCache Redis   │    │    S3 Bucket         │
    │  + PostGIS           │      │                      │    │   (이미지 저장)         │
    │  - 멀티 AZ            │      │  - 캐싱               │    │  - 버저닝              │
    │  - 자동 백업           │      │  - 세션               │    │  - 라이프사이클         │
    └──────────────────────┘      └──────────────────────┘    └──────────────────────┘
```

## 사전 요구사항

- AWS CLI 설치 및 구성
- Terraform >= 1.0
- Docker
- Node.js >= 20
- Python >= 3.11

## 빠른 시작 (로컬 개발)

### 1. Docker Compose로 로컬 실행

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에 IUCN_API_KEY, OPENAI_API_KEY 등 입력

# Docker Compose 실행
docker-compose up -d

# 접속
# Frontend: http://localhost
# Backend API: http://localhost:8000
```

## AWS 배포

### 1. Terraform 인프라 생성

```bash
cd infrastructure/terraform

# 변수 파일 생성
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars 파일 편집

# Terraform 초기화
terraform init

# 계획 확인
terraform plan

# 인프라 생성 (약 15-20분 소요)
terraform apply
```

### 2. Docker 이미지 빌드 및 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 백엔드 이미지 빌드 및 푸시
cd verde-backend
docker build -t verde-backend .
docker tag verde-backend:latest <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/verde-backend:latest
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/verde-backend:latest
```

### 3. 프론트엔드 빌드 및 S3 업로드

```bash
# 프론트엔드 빌드
npm run build

# S3 업로드
aws s3 sync dist/ s3://verde-static-assets-<account-id>/ --delete

# CloudFront 캐시 무효화
aws cloudfront create-invalidation --distribution-id <distribution-id> --paths "/*"
```

### 4. ECS 서비스 업데이트

```bash
# 새 이미지로 서비스 업데이트
aws ecs update-service \
  --cluster verde-cluster \
  --service verde-backend \
  --force-new-deployment
```

## CI/CD 파이프라인 설정

GitHub Actions를 사용한 자동 배포가 설정되어 있습니다.

### 필요한 GitHub Secrets

| Secret 이름 | 설명 |
|------------|------|
| `AWS_ROLE_ARN` | OIDC 인증용 IAM Role ARN |
| `API_BASE_URL` | CloudFront 또는 ALB URL |
| `S3_BUCKET` | 정적 자산 S3 버킷 이름 |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront 배포 ID |

### 배포 트리거

- `main` 브랜치에 푸시하면 자동 배포됩니다.
- GitHub Actions 워크플로우에서 수동 트리거도 가능합니다.

## 모니터링

### CloudWatch 대시보드

- ECS 서비스 메트릭 (CPU, 메모리)
- ALB 요청 메트릭 (응답 시간, 에러율)
- RDS 메트릭 (연결 수, 쿼리 성능)

### 로그 확인

```bash
# ECS 로그 확인
aws logs tail /ecs/verde-backend --follow
```

## 비용 최적화 팁

1. **Fargate Spot**: 비프로덕션 환경에서 70% 비용 절감
2. **단일 NAT Gateway**: 비프로덕션 환경에서 비용 절감
3. **Redis/RDS 크기**: 트래픽에 따라 스케일 업
4. **CloudFront 캐싱**: 원본 요청 최소화로 비용 절감

## 문제 해결

### 일반적인 문제

1. **ECS 태스크 시작 실패**
   ```bash
   aws ecs describe-tasks --cluster verde-cluster --tasks <task-id>
   ```

2. **헬스 체크 실패**
   - ALB 타겟 그룹 헬스 체크 설정 확인
   - ECS 태스크 로그 확인

3. **데이터베이스 연결 실패**
   - 보안 그룹 규칙 확인
   - RDS 엔드포인트 및 자격 증명 확인

## 롤백

```bash
# 이전 태스크 정의로 롤백
aws ecs update-service \
  --cluster verde-cluster \
  --service verde-backend \
  --task-definition verde-backend:<previous-revision>
```

## 보안 고려사항

- 모든 시크릿은 AWS SSM Parameter Store에 저장
- RDS/Redis는 프라이빗 서브넷에만 배치
- ALB는 CloudFront에서만 접근 가능하도록 설정 권장
- HTTPS 필수 (CloudFront에서 리다이렉트)
