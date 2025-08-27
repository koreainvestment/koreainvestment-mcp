from fastmcp import FastMCP, Context
from src.utils.api_searcher import APISearcher
import asyncio
import os
import requests
import time
import re

# 프롬프트 등록을 위한 import
from src.prompts.prompt import register_prompts

# Smithery 배포용 설정
mcp = FastMCP(
    name="kis_api_search",
    instructions="If the user requests stock market information, trading-related code, or investment data, ALWAYS call this tool. Do NOT generate the code yourself without first checking the API search results."
)

# 절대 경로로 data.csv 파일 지정
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "data2.csv")
searcher = APISearcher(data_path)

# 프롬프트 등록
register_prompts(mcp)

# GitHub URL 처리를 위한 헬퍼 함수들
def extract_category_function_from_url(github_url: str) -> dict:
    """GitHub URL에서 category와 function_name 추출"""
    # examples_llm/{category}/{function_name}/{function_name}.py 패턴 매칭
    pattern = r'examples_llm/([^/]+)/([^/]+)/(?:chk_)?([^/]+)\.py'
    match = re.search(pattern, github_url)
    
    if match:
        category = match.group(1)
        function_name = match.group(2)
        return {"category": category, "function_name": function_name}
    return None

# 공통 프롬프트 
COMMON_DESCRIPTION = """
검색 파라미터:
query: 사용자의 원본 질문을 그대로 입력하세요 (로깅용)
subcategory: 카테고리 내 서브카테고리 검색
api_name: 특정 API 이름 검색
function_name: 특정 함수 이름 검색
description: 함수에 대한 설명 검색
response: 응답 데이터 내용으로 검색

출력 형태: JSON 객체로 반환
- 단순 개수 조회: category/subcategory만 지정시 → API 목록만 반환
- 상세 검색: 여러 조건 지정시 → 매칭되는 API의 상세 정보 반환
- status: "success"/"error"/"no_results"
- total_count: 총 검색 결과 수
- results: API 정보 배열 (function_name, api_name, category, subcategory)

검색 전략 가이드라인:
1. 첫 번째 검색에서 결과가 없으면, 다른 파라미터 조합으로 재시도
2. description 파라미터는 정확히 매칭되는 키워드만 사용 
3. 검색 실패시 순서: query만 → function_name → api_name → subcategory 순으로 시도
4. "재무", "financial", "매출", "revenue" 등 핵심 키워드는 function_name이나 api_name으로 우선 검색

예시 검색 전략:
- 재무 정보 요청시: function_name="financial" 또는 function_name="finance" 우선 시도
- 실시간 데이터: subcategory="실시간시세" 우선 시도  
- 매출액/실적: response="매출액" 또는 function_name="financial" 시도
"""

# 각 도구별 description
TOOL_DESCRIPTIONS = {}

TOOL_DESCRIPTIONS["search_auth_api"] = f"""인증 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[인증]
ex) 인증 토큰 발급해줘. -> subcategory="인증", function_name="auth_token"
ex) 웹소켓 연결 방법 알려줘. -> subcategory="인증", function_name="auth_ws_token"
"""

TOOL_DESCRIPTIONS["search_domestic_stock_api"] = f"""국내주식 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) 삼성전자 현재 매수/매도 호가와 잔량 알려줘. -> subcategory="기본시세", api_name="주식현재가 호가/예상체결", function_name="inquire_asking_price_exp_ccn"
ex) SK하이닉스 시간외 단일가 예상 체결가 조회해줘. -> subcategory="기본시세", api_name="주식현재가 시간외일자별주가", description="예상 체결가"
ex) 코스피 지수 일봉 데이터 보여줘. -> subcategory="기본시세", function_name="inquire_daily_itemchartprice"
ex) 삼성전자 총 매도호가 잔량 알려줘. -> subcategory="기본시세", response="총 매도호가 잔량"
ex) SK하이닉스 누적 거래대금 보여줘. -> subcategory="기본시세", response="누적 거래대금"
ex) 삼성전자 52주 최고가 날짜 알려줘. -> subcategory="기본시세", response="52주일 최고가 일자"
ex) 코스피 상한가, 하한가 알려줘. -> subcategory="기본시세", response="상한가"
ex) 삼성전자 시가총액 확인해줘. -> subcategory="기본시세", response="HTS 시가총액"
ex) SK하이닉스 PER과 PBR 알려줘. -> subcategory="기본시세", response="PER"

[순위분석] 
ex) 오늘 거래대금 상위 종목 보여줘. -> subcategory="순위분석"
ex) 등락률 순위 알려줘. -> subcategory="순위분석", function_name="fluctuation"
ex) 등락률 상위 종목들의 데이터 순위 보여줘. -> subcategory="순위분석", response="데이터 순위"
ex) 거래량 많은 종목 순위 알려줘. -> subcategory="순위분석", response="누적 거래량"

[ELW시세]
ex) ELW 현재가 시세 보여줘. -> subcategory="ELW시세", function_name="inquire_elw_price"

[업종/기타]
ex) 코스피 업종별 지수 현황 알려줘. -> subcategory="업종/기타", function_name="inquire_index_price"
ex) 오늘 주요 뉴스 제목들 보여줘. -> subcategory="업종/기타", function_name="news_title"

[주문/계좌]
ex) 내 주식 잔고 조회해줘. -> subcategory="주문/계좌", function_name="inquire_balance"
ex) 오늘 내 주문 체결 내역 보여줘. -> subcategory="주문/계좌", function_name="inquire_daily_ccld"
ex) 내 계좌 총체결수량 보여줘. -> subcategory="주문/계좌", response="총체결수량"
ex) 오늘 내 매매 수수료 얼마 나왔어? -> subcategory="주문/계좌", response="수수료"
ex) 내 계좌 평가손익금액 알려줘. -> subcategory="주문/계좌", response="평가손익금액"
ex) 배당락일 다가오는 종목 있어? -> subcategory="주문/계좌", response="배당락일"

[시세분석]
ex) 관심종목 시세 조회해줘. -> subcategory="시세분석", function_name="intstock_multprice"

[종목정보]
ex) 삼성전자 종목 기본 정보 알려줘. -> subcategory="종목정보", function_name="search_stock_info"
ex) 상품 기본 정보 조회해줘. -> subcategory="종목정보", function_name="search_info"

[실시간시세]
ex) 삼성전자 주가 실시간으로 계속 받아줘. -> subcategory="실시간시세", function_name="ccnl_krx"
ex) 코스피 지수 장 마감 전 예상체결가 알려줘. -> subcategory="실시간시세", function_name="index_exp_ccnl"
ex) SK하이닉스 매수매도 호가 실시간 모니터링해줘. -> subcategory="실시간시세", function_name="asking_price_total"
ex) 장 시작했는지 VI 발동됐는지 실시간으로 알려줘. -> subcategory="실시간시세", function_name="market_status_krx"
ex) 내 주문이 체결되면 바로 알림 받고 싶어. -> subcategory="실시간시세", function_name="ccnl_notice"
ex) 시간외단일가 시간대 호가 변동 실시간으로 봐줘. -> subcategory="실시간시세", function_name="overtime_asking_price_krx"
ex) 기관 프로그램매매 동향 실시간으로 추적해줘. -> subcategory="실시간시세", function_name="program_trade_krx"
ex) 삼성전자 실시간 체결 현황 웹소켓으로 받아줘. -> subcategory="실시간시세", description="실시간 체결가"
ex) 장중 회원사별 거래 현황 실시간으로 보여줘. -> subcategory="실시간시세", response="회원사별 거래량"
"""

TOOL_DESCRIPTIONS["search_domestic_bond_api"] = f"""국내채권 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) 국고채 3년물 호가창에서 총 매도호가 잔량 알려줘. -> subcategory="기본시세", description="총 매도호가 잔량"
ex) 국고채 10년물 발행정보 확인해줘. -> subcategory="기본시세", api_name="장내채권 발행정보", function_name="issue_info"
ex) 장내채권 현재가 시세 조회해줘. -> subcategory="기본시세", function_name="inquire_price"
ex) 채권 호가 정보 보여줘. -> subcategory="기본시세", function_name="inquire_asking_price"
ex) 국고채 발행일자 확인해줘. -> subcategory="기본시세", response="발행일자"
ex) 채권 만기일자 알려줘. -> subcategory="기본시세", response="만기일자"
ex) 국고채 표면금리 얼마야? -> subcategory="기본시세", response="표면금리"

[주문/계좌]
ex) 오늘 내 채권 주문의 총체결수량합계 보여줘. -> subcategory="주문/계좌", function_name="inquire_daily_ccld", api_name="장내채권 주문체결내역"
ex) 내 채권 잔고 조회해줘. -> subcategory="주문/계좌", function_name="inquire_balance"
ex) 채권 매수가능조회 해줘. -> subcategory="주문/계좌", function_name="inquire_psbl_order"
ex) 채권 총체결수량합계 보여줘. -> subcategory="주문/계좌", response="총체결수량합계"

[실시간시세]
ex) 국고채 3년물 금리 변동 실시간으로 추적해줘. -> subcategory="실시간시세", function_name="bond_ccnl"
ex) 회사채 매수매도 호가 실시간으로 모니터링해줘. -> subcategory="실시간시세", function_name="bond_asking_price"
ex) 채권지수 움직임 실시간으로 받아줘. -> subcategory="실시간시세", function_name="bond_index_ccnl"
ex) 채권 체결가격 변화 웹소켓으로 받고 싶어. -> subcategory="실시간시세", description="실시간 체결가"
"""

TOOL_DESCRIPTIONS["search_domestic_futureoption_api"] = f"""국내선물옵션 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) 코스피200 선물 현재 호가 상황 알려줘. -> subcategory="기본시세", api_name="선물옵션 시세호가", function_name="inquire_asking_price"
ex) 30초봉으로 오늘 최고가/최저가 조회해줘. -> subcategory="기본시세", function_name="inquire_time_fuopchartprice", description="선물 최고가"
ex) 선물옵션 현재가 시세 보여줘. -> subcategory="기본시세", function_name="inquire_price"
ex) 국내선물 기초자산 시세 알려줘. -> subcategory="기본시세", function_name="display_board_top"
ex) 선물 총 매도호가 잔량 알려줘. -> subcategory="기본시세", response="총 매도호가 잔량"
ex) 선물 상한가, 하한가 확인해줘. -> subcategory="기본시세", response="선물 상한가"

[주문/계좌]
ex) 내 선물옵션 계좌 총자산 현황 알려줘. -> subcategory="주문/계좌", api_name="선물옵션 총자산현황", function_name="inquire_deposit"
ex) 선물옵션 잔고 조회해줘. -> subcategory="주문/계좌", description="잔고"
ex) 내 계좌 현금증거금 얼마야? -> subcategory="주문/계좌", response="현금증거금"
ex) 평가손익금액 보여줘. -> subcategory="주문/계좌", response="평가손익금액"

[실시간시세]
ex) 코스피200 선물 가격 실시간으로 추적해줘. -> subcategory="실시간시세", function_name="index_futures_realtime_conclusion"
ex) 선물 매수매도 호가 실시간으로 모니터링해줘. -> subcategory="실시간시세", function_name="index_futures_realtime_quote"
ex) 옵션 체결가 실시간 변동 알려줘. -> subcategory="실시간시세", function_name="index_option_realtime_conclusion"
ex) 내 선물 주문 체결되면 바로 알림해줘. -> subcategory="실시간시세", function_name="fuopt_ccnl_notice"
ex) 야간선물 거래 실시간으로 받아줘. -> subcategory="실시간시세", function_name="krx_ngt_futures_ccnl"
ex) 상품선물 WTI 원유 실시간 시세 보여줘. -> subcategory="실시간시세", function_name="commodity_futures_realtime_conclusion"
ex) 주식선물 실시간 체결가 웹소켓으로 받고 싶어. -> subcategory="실시간시세", description="실시간 체결가"
ex) 옵션 그리스 지표 실시간 변화 추적해줘. -> subcategory="실시간시세", response="델타, 감마, 베가"
"""

TOOL_DESCRIPTIONS["search_overseas_stock_api"] = f"""해외주식 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) 테슬라 현재 1호가 매수/매도 가격 알려줘. -> subcategory="기본시세", api_name="해외주식 현재가 1호가", function_name="inquire_asking_price"
ex) 애플 현재 체결가 알려줘. -> subcategory="기본시세", function_name="price", api_name="해외주식 현재체결가"
ex) 해외주식 분봉 차트 보여줘. -> subcategory="기본시세", function_name="inquire_time_itemchartprice"
ex) 해외주식 일봉 데이터 조회해줘. -> subcategory="기본시세", function_name="inquire_daily_chartprice"
ex) 애플 52주 최고가 날짜 알려줘. -> subcategory="기본시세", response="52주최고일자"
ex) 테슬라 원화환산 당일가격 보여줘. -> subcategory="기본시세", response="원환산당일가격"

[시세분석]
ex) 애플 다음 배당락일과 지급일 알려줘. -> subcategory="시세분석", function_name="rights_by_ice", api_name="해외주식 권리종합"
ex) 나스닥 상승률 순위 보여줘. -> subcategory="시세분석", function_name="updown_rate"
ex) 해외주식 거래량 순위 알려줘. -> subcategory="시세분석", function_name="trade_vol"
ex) 엔비디아 권리유형 뭐가 있어? -> subcategory="시세분석", response="권리유형"

[주문/계좌]
ex) 내 계좌의 해외주식 잔고 알려줘. -> subcategory="주문/계좌", function_name="inquire_balance", api_name="해외주식 잔고"
ex) 해외주식 체결기준 현재잔고 보여줘. -> subcategory="주문/계좌", function_name="inquire_present_balance"
ex) 해외주식 평가손익 보여줘. -> subcategory="주문/계좌", response="평가손익"

[실시간시세]
ex) 테슬라 주가 실시간으로 계속 받아줘. -> subcategory="실시간시세", function_name="delayed_ccnl"
ex) 애플 매수매도 호가 실시간 모니터링해줘. -> subcategory="실시간시세", function_name="asking_price"
ex) 내 해외주식 주문 체결되면 즉시 알림받고 싶어. -> subcategory="실시간시세", function_name="ccnl_notice"
ex) 나스닥 종목들 실시간 지연시세 받아줘. -> subcategory="실시간시세", function_name="delayed_ccnl"
ex) 홍콩주식 실시간 호가 변동 추적해줘. -> subcategory="실시간시세", function_name="delayed_asking_price_asia"
ex) 미국 주간거래 실시간 시세 모니터링해줘. -> subcategory="실시간시세", description="주간거래 실시간"
ex) 해외주식 체결 통보 웹소켓으로 받고 싶어. -> subcategory="실시간시세", response="체결통보"
"""

TOOL_DESCRIPTIONS["search_overseas_futureoption_api"] = f"""해외선물옵션 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) WTI 원유 선물 현재가 알려줘. -> subcategory="기본시세", api_name="해외선물종목현재가", function_name="inquire_price"
ex) 해외선물 분봉 차트 조회해줘. -> subcategory="기본시세", function_name="inquire_time_futurechartprice"
ex) 해외옵션 호가 정보 보여줘. -> subcategory="기본시세", function_name="opt_asking_price"
ex) 해외선물 호가단위 확인해줘. -> subcategory="기본시세", response="호가단위"

[주문/계좌]
ex) 오늘 내 해외선물옵션 주문 내역 보여줘. -> subcategory="주문/계좌", function_name="inquire_ccld", api_name="해외선물옵션 당일주문내역조회"
ex) 해외선물옵션 미결제 잔고 조회해줘. -> subcategory="주문/계좌", function_name="inquire_unpd"
ex) 해외선물옵션 예수금 현황 알려줘. -> subcategory="주문/계좌", function_name="inquire_deposit"
ex) 내 계좌 순손익금액 얼마야? -> subcategory="주문/계좌", response="순손익금액"

[실시간시세]
ex) WTI 원유 선물 가격 실시간으로 추적해줘. -> subcategory="실시간시세", function_name="ccnl"
ex) CME 선물 호가 실시간 모니터링해줘. -> subcategory="실시간시세", function_name="asking_price"
ex) 내 해외선물 주문 체결되면 바로 알림해줘. -> subcategory="실시간시세", function_name="ccnl_notice"
ex) 해외선물옵션 주문내역 실시간 통보받고 싶어. -> subcategory="실시간시세", function_name="order_notice"
ex) 금 선물 시세 변동 웹소켓으로 받아줘. -> subcategory="실시간시세", description="실시간 체결가"
ex) SGX 선물 유료시세 실시간으로 받고 싶어. -> subcategory="실시간시세", response="유료시세"
"""

TOOL_DESCRIPTIONS["search_elw_api"] = f"""ELW 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[ELW시세]
ex) ELW 거래량 순위 보여줘. -> subcategory="ELW시세", api_name="ELW 거래량순위", function_name="volume_rank"
ex) 삼성전자 콜 ELW 현재가, 시가, 고가, 저가 알려줘. -> subcategory="ELW시세", function_name="inquire_elw_price"
ex) 오늘 가장 많이 거래된 ELW 알려줘. -> subcategory="ELW시세", description="누적거래량"
ex) ELW 현재가 시세 조회해줘. -> subcategory="ELW시세", function_name="inquire_elw_price"
ex) ELW 잔존일수 확인해줘. -> subcategory="ELW시세", response="잔존일수"

[실시간시세]
ex) 삼성전자 콜 ELW 실시간 시세 받아줘. -> subcategory="실시간시세", function_name="elw_ccnl"
ex) ELW 매수매도 호가 실시간 모니터링해줘. -> subcategory="실시간시세", function_name="elw_asking_price"
ex) ELW 예상체결가 실시간으로 알려줘. -> subcategory="실시간시세", function_name="elw_exp_ccnl"
ex) 권리행사일 다가오는 ELW 실시간 추적해줘. -> subcategory="실시간시세", description="실시간 체결가"
ex) ELW 델타값 변화 웹소켓으로 받고 싶어. -> subcategory="실시간시세", response="델타값 변화"
"""

TOOL_DESCRIPTIONS["search_etfetn_api"] = f"""ETF/ETN 카테고리에 대한 검색 결과를 반환합니다.
{COMMON_DESCRIPTION}
[기본시세]
ex) KODEX 200 ETF NAV 추이 보여줘. -> subcategory="기본시세", api_name="NAV 비교추이(종목)", function_name="nav_comparison_trend"
ex) TIGER 나스닥100 ETN 현재가 알려줘. -> subcategory="기본시세", function_name="inquire_price", api_name="ETF/ETN 현재가"
ex) 오늘 KODEX 200 ETF 시가, 고가, 저가 NAV 각각 알려줘. -> subcategory="기본시세", description="NAV"
ex) ETF 현재가 조회해줘. -> subcategory="기본시세", api_name="ETF/ETN 현재가"
ex) ETF NAV 비교 분석해줘. -> subcategory="기본시세", function_name="nav_comparison_trend"
ex) ETF 설정액 얼마야? -> subcategory="기본시세", response="설정액"
ex) ETF 배당주기 확인해줘. -> subcategory="기본시세", response="ETF 배당 주기"

[실시간시세]
ex) KODEX 200 ETF NAV 실시간으로 추적해줘. -> subcategory="실시간시세", function_name="etf_nav_trend"
ex) TIGER 나스닥100 ETN 실시간 시세 받아줘. -> subcategory="실시간시세", function_name="etf_nav_trend"
ex) ETF와 기초지수 괴리율 실시간 모니터링해줘. -> subcategory="실시간시세", description="NAV 추이"
ex) 레버리지 ETF 실시간 변동률 알려줘. -> subcategory="실시간시세", response="실시간 NAV"
"""

# KIS API 템플릿 리소스 정의
@mcp.resource("internal://kis-api/{category}/{function_name}", mime_type="text/plain")
def _kis_api_main_file(category: str, function_name: str) -> str:
    """KIS API 메인 파일을 읽는 템플릿 리소스"""
    if not (category and function_name):
        return "❌ 잘못된 파라미터"
    
    url = f"https://raw.githubusercontent.com/koreainvestment/open-trading-api/main/examples_llm/{category}/{function_name}/{function_name}.py"
    
    # Rate limiting
    time.sleep(0.1)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"❌ GitHub 파일 읽기 실패: {str(e)}"

@mcp.resource("internal://kis-api-chk/{category}/{function_name}", mime_type="text/plain")
def _kis_api_check_file(category: str, function_name: str) -> str:
    """KIS API 체크 파일을 읽는 템플릿 리소스"""
    if not (category and function_name):
        return "❌ 잘못된 파라미터"
    
    url = f"https://raw.githubusercontent.com/koreainvestment/open-trading-api/main/examples_llm/{category}/{function_name}/chk_{function_name}.py"
    
    # Rate limiting
    time.sleep(0.1)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"❌ GitHub 파일 읽기 실패: {str(e)}"

# 공통 출력 스키마 정의 (MCP 스펙 준수: type must be "object")
SEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "error", "no_results"],
            "description": "검색 상태"
        },
        "message": {
            "type": "string",
            "description": "상태 메시지"
        },
        "total_count": {
            "type": "integer",
            "description": "총 검색 결과 수"
        },
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "API 함수명"},
                    "api_name": {"type": "string", "description": "API 이름"},
                    "category": {"type": "string", "description": "카테고리"},
                    "subcategory": {"type": "string", "description": "서브카테고리"}
                },
                "required": ["function_name", "api_name", "category", "subcategory"]
            },
            "description": "검색된 API 목록"
        }
    },
    "required": ["status", "message", "total_count", "results"]
}

# 각 tool 정의
@mcp.tool(
    name="search_auth_api",
    description=TOOL_DESCRIPTIONS["search_auth_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_auth_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "auth"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_domestic_stock_api",
    description=TOOL_DESCRIPTIONS["search_domestic_stock_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_domestic_stock_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "domestic_stock"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_domestic_bond_api",
    description=TOOL_DESCRIPTIONS["search_domestic_bond_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_domestic_bond_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "domestic_bond"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_domestic_futureoption_api",
    description=TOOL_DESCRIPTIONS["search_domestic_futureoption_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_domestic_futureoption_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "domestic_futureoption"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_overseas_stock_api",
    description=TOOL_DESCRIPTIONS["search_overseas_stock_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_overseas_stock_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "overseas_stock"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_overseas_futureoption_api",
    description=TOOL_DESCRIPTIONS["search_overseas_futureoption_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_overseas_futureoption_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "overseas_futureoption"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_elw_api",
    description=TOOL_DESCRIPTIONS["search_elw_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_elw_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "elw"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="search_etfetn_api",
    description=TOOL_DESCRIPTIONS["search_etfetn_api"],
    output_schema=SEARCH_OUTPUT_SCHEMA
)
async def search_etfetn_api(
    query: str = None,
    subcategory: str = None,
    api_name: str = None,
    function_name: str = None,
    description: str = None,
    response: str = None,
) -> str:
    search_params = {"category": "etfetn"}
    
    if subcategory:
        search_params["subcategory"] = subcategory
    if api_name:
        search_params["api_name"] = api_name
    if function_name:
        search_params["function_name"] = function_name
    if description:
        search_params["description"] = description
    if response:
        search_params["response"] = response
    
    return searcher.search(**search_params)

@mcp.tool(
    name="read_source_code",
    description="""API 검색 결과의 URL에서 실제 GitHub 코드를 가져옵니다.
    
    파라미터:
    - url_main: 메인 호출 파일 URL (필수)
    - url_chk: 테스트 호출 파일 URL (선택)
    
    사용 예시:
    1. api_search tool로 원하는 API를 찾습니다
    2. 검색 결과에서 url_main, url_chk를 확인합니다  
    3. 이 tool을 사용해서 실제 GitHub 코드를 가져옵니다
    """,
    output_schema={
        "type": "object", 
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "partial_success", "error"],
                "description": "전체 작업 상태"
            },
            "message": {
                "type": "string",
                "description": "상태 메시지"
            },
            "results": {
                "type": "object",
                "properties": {
                    "main": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "message": {"type": "string"},
                            "content": {"type": "string", "description": "실제 코드 내용"},
                            "url": {"type": "string"}
                        }
                    },
                    "check": {
                        "type": "object", 
                        "properties": {
                            "status": {"type": "string"},
                            "message": {"type": "string"},
                            "content": {"type": "string", "description": "실제 코드 내용"},
                            "url": {"type": "string"}
                        }
                    }
                },
                "description": "각 URL별 코드 가져오기 결과"
            }
        },
        "required": ["status", "message", "results"]
    }
)
async def fetch_api_code(
    url_main: str,
    url_chk: str = None,
    ctx: Context = None
) -> dict:
    """API URL에서 실제 GitHub 코드를 가져옴 (템플릿 리소스 사용)"""
    results = {}
    
    # 메인 URL 처리
    if url_main:
        params = extract_category_function_from_url(url_main)
        if params:
            git_uri = f"internal://kis-api/{params['category']}/{params['function_name']}"
            try:
                # Context를 통해 MCP Resource 직접 호출 (FastMCP 자동 캐싱)
                content = await ctx.read_resource(git_uri)
                
                results["main"] = {
                    "status": "success",
                    "message": "코드를 성공적으로 가져왔습니다",
                    "content": content,
                    "url": url_main,
                    "git_uri": git_uri
                }
            except Exception as e:
                results["main"] = {
                    "status": "error",
                    "message": f"오류: {str(e)}",
                    "content": "",
                    "url": url_main
                }
        else:
            results["main"] = {
                "status": "error",
                "message": "GitHub URL 형식이 올바르지 않습니다",
                "content": "",
                "url": url_main
            }
    
    # 체크 URL 처리  
    if url_chk:
        params = extract_category_function_from_url(url_chk)
        if params:
            git_uri = f"internal://kis-api-chk/{params['category']}/{params['function_name']}"
            try:
                # Context를 통해 MCP Resource 직접 호출 (FastMCP 자동 캐싱)
                content = await ctx.read_resource(git_uri)
                
                results["check"] = {
                    "status": "success",
                    "message": "코드를 성공적으로 가져왔습니다",
                    "content": content,
                    "url": url_chk,
                    "git_uri": git_uri
                }
            except Exception as e:
                results["check"] = {
                    "status": "error",
                    "message": f"오류: {str(e)}",
                    "content": "",
                    "url": url_chk
                }
        else:
            results["check"] = {
                "status": "error",
                "message": "GitHub URL 형식이 올바르지 않습니다",
                "content": "",
                "url": url_chk
            }
    
    # 전체 상태 판단
    if not results:
        return {
            "status": "error",
            "message": "제공된 URL이 없습니다",
            "results": {}
        }
    
    success_count = sum(1 for result in results.values() if result["status"] == "success")
    total_count = len(results)
    
    if success_count == total_count:
        status = "success"
        message = f"모든 코드를 성공적으로 가져왔습니다 ({success_count}/{total_count})"
    elif success_count > 0:
        status = "partial_success"
        message = f"일부 코드를 가져왔습니다 ({success_count}/{total_count})"
    else:
        status = "error"
        message = f"모든 코드 가져오기에 실패했습니다 (0/{total_count})"
    
    return {
        "status": status,
        "message": message,
        "results": results
    }

if __name__ == "__main__":
    # Smithery 배포용 서버 실행
    print("🚀 KIS API Search Server 시작 중...")
    print("📡 MCP 서버 모드로 실행됩니다")
    print("🌐 Smithery에서 사용 가능합니다")
    asyncio.run(mcp.run())
