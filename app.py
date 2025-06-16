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

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=BOT_TOKEN)

# Write base64-decoded content into credentials.json at runtime
b64_creds = os.environ.get("GOOGLE_CREDS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))

# Connect to Google Sheet
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("MyExpenseSheet").worksheet("Sheet1")
    return sheet

# Handle manual text input
def handle_text(message):
    try:
        raw_text = message.text.strip()
        print("Received message text:", raw_text)

        # Split by ' - ' to get description and amount
        if " - " not in raw_text:
            bot.send_message(chat_id=message.chat.id, text="❌ Format must be: Description - Amount\nExample: Dinner at Carlo's Pizza - 500")
            return

        description, amount = [part.strip() for part in raw_text.split(" - ", 1)]

        # Get current date and weekday
        now = datetime.now()
        date_str = now.strftime("%-m/%-d/%Y")  # e.g., 6/17/2025 (use %#m on Windows if needed)
        weekday = now.strftime("%A")           # e.g., Tuesday

        # Log to sheet
        sheet = get_sheet()
        sheet.append_row([date_str, weekday, description, amount])
        print("✅ Row appended.")

        bot.send_message(chat_id=message.chat.id, text=f"✅ Logged: {description} - ₱{amount}")

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

        sheet = get_sheet()
        sheet.append_row([message.from_user.first_name, text])
        bot.send_message(chat_id=message.chat.id, text=f"🧾 Receipt logged:\n{text}")

    except Exception as e:
        print("Image handling error:", e)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

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
