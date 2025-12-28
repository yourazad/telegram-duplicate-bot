from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import hashlib

TOKEN = "YOUR_BOT_TOKEN_HERE"

# storage
seen_messages = {}
deleted_messages = []

def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    text = update.message.text
    msg_hash = get_hash(text)

    if chat_id not in seen_messages:
        seen_messages[chat_id] = set()

    if msg_hash in seen_messages[chat_id]:
        try:
            await update.message.delete()
            deleted_messages.append(text)
        except:
            pass
    else:
        seen_messages[chat_id].add(msg_hash)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not deleted_messages:
        await update.message.reply_text("✅ Koi duplicate message delete nahi hua.")
        return

    msg = f"🧹 Duplicate Delete Report\n\n"
    msg += f"🔢 Total Deleted: {len(deleted_messages)}\n\n"
    msg += "🗑 Deleted Messages:\n"

    for i, text in enumerate(deleted_messages, 1):
        msg += f"{i}. {text}\n"

    await update.message.reply_text(msg)

    # reset after report
    deleted_messages.clear()
    seen_messages.clear()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Duplicate Cleaner Bot Active!\n\n"
        "• Duplicate messages auto delete honge\n"
        "• /report likho final count dekhne ke liye"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
