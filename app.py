from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
import os
from db import init_db
import logging

# ✅ 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ✅ 初始化 Flask 應用
app = Flask(__name__)

# ✅ 初始化 LINE 設定
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not channel_secret or not channel_access_token:
    logger.error("請設定 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN")
    exit(1)

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(ApiClient(configuration))

# ✅ 發送回覆

def reply(event, text):
    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text)]
            )
        )
    except Exception as e:
        logger.error("[Reply error] %s", e)

# ✅ Webhook 路由

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    logger.info("[Callback] Request body: %s", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature. Check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# ✅ 接收文字訊息事件

@handler.add(TextMessage)
def handle_message(event):
    user_text = event.text.strip()
    logger.info("[Received] %s", user_text)

    if user_text == "ping":
        reply(event, "pong")
    elif user_text == "hi":
        reply(event, "哈囉！")
    else:
        reply(event, f"你說了：{user_text}")

# ✅ 初始化（給 Gunicorn 用）
init_db()

# ✅ 若用 python app.py 啟動則使用內建伺服器

def main():
    init_db()
    app.run(host="0.0.0.0", port=5002, debug=True)

if __name__ == "__main__":
    main()
