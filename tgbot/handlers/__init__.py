from aiogram import Router
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from tgbot.handlers.config import handle_start, on_bot_added

def setup() -> Router:
    router = Router()

    router.message.register(handle_start, Command('start', ignore_mention=True))

    router.chat_member.register(on_bot_added, ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))

    return router
