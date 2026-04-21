import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.config import REQUIRED_CHANNELS, ADMIN_ID, CHANNEL_ID
from bot.db import session_scope, BotUser, RequiredChannel, PostedItem
from bot.keyboards import subscription_keyboard

log = logging.getLogger(__name__)


def get_required_channels() -> list:
    """Returns list of channel usernames from DB + ENV."""
    channels = list(REQUIRED_CHANNELS)
    try:
        with session_scope() as s:
            db_channels = s.query(RequiredChannel).all()
            for ch in db_channels:
                if ch.channel_username not in channels:
                    channels.append(ch.channel_username)
    except Exception as e:
        log.error(f"DB channel fetch error: {e}")
    return channels


async def check_user_subscribed(bot, user_id: int, channels: list) -> list:
    """Returns list of channels user is NOT subscribed to."""
    not_subscribed = []
    for ch in channels:
        try:
            ch_id = ch if ch.startswith("@") else f"@{ch}"
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch_id)
        except Exception as e:
            log.warning(f"Subscription check failed for {ch}: {e}")
            not_subscribed.append(ch)
    return not_subscribed


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    with session_scope() as s:
        existing = s.query(BotUser).filter_by(user_id=user.id).first()
        if not existing:
            s.add(BotUser(user_id=user.id))

    channels = get_required_channels()
    if channels:
        not_sub = await check_user_subscribed(context.bot, user.id, channels)
        if not_sub:
            text = (
                f"👋 Salom, <b>{user.first_name}</b>!\n\n"
                f"🚀 Botdan to'liq foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
                f"⬇️ <i>Obuna bo'lgach, \"Tekshirish\" tugmasini bosing.</i>"
            )
            await update.message.reply_text(
                text,
                reply_markup=subscription_keyboard(not_sub),
                parse_mode=ParseMode.HTML,
            )
            return

    welcome = (
        f"🎉 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
        f"🌌 Bu bot avtomatik ravishda kosmik rasmlar va qiziqarli faktlarni "
        f"bizning kanalimizga joylab boradi.\n\n"
        f"✨ Kuzatib boring va kosmosning sirlarini kashf qiling! 🚀"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.HTML)


async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    await query.answer()

    channels = get_required_channels()
    not_sub = await check_user_subscribed(context.bot, query.from_user.id, channels)

    if not_sub:
        await query.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)
        return

    with session_scope() as s:
        u = s.query(BotUser).filter_by(user_id=query.from_user.id).first()
        if u:
            u.is_subscribed = True

    await query.edit_message_text(
        f"✅ <b>Tabriklaymiz!</b>\n\n"
        f"🎉 Endi botdan to'liq foydalanishingiz mumkin!\n"
        f"🌌 Kanalimizni kuzatib boring — har 5 daqiqada yangi kosmik rasmlar! 🚀",
        parse_mode=ParseMode.HTML,
    )


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID or not update.message:
        return

    with session_scope() as s:
        users = s.query(BotUser).count()
        subs = s.query(BotUser).filter_by(is_subscribed=True).count()
        posts = s.query(PostedItem).count()
        channels = s.query(RequiredChannel).count()

    text = (
        f"👑 <b>Admin Panel</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"✅ Obuna bo'lganlar: <b>{subs}</b>\n"
        f"🖼 Yuborilgan rasmlar: <b>{posts}</b>\n"
        f"📢 Majburiy kanallar (DB): <b>{channels}</b>\n"
        f"📡 Joriy kanal: <code>{CHANNEL_ID or 'sozlanmagan'}</code>\n\n"
        f"<b>Komandalar:</b>\n"
        f"<code>/addchannel @kanal_nomi</code>\n"
        f"<code>/delchannel @kanal_nomi</code>\n"
        f"<code>/channels</code> — kanallar ro'yxati\n"
        f"<code>/postnow</code> — hozir post yuborish"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def add_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID or not update.message:
        return

    if not context.args:
        await update.message.reply_text("❌ Foydalanish: <code>/addchannel @kanal_nomi</code>", parse_mode=ParseMode.HTML)
        return

    ch = context.args[0]
    if not ch.startswith("@"):
        ch = "@" + ch

    with session_scope() as s:
        existing = s.query(RequiredChannel).filter_by(channel_username=ch).first()
        if existing:
            await update.message.reply_text(f"⚠️ {ch} allaqachon mavjud.")
            return
        s.add(RequiredChannel(channel_username=ch))

    await update.message.reply_text(f"✅ {ch} majburiy kanallar ro'yxatiga qo'shildi.")


async def del_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID or not update.message:
        return

    if not context.args:
        await update.message.reply_text("❌ Foydalanish: <code>/delchannel @kanal_nomi</code>", parse_mode=ParseMode.HTML)
        return

    ch = context.args[0]
    if not ch.startswith("@"):
        ch = "@" + ch

    with session_scope() as s:
        existing = s.query(RequiredChannel).filter_by(channel_username=ch).first()
        if not existing:
            await update.message.reply_text(f"❌ {ch} topilmadi.")
            return
        s.delete(existing)

    await update.message.reply_text(f"🗑 {ch} o'chirildi.")


async def list_channels_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID or not update.message:
        return

    channels = get_required_channels()
    if not channels:
        await update.message.reply_text("📭 Majburiy kanallar yo'q.")
        return

    text = "📢 <b>Majburiy kanallar:</b>\n\n" + "\n".join(f"• <code>{c}</code>" for c in channels)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def post_now_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID or not update.message:
        return

    await update.message.reply_text("⏳ Postlar yuborilmoqda...")
    from bot.scheduler import post_batch
    try:
        await post_batch()
        await update.message.reply_text("✅ Postlar muvaffaqiyatli yuborildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")
