import logging
import betterlogging as bl
import orjson
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from tgbot import handlers
from tgbot.data import config
from tgbot.database.config import create_pool, init_db
from tgbot.models.config import MainModel, UsersModel, GroupModel

# Конфигурация вебхуков
WEBHOOK_URL = config.WEBHOOK_URL
WEBHOOK_PATH = "/webhook"

dp = Dispatcher(storage=MemoryStorage())


# Настройка логирования
async def setup_logging():
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")


# Настройка обработчиков
async def setup_handlers():
    dp.include_router(handlers.setup())


# Настройка бота
async def setup_bot():
    session = AiohttpSession(json_loads=orjson.loads)
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создание пула соединений с базой
    pool = await create_pool()

    # Инициализация моделей и добавление их в dispatcher
    dp["db"] = pool
    dp["mainmodel"] = MainModel(pool, bot)
    dp["usersmodel"] = UsersModel(pool, bot)
    dp["groupmodel"] = GroupModel(pool, bot)

    # Инициализация базы данных
    await init_db(pool)

    # Установка webhook
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    return bot


# Логика старта и завершения работы приложения с использованием lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Настройка логирования и обработчиков
    await setup_logging()
    await setup_handlers()

    # Инициализация бота и передача его в состояние приложения
    app.state.bot = await setup_bot()
    logging.info("Webhook set")

    # Передаем управление FastAPI
    yield

    # Завершаем работу бота и очистку ресурсов
    await app.state.bot.session.close()
    await dp.storage.close()
    await dp["db"].close()
    logging.info("Bot shutdown")


# Инициализация приложения FastAPI с обработчиком lifespan
app = FastAPI(lifespan=lifespan)


# Роут для получения webhook обновлений
@app.post(WEBHOOK_PATH)
async def receive_update(request: Request):
    data = await request.body()
    update = Update.model_validate_json(data)

    # Обработка обновления в dispatcher
    await dp.feed_update(bot=app.state.bot, update=update)

    # Ответ о успешном получении
    return {"status": "ok"}


# Запуск приложения с использованием uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("webhook:app", host="0.0.0.0", port=8000)
