# NASA Kosmos Bot

## Loyiha haqida
Telegram bot bo'lib, NASA APOD API'dan har 5 daqiqada 10 ta yangi kosmik rasm va faktlarni avtomatik ravishda Telegram kanaliga joylab boradi. Render.com'da deploy qilish uchun avto webhook qo'llab-quvvatlaydi.

## Arxitektura
- **main.py** — Webhook (Render) yoki polling rejimini avtomatik tanlaydi
- **bot/app.py** — Flask + Telegram Application
- **bot/scheduler.py** — Background thread, har 5 daqiqada NASA'dan tartib bilan (sana cursor) rasm olib kanalga joylaydi. Random emas, takrorlanmaydi.
- **bot/nasa.py** — NASA APOD API client (sana bo'yicha so'rov)
- **bot/handlers.py** — /start (majburiy obuna), /admin, kanal qo'shish/o'chirish
- **bot/db.py** — PostgreSQL (SQLAlchemy): posted_items, bot_users, required_channels
- **bot/config.py** — ENV o'zgaruvchilar
- **bot/keyboards.py** — Inline tugmalar

## ENV O'zgaruvchilar
- `TELEGRAM_TOKEN` — BotFather token (majburiy)
- `ADMIN_ID` — admin Telegram ID
- `CHANNEL_ID` — post yuboriladigan kanal (@username yoki ID)
- `NASA_API_KEY` — NASA API kalit (default: DEMO_KEY)
- `REQUIRED_CHANNELS` — vergul bilan ajratilgan @kanal_username ro'yxati
- `POST_INTERVAL_MINUTES` — post oralig'i (default: 5)
- `POSTS_PER_BATCH` — har safar yuboriladigan rasmlar (default: 10)
- `DATABASE_URL` — PostgreSQL URL (Render avtomatik beradi)
- `WEBHOOK_URL` yoki `RENDER_EXTERNAL_URL` — webhook URL

## Foydalanuvchi sozlamalari
- Render.com'ga deploy uchun render.yaml mavjud
- Webhook avtomatik o'rnatiladi (RENDER_EXTERNAL_URL bo'lsa)
- BOT_QURISH_QOLLANMA.txt — to'liq qo'llanma
