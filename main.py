import os
from aiogram import Bot, Dispatcher
import asyncio
from tgbot.database.config import create_pool, init_db
from tgbot.business.config import MainClassBusiness, UsersClassBusiness
from tgbot.middlewares.config import MainClass, UsersClass
from tgbot import handlers
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

async def on_startup() -> None:
    pool = await create_pool()
    await init_db(pool)
    dp['pool'] = pool
    global midmain
    global miduser
    businessmain = MainClassBusiness(pool, bot)
    businessuser = UsersClassBusiness(pool, bot)
    midmain = MainClass(businessmain)
    miduser = UsersClass(businessuser)

    await setup_aiogram(dp)

async def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.setup())

async def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(midmain)
    dp.update.middleware(miduser)

async def setup_aiogram(dp: Dispatcher) -> None:
    await setup_handlers(dp)
    await setup_middlewares(dp)

async def main() -> None:
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
