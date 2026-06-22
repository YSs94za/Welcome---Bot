import logging
from aiogram.filters import BaseFilter
from aiogram.types import Message, ChatMemberAdministrator, ChatMemberOwner

logger = logging.getLogger(__name__)


class AdminFilter(BaseFilter):
    """Passes only if the sender is a group admin/owner. Always passes in private."""

    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            return True
        if message.from_user is None:
            return False
        try:
            member = await message.bot.get_chat_member(  # type: ignore[union-attr]
                message.chat.id, message.from_user.id
            )
            return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
        except Exception as exc:
            logger.warning("AdminFilter error chat=%d: %s", message.chat.id, exc)
            return False
