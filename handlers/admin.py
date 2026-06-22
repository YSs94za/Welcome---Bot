import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters.admin import AdminFilter
from keyboards.inline import build_welcome_keyboard
from database.pg_db import (
    get_welcome_message,
    set_welcome_message,
    delete_welcome_message,
    get_buttons,
    add_button,
    delete_button,
    delete_all_buttons,
    get_stats,
)

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(AdminFilter())


@router.message(Command("set_welcome"))
async def cmd_set_welcome(message: Message) -> None:
    """Set welcome message for this group (admin only)."""
    try:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            await message.answer(
                "⚠️ Usage: /set_welcome <code>&lt;message&gt;</code>\n\n"
                "Placeholders: <code>{name}</code>, <code>{chat}</code>\n\n"
                "Example:\n"
                "<code>/set_welcome Welcome, {name}! Glad you joined {chat} 🎉</code>"
            )
            return
        text = args[1].strip()
        await set_welcome_message(message.chat.id, text)
        await message.answer("✅ Welcome message saved!")
        logger.info("Welcome message set for chat %d", message.chat.id)
    except Exception as exc:
        logger.error("Error in cmd_set_welcome: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("show_welcome"))
async def cmd_show_welcome(message: Message) -> None:
    """Preview the welcome message for this group (admin only)."""
    try:
        text = await get_welcome_message(message.chat.id)
        if not text:
            await message.answer("ℹ️ No welcome message set for this chat.")
            return
        buttons = await get_buttons(message.chat.id)
        kb = build_welcome_keyboard(buttons)
        chat_title = message.chat.title or "this chat"
        preview = text.replace("{name}", "<b>John Doe</b>").replace("{chat}", f"<b>{chat_title}</b>")
        await message.answer(
            f"<b>👁 Preview:</b>\n\n{preview}",
            reply_markup=kb,
        )
        logger.info("Welcome preview shown for chat %d", message.chat.id)
    except Exception as exc:
        logger.error("Error in cmd_show_welcome: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("del_welcome"))
async def cmd_del_welcome(message: Message) -> None:
    """Delete welcome message and all buttons (admin only)."""
    try:
        deleted = await delete_welcome_message(message.chat.id)
        count = await delete_all_buttons(message.chat.id)
        if deleted:
            note = f" Also removed {count} button(s)." if count else ""
            await message.answer(f"🗑 Welcome message deleted.{note}")
            logger.info("Welcome deleted for chat %d (%d buttons removed)", message.chat.id, count)
        else:
            await message.answer("ℹ️ No welcome message to delete.")
    except Exception as exc:
        logger.error("Error in cmd_del_welcome: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("add_button"))
async def cmd_add_button(message: Message) -> None:
    """Add inline button to welcome message (admin only)."""
    try:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2 or "|" not in args[1]:
            await message.answer(
                "⚠️ Usage: /add_button <code>&lt;label&gt; | &lt;url&gt;</code>\n\n"
                "Example: <code>/add_button Visit us | https://example.com</code>"
            )
            return
        label, url = [p.strip() for p in args[1].split("|", 1)]
        if not label or not url:
            await message.answer("⚠️ Both label and URL are required.")
            return
        if not url.startswith(("http://", "https://")):
            await message.answer("⚠️ URL must start with <code>http://</code> or <code>https://</code>")
            return
        btn_id = await add_button(message.chat.id, label, url)
        await message.answer(f"✅ Button added — ID: <code>#{btn_id}</code>")
        logger.info("Button #%d added for chat %d: %s", btn_id, message.chat.id, label)
    except Exception as exc:
        logger.error("Error in cmd_add_button: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("del_button"))
async def cmd_del_button(message: Message) -> None:
    """Remove button by ID (admin only)."""
    try:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2 or not args[1].strip().isdigit():
            await message.answer("⚠️ Usage: /del_button <code>&lt;id&gt;</code>")
            return
        btn_id = int(args[1].strip())
        if await delete_button(btn_id, message.chat.id):
            await message.answer(f"🗑 Button <code>#{btn_id}</code> removed.")
            logger.info("Button #%d deleted for chat %d", btn_id, message.chat.id)
        else:
            await message.answer(f"❌ Button <code>#{btn_id}</code> not found.")
    except Exception as exc:
        logger.error("Error in cmd_del_button: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("list_buttons"))
async def cmd_list_buttons(message: Message) -> None:
    """List all buttons for this chat (admin only)."""
    try:
        buttons = await get_buttons(message.chat.id)
        if not buttons:
            await message.answer("ℹ️ No buttons configured for this chat.")
            return
        lines = [f"<code>#{b['id']}</code> — {b['label']}  →  {b['url']}" for b in buttons]
        await message.answer("<b>📎 Buttons:</b>\n\n" + "\n".join(lines))
        logger.info("Button list shown for chat %d (%d buttons)", message.chat.id, len(buttons))
    except Exception as exc:
        logger.error("Error in cmd_list_buttons: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show bot statistics (admin only)."""
    try:
        s = await get_stats()
        text = (
            "<b>📊 Bot Statistics</b>\n\n"
            "<b>🌐 Reach</b>\n"
            f"  Total known chats:   <b>{s['total_chats']}</b>\n"
            f"  ├ Groups/Supergroups: <b>{s['groups']}</b>\n"
            f"  └ Private chats:      <b>{s['private']}</b>\n\n"
            "<b>📝 Welcome System</b>\n"
            f"  Configured welcomes:  <b>{s['welcome_count']}</b>\n"
            f"  Total buttons:        <b>{s['button_count']}</b>\n"
            f"  Chats with buttons:   <b>{s['chats_with_btn']}</b>"
        )
        await message.answer(text)
        logger.info("Stats shown for chat %d", message.chat.id)
    except Exception as exc:
        logger.error("Error in cmd_stats: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")
