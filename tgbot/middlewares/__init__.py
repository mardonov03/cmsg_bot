from aiogram import Router
from aiogram.filters import CommandStart, Command
from tgbot.middlewares.config import MainClass
def setup() -> Router:
    router = Router()

    router.message.register(MainClass.handle_start, CommandStart())

    return router