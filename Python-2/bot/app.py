import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from bot.config import TELEGRAM_TOKEN, PORT, get_public_url
from bot.db import init_db
from bot.handlers import (
    start_handler,
    check_sub_callback,
    admin_handler,
    add_channel_handler,
    del_channel_handler,
    list_channels_handler,
    post_now_handler,
)
from bot.scheduler import start_scheduler

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

flask_app = Flask(__name__)
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

application: Application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(CommandHandler("admin", admin_handler))
application.add_handler(CommandHandler("addchannel", add_channel_handler))
application.add_handler(CommandHandler("delchannel", del_channel_handler))
application.add_handler(CommandHandler("channels", list_channels_handler))
application.add_handler(CommandHandler("postnow", post_now_handler))
application.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))

_loop.run_until_complete(application.initialize())


@flask_app.route("/")
def home():
    return jsonify({"status": "ok", "bot": "running", "emoji": "🚀"})


@flask_app.route("/health")
def health():
    return "OK", 200


@flask_app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        _loop.run_until_complete(application.process_update(update))
        return "OK", 200
    except Exception as e:
        log.error(f"Webhook error: {e}")
        return "ERR", 500


def setup_webhook():
    public_url = get_public_url()
    if not public_url:
        log.warning("⚠️  WEBHOOK_URL/RENDER_EXTERNAL_URL topilmadi. Polling rejimi ishga tushadi.")
        return False

    full_url = f"{public_url}/{TELEGRAM_TOKEN}"
    try:
        _loop.run_until_complete(application.bot.set_webhook(url=full_url, drop_pending_updates=True))
        log.info(f"✅ Webhook o'rnatildi: {full_url}")
        return True
    except Exception as e:
        log.error(f"❌ Webhook o'rnatishda xato: {e}")
        return False


_booted = False


def boot():
    global _booted
    if _booted:
        return
    _booted = True
    init_db()
    start_scheduler()
    setup_webhook()
