# 🍱 LINE 晚餐回覆統計系統

本系統是一個使用 LINE Bot + Flask 打造的互動問卷系統，能定時詢問使用者是否吃晚餐並回收回覆，最終回傳統計報告。

---

## ✨ 功能特色

- 🕒 **定時推送**：依照 `users_config.json` 設定，自動發送「晚餐要不要」或統計摘要訊息
- 🗣️ **簡單互動**：使用者只需傳「要」或「不要」即可完成回覆
- 📊 **回覆統計**：傳「統計」或「晚餐」關鍵字即可取得當日統計報告
- 👤 **識別暱稱**：透過 LINE ID 自動對應至使用者設定的名稱
- 💾 **本地儲存**：使用 SQLite 資料庫保存所有回覆

---

## 🗂️ 專案結構

```
.
├── app.py                 # 主程式，處理 LINE webhook 與回覆邏輯
├── scheduler.py           # 定時推播邏輯（依據 user 設定時間觸發）
├── db.py                  # SQLite 操作模組（儲存與查詢回覆）
├── line_service.py        # LINE API 操作（例如推播訊息）
├── users_config.json      # 使用者與通知時間設定
├── reply.db               # SQLite 回覆資料庫（自動建立）
├── .env                   # 儲存 LINE channel 憑證
└── README.md              # 專案說明文件
```

---

## ⚙️ 安裝與啟動

### 1. 安裝相依套件

```bash
pip install flask line-bot-sdk python-dotenv apscheduler
```

### 2. 建立 `.env` 檔案

請在根目錄建立 `.env`，並填入你的 LINE 憑證：

```
LINE_CHANNEL_ACCESS_TOKEN=你的ChannelAccessToken
LINE_CHANNEL_SECRET=你的ChannelSecret
```

### 3. 啟動伺服器

```bash
python app.py
```

### 4. 使用 ngrok（對外公開 webhook）

```bash
ngrok http 5000
```

並將產生的網址設定為 LINE Developers 裡的 Webhook URL，例如：

```
https://xxxxxx.ngrok.io/callback
```

---

## 👥 新增/編輯使用者設定

請打開 `users_config.json` 並加入使用者區塊：

```json
{
  "user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "name": "Lucas",
  "notification_times": [
    { "day": "monday", "hour": 9, "minute": 0, "type": "ask" },
    { "day": "friday", "hour": 17, "minute": 0, "type": "summary" }
  ]
}
```

- `type: "ask"` → 問「今天要吃晚餐嗎？」
- `type: "summary"` → 回傳當日統計報告

新增後重啟 `app.py` 即生效。

---

## 📊 使用說明

### 使用者互動：

| 操作                   | 說明                     |
| ---------------------- | ------------------------ |
| 傳送「要」             | 記錄為要吃晚餐           |
| 傳送「不要」           | 記錄為不吃晚餐           |
| 傳送「統計」或「晚餐」 | 顯示今日統計（不限群組） |

---

## 🧪 開發建議與擴充方向

- [ ] 顯示「尚未回覆」者清單
- [ ] 將訊息改為 Flex Message 美化格式
- [ ] 增加其他問卷項目（如午餐、飲料等）
- [ ] 使用 Web UI 管理 `users_config.json`
- [ ] 將儲存改為使用 ORM 或遠端資料庫

---

## 🪪 授權

本專案使用 MIT License，自由修改與散佈。
