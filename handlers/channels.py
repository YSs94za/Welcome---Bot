import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters.admin import AdminFilter
from database.pg_db import add_channel, delete_channel, list_channels

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(AdminFilter())


@router.message(Command("add_channel"))
async def cmd_add_channel(message: Message) -> None:
    """Add a channel to the registered list (admin only).
    
    Usage:
      1. Forward any message from the target channel, then reply with /add_channel
      2. /add_channel @username
      3. /add_channel -100xxxxxxxxxx
    
    Note: Channels are stored for informational purposes.
    The bot does NOT enforce channel membership or subscriptions.
    """
    try:
        bot = message.bot  # type: ignore[union-attr]
        channel_id: int | None = None
        username: str | None = None
        title: str | None = None

        # Case 1: replied to a forwarded channel message
        if message.reply_to_message and message.reply_to_message.forward_from_chat:
            fwd = message.reply_to_message.forward_from_chat
            channel_id = fwd.id
            username = fwd.username
            title = fwd.title
            logger.info("Channel extracted from forwarded message: %d", channel_id)

        else:
            # Case 2/3: argument provided
            args = (message.text or "").split(maxsplit=1)
            if len(args) < 2 or not args[1].strip():
                await message.answer(
                    "⚠️ Usage:\n"
                    "1. Forward a message from the channel → reply with /add_channel\n"
                    "2. <code>/add_channel @username</code>\n"
                    "3. <code>/add_channel -100xxxxxxxxxx</code>"
                )
                return

            arg = args[1].strip()
            try:
                chat = await bot.get_chat(arg)
                channel_id = chat.id
                username = chat.username
                title = chat.title
                logger.info("Channel fetched from argument: %d", channel_id)
            except Exception as exc:
                await message.answer(f"❌ Could not fetch channel info: <code>{exc}</code>")
                logger.error("Failed to fetch channel %s: %s", arg, exc)
                return

        if channel_id is None:
            await message.answer("❌ Could not determine channel ID.")
            return

        added_by = message.from_user.id if message.from_user else 0
        success = await add_channel(channel_id, username, title, added_by)

        if success:
            display = f"@{username}" if username else str(channel_id)
            name = title or display
            await message.answer(f"✅ Channel <b>{name}</b> (<code>{channel_id}</code>) added.")
            logger.info("Channel %d added by user %d", channel_id, added_by)
        else:
            await message.answer("❌ Failed to add channel (already exists or DB error).")
            logger.warning("Failed to add channel %d", channel_id)
    except Exception as exc:
        logger.error("Error in cmd_add_channel: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("del_channel"))
async def cmd_del_channel(message: Message) -> None:
    """Remove a channel from the registered list (admin only)."""
    try:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            await message.answer("⚠️ Usage: /del_channel <code>&lt;channel_id&gt;</code>")
            return

        arg = args[1].strip()
        try:
            channel_id = int(arg)
        except ValueError:
            await message.answer("⚠️ Channel ID must be a number (e.g. <code>-1001234567890</code>)")
            return

        removed = await delete_channel(channel_id)
        if removed:
            await message.answer(f"🗑 Channel <code>{channel_id}</code> removed.")
            logger.info("Channel %d deleted", channel_id)
        else:
            await message.answer(f"❌ Channel <code>{channel_id}</code> not found.")
    except Exception as exc:
        logger.error("Error in cmd_del_channel: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")


@router.message(Command("list_channels"))
async def cmd_list_channels(message: Message) -> None:
    """List all registered channels (admin only)."""
    try:
        channels = await list_channels()
        if not channels:
            await message.answer("ℹ️ No channels registered.")
            return

        lines = []
        for ch in channels:
            mention = f"@{ch['username']}" if ch["username"] else str(ch["channel_id"])
            name = ch["title"] or mention
            lines.append(f"• <b>{name}</b> ({mention}) — <code>{ch['channel_id']}</code>")

        await message.answer("<b>📡 Registered Channels:</b>\n\n" + "\n".join(lines))
        logger.info("Channel list shown for chat %d (%d channels)", message.chat.id, len(channels))
    except Exception as exc:
        logger.error("Error in cmd_list_channels: %s", exc)
        await message.answer(f"❌ Error: {type(exc).__name__}")
