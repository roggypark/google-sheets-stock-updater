import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 구글 시트 ID 및 시트 이름
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")

# 구글 API 인증 파일 경로
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")

# 시트 내 열(Column) 인덱스 정의 (gspread는 1부터 시작)
COL_STOCK_NAME = 2   # B열 (종목명)
COL_STOCK_CODE = 3   # C열 (종목코드)
COL_HOLDING_QTY = 4  # D열 (보유수량)
COL_CURRENT_PRICE = 5 # E열 (현재가)
COL_UPDATE_TIME = 6   # F열 (업데이트 시간, 추가 가능)
