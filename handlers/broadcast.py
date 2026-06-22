import asyncio
import logging

from aiogram import Router, Bot
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
    return user_id in BROADCAST_ADMIN_IDS


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext) -> None:
    if not message.from_user or not _is_broadcast_admin(message.from_user.id):
        await message.answer("⛔ You are not authorised to use this command.")
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


@router.message(Command("cancel"), BroadcastStates.waiting_for_content)
async def cmd_broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Broadcast cancelled.")


@router.message(BroadcastStates.waiting_for_content)
async def handle_broadcast_content(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()

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

    for cid in removed_ids:
        await remove_chat(cid)

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


async def _forward_message(bot: Bot, source: Message, chat_id: int) -> None:
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
