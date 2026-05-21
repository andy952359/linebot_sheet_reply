import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")


def _get_sheet():
    # 優先使用環境變數中的 JSON 內容（Render 雲端部署用）
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        # 本機開發：使用 credentials.json 檔案
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.sheet1  # 使用第一個工作表


def search_by(col_index: int, query: str):
    """
    依指定欄位（col_index，1-based）搜尋，
    回傳 (電號, 表號, 有無讀值, 更新時間) tuple，找不到回傳 None。
    欄位結構：A=電號, B=表號, C=有無讀值, D=更新時間
    """
    sheet = _get_sheet()
    col_values = sheet.col_values(col_index)

    for row_index, cell_value in enumerate(col_values[1:], start=2):
        if cell_value.strip() == query.strip():
            row = sheet.row_values(row_index)
            meter_no   = row[0] if len(row) > 0 else "（無資料）"
            table_no   = row[1] if len(row) > 1 else "（無資料）"
            reading    = row[2] if len(row) > 2 else "（無資料）"
            updated_at = row[3] if len(row) > 3 else "（無資料）"
            return meter_no, table_no, reading, updated_at

    return None
