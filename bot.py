import os
import io
import logging
import base64
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sarvamai import SarvamAI

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("8797339500:AAGGFunjF7QEfZtsyLuccItfVttHVdt95wU")
SARVAM_API_KEY = os.getenv("sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y")

MODEL = "bulbul:v3"
SPEAKER = "shubh"
LANGUAGE = "hi-IN"
SAMPLE_RATE = 24000

client = SarvamAI(api_key=SARVAM_API_KEY)   # ← ab sahi hai

async def start(update, context):
    await update.message.reply_text("🎙️ *Sarvam TTS Bot*\nSend me any text, I'll convert to speech.\n/voices - list voices\n/setvoice <name>\n/setlang <code>", parse_mode="Markdown")

async def help_command(update, context):
    await update.message.reply_text("Just type any text. Max 2500 chars.")

async def list_voices(update, context):
    await update.message.reply_text("🎤 Voices: shubh, ritu, priya, etc. Use /setvoice ritu")

async def set_voice(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setvoice ritu")
        return
    context.user_data['user_voice'] = context.args[0].lower()
    await update.message.reply_text(f"Voice set to {context.args[0]}")

async def set_language(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setlang hi-in")
        return
    context.user_data['user_language'] = context.args[0].lower()
    await update.message.reply_text(f"Language set to {context.args[0]}")

async def text_to_speech(update, context):
    text = update.message.text
    if len(text) > 2500:
        await update.message.reply_text("Text too long (max 2500).")
        return
    await update.message.chat.send_action(action="record_voice")
    try:
        voice = context.user_data.get('user_voice', SPEAKER)
        lang = context.user_data.get('user_language', LANGUAGE)
        processing = await update.message.reply_text(f"🎵 Converting... ({voice}, {lang})")
        audio_b64 = client.text_to_speech(text=text, target_language_code=lang, speaker=voice, model=MODEL, speech_sample_rate=SAMPLE_RATE, enable_preprocessing=True)
        audio_bytes = base64.b64decode(audio_b64)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"
        await update.message.reply_voice(voice=audio_file, caption=f"Voice: {voice} | Lang: {lang}")
        await processing.delete()
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"Error: {str(e)[:200]}")

def main():
    if not TELEGRAM_BOT_TOKEN or not SARVAM_API_KEY:
        logger.error("Missing environment variables!")
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voices", list_voices))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()