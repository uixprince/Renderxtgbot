import io
import logging
import base64
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIG (Hardcoded for now, but better to use env vars) ==========
TELEGRAM_BOT_TOKEN = "8797339500:AAHDrXZnOsBvltKhvjfy1C5RkFUnDGTMwqQ"
SARVAM_API_KEY = "sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y"

MODEL = "bulbul:v3"
SPEAKER = "shubh"
LANGUAGE = "hi-IN"
SAMPLE_RATE = 24000

async def start(update: Update, context):
    await update.message.reply_text(
        "🎙️ *Sarvam TTS Bot* (Background Worker)\n\n"
        "Send me any text, I'll convert it to speech.\n"
        "/setvoice <name> - Change voice (e.g., /setvoice ritu)\n"
        "/setlang <code> - Change language (e.g., /setlang en-IN)\n\n"
        "Supported langs: hi-IN, en-IN, ta-IN, te-IN, bn-IN, mr-IN, gu-IN, kn-IN, ml-IN, pa-IN, od-IN",
        parse_mode="Markdown"
    )

async def set_voice(update: Update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setvoice ritu")
        return
    context.user_data['user_voice'] = context.args[0].lower()
    await update.message.reply_text(f"✅ Voice set to {context.args[0]}")

async def set_language(update: Update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setlang hi-in")
        return
    context.user_data['user_language'] = context.args[0].lower()
    await update.message.reply_text(f"✅ Language set to {context.args[0]}")

async def text_to_speech(update: Update, context):
    text = update.message.text.strip()
    if not text or len(text) > 2500:
        await update.message.reply_text("Text too long or empty (max 2500 chars).")
        return

    await update.message.chat.send_action(action="record_voice")

    voice = context.user_data.get('user_voice', SPEAKER)
    lang = context.user_data.get('user_language', LANGUAGE)

    processing = await update.message.reply_text(f"🎵 Converting... ({voice}, {lang})")

    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "target_language_code": lang,
            "speaker": voice,
            "model": MODEL,
            "speech_sample_rate": SAMPLE_RATE,
            "enable_preprocessing": True
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text(f"API error {response.status_code}: {response.text[:200]}")
            await processing.delete()
            return

        data = response.json()
        
        # FIX: Sarvam API 'audios' key mein ek list bhejti hai
        audios_list = data.get("audios")
        
        if audios_list and len(audios_list) > 0:
            audio_b64 = audios_list[0] # List ka pehla audio chunk
        else:
            audio_b64 = None

        if not audio_b64:
            await update.message.reply_text(f"❌ No audio in response. Keys: {list(data.keys())}")
            await processing.delete()
            return

        audio_bytes = base64.b64decode(audio_b64)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"

        await update.message.reply_voice(voice=audio_file, caption=f"🔊 {voice} | {lang.upper()}")
        await processing.delete()

    except Exception as e:
        logger.error(f"TTS error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")

async def error_handler(update: Update, context):
    logger.error(f"Update error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Unexpected error. Please try again.")

def main():
    # Fix for Python 3.14+ event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Bot started as Background Worker. Listening for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
