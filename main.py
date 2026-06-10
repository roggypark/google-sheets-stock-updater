import sys
import logging
from sheet_service import update_stock_prices_in_sheet

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=========================================")
    logger.info(" 국내 주식 현재가 구글 시트 업데이트 시작")
    logger.info("=========================================")
    
    try:
        updated_count = update_stock_prices_in_sheet()
        logger.info(f"성공적으로 {updated_count}개 종목의 현재가를 업데이트했습니다.")
    except Exception as e:
        logger.critical(f"프로그램 실행 중 오류 발생: {e}")
        sys.exit(1)
        
    logger.info("=========================================")
    logger.info(" 프로그램 종료")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
