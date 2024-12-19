import os
from aiogram import Bot, Dispatcher, types
import asyncio
from tgbot.database.config import create_pool, init_db
from tgbot.business.config import MainClass, UsersClass
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

async def on_startup():
    pool = await create_pool()
    await init_db(pool)
    dp['pool'] = pool
    global mainclass
    global usersclass
    mainclass = MainClass(pool, bot)
    usersclass = UsersClass

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()