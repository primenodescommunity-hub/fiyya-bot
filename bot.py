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

# ==========================================
# 1. DUMMY WEB SERVER UNTUK RENDER PORT 10000
# ==========================================
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "FIYYA Official AI Bot Enterprise Engine Online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)


# ==========================================
# 2. KONFIGURASI BOT & FILE ID DOKUMEN RESMI
# ==========================================
TELEGRAM_TOKEN = "8850888324:AAF5aeXUKJ2jfxTR_Z70RwD4EaTj2PYeiio"
REFERRAL_LINK = "https://www.fiyya.co/signup?ref=66796114"
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


# ==========================================
# 3. KNOWLEDGE BASE & SYSTEM PROMPT (ENGLISH PRIMARY)
# ==========================================
SYSTEM_PROMPT = f"""
PRIMARY LANGUAGE INSTRUCTION:
Your primary language of communication is ENGLISH. 
Always communicate in high-quality, professional, and friendly English by default. 
However, if a user explicitly initiates or asks a question in another language (e.g., Portuguese, Indonesian, Japanese, Chinese, Spanish, French, etc.), match and reply STRICTLY in the user's language.

ROLE & IDENTITY:
You are the Official AI Assistant for the FIYYA platform ({REFERRAL_LINK}).
Be polite, articulate, professional, and natural. Understand user intent regardless of slang, abbreviations, or informal language (e.g., "min depo", "dp brp", "how much min deposit", "what is fiyya").

CORE BEHAVIOR RULES:
1. GREETING: Always greet users warmly first when they greet you.
2. REGISTRATION: Guide users to click the '🚀 Register / Join FIYYA' button when they inquire about joining, registering, or creating an account.
3. WHITEPAPER: When asked about whitepapers, official documents, or PDFs, summarize the contents (HFT Agentic OS, Dual Vault, Career Matrix, Tokenomics) and inform them that the official PDF document is attached.
4. STRICT RESTRICTIONS: STRICTLY FORBIDDEN to discuss religion, sharia finance, or non-FIYYA topics.Politely decline and redirect back to FIYYA ecosystem topics.

OFFICIAL FIYYA KNOWLEDGE BASE:
- **FIYYA Definition**: An institutional High-Frequency Trading (HFT) arbitrage platform driven by Agentic OS AI, connected via WebSocket to major global exchanges (Binance, OKX, Coinbase, Kraken).
- **Target Yield & Profit Split**: Target Daily Yield of 1.5% per day (Profit Split: 60% liquid USDT withdrawable anytime + 40% FIYYA Tokens with 100-day daily vesting).
- **Contract Duration & Payout Cap**: Combined Lifetime Payout Cap between 200% and 350% of original deposit. Contract completes upon reaching the Payout Cap, followed by optional re-stake / top-up.
- **Dual Vault System**:
  * Staking Vault: Modal entry from $100 to $10,000 USDT for daily passive yield.
  * Node Vault ($500 / $1,000 USDT): Instant rank acceleration pass to Rank V4 or V5 without requiring massive initial network volume.
- **Network Development & Career Matrix (V1 - V8)**: Daily Matching Bonus from downline passive profits, Payout Cap expansion up to 350%, and rank rank advancements.
- **Withdrawal**: Minimum withdrawal is 10 USDT. Fee structure: Instant (10%), >15 Days (5%), >30 Days (3%).
- **Tokenomics**: Total supply of 1 Billion BEP-20 Tokens (BNB Chain), Initial DEX Listing Price at $0.01 USD.
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_official_buttons():
    keyboard = [[InlineKeyboardButton("🚀 Register / Join FIYYA", url=REFERRAL_LINK)]]
    return InlineKeyboardMarkup(keyboard)

def clean_markdown(text):
    return re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', text)


# ==========================================
# 4. HANDLER MEMBER BARU GRUP (14 BAHASA)
# ==========================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
            
        first_name = member.first_name
        lang = (member.language_code or "").lower()

        # DEFAULT TO ENGLISH IF NOT SPECIFIED
        if lang.startswith("id"):
            welcome_text = f"Selamat datang di Komunitas Resmi FIYYA, {first_name}! 👋🚀\n\nSaya adalah Asisten AI FIYYA. Silakan tanyakan apa saja seputar Arbitrase HFT, Staking Vault, Node Vault, maupun Program Market & Strategic Plan V1-V8 langsung di grup ini."
        elif lang.startswith("ms"):
            welcome_text = f"Selamat datang ke Komuniti Rasmi FIYYA, {first_name}! 👋🚀\n\nSaya ialah Pembantu AI FIYYA. Sila tanya apa sahaja mengenai Arbitraj HFT, Staking Vault, Node Vault, atau Pelan Pasaran & Strategik V1-V8 terus di dalam kumpulan ini."
        elif lang.startswith("ja"):
            welcome_text = f"FIYYA公式コミュニティへようこそ、{first_name}さん！ 👋🚀\n\n私はFIYYA AIアシスタントです。HFTアービトラージ、ステーキングヴォルト、ノードヴォルト、マーケット＆戦略プランV1-V8について、このグループでお気軽にご質問ください。"
        elif lang.startswith("ko"):
            welcome_text = f"FIYYA 공식 커뮤니티에 오신 것을 환영합니다, {first_name}님! 👋🚀\n\n저는 FIYYA AI 어시스턴트입니다. HFT 차익거래, 스테이킹 볼트, 노드 볼트, 마켓 및 전략 플랜 V1-V8에 대해 궁금한 점이 있으시면 이 그룹에서 언제든지 질문해 주세요."
        elif lang.startswith("zh"):
            welcome_text = f"欢迎来到 FIYYA 官方社区，{first_name}！ 👋🚀\n\n我是 FIYYA AI 助手。欢迎在本群组中随时咨询有关 HFT 套利、质押金库 (Staking Vault)、节点金库 (Node Vault) 以及市场与战略计划 V1-V8 的任何问题。"
        elif lang.startswith("ru"):
            welcome_text = f"Добро пожаловать в официальное сообщество FIYYA, {first_name}! 👋🚀\n\nЯ — ИИ-ассистент FIYYA. Задавайте любые вопросы об арбитраже HFT, Staking Vault, Node Vault, а также о рыночном и стратегическом плане V1-V8 прямо в этой группе."
        elif lang.startswith("pt"):
            welcome_text = f"Bem-vindo à Comunidade Oficial da FIYYA, {first_name}! 👋🚀\n\nEu sou o Assistente de IA da FIYYA. Sinta-se à vontade para perguntar qualquer coisa sobre Arbitragem HFT, Staking Vault, Node Vault ou o Plano Estratégico e de Mercado V1-V8 diretamente neste grupo."
        elif lang.startswith("hi"):
            welcome_text = f"FIYYA आधिकारिक समुदाय में आपका स्वागत है, {first_name}! 👋🚀\n\nमैं FIYYA AI सहायक हूँ। इस समूह में HFT आर्बिट्राज, स्टेकिंग वॉल्ट, नोड वॉल्ट, या मार्केट और रणनीतिक योजना V1-V8 के बारे में बेझिझक कुछ भी पूछें।"
        elif lang.startswith("th"):
            welcome_text = f"ยินดีต้อนรับสู่ชุมชนอย่างเป็นทางการของ FIYYA, {first_name}! 👋🚀\n\nฉันคือผู้ช่วย AI ของ FIYYA สอบถามเกี่ยวกับ HFT Arbitrage, Staking Vault, Node Vault หรือแผนการตลาดและกลยุทธ์ V1-V8 ได้โดยตรงในกลุ่มนี้"
        elif lang.startswith("vi"):
            welcome_text = f"Chào mừng bạn đến với Cộng đồng Chính thức của FIYYA, {first_name}! 👋🚀\n\nTôi là Trợ lý AI của FIYYA. Hãy thoải mái hỏi bất kỳ điều gì về Chênh lệch giá HFT, Staking Vault, Node Vault hoặc Kế hoạch Chiến lược & Thị trường V1-V8 ngay trong nhóm này."
        elif lang.startswith("tl") or lang.startswith("fil"):
            welcome_text = f"Maligayang pagdating sa Opisyal na Komunidad ng FIYYA, {first_name}! 👋🚀\n\nAko ang FIYYA AI Assistant. Huwag mag-atubiling magtanong tungkol sa HFT Arbitrage, Staking Vault, Node Vault, o ang Market & Strategic Plan V1-V8 nang direkta sa grupong ito."
        elif lang.startswith("ar"):
            welcome_text = f"مرحبًا بك في مجتمع FIYYA الرسمي، {first_name}! 👋🚀\n\nأنا مساعد الذكاء الاصطناعي لـ FIYYA. لا تتردد في السؤال عن أي شيء يتعلق بالتحكيم HFT، أو Staking Vault، أو Node Vault، أو خطة السوق والاستراتيجية V1-V8 مباشرة في هذه المجموعة."
        elif lang.startswith("fr"):
            welcome_text = f"Bienvenue dans la communauté officielle de FIYYA, {first_name} ! 👋🚀\n\nJe suis l'assistant IA de FIYYA. N'hésitez pas à poser vos questions sur l'arbitrage HFT, le Staking Vault, le Node Vault ou le plan stratégique et de marché V1-V8 directement dans ce groupe."
        else:
            welcome_text = f"Welcome to the Official FIYYA Community, {first_name}! 👋🚀\n\nI am the Official FIYYA AI Assistant. Feel free to ask anything about HFT Arbitrage, Staking Vaults, Node Vaults, or the Market & Strategic Plan V1-V8 directly in this group."

        await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())


# ==========================================
# 5. COMMAND & MESSAGE HANDLER UTAMA
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user_conversations[chat_id] = []
    
    welcome_text = (
        "Welcome to the Official FIYYA AI Assistant! 👋\n\n"
        "I am your official virtual assistant for the FIYYA platform.\n"
        "How can I assist you today regarding HFT Arbitrage, Dual Vaults, minimum deposit, rewards, plans, or whitepaper documentation?"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_official_buttons())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    raw_text = update.message.text
    t = raw_text.lower().strip()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # A. INSTANT INTERCEPT: WHITEPAPER DOCUMENT FILE
    if any(k in t for k in ["whitepaper", "paper", "pdf", "dokumen", "document"]):
        caption_text = (
            "Official FIYYA Whitepaper (V.01.0.3):\n\n"
            "Here is the official FIYYA Whitepaper outlining the Agentic OS AI HFT architecture, Dual Vault mechanism, Career Matrix (V1-V8), and BEP-20 Tokenomics specifications."
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
            logging.error(f"Failed to send PDF: {e}")

    # B. PROCESS VIA OPENROUTER AI ENGINE (ENGLISH PRIMARY)
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
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-7b-instruct:free"
    ]
    
    bot_reply = None
    
    async with httpx.AsyncClient(timeout=12.0) as client_http:
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

    # FALLBACK ADAPTIVE SMART MULTI-LANGUAGE (ENGLISH DEFAULT)
    if not bot_reply:
        # Indonesian Language Check
        if any(k in t for k in ["apa", "berapa", "bagaimana", "depo", "min", "wd", "halo"]):
            bot_reply = f"Halo! FIYYA adalah platform arbitrase High-Frequency Trading (HFT) institusional berbasis Agentic OS AI. Minimal deposit Staking Vault mulai dari $100 USDT.\n\nPendaftaran akun resmi:\n👉 {REFERRAL_LINK}"
        # Portuguese Language Check
        elif any(k in t for k in ["boa", "bom", "obrigado", "quanto", "como", "olá"]):
            bot_reply = f"Olá! FIYYA é uma plataforma institucional de arbitragem HFT baseada em Agentic OS AI. O depósito mínimo no Staking Vault é de $100 USDT.\n\nRegiste-se aqui:\n👉 {REFERRAL_LINK}"
        # Chinese Characters Check
        elif re.search(r'[\u4e00-\u9fff]', raw_text):
            bot_reply = f"您好！FIYYA 是基于 Agentic OS AI 的机构级高频套利 (HFT) 平台。Staking Vault 的最低存款额为 $100 USDT。\n\n注册链接：\n👉 {REFERRAL_LINK}"
        # Japanese Characters Check
        elif re.search(r'[\u3040-\u30ff]', raw_text):
            bot_reply = f"こんにちは！FIYYAはAgentic OS AIをベースとしたHFTアービトラージプラットフォームです。最低預入額は $100 USDT から。\n\n登録はこちら：\n👉 {REFERRAL_LINK}"
        # Default English Fallback
        else:
            bot_reply = f"Hello! FIYYA is an institutional High-Frequency Trading (HFT) arbitrage platform powered by Agentic OS AI. Minimum deposit for Staking Vault starts at $100 USDT (Target daily yield 1.5% per day).\n\nFor official registration, click here:\n👉 {REFERRAL_LINK}"

    # CLEAN TEXT: REMOVE AUTO COMMAND PATTERNS LIKE /hari OR /day
    bot_reply = re.sub(r'/hari', 'per hari', bot_reply, flags=re.IGNORECASE)
    bot_reply = re.sub(r'/day', 'per day', bot_reply, flags=re.IGNORECASE)

    user_conversations[chat_id].append({"role": "assistant", "content": bot_reply})

    try:
        await update.message.reply_text(bot_reply, reply_markup=get_official_buttons())
    except Exception:
        clean_reply = clean_markdown(bot_reply)
        await update.message.reply_text(clean_reply, reply_markup=get_official_buttons())


# ==========================================
# 6. MAIN EXECUTION
# ==========================================
def main():
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot FIYYA AI Enterprise Engine (English Primary) Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
