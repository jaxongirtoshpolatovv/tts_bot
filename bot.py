import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import edge_tts
import asyncio
import os
import tempfile
from flask import Flask
import threading
from waitress import serve

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot ishlayapti!'

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Bot tokeni
TOKEN = os.getenv("TOKEN", "7741311977:AAGoqlp5jtfX7zOKeviDVafUWQO89RybAd4")

# Ovozlar
VOICES = {
    "🚹 Erkak ovozi": "uz-UZ-SardorNeural",
    "👩 Ayol ovozi": "uz-UZ-MadinaNeural"
}

# Default ovoz
current_voice = "uz-UZ-SardorNeural"

async def generate_audio(text, voice, output_path):
    """Matnni ovozga o'girish"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda salomlashish"""
    keyboard = [[button] for button in VOICES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Assalomu alaykum! Men matnni ovozli xabarga aylantirib beruvchi botman.\n\n"
        "Ovozni tanlang va menga istalgan matningizni yuboring, "
        "men uni ovozli xabar qilib qaytaraman.",
        reply_markup=reply_markup
    )

async def change_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ovozni o'zgartirish"""
    global current_voice
    selected = update.message.text
    
    if selected in VOICES:
        current_voice = VOICES[selected]
        await update.message.reply_text(f"Ovoz {selected} ga o'zgartirildi. Endi menga matn yuboring.")
    else:
        await text_to_speech(update, context)

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnni ovozga o'girish"""
    try:
        # Foydalanuvchi yuborgan xabarni olish
        text = update.message.text
        chat_id = update.message.chat_id
        
        logger.info(f"Yangi xabar qabul qilindi: {text[:50]}...")
        
        # Foydalanuvchiga jarayon boshlanganini bildirish
        status_message = await update.message.reply_text("Audio tayyorlanmoqda...")
        
        # Vaqtinchalik fayl yaratish
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            audio_path = temp_file.name
            
            # Matnni ovozga o'girish
            await generate_audio(text, current_voice, audio_path)
            
            # Ovozli xabarni yuborish
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title="Text to Speech Audio",
                    performer="TTS Bot"
                )
                logger.info("Audio xabar yuborildi")
            
            # Status xabarni o'chirish
            await status_message.delete()
            
            # Vaqtinchalik faylni o'chirish
            os.unlink(audio_path)
            logger.info("Vaqtinchalik fayl o'chirildi")
        
    except Exception as e:
        error_message = f"Xatolik yuz berdi: {str(e)}"
        logger.error(error_message)
        await update.message.reply_text(
            "Kechirasiz, xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.\n"
            f"Xatolik: {str(e)}"
        )

def run_flask():
    """Flask serverni ishga tushirish"""
    # Koyeb PORT environment variableni olish
    port = int(os.getenv("PORT", os.getenv("KOYEB_PORT", 8000)))
    serve(app, host='0.0.0.0', port=port)
    logger.info(f"Flask server {port}-portda ishga tushdi")

async def run_bot():
    """Botni ishga tushirish"""
    try:
        # Bot applicationini yaratish
        application = Application.builder().token(TOKEN).build()

        # Handlerlarni qo'shish
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.Regex(f"^({'|'.join(VOICES.keys())})$"), change_voice))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

        # Botni ishga tushirish
        logger.info("Bot ishga tushirilmoqda...")
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Bot ishga tushishda xatolik: {e}")
        raise e

async def main():
    """Asosiy funksiya"""
    try:
        # Flask serverni alohida thread da ishga tushirish
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Botni ishga tushirish
        await run_bot()
    except Exception as e:
        logger.error(f"Asosiy funksiyada xatolik: {e}")
        raise e

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
