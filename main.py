from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import datetime
import dateparser
from apscheduler.schedulers.background import BackgroundScheduler

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# گرفتن توکن از متغیر محیطی
TOKEN = "7670540618:AAEWwCquj0h3ErWoWX8OLnv2puMHLozbtBg"
bot = Application.builder().token(TOKEN).build()

# ذخیره‌ی وظایف
reminders = {}

# تعریف دستور /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("سلام! من یک بات یادآوری هستم. زمان یادآوری خود را ارسال کنید.")

# ثبت یادآوری
async def set_reminder(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})

    if date:
        reminders[chat_id] = date
        await update.message.reply_text(f"یادآوری تنظیم شد برای: {date}")
    else:
        await update.message.reply_text("زمان مشخص نیست. لطفاً دقیق‌تر بفرست.")

# چک کردن زمان یادآوری
def check_reminders():
    now = datetime.datetime.now()
    for chat_id, date in list(reminders.items()):
        if now >= date:
            bot.bot.send_message(chat_id=chat_id, text="🚀 یادت نره! زمانش رسید!")
            del reminders[chat_id]

# زمان‌بندی اجرای چک کردن یادآوری
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()

# تنظیمات تلگرام
def main():
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder))

    bot.run_polling()

if __name__ == '__main__':
    main()
