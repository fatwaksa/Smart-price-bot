import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, GROQ_API_KEY
from scraper import scrape_prices
from scoring import score_offer
from ai_engine import analyze
from functools import lru_cache
import time

# ==============================
# رسائل ترحيب محسنة
# ==============================
WELCOME_MESSAGE = """
👋 أهلاً بك {user} في منصة عزو لتحليل السوق!

ضع اسم المنتج أو الخدمة التي تريد البحث عنها، وسأوفر لك أفضل الأسعار الموثوقة والمناسبة.

💡 يمكنك الاعتماد علينا لتحليل سريع ودقيق، ومقارنة الأسعار بين المتاجر العالمية والمحلية.

تابعنا على حساباتنا:
@YourTwitter
@YourInstagram
"""

# ==============================
# Caching للعروض لتسريع البوت
# ==============================
@lru_cache(maxsize=128)
def cached_scrape(product: str):
    return scrape_prices(product)

# ==============================
# أمر البداية
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(WELCOME_MESSAGE.format(user=user_name))

# ==============================
# التعامل مع أي رسالة
# ==============================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = update.message.text.strip()
    user_name = update.effective_user.first_name or "صديقي"

    await update.message.reply_text(f"🔍 {user_name}، جاري تحليل السوق للمنتج: {product} ...")

    loop = asyncio.get_event_loop()

    # 1️⃣ جلب العروض بشكل async مع timeout
    try:
        offers = await asyncio.wait_for(loop.run_in_executor(None, cached_scrape, product), timeout=15)
    except asyncio.TimeoutError:
        await update.message.reply_text("⚠️ عذرًا، استغرق تحليل السوق وقتًا طويلاً. حاول مرة أخرى.")
        return

    if not offers:
        await update.message.reply_text("⚠️ لم يتم العثور على أي عروض لهذا المنتج.")
        return

    # 2️⃣ حساب الدرجات لكل عرض بشكل async
    await update.message.reply_text(f"📝 تقييم {len(offers)} عرضًا ...")
    scored = await asyncio.gather(*[loop.run_in_executor(None, score_offer, o) for o in offers])
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    # 3️⃣ تحليل Groq AI للعروض الثلاثة الأفضل
    await update.message.reply_text("🤖 تحليل الذكاء الاصطناعي للعروض الأفضل ...")
    try:
        ai_reply = await asyncio.wait_for(loop.run_in_executor(None, analyze, product, scored[:3]), timeout=10)
    except asyncio.TimeoutError:
        ai_reply = "⚠️ حدثت مشكلة أثناء تحليل الذكاء الاصطناعي. يمكن تجربة إعادة البحث."

    # 4️⃣ إرسال الرد النهائي
    await update.message.reply_text(ai_reply)

# ==============================
# تشغيل البوت
# ==============================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
