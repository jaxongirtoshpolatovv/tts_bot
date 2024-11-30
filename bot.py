import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

def get_voice_keyboard():
    """Ovoz tanlash uchun keyboard yaratish"""
    keyboard = []
    for voice_name in VOICES.keys():
        keyboard.append([InlineKeyboardButton(voice_name, callback_data=voice_name)])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda salomlashish"""
    await update.message.reply_text(
        "👋 Assalomu alaykum! Men matnni ovozli xabarga aylantirib beruvchi botman.\n\n"
        "📝 Menga istalgan matningizni yuboring, men uni ovozli xabar qilib qaytaraman.\n\n"
        "🎙 Ovozni o'zgartirish uchun /voice buyrug'ini yuboring.\n"
        "❓ Yordam olish uchun /help buyrug'ini yuboring.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam xabarini yuborish"""
    help_text = (
        "🤖 *Bot buyruqlari:*\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam xabarini ko'rsatish\n"
        "/voice - Ovozni o'zgartirish\n\n"
        "💡 *Qo'shimcha ma'lumotlar:*\n"
        "1. Menga istalgan matningizni yuboring\n"
        "2. Men uni tanlangan ovozda o'qib beraman\n"
        "3. Hozirgi ovoz: " + [k for k, v in VOICES.items() if v == current_voice][0]
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ovoz tanlash"""
    keyboard = get_voice_keyboard()
    await update.message.reply_text(
        "🎙 Ovozni tanlang:",
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button bosilganda"""
    global current_voice
    query = update.callback_query
    selected = query.data
    
    if selected in VOICES:
        current_voice = VOICES[selected]
        await query.answer(f"Ovoz {selected} ga o'zgartirildi")
        await query.edit_message_text(
            f"✅ Ovoz {selected} ga o'zgartirildi.\n\nEndi menga matn yuboring."
        )

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnni ovozga o'girish"""
    try:
        # Foydalanuvchi yuborgan xabarni olish
        text = update.message.text
        chat_id = update.message.chat_id
        
        logger.info(f"Yangi xabar qabul qilindi: {text[:50]}...")
        
        # Foydalanuvchiga jarayon boshlanganini bildirish
        status_message = await update.message.reply_text("🎵 Audio tayyorlanmoqda...")
        
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
            "❌ Kechirasiz, xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.\n"
            f"Xatolik: {str(e)}"
        )

async def handle_invalid_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Noto'g'ri turdagi xabarlarni qayta ishlash"""
    message_type = "nomalum"
    if update.message.photo:
        message_type = "rasm"
    elif update.message.video:
        message_type = "video"
    elif update.message.audio:
        message_type = "audio"
    elif update.message.voice:
        message_type = "ovozli xabar"
    elif update.message.document:
        message_type = "fayl"
    elif update.message.sticker:
        message_type = "sticker"
    elif update.message.animation:
        message_type = "GIF"
    elif update.message.video_note:
        message_type = "video xabar"
    
    await update.message.reply_text(
        f"❌ Kechirasiz, men {message_type} bilan ishlay olmayman.\n\n"
        "📝 Iltimos, menga matn yuboring - men uni ovozli xabar qilib qaytaraman.\n"
        "🎙 Ovozni o'zgartirish uchun /voice buyrug'ini yuboring.\n"
        "❓ Yordam olish uchun /help buyrug'ini yuboring."
    )

def run_flask():
    """Flask serverni ishga tushirish"""
    port = int(os.getenv("PORT", os.getenv("KOYEB_PORT", 8000)))
    serve(app, host='0.0.0.0', port=port)
    logger.info(f"Flask server {port}-portda ishga tushdi")

async def run_bot():
    """Botni ishga tushirish"""
    # Bot applicationini yaratish
    application = Application.builder().token(TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voice", voice_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    
    # Noto'g'ri turdagi xabarlarni qayta ishlash
    application.add_handler(MessageHandler(
        filters.PHOTO | 
        filters.VIDEO | 
        filters.AUDIO | 
        filters.VOICE | 
        filters.DOCUMENT | 
        filters.STICKER | 
        filters.ANIMATION | 
        filters.VIDEO_NOTE, 
        handle_invalid_message
    ))

    # Botni ishga tushirish
    logger.info("Bot ishga tushirilmoqda...")
    await application.initialize()
    await application.start()
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Asosiy funksiya"""
    # Flask serverni alohida thread da ishga tushirish
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Botni ishga tushirish
    asyncio.run(run_bot())

if __name__ == '__main__':
    main()
