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

seen_media = set()
deleted_count = 0

# 👇 bot ke resend ko protect karne ke liye
bot_resending = set()


def media_hash(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deleted_count
    msg = update.message
    if not msg:
        return

    # ✅ allowed media
    allowed = msg.photo or msg.video or msg.animation

    # ❌ delete non-media
    if not allowed:
        try:
            await msg.delete()
        except:
            pass
        return

    # 🔍 file_id
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    elif msg.animation:
        file_id = msg.animation.file_id
    else:
        return

    h = media_hash(file_id)

    # ❌ duplicate delete (but NOT bot resend)
    if h in seen_media and h not in bot_resending:
        try:
            await msg.delete()
            deleted_count += 1
        except:
            pass
        return

    # first time seen
    seen_media.add(h)

    # 🎯 BLANK THUMB FIX
    if msg.video and not msg.video.thumbs:
        try:
            # mark resend protection
            bot_resending.add(h)

            # resend with Telegram processing (thumbnail auto)
            await context.bot.send_video(
                chat_id=msg.chat_id,
                video=msg.video.file_id,
                caption=msg.caption,
                supports_streaming=True
            )

            # delete original blank-thumb video
            await msg.delete()

            # cleanup flag
            bot_resending.discard(h)

        except Exception as e:
            print("Thumbnail resend error:", e)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Duplicate Media Remover Bot Active\n\n"
        "✅ Photo | Video | GIF allowed\n"
        "❌ Text | Audio | Sticker deleted\n"
        "🗑 Duplicate media auto delete\n"
        "🖼 Blank thumbnail auto-fix\n\n"
        "📊 /report"
    )


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Duplicate Media Report\n\n"
        f"🗑 Total duplicate media deleted: {deleted_count}"
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()
