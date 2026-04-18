import io
import logging
import base64
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== LOGGING ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== YOUR KEYS (direct daal diye) ==========
TELEGRAM_BOT_TOKEN = "8797339500:AAGGFunjF7QEfZtsyLuccItfVttHVdt95wU"
SARVAM_API_KEY = "sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y"

# ========== TTS CONFIG ==========
MODEL = "bulbul:v3"
SPEAKER = "shubh"          # default male voice
LANGUAGE = "hi-IN"         # Hindi
SAMPLE_RATE = 24000

# ========== BOT COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ *Sarvam TTS Bot*\n\n"
        "Send me any text, I'll convert it to speech.\n\n"
        "/voices - List all voices\n"
        "/setvoice <name> - Change voice (e.g., /setvoice ritu)\n"
        "/setlang <code> - Change language (e.g., /setlang en-IN)\n\n"
        "Supported languages: hi-IN, en-IN, ta-IN, te-IN, bn-IN, mr-IN, gu-IN, kn-IN, ml-IN, pa-IN, od-IN",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Just type any text (max 2500 chars). Use /setvoice and /setlang to customize.")

async def list_voices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voices_text = (
        "🎤 *Available Voices*\n"
        "Male: shubh (default), aditya, rahul, rohan, amit, dev, ratan, varun, manan, sumit, kabir, aayan, ashutosh, advait, anand, tarun, sunny, mani, gokul, vijay, mohit, rehan, soham\n\n"
        "Female: ritu, priya, neha, pooja, simran, kavya, ishita, shreya, roopa, amelia, sophia, tanya, shruti, suhani, kavitha, rupali"
    )
    await update.message.reply_text(voices_text, parse_mode="Markdown")

async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/setvoice ritu`", parse_mode="Markdown")
        return
    new_voice = context.args[0].lower()
    # simple validation (optional)
    context.user_data['user_voice'] = new_voice
    await update.message.reply_text(f"✅ Voice changed to `{new_voice}`", parse_mode="Markdown")

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/setlang hi-in`\nOptions: hi-IN, en-IN, ta-IN, te-IN, bn-IN, mr-IN, gu-IN, kn-IN, ml-IN, pa-IN, od-IN", parse_mode="Markdown")
        return
    new_lang = context.args[0].lower()
    context.user_data['user_language'] = new_lang
    await update.message.reply_text(f"✅ Language changed to `{new_lang}`", parse_mode="Markdown")

# ========== MAIN TTS FUNCTION ==========
async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return

    if len(text) > 2500:
        await update.message.reply_text("❌ Text too long (max 2500 characters).")
        return

    # Send "recording" action
    await update.message.chat.send_action(action="record_voice")

    # Get user preferences or defaults
    voice = context.user_data.get('user_voice', SPEAKER)
    lang = context.user_data.get('user_language', LANGUAGE)

    processing_msg = await update.message.reply_text(f"🎵 Converting: `{voice}`, `{lang}`...", parse_mode="Markdown")

    try:
        # Direct API call to Sarvam
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
        response.raise_for_status()
        data = response.json()

        # Extract base64 audio
        audio_b64 = data.get("audio_content") or data.get("audio")
        if not audio_b64:
            raise Exception("No audio content in API response")

        audio_bytes = base64.b64decode(audio_b64)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"

        # Send voice message
        await update.message.reply_voice(
            voice=audio_file,
            caption=f"🔊 {voice} | {lang.upper()}"
        )
        await processing_msg.delete()

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        error_detail = ""
        if e.response is not None:
            error_detail = f"\n{e.response.text[:200]}"
        await update.message.reply_text(f"❌ API error: {str(e)}{error_detail}")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")

# ========== ERROR HANDLER ==========
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Unexpected error. Please try again later.")

# ========== MAIN ==========
def main():
    # Fix for Python 3.14+ event loop issue
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

    logger.info("Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()