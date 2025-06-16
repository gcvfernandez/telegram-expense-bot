from flask import Flask, request
import telegram
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv
import base64
from datetime import datetime
import pytz

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=BOT_TOKEN)

# Write base64-decoded content into credentials.json at runtime
b64_creds = os.environ.get("GOOGLE_CREDS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))

# Handle manual text input
def handle_text(message):
    try:
        raw_text = message.text.strip()
        print("Received message text:", raw_text)

        if " - " not in raw_text:
            bot.send_message(chat_id=message.chat.id, text="❌ Format must be: Description - Amount\nExample: Dinner at Carlo's Pizza - 500")
            return

        description, amount = [part.strip() for part in raw_text.split(" - ", 1)]

        # Set timezone to Asia/Manila
        timezone = pytz.timezone("Asia/Manila")
        now = datetime.now(timezone)

        date_str = now.strftime("%-m/%-d/%Y")     # e.g., 6/17/2025
        weekday = now.strftime("%A")              # e.g., Tuesday
        month_tab = now.strftime("%B %Y")         # e.g., June 2025

        # Access the spreadsheet
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet_file = client.open("MyExpenseSheet")

        # Get or create the monthly worksheet
        try:
            sheet = sheet_file.worksheet(month_tab)
        except gspread.exceptions.WorksheetNotFound:
            template = sheet_file.worksheet("Sheet1")
            sheet = template.duplicate(new_sheet_name=month_tab)

        # Append the row
        sheet.append_row([date_str, weekday, description, amount])
        print(f"✅ Row appended to '{month_tab}'.")

        bot.send_message(chat_id=message.chat.id, text=f"✅ Logged to {month_tab}: {description} - ₱{amount}")

    except Exception as e:
        print("Text handling error:", e)
        bot.send_message(chat_id=message.chat.id, text="❌ Something went wrong while logging your expense.")

# Handle image input safely (with fallback)
def handle_image(message):
    try:
        file_id = message.photo[-1].file_id
        file = bot.get_file(file_id)
        file_path = f"temp_{file_id}.jpg"
        file.download(file_path)

        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
        except Exception as e:
            text = "❌ OCR failed: Tesseract not available."
            print("OCR error:", e)

        os.remove(file_path)

        # Default fallback: still log in Sheet1
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("MyExpenseSheet").worksheet("Sheet1")

        sheet.append_row([message.from_user.first_name, text])
        bot.send_message(chat_id=message.chat.id, text=f"🧾 Receipt logged:\n{text}")

    except Exception as e:
        print("Image handling error:", e)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    print("User ID:", update.message.from_user.id)

    if update.message:
        if update.message.text:
            handle_text(update.message)
        elif update.message.photo:
            handle_image(update.message)

    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
