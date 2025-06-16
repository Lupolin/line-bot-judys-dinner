import sqlite3
from datetime import datetime
import json
import os

db_path = "reply.db"

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            user_id TEXT,
            user_name TEXT,
            reply_text TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_reply(group_id, user_id, user_name, reply_text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO replies (group_id, user_id, user_name, reply_text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (group_id, user_id, user_name, reply_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def has_replied_today(group_id, user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM replies
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (group_id, user_id, today))
    result = c.fetchone()[0]
    conn.close()
    return result > 0

def update_reply(group_id, user_id, reply_text):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT reply_text FROM replies
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (group_id, user_id, today))
    row = c.fetchone()
    if row is None:
        conn.close()
        return False
    if row[0] == reply_text:
        conn.close()
        return False

    c.execute('''
        UPDATE replies
        SET reply_text = ?, timestamp = ?
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (reply_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), group_id, user_id, today))
    conn.commit()
    conn.close()
    return True

def get_today_stats(group_id=None):
    """獲取今天的統計，支援特定群組或全局統計"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if group_id == "all" or group_id is None:
        # 獲取所有用戶的統計
        c.execute('''
            SELECT user_name, reply_text FROM replies
            WHERE DATE(timestamp) = ?
        ''', (today,))
    else:
        # 獲取特定群組的統計
        c.execute('''
            SELECT user_name, reply_text FROM replies
            WHERE group_id = ? AND DATE(timestamp) = ?
        ''', (group_id, today))
    
    rows = c.fetchall()
    conn.close()

    yes_list = [row[0] for row in rows if row[1] in ["要", "yes", "Yes"]]
    no_list = [row[0] for row in rows if row[1] in ["不要", "no", "No"]]
    return yes_list, no_list

# 新增程式碼
def get_name_from_config(user_id):
    config_path = "users_config.json"
    if not os.path.exists(config_path):
        return "未知使用者"
    
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
            for user in data.get("users", []):
                if user.get("user_id") == user_id:
                    return user.get("name", "未知使用者")
    except Exception:
        return "未知使用者"
    
    return "未知使用者"