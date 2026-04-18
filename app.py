import io
import logging
import base64
import asyncio
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = "8797339500:AAGGFunjF7QEfZtsyLuccItfVttHVdt95wU"
SARVAM_API_KEY = "sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y"

MODEL = "bulbul:v3"
SPEAKER = "shubh"
LANGUAGE = "hi-IN"
SAMPLE_RATE = 24000

async def start(update, context):
    await update.message.reply_text("🎙️ Sarvam TTS Bot\nSend text.")

async def help_command(update, context):
    await update.message.reply_text("Send any text")

async def list_voices(update, context):
    await update.message.reply_text("Voices: shubh, ritu, priya")

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
    text = update.message.text.strip()
    if not text or len(text) > 2500:
        await update.message.reply_text("Text too long or empty.")
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

        logger.info(f"Sending request to Sarvam: {payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text[:500]}")  # Log first 500 chars

        if response.status_code != 200:
            await update.message.reply_text(f"API error {response.status_code}: {response.text[:200]}")
            await processing.delete()
            return

        data = response.json()
        logger.info(f"Response JSON keys: {data.keys()}")

        # Try multiple possible keys
        audio_b64 = data.get("audio_content") or data.get("audio") or data.get("data") or data.get("base64")
        if not audio_b64:
            # If no audio field, send the whole response as error for debugging
            await update.message.reply_text(f"API response missing audio. Keys: {list(data.keys())}\nPreview: {str(data)[:200]}")
            await processing.delete()
            return

        audio_bytes = base64.b64decode(audio_b64)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"

        await update.message.reply_voice(voice=audio_file, caption=f"{voice} | {lang}")
        await processing.delete()

    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")

async def error_handler(update, context):
    logger.error(f"Update error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Unexpected error.")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voices", list_voices))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    app.add_error_handler(error_handler)
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()