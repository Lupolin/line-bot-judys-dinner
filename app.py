from flask import Flask, request, abort
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from db import init_db, insert_reply, has_replied_today, get_today_stats, update_reply
from line_service import push_message_to_user  # 保留以供排程通知使用

# ✅ 載入 .env
load_dotenv()

# ✅ 建立 Flask app
app = Flask(__name__)

# ✅ LINE Messaging API 設定
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
api_client = ApiClient(configuration=configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


# ✅ 從 config JSON 取 user name
def get_name_from_config(user_id):
    try:
        with open("users_config.json", encoding="utf-8") as f:
            config = json.load(f)
            for user in config.get("users", []):
                if user["user_id"] == user_id:
                    return user["name"]
    except Exception as e:
        print("[取得使用者名稱錯誤]", e)
    return user_id  # fallback 成 user_id


# ✅ 處理 LINE webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    print("[Webhook Triggered] body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[Webhook Error] Invalid signature.")
        abort(400)
    except Exception as e:
        print("[Webhook Exception]", e)
        abort(500)

    return 'OK'


# ✅ 處理訊息事件
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
        print("[Reply error]", e)


# ✅ 只在開發模式時初始化並啟動 Flask
def main():
    from scheduler import scheduler
    init_db()
    app.run(host="0.0.0.0", port=5002, debug=True)


# ✅ 給 Gunicorn 用：不會跑 main()，但仍能載入 app 與初始化需要的內容
from scheduler import scheduler
init_db()

if __name__ == "__main__":
    main()
