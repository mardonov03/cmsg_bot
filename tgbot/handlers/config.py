from aiogram.types import Message, ChatMemberUpdated
from tgbot.models.config import UsersModel, GroupModel

async def handle_start(message: Message, **kwargs) -> None:
    if message.chat.type in ['group', 'supergroup']:
        groupid = message.chat.id

        if not message.text.startswith('/start@cleanermsgbot'):
            return

        groupmodel: GroupModel = kwargs['groupmodel']

        result = await groupmodel.get_group(groupid)

        if not result:
            await message.answer('Привет! Я бот помощник, который удаляет нежелательный контент по вашему списку.\n\n''Дайте боту права администратора и нажмите на /start.')
            return

        await message.answer('Бот включен!')

    elif message.chat.type == 'private':
        usersmodel: UsersModel = kwargs['usersmodel']

        userid = message.from_user.id
        user_data = await usersmodel.get_user(userid)

        if user_data:
            await message.answer(f"Привет, {user_data['username']}! Ваш ID: {userid}.")
        else:
            await message.answer("Добро пожаловать! Вы не зарегистрированы в базе.")

async def on_bot_added(event: ChatMemberUpdated) -> None:
    print(2221)
    if event.new_chat_member.status == "member" and event.old_chat_member.status == "left":
        await event.chat.send_message(
            "Привет! Я бот-помощник, который удаляет нежелательный контент по вашему списку.\n\n"
            "Дайте мне права администратора и настройте фильтры!"
        )
