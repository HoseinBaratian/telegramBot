import os
import logging
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import dateparser

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# گرفتن توکن از متغیر محیطی
TOKEN = os.getenv("BOT_TOKEN")  # مقدار رو از متغیر محیطی بگیر
bot = telegram.Bot(token=TOKEN)

# ذخیره‌ی وظایف
reminders = {}

# تعریف دستور /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("سلام! من یک بات یادآوری هستم. زمان یادآوری خود را ارسال کنید.")

# ثبت یادآوری
def set_reminder(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    chat_id = update.message.chat_id
    date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})

    if date:
        reminders[chat_id] = date
        update.message.reply_text(f"یادآوری تنظیم شد برای: {date}")
    else:
        update.message.reply_text("زمان مشخص نیست. لطفاً دقیق‌تر بفرست.")

# چک کردن زمان یادآوری
def check_reminders():
    now = datetime.datetime.now()
    for chat_id, date in list(reminders.items()):
        if now >= date:
            bot.send_message(chat_id, "🚀 یادت نره! زمانش رسید!")
            del reminders[chat_id]

# زمان‌بندی اجرای چک کردن یادآوری
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()

# تنظیمات تلگرام
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder))

    app.run_polling()

if __name__ == '__main__':
    main()
