from aiogram import BaseMiddleware
from tgbot.models.config import MainModel

class MainClass(BaseMiddleware):
    def __init__(self, models: MainModel):
        super().__init__()
        self.models = models

    async def __call__(self, handler, event, data):
        data['models'] = self.models
        return await handler(event, data)

class UsersClass(MainClass):
    pass