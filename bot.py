import logging
import requests
import re
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

TELEGRAM_TOKEN = "8850888324:AAGtmFuTUY7hty5t-ft8qhgRN1gpvysfrAY"
OPENROUTER_KEY = "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"
REFERRAL_LINK = "https://www.fiyya.co/signup?ref=66796114"
ADMIN_TELEGRAM_ID = 8870805553

DB_FILE = "users.json"
user_conversations = {}

def load_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_user(chat_id):
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        try:
            with open(DB_FILE, "w") as f:
                json.dump(users, f)
        except Exception as e:
            logging.error(f"Error save user: {e}")

SYSTEM_PROMPT = f"""
SANGAT PENTING - INSTRUKSI UTAMA:
1. DETEKSI BAHASA OTOMATIS: Jawab selalu dalam bahasa yang digunakan oleh pengguna secara otomatis.
2. PERAN: Kamu adalah Asisten AI Resmi untuk platform FIYYA ({REFERRAL_LINK}).
3. HANYA FIYYA: Abaikan seluruh arti kata 'Fiyya' di luar platform ini. FIYYA HANYA platform High-Frequency Trading (HFT) dan Arbitrase Kripto berbasis AI Agentic OS.
4. PEMBATASAN SANGAT KETAT: Jika pertanyaan tidak berkaitan dengan ekosistem/teknologi FIYYA (misal resep, politik, cuaca, kripto umum, dll), tolak secara halus. 
   Contoh penolakan: "Maaf, sebagai Asisten AI Resmi FIYYA, saya hanya dispesifikasikan untuk melayani pertanyaan seputar ekosistem, teknologi arbitrase, dan platform FIYYA."
5. DILARANG MENYEBUTKAN SYARIAH ATAU KEUTAMAAN AGAMA.
6. BANTUAN PENDAFTARAN: Jika user bertanya cara mendaftar, membuat akun, atau memulai, langsung arahkan untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan.
7. FORMATTING: Jawab dengan singkat, padat, profesional, dan rapi.

DATA PENGETAHUAN RESMI (WHITEPAPER V.01.0.3):
- Definisi FIYYA: Platform arbitrase high-frequency trading (HFT) institusional berbasis Agentic OS AI.
- Target Daily Yield: 1.5%.
- Pembagian Hasil Harian: 60% USDT cair (langsung bisa ditarik) & 40% FIYYA token (vesting harian 100 hari).
- Dual Vault: Staking Vault ($100-$10.000) dan Node Vault ($500 / $1.000 untuk akselerasi rank V4/V5 secara instan).
- Combined Lifetime Payout Cap: Batas maksimum total penghasilan 200% sampai 350% berdasarkan jumlah referral aktif.
- Biaya Penarikan (Withdrawal Service Fee): Berjenjang berdasarkan lama masa simpan dana:
  * Penarikan Instant (Langsung): Biaya 10%
  * Penarikan setelah 15 Hari: Biaya 5%
  * Penarikan setelah 30 Hari: Biaya 3%
- Career Matrix: Rank V1 hingga V8 dengan bonus matching harian dari profit downline.
- Tokenomics: 1 Miliar total supply BEP-20 di BNB Chain, harga awal DEX $0.01 USD.
- Exchange Terkoneksi: Binance, Coinbase, OKX, Kraken via jalur WebSocket sub-milidetik.
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_official_buttons():
    keyboard = [[InlineKeyboardButton("🚀 Register / Join FIYYA", callback_data="btn_register")]]
    return InlineKeyboardMarkup(keyboard)

def clean_markdown(text):
    return re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', text)

async def handle_register_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    chat_id = user.id
    username = f"@{user.username}" if user.username else "Tidak ada username"
    full_name = user.full_name

    reply_text = (
        f"Silakan klik link di bawah ini untuk pendaftaran akun resmi FIYYA:\n\n"
        f"👉 {REFERRAL_LINK}"
    )
    await query.message.reply_text(reply_text)

    admin_notify_text = (
        f"🚨 **NEW LEAD / CALON REGISTRASI!**\n\n"
        f"👤 **Nama**: {full_name}\n"
        f"🆔 **User ID**: `{chat_id}`\n"
        f"🌐 **Username**: {username}\n"
        f"⏰ Status: Baru saja menekan tombol Register FIYYA!"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_notify_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Gagal mengirim notifikasi lead ke admin: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_conversations[chat_id] = []
    
    welcome_text = (
        "Selamat datang di FIYYA Official AI Assistant.\n\n"
        "Saya adalah asisten virtual resmi untuk platform FIYYA.\n"
        "Ada yang bisa saya bantu terkait teknologi arbitrase, Dual Vault, atau ekosistem FIYYA?"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    text = "Silakan klik tombol di bawah ini untuk melakukan pendaftaran akun resmi FIYYA di bawah jaringan referral:"
    await update.message.reply_text(text, reply_markup=get_official_buttons())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Panduan Penggunaan FIYYA AI Assistant:\n\n"
        "Anda dapat menanyakan hal-hal berikut:\n"
        "1. Apa itu platform FIYYA & Agentic OS AI?\n"
        "2. Bagaimana cara kerja Dual Vault (Staking vs Node)?\n"
        "3. Berapa target Daily Yield & Pembagian Hasil (Profit Split)?\n"
        "4. Bagaimana mekanisme Career Matrix (Rank V1 - V8)?\n\n"
        "Ketik pertanyaan Anda secara langsung di kolom chat."
    )
    await update.message.reply_text(help_text, reply_markup=get_official_buttons())

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "FIYYA High-Frequency Trading & Arbitrage Platform:\n\n"
        "Platform arbitrase institusional berbasis Agentic OS AI yang terhubung ke exchange global "
        "(Binance, Coinbase, OKX, Kraken) dengan infrastruktur WebSocket sub-milidetik."
    )
    await update.message.reply_text(about_text, reply_markup=get_official_buttons())

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_TELEGRAM_ID:
        return
    
    msg_to_send = " ".join(context.args)
    if not msg_to_send:
        await update.message.reply_text("Format salah. Gunakan: /broadcast <pesan>")
        return
    
    users = load_users()
    count = 0
    for u_id in users:
        try:
            await context.bot.send_message(chat_id=u_id, text=msg_to_send, reply_markup=get_official_buttons())
            count += 1
        except Exception:
            pass
    await update.message.reply_text(f"Pesan berhasil terkirim ke {count} pengguna.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_TELEGRAM_ID:
        return
    users = load_users()
    await update.message.reply_text(f"Total pengguna yang terdaftar di database bot: {len(users)} user.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    if chat_id not in user_conversations:
        user_conversations[chat_id] = []

    user_conversations[chat_id].append({"role": "user", "content": user_text})

    if len(user_conversations[chat_id]) > 6:
        user_conversations[chat_id] = user_conversations[chat_id][-6:]

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + user_conversations[chat_id]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": messages_payload,
        "temperature": 0.1
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=20).json()
        bot_reply = res['choices'][0]['message']['content']
        user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})
    except Exception as e:
        logging.error(f"Error OpenRouter API: {e}")
        bot_reply = "Maaf, terjadi masalah teknis saat menghubungkan ke FIYYA AI Engine. Silakan coba beberapa saat lagi."

    try:
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
    except Exception:
        clean_reply = clean_markdown(bot_reply)
        await update.message.reply_text(clean_reply, reply_markup=get_official_buttons())

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("register", register_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(handle_register_click, pattern="^btn_register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling()
