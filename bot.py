import os
import hashlib
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")

# storage
seen_media = set()
deleted_count = 0


def media_hash(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deleted_count
    msg = update.message

    if not msg:
        return

    # ✅ ALLOWED: photo, video, gif(animation)
    allowed = msg.photo or msg.video or msg.animation

    # ❌ DELETE everything else
    if not allowed:
        try:
            await msg.delete()
        except:
            pass
        return

    # 🔍 find file_id
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    elif msg.animation:
        file_id = msg.animation.file_id

    if not file_id:
        return

    h = media_hash(file_id)

    # ❌ duplicate media delete
    if h in seen_media:
        try:
            await msg.delete()
            deleted_count += 1
        except:
            pass
    else:
        seen_media.add(h)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Duplicate Media Report\n\n"
        f"🗑 Total duplicate media deleted: {deleted_count}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Media Filter Bot Active\n\n"
        "✅ Allowed: Photo | Video | GIF\n"
        "❌ Deleted: Text, Music, Sticker, Emoji, File\n"
        "🗑 Duplicate media auto delete\n\n"
        "📊 /report for deleted count"
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()
