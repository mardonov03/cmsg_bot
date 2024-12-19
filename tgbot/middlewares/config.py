from aiogram import BaseMiddleware
from aiogram.types import Message

class MainClass(BaseMiddleware):
    def __init__(self, usermodel):
        self.usermodel = usermodel

    async def handle_start(self, message: Message):
            user_id = message.from_user.id
            user_data = await self.usermodel.get_user(user_id)
            if user_data:
                await message.answer(f"Привет, {user_data['username']}! Ваш ID: {user_id}.")
            else:
                await message.answer("Добро пожаловать! Вы не зарегистрированы в базе.")

class UsersClass(MainClass):
    pass
