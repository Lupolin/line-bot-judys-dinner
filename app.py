from flask import Flask, request, abort
from datetime import datetime
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3 import WebhookHandler
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
import os
from db import (
    init_db,
    get_today_stats,
    has_replied_today,
    update_reply,
    insert_reply,
    get_name_from_config  # <-- 這是前面補過的函式
)
from scheduler import start_scheduler
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

# ✅ 處理訊息事件Add commentMore actions
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        user_id = event.source.user_id
        reply_text = event.message.text.strip()
        user_name = get_name_from_config(user_id)

        print(f"[MessageEvent] 使用者 {user_id}（{user_name}）輸入：{reply_text}")

        # 📊 查詢統計
        if reply_text in ["統計", "晚餐"]:
            yes_list, no_list = get_today_stats("all")
            yes_names = "\n".join(f"- {name}" for name in yes_list)
            no_names = "\n".join(f"- {name}" for name in no_list)
            response = f"🍽 晚餐統計（{datetime.now().strftime('%m/%d')}）\n"
            response += f"✅ 要吃晚餐（{len(yes_list)}人）:\n{yes_names or '（無）'}\n\n"
            response += f"❌ 不吃晚餐（{len(no_list)}人）:\n{no_names or '（無）'}"
            reply(event, response)
            return

        # ✅ 回覆「要 / 不要」
        if reply_text in ["要", "不要", "yes", "Yes", "no", "No"]:
            group_or_user_id = user_id
            try:
                if has_replied_today(group_or_user_id, user_id):
                    updated = update_reply(group_or_user_id, user_id, reply_text)
                    if updated:
                        print(f"[記錄更新] {user_name} 已更新為「{reply_text}」")
                    else:
                        print(f"[記錄略過] {user_name} 已回覆相同內容「{reply_text}」，略過")
                else:
                    insert_reply(group_or_user_id, user_id, user_name, reply_text)
                    print(f"[記錄新增] {user_name} 回覆「{reply_text}」")
            except Exception as e:
                print("[資料庫錯誤]", e)
            return

    except Exception as e:
        print("[Unhandled error in handle_message]", e)

# ✅ 初始化（給 Gunicorn 或本地開發使用）
init_db()

def main():
    print("✅ Running local Flask server")
    start_scheduler()
    app.run(host="0.0.0.0", port=5002, debug=False)

# ✅ 若是本地執行，跑 main()（含 scheduler 與 app.run）
# ✅ 若是 Gunicorn，則由環境變數控制是否啟動 scheduler
if __name__ == "__main__":
    main()
elif os.environ.get("RUN_SCHEDULER") == "true":
    print("✅ Starting scheduler under Gunicorn")
    start_scheduler()
