import os
import hashlib
import hmac
import base64

from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from sheet import search_by

load_dotenv()

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


@app.route("/", methods=["GET"])
def index():
    return "LINE Bot server is running.", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


USAGE = "請輸入查詢指令：\n電號 <號碼>\n表號 <號碼>\n例如：電號 100"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_input = event.message.text.strip()

    # 解析指令格式：「電號XXX」或「表號XXX」（有無空格皆可）
    if user_input.startswith("電號"):
        query = user_input[2:].strip()
        col_index = 1  # A 欄
    elif user_input.startswith("表號"):
        query = user_input[2:].strip()
        col_index = 2  # B 欄
    else:
        reply_text = USAGE
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        return

    result = search_by(col_index, query)

    if result is None:
        reply_text = f"查無「{user_input}」，請確認後再試。"
    else:
        meter_no, table_no, reading, updated_at = result
        reply_text = (
            f"電號：{meter_no}\n"
            f"表號：{table_no}\n"
            f"有無讀值：{reading}\n"
            f"更新時間：{updated_at}"
        )

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
