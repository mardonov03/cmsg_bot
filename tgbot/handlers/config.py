from aiogram.types import Message
from tgbot.models.config import MainModel, UsersModel

async def handle_start(message: Message, **kwargs) -> None:

    usersmodel: UsersModel = kwargs['usersmodel']

    userid = message.from_user.id
    user_data = await usersmodel.get_user(userid)
    if user_data:
        await message.answer(f"Привет, {user_data['username']}! Ваш ID: {userid}.")
    else:
        await message.answer("Добро пожаловать! Вы не зарегистрированы в базе.")
