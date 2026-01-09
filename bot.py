import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from config import TELEGRAM_TOKEN, GROQ_API_KEY  # تأكد من وضعهم كـ Environment Variables
from scraper import scrape_prices  # Scraper مختصر فقط (name, price, link, rating)
from scoring import score_offer
from ai_engine import analyze  # تحليل AI مختصر للعروض الأفضل

# رسالة ترحيب مميزة
WELCOME_MESSAGE = """
👋 أهلاً بك #user في منصة عزو لتحليل السوق!

ضع اسم المنتج الذي تريد البحث عنه، وسأساعدك باختيار أفضل عرض موثوق وبأفضل سعر ممكن.

💡 حساباتنا على التواصل الاجتماعي:
@social1
@social2
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(WELCOME_MESSAGE.replace("#user", user_name))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = update.message.text.strip()
    user_name = update.effective_user.first_name or "صديقي"

    # رسالة أولية
    msg = await update.message.reply_text(f"🔍 {user_name}، جاري تحليل السوق للمنتج: {product} ...")

    loop = asyncio.get_event_loop()

    # 1️⃣ جلب العروض بشكل مختصر (Async + Timeout)
    try:
        offers = await asyncio.wait_for(loop.run_in_executor(None, scrape_prices, product), timeout=15)
    except asyncio.TimeoutError:
        await msg.edit_text("⚠️ عذرًا، استغرق تحليل السوق وقتًا طويلاً. حاول مرة أخرى.")
        return

    if not offers:
        await msg.edit_text("⚠️ لم يتم العثور على أي عروض لهذا المنتج.")
        return

    # 2️⃣ تقييم العروض تدريجيًا
    scored = []
    for idx, o in enumerate(offers):
        try:
            s = await loop.run_in_executor(None, score_offer, o)
        except Exception as e:
            s = {"score": 0, "offer": o}
        scored.append(s)
        await msg.edit_text(f"📝 تقييم {idx+1}/{len(offers)} عرض ...")

    # ترتيب العروض حسب الدرجة
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    # 3️⃣ تحليل الذكاء الاصطناعي للعروض الثلاثة الأولى
    await msg.edit_text("🤖 تحليل الذكاء الاصطناعي للعروض الأفضل ...")
    try:
        ai_reply = await asyncio.wait_for(loop.run_in_executor(None, analyze, product, scored[:3]), timeout=10)
    except asyncio.TimeoutError:
        ai_reply = "⚠️ حدثت مشكلة أثناء تحليل الذكاء الاصطناعي. يرجى إعادة المحاولة."
    except Exception as e:
        ai_reply = f"⚠️ خطأ أثناء تحليل AI: {str(e)}"

    # 4️⃣ عرض النتيجة النهائية
    await msg.edit_text(ai_reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
