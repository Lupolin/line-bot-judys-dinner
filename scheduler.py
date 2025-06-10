from apscheduler.schedulers.background import BackgroundScheduler
from line_service import push_message_to_user
import json
import datetime
import os

def schedule_push():
    today = datetime.datetime.now().strftime("%a").lower()  # 'mon', 'tue', etc.

    try:
        if not os.path.exists("user_config.json"):
            print("[警告] 找不到 user_config.json 檔案，略過推播")
            return

        with open("user_config.json", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print("[警告] user_config.json 是空的，略過推播")
                return

            users = json.loads(content)

        for user in users:
            if today in user.get("days", []):
                push_message_to_user(
                    user["user_id"],
                    f"{user['name']}，今天要吃晚餐嗎？請回覆「要」或「不要」喔！"
                )

    except Exception as e:
        print("[Scheduler Error]", e)

scheduler = BackgroundScheduler()
scheduler.add_job(schedule_push, 'cron', hour=16, minute=34)
scheduler.start()
