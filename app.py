import os
import io
import logging
import base64
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sarvamai import SarvamAI  # ✅ Correct import

# Load environment variables from .env file (if present)
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
# Read tokens from environment variables (set on Render dashboard)
TELEGRAM_BOT_TOKEN = os.getenv("8797339500:AAGGFunjF7QEfZtsyLuccItfVttHVdt95wU")
SARVAM_API_KEY = os.getenv("sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y")

# TTS defaults
MODEL = "bulbul:v3"
SPEAKER = "shubh"           # default male voice
LANGUAGE = "hi-IN"          # default Hindi
SAMPLE_RATE = 24000

# Initialize Sarvam client (correct class)
client = SarvamAI(api_key=SARVAM_API_KEY)

# ===== BOT COMMAND HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎙️ *Welcome to Sarvam TTS Bot!*\n\n"
        "Send me any text, and I'll convert it to speech using Sarvam AI.\n\n"
        "*Available Commands:*\n"
        "/start - Show this message\n"
        "/help - Show help information\n"
        "/voices - List available voices\n"
        "/setvoice <voice> - Change voice (e.g., /setvoice ritu)\n"
        "/setlang <lang> - Change language (e.g., /setlang en-IN)\n\n"
        "*Supported Languages:*\n"
        "🇮🇳 Hindi (hi-IN) | 🇬🇧 English (en-IN) | 🇮🇳 Tamil (ta-IN)\n"
        "🇮🇳 Telugu (te-IN) | 🇮🇳 Bengali (bn-IN) | 🇮🇳 Marathi (mr-IN)\n"
        "🇮🇳 Gujarati (gu-IN) | 🇮🇳 Kannada (kn-IN) | 🇮🇳 Malayalam (ml-IN)\n"
        "🇮🇳 Punjabi (pa-IN) | 🇮🇳 Odia (od-IN)\n\n"
        "Just type any text and I'll speak it back to you! 🎵"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔊 *How to use this bot:*\n\n"
        "1. Simply type any text message\n"
        "2. Bot will convert it to speech\n"
        "3. You'll receive a voice message\n\n"
        "*Customization:*\n"
        "• /voices - See all available voices\n"
        "• /setvoice <voice> - Change the speaker voice\n"
        "• /setlang <code> - Change language\n\n"
        "*Example:*\n"
        "Send: 'नमस्ते दुनिया' (Hello World in Hindi)\n\n"
        "*Note:* Maximum 2500 characters per request for v3 model."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def list_voices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voices_text = (
        "🎤 *Available Voices (Bulbul v3):*\n\n"
        "*Male Voices:*\n"
        "shubh (default), aditya, rahul, rohan, amit, dev, ratan, varun, manan, sumit,\n"
        "kabir, aayan, ashutosh, advait, anand, tarun, sunny, mani, gokul, vijay,\n"
        "mohit, rehan, soham\n\n"
        "*Female Voices:*\n"
        "ritu, priya, neha, pooja, simran, kavya, ishita, shreya, roopa, amelia,\n"
        "sophia, tanya, shruti, suhani, kavitha, rupali\n\n"
        "*Recommended by Language:*\n"
        "• Hindi: priya, ishita, shubh\n"
        "• English: ratan, priya\n"
        "• Tamil: priya, ishita, ratan\n\n"
        f"Current voice: `{SPEAKER}`\n\n"
        "Use `/setvoice <voice>` to change (e.g., `/setvoice ritu`)"
    )
    await update.message.reply_text(voices_text, parse_mode="Markdown")

async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please specify a voice name.\n"
            "Example: `/setvoice ritu`\n"
            "Use `/voices` to see all available voices.",
            parse_mode="Markdown"
        )
        return
    
    new_voice = context.args[0].lower()
    valid_voices = [
        "shubh", "aditya", "ritu", "priya", "neha", "rahul", "pooja", "rohan",
        "simran", "kavya", "amit", "dev", "ishita", "shreya", "ratan", "varun",
        "manan", "sumit", "roopa", "kabir", "aayan", "ashutosh", "advait", "amelia",
        "sophia", "anand", "tanya", "tarun", "sunny", "mani", "gokul", "vijay",
        "shruti", "suhani", "mohit", "kavitha", "rehan", "soham", "rupali"
    ]
    
    if new_voice not in valid_voices:
        await update.message.reply_text(
            f"❌ Voice '{new_voice}' not found.\n"
            "Use `/voices` to see all available voices.",
            parse_mode="Markdown"
        )
        return
    
    context.user_data['user_voice'] = new_voice
    await update.message.reply_text(
        f"✅ Voice changed to: `{new_voice}`\n\n"
        "Try sending some text to hear the new voice!",
        parse_mode="Markdown"
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valid_languages = {
        "hi-in": "Hindi 🇮🇳",
        "en-in": "English (Indian) 🇬🇧🇮🇳",
        "ta-in": "Tamil 🇮🇳",
        "te-in": "Telugu 🇮🇳",
        "bn-in": "Bengali 🇮🇳",
        "mr-in": "Marathi 🇮🇳",
        "gu-in": "Gujarati 🇮🇳",
        "kn-in": "Kannada 🇮🇳",
        "ml-in": "Malayalam 🇮🇳",
        "pa-in": "Punjabi 🇮🇳",
        "od-in": "Odia 🇮🇳"
    }
    
    if not context.args:
        lang_list = "\n".join([f"• `{k}` - {v}" for k, v in valid_languages.items()])
        await update.message.reply_text(
            f"Please specify a language code.\n\n*Supported Languages:*\n{lang_list}\n\n"
            "Example: `/setlang hi-IN`\n"
            f"Current language: `{LANGUAGE}`",
            parse_mode="Markdown"
        )
        return
    
    new_lang = context.args[0].lower()
    if new_lang not in valid_languages:
        await update.message.reply_text(
            f"❌ Language '{new_lang}' not supported.\n"
            "Use `/setlang` without arguments to see all supported languages.",
            parse_mode="Markdown"
        )
        return
    
    context.user_data['user_language'] = new_lang
    await update.message.reply_text(
        f"✅ Language changed to: `{new_lang}` - {valid_languages[new_lang]}\n\n"
        "Try sending some text in that language!",
        parse_mode="Markdown"
    )

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if len(text) > 2500:
        await update.message.reply_text(
            "❌ Text is too long! Maximum 2500 characters allowed.\n"
            f"Your text: {len(text)} characters.\n"
            "Please shorten your message and try again."
        )
        return
    
    await update.message.chat.send_action(action="record_voice")
    
    try:
        voice = context.user_data.get('user_voice', SPEAKER)
        lang = context.user_data.get('user_language', LANGUAGE)
        
        processing_msg = await update.message.reply_text(
            f"🎵 Converting to speech...\n"
            f"Voice: `{voice}` | Language: `{lang}`\n"
            f"Text: `{text[:50]}{'...' if len(text) > 50 else ''}`",
            parse_mode="Markdown"
        )
        
        logger.info(f"TTS request: user={user_id}, voice={voice}, lang={lang}, text={text[:100]}")
        
        # Call Sarvam TTS API – returns base64 encoded audio
        audio_data = client.text_to_speech(
            text=text,
            target_language_code=lang,
            speaker=voice,
            model=MODEL,
            speech_sample_rate=SAMPLE_RATE,
            enable_preprocessing=True
        )
        
        audio_bytes = base64.b64decode(audio_data)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"
        
        await update.message.reply_voice(
            voice=audio_file,
            caption=f"🎙️ Text-to-speech using Sarvam AI\nVoice: {voice} | Language: {lang}"
        )
        
        await processing_msg.delete()
        logger.info(f"Voice message sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        await update.message.reply_text(
            f"❌ Sorry, an error occurred.\n\nError: {str(e)[:200]}\n\nPlease try again."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ An unexpected error occurred. Please try again later.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    if not SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY environment variable not set!")
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voices", list_voices))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    app.add_error_handler(error_handler)
    
    logger.info("Starting Telegram TTS Bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()