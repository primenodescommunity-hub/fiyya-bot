import logging
import requests
import re
import json
import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

# 1. DUMMY WEB SERVER UNTUK RENDER (MEMENUHI SYARAT PORT 10000)
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "FIYYA Official AI Bot is Online & Running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# 2. KONFIGURASI BOT & KREDENSIAL
TELEGRAM_TOKEN = "8850888324:AAHyqhbTzGZuHH2ytQY45qaYPYT6-ARvDd0"
REFERRAL_LINK = "https://www.fiyya.co/signup?ref=66796114"
ADMIN_TELEGRAM_ID = 8870805553

OPENROUTER_KEY = "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"

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

# KNOWLEDGE BASE LENGKAP FIYYA (SESUAI WHITEPAPER RESMI)
SYSTEM_PROMPT = f"""
PERAN & KONTROL UTAMA:
Kamu adalah Asisten AI Resmi & Pintar untuk platform FIYYA ({REFERRAL_LINK}).
Jawab selalu dalam bahasa yang digunakan oleh pengguna secara otomatis (Indonesia, Jepang, Inggris, Mandarin, dll) dengan nada profesional, akurat, dan sangat pintar.

ATURAN UTAMA:
1. RESPON KONTEKSUAL & CERDAS: Jawab pertanyaan user dengan presisi tinggi berdasarkan seluruh data resmi FIYYA di bawah ini.
2. PENDAFTARAN: Jika pengguna menanyakan cara mendaftar/buat akun/join, arahkan untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan.
3. BATASAN: Dilarang keras menyebutkan syariah, agama, atau hal-hal di luar ekosistem FIYYA.

DATABASE PENGETAHUAN LENGKAP FIYYA (WHITEPAPER V.01.0.3):
1. **Definisi Platform**:
   - FIYYA adalah platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI.
   - Terhubung secara real-time via infrastruktur WebSocket sub-milidetik ke exchange global utama (Binance, OKX, Coinbase, Kraken).

2. **Target Yield & Profit Split Harian**:
   - Target Daily Yield Personal: **1.5% per hari**.
   - Pembagian Hasil (Profit Split): **60% USDT** (cair & dapat ditarik kapan saja) + **40% FIYYA Token** (vesting harian selama 100 hari).

3. **Sistem Dual Vault**:
   - **Staking Vault**: Modal partisipasi mulai dari **$100 USDT** hingga $10.000 USDT untuk mendapatkan yield pasif harian.
   - **Node Vault**: Nominal partisipasi $500 atau $1.000 USDT. Memberikan akselerasi kualifikasi instan ke Rank V4/V5 tanpa memerlukan struktur jaringan awal yang besar.

4. **Reward & Bonus Jaringan (Career Matrix V1 - V8)**:
   - Memiliki jenjang karir V1 hingga V8 berdasarkan akumulasi omzet tim downline.
   - **Daily Matching Bonus**: Mendapatkan persentase bonus harian dari hasil profit harian jaringan downline.
   - **Combined Lifetime Payout Cap**: Batas maksimal total pendapatan berjenjang mulai dari **200% hingga 350%** dari total deposit sebelum harus melakukan top-up/re-stake.

5. **Ketentuan Penarikan (Withdrawal / WD)**:
   - **Minimal Penarikan (Minimal WD)**: **10 USDT**.
   - **Biaya Penarikan (Withdrawal Fee)** berjenjang berdasarkan lama masa simpan:
     * Instant / Langsung Penarikan: Biaya 10%
     * Setelah 15 Hari Masa Simpan: Biaya 5%
     * Setelah 30 Hari Masa Simpan: Biaya 3%

6. **Tokenomics (FIYYA Token)**:
   - Total Supply: 1.000.000.000 (1 Miliar) Token BEP-20 di BNB Chain.
   - Initial Listing / DEX Price: $0.01 USD per token.
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

    reply_text = f"Silakan klik link di bawah ini untuk pendaftaran akun resmi FIYYA:\n\n👉 {REFERRAL_LINK}"
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
        logging.error(f"Gagal notif admin: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_conversations[chat_id] = []
    
    welcome_text = (
        "Selamat datang di FIYYA Official AI Assistant.\n\n"
        "Saya adalah asisten virtual resmi untuk platform FIYYA.\n"
        "Ada yang bisa saya bantu terkait teknologi arbitrase, Dual Vault, minimal deposit, reward jaringan, atau penarikan?"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

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
        "HTTP-Referer": "https://fiyya.co",
        "X-Title": "FIYYA Bot",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
        "messages": messages_payload,
        "temperature": 0.3
    }
    
    bot_reply = None
    try:
        loop = asyncio.get_event_loop()
        req = await loop.run_in_executor(None, lambda: requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=15))
        res_json = req.json()
        if "choices" in res_json and len(res_json["choices"]) > 0:
            bot_reply = res_json['choices'][0]['message']['content']
        else:
            data["model"] = "google/gemini-2.0-flash-exp:free"
            req2 = await loop.run_in_executor(None, lambda: requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=15))
            res_json2 = req2.json()
            if "choices" in res_json2 and len(res_json2["choices"]) > 0:
                bot_reply = res_json2['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error API: {e}")

    # Fallback Komprehensif Berdasarkan Seluruh Sumber Data FIYYA
    if not bot_reply:
        t = user_text.lower()
        if any(k in t for k in ["jaringan", "referral", "refrensi", "matrix", "career", "v1", "v8", "matching", "downline"]):
            bot_reply = (
                "Bonus & Reward Jaringan FIYYA (Career Matrix V1 - V8):\n\n"
                "• **Daily Matching Bonus**: Bonus harian dari profit pasif tim downline Anda.\n"
                "• **Payout Cap**: Batas total pendapatan (Combined Lifetime Payout Cap) meningkat dari 200% hingga 350%.\n"
                "• **Akselerasi Node Vault**: Node Vault ($500 / $1.000 USDT) memberikan kualifikasi instan ke Rank V4/V5 tanpa jaringan besar dari awal."
            )
        elif any(k in t for k in ["wd", "withdraw", "penarikan", "tarik"]):
            bot_reply = (
                "Informasi Penarikan (Withdrawal) FIYYA:\n\n"
                "• **Minimal WD**: 10 USDT\n"
                "• **Biaya Penarikan (Fee)**: Instant (10%), Simpan >15 Hari (5%), Simpan >30 Hari (3%)."
            )
        elif any(k in t for k in ["deposit", "modal", "depo", "vault"]):
            bot_reply = (
                "Minimal Deposit FIYYA:\n\n"
                "• **Staking Vault**: Mulai $100 USDT hingga $10.000 USDT (Target Yield 1.5%/hari).\n"
                "• **Node Vault**: $500 / $1.000 USDT (Akselerasi Rank V4/V5)."
            )
        elif any(k in t for k in ["reward", "profit", "yield", "bunga", "hasil"]):
            bot_reply = "Target Daily Yield FIYYA adalah 1.5% per hari dengan pembagian profit 60% USDT cair dan 40% FIYYA Token (vesting harian 100 hari)."
        else:
            bot_reply = f"Untuk pendaftaran akun resmi FIYYA atau informasi selengkapnya, silakan klik tombol '🚀 Register / Join FIYYA' di bawah atau via link: {REFERRAL_LINK}"

    user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})

    try:
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
    except Exception:
        clean_reply = clean_markdown(bot_reply)
        await update.message.reply_text(clean_reply, reply_markup=get_official_buttons())

def main():
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_register_click, pattern="^btn_register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
