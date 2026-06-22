import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import developer_keyboard, start_keyboard

logger = logging.getLogger(__name__)
router = Router()

START_GIF = "https://i.postimg.cc/nhH6hs8t/c81f81a024caf4cb16ddfdc7585848c4.gif"
DEV_PHOTO = "https://i.postimg.cc/tgrqP2sW/IMG-20260620-133210-543.jpg"

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
    "<b>Channels (admin only):</b>\n"
    "/add_channel — Add channel (reply to forwarded msg, or send ID/@username)\n"
    "/del_channel <code>&lt;channel_id&gt;</code> — Remove channel\n"
    "/list_channels — List all registered channels\n\n"
    "<b>Placeholders:</b>\n"
    "<code>{name}</code> — Member's full name\n"
    "<code>{chat}</code> — Group name"
)

DEVELOPER_TEXT = (
    "<b>YOUSEF SHAHEEN</b> | Coding the future, beyond the limits of imagination.\n\n"
    "أنا لا أبني مجرد بوتات تليجرام، بل أصيغ حلولاً رقمية ذكية تتنفس الابتكار.\n\n"
    "<i>Engineering excellence</i> بلمسة فنية، لنحول أفكارك إلى واقع automated يسبق زمنه.\n\n"
    "Ready to disrupt? Let's connect:\n\n"
    "📩 @Y9_S4"
)


@router.callback_query(F.data == "developer")
async def cb_developer(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer_photo(  # type: ignore[union-attr]
        photo=DEV_PHOTO,
        caption=DEVELOPER_TEXT,
        reply_markup=developer_keyboard(),
    )


@router.callback_query(F.data == "commands")
async def cb_commands(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer(  # type: ignore[union-attr]
        COMMANDS_TEXT,
        reply_markup=None,
    )


@router.callback_query(F.data == "back_start")
async def cb_back_start(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer_animation(  # type: ignore[union-attr]
        animation=START_GIF,
        caption=START_CAPTION,
        reply_markup=start_keyboard(),
    )
