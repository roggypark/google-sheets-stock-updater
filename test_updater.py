import unittest
from unittest.mock import patch, MagicMock
from gspread import Cell

# Setup path and environment mock before import
import os
os.environ["SPREADSHEET_ID"] = "mock_spreadsheet_id"
os.environ["SHEET_NAME"] = "Sheet1"
os.environ["CREDENTIALS_FILE"] = "mock_credentials.json"

import sheet_service

class TestStockUpdater(unittest.TestCase):
    
    @patch('sheet_service.Credentials')
    @patch('sheet_service.gspread.authorize')
    @patch('sheet_service.get_korean_stock_price')
    def test_update_stock_prices_in_sheet(self, mock_get_price, mock_authorize, mock_credentials):
        # 1. Mock Credentials and gspread Client
        mock_client = MagicMock()
        mock_authorize.return_value = mock_client
        
        # 2. Mock Spreadsheet and Worksheet
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        # 3. Mock Sheet Data (Row 1: Header, Row 2-4: Stock items)
        # B column: Name, C column: Code, D column: Qty
        # C is index 2, E is index 4 (COL_CURRENT_PRICE = 5, so index 4)
        mock_worksheet.get_all_values.return_value = [
            ["번호", "종목명", "종목코드", "보유수량", "현재가격", "업데이트시간"],
            ["1", "삼성전자", "005930", "10", "", ""],
            ["2", "카카오", "035720", "5", "50000", ""],
            ["3", "잘못된코드", "INVALID", "2", "", ""]
        ]
        
        # 4. Mock Price Fetching
        # Return {"price": 73500, "prev_close": 73000} for Samsung, {"price": 48000, "prev_close": 49000} for Kakao
        def side_effect(code):
            if code == "005930":
                return {"price": 73500, "prev_close": 73000}
            elif code == "035720":
                return {"price": 48000, "prev_close": 49000}
            return None
        mock_get_price.side_effect = side_effect
        
        # 5. Run the function
        updated_count = sheet_service.update_stock_prices_in_sheet()
        
        # 6. Verify assertions
        self.assertEqual(updated_count, 2)  # Should update Samsung and Kakao, skip invalid code
        
        # Verify worksheet opening parameters
        mock_client.open_by_key.assert_called_with("mock_spreadsheet_id")
        mock_spreadsheet.worksheet.assert_called_with("Sheet1")
        
        # Verify update_cells was called
        self.assertTrue(mock_worksheet.update_cells.called)
        
        # Check details of update_cells argument
        called_args, _ = mock_worksheet.update_cells.call_args
        cells = called_args[0]
        
        # Samsung Electronics (Row 2): Price at E (Col 5) = 73500, Diff at F (Col 6) = 500, Time at G (Col 7)
        samsung_price_cell = next((c for c in cells if c.row == 2 and c.col == 5), None)
        samsung_diff_cell = next((c for c in cells if c.row == 2 and c.col == 6), None)
        samsung_time_cell = next((c for c in cells if c.row == 2 and c.col == 7), None)
        
        # Kakao (Row 3): Price at E (Col 5) = 48000, Diff at F (Col 6) = -1000, Time at G (Col 7)
        kakao_price_cell = next((c for c in cells if c.row == 3 and c.col == 5), None)
        kakao_diff_cell = next((c for c in cells if c.row == 3 and c.col == 6), None)
        
        self.assertIsNotNone(samsung_price_cell)
        self.assertEqual(samsung_price_cell.value, 73500)
        self.assertIsNotNone(samsung_diff_cell)
        self.assertEqual(samsung_diff_cell.value, 500)
        self.assertIsNotNone(samsung_time_cell)
        self.assertTrue(samsung_time_cell.value != "")
        
        self.assertIsNotNone(kakao_price_cell)
        self.assertEqual(kakao_price_cell.value, 48000)
        self.assertIsNotNone(kakao_diff_cell)
        self.assertEqual(kakao_diff_cell.value, -1000)


if __name__ == '__main__':
    unittest.main()
