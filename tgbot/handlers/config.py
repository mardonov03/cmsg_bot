from aiogram.types import Message
from tgbot.business.config import UsersClassBusiness

async def handle_start(message: Message, **kwargs) -> None:
    business: UsersClassBusiness = kwargs['business']

    userid = message.from_user.id
    user_data = await business.get_user(userid)
    if user_data:
        await message.answer(f"Привет, {user_data['username']}! Ваш ID: {userid}.")
    else:
        await message.answer("Добро пожаловать! Вы не зарегистрированы в базе.")
