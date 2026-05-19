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


def search_meter(meter_id: str):
    """
    在 A 欄搜尋電表編號，回傳 (有無讀值, 更新時間) tuple。
    找不到回傳 None。
    """
    sheet = _get_sheet()
    # 取得 A 欄所有電表編號
    meter_ids = sheet.col_values(1)

    # 從第 2 列開始搜尋（跳過標題列）
    for row_index, cell_value in enumerate(meter_ids[1:], start=2):
        if cell_value.strip() == meter_id.strip():
            row = sheet.row_values(row_index)
            reading_status = row[1] if len(row) > 1 else "（無資料）"
            update_time = row[2] if len(row) > 2 else "（無資料）"
            return reading_status, update_time

    return None
