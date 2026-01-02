from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import os
import hashlib

TOKEN = os.getenv("TOKEN")

# storage
seen_media = set()
text_deleted_count = 0
media_deleted_count = 0


def media_hash(message):
    if message.photo:
        return message.photo[-1].file_unique_id
    if message.video:
        return message.video.file_unique_id
    if message.document:
        return message.document.file_unique_id
    return None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global text_deleted_count
    try:
        await update.message.delete()
        text_deleted_count += 1
    except:
        pass


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global media_deleted_count

    msg = update.message
    media_id = media_hash(msg)

    if not media_id:
        return

    if media_id in seen_media:
        try:
            await msg.delete()
            media_deleted_count += 1
        except:
            pass
    else:
        seen_media.add(media_id)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📊 **Delete Report**\n\n"
        f"🗑 Text deleted: {text_deleted_count}\n"
        f"🖼 Duplicate media deleted: {media_deleted_count}"
    )
    await update.message.reply_text(msg)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Active\n\n"
        "✔ Text auto delete\n"
        "✔ Duplicate media delete\n"
        "📊 /report for count"
    )


app = ApplicationBuilder().token(TOKEN).build()

# delete ONLY text messages (no captions)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# handle media (photo, video, document)
app.add_handler(
    MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL,
        handle_media
    )
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))

app.run_polling()
