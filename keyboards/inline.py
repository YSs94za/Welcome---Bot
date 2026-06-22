from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard with safe buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Developer", callback_data="developer")],
        [InlineKeyboardButton(text="📋 Commands",   callback_data="commands")],
    ])


def developer_keyboard() -> InlineKeyboardMarkup:
    """Developer contact keyboard with verified URLs."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Instagram", url="https://www.instagram.com/1.0_v_?igsh=N2N5MXNwN3p4ZDY2"),
            InlineKeyboardButton(text="✈️ Telegram",  url="https://t.me/Y9_S4"),
        ],
        [
            InlineKeyboardButton(text="🎵 TikTok",   url="https://www.tiktok.com/@zix8ii"),
            InlineKeyboardButton(text="👤 Facebook",  url="https://www.facebook.com/share/1BkTUUih6e/"),
        ],
        [
            InlineKeyboardButton(text="💬 WhatsApp",  url="https://wa.link/lc6f5w"),
            InlineKeyboardButton(text="🆘 Support",   url="https://t.me/shaheen_ys"),
        ],
    ])


def back_to_start_keyboard() -> InlineKeyboardMarkup:
    """Back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_start")],
    ])


def build_welcome_keyboard(buttons: list[dict]) -> InlineKeyboardMarkup | None:
    """Build inline keyboard for welcome message buttons.
    
    Args:
        buttons: List of dicts with 'label' and 'url' keys.
    
    Returns:
        InlineKeyboardMarkup or None if no buttons.
    """
    if not buttons:
        return None
    
    rows = []
    for b in buttons:
        try:
            rows.append([
                InlineKeyboardButton(text=b["label"], url=b["url"])
            ])
        except (KeyError, ValueError) as exc:
            # Skip malformed button
            continue
    
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
