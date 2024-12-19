from aiogram import Router
from aiogram.filters import CommandStart
from tgbot.handlers.config import handle_start

def setup() -> Router:
    router = Router()

    router.message.register(handle_start, CommandStart())

    return router
