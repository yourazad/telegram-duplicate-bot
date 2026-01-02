from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import os

TOKEN = os.getenv("TOKEN")

# per-group storage
seen_media = {}          # {chat_id: set(file_unique_id)}
text_count = {}          # {chat_id: int}
media_count = {}         # {chat_id: int}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = msg.chat_id

    # init group data
    seen_media.setdefault(chat_id, set())
    text_count.setdefault(chat_id, 0)
    media_count.setdefault(chat_id, 0)

    # ❌ TEXT → DELETE
    if msg.text:
        try:
            await msg.delete()
            text_count[chat_id] += 1
        except:
            pass
        return

    # ✅ MEDIA
    media_id = None

    if msg.photo:
        media_id = msg.photo[-1].file_unique_id
    elif msg.video:
        media_id = msg.video.file_unique_id
    elif msg.document:
        media_id = msg.document.file_unique_id
    elif msg.audio:
        media_id = msg.audio.file_unique_id
    else:
        return

    # ❌ DUPLICATE MEDIA → DELETE
    if media_id in seen_media[chat_id]:
        try:
            await msg.delete()
            media_count[chat_id] += 1
        except:
            pass
    else:
        seen_media[chat_id].add(media_id)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    t = text_count.get(chat_id, 0)
    m = media_count.get(chat_id, 0)

    await update.message.reply_text(
        f"📊 Group Delete Report\n\n"
        f"✍️ Text deleted: {t}\n"
        f"📁 Duplicate media deleted: {m}"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("report", report))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
