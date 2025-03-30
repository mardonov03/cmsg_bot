from aiogram import Router, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR, StateFilter, KICKED
from tgbot.handlers.config import handle_start, on_bot_added, register_creator, handle_stop, select_group, on_bot_deleted, RegisterMessage, CheckMessage
from tgbot.states.config import UserState

def setup() -> Router:
    router = Router()

    router.message.register(handle_start, Command('start', ignore_mention=True))
    router.message.register(handle_stop, Command('stop', ignore_mention=True))

    router.my_chat_member.register(on_bot_added, ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))

    router.my_chat_member.register(register_creator, ChatMemberUpdatedFilter(ADMINISTRATOR))

    router.my_chat_member.register(on_bot_deleted, ChatMemberUpdatedFilter(IS_NOT_MEMBER or KICKED))

    router.message.register(select_group, StateFilter(UserState.select_group_state))

    router.message.register(RegisterMessage.register_message, F.chat.type == "private")

    router.message.register(CheckMessage.check_message, (F.chat.type == "group") | (F.chat.type == "supergroup"))

    return router
