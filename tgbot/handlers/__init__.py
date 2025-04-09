from aiogram import Router, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR, StateFilter, KICKED
from tgbot.handlers.config import handle_start, on_bot_added, register_creator, handle_stop, select_group, on_bot_deleted, RegisterMessage, CheckMessage, handle_settings, select_group, select_group_1
from tgbot.states.config import UserState

def setup() -> Router:
    router = Router()

    router.message.register(handle_start, Command('start', ignore_mention=True))
    router.message.register(handle_stop, Command('stop', ignore_mention=True))
    router.message.register(handle_settings, Command('settings', ignore_mention=True))
    router.message.register(RegisterMessage.get_message_list, Command('list', ignore_mention=True))
    router.message.register(select_group_1, Command(commands=['add', 'remove'], ignore_mention=True))
    # router.message.register(select_group, (Command(commands=['add', 'remove'], ignore_mention=True) or StateFilter(UserState.select_group_state)))

    router.my_chat_member.register(on_bot_added, ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))

    router.my_chat_member.register(register_creator, ChatMemberUpdatedFilter(ADMINISTRATOR))

    router.my_chat_member.register(on_bot_deleted, ChatMemberUpdatedFilter(IS_NOT_MEMBER or KICKED))

    router.message.register(select_group, StateFilter(UserState.select_group_state))

    router.message.register(RegisterMessage.register_message_add_delete, F.chat.type == "private")

    router.message.register(CheckMessage.check_message, (F.chat.type == "group") | (F.chat.type == "supergroup"))

    return router
