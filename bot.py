from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
import os

TOKEN = os.getenv("TOKEN")

# storage
seen_media = set()
deleted_text_count = 0
deleted_media_count = 0


async def cleaner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deleted_text_count, deleted_media_count

    msg = update.message
    if not msg:
        return

    # 🧹 TEXT DELETE (only pure text)
    if msg.text and not msg.photo and not msg.video and not msg.document:
        try:
            await msg.delete()
            deleted_text_count += 1
        except:
            pass
        return

    # 🖼️ MEDIA HANDLING
    file_id = None

    if msg.photo:
        file_id = msg.photo[-1].file_unique_id
    elif msg.video:
        file_id = msg.video.file_unique_id
    elif msg.document:
        file_id = msg.document.file_unique_id

    if file_id:
        if file_id in seen_media:
            try:
                await msg.delete()
                deleted_media_count += 1
            except:
                pass
        else:
            seen_media.add(file_id)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 **Delete Report**\n\n"
        f"🗑️ Text deleted: {deleted_text_count}\n"
        f"🖼️ Duplicate media deleted: {deleted_media_count}",
        parse_mode="Markdown"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Cleaner Bot Active**\n\n"
        "✍️ Text → auto delete\n"
        "🖼️ Duplicate media → auto delete\n"
        "📝 Media captions safe\n\n"
        "📊 Use /report for count",
        parse_mode="Markdown"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            cleaner
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
