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

# Default Settings
DEFAULT_MODEL = "bulbul:v3"
DEFAULT_SPEAKER = "aditya"
DEFAULT_LANGUAGE = "hi-IN"
DEFAULT_PACE = 1.0 
SAMPLE_RATE = 24000

OWNER_LINK = "https://t.me/KYA_KROGE_NAME_JAANKE"
FOOTER = f'\n\n<b>POWERED BY <a href="{OWNER_LINK}">ᏢᎡϟꋊᏣᎬ༒࿗</a></b>'

# ========== FULL VOICE DATABASE ==========
VOICES_V3_MALE = ["aditya", "rahul", "rohan", "amit", "dev", "ratan", "varun", "manan", "sumit", "kabir", "aayan", "shubh", "ashutosh", "advait"]
VOICES_V3_FEMALE = ["ritu", "priya", "neha", "pooja", "simran", "kavya", "ishita", "shreya", "roopa", "amelia", "sophia"]

VOICES_V1_MALE = ["abhilash", "karun", "hitesh", "samir", "pranav", "karan", "vikram", "ajit", "alok", "deepak", "gourav", "jatin", "lalit", "mahesh", "nitin", "omkar", "piyush", "rajat", "sagar", "tarun", "umesh", "vinay"]
VOICES_V1_FEMALE = ["anushka", "manisha", "vidya", "arya", "sonia", "tanvi", "kiara", "bharti", "chitra", "divya", "esha", "falak", "geeta", "heena", "indu", "jaya", "kirti", "latika", "meena", "nidhi", "payal", "reema"]

LANGUAGES = {
    "Hindi 🇮🇳": "hi-IN", "English 🇺🇸": "en-IN", "Tamil 🇮🇳": "ta-IN", 
    "Telugu 🇮🇳": "te-IN", "Bengali 🇮🇳": "bn-IN", "Marathi 🇮🇳": "mr-IN", 
    "Gujarati 🇮🇳": "gu-IN", "Kannada 🇮🇳": "kn-IN", "Malayalam 🇮🇳": "ml-IN"
}

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

# ========== UI KEYBOARDS ==========
def kb_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎙️ Bulbul V3 (25 Voices)", callback_data='nav_v3'), InlineKeyboardButton("📻 Bulbul V1 (50+ Voices)", callback_data='nav_v1')],
        [InlineKeyboardButton("🌐 Languages", callback_data='nav_lang'), InlineKeyboardButton("⚙️ Speed", callback_data='nav_speed')],
        [InlineKeyboardButton("📖 Help & Usage Details", callback_data='nav_help')],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ])

def kb_help_details():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='nav_main')]])

def kb_lang_menu():
    keyboard = []
    row = []
    for name, code in LANGUAGES.items():
        row.append(InlineKeyboardButton(name, callback_data=f'setl_{code}'))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='nav_main')])
    return InlineKeyboardMarkup(keyboard)

def kb_voice_grid(voices, version, back_callback):
    keyboard = []
    row = []
    for voice in voices:
        row.append(InlineKeyboardButton(voice.capitalize(), callback_data=f'setv_{version}_{voice}'))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

# ========== COMMAND HANDLERS ==========
async def start(update: Update, context):
    user = update.effective_user
    msg = f"<b>HELLO {user.mention_html()}, WELCOME!</b>\n\n<b>Use /help to see all command details.</b>{FOOTER}"
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_main_menu())

async def help_cmd(update: Update, context):
    msg = (
        "<b>📖 A to Z BOT USAGE DETAILS:</b>\n\n"
        "<b>1️⃣ /tts &lt;text&gt;</b> - Text ko voice mein badalne ke liye.\n"
        "<b>2) /voice</b> - Voice selection menu kholne ke liye.\n"
        "<b>3) /lang</b> - Language badalne ke liye.\n"
        "<b>4) /setvoice &lt;name&gt;</b> - Direct voice set karne ke liye.\n"
        "<b>5) /sample &lt;name&gt;</b> - Voice ka sample sunne ke liye.\n"
        "<b>6) /help</b> - Yeh menu dekhne ke liye."
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_help_details())

# ========== CALLBACK HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'nav_main':
        await query.edit_message_text("<b>MASTER CONTROL PANEL</b>", parse_mode="HTML", reply_markup=kb_main_menu())
    elif data == 'nav_help':
        await query.edit_message_text("<b>📖 HELP DETAILS:</b>\nUse /tts for speech.\nUse /sample for demo.", parse_mode="HTML", reply_markup=kb_help_details())
    elif data == 'nav_lang':
        await query.edit_message_text("<b>🌐 SELECT LANGUAGE:</b>", parse_mode="HTML", reply_markup=kb_lang_menu())
    elif data.startswith('setl_'):
        lang = data.split('_')[1]
        context.user_data['user_language'] = lang
        await query.edit_message_text(f"<b>✅ Language set to {lang.upper()}</b>", parse_mode="HTML", reply_markup=kb_lang_menu())
    elif data == 'nav_v3':
        await query.edit_message_text("<b>Bulbul V3 Male:</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V3_MALE, 'v3', 'nav_main'))
    elif data == 'nav_v1':
        await query.edit_message_text("<b>Bulbul V1 Male:</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V1_MALE, 'v1', 'nav_main'))
    elif data.startswith('setv_'):
        v = data.split('_')[1]
        name = data.split('_')[2]
        context.user_data['user_voice'] = name
        context.user_data['user_model'] = f"bulbul:{v}"
        await query.edit_message_text(f"<b>✅ Voice set to {name.upper()} ({v.upper()})</b>", parse_mode="HTML", reply_markup=kb_help_details())

# ========== TTS LOGIC ==========
async def text_to_speech(update: Update, context):
    text = " ".join(context.args) if context.args else update.message.text
    if not text or text.startswith('/'): return
    
    voice = context.user_data.get('user_voice', DEFAULT_SPEAKER)
    model = context.user_data.get('user_model', DEFAULT_MODEL)
    lang = context.user_data.get('user_language', DEFAULT_LANGUAGE)
    
    processing = await update.message.reply_text("<b>🎵 Generating...</b>", parse_mode="HTML")
    try:
        res = requests.post("https://api.sarvam.ai/text-to-speech", 
            headers={"api-subscription-key": SARVAM_API_KEY},
            json={"text": text, "target_language_code": lang, "speaker": voice, "model": model})
        audio_b64 = res.json().get("audios")[0]
        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "voice.mp3"
        await update.message.reply_voice(voice=audio_file, caption=f"<b>🔊 {voice.upper()}</b>{FOOTER}", parse_mode="HTML")
        await processing.delete()
    except:
        await processing.edit_text("<b>❌ Error!</b>")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("voice", start))
    app.add_handler(CommandHandler("lang", lambda u, c: u.message.reply_text("<b>Select Language:</b>", parse_mode="HTML", reply_markup=kb_lang_menu())))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
