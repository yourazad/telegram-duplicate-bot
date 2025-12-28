from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import hashlib
import os

# TOKEN from Railway / Environment Variable
TOKEN = os.getenv("TOKEN")

# storage
seen_messages = {}
deleted_messages = []

def get_hash(message):
    if message.text:
        return hashlib.md5(message.text.encode()).hexdigest()

    if message.photo:
        return message.photo[-1].file_unique_id

    if message.video:
        return message.video.file_unique_id

    if message.document:
        return message.document.file_unique_id

    if message.audio:
        return message.audio.file_unique_id

    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    msg_hash = get_hash(update.message)

    if not msg_hash:
        return

    if chat_id not in seen_messages:
        seen_messages[chat_id] = set()

    if msg_hash in seen_messages[chat_id]:
        try:
            await update.message.delete()
            deleted_messages.append(
                update.message.text
                or update.message.caption
                or "Media/File"
            )
        except:
            pass
    else:
        seen_messages[chat_id].add(msg_hash)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not deleted_messages:
        await update.message.reply_text(
            "✅ Koi duplicate message delete nahi hua."
        )
        return

    msg = "📊 Duplicate Delete Report\n\n"
    msg += f"🗑 Total Deleted: {len(deleted_messages)}\n\n"
    msg += "📌 Deleted Messages:\n"

    for i, text in enumerate(deleted_messages, 1):
        msg += f"{i}. {text}\n"

    await update.message.reply_text(msg)

    # reset after report
    deleted_messages.clear()
    seen_messages.clear()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Duplicate Cleaner Bot Active!\n\n"
        "• Text / Photo / Video / File duplicate auto delete honge\n"
        "• Final report ke liye /report likho"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
