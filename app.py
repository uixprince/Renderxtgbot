import os
import io
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sarvamai import Sarvam

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("8797339500:AAGGFunjF7QEfZtsyLuccItfVttHVdt95wU")
SARVAM_API_KEY = os.getenv("sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y")

# TTS Configuration
MODEL = "bulbul:v3"
SPEAKER = "shubh"  # Default voice (male) - Options: ritu (female), aditya, priya, etc.
LANGUAGE = "hi-IN"  # Hindi - Change as needed: en-IN, ta-IN, te-IN, bn-IN, etc.
SAMPLE_RATE = 24000

# Initialize Sarvam client
client = Sarvam(api_key=SARVAM_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
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
    """Send help information."""
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
    """List all available voices."""
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
    """Change the TTS voice."""
    if not context.args:
        await update.message.reply_text(
            "Please specify a voice name.\n"
            "Example: `/setvoice ritu`\n"
            "Use `/voices` to see all available voices.",
            parse_mode="Markdown"
        )
        return
    
    new_voice = context.args[0].lower()
    
    # Basic validation - check if it's in our known voices list
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
    
    # Store in user context
    if 'user_voice' not in context.user_data:
        context.user_data['user_voice'] = {}
    context.user_data['user_voice'] = new_voice
    
    await update.message.reply_text(
        f"✅ Voice changed to: `{new_voice}`\n\n"
        "Try sending some text to hear the new voice!",
        parse_mode="Markdown"
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change the TTS language."""
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
            "Current language: `{LANGUAGE}`",
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
    
    # Store in user context
    if 'user_language' not in context.user_data:
        context.user_data['user_language'] = {}
    context.user_data['user_language'] = new_lang
    
    await update.message.reply_text(
        f"✅ Language changed to: `{new_lang}` - {valid_languages[new_lang]}\n\n"
        "Try sending some text in that language!",
        parse_mode="Markdown"
    )

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert text to speech and send as voice message."""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check text length
    if len(text) > 2500:
        await update.message.reply_text(
            "❌ Text is too long! Maximum 2500 characters allowed.\n"
            f"Your text: {len(text)} characters.\n"
            "Please shorten your message and try again."
        )
        return
    
    # Send "typing" indicator
    await update.message.chat.send_action(action="record_voice")
    
    try:
        # Get user preferences or use defaults
        voice = context.user_data.get('user_voice', SPEAKER)
        lang = context.user_data.get('user_language', LANGUAGE)
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            f"🎵 Converting to speech...\n"
            f"Voice: `{voice}` | Language: `{lang}`\n"
            f"Text: `{text[:50]}{'...' if len(text) > 50 else ''}`",
            parse_mode="Markdown"
        )
        
        # Call Sarvam TTS API
        logger.info(f"Generating TTS for user {user_id}: text='{text[:100]}', voice={voice}, lang={lang}")
        
        audio_data = client.text_to_speech(
            text=text,
            target_language_code=lang,
            speaker=voice,
            model=MODEL,
            speech_sample_rate=SAMPLE_RATE,
            enable_preprocessing=True
        )
        
        # The audio_data is base64 encoded - decode it
        import base64
        audio_bytes = base64.b64decode(audio_data)
        
        # Use BytesIO to send audio directly without saving to disk
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "speech.mp3"
        
        # Send voice message
        await update.message.reply_voice(
            voice=audio_file,
            caption=f"🎙️ Text-to-speech using Sarvam AI\nVoice: {voice} | Language: {lang}"
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        logger.info(f"Successfully sent voice message to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        error_msg = f"❌ Sorry, an error occurred while generating speech.\n\nError: {str(e)[:200]}\n\nPlease try again with different text."
        await update.message.reply_text(error_msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    if not SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY not found in environment variables!")
        return
    
    # Create Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voices", list_voices))
    application.add_handler(CommandHandler("setvoice", set_voice))
    application.add_handler(CommandHandler("setlang", set_language))
    
    # Add message handler for text messages (TTS)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting Telegram TTS Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()