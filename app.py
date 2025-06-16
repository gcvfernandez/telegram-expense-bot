from flask import Flask, request
import telegram
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv
import base64

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
    print("Received message text:", message.text)
    print("From user:", message.from_user.first_name)

    sheet = get_sheet()
    sheet.append_row([message.from_user.first_name, message.text])
    print("✅ Row appended.")
    bot.send_message(chat_id=message.chat.id, text="✅ Text expense logged.")

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
