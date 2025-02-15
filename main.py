import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from transformers import pipeline
import pytz
from datetime import datetime
import schedule
import time
import threading
import logging

# خواندن توکن از متغیر محیطی
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # تغییر این خط

# مدل زبانی برای استخراج تاریخ و زمان
nlp = pipeline("ner", model="dslim/bert-base-NER")

# ذخیره وظایف کاربران
tasks = {}

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('سلام! من بات To-Do List هستم. می‌تونید کارهای خود را به من بگید و من به شما یادآوری می‌کنم.')

def extract_datetime(text):
    # استخراج تاریخ و زمان از متن کاربر
    entities = nlp(text)
    date_time = None
    for entity in entities:
        if entity['entity'] == 'DATE' or entity['entity'] == 'TIME':
            date_time = entity['word']
            break
    return date_time

async def add_task(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text
    date_time = extract_datetime(text)

    if date_time:
        tasks[user_id] = {'task': text, 'datetime': date_time}
        await update.message.reply_text(f'کار شما برای {date_time} ذخیره شد.')
        schedule_reminder(user_id, date_time)
    else:
        await update.message.reply_text('متوجه تاریخ و زمان نشدم. لطفاً دوباره تلاش کنید.')

def schedule_reminder(user_id, date_time):
    # زمان‌بندی ارسال یادآوری
    reminder_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    schedule.every().day.at(reminder_time.strftime('%H:%M')).do(send_reminder, user_id)

async def send_reminder(user_id):
    # ارسال یادآوری به کاربر
    await context.bot.send_message(chat_id=user_id, text=f'یادآوری: کار شما نزدیک است!')

def run_scheduler():
    # اجرای زمان‌بندی‌ها
    while True:
        schedule.run_pending()
        time.sleep(1)

async def main() -> None:
    # ایجاد Application به جای Updater
    application = ApplicationBuilder().token(TOKEN).build()

    # دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_task))

    # اجرای زمان‌بندی‌ها در یک thread جداگانه
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    # شروع بات
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
