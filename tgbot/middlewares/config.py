from aiogram import BaseMiddleware
from tgbot.business.config import MainClassBusiness

class MainClass(BaseMiddleware):
    def __init__(self, business: MainClassBusiness):
        super().__init__()
        self.business = business

    async def __call__(self, handler, event, data):
        data['business'] = self.business
        return await handler(event, data)

class UsersClass(MainClass):
    pass