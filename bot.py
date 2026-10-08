import logging
import requests
import re
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

TELEGRAM_TOKEN = "8850888324:AAHyqhbTzGZuHH2ytQY45qaYPYT6-ARvDd0"
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
PERAN & KONTROL:
Kamu adalah Asisten AI Resmi untuk platform FIYYA ({REFERRAL_LINK}). Jawab selalu dalam bahasa yang digunakan oleh pengguna secara otomatis.

ATURAN UTAMA:
1. HANYA JAWAB TOPIK FIYYA: Kamu hanya melayani pertanyaan seputar ekosistem, teknologi HFT arbitrase, Dual Vault, Yield, dan platform FIYYA.
2. PENDAFTARAN: Jika user bertanya cara mendaftar/buat akun/join, arahkan untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan.
3. DILARANG MENYEBUTKAN SYARIAH ATAU KEUTAMAAN AGAMA.
4. FORMATTING: Jawab singkat, padat, ramah, dan profesional.

DATA RESMI FIYYA (WHITEPAPER V.01.0.3):
- Definisi FIYYA: Platform arbitrase high-frequency trading (HFT) institusional berbasis Agentic OS AI.
- Target Daily Yield / Reward: 1.5% per hari.
- Profit Split Harian: 60% USDT cair (bisa ditarik kapan saja) & 40% FIYYA token (vesting harian 100 hari).
- Dual Vault: Staking Vault ($100-$10.000 USDT) dan Node Vault ($500 / $1.000 USDT untuk akselerasi rank V4/V5 instan).
- Combined Lifetime Payout Cap: Batas total penghasilan 200% sampai 350% tergantung referral.
- Biaya Penarikan (Withdrawal Fee): Instant (10%), 15 Hari (5%), 30 Hari (3%).
- Career Matrix: Rank V1 hingga V8 dengan bonus matching harian dari profit downline.
- Tokenomics: 1 Miliar total supply BEP-20 di BNB Chain, harga DEX $0.01 USD.
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
        "Ada yang bisa saya bantu terkait teknologi arbitrase, Dual Vault, minimal deposit, atau ekosistem FIYYA?"
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
        "model": "qwen/qwen-2.5-7b-instruct:free",
        "messages": messages_payload,
        "temperature": 0.3
    }
    
    bot_reply = None
    try:
        req = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=20)
        res_json = req.json()
        if "choices" in res_json and len(res_json["choices"]) > 0:
            bot_reply = res_json['choices'][0]['message']['content']
        else:
            data["model"] = "meta-llama/llama-3.3-70b-instruct:free"
            req2 = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=20)
            res_json2 = req2.json()
            if "choices" in res_json2 and len(res_json2["choices"]) > 0:
                bot_reply = res_json2['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error AI API: {e}")

    if not bot_reply:
        t = user_text.lower()
        if any(k in t for k in ["reward", "profit", "yield", "bunga", "hasil"]):
            bot_reply = "Target Daily Yield FIYYA adalah 1.5% per hari dengan pembagian profit 60% USDT cair dan 40% FIYYA Token (vesting 100 hari)."
        elif any(k in t for k in ["deposit", "modal", "minimal"]):
            bot_reply = "Minimal deposit di FIYYA:\n• Staking Vault: Mulai $100 USDT (Target Yield 1.5%/hari).\n• Node Vault: Mulai $500 / $1.000 USDT."
        else:
            bot_reply = f"Untuk informasi selengkapnya atau pendaftaran akun resmi FIYYA, silakan klik tombol '🚀 Register / Join FIYYA' di bawah ini atau kunjungi link berikut:\n\n👉 {REFERRAL_LINK}"

    user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})

    try:
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
    except Exception:
        clean_reply = clean_markdown(bot_reply)
        await update.message.reply_text(clean_reply, reply_markup=get_official_buttons())

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_register_click, pattern="^btn_register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling()
