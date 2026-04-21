import os
import logging

from bot.config import TELEGRAM_TOKEN, PORT, get_public_url

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

if not TELEGRAM_TOKEN:
    log.error("❌ TELEGRAM_TOKEN topilmadi! Iltimos, Secrets bo'limiga TELEGRAM_TOKEN qo'shing.")
    raise SystemExit(1)


from bot.app import flask_app, application, boot

boot()

if get_public_url():
    log.info(f"🌍 Webhook server ishga tushmoqda — port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT)
else:
    log.info("🤖 Polling rejimi (Webhook URL topilmadi)")
    application.run_polling(drop_pending_updates=True)
