import yfinance as yf
import logging

logger = logging.getLogger(__name__)

def clean_stock_code(raw_code):
    """
    주식 종목코드를 6자리 문자열로 정규화합니다.
    예: 5930 (int) -> '005930'
        ' 35720 ' -> '035720'
        '005930.KS' -> '005930'
    """
    if raw_code is None:
        return None
        
    code_str = str(raw_code).strip()
    
    # .KS 또는 .KQ 접미사가 있으면 제거
    if code_str.upper().endswith('.KS') or code_str.upper().endswith('.KQ'):
        code_str = code_str[:-3]
        
    # 숫자만 남기기
    code_str = ''.join(c for c in code_str if c.isdigit())
    
    if not code_str:
        return None
        
    # 6자리로 맞춰서 앞부분에 0을 채움
    return code_str.zfill(6)

def _get_price_from_naver(code):
    """
    네이버 금융에서 실시간 현재가와 전일 종가를 크롤링하여 반환합니다 (지연 없음).
    """
    import urllib.request
    import re
    
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    # 네이버 차단 방지를 위한 User-Agent 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('euc-kr', errors='ignore')
            # 현재가가 담긴 no_today 영역의 blind 스팬 검색
            match_today = re.search(r'class="no_today".*?<span class="blind">([0-9,]+)</span>', html, re.DOTALL)
            price = int(match_today.group(1).replace(',', '')) if match_today else None
            
            # 전일 종가 검색 (sp_txt2 가 "전일" 텍스트 이미지)
            match_prev = re.search(r'class="first".*?sp_txt2.*?blind">([0-9,]+)</span>', html, re.DOTALL)
            prev_close = int(match_prev.group(1).replace(',', '')) if match_prev else None
            
            if price is not None and prev_close is not None:
                return price, prev_close
    except Exception as e:
        logger.debug(f"네이버 금융 현재가/전일가 조회 실패 ({code}): {e}")
    return None

def get_korean_stock_price(code):
    """
    6자리 종목코드에 대해 네이버 금융 실시간 가격 및 전일 종가를 우선 조회하고,
    실패 시 yfinance를 백업으로 조회하여 반환합니다.
    반환값: {"price": 현재가, "prev_close": 전일종가} 또는 실패 시 None
    """
    cleaned_code = clean_stock_code(code)
    if not cleaned_code:
        logger.warning(f"유효하지 않은 종목코드 형식: {code}")
        return None
        
    # 1. 네이버 금융 실시간 현재가/전일가 시도 (실시간, 지연 없음)
    res = _get_price_from_naver(cleaned_code)
    if res is not None:
        price, prev_close = res
        return {"price": price, "prev_close": prev_close}
        
    logger.info(f"네이버 금융 조회 실패로 yfinance 백업 조회를 시작합니다: {cleaned_code}")
    
    # 2. 백업: 코스피 (.KS) 시도
    try:
        ticker_ks = yf.Ticker(f"{cleaned_code}.KS")
        price = ticker_ks.fast_info.get('lastPrice')
        prev_close = ticker_ks.fast_info.get('previousClose')
        if price is not None and not (isinstance(price, float) and str(price) == 'nan'):
            p_val = int(round(price))
            pc_val = int(round(prev_close)) if prev_close is not None else p_val
            return {"price": p_val, "prev_close": pc_val}
    except Exception as e:
        logger.debug(f"코스피({cleaned_code}.KS) 백업 조회 실패: {e}")
        
    # 3. 백업: 코스닥 (.KQ) 시도
    try:
        ticker_kq = yf.Ticker(f"{cleaned_code}.KQ")
        price = ticker_kq.fast_info.get('lastPrice')
        prev_close = ticker_kq.fast_info.get('previousClose')
        if price is not None and not (isinstance(price, float) and str(price) == 'nan'):
            p_val = int(round(price))
            pc_val = int(round(prev_close)) if prev_close is not None else p_val
            return {"price": p_val, "prev_close": pc_val}
    except Exception as e:
        logger.debug(f"코스닥({cleaned_code}.KQ) 백업 조회 실패: {e}")
        
    logger.error(f"종목코드 {cleaned_code}의 현재가 및 전일가를 조회할 수 없습니다.")
    return None

def fetch_prices_batch(codes):
    """
    여러 종목코드의 현재가/전일가 정보를 딕셔너리 형태로 한 번에 조회합니다.
    """
    results = {}
    for code in codes:
        cleaned = clean_stock_code(code)
        if not cleaned:
            continue
        res = get_korean_stock_price(cleaned)
        if res is not None:
            results[cleaned] = res
    return results

