from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import datetime
import dateparser
from apscheduler.schedulers.background import BackgroundScheduler
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# گرفتن توکن از متغیر محیطی
TOKEN = "7670540618:AAEWwCquj0h3ErWoWX8OLnv2puMHLozbtBg"
bot = Application.builder().token(TOKEN).build()

# لود مدل هوش مصنوعی رایگان (mT5-Small که از فارسی پشتیبانی می‌کند)
model_name = "google/mt5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def extract_time(text):
    prompt = f"""
    متن زیر را تحلیل کن و تاریخ و ساعت دقیق را استخراج کن.
    اگر متن شامل تاریخ نیست، مقدار None را برگردان.
    متن: "{text}"
    خروجی:
    """
    
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=50)
    parsed_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return dateparser.parse(parsed_text, settings={'PREFER_DATES_FROM': 'future'})

# ذخیره‌ی وظایف
reminders = {}

# دستور /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("سلام! من یک بات یادآوری هستم. زمان یادآوری خود را ارسال کنید.")

# ثبت یادآوری
async def set_reminder(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    date = extract_time(text)

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
