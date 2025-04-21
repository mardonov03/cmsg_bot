import datetime
import logging
import betterlogging as bl
import os
import opennsfw2 as n2
import re
import itertools


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
                await conn.execute('INSERT INTO user_states (userid) VALUES ($1)', userid)
                await conn.execute('INSERT INTO user_agreement (userid, agreement_status) VALUES ($1, $2)', userid, False)
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

    async def get_user_agreement(self, userid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM user_agreement WHERE userid = $1', userid)
                return {'status': 'ok', 'agreement_status': result['agreement_status'], 'update_time': result['update_time'], 'mesid':result['mesid']}
        except Exception as e:
            logging.error(f'"get_user_agreement error: {e}')
            return {'status': 'no', 'agreement_status': None, 'update_time': None}

    async def agreement_yes(self, userid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE user_agreement SET agreement_status = $1, update_time = $2, mesid = NULL WHERE userid = $3',True, datetime.datetime.now(), userid)
                return {"status": 'ok'}
        except Exception as e:
            logging.error(f'"agreement_yes error: {e}')
            return {"status": 'error'}

    async def update_agreement_mesid(self, userid, mesid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE user_agreement SET mesid = $1 WHERE userid = $2',mesid,userid)
                return {"status": 'ok'}
        except Exception as e:
            logging.error(f'"agreement_mesid error: {e}')
            return {"status": 'error'}


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

    async def last_group_update(self, groupid, userid, action):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("INSERT INTO user_states (userid, last_group_update, action) VALUES ($1, $2, $3) ON CONFLICT (userid) DO UPDATE SET last_group_update = EXCLUDED.last_group_update, action = EXCLUDED.action",userid, groupid, action)
            return True
        except Exception as e:
            logging.error(f'"last_group_update error": {e}')

    async def get_user_privilage(self, userid, groupid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM privilege WHERE groupid = $1 AND userid = $2',groupid, userid)
            if result:
                return {'status': 'ok', 'datanow': result['datanow'], 'per_secundes': result['per_secundes']}
            return {'status': 'no', 'datanow': '', 'per_secundes': ''}
        except Exception as e:
            logging.error(f'"get_user_privilage error": {e}')
            return {'status': 'error'}


class GroupModel(MainModel):
    async def add_group(self, groupid):
        try:
            chat = await self.bot.get_chat(groupid)
            username = chat.username if chat.username else None
            name = chat.title

            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO groups (groupid, username, name) VALUES ($1, $2, $3)', groupid, username, name)
                await conn.execute('INSERT INTO group_states (groupid) VALUES ($1)', groupid)
                await conn.execute('INSERT INTO group_settings (groupid) VALUES ($1)', groupid)
                return {'status': 'ok','groupid': groupid, 'username': username, 'name': name}
        except Exception as e:
            logging.error(f'add_group error: {e}')
            return {'status': 'no', 'groupid': None, 'username': '', 'name': ''}


    async def delete_group(self, groupid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM groups WHERE groupid = $1', groupid)
                return {'status': 'ok'}
        except Exception as e:
            logging.error(f'delete_group error: {e}')
            return {'status': 'error'}

    async def get_group(self, groupid):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT * FROM groups WHERE groupid = $1', groupid)
            return result
        except Exception as e:
            logging.error(f'"get_group error: {e}')

    async def get_ban_words(self, groupid, message_type):
        try:
            async with self.pool.acquire() as conn:
                if message_type != 'all':
                    result = await conn.fetch('SELECT message_id FROM ban_messages WHERE groupid = $1 AND message_type = $2', groupid, message_type)
                else:
                    result = await conn.fetch('SELECT message_id FROM ban_messages WHERE groupid = $1', groupid)
            return result
        except Exception as e:
            logging.error(f'"get_ban_words error": {e}')


    async def turn_on_off_bot(self, groupid: int, newstatus: bool):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO group_states (groupid, bot_status) VALUES ($1, $2) ON CONFLICT (groupid) DO UPDATE SET bot_status = EXCLUDED.bot_status', groupid, newstatus)
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

    async def is_logs_on(self, groupid: int):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT logs FROM group_settings WHERE groupid = $1', groupid)
                return {'status': 'ok', 'logs': result}
        except Exception as e:
            logging.error(f'"turn-is_logs_on error": {e}')
            return {'status': 'error', 'logs': ''}


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
            logging.error(f'"is_user_creator error": {e}')
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

    async def get_group_settings(self, groupid: int):
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('SELECT userid, nsfw_prots, logs FROM group_settings WHERE groupid = $1', groupid)
                return {'status': 'ok', 'userid': result['userid'], 'nsfw_prots': result['nsfw_prots'], 'logs': result['logs'], 'groupid': groupid}
        except Exception as e:
            logging.error(f'"get_group_settings error": {e}')
            return {'status': 'error'}

    async def toggle_setting(self, groupid: int, setting: str):
        try:
            async with self.pool.acquire() as conn:
                setting = setting.split('_gid_')
                setting = setting[0]

                if setting.startswith("logs"):
                    value = setting.replace('logs_', '')

                    new_value = True if value == 'False' else False

                    await conn.execute('UPDATE group_settings SET logs = $1 WHERE groupid = $2', new_value, groupid)

                elif setting.startswith("nsfw_prots"):
                    value = setting.replace('nsfw_prots_', '')

                    if int(value) == 20:
                        new_value = 40
                    elif int(value) == 40:
                        new_value = 60
                    else:
                        new_value = 20
                    await conn.execute('UPDATE group_settings SET nsfw_prots = $1 WHERE groupid = $2', new_value, groupid)

                return {'status': 'ok'}
        except Exception as e:
            logging.error(f'"toggle_setting error": {e}')
            return {'status': 'error'}

class MessagesModel(MainModel):
    lat_to_kir = {'q': ['қ', "к'"], 'w': ['щ', 'ш'], 'e': ['э', 'е'], 'r': ['р'], 't': ['т'],
        'y': ['й', 'е'], 'u': ['у'], 'i': ['и'], 'o': ['о', 'ө'], 'p': ['п'],'a': ['а'],
        's': ['с'], 'd': ['д'], 'f': ['ф'], 'g': ['г', 'ғ'], 'h': ['х'], 'j': ['ж'], 'k': ['к'],'l': ['л'],'z': ['з'],
        'x': ['х'],'c': ['ц'],'v': ['в'],'b': ['б'],'n': ['н'],'m': ['м'],'yo': ['е','ё'],'ya': ['я'],'yu': ['ю']
    }

    kir_to_lat = { 'а': ['a'],'б': ['b'],'в': ['v'],'г': ['g'],'ғ': ['g'],'д': ['d'],'е': ['e', 'yo', 'y'],'ё': ['yo'],'ж': ['j'],
        'з': ['z'],'и': ['i'],'й': ['y'],'к': ['k'],'қ': ['q'],'л': ['l'],'м': ['m'],'н': ['n'],'ң': ['n'],'о': ['o'],'ө': ['o'],
        'п': ['p'],'р': ['r'],'с': ['s'],'т': ['t'],'у': ['u'],'ұ': ['u'],'ү': ['u'],'ф': ['f'],'х': ['h', 'x'],'ц': ['c'],
        'ч': ['c','ch'],'ш': ['w'],'щ': ['w'],'ъ': [],'ы': ['i'],'ь': [],'э': ['e'],'ю': ['yu'],'я': ['ya'], "к'": ['q']
    }

    async def get_last_group(self, userid):
        try:
            async with self.pool.acquire() as conn:
                last_group = await conn.fetchrow('SELECT last_group_update, action FROM user_states WHERE userid = $1', userid)
                return {'status': 'ok', 'last_group_update': last_group['last_group_update'], 'action': last_group['action']}
        except Exception as e:
            logging.error(f'get_last_group error: {e}')
            return {'status': 'error', 'last_group_update': None, 'action': None}

    async def scan_message_text(self, message_text, groupid):
        try:
            async with self.pool.acquire() as conn:
                global_white_rows = await conn.fetch('SELECT message_id FROM global_white_texts')
            if message_text in global_white_rows:
                return

            message_filter = re.sub(r"[^a-zа-яёңұүөқғ\s']", '', message_text.lower())
            message_filter_no_duplicates = re.sub(r'(.)\1+', r'\1', message_filter)

            words = message_filter.split()
            words_no_duplicates = message_filter_no_duplicates.split()

            all_combinations = []
            for word in words + words_no_duplicates:
                all_combinations.extend(self.__get_word_variants(word))

            async with self.pool.acquire() as conn:
                global_ban_rows = await conn.fetch('SELECT message_id FROM global_ban_messages WHERE message_type = $1', "text")
                group_ban_rows = await conn.fetch('SELECT message_id FROM ban_messages WHERE message_type = $1 AND groupid = $2', "text", groupid)

            global_ban_words = {row['message_id'] for row in global_ban_rows}
            group_ban_words = {row['message_id'] for row in group_ban_rows}

            if len(message_text) >= 7 and ' ' not in message_text:
                for banword in global_ban_words:
                    if banword.lower() in words_no_duplicates:
                        return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'is_global': 'ok', 'banword': banword}
                for banword in group_ban_words:
                    if banword.lower() in words_no_duplicates:
                        return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'is_global': 'ok', 'banword': banword}

            for banword in global_ban_words:
                if banword.lower() in all_combinations:
                    return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'is_global': 'no', 'banword': banword}
            for banword in group_ban_words:
                if banword.lower() in all_combinations:
                    return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'is_global': 'no', 'banword': banword}

            return {'status': 'ok', 'groupid': groupid,'is_banned': 'no', 'is_global': None,'banword': None}

        except Exception as e:
            logging.error(f'"scan_message_text error": {e}')
            return {'status': 'error', 'groupid': groupid,'is_banned': '', 'is_global': '', 'banword': ''}

    async def scan_message_sticker(self, sticker_id, groupid):
        try:
            async with self.pool.acquire() as conn:
                group_ban_stickers = await conn.fetch('SELECT message_id FROM ban_messages WHERE message_type = $1 AND groupid = $2', "sticker", groupid)

                if sticker_id in [record['message_id'] for record in group_ban_stickers]:
                    return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'bansticker': sticker_id}
                return {'status': 'ok', 'groupid': groupid, 'is_banned': 'no', 'bansticker': ''}
        except Exception as e:
            logging.error(f'"scan_message_sticker error": {e}')
            return {'status': 'error', 'groupid': groupid,'is_banned': '', 'bansticker': ''}

    async def scan_message_animation(self, gif_id, groupid):
        try:
            async with self.pool.acquire() as conn:
                group_ban_stickers = await conn.fetch('SELECT message_id FROM ban_messages WHERE message_type = $1 AND groupid = $2', "animation", groupid)

                if gif_id in [record['message_id'] for record in group_ban_stickers]:
                    return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'bangif': gif_id}
                return {'status': 'ok', 'groupid': groupid, 'is_banned': 'no', 'bangif': ''}
        except Exception as e:
            logging.error(f'"scan_message_animation error": {e}')
            return {'status': 'error', 'groupid': groupid,'is_banned': '', 'bangif': ''}

    async def scan_message_voice(self, voice_id, groupid):
        try:
            async with self.pool.acquire() as conn:
                group_ban_stickers = await conn.fetch('SELECT message_id FROM ban_messages WHERE message_type = $1 AND groupid = $2', "voice", groupid)

                if voice_id in [record['message_id'] for record in group_ban_stickers]:
                    return {'status': 'ok', 'groupid': groupid, 'is_banned': 'ok', 'voice': voice_id}
                return {'status': 'ok', 'groupid': groupid, 'is_banned': 'no', 'voice': ''}
        except Exception as e:
            logging.error(f'"scan_message_voice error": {e}')
            return {'status': 'error', 'groupid': groupid,'is_banned': '', 'voice': ''}


    def __get_word_variants(self, word):
        parsed_letters = []
        skip = False
        for i in range(len(word)):
            if skip:
                skip = False
                continue
            if i + 1 < len(word) and word[i + 1] == "'" and word[i] == 'к':
                parsed_letters.append(word[i] + "'")
                skip = True
            else:
                parsed_letters.append(word[i])

        variants_per_letter = []
        for letter in parsed_letters:
            if letter in self.kir_to_lat:
                variants = self.kir_to_lat[letter] + [letter]
                variants_per_letter.append(variants)
            elif letter in 'abcdefghijklmnopqrstuvwxyz':
                lat_to_kir = [k for k, v in self.kir_to_lat.items() if letter in v]
                variants = [letter] + lat_to_kir
                variants_per_letter.append(variants)
            else:
                variants_per_letter.append([''])

        return [''.join(comb) for comb in itertools.product(*variants_per_letter)]

    async def scan_message_photo(self, message, groupid):
        photo = message.photo[-1]
        photo_id = photo.file_unique_id

        if message.caption:
            await self.scan_message_text(message.caption, groupid)

        is_banned_global = await self.__check_global(photo_id, 'photo')

        try:
            if is_banned_global['status'] == 'ok' and is_banned_global['is_banned'] is True:
                return {'status': 'ok', 'message_status': 'ban', 'is_global': 'ok', 'groupid': groupid, 'message_id': photo.file_unique_id}

            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT 1 FROM ban_messages WHERE groupid = $1 AND message_type =$2 AND message_id = $3', groupid, message.content_type, photo_id)

                if result:
                    return {'status': 'ok', 'message_status': 'ban', 'is_global': 'no', 'groupid': groupid, 'message_id': photo.file_unique_id}
                nsfw_prots_group = await conn.fetchval('SELECT nsfw_prots FROM group_settings WHERE groupid = $1', groupid)

            os.makedirs("photos", exist_ok=True)
            file_info = await message.bot.get_file(photo.file_id)

            file_path = file_info.file_path

            local_path = f"photos/temp_{photo.file_unique_id}.jpg"
            await message.bot.download_file(file_path, local_path)

            nsfw_probability = n2.predict_image(local_path)

            os.remove(local_path)
            nsfw, prots = f'{nsfw_probability * 100}'.split('.')
            print(int(nsfw))
            if int(nsfw) >= 60:
                async with self.pool.acquire() as conn:
                    await conn.execute('INSERT INTO global_ban_messages (message_id, message_type) VALUES ($1, $2) ON CONFLICT (message_id, message_type) DO NOTHING', photo_id, 'photo')
                return {'status': 'ok', 'message_status': 'ban', 'is_global': 'ok', 'groupid': groupid, 'message_id': photo.file_unique_id}

            elif int(nsfw) >= nsfw_prots_group:
                async with self.pool.acquire() as conn:
                    await conn.execute('INSERT INTO ban_messages (groupid, message_id, message_type) VALUES ($1, $2, $3) ON CONFLICT (groupid, message_id, message_type) DO NOTHING', groupid, photo_id, 'photo')
                return {'status': 'ok', 'message_status': 'ban', 'is_global': 'no', 'groupid': groupid, 'message_id': photo.file_unique_id}
            return {'status': 'ok', 'message_status': 'not_ban', 'is_global': 'no', 'groupid': groupid, 'message_id': photo.file_unique_id}
        except Exception as e:
            logging.error(f'scan_message_text error: {e}')
            return {'status': 'error', 'message_status': '', 'is_global': '', 'groupid': '', 'message_id': ''}

    async def __check_global(self, message_id, message_type):
        try:
            async with self.pool.acquire() as conn:
                res = await conn.fetchval('SELECT 1 FROM global_ban_messages WHERE message_id = $1 AND message_type = $2', message_id, message_type)
            if res:
                is_banned = True
            else:
                is_banned = False
            return {'status': 'ok', 'is_banned': is_banned}
        except Exception as e:
            logging.error(f'"error": {e}')
            return {'status': 'error', 'is_banned': False}

    async def register_ban_message(self, groupid, message_type, file_id):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO ban_messages (groupid, message_id, message_type) VALUES ($1, $2, $3) ON CONFLICT (groupid, message_id, message_type) DO NOTHING', groupid, file_id, message_type)
            return {'status': 'ok', 'groupid': groupid, 'file_id': file_id, 'message_type': message_type}
        except Exception as e:
            logging.error(f'register_ban_message error: {e}')
            return {'status': 'error', 'groupid': None, 'file_id': None, 'message_type': None}

    async def delete_ban_message(self, groupid, message_type, file_id):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM ban_messages WHERE groupid = $1 AND message_id =$2 AND message_type=$3', groupid, file_id, message_type)
            return {'status': 'ok', 'groupid': groupid, 'file_id': file_id, 'message_type': message_type}
        except Exception as e:
            logging.error(f'delete_ban_message error: {e}')
            return {'status': 'error', 'groupid': None, 'file_id': None, 'message_type': None}

    async def add_message_cancel(self, groupid, file_id, content_type, action, mesid, userid):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO message_cancel (groupid, content_type, file_id, action, mesid, userid) VALUES ($1, $2, $3, $4, $5, $6)', groupid, content_type, file_id, action, mesid, userid)
            return {'status': 'ok', 'groupid': groupid, 'content_type': content_type, 'file_id': file_id, 'action': action}
        except Exception as e:
            logging.error(f'add_message_cancel error: {e}')
            return {'status': 'error', 'groupid': None, 'content_type': None, 'file_id': None, 'action': None}

    async def get_cancel_data(self, userid, mesid):
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT groupid, content_type, file_id, action FROM message_cancel WHERE mesid = $1 AND userid = $2', mesid, userid)
            if row:
                return {'status': 'ok', 'groupid': row['groupid'], 'content_type': row['content_type'],
                        'file_id': row['file_id'], 'action': row['action']}
            return {'status': 'empty', 'groupid': None, 'content_type': None, 'file_id': None, 'action': None}
        except Exception as e:
            logging.error(f'get_cancel_data error: {e}')
            return {'status': 'error', 'groupid': None, 'content_type': None, 'file_id': None, 'action': None}
