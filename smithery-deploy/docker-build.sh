#!/bin/bash

# KIS API Search Server Docker 빌드 스크립트

echo "🐳 KIS API Search Server Docker 이미지 빌드 시작..."

# 이미지 이름과 태그 설정
IMAGE_NAME="kis-api-search-server"
TAG="latest"

# 기존 이미지가 있다면 제거
echo "🧹 기존 이미지 정리 중..."
docker rmi ${IMAGE_NAME}:${TAG} 2>/dev/null || true

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t ${IMAGE_NAME}:${TAG} .

# 빌드 결과 확인
if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 성공!"
    echo "📦 이미지 정보:"
    docker images ${IMAGE_NAME}:${TAG}
    
    echo ""
    echo "🚀 실행 방법:"
    echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
    echo "  또는"
    echo "  docker-compose up"
else
    echo "❌ Docker 이미지 빌드 실패!"
    exit 1
fi
