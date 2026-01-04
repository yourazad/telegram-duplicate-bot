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

TOKEN = os.getenv("TOKEN")

# storage
seen_media = set()
deleted_count = 0


def media_hash(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()


def extract_thumbnail(video_path: str, thumb_path: str):
    clip = VideoFileClip(video_path)
    t = int(clip.duration // 2) if clip.duration > 2 else 1
    clip.save_frame(thumb_path, t=t)
    clip.close()


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
        return
    else:
        seen_media.add(h)

    # 🎯 VIDEO THUMBNAIL FIX (ONLY IF THUMB MISSING)
    if msg.video and not msg.video.thumbnail:
        try:
            video_file = await msg.video.get_file()
            video_path = "video.mp4"
            thumb_path = "thumb.jpg"

            await video_file.download_to_drive(video_path)
            extract_thumbnail(video_path, thumb_path)

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
            print("Thumbnail error:", e)


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
        "🗑 Duplicate media auto delete\n"
        "🖼 Video thumbnail auto-fix\n\n"
        "📊 /report for deleted count"
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()
