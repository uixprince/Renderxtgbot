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
DEFAULT_PACE = 1.0 # Normal Speed
SAMPLE_RATE = 24000

OWNER_LINK = "https://t.me/KYA_KROGE_NAME_JAANKE"
FOOTER = f'\n\n<b>POWERED BY <a href="{OWNER_LINK}">ᏢᎡϟꋊᏣᎬ༒࿗</a></b>'

# ========== VOICE DATABASES ==========
VOICES_V3_MALE = ["aditya", "rahul", "rohan", "amit", "dev", "ratan", "varun", "manan", "sumit", "kabir", "aayan", "shubh", "ashutosh", "advait"]
VOICES_V3_FEMALE = ["ritu", "priya", "neha", "pooja", "simran", "kavya", "ishita", "shreya", "roopa"]

# Sample of V1 Voices (The old 50+ list)
VOICES_V1_MALE = ["abhilash", "karun", "hitesh", "samir", "pranav", "karan", "vikram"]
VOICES_V1_FEMALE = ["anushka", "manisha", "vidya", "arya", "sonia", "tanvi", "kiara"]

# 🌟 BEST CURATED VOICES (Top tier realistic voices)
BEST_VOICES = ["aditya", "ritu", "shubh", "priya", "amit", "neha", "rohan", "kavya"]

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

# ========== UI KEYBOARDS GENERATORS ==========
def kb_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Best Voices (Top Picks)", callback_data='nav_best')],
        [InlineKeyboardButton("🎙️ Bulbul V3 (25 Premium)", callback_data='nav_v3')],
        [InlineKeyboardButton("📻 Bulbul V1 (Classic 50+)", callback_data='nav_v1')],
        [InlineKeyboardButton("⚙️ Speed Control", callback_data='nav_speed')],
        [InlineKeyboardButton("👑 Owner Info", url=OWNER_LINK)]
    ])

def kb_gender_menu(version):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👦 Male Voices", callback_data=f'gen_{version}_m'), InlineKeyboardButton("👧 Female Voices", callback_data=f'gen_{version}_f')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='nav_main')]
    ])

def kb_speed_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐢 Slow (0.8x)", callback_data='spd_0.85'), InlineKeyboardButton("🚶 Normal (1.0x)", callback_data='spd_1.0')],
        [InlineKeyboardButton("🏃 Fast (1.2x)", callback_data='spd_1.2')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='nav_main')]
    ])

def kb_voice_grid(voices, version, back_callback):
    # Generates a 3-column grid for voices
    keyboard = []
    row = []
    for voice in voices:
        row.append(InlineKeyboardButton(voice.capitalize(), callback_data=f'setv_{version}_{voice}'))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

# ========== COMMAND HANDLERS ==========
async def start(update: Update, context):
    user = update.effective_user
    msg = (
        f"<b>HELLO {user.mention_html()}, WELCOME TO THE VIP TTS BOT!</b>\n\n"
        "<b>Send /voice to open the Interactive Control Panel!</b>"
        f"{FOOTER}"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎛️ OPEN CONTROL PANEL", callback_data='nav_main')]]), disable_web_page_preview=True)

async def voice_panel_cmd(update: Update, context):
    msg = "<b>🎛️ MASTER CONTROL PANEL</b>\n\n<b>Select a category below to customize your voice and speed:</b>"
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_main_menu())

# ========== THE NESTED BUTTON LOGIC ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # Main Navigation
    if data == 'nav_main':
        await query.answer()
        await query.edit_message_text("<b>🎛️ MASTER CONTROL PANEL</b>\n\n<b>Select an option:</b>", parse_mode="HTML", reply_markup=kb_main_menu())
    
    elif data == 'nav_best':
        await query.answer()
        await query.edit_message_text("<b>⭐ CURATED BEST VOICES</b>\n\n<b>Most realistic voices handpicked for you:</b>", parse_mode="HTML", reply_markup=kb_voice_grid(BEST_VOICES, 'v3', 'nav_main'))
        
    elif data == 'nav_v3':
        await query.answer()
        await query.edit_message_text("<b>🎙️ BULBUL V3 (PREMIUM VOICES)</b>\n\n<b>Choose a gender:</b>", parse_mode="HTML", reply_markup=kb_gender_menu('v3'))
        
    elif data == 'nav_v1':
        await query.answer()
        await query.edit_message_text("<b>📻 BULBUL V1 (CLASSIC VOICES)</b>\n\n<b>Choose a gender:</b>", parse_mode="HTML", reply_markup=kb_gender_menu('v1'))
        
    elif data == 'nav_speed':
        await query.answer()
        await query.edit_message_text("<b>⚙️ SPEED CONTROL</b>\n\n<b>Adjust how fast the bot speaks:</b>", parse_mode="HTML", reply_markup=kb_speed_menu())

    # Speed Setup
    elif data.startswith('spd_'):
        speed_val = float(data.split('_')[1])
        context.user_data['user_pace'] = speed_val
        await query.answer(f"Speed set to {speed_val}x!")
        await query.edit_message_text(f"<b>✅ Speed successfully set to {speed_val}x!</b>", parse_mode="HTML", reply_markup=kb_speed_menu())

    # Gender Selections (Shows grids)
    elif data == 'gen_v3_m':
        await query.answer()
        await query.edit_message_text("<b>👦 PREMIUM MALE VOICES (V3)</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V3_MALE, 'v3', 'nav_v3'))
    elif data == 'gen_v3_f':
        await query.answer()
        await query.edit_message_text("<b>👧 PREMIUM FEMALE VOICES (V3)</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V3_FEMALE, 'v3', 'nav_v3'))
    elif data == 'gen_v1_m':
        await query.answer()
        await query.edit_message_text("<b>👦 CLASSIC MALE VOICES (V1)</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V1_MALE, 'v1', 'nav_v1'))
    elif data == 'gen_v1_f':
        await query.answer()
        await query.edit_message_text("<b>👧 CLASSIC FEMALE VOICES (V1)</b>", parse_mode="HTML", reply_markup=kb_voice_grid(VOICES_V1_FEMALE, 'v1', 'nav_v1'))

    # Final Voice Setup
    elif data.startswith('setv_'):
        parts = data.split('_')
        version = "bulbul:v3" if parts[1] == 'v3' else "bulbul:v1"
        voice_name = parts[2]
        
        context.user_data['user_voice'] = voice_name
        context.user_data['user_model'] = version
        
        await query.answer(f"Voice set to {voice_name.capitalize()} ({version})")
        await query.edit_message_text(
            f"<b>✅ PERFECT!</b>\n\n<b>Voice:</b> {voice_name.capitalize()}\n<b>Model:</b> {version.upper()}\n\n<b>Now use /tts &lt;text&gt; to generate speech!</b>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='nav_main')]])
        )

# ========== MANUAL COMMANDS (Direct Set) ==========
async def set_voice_cmd(update: Update, context):
    if not context.args:
        return await update.message.reply_text("<b>USAGE: /setvoice ritu</b>\n<i>Pro tip: Use /voice for a better button menu!</i>", parse_mode="HTML")
    voice = context.args[0].lower()
    context.user_data['user_voice'] = voice
    await update.message.reply_text(f"<b>✅ VOICE UPDATED TO: {voice.upper()}</b>", parse_mode="HTML")

# ========== TTS GENERATOR ==========
async def text_to_speech(update: Update, context):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("<b>⚠️ INPUT TEXT REQUIRED! EXAMPLE: /tts Hello Boss</b>", parse_mode="HTML")

    await update.message.chat.send_action(action="record_voice")
    
    # Fetch user preferences
    voice = context.user_data.get('user_voice', DEFAULT_SPEAKER)
    model = context.user_data.get('user_model', DEFAULT_MODEL)
    lang = context.user_data.get('user_language', DEFAULT_LANGUAGE)
    pace = context.user_data.get('user_pace', DEFAULT_PACE)
    
    processing = await update.message.reply_text(f"<b>🎵 PROCESSING...</b>\n<i>Voice: {voice.capitalize()} | Model: {model[-2:].upper()} | Speed: {pace}x</i>", parse_mode="HTML")

    try:
        response = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text, 
                "target_language_code": lang, 
                "speaker": voice,
                "model": model, 
                "speech_sample_rate": SAMPLE_RATE, 
                "enable_preprocessing": True,
                "pace": pace # <--- Speed Control sent to API
            },
            timeout=30
        )
        
        if response.status_code != 200:
            await processing.edit_text(f"<b>❌ API ERROR: {response.status_code}</b>\nDetails: {response.text[:100]}", parse_mode="HTML")
            return
            
        data = response.json()
        audio_b64 = data.get("audios", [None])[0]

        if not audio_b64:
            await processing.edit_text("<b>❌ FAILED TO RECEIVE AUDIO FROM API.</b>", parse_mode="HTML")
            return

        audio_file = io.BytesIO(base64.b64decode(audio_b64))
        audio_file.name = "voice.mp3"

        caption = f"<b>🔊 VOICE: {voice.upper()} ({model[-2:].upper()})</b>\n<b>⚡ SPEED: {pace}x</b>{FOOTER}"
        await update.message.reply_voice(voice=audio_file, caption=caption, parse_mode="HTML")
        await processing.delete()

    except Exception as e:
        logger.error(f"TTS Error: {e}")
        await update.message.reply_text(f"<b>❌ ERROR: {str(e)[:100]}</b>", parse_mode="HTML")

async def error_handler(update: Update, context):
    logger.error(f"CRITICAL Update error: {context.error}")

def main():
    threading.Thread(target=keep_alive, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", voice_panel_cmd))  # The Master Menu Command
    app.add_handler(CommandHandler("setvoice", set_voice_cmd)) 
    app.add_handler(CommandHandler("tts", text_to_speech))
    
    # Handle all the nested button clicks
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("🚀 BOT DEPLOYED WITH NESTED UI & SPEED CONTROL!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
