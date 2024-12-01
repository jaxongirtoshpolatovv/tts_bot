import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import edge_tts
import asyncio
import os
import tempfile
from dotenv import load_dotenv
import nest_asyncio

# Enable nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Get bot token from environment variables
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Voices
VOICES = {
    "🚹 Erkak ovozi": "uz-UZ-SardorNeural",
    "👩 Ayol ovozi": "uz-UZ-MadinaNeural"
}

# Default voice
current_voice = "uz-UZ-SardorNeural"

def get_voice_keyboard():
    """Create voice selection keyboard"""
    keyboard = []
    for voice_name in VOICES.keys():
        keyboard.append([InlineKeyboardButton(voice_name, callback_data=voice_name)])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text(
        "👋 Assalomu alaykum! Men matnni ovozli xabarga aylantirib beruvchi botman.\n\n"
        "📝 Menga istalgan matningizni yuboring, men uni ovozli xabar qilib qaytaraman.\n\n"
        "🎙 Ovozni o'zgartirish uchun /voice buyrug'ini yuboring.\n"
        "❓ Yordam olish uchun /help buyrug'ini yuboring."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    current_voice_name = [k for k, v in VOICES.items() if v == current_voice][0]
    help_text = (
        "🤖 *Bot buyruqlari:*\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam xabarini ko'rsatish\n"
        "/voice - Ovozni o'zgartirish\n\n"
        "💡 *Qo'shimcha ma'lumotlar:*\n\n"
        "1. Menga istalgan matningizni yuboring\n"
        "2. Men uni ovozli xabar qilib qaytaraman\n"
        "3. Audio fayl nomi yuborilgan matningizning birinchi 2 ta so'zidan hosil qilinadi\n"
        f"4. Hozirgi tanlangan ovoz: {current_voice_name}"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice selection command handler"""
    keyboard = get_voice_keyboard()
    await update.message.reply_text(
        "🎙 Ovozni tanlang:",
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
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
    """Text to speech handler"""
    status_message = None
    audio_path = None
    
    try:
        text = update.message.text
        if not text:
            await update.message.reply_text("❌ Matn bo'sh bo'lishi mumkin emas!")
            return
        
        if len(text) > 1000:
            await update.message.reply_text("❌ Matn juda uzun! 1000 ta belgidan kam bo'lishi kerak.")
            return
            
        # Get first two words for audio title
        words = text.split()
        title = "_".join(words[:2]) if len(words) > 1 else words[0]
        title = f"audio_{title}"
        
        # Send status message
        status_message = await update.message.reply_text(
            "🎵 Audio tayyorlanmoqda...\n"
            "⏳ Biroz kuting..."
        )
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                audio_path = temp_file.name
            
            # Generate audio
            communicate = edge_tts.Communicate(text, current_voice)
            await communicate.save(audio_path)
            
            # Check if file exists and has content
            if not os.path.exists(audio_path):
                raise Exception("Audio fayl yaratilmadi!")
            
            if os.path.getsize(audio_path) == 0:
                raise Exception("Audio fayl bo'sh yaratildi!")
                
            # Send audio with custom title
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=title,
                    performer="TTS Bot",
                    caption="✅ Audio xabar tayyor!"
                )
        finally:
            # Clean up temp file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logging.error(f"Failed to delete temp file: {e}")
            
        # Delete status message
        if status_message:
            await status_message.delete()
            
    except Exception as e:
        error_text = f"❌ Xatolik yuz berdi: {str(e)}"
        if status_message:
            try:
                await status_message.edit_text(error_text)
            except:
                await update.message.reply_text(error_text)
        else:
            await update.message.reply_text(error_text)
        
        # Log the error
        logging.error(f"Error in text_to_speech: {str(e)}")

async def handle_invalid_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-text messages"""
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
        "📝 Iltimos, menga faqat matn yuboring - men uni ovozli xabar qilib qaytaraman.\n"
        "🎙 Ovozni o'zgartirish uchun /voice buyrug'ini yuboring.\n"
        "❓ Yordam olish uchun /help buyrug'ini yuboring."
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logging.error("Exception while handling an update:", exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            )
    except:
        pass

async def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Create application with all necessary parameters
    application = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voice", voice_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Handle text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    
    # Handle non-text messages
    non_text_filter = (
        filters.PHOTO |  # For photos
        filters.VIDEO |  # For videos
        filters.AUDIO |  # For audio files
        filters.VOICE |  # For voice messages
        filters.Document.ALL |  # For documents/files
        filters.Sticker.ALL |  # For stickers (both static and animated)
        filters.ANIMATION |  # For animations/GIFs
        filters.VIDEO_NOTE  # For video notes (round videos)
    )
    application.add_handler(MessageHandler(non_text_filter, handle_invalid_message))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start bot
    print("Bot ishga tushirilmoqda...")
    
    try:
        await application.initialize()
        await application.start()
        print("Bot muvaffaqiyatli ishga tushdi!")
        
        # Run the bot until a stop signal is received
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0
        )
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Bot ishga tushishda xatolik: {e}")
    finally:
        try:
            print("Bot to'xtatilmoqda...")
            if application.running:
                await application.stop()
            print("Bot to'xtatildi")
        except Exception as e:
            print(f"Botni to'xtatishda xatolik: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        print(f"Kutilmagan xatolik: {e}")
