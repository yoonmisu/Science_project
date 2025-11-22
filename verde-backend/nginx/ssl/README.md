# SSL 인증서 설정 가이드

이 디렉토리에 SSL 인증서 파일을 배치하세요.

## 필요한 파일

- `fullchain.pem` - 전체 인증서 체인 (서버 인증서 + 중간 인증서)
- `privkey.pem` - 개인 키

## Let's Encrypt로 인증서 발급

### 1. Certbot 설치

```bash
# Ubuntu/Debian
sudo apt install certbot

# macOS
brew install certbot
```

### 2. 인증서 발급

```bash
# Standalone 모드 (서버 중지 필요)
sudo certbot certonly --standalone -d yourdomain.com

# 또는 DNS 검증 모드
sudo certbot certonly --manual --preferred-challenges dns -d yourdomain.com
```

### 3. 인증서 복사

```bash
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
```

### 4. 권한 설정

```bash
chmod 600 nginx/ssl/privkey.pem
chmod 644 nginx/ssl/fullchain.pem
```

## 자동 갱신 설정

Let's Encrypt 인증서는 90일마다 갱신이 필요합니다.

```bash
# 크론탭에 추가
0 0 1 * * certbot renew --quiet && docker restart verde_nginx
```

## 개발 환경용 자체 서명 인증서

테스트 목적으로만 사용하세요:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=localhost"
```

## 주의사항

- `privkey.pem`은 절대 Git에 커밋하지 마세요
- 프로덕션에서는 반드시 신뢰할 수 있는 CA의 인증서를 사용하세요
- 인증서 만료일을 주기적으로 확인하세요
