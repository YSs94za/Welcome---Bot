from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Developer", callback_data="developer")],
        [InlineKeyboardButton(text="📋 Commands", callback_data="commands")],
    ])


def developer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Instagram", url="https://www.instagram.com/1.0_v_?igsh=N2N5MXNwN3p4ZDY2"),
            InlineKeyboardButton(text="✈️ Telegram",  url="https://t.me/Y9_S4"),
        ],
        [
            InlineKeyboardButton(text="🎵 TikTok",    url="https://www.tiktok.com/@zix8ii?_r=1&_d=f3c01a6371bii9&sec_uid="),
            InlineKeyboardButton(text="👤 Facebook",  url="https://www.facebook.com/share/1BkTUUih6e/"),
        ],
        [
            InlineKeyboardButton(text="💬 WhatsApp",  url="https://wa.link/lc6f5w"),
            InlineKeyboardButton(text="🆘 Support",   url="https://t.me/shaheen_ys"),
        ],
    ])


def back_to_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_start")],
    ])


def build_welcome_keyboard(buttons: list[dict]) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None
    rows = [
        [InlineKeyboardButton(text=b["label"], url=b["url"])]
        for b in buttons
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
