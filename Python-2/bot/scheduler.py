import asyncio
import logging
import threading
from datetime import datetime, timedelta, date
from telegram import Bot
from telegram.constants import ParseMode
from bot.config import CHANNEL_ID, POST_INTERVAL_MINUTES, POSTS_PER_BATCH, TELEGRAM_TOKEN
from bot.db import session_scope, PostedItem, get_setting, set_setting
from bot.nasa import fetch_apod_by_date, is_valid_image

log = logging.getLogger(__name__)

APOD_FIRST_DATE = date(1995, 6, 16)
CURSOR_KEY = "apod_cursor_date"


def format_caption(item: dict) -> str:
    title = item.get("title", "Nomalum")
    explanation = item.get("explanation", "")
    nasa_date = item.get("date", "")
    copyright_ = item.get("copyright", "NASA")

    if len(explanation) > 700:
        explanation = explanation[:700].rsplit(" ", 1)[0] + "..."

    return (
        f"🌌 <b>{title}</b>\n\n"
        f"📅 <i>Sana:</i> <code>{nasa_date}</code>\n"
        f"📸 <i>Muallif:</i> {copyright_}\n\n"
        f"🔭 <b>Qiziqarli fakt:</b>\n{explanation}\n\n"
        f"✨ #NASA #Kosmos #Astronomiya"
    )


def get_cursor() -> date:
    """Read cursor date from DB; default to yesterday."""
    val = get_setting(CURSOR_KEY, "")
    if val:
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except Exception:
            pass
    return date.today() - timedelta(days=1)


def save_cursor(d: date):
    set_setting(CURSOR_KEY, d.strftime("%Y-%m-%d"))


def date_already_posted(d: date) -> bool:
    with session_scope() as s:
        return s.query(PostedItem).filter_by(nasa_date=d.strftime("%Y-%m-%d")).first() is not None


async def collect_unique_items(needed: int) -> list:
    """Collect `needed` items by walking dates backward from cursor, skipping already-posted ones."""
    items = []
    cursor = get_cursor()
    walked = 0
    max_walk = needed * 30

    while len(items) < needed and walked < max_walk:
        walked += 1

        if cursor < APOD_FIRST_DATE:
            log.warning("📭 APOD arxivining boshiga yetildi, qayta yuqoridan boshlayapmiz.")
            cursor = date.today() - timedelta(days=1)

        if date_already_posted(cursor):
            cursor -= timedelta(days=1)
            continue

        date_str = cursor.strftime("%Y-%m-%d")
        item = await fetch_apod_by_date(date_str)
        if item and is_valid_image(item):
            items.append(item)

        cursor -= timedelta(days=1)
        await asyncio.sleep(1.5)

    save_cursor(cursor)
    return items


async def post_batch():
    if not CHANNEL_ID or not TELEGRAM_TOKEN:
        log.warning("⚠️  CHANNEL_ID yoki TELEGRAM_TOKEN topilmadi.")
        return

    log.info(f"🚀 {POSTS_PER_BATCH} ta yangi rasm qidirilmoqda (tartib bilan)...")
    items = await collect_unique_items(POSTS_PER_BATCH)
    if not items:
        log.warning("❌ Yangi rasm topilmadi.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    sent = 0
    for it in items:
        nasa_date = it.get("date")
        if not nasa_date:
            continue
        if date_already_posted(date.fromisoformat(nasa_date)):
            continue
        try:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=it["url"],
                caption=format_caption(it),
                parse_mode=ParseMode.HTML,
            )
            with session_scope() as s:
                s.add(PostedItem(
                    nasa_date=nasa_date,
                    image_url=it.get("url", ""),
                ))
            sent += 1
            await asyncio.sleep(2)
        except Exception as e:
            log.error(f"❌ Yuborishda xato ({nasa_date}): {e}")
    log.info(f"✅ {sent}/{len(items)} ta post yuborildi.")


def _runner_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    interval = POST_INTERVAL_MINUTES * 60

    async def main():
        while True:
            try:
                await post_batch()
            except Exception as e:
                log.error(f"Scheduler error: {e}")
            await asyncio.sleep(interval)

    loop.run_until_complete(main())


def start_scheduler():
    t = threading.Thread(target=_runner_loop, daemon=True, name="nasa-scheduler")
    t.start()
    log.info(f"⏰ Scheduler ishga tushdi: har {POST_INTERVAL_MINUTES} daqiqada {POSTS_PER_BATCH} ta post.")
