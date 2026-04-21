from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List


def subscription_keyboard(channels: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url_name = ch.lstrip("@")
        rows.append([InlineKeyboardButton(f"📢 {url_name} ga obuna bo'lish", url=f"https://t.me/{url_name}")])
    rows.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌌 Kanalimizga o'tish", url="https://t.me/")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ])
