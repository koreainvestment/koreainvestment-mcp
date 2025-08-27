# Python 3.13 slim 이미지 사용
FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY data2.csv ./
COPY src/ ./src/
COPY server.py ./

# 의존성 설치
RUN uv sync --frozen

# 포트 노출 (HTTP 모드용)
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서버 실행
CMD ["uv", "run", "python", "server.py"]
