import io
import os
import logging
import base64
import asyncio
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
TELEGRAM_BOT_TOKEN = "8797339500:AAHDrXZnOsBvltKhvjfy1C5RkFUnDGTMwqQ"
SARVAM_API_KEY = "sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y"

MODEL = "bulbul:v3"
DEFAULT_SPEAKER = "shubh"
DEFAULT_LANGUAGE = "en-IN"
SAMPLE_RATE = 24000
FOOTER = "\n\n**POWERED BY ᏢᎡϟꋊᏣᎬ༒࿗ @KYA_KROGE_NAME_JAANKE**"

# ========== DUMMY SERVER FOR RENDER ==========
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")
    def log_message(self, format, *args): pass

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

# ========== COMMAND HANDLERS ==========

async def start(update: Update, context):
    msg = (
        "**🎙️ WELCOME TO SARVAM TTS BOT!**\n\n"
        "**I can convert any text into high-quality speech.**\n\n"
        "**Check out the commands below to see how to use me:**\n"
        "**👉 /help - How to use this bot?**"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, context):
    msg = (
        "**📖 BOT USAGE GUIDE:**\n\n"
        "**1️⃣ /tts <text> - Generate voice (Example: /tts Hello everyone)**\n"
        "**2️⃣ /setvoice <name> - Set your preferred voice.**\n"
        "**3️⃣ /setlang <lang_code> - Change the language.**\n"
        "**4️⃣ /voices - View all available voices.**\n\n"
        "**⚠️ Note: Normal messages are ignored. Use the /tts command to generate speech.**"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def voices_cmd(update: Update, context):
    msg = (
        "**🎭 AVAILABLE VOICES:**\n\n"
        "**MALE:**\n"
        "**• shubh (Default)**\n"
        "**• deepak**\n"
        "**• amit**\n\n"
        "**FEMALE:**\n"
        "**• ritu**\n"
        "**• sneha**\n"
        "**• arpit**\n\n"
        "**To set a voice, type: /setvoice ritu**"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def set_voice(update: Update, context):
    if not context.args:
        return await update.message.reply_text("**Usage: /setvoice ritu**", parse_mode="Markdown")
    voice = context.args[0].lower()
    context.user_data['user_voice'] = voice
    await update.message.reply_text(f"**✅ Voice successfully set to: {voice}**", parse_mode="Markdown")

async def set_language(update: Update, context):
    if not context.args:
        return await update.message.reply_text("**Usage: /setlang en-IN**", parse_mode="Markdown")
    lang = context.args[0]
    context.user_data['user_language'] = lang
    await update.message.reply_text(f"**✅ Language successfully set to: {lang}**", parse_mode="Markdown")

async def text_to_speech(update: Update, context):
    # Process only text passed with the command
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("**⚠️ Please provide some text! Example: /tts How are you?**", parse_mode="Markdown")

    if len(text) > 2000:
        return await update.message.reply_text("**❌ Text is too long! (Max limit is 2000 characters)**", parse_mode="Markdown")

    await update.message.chat.send_action(action="record_voice")
    voice = context.user_data.get('user_voice', DEFAULT_SPEAKER)
    lang = context.user_data.get('user_language', DEFAULT_LANGUAGE)
    
    processing = await update.message.reply_text(f"**🎵 Processing... Generating speech... ({voice})**", parse_mode="Markdown")

    try:
        response = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text, "target_language_code": lang, "speaker": voice,
                "model": MODEL, "speech_sample_rate": SAMPLE_RATE, "enable_preprocessing": True
            },
            timeout=30
        )
        
        data = response.json()
        audio_b64 = data.get("audios", [None])[0]

        if not audio_b64:
            await processing.edit_text("**❌ No audio received from the API!**")
            return

        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "voice.mp3"

        caption = f"**🔊 Voice: {voice.upper()}**\n**🌐 Lang: {lang.upper()}**\n{FOOTER}"
        
        await update.message.reply_voice(voice=audio_file, caption=caption, parse_mode="Markdown")
        await processing.delete()

    except Exception as e:
        logger.error(f"TTS Error: {e}")
        await update.message.reply_text(f"**❌ Error: {str(e)[:100]}**", parse_mode="Markdown")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("voices", voices_cmd))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(CommandHandler("tts", text_to_speech))

    logger.info("🚀 VIP Bot Started in English!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
