from flask import Flask, request, abort
from dotenv import load_dotenv
import os
from datetime import datetime
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from db import init_db, insert_reply, has_replied_today, get_today_stats, update_reply
from line_service import get_group_member_name

load_dotenv()
app = Flask(__name__)

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
api_client = ApiClient(configuration=configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        source_type = event.source.type
        user_id = event.source.user_id
        group_id = getattr(event.source, 'group_id', None)
        reply_text = event.message.text.strip()

        print(f"[MessageEvent] 來源 {source_type}，使用者 {user_id}，訊息：{reply_text}")

        # 查詢統計指令（僅限群組內）
        if reply_text in ["統計", "晚餐"] and group_id:
            yes_list, no_list = get_today_stats(group_id)
            yes_names = "\n".join(f"- {name}" for name in yes_list)
            no_names = "\n".join(f"- {name}" for name in no_list)
            response = f"🍽 晚餐統計（{datetime.now().strftime('%m/%d')}）\n"
            response += f"✅ 要吃晚餐（{len(yes_list)}人）:\n{yes_names or '（無）'}\n\n"
            response += f"❌ 不吃晚餐（{len(no_list)}人）:\n{no_names or '（無）'}"
            reply(event, response)
            return

        # 靜默記錄「要 / 不要」
        if reply_text in ["要", "不要", "yes", "Yes", "no", "No"]:
            try:
                user_name = get_group_member_name(group_id, user_id) if group_id else user_id
            except Exception as e:
                print("[get_group_member_name error]", e)
                user_name = "匿名使用者"

            try:
                if has_replied_today(group_id or user_id, user_id):
                    updated = update_reply(group_id or user_id, user_id, reply_text)
                    if updated:
                        print(f"[記錄更新] 使用者 {user_name} 已更新為「{reply_text}」")
                    else:
                        print(f"[記錄略過] 使用者 {user_name} 已回覆相同內容「{reply_text}」，略過")
                else:
                    insert_reply(group_id or user_id, user_id, user_name, reply_text)
                    print(f"[記錄新增] 使用者 {user_name} 新增「{reply_text}」")
            except Exception as e:
                print("[資料庫錯誤]", e)
            return

    except Exception as e:
        print("[Unhandled error in handle_message]", e)

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

if __name__ == "__main__":
    from scheduler import scheduler
    init_db()
    app.run(host="0.0.0.0", port=5000)
