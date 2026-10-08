import logging
import requests
import re
import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

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

SYSTEM_PROMPT = f"""
PERAN & INSTRUKSI UTAMA:
Kamu adalah Asisten AI Pintar dan Resmi untuk platform FIYYA ({REFERRAL_LINK}).
Jawab selalu dalam bahasa yang digunakan oleh pengguna secara otomatis (Indonesia, Jepang, Inggris, dll) dengan nada profesional, ramah, dan pintar.

ATURAN KETAT:
1. PINTAR & KONTEKSUAL: Pahami maksud pertanyaan user secara alami (misal "minimal wd", "berapa modalnya", "cara kerja", "FIYYA itu apa").
2. HANYA TOPIK FIYYA: Jika ditanya di luar topik FIYYA, tolak dengan sopan.
3. DILARANG MENYEBUTKAN SYARIAH ATAU KEUTAMAAN AGAMA.
4. PENDAFTARAN: Arahkan user untuk menekan tombol '🚀 Register / Join FIYYA' di bawah jika menanyakan cara mendaftar/buat akun.

DATA PENGETAHUAN RESMI FIYYA (WHITEPAPER V.01.0.3):
- Platform: FIYYA (Arbitrase High-Frequency Trading / HFT berbasis Agentic OS AI).
- Daily Yield / Reward: Target 1.5% per hari.
- Profit Split Harian: 60% USDT cair (bisa ditarik kapan saja) & 40% FIYYA token (vesting harian 100 hari).
- Dual Vault: Staking Vault ($100-$10.000 USDT) dan Node Vault ($500 / $1.000 USDT untuk akselerasi rank V4/V5 instan).
- Penarikan Dana (Withdrawal / WD): Minimal WD adalah 10 USDT. Biaya (Fee): Instant (10%), Simpan >15 Hari (5%), Simpan >30 Hari (3%).
- Career Matrix: Rank V1 hingga V8 dengan bonus matching harian dari profit downline.
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

    if not bot_reply:
        t = user_text.lower()
        if any(k in t for k in ["wd", "withdraw", "penarikan", "tarik"]):
            bot_reply = "Minimal penarikan (WD) di FIYYA adalah 10 USDT dengan biaya berjenjang: Instant (10%), 15 Hari (5%), dan 30 Hari (3%)."
        elif any(k in t for k in ["deposit", "modal", "depo"]):
            bot_reply = "Minimal deposit Staking Vault di FIYYA mulai dari $100 USDT, sedangkan Node Vault mulai dari $500 / $1.000 USDT."
        else:
            bot_reply = f"Untuk informasi pendaftaran akun resmi FIYYA, silakan tekan tombol '🚀 Register / Join FIYYA' di bawah atau via link: {REFERRAL_LINK}"

    user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})

    try:
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
    except Exception:
        clean_reply = clean_markdown(bot_reply)
        await update.message.reply_text(clean_reply, reply_markup=get_official_buttons())

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_register_click, pattern="^btn_register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
