from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from config import TELEGRAM_TOKEN
from scraper import scrape_prices
from scoring import score_offer
from ai_engine import analyze

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أرسل اسم المنتج، وسأساعدك باختيار أفضل عرض موثوق."
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = update.message.text
    await update.message.reply_text("🔍 جاري تحليل السوق...")

    offers = scrape_prices(product)
    scored = [score_offer(o) for o in offers]
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    ai_reply = analyze(product, scored[:3])

    await update.message.reply_text(ai_reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
