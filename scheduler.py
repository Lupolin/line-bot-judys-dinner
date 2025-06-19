from datetime import datetime, timedelta
import json
import os
import pytz
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from line_service import push_message_to_user
from db import get_today_stats

# ✅ 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ✅ 設定台灣時區
tz = pytz.timezone("Asia/Taipei")

def get_next_monday():
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # 今天就是週一的話，下一個週一是 7 天後
    next_monday = today + timedelta(days=days_until_monday)
    return next_monday.strftime("%m/%d")  # e.g. 06/24

def load_user_config():
    try:
        if not os.path.exists("users_config.json"):
            logger.warning("找不到 users_config.json，請建立此檔案")
            return {"users": []}
        with open("users_config.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("配置載入錯誤: %s", e)
        return {"users": []}

def send_ask_notification(user):
    next_monday_str = get_next_monday()
    message = f"{user['name']}\n下周一({next_monday_str})要吃晚餐嗎？\n請回覆「要」或「不要」喔！"
    push_message_to_user(user["user_id"], message)
    logger.info("已向 %s 發送詢問通知", user["name"])

def send_summary_notification(user):
    try:
        yes_list, no_list = get_today_stats("all")
        today_str = datetime.now(tz).strftime('%m/%d')

        summary = f"🍽 晚餐統計（{today_str}）\n"
        summary += f"✅ 要吃晚餐（{len(yes_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in yes_list) or "（無）"
        summary += f"\n\n❌ 不吃晚餐（{len(no_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in no_list) or "（無）"

        push_message_to_user(user["user_id"], summary)
        logger.info("已向 %s 發送統計摘要", user["name"])
    except Exception as e:
        logger.error("摘要發送錯誤: %s", e)

def scheduled_notification():
    config = load_user_config()
    current_time = datetime.now(tz)
    current_day = current_time.strftime("%A").lower()
    current_hour = current_time.hour
    current_minute = current_time.minute

    logger.info("排程檢查: %s %02d:%02d（Asia/Taipei）", current_day, current_hour, current_minute)

    for user in config.get("users", []):
        for notification in user.get("notification_times", []):
            if (
                notification["day"] == current_day and
                notification["hour"] == current_hour and
                notification["minute"] == current_minute
            ):
                if notification["type"] == "ask":
                    send_ask_notification(user)
                elif notification["type"] == "summary":
                    send_summary_notification(user)

# ✅ 建立排程器，但不自動啟動（供 app.py 控制）
scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(scheduled_notification, 'cron', minute='*')

# ✅ 對外暴露的排程啟動函式
def start_scheduler():
    scheduler.start()
    logger.info("排程器已啟動（start_scheduler）")
