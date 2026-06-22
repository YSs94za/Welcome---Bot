import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import developer_keyboard, start_keyboard

logger = logging.getLogger(__name__)
router = Router()

DEVELOPER_TEXT = (
    "<b>YOUSEF SHAHEEN</b> | Coding the future, beyond the limits of imagination.\n\n"
    "أنا لا أبني مجرد بوتات تليجرام، بل أصيغ حلولاً رقمية ذكية تتنفس الابتكار.\n\n"
    "<i>Engineering excellence</i> بلمسة فنية، لنحول أفكارك إلى واقع automated يسبق زمنه.\n\n"
    "Ready to disrupt? Let's connect:\n\n"
    "📩 @Y9_S4"
)

COMMANDS_TEXT = (
    "<b>📋 All Commands</b>\n\n"
    "<b>General:</b>\n"
    "/start — Show main menu\n\n"
    "<b>Welcome System (admin only):</b>\n"
    "/set_welcome <code>&lt;text&gt;</code> — Set welcome message\n"
    "/show_welcome — Preview current welcome message\n"
    "/del_welcome — Delete welcome message &amp; buttons\n\n"
    "<b>Buttons (admin only):</b>\n"
    "/add_button <code>&lt;label&gt; | &lt;url&gt;</code> — Add inline button\n"
    "/del_button <code>&lt;id&gt;</code> — Remove button by ID\n"
    "/list_buttons — List all buttons\n\n"
    "<b>Statistics (admin only):</b>\n"
    "/stats — Show bot reach & database statistics\n\n"
    "<b>Broadcast (super-admin only):</b>\n"
    "/broadcast — Send message to all known chats\n\n"
    "<b>Placeholders:</b>\n"
    "<code>{name}</code> — Member's full name\n"
    "<code>{chat}</code> — Group name"
)

START_CAPTION = (
    "<b>👋 Welcome Bot</b>\n\n"
    "I automatically greet new members with a custom message and inline buttons.\n\n"
    "<b>📌 Features:</b>\n"
    "• Custom welcome messages per group\n"
    "• Unlimited inline URL buttons\n"
    "• Placeholder support: <code>{name}</code>, <code>{chat}</code>\n"
    "• Admin-only management\n"
    "• Multi-group support\n\n"
    "Press a button below to get started ↓"
)


@router.callback_query(F.data == "developer")
async def cb_developer(call: CallbackQuery) -> None:
    """Show developer contact information."""
    try:
        await call.answer()
        await call.message.answer(
            DEVELOPER_TEXT,
            reply_markup=developer_keyboard(),
        )
        logger.info("Developer info shown to user %s", call.from_user.id)
    except Exception as exc:
        logger.error("Error in cb_developer: %s", exc)
        try:
            await call.answer(f"❌ Error: {type(exc).__name__}")
        except Exception:
            pass


@router.callback_query(F.data == "commands")
async def cb_commands(call: CallbackQuery) -> None:
    """Show all available commands."""
    try:
        await call.answer()
        await call.message.answer(
            COMMANDS_TEXT,
            reply_markup=None,
        )
        logger.info("Commands list shown to user %s", call.from_user.id)
    except Exception as exc:
        logger.error("Error in cb_commands: %s", exc)
        try:
            await call.answer(f"❌ Error: {type(exc).__name__}")
        except Exception:
            pass


@router.callback_query(F.data == "back_start")
async def cb_back_start(call: CallbackQuery) -> None:
    """Return to main menu."""
    try:
        await call.answer()
        await call.message.answer(
            START_CAPTION,
            reply_markup=start_keyboard(),
        )
        logger.info("Returned to start menu for user %s", call.from_user.id)
    except Exception as exc:
        logger.error("Error in cb_back_start: %s", exc)
        try:
            await call.answer(f"❌ Error: {type(exc).__name__}")
        except Exception:
            pass
