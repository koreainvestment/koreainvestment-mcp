#!/bin/bash

# KIS API Search Server Docker 실행 스크립트

echo "🚀 KIS API Search Server Docker 컨테이너 실행 시작..."

# 컨테이너 이름 설정
CONTAINER_NAME="kis-api-search-server"
IMAGE_NAME="kis-api-search-server:latest"
PORT="8000"

# 기존 컨테이너가 실행 중이면 중지 및 제거
echo "🧹 기존 컨테이너 정리 중..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Docker 컨테이너 실행
echo "🐳 Docker 컨테이너 실행 중..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8000 \
    --restart unless-stopped \
    ${IMAGE_NAME}

# 실행 결과 확인
if [ $? -eq 0 ]; then
    echo "✅ Docker 컨테이너 실행 성공!"
    echo "📦 컨테이너 정보:"
    docker ps --filter name=${CONTAINER_NAME}
    
    echo ""
    echo "🌐 서버 접속 정보:"
    echo "  URL: http://localhost:${PORT}"
    echo "  상태 확인: curl http://localhost:${PORT}/health"
    
    echo ""
    echo "📋 컨테이너 로그 확인:"
    echo "  docker logs ${CONTAINER_NAME}"
    
    echo ""
    echo "🛑 컨테이너 중지:"
    echo "  docker stop ${CONTAINER_NAME}"
else
    echo "❌ Docker 컨테이너 실행 실패!"
    exit 1
fi
