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

    async def get_user_groups(self, userid):
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch('SELECT * FROM groups WHERE creator = $1', userid)
                if results:
                    return {'status': 'ok', 'groups': [{"groupid": row["groupid"], "username": row["username"], "name": row['name'], "creator": row['creator']} for row in results]}
                return {'status': 'no', 'groups': []}
        except Exception as e:
            logging.error(f'get_user_groups error: {e}')
            return {'status': 'error', 'groups': []}


    async def add_creator(self, groupid, userid):
        user = await self.get_user(userid)
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE groups SET creator = $1 WHERE groupid =$2',userid, groupid)
                return True
        except Exception as e:
            logging.error(f'"add_creator error": {e}')

    async def last_group_update(self, groupid, userid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE user_states SET last_group_update = $1 WHERE userid =$2', groupid, userid)
                return True
        except Exception as e:
            logging.error(f'"last_group_update error": {e}')



class GroupModel(MainModel):
    async def add_group(self, groupid):
        try:
            chat = await self.bot.get_chat(groupid)
            username = chat.username if chat.username else None
            name = chat.title

            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO groups (groupid, username, name) VALUES ($1, $2, $3)', groupid, username, name)
                return {'status': 'ok','groupid': groupid, 'username': username, 'name': name}
        except Exception as e:
            logging.error(f'__add_group error: {e}')
            return {'status': 'no', 'groupid': None, 'username': '', 'name': ''}


    async def delete_group(self, groupid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM groups WHERE groupid = $1', groupid)
                return {'status': 'ok'}
        except Exception as e:
            logging.error(f'__add_group error: {e}')
            return {'status': 'no'}

    async def get_group(self, groupid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM groups WHERE groupid = $1', groupid)
            return result
        except Exception as e:
            logging.error(f'"get_user error: {e}')

    async def turn_on_off_bot(self, groupid: int, newstatus: bool):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE group_states SET bot_status =$1 WHERE groupid = $2', newstatus, groupid)
                return newstatus
        except Exception as e:
            logging.error(f'"turn-on_bot error": {e}')

    async def get_bot_status(self, groupid: int):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT bot_status FROM group_states WHERE groupid = $1', groupid)
                return {'status': 'ok', 'bot_status': result}
        except Exception as e:
            logging.error(f'"turn-get_bot_status error": {e}')
            return {'status': 'error', 'bot_status': ''}

    async def is_bot_admin(self, groupid) -> bool:
        try:
            result = await self.bot.get_chat_member(groupid, self.bot.id)
            return result.status in ["administrator", "creator"]
        except Exception as e:
            logging.error(f'"is_bot_admin error": {e}')

    async def is_user_creator(self, groupid, userid):
        try:
            result = await self.bot.get_chat_member(groupid, userid)
            return {'status': 'ok', 'result': result.status}
        except Exception as e:
            logging.error(f'"is_bot_admin error": {e}')
            return {'status': 'error', 'result': ''}

    async def get_bot_privileges(self, groupid) -> dict:
        try:
            chat_member = await self.bot.get_chat_member(groupid, self.bot.id)

            missing_permissions = []
            if not chat_member.can_delete_messages:
                missing_permissions.append("✔️ Удаление сообщений")
            if not chat_member.can_restrict_members:
                missing_permissions.append("✔️ Блокировка пользователей")

            return {'status': 'ok' if not missing_permissions else 'no', 'missed': missing_permissions}

        except Exception as e:
            logging.error(f'"get_bot_privileges error": {e}')
            return {'status': 'error', 'missed': []}

