import logging
import re
import json
import os
import asyncio
import threading
import httpx
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# 1. DUMMY WEB SERVER UNTUK RENDER PORT 10000
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "FIYYA Official AI Bot Engine Online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# 2. KONFIGURASI BOT TELEGRAM & OPENROUTER
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

# SYSTEM PROMPT WHITEPAPER V.01.0.3 LENGKAP
SYSTEM_PROMPT = f"""
PERAN & KONTROL UTAMA:
Kamu adalah Asisten AI Resmi & Pintar untuk platform FIYYA ({REFERRAL_LINK}).
Jawab pertanyaan pengguna secara cerdas, profesional, ramah, dan teliti dalam bahasa yang digunakan pengguna.

ATURAN PERILAKU WAJIB:
1. SAPAAN RAMAH: Setiap kali pengguna menyapa (Halo, Pagi/Sore/Malam, Hai, dsb), WAJIB membalas ramah terlebih dahulu.
2. RESPON RINCI: Jika pengguna menanyakan tentang bonus jaringan/pengembangan tim, berikan rincian Career Matrix V1-V8, Daily Matching Bonus, dan Payout Cap secara detail.
3. PENDAFTARAN: Arahkan pengguna untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan jika menanyakan cara mendaftar/buat akun.
4. BATASAN: Dilarang keras membahas agama, syariah, atau topik di luar ekosistem FIYYA.

DATABASE PENGETAHUAN RESMI FIYYA:
- **Definisi FIYYA**: Platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI yang terhubung via WebSocket ke exchange global (Binance, OKX, Coinbase, Kraken).
- **Target Yield & Profit Split**: Target Daily Yield 1.5% per hari (Profit Split: 60% USDT cair + 40% FIYYA Token vesting harian 100 hari).
- **Plan & Masa Kontrak (Payout Cap)**: Combined Lifetime Payout Cap antara 200% hingga 350% dari total deposit. Masa kontrak selesai begitu total profit mencapai Payout Cap.
- **Sistem Dual Vault**:
  * Staking Vault: Modal $100 - $10.000 USDT (yield pasif 1.5%/hari).
  * Node Vault ($500 / $1.000 USDT): Paket kualifikasi akselerasi instan ke Rank V4/V5 tanpa syarat tim awal yang besar.
- **Rincian Bonus Pengembangan Jaringan (Career Matrix V1 - V8)**:
  * **Daily Matching Bonus**: Bonus persentase dari profit harian pasif tim downline Anda.
  * **Peningkatan Payout Cap**: Payout Cap bertambah seiring kenaikan rank (dari 200% hingga maksimal 350%).
  * **Kualifikasi Rank (V1 - V8)**: Didasarkan pada akumulasi omzet staking tim jaringan.
  * **Node Vault Pass**: Membeli Node Vault ($500 / $1.000) memotong syarat omzet dan langsung memberikan kualifikasi Rank V4 atau V5.
- **Penarikan (Withdrawal / WD)**: Minimal WD 10 USDT. Fee: Instant (10%), >15 Hari (5%), >30 Hari (3%).
- **Tokenomics**: Total Supply 1 Miliar Token BEP-20 (BNB Chain), Initial Listing DEX Price $0.01 USD.
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# TOMBOL RESMI (DIRECT URL LINK - BEBAS CRASH)
def get_official_buttons():
    keyboard = [[InlineKeyboardButton("🚀 Register / Join FIYYA", url=REFERRAL_LINK)]]
    return InlineKeyboardMarkup(keyboard)

def clean_markdown(text):
    return re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', text)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_conversations[chat_id] = []
    
    welcome_text = (
        "Halo! Selamat datang di FIYYA Official AI Assistant. 👋\n\n"
        "Saya adalah asisten virtual resmi untuk platform FIYYA.\n"
        "Ada yang bisa saya bantu terkait teknologi arbitrase, Dual Vault, minimal deposit, reward, plan, atau penarikan?"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_text = update.message.text
    t = user_text.lower().strip()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # 1. HANDLING SAPAAN INSTAN
    if any(k in t for k in ["sore", "pagi", "siang", "malam", "halo", "hi", "hai", "helo", "apa kabar", "assalamualaikum"]):
        if "pagi" in t: sapaan = "Selamat pagi!"
        elif "siang" in t: sapaan = "Selamat siang!"
        elif "malam" in t: sapaan = "Selamat malam!"
        else: sapaan = "Selamat sore!"

        bot_reply = f"Halo, {sapaan} 👋 Selamat datang di FIYYA Official AI Assistant. Ada yang bisa saya bantu terkait platform FIYYA, deposit, plan, atau reward jaringan hari ini?"
        user_conversations.setdefault(chat_id, []).append({"role": "user", "content": user_text})
        user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
        return

    # 2. MEMORI PERCAKAPAN
    if chat_id not in user_conversations:
        user_conversations[chat_id] = []

    user_conversations[chat_id].append({"role": "user", "content": user_text})
    if len(user_conversations[chat_id]) > 8:
        user_conversations[chat_id] = user_conversations[chat_id][-8:]

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + user_conversations[chat_id]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://fiyya.co",
        "X-Title": "FIYYA Bot",
        "Content-Type": "application/json"
    }
    
    models_to_try = [
        "qwen/qwen-2.5-7b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-lite-preview-02-05:free"
    ]
    
    bot_reply = None
    
    # 3. PANGGIL LLM API
    async with httpx.AsyncClient(timeout=10.0) as client_http:
        for model in models_to_try:
            try:
                data = {
                    "model": model,
                    "messages": messages_payload,
                    "temperature": 0.3
                }
                res = await client_http.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
                if res.status_code == 200:
                    res_json = res.json()
                    if "choices" in res_json and len(res_json["choices"]) > 0:
                        bot_reply = res_json['choices'][0]['message']['content']
                        break
            except Exception as e:
                logging.error(f"Error model {model}: {e}")
                continue

    # 4. FALLBACK FLEKSIBEL (DETEKSI TYPO "JARINGAM", "BONOS", DLSB)
    if not bot_reply:
        if any(k in t for k in ["jaring", "referral", "refrensi", "matrix", "career", "v1", "v8", "matching", "downline", "kembang"]):
            bot_reply = (
                "Rincian Bonus & Program Pengembangan Jaringan FIYYA (Career Matrix V1 - V8):\n\n"
                "1. **Daily Matching Bonus**: Anda menerima bonus persentase harian yang dihitung dari hasil profit pasif tim/downline Anda.\n"
                "2. **Peningkatan Payout Cap (200% - 350%)**: Batas maksimal total pendapatan Anda terus naik seiring meningkatnya rank karir (V1 ke V8).\n"
                "3. **Kualifikasi Rank (V1-V8)**: Dicapai berdasarkan akumulasi total omzet Staking Vault tim jaringan Anda.\n"
                "4. **Node Vault Pass ($500 / $1.000 USDT)**: Memungkinkan Anda meraih kualifikasi instan ke Rank V4/V5 tanpa harus mengumpulkan omzet jaringan besar dari awal."
            )
        elif any(k in t for k in ["500", "1000", "node"]):
            bot_reply = "Node Vault ($500 / $1.000 USDT) adalah paket partisipasi khusus untuk memberikan **akselerasi kualifikasi rank V4 atau V5 secara instan** tanpa harus membangun omzet tim awal yang besar."
        elif any(k in t for k in ["plan", "kontrak", "durasi", "lama", "payout cap"]):
            bot_reply = "Sistem kontrak di FIYYA menggunakan **Combined Lifetime Payout Cap** antara 200% hingga 350% dari modal deposit. Masa kontrak selesai jika total profit harian Anda sudah mencapai batas Payout Cap tersebut."
        elif any(k in t for k in ["reward", "profit", "yield", "bunga", "hasil"]):
            bot_reply = "Target Daily Yield FIYYA adalah **1.5% per hari** (Profit split: 60% USDT cair yang dapat ditarik langsung + 40% Token FIYYA dengan vesting 100 hari)."
        elif any(k in t for k in ["apa itu", "fiyya itu", "jelaskan", "pengertian"]):
            bot_reply = "FIYYA adalah platform arbitrase High-Frequency Trading (HFT) berbasis Agentic OS AI yang mengeksekusi perbedaan harga aset kripto di berbagai exchange global (Binance, OKX, Coinbase, Kraken) secara otomatis."
        elif any(k in t for k in ["wd", "withdraw", "penarikan", "tarik"]):
            bot_reply = "Minimal penarikan (WD) di FIYYA adalah **10 USDT** dengan biaya berjenjang: Instant (10%), >15 Hari (5%), dan >30 Hari (3%)."
        elif any(k in t for k in ["deposit", "modal", "depo", "vault"]):
            bot_reply = "Minimal deposit Staking Vault mulai dari **$100 USDT**, sedangkan Node Vault sebesar **$500 / $1.000 USDT**."
        else:
            bot_reply = f"Silakan tanyakan informasi seputar FIYYA, atau klik tombol '🚀 Register / Join FIYYA' di bawah untuk pendaftaran akun resmi:\n\n👉 {REFERRAL_LINK}"

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
