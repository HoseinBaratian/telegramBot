import os
import nest_asyncio
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import logging
import datetime
import pandas as pd
import google.generativeai as genai
import json
import dateparser
import jdatetime

nest_asyncio.apply()

# توکن‌های شما - در حالت واقعی، این مقادیر را در متغیر محیطی ذخیره کنید
TOKEN = '000'
API_KEY = '000'

genai.configure(api_key=API_KEY)

user_tasks = {}
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ایجاد کیبورد آماده
def create_reply_keyboard():
    keyboard = [['اضافه کردن وظیفه جدید'], ['نمایش تسک‌ها']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# تابع برای تجزیه متن و پردازش تاریخ
def parse_task_with_gemini(text):
    model = genai.GenerativeModel('gemini-pro')
    prompt = (
        "Extract the task description from this sentence: '" + text +
        "'. Return a JSON object with key: description."
    )
    response = model.generate_content(prompt)
    try:
        result = json.loads(response.text)
        description = result.get('description', text)
        
        # Parse date and time using dateparser
        parsed_date = dateparser.parse(text, languages=['fa'])
        if parsed_date:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=parsed_date)
            date_str = jalali_date.strftime('%Y-%m-%d')
            time_str = parsed_date.strftime('%H:%M')
            return date_str, time_str, description
        else:
            return 'نامشخص', 'نامشخص', description
    except Exception as e:
        logger.error(f'Error parsing with Gemini: {e}')
        return 'نامشخص', 'نامشخص', text

# تابع شروع
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = create_reply_keyboard()
    await update.message.reply_text(
        'سلام! لطفا یک گزینه را انتخاب کنید:',
        reply_markup=keyboard
    )

# تابع نمایش تسک‌ها
async def show_tasks(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_tasks and not user_tasks[user_id].empty:
        tasks_str = user_tasks[user_id].to_string(index=False)
        await update.message.reply_text(f'📋 لیست وظایف شما:\n{tasks_str}')
    else:
        await update.message.reply_text('🔹 هنوز وظیفه‌ای ثبت نشده است.')

# تابع اضافه کردن تسک
async def add_task(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text
    try:
        day, time, description = parse_task_with_gemini(text)
        if day == 'نامشخص' or time == 'نامشخص':
            await update.message.reply_text('❌ نتوانستم تاریخ و زمان را تشخیص دهم. لطفا به فرمت دقیق‌تری بنویسید.')
            return
        if user_id not in user_tasks:
            user_tasks[user_id] = pd.DataFrame(columns=['روز', 'ساعت', 'شرح'])
        user_tasks[user_id] = pd.concat([
            user_tasks[user_id],
            pd.DataFrame({'روز': [day], 'ساعت': [time], 'شرح': [description]})
        ], ignore_index=True)
        await update.message.reply_text(f'✅ وظیفه «{description}» برای {day} ساعت {time} ذخیره شد.')
    except Exception as e:
        logger.error(f'Error adding task: {e}')
        await update.message.reply_text('❌ خطا در ثبت وظیفه. دوباره تلاش کنید.')

# تابع مدیریت پیام‌ها
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == 'اضافه کردن وظیفه جدید':
        await update.message.reply_text('لطفا وظیفه جدید را وارد کنید:')
    elif text == 'نمایش تسک‌ها':
        await show_tasks(update, context)
    else:
        await add_task(update, context)

# تابع اصلی
async def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
