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
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

# 1. DUMMY WEB SERVER UNTUK RENDER (MEMENUHI SYARAT PORT 10000)
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "FIYYA Official AI Bot Enterprise Engine Online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# 2. KONFIGURASI KREDENSIAL & PARAMETER UTAMA
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

# KNOWLEDGE BASE UTUH FIYYA (WHITEPAPER V.01.0.3)
SYSTEM_PROMPT = f"""
PERAN & INSTRUKSI UTAMA:
Kamu adalah Asisten AI Resmi, Pintar, dan Ramah untuk ekosistem FIYYA ({REFERRAL_LINK}).
Jawab pertanyaan pengguna secara cerdas, profesional, luwes, dan kontekstual dalam bahasa yang digunakan pengguna.

ATURAN PERILAKU WAJIB:
1. SAPAAN RAMAH: Setiap kali pengguna menyapa (seperti "Halo", "Hai", "Selamat sore/pagi/siang/malam", "Apa kabar", "Assalamu'alaikum", dll), WAJIB membalas sapaan dengan ramah terlebih dahulu, lalu tanyakan apa yang bisa dibantu mengenai ekosistem FIYYA.
2. RESPON KONTEKSUAL: Jawab pertanyaan pengguna secara akurat, cerdas, dan lengkap berdasarkan data resmi di bawah ini.
3. PENDAFTARAN: Jika pengguna menanyakan pendaftaran / cara join / pendaftaran akun, arahkan untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan.
4. BATASAN KETAT: Dilarang keras membahas agama, syariah, atau topik di luar ekosistem FIYYA.

DATABASE PENGETAHUAN RESMI FIYYA:
- **Definisi FIYYA**: Platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI yang terhubung via WebSocket sub-milidetik ke exchange global utama (Binance, OKX, Coinbase, Kraken).
- **Target Yield & Profit Split Harian**: Target Daily Yield 1.5% per hari (Profit Split: 60% USDT cair yang bisa ditarik kapan saja + 40% FIYYA Token vesting harian 100 hari).
- **Masa Kontrak & Plan (Payout Cap)**: Menggunakan Combined Lifetime Payout Cap antara 200% hingga 350% dari modal deposit. Masa kontrak selesai begitu total profit mencapai batas Payout Cap tersebut, lalu dapat melakukan re-stake / top-up.
- **Sistem Dual Vault**:
  * Staking Vault: Modal partisipasi $100 - $10.000 USDT untuk pasif yield harian.
  * Node Vault ($500 / $1.000 USDT): Paket kualifikasi akselerasi instan ke Rank V4 atau V5 tanpa syarat omzet tim awal yang besar.
- **Reward Jaringan (Career Matrix V1 - V8)**: Daily Matching Bonus dari profit pasif tim downline dan kenaikan Payout Cap hingga 350%.
- **Penarikan (Withdrawal / WD)**: Minimal WD 10 USDT. Biaya (Fee): Instant (10%), >15 Hari (5%), >30 Hari (3%).
- **Tokenomics**: Total Supply 1 Miliar Token BEP-20 (BNB Chain), Initial Listing DEX Price $0.01 USD.
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
        f"⏰ Status: Menekan tombol Register FIYYA!"
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

    # 1. HANDLING SAPAAN INSTAN (RESPONS CEPAT & HUMANIS)
    if any(k in t for k in ["sore", "pagi", "siang", "malam", "halo", "hi", "hai", "helo", "apa kabar", "assalamualaikum"]):
        if "pagi" in t:
            sapaan_waktu = "Selamat pagi!"
        elif "siang" in t:
            sapaan_waktu = "Selamat siang!"
        elif "malam" in t:
            sapaan_waktu = "Selamat malam!"
        else:
            sapaan_waktu = "Selamat sore!"

        bot_reply = f"Halo, {sapaan_waktu} 👋 Selamat datang di FIYYA Official AI Assistant. Ada yang bisa saya bantu terkait platform FIYYA, deposit, plan, atau reward jaringan hari ini?"
        user_conversations.setdefault(chat_id, []).append({"role": "user", "content": user_text})
        user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
        return

    # 2. PROSES MEMORI CHAT UNTUK PERTANYAAN MATERI
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
    
    # 3. PANGGIL API LLM OPENROUTER VIA HTTPX ASYNC
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

    # 4. COMPREHENSIVE LOCAL FALLBACK ENGINE (JIKA API FAILOVER TIMEOUT)
    if not bot_reply:
        if any(k in t for k in ["500", "1000", "node"]):
            bot_reply = (
                "Node Vault ($500 / $1.000 USDT):\n\n"
                "Node Vault seharga $500 atau $1.000 USDT adalah paket partisipasi khusus untuk memberikan **akselerasi kualifikasi rank V4 atau V5 secara instan** "
                "tanpa harus membangun omzet tim awal yang besar."
            )
        elif any(k in t for k in ["plan", "kontrak", "durasi", "lama", "payout cap"]):
            bot_reply = (
                "Sistem Plan & Masa Kontrak FIYYA:\n\n"
                "Kontrak di FIYYA ditentukan berdasarkan **Combined Lifetime Payout Cap** antara 200% hingga 350% dari total deposit Anda. "
                "Masa kontrak selesai apabila total profit harian Anda sudah mencapai batas Payout Cap tersebut."
            )
        elif any(k in t for k in ["reward", "profit", "yield", "bunga", "hasil"]):
            bot_reply = (
                "Reward & Hasil Harian FIYYA:\n\n"
                "• **Target Yield**: 1.5% per hari.\n"
                "• **Profit Split**: 60% USDT (cair & dapat ditarik langsung) + 40% Token FIYYA (vesting harian 100 hari)."
            )
        elif any(k in t for k in ["jaringan", "referral", "refrensi", "matrix", "career", "v1", "v8", "matching", "downline"]):
            bot_reply = (
                "Reward & Bonus Jaringan FIYYA (Career Matrix V1 - V8):\n\n"
                "• **Daily Matching Bonus**: Bonus harian dari profit pasif tim downline Anda.\n"
                "• **Payout Cap**: Batas total pendapatan meningkat dari 200% hingga 350%.\n"
                "• **Akselerasi Node Vault**: Mengambil Node Vault ($500 / $1.000 USDT) memberikan kualifikasi instan ke Rank V4/V5."
            )
        elif any(k in t for k in ["apa itu", "fiyya itu", "jelaskan", "pengertian"]):
            bot_reply = (
                "FIYYA adalah platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI "
                "yang mengeksekusi selisih harga aset kripto di berbagai exchange global (Binance, OKX, Coinbase, Kraken) secara otomatis."
            )
        elif any(k in t for k in ["wd", "withdraw", "penarikan", "tarik"]):
            bot_reply = "Minimal penarikan (WD) di FIYYA adalah 10 USDT dengan biaya berjenjang: Instant (10%), >15 Hari (5%), dan >30 Hari (3%)."
        elif any(k in t for k in ["deposit", "modal", "depo", "vault"]):
            bot_reply = "Minimal deposit Staking Vault mulai dari $100 USDT, sedangkan Node Vault sebesar $500 / $1.000 USDT."
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
    app.add_handler(CallbackQueryHandler(handle_register_click, pattern="^btn_register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Final Enterprise Engine Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
