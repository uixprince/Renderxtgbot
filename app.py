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
SARVAM_API_KEY = "sk_g7nu0ztm_bJSAdtnwoM6aTPXVoF30F9WV" 

DEFAULT_MODEL = "bulbul:v3"
DEFAULT_SPEAKER = "aditya"
DEFAULT_LANGUAGE = "hi-IN"
DEFAULT_PACE = 1.0 
SAMPLE_RATE = 24000

OWNER_LINK = "https://t.me/KYA_KROGE_NAME_JAANKE"
CHANNEL_LINK = "https://t.me/ui_zone"
FOOTER = f'\n\n<b>POWERED BY <a href="{OWNER_LINK}">ᏢᎡϟꋊᏣᎬ༒࿗</a></b>'

# ========== VOICE DATABASE (ONLY VERIFIED V3) ==========
VOICES_V3_MALE = ["aditya", "rahul", "rohan", "amit", "dev", "ratan", "varun", "manan", "sumit", "kabir", "aayan", "shubh", "ashutosh", "advait"]
VOICES_V3_FEMALE = ["ritu", "priya", "neha", "pooja", "simran", "kavya", "ishita", "shreya", "roopa"]

VOICES_V1_MALE = ["abhilash", "karun", "hitesh", "samir", "pranav", "karan", "vikram", "ajit", "alok", "deepak"]
VOICES_V1_FEMALE = ["anushka", "manisha", "vidya", "arya", "sonia", "tanvi", "kiara", "bharti", "chitra", "divya"]

LANGUAGES = {"Hindi 🇮🇳": "hi-IN", "English 🇺🇸": "en-IN", "Tamil 🇮🇳": "ta-IN", "Telugu 🇮🇳": "te-IN", "Bengali 🇮🇳": "bn-IN"}

# ========== DUMMY SERVER ==========
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
        [InlineKeyboardButton("🎙️ V3 (Premium)", callback_data='nav_v3_gen'), InlineKeyboardButton("📻 V1 (Classic)", callback_data='nav_v1_gen')],
        [InlineKeyboardButton("🌐 Languages", callback_data='nav_lang'), InlineKeyboardButton("⚙️ Speed", callback_data='nav_speed')],
        [InlineKeyboardButton("📖 Help", callback_data='nav_help')],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]
    ])

def kb_gender_menu(version):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👦 Male", callback_data=f'gen_{version}_m'), InlineKeyboardButton("👧 Female", callback_data=f'gen_{version}_f')],
        [InlineKeyboardButton("🔙 Back", callback_data='nav_main')]
    ])

# ========== HANDLERS ==========
async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(f"<b>HELLO {user.mention_html()}!</b>\nUse /voice for settings.{FOOTER}", parse_mode="HTML", reply_markup=kb_main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'nav_main':
        await query.edit_message_text("<b>MASTER CONTROL PANEL</b>", parse_mode="HTML", reply_markup=kb_main_menu())
    elif data == 'nav_lang':
        keyboard = []
        row = []
        for name, code in LANGUAGES.items():
            row.append(InlineKeyboardButton(name, callback_data=f'setl_{code}'))
            if len(row) == 2: keyboard.append(row); row = []
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='nav_main')])
        await query.edit_message_text("<b>🌐 SELECT LANGUAGE:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'nav_speed':
        await query.edit_message_text("<b>SELECT SPEED:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🐢 Slow", callback_data='spd_0.8'), InlineKeyboardButton("🚶 Normal", callback_data='spd_1.0'), InlineKeyboardButton("🏃 Fast", callback_data='spd_1.3')], [InlineKeyboardButton("🔙 Back", callback_data='nav_main')]]))
    elif data.startswith('spd_'):
        context.user_data['user_pace'] = float(data.split('_')[1])
        await query.answer(f"Speed set to {data.split('_')[1]}x")
    elif data.startswith('setl_'):
        context.user_data['user_language'] = data.split('_')[1]
        await query.answer(f"Language set to {data.split('_')[1]}")
    elif data.startswith('gen_'):
        v, g = data.split('_')[1], data.split('_')[2]
        list_v = (VOICES_V3_MALE if g=='m' else VOICES_V3_FEMALE) if v=='v3' else (VOICES_V1_MALE if g=='m' else VOICES_V1_FEMALE)
        keyboard = []
        row = []
        for voice in list_v:
            row.append(InlineKeyboardButton(voice.capitalize(), callback_data=f'setv_{v}_{voice}'))
            if len(row) == 3: keyboard.append(row); row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f'nav_{v}_gen')])
        await query.edit_message_text(f"<b>SELECT {v.upper()} VOICE:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith('setv_'):
        v, name = data.split('_')[1], data.split('_')[2]
        context.user_data['user_voice'], context.user_data['user_model'] = name, f"bulbul:{v}"
        await query.edit_message_text(f"<b>✅ Voice Set: {name.upper()}</b>", parse_mode="HTML", reply_markup=kb_main_menu())
    elif data.startswith('nav_v3_gen') or data.startswith('nav_v1_gen'):
        await query.edit_message_text("<b>SELECT GENDER:</b>", parse_mode="HTML", reply_markup=kb_gender_menu(data.split('_')[1]))

async def text_to_speech(update: Update, context):
    text = " ".join(context.args)
    if not text: return await update.message.reply_text("<b>⚠️ USAGE: /tts your text</b>", parse_mode="HTML")
    
    voice = context.user_data.get('user_voice', DEFAULT_SPEAKER)
    model = context.user_data.get('user_model', DEFAULT_MODEL)
    pace = context.user_data.get('user_pace', DEFAULT_PACE)
    lang = context.user_data.get('user_language', DEFAULT_LANGUAGE)
    
    proc = await update.message.reply_text("<b>🎵 Generating...</b>", parse_mode="HTML")
    try:
        res = requests.post("https://api.sarvam.ai/text-to-speech", 
            headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "target_language_code": lang,
                "speaker": voice,
                "model": model,
                "pace": pace,
                "speech_sample_rate": SAMPLE_RATE,
                "enable_preprocessing": True
            }, timeout=25)
        
        if res.status_code != 200:
            return await proc.edit_text(f"<b>❌ API ERROR: {res.status_code}</b>\n<i>Shayad Credits khatam hain ya API Key block hai!</i>", parse_mode="HTML")

        data = res.json()
        audio_b64 = data.get("audios", [None])[0] or data.get("audio_content")
        
        if not audio_b64:
            return await proc.edit_text("<b>❌ Error: No audio received!</b>", parse_mode="HTML")

        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "v.mp3"
        await update.message.reply_voice(voice=audio_file, caption=f"<b>🔊 {voice.upper()} | {pace}x</b>{FOOTER}", parse_mode="HTML")
        await proc.delete()
        
    except Exception as e: 
        await proc.edit_text(f"<b>❌ Bot Error:</b> {str(e)[:50]}", parse_mode="HTML")

async def run_bot():
    threading.Thread(target=keep_alive, daemon=True).start()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", start))
    app.add_handler(CommandHandler("tts", text_to_speech))
    app.add_handler(CallbackQueryHandler(button_handler))
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__": 
    asyncio.run(run_bot())
                
