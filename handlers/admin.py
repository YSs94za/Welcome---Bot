import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters.admin import AdminFilter
from keyboards.inline import build_welcome_keyboard
from database.sqlite_db import (
    get_welcome_message,
    set_welcome_message,
    delete_welcome_message,
    get_buttons,
    add_button,
    delete_button,
    delete_all_buttons,
)

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(AdminFilter())


@router.message(Command("set_welcome"))
async def cmd_set_welcome(message: Message) -> None:
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


@router.message(Command("show_welcome"))
async def cmd_show_welcome(message: Message) -> None:
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


@router.message(Command("del_welcome"))
async def cmd_del_welcome(message: Message) -> None:
    deleted = await delete_welcome_message(message.chat.id)
    count = await delete_all_buttons(message.chat.id)
    if deleted:
        note = f" Also removed {count} button(s)." if count else ""
        await message.answer(f"🗑 Welcome message deleted.{note}")
    else:
        await message.answer("ℹ️ No welcome message to delete.")


@router.message(Command("add_button"))
async def cmd_add_button(message: Message) -> None:
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


@router.message(Command("del_button"))
async def cmd_del_button(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer("⚠️ Usage: /del_button <code>&lt;id&gt;</code>")
        return
    btn_id = int(args[1].strip())
    if await delete_button(btn_id, message.chat.id):
        await message.answer(f"🗑 Button <code>#{btn_id}</code> removed.")
    else:
        await message.answer(f"❌ Button <code>#{btn_id}</code> not found.")


@router.message(Command("list_buttons"))
async def cmd_list_buttons(message: Message) -> None:
    buttons = await get_buttons(message.chat.id)
    if not buttons:
        await message.answer("ℹ️ No buttons configured for this chat.")
        return
    lines = [f"<code>#{b['id']}</code> — {b['label']}  →  {b['url']}" for b in buttons]
    await message.answer("<b>📎 Buttons:</b>\n\n" + "\n".join(lines))
