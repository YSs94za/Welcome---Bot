import asyncio
import logging

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter

from config import BROADCAST_ADMIN_IDS
from database.pg_db import get_all_chats, remove_chat

logger = logging.getLogger(__name__)
router = Router()

RATE_DELAY = 0.05  # seconds between sends to avoid flood


class BroadcastStates(StatesGroup):
    waiting_for_content = State()


def _is_broadcast_admin(user_id: int) -> bool:
    """Check if user is authorized for broadcast."""
    return user_id in BROADCAST_ADMIN_IDS


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext) -> None:
    """Start broadcast mode (super-admin only)."""
    try:
        if not message.from_user or not _is_broadcast_admin(message.from_user.id):
            await message.answer("⛔ You are not authorised to use this command.")
            logger.warning("Unauthorized broadcast attempt from user %s", message.from_user.id if message.from_user else "?")
            return

        chats = await get_all_chats()
        if not chats:
            await message.answer(
                "⚠️ No known chats found in the database.\n"
                "Chats are registered automatically when users interact with the bot."
            )
            return

        await state.set_state(BroadcastStates.waiting_for_content)
        await message.answer(
            f"📢 <b>Broadcast mode</b>\n\n"
            f"Target chats: <b>{len(chats)}</b>\n\n"
            f"Send the message you want to broadcast.\n"
            f"Supported: text, photo, video, document, animation.\n\n"
            f"Send /cancel to abort."
        )
        logger.info("Broadcast mode started by user %s for %d chats", message.from_user.id, len(chats))
    except Exception as exc:
        logger.error("Error in cmd_broadcast: %s", exc)
        try:
            await message.answer(f"❌ Error: {type(exc).__name__}")
        except Exception:
            pass


@router.message(Command("cancel"), BroadcastStates.waiting_for_content)
async def cmd_broadcast_cancel(message: Message, state: FSMContext) -> None:
    """Cancel broadcast."""
    try:
        await state.clear()
        await message.answer("❌ Broadcast cancelled.")
        logger.info("Broadcast cancelled by user %s", message.from_user.id if message.from_user else "?")
    except Exception as exc:
        logger.error("Error in cmd_broadcast_cancel: %s", exc)


@router.message(BroadcastStates.waiting_for_content)
async def handle_broadcast_content(message: Message, state: FSMContext, bot: Bot) -> None:
    """Process and send broadcast to all chats."""
    await state.clear()

    try:
        chats = await get_all_chats()
        if not chats:
            await message.answer("⚠️ No known chats found. Broadcast aborted.")
            return

        status_msg = await message.answer(
            f"📤 Broadcasting to <b>{len(chats)}</b> chat(s)… please wait."
        )

        ok = 0
        failed = 0
        blocked = 0
        removed_ids: list[int] = []

        for chat in chats:
            chat_id = chat["chat_id"]
            try:
                await _forward_message(bot, message, chat_id)
                ok += 1
                await asyncio.sleep(RATE_DELAY)

            except TelegramRetryAfter as e:
                logger.warning("FloodWait %ds for chat %d — sleeping", e.retry_after, chat_id)
                await asyncio.sleep(e.retry_after + 1)
                try:
                    await _forward_message(bot, message, chat_id)
                    ok += 1
                except Exception as retry_exc:
                    logger.error("Retry failed for chat %d: %s", chat_id, retry_exc)
                    failed += 1

            except TelegramForbiddenError:
                logger.info("Bot blocked/kicked in chat %d — removing from DB", chat_id)
                removed_ids.append(chat_id)
                blocked += 1

            except TelegramBadRequest as exc:
                logger.warning("BadRequest for chat %d: %s", chat_id, exc)
                failed += 1

            except Exception as exc:
                logger.error("Unexpected error for chat %d: %s", chat_id, exc)
                failed += 1

        # Clean up removed chats
        for cid in removed_ids:
            try:
                await remove_chat(cid)
            except Exception as exc:
                logger.error("Failed to remove chat %d from DB: %s", cid, exc)

        total = len(chats)
        summary_lines = [
            "📊 <b>Broadcast complete</b>\n",
            f"✅ Delivered:  <b>{ok}</b> / {total}",
            f"🚫 Blocked:    <b>{blocked}</b> (removed from DB)",
            f"❌ Failed:     <b>{failed}</b>",
        ]
        if removed_ids:
            summary_lines.append(f"\n🗑 Cleaned {len(removed_ids)} inactive chat(s).")

        try:
            await status_msg.edit_text("\n".join(summary_lines))
        except Exception:
            await message.answer("\n".join(summary_lines))

        logger.warning(
            "Broadcast done | total=%d ok=%d blocked=%d failed=%d",
            total, ok, blocked, failed,
        )
    except Exception as exc:
        logger.error("Error in handle_broadcast_content: %s", exc)
        try:
            await message.answer(f"❌ Broadcast error: {type(exc).__name__}")
        except Exception:
            pass


async def _forward_message(bot: Bot, source: Message, chat_id: int) -> None:
    """Forward message to target chat with error handling.
    
    Supports: text, photo, video, document, animation, voice, audio.
    """
    try:
        if source.text:
            await bot.send_message(
                chat_id,
                source.text,
                entities=source.entities,
            )
        elif source.photo:
            await bot.send_photo(
                chat_id,
                source.photo[-1].file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        elif source.video:
            await bot.send_video(
                chat_id,
                source.video.file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        elif source.document:
            await bot.send_document(
                chat_id,
                source.document.file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        elif source.animation:
            await bot.send_animation(
                chat_id,
                source.animation.file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        elif source.voice:
            await bot.send_voice(
                chat_id,
                source.voice.file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        elif source.audio:
            await bot.send_audio(
                chat_id,
                source.audio.file_id,
                caption=source.caption,
                caption_entities=source.caption_entities,
            )
        else:
            raise ValueError(f"Unsupported message type in chat {chat_id}")
    except Exception as exc:
        logger.error("Failed to forward message to chat %d: %s", chat_id, exc)
        raise
