from fastmcp import FastMCP

def register_prompts(mcp: FastMCP):
    """mcp 인스턴스에 프롬프트들을 등록하는 함수"""
    
    @mcp.prompt(
        name="kis_api_helper",
        description="한국투자증권 KIS API 사용을 위한 코드 생성 도우미 프롬프트"
    )
    def kis_api_helper_prompt(
        stock_code,
        task: str = "주식 현재가 조회",
        category: str = "domestic_stock"
    ) -> str:
        """
        KIS API 사용을 위한 코드 생성 도우미 프롬프트
        
        Args:
            task: 수행하고 싶은 작업 (예: "주식 현재가 조회", "계좌 잔고 확인")
            stock_code: 종목코드 (예: "005930" - 삼성전자)
            api_type: API 타입 (domestic_stock, overseas_stock, auth 등)
        """
            
        prompt_template = f"""
# KIS API 코드 생성 요청

## 작업 요청사항
- **작업**: {task}
- **종목코드**: {stock_code}
- **API 타입**: {category}

## 코드 생성 가이드라인

1. **API 검색 단계**:
   - 먼저 적절한 search_{category}_api 툴을 사용하여 관련 API를 검색하세요
   - 검색 결과에서 가장 적합한 API의 function_name과 url을 확인하세요

2. **소스코드 확인 단계**:
   - read_source_code 툴을 사용하여 실제 GitHub 코드를 가져오세요
   - 메인 파일과 체크 파일(있는 경우) 모두 확인하세요

3. **인증 시스템 활용**:
   - **kis_devlp.yaml**: 기존 설정 파일에 appkey/appsecret 입력
   - **kis_auth.py**: 기존 인증 모듈 import 및 활용 (import kis_auth as ka)
   - **토큰 저장**: KIS20250821 파일에 자동 저장되는 기존 시스템 활용
   - 기존 ka.auth() 함수로 토큰 발급 및 관리

4. **API 호출 유량 제어**:
   - **REST API**: 실전 0.05초, 모의 0.5초 sleep 적용
   - **WebSocket**: 1개 appkey당 최대 41건 등록 제한 (주석 또는 코드로 명시)

5. **코드 구조 템플릿**:
   ```python
   import sys
   import logging
   import time
   import json
   sys.path.extend(['..', '.'])
   
   # 기존 kis_auth 모듈 활용
   import kis_auth as ka
   
   # 로깅 설정
   logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
   logger = logging.getLogger(__name__)
   
   # API 호출 함수 (유량 제어 포함)
   def {task.replace(' ', '_').lower()}():
       # 인증 (기존 kis_auth 활용)
       ka.auth(svr="vps", product="01")  # 모의투자, 종합계좌
       # ka.auth(svr="prod", product="01")  # 실전투자시 주석 해제
       
       # 유량 제어 - 모의투자 0.5초, 실전투자 0.05초
       ka.smart_sleep()
       
       # API 호출 (ka.auth() 후에는 바로 함수 호출만 하면 됨)
       try:
           # 예시: 주식현재가 조회 (실제 함수명은 GitHub 소스코드 확인 후 사용)
           result = inquire_price(
               env_dv="real",
               fid_cond_mrkt_div_code="J", 
               fid_input_iscd="{stock_code}"
           )
           return result
       except Exception as e:
           logger.error(f"API 호출 오류: {{e}}")
           return None
   
   # WebSocket 예제 (필요시)
   def websocket_example():
       # 기존 kis_auth의 WebSocket 기능 활용
       ka.auth_ws()
       kws = ka.KISWebSocket(api_url="/tryitout")
       
       # 주의: 1개 appkey당 최대 41건까지만 등록 가능
       # 현재 등록된 구독: 0/41
       
       # 구독 로직 구현
       pass
   
   # 실행 부분
   if __name__ == "__main__":
       try:
           result = {task.replace(' ', '_').lower()}()
           if result:
               print(json.dumps(result, indent=2, ensure_ascii=False))
           else:
               print("결과를 가져올 수 없습니다.")
       except Exception as e:
           logger.error(f"실행 오류: {{e}}")
   ```

6. **필수 설정 파일 생성**:
   ```yaml
   # kis_devlp.yaml 템플릿
   # 실전투자
   my_app: "실전투자_앱키"
   my_sec: "실전투자_앱시크릿"
   
   # 모의투자  
   paper_app: "모의투자_앱키"
   paper_sec: "모의투자_앱시크릿"
   
   # HTS ID
   my_htsid: "사용자_HTS_ID"
   
   # 계좌번호
   my_acct_stock: "증권계좌_8자리"
   my_prod: "01"  # 종합계좌
   ```

## 추가 요청사항  
- **기존 kis_auth.py 모듈 활용**: import kis_auth as ka 방식으로 사용
- **기존 인증 함수 사용**: ka.auth(svr="vps") 또는 ka.auth(svr="prod") 활용
- **기존 환경 정보**: ka.getTREnv()로 토큰 및 설정 정보 가져오기
- **WebSocket 기존 기능**: ka.auth_ws(), ka.KISWebSocket() 활용
- API 호출 전 유량 제어 sleep 적용
- WebSocket 사용시 41건 제한 명시
- 에러 핸들링 및 로깅 포함
- examples_user/ 폴더의 기존 샘플 코드 패턴 참고

위 가이드라인에 따라 "{task}" 작업을 위한 완전한 Python 코드를 생성해주세요.
"""
        
        return prompt_template

    @mcp.prompt(
        name="api_search_helper", 
        description="KIS API 검색을 위한 최적화된 검색 파라미터 추천 프롬프트"
    )
    def api_search_helper_prompt(
        user_request: str = "삼성전자 주가 확인"
    ) -> str:
        """
        사용자 요청을 분석하여 적절한 API 검색 파라미터를 추천하는 프롬프트
        
        Args:
            user_request: 사용자의 원본 요청사항
        """
        
        prompt_template = f"""
# KIS API 검색 파라미터 추천

## 사용자 요청
"{user_request}"

## 분석 및 추천

위 요청을 분석하여 다음 사항들을 추천해주세요:

### 1. 카테고리 분류 및 환경 설정
- **추천 카테고리**: [auth, domestic_stock, domestic_bond, domestic_futureoption, overseas_stock, overseas_futureoption, elw, etfetn] 중 선택
- **이유**: 요청 내용이 해당 카테고리에 해당하는 이유 설명

### 2. 검색 파라미터 추천
```json
{{
  "category": "추천_카테고리",
  "subcategory": "추천_서브카테고리", 
  "function_name": "추천_함수명",
  "api_name": "추천_API명",
  "description": "추천_설명_키워드",
  "response": "추천_응답_키워드"
}}
```

### 3. 검색 전략 (우선순위별)
1. **1차 검색**: 가장 확실한 파라미터 조합
2. **2차 검색**: 1차에서 결과가 없을 경우의 대안  
3. **3차 검색**: 최종 대안 검색 방법

### 4. 예상 API 후보 및 구현 고려사항
- **예상 function_name 목록**: 각각의 용도와 차이점
- **유량 제어**: REST(실전:0.05초, 모의:0.5초) / WebSocket(41건 제한)
- **인증 요구사항**: kis_devlp.yaml, kis_auth.py 활용 필요성
- **토큰 관리**: KIS20250821 파일 저장 방식 적용

### 5. 실행 코드 예시
```python
# 1. API 검색
result = await search_[카테고리]_api(
    query="{user_request}",
    subcategory="추천_서브카테고리",
    function_name="추천_함수명"
)

# 2. 소스코드 확인 
code = await read_source_code(
    url_main="검색결과의_메인URL",
    url_chk="검색결과의_체크URL"  # 선택사항
)

# 3. 구현 시 고려사항
# - kis_devlp.yaml 설정 필수 (기존 파일 활용)
# - 기존 kis_auth.py 모듈 import 및 활용
# - ka.auth(), ka.getTREnv() 함수 사용
# - 유량 제어 sleep 적용
# - 에러 핸들링 및 로깅
```

### 6. KIS API 샘플 코드 참고 가이드
- **examples_llm/**: 단일 API 기능 테스트용 (chk_*.py 파일)
- **examples_user/**: 통합 기능 구현용 (*_functions.py, *_examples.py)
- **WebSocket**: *_functions_ws.py, *_examples_ws.py 파일 참고
- **설정 파일**: kis_devlp.yaml에서 앱키/시크릿 관리
- **토큰 저장**: ~/KIS/config 경로에 KIS20250821 파일 자동 생성

### 7. 주의사항
- **실전투자 주의**: 모의투자(vps)로 충분한 테스트 후 실전(prod) 전환
- **API 제한**: 토큰 재발급은 1분당 1회만 가능
- **WebSocket 제한**: 1개 appkey당 최대 41건 구독 제한
- **계좌번호 형식**: 앞 8자리 + 뒤 2자리 분리하여 설정

위 분석을 바탕으로 "{user_request}" 요청에 가장 적합한 API를 찾고 안전하게 구현하기 위한 구체적인 검색 전략과 구현 가이드를 제시해주세요.
"""
        
        return prompt_template
