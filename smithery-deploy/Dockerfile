# Smithery 요구사항에 맞는 Linux 기반 Python 이미지 사용
FROM python:3.13-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 도구 설치 (Alpine Linux)
RUN apk update && apk add --no-cache \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# uv 설치
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사 (의존성 먼저)
COPY pyproject.toml uv.lock ./

# 의존성 설치
RUN uv sync --frozen

# 애플리케이션 코드 복사
COPY data2.csv ./
COPY src/ ./src/
COPY server.py ./

# 포트 노출 (Smithery HTTP 모드용)
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 헬스체크 추가 (Smithery 호환)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Smithery 요구사항: sh 실행 가능하도록 설정
RUN chmod +x /bin/sh

# 서버 실행 (Streamable HTTP 서버)
CMD ["uv", "run", "python", "server.py"]
