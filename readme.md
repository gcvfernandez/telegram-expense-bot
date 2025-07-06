# Telegram Expense Logger Bot

A personal Telegram bot that logs your daily expenses — via **text** or **receipt images** — directly into a **Google Spreadsheet**.

Built with:
- Python + Flask
- Google Sheets API (`gspread`)
- OCR via Tesseract (`pytesseract`)
- Telegram Bot API

---

## Features

Log expenses via messages like:  
`Dinner at Carlo's Pizza - 500`

Auto-append to a Google Sheet with:
- Date
- Time
- Day of week
- Description
- Amount

Each month's data goes to a separate tab (e.g., `June 2025`)

Upload receipt photos — uses OCR to read and log text

Access **restricted to your Telegram ID**

---

## Requirements

- Python 3.8+
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- Google Cloud Service Account with Sheets access
- A Google Sheet named `MyExpenseSheet` with a `Sheet1` tab (used as template)
- Optional: Railway.app (for free deployment)

---

## Local Setup


### 1. Clone the repository

```bash
git clone https://github.com/gcvfernandez/telegram-expense-bot.git
cd telegram-expense-bot
````

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Create `.env` file

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_CREDS_B64=your_base64_encoded_credentials.json
PORT=5000
```

To get the `GOOGLE_CREDS_B64`, run the following:

```bash
base64 -i credentials.json
```

Copy the entire output and paste it as the value for `GOOGLE_CREDS_B64`.

> **Do NOT upload `credentials.json` directly to GitHub.** Use this method instead.

---

### 4. Set up your Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new sheet named:

   ```
   MyExpenseSheet
   ```

2. Create a `Sheet1` tab with these headers:

   | Date | Time | Weekday | Description | Amount |
   | ---- | ---- | ------- | ----------- | ------ |

3. Share the sheet with the service account email (from your `credentials.json`) and give it **Editor** access.

---

### 5. Run the bot locally (for testing)

```bash
python app.py
```

You should see:

```
 * Running on http://0.0.0.0:5000/
```

---

### 6. Deploy on Railway 

1. Go to [Railway](https://railway.app) and create a new project
2. Connect your GitHub repo
3. Add the following environment variables:

   * `BOT_TOKEN`
   * `GOOGLE_CREDS_B64`
4. Set the start command:

```bash
python app.py
```

5. Go to the **Settings > Generate Domain** section to get your public URL

6. Set your Telegram webhook:

```bash
curl -F "url=https://your-app.up.railway.app/webhook" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

Replace `<YOUR_BOT_TOKEN>` with your actual bot token.

---

### Example Usage

Send messages in this format:

```
Coffee - 150
Lunch with team - 400
Taxi to office - 100
```

Bot will log it in the sheet with:

| Date      | Time  | Weekday | Description     | Amount |
| --------- | ----- | ------- | --------------- | ------ |
| 6/17/2025 | 09:43 | Tuesday | Coffee          | 150    |
| 6/17/2025 | 12:01 | Tuesday | Lunch with team | 400    |

---

### Image Logging

[WIP]

---

### Security

Only you can use the bot. It restricts access by your Telegram ID.
To change this, update the line in `app.py`:
