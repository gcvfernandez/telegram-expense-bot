from flask import Flask, request
import telegram
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=BOT_TOKEN)

# Connect to Google Sheet
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open("MyExpenseSheet").sheet1

# Handle manual text input
def handle_text(message):
    sheet = get_sheet()
    sheet.append_row([message.from_user.first_name, message.text])
    bot.send_message(chat_id=message.chat.id, text="✅ Text expense logged.")

# Handle image receipts
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    if update.message:
        if update.message.text:
            handle_text(update.message)

        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file = bot.get_file(file_id)
            file_path = f"temp_{file_id}.jpg"
            file.download(file_path)

            text = pytesseract.image_to_string(Image.open(file_path))
            os.remove(file_path)

            sheet = get_sheet()
            sheet.append_row([update.message.from_user.first_name, text])
            bot.send_message(chat_id=update.message.chat.id, text="🧾 Receipt logged:\n" + text)

    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(port=5000)
