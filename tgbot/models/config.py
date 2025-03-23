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
    async def __add_user(self, userid):
        try:
            user = await self.bot.get_chat(userid)
            username = user.username if user.username else None
            name = user.first_name

            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO users (userid, username, name) VALUES ($1, $2, $3)', userid, username, name)

            return {'userid': userid, 'username': username, 'name': name}

        except Exception as e:
            logging.error(f'__add_user error: {e}')

    async def get_user(self, userid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM users WHERE userid = $1', userid)
                if not result:
                    result = await self.__add_user(userid)
                return {"userid": result["userid"], "username": result["username"], "name": result['name']}
        except Exception as e:
            logging.error(f'"get_user error: {e}')

class GroupModel(MainModel):
    async def add_group(self, groupid):
        try:
            chat = await self.bot.get_chat(groupid)
            username = chat.username if chat.username else None
            name = chat.title

            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO groups (groupid, username, name) VALUES ($1, $2, $3)', groupid, username, name)

            return {'groupid': groupid, 'username': username, 'name': name}

        except Exception as e:
            logging.error(f'__add_group error: {e}')

    async def get_group(self, groupid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM groups WHERE groupid = $1', groupid)
            return result
        except Exception as e:
            logging.error(f'"get_user error: {e}')

    async def turn_on_off_bot(self, groupid, newstatus: bool):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE group_states SET (group_status = $1) WHERE groupid = $2', newstatus, groupid)
        except Exception as e:
            logging.error(f'"turn-on_bot error": {e}')