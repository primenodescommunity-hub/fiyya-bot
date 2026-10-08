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

# 2. KONFIGURASI BOT TELEGRAM & FILE ID DOKUMEN
TELEGRAM_TOKEN = "8850888324:AAHyqhbTzGZuHH2ytQY45qaYPYT6-ARvDd0"
REFERRAL_LINK = "https://www.fiyya.co/signup?ref=66796114"

# FILE_ID RESMI WHITEPAPER PDF
WHITEPAPER_FILE_ID = "BQACAgUAAxkBAAEviX1qx3V07WaYsErlOJImg2hYPDkHRgAC6SMAAgLcOVZOP909CN2LEz0E"

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
2. RESPON WHITEPAPER: Jika pengguna meminta Whitepaper / dokumen resmi / PDF, jelaskan bahwa dokumen resmi memuat arsitektur HFT Agentic OS, Dual Vault, Career Matrix, dan Tokenomics.
3. RESPON RINCI JARINGAN: Jika pengguna menanyakan tentang bonus jaringan/pengembangan tim, berikan rincian Career Matrix V1-V8, Daily Matching Bonus, dan Payout Cap secara detail.
4. PENDAFTARAN: Arahkan pengguna untuk menekan tombol '🚀 Register / Join FIYYA' di bawah pesan jika menanyakan cara mendaftar/buat akun.
5. BATASAN: Dilarang keras membahas agama, syariah, atau topik di luar ekosistem FIYYA.

DATABASE PENGETAHUAN RESMI FIYYA:
- **Definisi FIYYA**: Platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI yang terhubung via WebSocket ke exchange global (Binance, OKX, Coinbase, Kraken).
- **Target Yield & Profit Split**: Target Daily Yield 1.5% per hari (Profit Split: 60% USDT cair + 40% FIYYA Token vesting harian 100 hari).
- **Plan & Masa Kontrak (Payout Cap)**: Combined Lifetime Payout Cap antara 200% hingga 350% dari total deposit. Masa kontrak selesai begitu total profit mencapai Payout Cap.
- **Sistem Dual Vault**:
  * Staking Vault: Modal $100 - $10.000 USDT (yield pasif 1.5%/hari).
  * Node Vault ($500 / $1.000 USDT): Paket kualifikasi akselerasi instan ke Rank V4/V5 tanpa syarat omzet tim awal yang besar.
- **Rincian Bonus Pengembangan Jaringan (Career Matrix V1 - V8)**:
  * **Daily Matching Bonus**: Bonus persentase dari profit harian pasif tim downline Anda.
  * **Peningkatan Payout Cap**: Payout Cap bertambah seiring kenaikan rank (dari 200% hingga maksimal 350%).
  * **Kualifikasi Rank (V1 - V8)**: Didasarkan pada akumulasi omzet staking tim jaringan.
  * **Node Vault Pass**: Membeli Node Vault ($500 / $1.000) memotong syarat omzet dan langsung memberikan kualifikasi Rank V4 atau V5.
- **Penarikan (Withdrawal / WD)**: Minimal WD 10 USDT. Fee: Instant (10%), >15 Hari (5%), >30 Hari (3%).
- **Tokenomics**: Total Supply 1 Miliar Token BEP-20 (BNB Chain), Initial Listing DEX Price $0.01 USD.
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_official_buttons():
    keyboard = [[InlineKeyboardButton("🚀 Register / Join FIYYA", url=REFERRAL_LINK)]]
    return InlineKeyboardMarkup(keyboard)

def clean_markdown(text):
    return re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', text)

# 3. HANDLER KHUSUS MEMBER BARU JOIN GRUP (DUKUNGAN 14 BAHASA)
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
            
        first_name = member.first_name
        lang = (member.language_code or "").lower()

        # 1. INDONESIA (id)
        if lang.startswith("id"):
            welcome_text = (
                f"Selamat datang di Komunitas Resmi FIYYA, {first_name}! 👋🚀\n\n"
                "Saya adalah Asisten AI FIYYA. Silakan tanyakan apa saja seputar Arbitrase HFT, Staking Vault, Node Vault, maupun Program Market & Strategic Plan V1-V8 langsung di grup ini."
            )
        # 2. MELAYU (ms)
        elif lang.startswith("ms"):
            welcome_text = (
                f"Selamat datang ke Komuniti Rasmi FIYYA, {first_name}! 👋🚀\n\n"
                "Saya ialah Pembantu AI FIYYA. Sila tanya apa sahaja mengenai Arbitraj HFT, Staking Vault, Node Vault, atau Pelan Pasaran & Strategik V1-V8 terus di dalam kumpulan ini."
            )
        # 3. JEPANG / JAPANESE (ja)
        elif lang.startswith("ja"):
            welcome_text = (
                f"FIYYA公式コミュニティへようこそ、{first_name}さん！ 👋🚀\n\n"
                "私はFIYYA AIアシスタントです。HFTアービトラージ、ステーキングヴォルト、ノードヴォルト、マーケット＆戦略プランV1-V8について、このグループでお気軽にご質問ください。"
            )
        # 4. KOREA / KOREANESE (ko)
        elif lang.startswith("ko"):
            welcome_text = (
                f"FIYYA 공식 커뮤니티에 오신 것을 환영합니다, {first_name}님! 👋🚀\n\n"
                "저는 FIYYA AI 어시스턴트입니다. HFT 차익거래, 스테이킹 볼트, 노드 볼트, 마켓 및 전략 플랜 V1-V8에 대해 궁금한 점이 있으시면 이 그룹에서 언제든지 질문해 주세요."
            )
        # 5. CINA / CHINESE (zh)
        elif lang.startswith("zh"):
            welcome_text = (
                f"欢迎来到 FIYYA 官方社区，{first_name}！ 👋🚀\n\n"
                "我是 FIYYA AI 助手。欢迎在本群组中随时咨询有关 HFT 套利、质押金库 (Staking Vault)、节点金库 (Node Vault) 以及市场与战略计划 V1-V8 的任何问题。"
            )
        # 6. RUSIA / RUSSIAN (ru)
        elif lang.startswith("ru"):
            welcome_text = (
                f"Добро пожаловать в официальное сообщество FIYYA, {first_name}! 👋🚀\n\n"
                "Я — ИИ-ассистент FIYYA. Задавайте любые вопросы об арбитраже HFT, Staking Vault, Node Vault, а также о рыночном и стратегическом плане V1-V8 прямо в этой группе."
            )
        # 7. PORTUGIS / PORTUGUESE (pt)
        elif lang.startswith("pt"):
            welcome_text = (
                f"Bem-vindo à Comunidade Oficial da FIYYA, {first_name}! 👋🚀\n\n"
                "Eu sou o Assistente de IA da FIYYA. Sinta-se à vontade para perguntar qualquer coisa sobre Arbitragem HFT, Staking Vault, Node Vault ou o Plano Estratégico e de Mercado V1-V8 diretamente neste grupo."
            )
        # 8. HINDI (hi)
        elif lang.startswith("hi"):
            welcome_text = (
                f"FIYYA आधिकारिक समुदाय में आपका स्वागत है, {first_name}! 👋🚀\n\n"
                "मैं FIYYA AI सहायक हूँ। इस समूह में HFT आर्बिट्राज, स्टेकिंग वॉल्ट, नोड वॉल्ट, या मार्केट और रणनीतिक योजना V1-V8 के बारे में बेझिझक कुछ भी पूछें।"
            )
        # 9. THAILAND / THAI (th)
        elif lang.startswith("th"):
            welcome_text = (
                f"ยินดีต้อนรับสู่ชุมชนอย่างเป็นทางการของ FIYYA, {first_name}! 👋🚀\n\n"
                "ฉันคือผู้ช่วย AI ของ FIYYA สอบถามเกี่ยวกับ HFT Arbitrage, Staking Vault, Node Vault หรือแผนการตลาดและกลยุทธ์ V1-V8 ได้โดยตรงในกลุ่มนี้"
            )
        # 10. VIETNAM / VIETNAMESE (vi)
        elif lang.startswith("vi"):
            welcome_text = (
                f"Chào mừng bạn đến với Cộng đồng Chính thức của FIYYA, {first_name}! 👋🚀\n\n"
                "Tôi là Trợ lý AI của FIYYA. Hãy thoải mái hỏi bất kỳ điều gì về Chênh lệch giá HFT, Staking Vault, Node Vault hoặc Kế hoạch Chiến lược & Thị trường V1-V8 ngay trong nhóm này."
            )
        # 11. TAGALOG / FILIPINO (tl / fil)
        elif lang.startswith("tl") or lang.startswith("fil"):
            welcome_text = (
                f"Maligayang pagdating sa Opisyal na Komunidad ng FIYYA, {first_name}! 👋🚀\n\n"
                "Ako ang FIYYA AI Assistant. Huwag mag-atubiling magtanong tungkol sa HFT Arbitrage, Staking Vault, Node Vault, o ang Market & Strategic Plan V1-V8 nang direkta sa grupong ito."
            )
        # 12. ARABIC (ar)
        elif lang.startswith("ar"):
            welcome_text = (
                f"مرحبًا بك في مجتمع FIYYA الرسمي، {first_name}! 👋🚀\n\n"
                "أنا مساعد الذكاء الاصطناعي لـ FIYYA. لا تتردد في السؤال عن أي شيء يتعلق بالتحكيم HFT، أو Staking Vault، أو Node Vault، أو خطة السوق والاستراتيجية V1-V8 مباشرة في هذه المجموعة."
            )
        # 13. PRANCIS / FRENCH (fr)
        elif lang.startswith("fr"):
            welcome_text = (
                f"Bienvenue dans la communauté officielle de FIYYA, {first_name} ! 👋🚀\n\n"
                "Je suis l'assistant IA de FIYYA. N'hésitez pas à poser vos questions sur l'arbitrage HFT, le Staking Vault, le Node Vault ou le plan stratégique et de marché V1-V8 directement dans ce groupe."
            )
        # 14. INGGRIS / ENGLISH & LAINNYA (en / Global Default)
        else:
            welcome_text = (
                f"Welcome to the Official FIYYA Community, {first_name}! 👋🚀\n\n"
                "I am the FIYYA AI Assistant. Feel free to ask anything about HFT Arbitrage, Staking Vaults, Node Vaults, or the Market & Strategic Plan V1-V8 directly in this group."
            )

        await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_conversations[chat_id] = []
    
    welcome_text = (
        "Halo! Selamat datang di FIYYA Official AI Assistant. 👋\n\n"
        "Saya adalah asisten virtual resmi untuk platform FIYYA.\n"
        "Ada yang bisa saya bantu terkait teknologi arbitrase, Dual Vault, minimal deposit, reward, plan, whitepaper, atau penarikan?"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    raw_text = update.message.text
    t = re.sub(r'[^a-zA-Z0-9\s]', ' ', raw_text.lower()).strip()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # 1. PRIO UTAMA INSTAN: JIKA MINTA WHITEPAPER / PDF
    if any(k in t for k in ["whitepaper", "paper", "pdf", "dokumen", "dokumem"]):
        caption_text = (
            "Dokumen Resmi FIYYA (Whitepaper V.01.0.3):\n\n"
            "Berikut adalah dokumen resmi Whitepaper FIYYA yang memuat rincian arsitektur HFT berbasis Agentic OS AI, skema Dual Vault, Career Matrix (V1-V8), hingga spesifikasi Tokenomics BEP-20."
        )
        try:
            await context.bot.send_document(
                chat_id=chat_id,
                document=WHITEPAPER_FILE_ID,
                caption=caption_text,
                reply_markup=get_official_buttons()
            )
            return
        except Exception as e:
            logging.error(f"Gagal kirim PDF: {e}")

    # 2. PRIO KEDUA INSTAN: SAPAAN BIASA
    is_greeting = any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in ["sore", "pagi", "siang", "malam", "halo", "hi", "hai", "helo", "apa kabar", "assalamualaikum"])
    is_query = any(k in t for k in ["jaring", "node", "plan", "reward", "wd", "deposit", "fiyya", "vault", "bunga", "profit", "sistem", "cara"])
    
    if is_greeting and not is_query:
        if "pagi" in t: sapaan = "Selamat pagi!"
        elif "siang" in t: sapaan = "Selamat siang!"
        elif "malam" in t: sapaan = "Selamat malam!"
        else: sapaan = "Selamat sore!"

        bot_reply = f"Halo, {sapaan} 👋 Selamat datang di FIYYA Official AI Assistant. Ada yang bisa saya bantu terkait platform FIYYA, deposit, plan, atau reward jaringan hari ini?"
        user_conversations.setdefault(chat_id, []).append({"role": "user", "content": raw_text})
        user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
        return

    # 3. PROSES API OPENROUTER JIKA BUKAN DOKUMEN / SAPAAN MURNI
    if chat_id not in user_conversations:
        user_conversations[chat_id] = []

    user_conversations[chat_id].append({"role": "user", "content": raw_text})
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

    # 4. FALLBACK JIKA ALL API OVERLOAD
    if not bot_reply:
        if any(k in t for k in ["jaring", "referral", "refrensi", "matrix", "career", "v1", "v8", "matching", "downline", "kembang"]):
            bot_reply = (
                "Rincian Bonus & Program Pengembangan Jaringan FIYYA (Career Matrix V1 - V8):\n\n"
                "1. **Daily Matching Bonus**: Bonus persentase harian dari profit pasif tim downline Anda.\n"
                "2. **Peningkatan Payout Cap (200% - 350%)**: Batas maksimal total pendapatan Anda naik seiring kenaikan rank.\n"
                "3. **Kualifikasi Rank (V1-V8)**: Dicapai berdasarkan akumulasi total omzet Staking Vault tim jaringan Anda.\n"
                "4. **Node Vault Pass ($500 / $1.000 USDT)**: Akselerasi kualifikasi instan ke Rank V4/V5."
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
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
