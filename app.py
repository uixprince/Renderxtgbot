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
DEFAULT_SPEAKER = "aditya"
DEFAULT_LANGUAGE = "hi-IN"
SAMPLE_RATE = 24000

# ONLY 100% STABLE VOICES FOR V3
VALID_VOICES = [
    "aditya", "rahul", "rohan", "amit", "dev", "ratan", "varun", "manan", "sumit", "kabir", "aayan", "shubh", "ashutosh", "advait",
    "ritu", "priya", "neha", "pooja", "simran", "kavya", "ishita", "shreya", "roopa"
]

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
    "<b>🎭 STABLE BULBUL-V3 VOICES</b>\n\n"
    "<b>👦 MALE VOICES:</b>\n"
    "<b>• aditya</b> | <b>• rahul</b> | <b>• rohan</b>\n"
    "<b>• amit</b> | <b>• dev</b> | <b>• ratan</b>\n"
    "<b>• varun</b> | <b>• manan</b> | <b>• sumit</b>\n"
    "<b>• kabir</b> | <b>• aayan</b> | <b>• shubh</b>\n"
    "<b>• ashutosh</b> | <b>• advait</b>\n\n"
    "<b>👧 FEMALE VOICES:</b>\n"
    "<b>• ritu</b> | <b>• priya</b> | <b>• neha</b>\n"
    "<b>• pooja</b> | <b>• simran</b> | <b>• kavya</b>\n"
    "<b>• ishita</b> | <b>• shreya</b> | <b>• roopa</b>\n\n"
    "<b>🎧 LISTEN SAMPLE: /sample ritu</b>\n"
    "<b>✅ COMMAND TO SET: /setvoice ritu</b>"
    f"{FOOTER}"
)

# ========== KEYBOARDS ==========
def get_start_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟢 GET STARTED (HELP)", callback_data='help_back')]])

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔵 VOICES", callback_data='v_list'), InlineKeyboardButton("🟡 LANGUAGES", callback_data='l_list')],
        [InlineKeyboardButton("🔴 USAGE GUIDE", callback_data='u_guide'), InlineKeyboardButton("👑 OWNER", url=OWNER_LINK)]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK TO MENU", callback_data='help_back')]])

# ========== COMMAND HANDLERS ==========
async def start(update: Update, context):
    user = update.effective_user
    # HELLO USER MENTION ADDED HERE
    msg = (
        f"<b>HELLO {user.mention_html()}, WELCOME TO THE PREMIUM SARVAM TTS BOT!</b>\n\n"
        "<b>I CAN CONVERT YOUR TEXT INTO CRYSTAL CLEAR VOICES.</b>\n"
        "<b>HIGH-QUALITY NEURAL SPEECH GENERATION IS NOW AT YOUR FINGERTIPS.</b>\n\n"
        "<b>CLICK THE BUTTON BELOW TO GET STARTED!</b>"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_start_keyboard(), disable_web_page_preview=True)

async def help_cmd(update: Update, context):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard(), disable_web_page_preview=True)

async def voices_cmd(update: Update, context):
    await update.message.reply_text(VOICES_TEXT, parse_mode="HTML", disable_web_page_preview=True)

# ========== BUTTON CLICK HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    if query.data == 'help_back':
        await query.edit_message_text(text=HELP_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    elif query.data == 'v_list':
        await query.edit_message_text(text=VOICES_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard(), disable_web_page_preview=True)

# ========== TTS AND SETTINGS HANDLERS ==========
async def set_voice(update: Update, context):
    if not context.args:
        return await update.message.reply_text("<b>USAGE: /setvoice ritu</b>", parse_mode="HTML")
    voice = context.args[0].lower()
    if voice not in VALID_VOICES:
        return await update.message.reply_text("<b>❌ INVALID VOICE! Use /voices to check the list.</b>", parse_mode="HTML")
    context.user_data['user_voice'] = voice
    await update.message.reply_text(f"<b>✅ VOICE UPDATED TO: {voice.upper()}</b>", parse_mode="HTML")

async def sample_voice(update: Update, context):
    if not context.args:
        return await update.message.reply_text("<b>USAGE: /sample ritu</b>", parse_mode="HTML")
    voice = context.args[0].lower()
    if voice not in VALID_VOICES:
        return await update.message.reply_text("<b>❌ INVALID VOICE!</b>", parse_mode="HTML")
    await update.message.chat.send_action(action="record_voice")
    processing = await update.message.reply_text(f"<b>🎵 GENERATING SAMPLE FOR {voice.upper()}...</b>", parse_mode="HTML")
    try:
        response = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"},
            json={"text": f"Namaste, mera naam {voice} hai. This is my voice sample.", "target_language_code": "hi-IN", "speaker": voice, "model": MODEL, "speech_sample_rate": SAMPLE_RATE, "enable_preprocessing": True},
            timeout=30
        )
        audio_b64 = response.json().get("audios", [None])[0]
        if not audio_b64:
            return await processing.edit_text("<b>❌ FAILED TO RECEIVE AUDIO.</b>")
        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = f"{voice}_sample.mp3"
        await update.message.reply_voice(voice=audio_file, caption=f"<b>🎧 SAMPLE VOICE: {voice.upper()}</b>{FOOTER}", parse_mode="HTML")
        await processing.delete()
    except Exception as e:
        await update.message.reply_text(f"<b>❌ ERROR: {str(e)[:100]}</b>")

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
            json={"text": text, "target_language_code": lang, "speaker": voice, "model": MODEL, "speech_sample_rate": SAMPLE_RATE, "enable_preprocessing": True},
            timeout=30
        )
        audio_b64 = response.json().get("audios", [None])[0]
        if not audio_b64:
            return await processing.edit_text("<b>❌ FAILED TO RECEIVE AUDIO.</b>")
        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "voice.mp3"
        await update.message.reply_voice(voice=audio_file, caption=f"<b>🔊 VOICE: {voice.upper()}</b>\n{FOOTER}", parse_mode="HTML")
        await processing.delete()
    except Exception as e:
        await update.message.reply_text(f"<b>❌ ERROR: {str(e)[:100]}</b>")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("voices", voices_cmd)) # DIRECT CMD ADDED
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CommandHandler("sample", sample_voice))
    app.add_handler(CommandHandler("tts", text_to_speech))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("🚀 STABLE BOT DEPLOYED!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
