from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

group_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot LIVE hai 🤖")

async def duplicate_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = update.effective_chat.id
    group_cache.setdefault(chat_id, set())

    uid = None

    if msg.text:
        uid = f"text:{msg.text}"
    elif msg.photo:
        uid = f"photo:{msg.photo[-1].file_unique_id}"
    elif msg.video:
        uid = f"video:{msg.video.file_unique_id}"
    elif msg.document:
        uid = f"doc:{msg.document.file_unique_id}"

    if not uid:
        return

    if uid in group_cache[chat_id]:
        await msg.delete()
    else:
        group_cache[chat_id].add(uid)

app = ApplicationBuilder().token("8398833039:AAFX4xezoTiU4NYAh9a2R2LfRBnm9Ns6324").build()

# /start command
app.add_handler(CommandHandler("start", start))

# duplicate delete (normal messages)
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, duplicate_delete))

print("Bot running...")
app.run_polling()
