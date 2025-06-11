from apscheduler.schedulers.background import BackgroundScheduler
from line_service import push_message_to_user
from db import get_today_stats
import json
import datetime
import os
import pytz
import logging

# ✅ 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 如果沒有 handler，就加上一個
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 設定台灣時區
tz = pytz.timezone("Asia/Taipei")

def load_user_config():
    """載入用戶配置"""
    try:
        if not os.path.exists("users_config.json"):
            logger.warning("找不到 users_config.json，請建立此檔案")
            return {"users": []}
        
        with open("users_config.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"配置載入錯誤: {e}")
        return {"users": []}

def send_ask_notification(user):
    """發送詢問通知"""
    message = f"{user['name']}，今天要吃晚餐嗎？請回覆「要」或「不要」喔！"
    push_message_to_user(user["user_id"], message)
    logger.info(f"已向 {user['name']} 發送詢問通知")

def send_summary_notification(user):
    """發送統計摘要通知"""
    try:
        yes_list, no_list = get_today_stats("all")
        today_str = datetime.datetime.now(tz).strftime('%m/%d')
        summary = f"🍽 晚餐統計（{today_str}）\n"
        summary += f"✅ 要吃晚餐（{len(yes_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in yes_list) or "（無）"
        summary += f"\n\n❌ 不吃晚餐（{len(no_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in no_list) or "（無）"

        push_message_to_user(user["user_id"], summary)
        logger.info(f"已向 {user['name']} 發送統計摘要")
    except Exception as e:
        logger.error(f"摘要發送錯誤: {e}")

def scheduled_notification():
    """定時通知處理"""
    config = load_user_config()
    current_time = datetime.datetime.now(tz)
    current_day = current_time.strftime("%A").lower()
    current_hour = current_time.hour
    current_minute = current_time.minute

    logger.info(f"排程檢查: {current_day} {current_hour:02d}:{current_minute:02d}（Asia/Taipei）")

    for user in config.get("users", []):
        for notification in user.get("notification_times", []):
            if (notification["day"] == current_day and
                notification["hour"] == current_hour and
                notification["minute"] == current_minute):

                if notification["type"] == "ask":
                    send_ask_notification(user)
                elif notification["type"] == "summary":
                    send_summary_notification(user)

# ✅ 設置排程器
scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(scheduled_notification, 'cron', minute='*')
scheduler.start()

logger.info("個人化通知系統已啟動（Asia/Taipei）")