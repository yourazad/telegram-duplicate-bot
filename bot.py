import os
import hashlib
from moviepy.editor import VideoFileClip
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")  # or paste token directly

# ---------------- STORAGE ----------------
seen_media = set()
deleted_count = 0


# ---------------- HASH ----------------
def media_hash(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()


# ---------------- THUMB EXTRACT ----------------
def extract_thumbnail(video_path: str, thumb_path: str):
    clip = VideoFileClip(video_path)
    t = int(clip.duration // 2) if clip.duration and clip.duration > 2 else 1
    clip.save_frame(thumb_path, t=t)
    clip.close()


# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deleted_count
    msg = update.message

    if not msg:
        return

    # ✅ ALLOWED MEDIA
    allowed = msg.photo or msg.video or msg.animation

    # ❌ DELETE NON-MEDIA
    if not allowed:
        try:
            await msg.delete()
        except:
            pass
        return

    # 🔍 FILE ID
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

    # ❌ DUPLICATE DELETE
    if h in seen_media:
        try:
            await msg.delete()
            deleted_count += 1
        except:
            pass
        return
    else:
        seen_media.add(h)

    # 🎯 VIDEO THUMB FIX (ONLY IF MISSING)
    if msg.video and not msg.video.thumbs:
        try:
            video_file = await msg.video.get_file()

            video_path = f"video_{msg.message_id}.mp4"
            thumb_path = f"thumb_{msg.message_id}.jpg"

            await video_file.download_to_drive(video_path)
            extract_thumbnail(video_path, thumb_path)

            # delete original blank-thumb video
            await msg.delete()

            with open(video_path, "rb") as v, open(thumb_path, "rb") as t:
                await context.bot.send_video(
                    chat_id=msg.chat_id,
                    video=v,
                    thumb=t,
                    caption=msg.caption
                )

            os.remove(video_path)
            os.remove(thumb_path)

        except Exception as e:
            print("THUMB ERROR:", e)


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Duplicate Media Remover Bot Active\n\n"
        "✅ Allowed: Photo | Video | GIF\n"
        "❌ Deleted: Text | Audio | Sticker | File\n"
        "🗑 Duplicate media auto delete\n"
        "🖼 HQ video thumbnail auto-fix\n\n"
        "📊 Use /report"
    )


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Duplicate Media Report\n\n"
        f"🗑 Total duplicate media deleted: {deleted_count}"
    )


# ---------------- START BOT ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()
