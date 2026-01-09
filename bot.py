import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import TelegramError

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

# عدد العروض القصوى للمعالجة لتجنب الإفراط
MAX_OFFERS = 20

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(WELCOME_MESSAGE.replace("#user", user_name))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = update.message.text.strip()
    user_name = update.effective_user.first_name or "صديقي"

    # رسالة أولية
    msg = await update.message.reply_text(f"🔍 {user_name}، جاري تحليل السوق للمنتج: {product} ...")

    # استخدام ThreadPoolExecutor للعمليات الحظرية
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_running_loop()

        # 1️⃣ جلب العروض بشكل مختصر (Async + Timeout)
        try:
            future = loop.run_in_executor(executor, scrape_prices, product)
            offers = await asyncio.wait_for(future, timeout=15.0)
            offers = offers[:MAX_OFFERS]  # حد العروض لتجنب التأخير
        except asyncio.TimeoutError:
            await safe_edit_text(msg, "⚠️ عذرًا، استغرق تحليل السوق وقتًا طويلاً. حاول مرة أخرى.")
            return
        except Exception as e:
            await safe_edit_text(msg, f"⚠️ خطأ أثناء جلب العروض: {str(e)}")
            return

        if not offers:
            await safe_edit_text(msg, "⚠️ لم يتم العثور على أي عروض لهذا المنتج.")
            return

        # 2️⃣ تقييم العروض بشكل متوازي مع تحديث التقدم
        await safe_edit_text(msg, f"📝 جاري تقييم {len(offers)} عرض ...")
        scored = []
        tasks = []

        for o in offers:
            tasks.append(loop.run_in_executor(executor, score_offer, o))

        for idx, task in enumerate(asyncio.as_completed(tasks)):
            try:
                s = await asyncio.wait_for(task, timeout=5.0)  # timeout لكل تقييم
            except asyncio.TimeoutError:
                s = {"score": 0, "offer": offers[idx]}
            except Exception as e:
                s = {"score": 0, "offer": offers[idx]}
            scored.append(s)
            if idx % 5 == 0 or idx == len(offers) - 1:  # تحديث كل 5 أو في النهاية لتجنب rate limit
                await safe_edit_text(msg, f"📝 تقييم {idx+1}/{len(offers)} عرض ...")

        # ترتيب العروض حسب الدرجة
        scored = sorted(scored, key=lambda x: x.get("score", 0), reverse=True)

        # 3️⃣ تحليل الذكاء الاصطناعي للعروض الثلاثة الأولى
        await safe_edit_text(msg, "🤖 تحليل الذكاء الاصطناعي للعروض الأفضل ...")
        try:
            future = loop.run_in_executor(executor, analyze, product, scored[:3])
            ai_reply = await asyncio.wait_for(future, timeout=10.0)
        except asyncio.TimeoutError:
            ai_reply = "⚠️ حدثت مشكلة أثناء تحليل الذكاء الاصطناعي. يرجى إعادة المحاولة."
        except Exception as e:
            ai_reply = f"⚠️ خطأ أثناء تحليل AI: {str(e)}"

        # 4️⃣ عرض النتيجة النهائية
        await safe_edit_text(msg, ai_reply)

async def safe_edit_text(msg, text):
    """تحرير الرسالة بأمان مع التعامل مع الأخطاء"""
    try:
        await msg.edit_text(text)
    except TelegramError as e:
        if "Message is not modified" in str(e):
            pass  # تجاهل إذا لم يتغير النص
        else:
            print(f"Error editing message: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
