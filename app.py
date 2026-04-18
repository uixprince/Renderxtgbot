import io
import os
import logging
import base64
import asyncio
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
TELEGRAM_BOT_TOKEN = "8797339500:AAHDrXZnOsBvltKhvjfy1C5RkFUnDGTMwqQ"
SARVAM_API_KEY = "sk_90f9w85z_MXwZGYjXzrlhjWZY4vaK5F5Y"

MODEL = "bulbul:v3"
DEFAULT_SPEAKER = "shubh"
DEFAULT_LANGUAGE = "hi-IN"
SAMPLE_RATE = 24000

# HTML Format Mention - Clickable Name
OWNER_LINK = "https://t.me/KYA_KROGE_NAME_JAANKE"
FOOTER = f'\n\n<b>POWERED BY <a href="{OWNER_LINK}">ᏢᎡϟꋊᏣᎬ༒࿗</a></b>'

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

# ========== TEXT STRINGS ==========
HELP_TEXT = (
    "<b>📚 BOT HELP MENU</b>\n\n"
    "<b>SELECT AN OPTION FROM THE BUTTONS BELOW TO LEARN HOW TO OPERATE THE BOT.</b>\n\n"
    "<b>ALL COMMANDS ARE CASE SENSITIVE. USE /tts TO START GENERATING.</b>"
    f"{FOOTER}"
)

VOICES_TEXT = (
    "<b>🎭 AVAILABLE VOICES LIST</b>\n\n"
    "<b>MALE VOICES:</b>\n"
    "<b>• shubh (Default / Smooth)</b>\n"
    "<b>• deepak (Deep)</b>\n"
    "<b>• amit (Clear)</b>\n\n"
    "<b>FEMALE VOICES:</b>\n"
    "<b>• ritu (Sweet)</b>\n"
    "<b>• sneha (Soft)</b>\n"
    "<b>• arpit (Professional)</b>\n\n"
    "<b>COMMAND TO SET: /setvoice ritu</b>"
    f"{FOOTER}"
)

LANGS_TEXT = (
    "<b>🌐 SUPPORTED LANGUAGES</b>\n\n"
    "<b>• hi-IN (Hindi)</b>\n"
    "<b>• en-IN (English)</b>\n"
    "<b>• ta-IN (Tamil)</b>\n"
    "<b>• te-IN (Telugu)</b>\n"
    "<b>• bn-IN (Bengali)</b>\n"
    "<b>• mr-IN (Marathi)</b>\n"
    "<b>• gu-IN (Gujarati)</b>\n"
    "<b>• kn-IN (Kannada)</b>\n\n"
    "<b>COMMAND TO SET: /setlang en-IN</b>"
    f"{FOOTER}"
)

USAGE_TEXT = (
    "<b>🛠️ BOT USAGE GUIDE</b>\n\n"
    "<b>1️⃣ /tts &lt;text&gt; - Generate voice (Example: /tts Hello Boss)</b>\n"
    "<b>2️⃣ /setvoice &lt;name&gt; - Set your preferred voice.</b>\n"
    "<b>3️⃣ /setlang &lt;lang_code&gt; - Change the language.</b>\n"
    "<b>4️⃣ /help - Open the main help menu.</b>\n\n"
    "<b>⚠️ Normal messages are ignored. Use the /tts command to generate speech.</b>"
    f"{FOOTER}"
)

# ========== KEYBOARDS (COLORFUL BUTTONS BYPASS) ==========
def get_start_keyboard():
    btn = InlineKeyboardButton("GET STARTED (HELP)", callback_data='help_back')
    btn.api_kwargs = {'style': 'success'} # Green Color
    return InlineKeyboardMarkup([[btn]])

def get_main_keyboard():
    # Adding colors dynamically using api_kwargs
    btn_voices = InlineKeyboardButton("VOICES", callback_data='v_list')
    btn_voices.api_kwargs = {'style': 'primary'} # Blue Color
    
    btn_langs = InlineKeyboardButton("LANGUAGES", callback_data='l_list')
    btn_langs.api_kwargs = {'style': 'primary'} # Blue Color
    
    btn_usage = InlineKeyboardButton("USAGE GUIDE", callback_data='u_guide')
    btn_usage.api_kwargs = {'style': 'danger'} # Red Color
    
    btn_owner = InlineKeyboardButton("OWNER", url=OWNER_LINK)
    btn_owner.api_kwargs = {'style': 'success'} # Green Color
    
    # 2x2 Grid Layout
    return InlineKeyboardMarkup([
        [btn_voices, btn_langs],
        [btn_usage, btn_owner]
    ])

def get_back_keyboard():
    btn_back = InlineKeyboardButton("🔙 BACK TO MENU", callback_data='help_back')
    btn_back.api_kwargs = {'style': 'danger'} # Red Color
    return InlineKeyboardMarkup([[btn_back]])

# ========== COMMAND HANDLERS ==========

async def start(update: Update, context):
    msg = (
        "<b>🎙️ WELCOME TO THE PREMIUM SARVAM TTS BOT!</b>\n\n"
        "<b>I CAN CONVERT YOUR TEXT INTO CRYSTAL CLEAR VOICES.</b>\n"
        "<b>HIGH-QUALITY NEURAL SPEECH GENERATION IS NOW AT YOUR FINGERTIPS.</b>\n\n"
        "<b>CLICK THE BUTTON BELOW TO GET STARTED!</b>"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_start_keyboard(), disable_web_page_preview=True)

async def help_cmd(update: Update, context):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard(), disable_web_page_preview=True)

# ========== BUTTON CLICK HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    data = query.data
    
    if data == 'help_back':
        await query.edit_message_text(text=HELP_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    elif data == 'v_list':
        await query.edit_message_text(text=VOICES_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard(), disable_web_page_preview=True)
    elif data == 'l_list':
        await query.edit_message_text(text=LANGS_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard(), disable_web_page_preview=True)
    elif data == 'u_guide':
        await query.edit_message_text(text=USAGE_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard(), disable_web_page_preview=True)

# ========== TTS AND SETTINGS HANDLERS ==========
async def set_voice(update: Update, context):
    if not context.args:
        return await update.message.reply_text("<b>USAGE: /setvoice ritu</b>", parse_mode="HTML")
    voice = context.args[0].lower()
    context.user_data['user_voice'] = voice
    await update.message.reply_text(f"<b>✅ VOICE UPDATED TO: {voice.upper()}</b>", parse_mode="HTML")

async def set_language(update: Update, context):
    if not context.args:
        return await update.message.reply_text("<b>USAGE: /setlang en-IN</b>", parse_mode="HTML")
    lang = context.args[0]
    context.user_data['user_language'] = lang
    await update.message.reply_text(f"<b>✅ LANGUAGE UPDATED TO: {lang.upper()}</b>", parse_mode="HTML")

async def text_to_speech(update: Update, context):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("<b>⚠️ INPUT TEXT REQUIRED! EXAMPLE: /tts Hello Boss</b>", parse_mode="HTML")

    await update.message.chat.send_action(action="record_voice")
    voice = context.user_data.get('user_voice', DEFAULT_SPEAKER)
    lang = context.user_data.get('user_language', DEFAULT_LANGUAGE)
    
    processing = await update.message.reply_text(f"<b>🎵 PROCESSING YOUR REQUEST... ({voice.upper()})</b>", parse_mode="HTML")

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
            await processing.edit_text("<b>❌ FAILED TO RECEIVE AUDIO FROM API.</b>", parse_mode="HTML")
            return

        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "voice.mp3"

        caption = f"<b>🔊 VOICE: {voice.upper()}</b>\n<b>🌐 LANG: {lang.upper()}</b>{FOOTER}"
        
        await update.message.reply_voice(voice=audio_file, caption=caption, parse_mode="HTML")
        await processing.delete()

    except Exception as e:
        logger.error(f"TTS Error: {e}")
        await update.message.reply_text(f"<b>❌ ERROR: {str(e)[:100]}</b>", parse_mode="HTML")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(CommandHandler("tts", text_to_speech))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 VIP PREMIUM BOT DEPLOYED WITH COLORED BUTTONS!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
