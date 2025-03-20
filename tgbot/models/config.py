import logging
import betterlogging as bl

log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
logger = logging.getLogger(__name__)

class MainModel:
    def __init__(self, pool, bot):
        self.pool = pool
        self.bot = bot

class UsersModel(MainModel):
    async def get_user(self, userid):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('SELECT * FROM users WHERE userid = $1', userid)
            if result:
                return {"userid": result["userid"], "username": result["username"]}
            return None

    async def __user_exists(self, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            user_record = await conn.fetch('SELECT userid FROM users WHERE userid = $1', user_id)
            return bool(user_record)
