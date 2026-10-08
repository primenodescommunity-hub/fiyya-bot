import logging
import re
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

TELEGRAM_TOKEN = "8850888324:AAGtmFuTUY7hty5t-ft8qhgRN1gpvysfrAY"
REFERRAL_LINK = "https://www.fiyya.co/signup?ref=66796114"
ADMIN_TELEGRAM_ID = 8870805553

DB_FILE = "users.json"

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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_official_buttons():
    keyboard = [[InlineKeyboardButton("🚀 Register / Join FIYYA", callback_data="btn_register")]]
    return InlineKeyboardMarkup(keyboard)

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
    text = update.message.text.lower()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    if "daftar" in text or "register" in text or "join" in text or "buat akun" in text:
        bot_reply = f"Untuk mendaftar di akun resmi platform FIYYA, silakan klik tombol '🚀 Register / Join FIYYA' di bawah pesan ini atau akses langsung via link berikut:\n\n👉 {REFERRAL_LINK}"
    elif "vault" in text or "staking" in text or "node" in text:
        bot_reply = "FIYYA menggunakan sistem Dual Vault:\n\n1. **Staking Vault** ($100 - $10.000): Target Daily Yield 1.5% dengan pembagian hasil 60% USDT cair & 40% FIYYA token.\n2. **Node Vault** ($500 / $1.000): Untuk akselerasi instan kualifikasi Rank V4/V5."
    elif "yield" in text or "profit" in text or "hasil" in text or "bunga" in text:
        bot_reply = "Target Daily Yield FIYYA adalah **1.5% per hari**.\n\nPembagian hasil harian:\n• 60% USDT cair (dapat ditarik langsung)\n• 40% FIYYA Token (vesting harian 100 hari)."
    elif "biaya" in text or "fee" in text or "withdraw" in text or "tarik" in text:
        bot_reply = "Biaya Penarikan (Withdrawal Service Fee) FIYYA berjenjang:\n• Penarikan Instant: Biaya 10%\n• Penarikan setelah 15 Hari: Biaya 5%\n• Penarikan setelah 30 Hari: Biaya 3%"
    elif "rank" in text or "career" in text or "v1" in text or "v8" in text or "referral" in text:
        bot_reply = "Ekosistem FIYYA memiliki **Career Matrix V1 hingga V8** dengan bonus matching harian dari profit downline serta Combined Lifetime Payout Cap mulai dari 200% hingga 350%."
    elif "halo" in text or "hi" in text or "p" in text or "test" in text:
        bot_reply = "Halo! Saya adalah Asisten AI Resmi FIYYA. Ada yang bisa saya bantu terkait platform arbitrase FIYYA, Dual Vault, Daily Yield, atau pendaftaran?"
    else:
        bot_reply = f"Sebagai Asisten AI Resmi FIYYA, saya siap melayani pertanyaan seputar ekosistem, teknologi arbitrase, Dual Vault, dan platform FIYYA.\n\nUntuk pendaftaran akun, silakan tekan tombol '🚀 Register / Join FIYYA' di bawah ini."

    await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())

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
    print("Bot FIYYA Ready!")
    app.run_polling()
