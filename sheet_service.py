import gspread
from google.oauth2.service_account import Credentials
from gspread import Cell
from datetime import datetime
import logging
from config import (
    SPREADSHEET_ID,
    SHEET_NAME,
    CREDENTIALS_FILE,
    COL_STOCK_CODE,
    COL_CURRENT_PRICE,
    COL_UPDATE_TIME
)
from stock_service import clean_stock_code, get_korean_stock_price

logger = logging.getLogger(__name__)

def get_sheet_client():
    """
    Credentials 파일을 사용하여 gspread 클라이언트를 인증하고 반환합니다.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"구글 API 인증 실패 (credentials.json 파일을 확인하세요): {e}")
        raise e

def update_stock_prices_in_sheet():
    """
    구글 시트의 C열(종목코드)을 읽어서 현재가를 조회한 후 E열(현재가격)에 일괄 업데이트합니다.
    """
    logger.info("구글 시트 연동을 시작합니다...")
    client = get_sheet_client()
    
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID가 설정되지 않았습니다. .env 파일을 확인해 주세요.")
        
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
    except Exception as e:
        logger.error(f"구글 시트를 열 수 없습니다. ID 또는 시트 이름을 확인하세요: {e}")
        raise e
        
    # 모든 행 데이터 가져오기
    all_rows = worksheet.get_all_values()
    if not all_rows:
        logger.warning("시트에 데이터가 없습니다.")
        return
        
    logger.info(f"시트에서 {len(all_rows)}개의 행을 읽어왔습니다 (헤더 포함).")
    
    cells_to_update = []
    updated_count = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2번째 행부터 처리 (1번째 행은 헤더로 가정)
    for row_idx, row in enumerate(all_rows[1:], start=2):
        # C열(종목코드) 가져오기. 리스트는 0-indexed이므로 COL_STOCK_CODE - 1
        if len(row) < COL_STOCK_CODE:
            continue
            
        raw_code = row[COL_STOCK_CODE - 1]
        cleaned_code = clean_stock_code(raw_code)
        
        if not cleaned_code:
            continue
            
        logger.info(f"종목코드 조회 중: {cleaned_code} (행 번호: {row_idx})")
        price = get_korean_stock_price(cleaned_code)
        
        if price is not None:
            # E열 (현재가) 업데이트 셀 생성
            cells_to_update.append(Cell(row=row_idx, col=COL_CURRENT_PRICE, value=price))
            # F열 (업데이트 시간) 업데이트 셀 생성
            cells_to_update.append(Cell(row=row_idx, col=COL_UPDATE_TIME, value=now_str))
            
            # 종목명(B열) 정보 로깅용
            stock_name = row[1] if len(row) > 1 else "알 수 없음"
            logger.info(f"-> {stock_name} ({cleaned_code}) 현재가: {price:,}원")
            updated_count += 1
        else:
            logger.warning(f"-> {cleaned_code} 시세 조회 실패")
            
    if cells_to_update:
        logger.info(f"구글 시트에 현재가 일괄 업데이트 중... (업데이트 대상 종목: {updated_count}개)")
        # USER_ENTERED 옵션을 주어 셀에 문자열 대신 숫자 포맷이 올바르게 들어가도록 설정
        worksheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
        logger.info("구글 시트 업데이트가 완료되었습니다!")
    else:
        logger.warning("업데이트할 가격 데이터가 없습니다.")
        
    return updated_count
