import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import TelegramError

from config import TELEGRAM_TOKEN, GROQ_API_KEY
from scraper import scrape_prices
from scoring import score_offer
from ai_engine import analyze

# رسالة ترحيب مميزة
WELCOME_MESSAGE = """
👋 أهلاً بك #user في منصة عزو لتحليل السوق!

ضع اسم المنتج الذي تريد البحث عنه، وسأساعدك باختيار أفضل عرض موثوق وبأفضل سعر ممكن.

💡 حساباتنا على التواصل الاجتماعي:
@social1
@social2
"""

MAX_OFFERS = 20  # أقصى عدد عروض للمعالجة

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(WELCOME_MESSAGE.replace("#user", user_name))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = update.message.text.strip()
    user_name = update.effective_user.first_name or "صديقي"

    msg = await update.message.reply_text(f"🔍 {user_name}، جاري تحليل السوق للمنتج: {product} ...")

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 1️⃣ جلب العروض
        try:
            offers = await asyncio.wait_for(loop.run_in_executor(executor, scrape_prices, product), timeout=15)
            offers = offers[:MAX_OFFERS]
        except asyncio.TimeoutError:
            await safe_edit_text(msg, "⚠️ عذرًا، استغرق تحليل السوق وقتًا طويلاً. حاول مرة أخرى.")
            return
        except Exception as e:
            await safe_edit_text(msg, f"⚠️ خطأ أثناء جلب العروض: {str(e)}")
            return

        if not offers:
            await safe_edit_text(msg, "⚠️ لم يتم العثور على أي عروض لهذا المنتج.")
            return

        # 2️⃣ تقييم العروض
        await safe_edit_text(msg, f"📝 جاري تقييم {len(offers)} عرض ...")
        scored = []

        tasks = [loop.run_in_executor(executor, score_offer, o) for o in offers]

        for idx, task in enumerate(asyncio.as_completed(tasks)):
            try:
                s = await asyncio.wait_for(task, timeout=5.0)
                # تأكد من شكل dict الصحيح
                if not isinstance(s, dict) or "score" not in s or "offer" not in s:
                    s = {"score": s if isinstance(s, (int, float)) else 0, "offer": offers[idx]}
            except Exception:
                s = {"score": 0, "offer": offers[idx]}
            scored.append(s)
            if idx % 5 == 0 or idx == len(offers) - 1:
                await safe_edit_text(msg, f"📝 تقييم {idx+1}/{len(offers)} عرض ...")

        scored = sorted(scored, key=lambda x: x.get("score", 0), reverse=True)

        # 3️⃣ تحليل AI للعروض الثلاثة الأعلى
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
    try:
        await msg.edit_text(text)
    except TelegramError as e:
        if "Message is not modified" in str(e):
            pass
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
