import asyncio
import datetime
import logging
import betterlogging as bl

log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
logger = logging.getLogger(__name__)


class Users:
    class Users:
        def __init__(self, db_pool):
            self.pool = db_pool

        async def __user_exists(self, user_id: int) -> bool:
            async with self.pool.acquire() as conn:
                user_record = await conn.fetch('SELECT userid FROM users WHERE userid = $1', user_id)
                return bool(user_record)