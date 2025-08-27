# KIS API Search Server - Smithery 배포용

한국투자증권(KIS) API를 검색하고 활용할 수 있는 MCP(Model Context Protocol) 서버입니다.

## 🚀 주요 기능

- **8개 카테고리별 API 검색**: 인증, 국내주식, 국내채권, 국내선물옵션, 해외주식, 해외선물옵션, ELW, ETF/ETN
- **실시간 소스코드 읽기**: GitHub에서 실제 API 코드를 가져와서 활용
- **스마트 검색**: 다양한 파라미터 조합으로 정확한 API 찾기
- **HTTP Transport**: Smithery에서 사용 가능한 HTTP 모드 지원

## 📁 프로젝트 구조

```
smithery-deploy/
├── server.py              # 메인 서버 파일 (HTTP transport)
├── manifest.json          # Smithery MCP 설정 파일
├── pyproject.toml         # Python 의존성 설정
├── uv.lock               # 의존성 잠금 파일
├── data2.csv             # API 데이터베이스
├── src/
│   ├── utils/
│   │   └── api_searcher.py  # API 검색 엔진
│   └── prompts/
│       └── prompt.py         # 프롬프트 시스템
└── README.md              # 이 파일
```

## 🛠️ 설치 방법

### 1. 의존성 설치

```bash
# uv를 사용한 의존성 설치
uv sync
```

### 2. Smithery 설정

1. Smithery에서 새 프로젝트 생성
2. `manifest.json` 파일을 프로젝트 루트에 복사
3. 모든 소스 파일을 프로젝트에 업로드

## 🚀 서버 실행

### 1. Docker 사용 (권장)

#### Docker Compose로 실행
```bash
# 프로덕션 모드
docker-compose up -d

# 개발 모드 (코드 변경 실시간 반영)
docker-compose --profile dev up -d
```

#### Docker 명령어로 실행
```bash
# 이미지 빌드
./docker-build.sh

# 컨테이너 실행
./docker-run.sh

# 또는 수동으로
docker build -t kis-api-search-server .
docker run -d -p 8000:8000 --name kis-api-server kis-api-search-server
```

### 2. 로컬 테스트

```bash
# 의존성 설치
uv sync

# HTTP 모드로 서버 실행
uv run python server.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 3. Smithery 배포

1. 모든 파일을 Smithery 프로젝트에 업로드
2. Smithery에서 자동으로 MCP 서버가 시작됩니다
3. `kis_api_search` 서버가 사용 가능한 도구로 등록됩니다

### 4. Docker 컨테이너 관리

```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs kis-api-search-server

# 컨테이너 중지
docker stop kis-api-search-server

# 컨테이너 제거
docker rm kis-api-search-server

# 이미지 제거
docker rmi kis-api-search-server:latest
```

## 🔧 사용 가능한 도구

### 1. API 검색 도구

- `search_auth_api` - 인증 관련 API 검색
- `search_domestic_stock_api` - 국내주식 API 검색
- `search_domestic_bond_api` - 국내채권 API 검색
- `search_domestic_futureoption_api` - 국내선물옵션 API 검색
- `search_overseas_stock_api` - 해외주식 API 검색
- `search_overseas_futureoption_api` - 해외선물옵션 API 검색
- `search_elw_api` - ELW API 검색
- `search_etfetn_api` - ETF/ETN API 검색

### 2. 소스코드 읽기 도구

- `read_source_code` - GitHub에서 실제 API 코드 가져오기

## 📖 사용 예시

### 1. 삼성전자 주가 조회 API 찾기

```python
# 국내주식 API에서 삼성전자 관련 API 검색
result = await search_domestic_stock_api(
    query="삼성전자 주가 조회",
    subcategory="기본시세",
    function_name="inquire_price"
)
```

### 2. 실제 코드 가져오기

```python
# 검색 결과에서 URL을 사용하여 실제 코드 가져오기
code = await read_source_code(
    url_main="검색결과의_메인URL",
    url_chk="검색결과의_체크URL"  # 선택사항
)
```

## 🔍 검색 파라미터

각 검색 도구는 다음 파라미터를 지원합니다:

- `query`: 사용자의 원본 질문 (로깅용)
- `subcategory`: 카테고리 내 서브카테고리
- `api_name`: 특정 API 이름
- `function_name`: 특정 함수 이름
- `description`: 함수 설명 키워드
- `response`: 응답 데이터 키워드

## 📊 출력 형식

모든 검색 결과는 다음 JSON 형식으로 반환됩니다:

```json
{
  "status": "success|error|no_results",
  "message": "상태 메시지",
  "total_count": 10,
  "results": [
    {
      "function_name": "API 함수명",
      "api_name": "API 이름",
      "category": "카테고리",
      "subcategory": "서브카테고리",
      "url_main": "메인 코드 URL",
      "url_chk": "체크 코드 URL"
    }
  ]
}
```

## 🌐 HTTP Transport

이 서버는 Smithery에서 사용하기 위해 HTTP transport 모드로 설정되어 있습니다:

- **포트**: 8000
- **호스트**: 0.0.0.0 (모든 인터페이스)
- **프로토콜**: HTTP/1.1
- **FastMCP**: FastMCP 프레임워크 기반

## 🐳 Docker 지원

### Docker 이미지 특징

- **Python 3.13 slim**: 가벼운 베이스 이미지 사용
- **uv 패키지 매니저**: 빠른 의존성 설치
- **헬스체크**: 자동 상태 모니터링
- **볼륨 마운트**: 데이터 파일 외부 관리 가능
- **멀티 스테이지**: 최적화된 이미지 크기

### Docker Compose 서비스

1. **프로덕션 서비스** (`kis-api-server`)
   - 포트: 8000
   - 자동 재시작
   - 헬스체크 포함

2. **개발 서비스** (`kis-api-server-dev`)
   - 포트: 8001
   - 코드 변경 실시간 반영
   - 볼륨 마운트로 개발 편의성 향상

### 환경 변수

- `PYTHONPATH=/app`: Python 모듈 경로 설정
- `PYTHONUNBUFFERED=1`: 로그 즉시 출력

## ⚠️ 주의사항

1. **API 제한**: GitHub API 호출 시 rate limiting 적용 (0.1초 간격)
2. **데이터 크기**: `data2.csv` 파일이 약 12,000개의 API 정보를 포함
3. **의존성**: Python 3.13+ 및 uv 패키지 매니저 필요
4. **네트워크**: GitHub 접근이 가능한 환경에서만 동작
5. **Docker**: Docker 20.10+ 및 Docker Compose 2.0+ 필요
6. **포트**: 8000번 포트가 사용 가능해야 함
7. **메모리**: 최소 512MB RAM 권장 (컨테이너 실행 시)

## 🔗 관련 링크

- [한국투자증권 Open Trading API](https://github.com/koreainvestment/open-trading-api)
- [FastMCP 문서](https://github.com/fastmcp/fastmcp)
- [MCP 스펙](https://modelcontextprotocol.io/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Python Docker 이미지](https://hub.docker.com/_/python)

## 📝 라이선스

MIT License

## 👥 기여자

- jjlee (원본 개발자)
