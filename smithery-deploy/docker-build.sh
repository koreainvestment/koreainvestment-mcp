#!/bin/bash

# KIS API Search Server Docker 빌드 스크립트 (Smithery 최적화)

echo "🐳 KIS API Search Server Docker 이미지 빌드 시작..."
echo "📋 Smithery 요구사항에 맞게 최적화됨"

# 이미지 이름과 태그 설정
IMAGE_NAME="kis-api-search-server"
TAG="latest"

# 기존 이미지가 있다면 제거
echo "🧹 기존 이미지 정리 중..."
docker rmi ${IMAGE_NAME}:${TAG} 2>/dev/null || true

# Smithery 호환성 검사
echo "🔍 Smithery 호환성 검사 중..."
if ! docker version | grep -q "linux"; then
    echo "⚠️  경고: Linux 기반 Docker 환경 권장"
fi

# Docker 이미지 빌드 (Smithery 최적화)
echo "🔨 Docker 이미지 빌드 중..."
echo "📦 Alpine Linux 기반 Python 3.13 이미지 사용"
docker build \
    --platform linux/amd64 \
    --tag ${IMAGE_NAME}:${TAG} \
    --file Dockerfile \
    .

# 빌드 결과 확인
if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 성공!"
    echo "📦 이미지 정보:"
    docker images ${IMAGE_NAME}:${TAG}
    
    echo ""
    echo "🚀 실행 방법:"
    echo "  # 단일 컨테이너 실행"
    echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
    echo ""
    echo "  # Docker Compose 실행"
    echo "  docker-compose up -d"
    echo ""
    echo "  # Smithery 배포 준비 완료!"
    echo "  smithery.yaml 파일과 함께 사용 가능"
else
    echo "❌ Docker 이미지 빌드 실패!"
    exit 1
fi
