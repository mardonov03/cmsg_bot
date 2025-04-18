import logging
from tgbot.keyboards.config import group_list, cancel, settings_keyboard, agreement_keyboard, group_ban_list
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery
from tgbot.models.config import UsersModel, GroupModel, MessagesModel
from aiogram.fsm.context import FSMContext
from tgbot.states.config import UserState, SettingsState
from datetime import datetime, timedelta

async def handle_start(message: Message, state: FSMContext, **kwargs) -> None:
    if message.chat.type in ['group', 'supergroup']:
        try:
            groupid = message.chat.id

            if not message.text.startswith('/start@PurifyAiBot'):
                return

            groupmodel: GroupModel = kwargs['groupmodel']

            is_bot_admin = await groupmodel.is_bot_admin(groupid)

            if not is_bot_admin:
                await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                return

            permissions = await groupmodel.get_bot_privileges(groupid)

            if permissions['status'] == 'no':
                await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                return

            result = await groupmodel.get_group(groupid)

            if not result:
                await groupmodel.add_group(groupid)

            is_user_creator = await groupmodel.is_user_creator(groupid, message.from_user.id)

            if is_user_creator['result'] == 'creator':

                status = await groupmodel.turn_on_off_bot(groupid, True)

                await message.answer('🟢 Бот включен!' if status is True else '🔴 Бот выключен!')
        except Exception as e:
            logging.error(f'"handle_start error (group):" {e}')

    elif message.chat.type == 'private':
        try:
            usersmodel: UsersModel = kwargs['usersmodel']

            userid = message.from_user.id
            user_data = await usersmodel.get_user(userid)

            user_agreement = await usersmodel.get_user_agreement(userid)

            if user_agreement['mesid']:
                try:
                    await message.bot.delete_message(message.chat.id, user_agreement['mesid'])
                except Exception as e:
                    logging.info(f'info delete_message23255: {e}')

            if not user_agreement['agreement_status']:
                await handle_user_agreement(message, **kwargs)
                return

            user_groups = await usersmodel.get_user_groups(userid)

            if not user_groups or not user_groups['status'] == 'ok':
                await message.answer('У вас пока нет груп')
                return

            await message.answer('Выберите группу для добавления сообщений', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.update_data(action=message.text)
            await state.set_state(UserState.select_group_state)
        except Exception as e:
            logging.error(f'"handle_start error (private): {e}')

async def select_group_1(message:Message, state: FSMContext, **kwargs):
    if message.chat.type == 'private':
        try:
            usersmodel: UsersModel = kwargs['usersmodel']

            userid = message.from_user.id
            user_data = await usersmodel.get_user(userid)

            user_agreement = await usersmodel.get_user_agreement(userid)

            if user_agreement['mesid']:
                try:
                    await message.bot.delete_message(message.chat.id, user_agreement['mesid'])
                except Exception as e:
                    logging.info(f'info delete_message23255: {e}')

            if not user_agreement['agreement_status']:
                await handle_user_agreement(message, **kwargs)
                return

            user_groups = await usersmodel.get_user_groups(userid)

            if not user_groups or not user_groups['status'] == 'ok':
                await message.answer('У вас пока нет груп')
                return

            await message.answer('Выберите группу для добавления сообщений', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.update_data(action=message.text)
            await state.set_state(UserState.select_group_state)
        except Exception as e:
            logging.error(f'"select_group_1 error": {e}')

async def select_group(message:Message, state:FSMContext, **kwargs):
    if message.text == 'отмена':
        await state.clear()
        await message.answer('Вы отменили все действии.', reply_markup=cancel())
        return

    data = await state.get_data()

    g_list = data['g_list']

    selected_group = next((i for i in g_list if i[0] == message.text), None)

    if selected_group:
        groupid = selected_group[1]
        try:
            groupmodel: GroupModel = kwargs['groupmodel']
            is_user_creator = await groupmodel.is_user_creator(selected_group[1], message.from_user.id)

            if not is_user_creator['result'] == 'creator':
                await state.clear()
                await message.answer('Вы уже не являетесь содателем этой группы',reply_markup=cancel())
                return

            is_bot_admin = await groupmodel.is_bot_admin(groupid)

            if not is_bot_admin:
                await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                return

            permissions = await groupmodel.get_bot_privileges(groupid)

            if permissions['status'] == 'no':
                await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                return

            usersmodel: UsersModel = kwargs['usersmodel']

            if data['action'] and data['action']=='/remove':
                action = 'remove'
            else:
                action = 'add'
            restult = await usersmodel.last_group_update(groupid, message.from_user.id, action)
            if restult:
                await message.answer('Группа выбрана удачно', reply_markup=cancel())
            else:
                await message.answer('Нам не удалось выбрать группу', reply_markup=cancel())
            await state.clear()
        except Exception as e:
            logging.error(f'"select_group error": {e}')


async def handle_stop(message: Message, **kwargs) -> None:
    if message.chat.type in ['group', 'supergroup']:
        try:
            groupid = message.chat.id

            if not message.text.startswith('/stop@PurifyAiBot'):
                return

            groupmodel: GroupModel = kwargs['groupmodel']

            is_bot_admin = await groupmodel.is_bot_admin(groupid)

            if not is_bot_admin:
                await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                return

            permissions = await groupmodel.get_bot_privileges(groupid)

            if permissions['status'] == 'no':
                await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                return

            result = await groupmodel.get_group(groupid)

            if not result:
                await groupmodel.add_group(groupid)

            is_user_creator = await groupmodel.is_user_creator(groupid, message.from_user.id)

            if is_user_creator['result'] == 'creator':
                status = await groupmodel.turn_on_off_bot(groupid, False)

                await message.answer('🟢 Бот включен!' if status is True else '🔴 Бот выключен!')
        except Exception as e:
            logging.error(f'"handle_stop error:" {e}')

async def on_bot_added(event: ChatMemberUpdated, **kwargs) -> None:
    try:
        if event.new_chat_member.user.id == event.bot.id:
            groupid = event.chat.id
            groupmodel: GroupModel = kwargs['groupmodel']

            try:
                result = await groupmodel.get_group(groupid)
                if not result:
                    await groupmodel.add_group(groupid)
            except Exception as e:
                logging.error(f'"on_bot_added (add bot to db) error": {e}')

            text = '⚙Привет! я бот помощник, который удаляет нежелательный контент по вашему списку.🤓\n\nМне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей'
            if event.new_chat_member.status == 'administrator':
                permissions = await groupmodel.get_bot_privileges(groupid)

                if permissions['status'] == 'no':
                    text = '⚙Привет! я бот помощник, который удаляет нежелательный контент по вашему списку.🤓\n\nЯ смотрю мне уже дали права администратора)\n\n🛠 Но мне не хватает прав:\n\n' + "\n".join(permissions['missed'])
                else:
                    text = '⚙Привет! я бот помощник, который удаляет нежелательный контент по вашему списку.🤓\n\nЯ смотрю мне уже дали права администратора) приступаю к работе!'
                await register_creator(event, **kwargs)
            await event.bot.send_message(groupid, text)

    except Exception as e:
        logging.error(f'"on_bot_added error": {e}')

async def on_bot_deleted(event: ChatMemberUpdated, **kwargs) -> None:
    try:
        if event.old_chat_member.user.id == event.bot.id:
            groupid = event.chat.id
            groupmodel: GroupModel = kwargs['groupmodel']


            group_data = await groupmodel.get_group(groupid)

            creatorid = group_data['creator']
            groupname = group_data['name']
            if creatorid:
                try:
                    await event.bot.send_message(creatorid, f'❕Бот был удалён из группы (<b>{groupname}</b>).\n\nПоэтому все связанные с ней данные были удалены 👾', parse_mode='HTML')
                except Exception as e:
                    logging.error(f'"on_bot_deleted (send message to creator) error": {e}')

            await groupmodel.delete_group(groupid)

    except Exception as e:
        logging.error(f'"on_bot_deleted error": {e}')

async def register_creator(event: ChatMemberUpdated, **kwargs) -> None:
    try:
        if event.new_chat_member.user.id == event.bot.id:
            groupid = event.chat.id

            try:
                groupmodel: GroupModel = kwargs['groupmodel']

                result = await groupmodel.get_group(groupid)
                if not result:
                    await groupmodel.add_group(groupid)
            except Exception as e:
                logging.error(f'"register_creator (add bot to db) error": {e}')

            admins = await event.bot.get_chat_administrators(groupid)

            creator = next((i for i in admins if i.status == 'creator'), None)

            if not creator:
                await event.bot.send_message(event.chat.id, 'Нам не удалось найти создателья группы.')
                return

            usersmodel: UsersModel = kwargs['usersmodel']

            res = await usersmodel.add_creator(groupid, creator.user.id)

            if not res:
                await event.bot.send_message(event.chat.id, 'Не удалось назначит администратора. Попробуйте заново')
                return
    except Exception as e:
        logging.error(f'"on_bot_added error": {e}')

class CheckMessage():
    @staticmethod
    async def check_message(message: Message, state: FSMContext, bot, **kwargs) -> None:
        groupid = message.chat.id
        userid = message.from_user.id
        try:
            groupmodel: GroupModel = kwargs['groupmodel']
            usersmodel: UsersModel = kwargs['usersmodel']

            is_bot_admin = await groupmodel.is_bot_admin(groupid)

            if not is_bot_admin:
                return

            status = await groupmodel.get_bot_status(groupid)

            if not status['status'] == 'ok' or not status['bot_status']:
                return

            user_privilage = await usersmodel.get_user_privilage(userid, groupid)

            if user_privilage['status'] == 'ok':
                if user_privilage['per_secundes'] is None:
                    return
                given_secundes = user_privilage['per_secundes']
                privilage_given_time = user_privilage['datanow']
                data_now = datetime.now()

                if not (data_now - privilage_given_time > timedelta(seconds=given_secundes)):
                    return

            permissions = await groupmodel.get_bot_privileges(groupid)

            if permissions['status'] == 'no':
                return

            messagesmodel: MessagesModel = kwargs['messagesmodel']

            is_logs_on = await groupmodel.is_logs_on(groupid)

            if message.content_type == 'text':
                result = await messagesmodel.scan_message_text(message.text, groupid)
                if result['status'] == 'ok':
                    if result['is_banned'] == 'ok':
                        await message.bot.delete_message(groupid, message.message_id)
                        if is_logs_on['logs'] is True:
                            await message.bot.send_message(userid, f'Banned word: {str(result["banword"])}', parse_mode='HTML')
                return
            if message.content_type == 'sticker':
                is_banned = await messagesmodel.scan_message_sticker(message.sticker.file_unique_id, message.chat.id)

                if is_banned['status'] == 'ok' and is_banned['is_banned'] == 'ok':
                    await message.bot.delete_message(message.chat.id, message.message_id)
                    if is_logs_on['logs'] is True:
                        await message.bot.send_message(userid, f'Banned sticker id: <b>{is_banned["bansticker"]}</b>', parse_mode='HTML')
                return

            if message.content_type == 'animation':

                is_banned = await messagesmodel.scan_message_animation(message.animation.file_unique_id, message.chat.id)

                if is_banned['status'] == 'ok' and is_banned['is_banned'] == 'ok':
                    await message.bot.delete_message(message.chat.id, message.message_id)
                    if is_logs_on['logs'] is True:
                        await message.bot.send_message(userid, f'Banned gif id: <b>{is_banned["bangif"]}</b>', parse_mode='HTML')
                return

            if message.content_type == 'voice':

                is_banned = await messagesmodel.scan_message_voice(message.voice.file_unique_id, message.chat.id)

                if is_banned['status'] == 'ok' and is_banned['is_banned'] == 'ok':
                    await message.bot.delete_message(message.chat.id, message.message_id)
                    if is_logs_on['logs'] is True:
                        await message.bot.send_message(userid, f'Banned voice id: <b>{is_banned["voice"]}</b>',parse_mode='HTML')
                return

            if message.content_type == 'photo':
                is_banned = await messagesmodel.scan_message_photo(message, message.chat.id)
                if is_banned['status'] == 'ok' and is_banned['message_status'] == 'ban':
                    await message.bot.delete_message(message.chat.id, message.message_id)
                    if is_logs_on['logs'] is True:
                        await message.bot.send_message(userid, f'Banned photo id: <b>{is_banned["message_id"]}</b>', parse_mode='HTML')
                return
        except Exception as e:
            logging.error(f'"check_message error": {e}')


class RegisterMessage():
    @staticmethod
    async def register_message_add_delete(message: Message, state:FSMContext, bot, **kwargs) -> None:
        userid = message.from_user.id
        try:
            if message.chat.type != 'private':
                return

            usersmodel: UsersModel = kwargs['usersmodel']

            groupmodel: GroupModel = kwargs['groupmodel']

            messagesmodel: MessagesModel = kwargs['messagesmodel']

            last_group = await messagesmodel.get_last_group(userid)

            if not last_group['last_group_update']:
                user_groups = await usersmodel.get_user_groups(userid)

                if not user_groups or not user_groups['status'] == 'ok':
                    await message.answer('У вас пока нет груп')
                    return

                await message.answer('Старих данних не нашли пожалюста выберите группу', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
                await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
                await state.update_data(action=message.text)
                await state.set_state(UserState.select_group_state)
                return

            is_user_creator = await groupmodel.is_user_creator(last_group['last_group_update'], message.from_user.id)

            if is_user_creator['result'] == 'creator':
                group = await groupmodel.get_group(last_group['last_group_update'])
                if group['username']:
                    invite_link = f"https://t.me/{group['username']}"
                else:
                    invite_link = await bot.export_chat_invite_link(last_group['last_group_update'])
                action = last_group['action']
                if action == 'remove':
                    if message.content_type == 'text':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.text)

                        if result['status'] == 'ok':
                            await message.answer(f'📄 Слово "<b>{message.text}</b>" <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить слово из запретов.')
                        return

                    elif message.content_type == 'sticker':
                        result= await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.sticker.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🔮 Стикер <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.sticker.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить стикер из запретов.')
                        return

                    elif message.content_type == 'animation':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.animation.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🎞 Гиф <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.animation.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить гиф из запретов.')
                        return

                    elif message.content_type == 'voice':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.voice.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🎙 Голосовое <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.voice.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить голосовое из запретов.')
                        return

                    elif message.content_type == 'document':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.document.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'💾 Документ <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.document.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить документ из запретов.')
                        return

                    elif message.content_type == 'photo':
                        photo = message.photo[-1]
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,photo.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🖼 Фото <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{photo.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить фото из запретов.')
                        return

                    elif message.content_type == 'video':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.video.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'📹 Видео <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить видео из запретов.')
                        return

                    elif message.content_type == 'video_note':
                        result = await messagesmodel.delete_ban_message(last_group['last_group_update'], message.content_type,message.video_note.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'📷 Кружок <b>удалён</b>🗑 из запретов для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video_note.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось удалить кружок из запретов.')
                        return

                else:
                    if message.content_type == 'text':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.text)
                        if result['status'] == 'ok':
                            await message.answer(f'📄 Слово "<b>{message.text}</b>" <b>добавлено</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить слово в запреты.')
                        return

                    elif message.content_type == 'sticker':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.sticker.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🔮 Стикер <b>добавлен</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.sticker.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить стикер в запреты.')
                        return

                    elif message.content_type == 'animation':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.animation.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🎞 Гиф <b>добавлено</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.animation.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить гиф в запреты.')
                        return

                    elif message.content_type == 'voice':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.voice.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🎙 Голосовое <b>добавлено</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.voice.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить голосовое в запреты.')
                        return

                    elif message.content_type == 'document':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.document.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'💾 Документ <b>добавлен</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.document.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить документ в запреты.')
                        return

                    elif message.content_type == 'photo':
                        photo = message.photo[-1]
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, photo.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'🖼 Фото <b>добавлен</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{photo.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить фото в запреты.')
                        return

                    elif message.content_type == 'video':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.video.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'📹 Видео <b>добавлен</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video.file_unique_id}</b>', parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить видео в запреты.')
                        return

                    elif message.content_type == 'video_note':
                        result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type, message.video_note.file_unique_id)
                        if result['status'] == 'ok':
                            await message.answer(f'📷 Кружок <b>добавлен</b>☑️ в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video_note.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await message.answer('❌ Не удалось добавить кружок в запреты.')
                        return
        except Exception as e:
            logging.error(f'"register_message_add_delete error": {e}')


    @staticmethod
    async def get_message_list(message: Message, state:FSMContext, bot, **kwargs) -> None:
        if not message.chat.type == 'private':
            return
        try:
            usersmodel: UsersModel = kwargs['usersmodel']

            userid = message.from_user.id
            user_data = await usersmodel.get_user(userid)

            user_agreement = await usersmodel.get_user_agreement(userid)

            if user_agreement['mesid']:
                try:
                    await message.bot.delete_message(message.chat.id, user_agreement['mesid'])
                except Exception as e:
                    logging.info(f'info delete_message23255: {e}')

            if not user_agreement['agreement_status']:
                await handle_user_agreement(message, **kwargs)
                return

            user_groups = await usersmodel.get_user_groups(userid)

            if not user_groups or not user_groups['status'] == 'ok':
                await message.answer('У вас пока нет груп')
                return

            await message.answer('Выберите группу для добавления сообщений', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.set_state(UserState.get_ban_list_state)
        except Exception as e:
            logging.error(f'"get_message_list error": {e}')

    @staticmethod
    async def get_ban_list(message:Message, state:FSMContext, **kwargs):
        if message.text == 'отмена':
            await state.clear()
            await message.answer('Вы отменили все действии.', reply_markup=cancel())
            return

        data = await state.get_data()

        g_list = data['g_list']

        selected_group = next((i for i in g_list if i[0] == message.text), None)

        groupmodel: GroupModel = kwargs['groupmodel']
        if selected_group:
            groupid = selected_group[1]
            is_user_creator = await groupmodel.is_user_creator(groupid, message.from_user.id)

            if not is_user_creator['result'] == 'creator':
                await state.clear()
                await message.answer('Вы уже не являетесь содателем этой группы',reply_markup=cancel())
                return

            is_bot_admin = await groupmodel.is_bot_admin(groupid)

            if not is_bot_admin:
                await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                return

            permissions = await groupmodel.get_bot_privileges(groupid)

            if permissions['status'] == 'no':
                await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                return


            try:
                action_list = ['текст', 'стикер', 'гиф', 'голосовое', 'документ', 'фото', 'видео', 'видео кружок']
                await message.answer('Список чего вам нужен?', reply_markup=group_ban_list(action_list))
                await state.update_data(action_list=action_list, group_id=groupid, groupname= selected_group[0])
                await state.set_state(UserState.get_ban_list_state_2)
            except Exception as e:
                logging.error(f'"get_ban_list error": {e}')

    @staticmethod
    async def get_ban_list_2(message:Message, state:FSMContext, **kwargs):
        if message.text == 'отмена':
            await state.clear()
            await message.answer('Вы отменили все действии.', reply_markup=cancel())
            return

        data = await state.get_data()

        if not message.text in data['action_list'] and not message.text == 'все':
            action_list = ['текст', 'стикер', 'гиф', 'голосовое', 'документ', 'фото', 'видео', 'видео кружок']
            await message.answer('Неправильная комманда, пожалюста повторите ввод', reply_markup=group_ban_list(action_list))
            await state.set_state(UserState.get_ban_list_state_2)
            return

        action_list_db_form = {'текст': 'text', 'стикер': 'sticker', 'гиф': 'animation', 'голосовое': 'voice', 'документ': 'document', 'фото': 'photo', 'видео': 'video', 'видео кружок': 'video_note', 'все': 'all'}

        action = action_list_db_form[message.text]
        groupid = data['group_id']
        groupname= data['groupname']

        groupmodel: GroupModel = kwargs['groupmodel']

        is_user_creator = await groupmodel.is_user_creator(groupid, message.from_user.id)

        if not is_user_creator['result'] == 'creator':
            await state.clear()
            await message.answer('Вы уже не являетесь создателем этой группы',reply_markup=cancel())
            return

        try:
            ban_list = await groupmodel.get_ban_words(groupid, action)

            sorted_list = sorted(ban_list, key=lambda x: str(x['message_id']))
            chunks = [sorted_list[i:i + 4] for i in range(0, len(sorted_list), 4)]

            text = f'📋Список запрегеных {action} в группе <b>{groupname}</b>:\n\n'
            text += '\n'.join([', '.join(f"<b>{i['message_id']}</b>" for i in chunk) for chunk in chunks])

            await message.answer(text, reply_markup=cancel(), parse_mode='HTML')

            await state.clear()
        except Exception as e:
            logging.error(f'"get_ban_list error": {e}')

class SettingsClass():
    @staticmethod
    async def handle_settings(message: Message, state: FSMContext, **kwargs) -> None:
        groupmodel: GroupModel = kwargs['groupmodel']
        if message.chat.type != 'private':
            if not message.text.startswith('/settings@PurifyAiBot'):
                return

            result = await groupmodel.get_group(message.chat.id)

            if not result:
                await groupmodel.add_group(message.chat.id)

            is_user_creator = await groupmodel.is_user_creator(message.chat.id, message.from_user.id)
            if is_user_creator['result'] != 'creator':
                return

            is_bot_admin = await groupmodel.is_bot_admin(message.chat.id)

            if not is_bot_admin:
                await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                return

            permissions = await groupmodel.get_bot_privileges(message.chat.id)

            if permissions['status'] == 'no':
                await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                return

            usersmodel: UsersModel = kwargs['usersmodel']

            userid = message.from_user.id
            user_data = await usersmodel.get_user(userid)

            user_agreement = await usersmodel.get_user_agreement(userid)

            if user_agreement['mesid']:
                try:
                    await message.bot.delete_message(message.from_user.id, user_agreement['mesid'])
                except Exception as e:
                    logging.info(f'info delete_message63723: {e}')

            if not user_agreement['agreement_status']:
                await handle_user_agreement(message, **kwargs)
                await message.answer("⚙️ <b>Бот временно недоступен</b>\n\nВладелец группы ещё не подтвердил пользовательское соглашение. Пожалуйста, подождите или свяжитесь с ним.",parse_mode="HTML")

                return


            await message.answer('👾 Настроить бота можно только в личном чате. Меню уже отправлено.')

            settings = await groupmodel.get_group_settings(message.chat.id)
            mes = await message.bot.send_message(message.from_user.id ,'Клавиатура убрана.', reply_markup=cancel())
            await message.bot.delete_message(message.from_user.id, mes.message_id)
            await state.clear()
            await message.bot.send_message(message.from_user.id, f'⚙️ Настройки группы: <b>{message.chat.full_name}</b>', reply_markup=settings_keyboard(settings), parse_mode='HTML')
        else:
            usersmodel: UsersModel = kwargs['usersmodel']

            userid = message.from_user.id
            user_data = await usersmodel.get_user(userid)

            user_agreement = await usersmodel.get_user_agreement(userid)

            if user_agreement['mesid']:
                try:
                    await message.bot.delete_message(message.chat.id, user_agreement['mesid'])
                except Exception as e:
                    logging.info(f'info delete_message23255: {e}')

            if not user_agreement['agreement_status']:
                await handle_user_agreement(message, **kwargs)
                return

            user_groups = await usersmodel.get_user_groups(userid)

            if not user_groups or not user_groups['status'] == 'ok':
                await message.answer('У вас пока нет груп')
                return

            await message.answer('Выберите группу для настройки',reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.set_state(SettingsState.settngs_select_group_state)

    @staticmethod
    async def settngs_select_group(message: Message, state: FSMContext, **kwargs):
        if message.text == 'отмена':
            await state.clear()
            await message.answer('Вы отменили все действии.', reply_markup=cancel())
            return

        data = await state.get_data()

        g_list = data['g_list']

        selected_group = next((i for i in g_list if i[0] == message.text), None)

        if selected_group:
            groupid = selected_group[1]
            try:
                groupmodel: GroupModel = kwargs['groupmodel']
                is_user_creator = await groupmodel.is_user_creator(groupid, message.from_user.id)

                if not is_user_creator['result'] == 'creator':
                    await state.clear()
                    await message.answer('Вы уже не являетесь создателем этой группы', reply_markup=cancel())
                    return

                is_bot_admin = await groupmodel.is_bot_admin(groupid)

                if not is_bot_admin:
                    await message.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
                    return

                permissions = await groupmodel.get_bot_privileges(groupid)

                if permissions['status'] == 'no':
                    await message.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
                    return

                settings = await groupmodel.get_group_settings(groupid)
                if settings['status'] == 'ok':
                    mes = await message.answer('Клавиатура убрана.',reply_markup=cancel())
                    await message.bot.delete_message(message.chat.id, mes.message_id)
                    await message.bot.send_message(message.from_user.id, f'⚙️ Настройки группы: <b>{selected_group[0]}</b>',reply_markup=settings_keyboard(settings), parse_mode='HTML')
                await state.clear()
            except Exception as e:
                logging.error(f'"select_group error": {e}')

    @staticmethod
    async def toggle_settings_callback(callback_query: CallbackQuery, **kwargs):
        groupmodel = kwargs['groupmodel']
        setting_name = callback_query.data.replace("toggle_", "")
        group_id = int(callback_query.data.split("gid_")[-1])

        is_user_creator = await groupmodel.is_user_creator(int(callback_query.data.split("gid_")[-1]), callback_query.from_user.id)
        if not is_user_creator['result'] == 'creator':
            await callback_query.message.edit_text('Вы уже не являетесь содателем этой группы', reply_markup=cancel())
            return

        is_bot_admin = await groupmodel.is_bot_admin(group_id)

        if not is_bot_admin:
            await callback_query.answer("🛠 Мне нужны права администратора на:\n\n✔️Удаление сообщений\n✔️Блокировка Пользователей")
            return

        permissions = await groupmodel.get_bot_privileges(group_id)

        if permissions['status'] == 'no':
            await callback_query.answer(f"🛠 Мне не хватает прав:\n\n" + "\n".join(permissions['missed']))
            return


        if setting_name.startswith('close_settings'):
            await callback_query.message.edit_text('✅ Настройки сохранены')
            return

        result = await groupmodel.toggle_setting(group_id, setting_name)

        if result['status'] == 'ok':
            settings = await groupmodel.get_group_settings(group_id)

            await callback_query.message.edit_reply_markup(reply_markup=settings_keyboard(settings))
        else:
            await callback_query.answer("Ошибка при переключении")

async def handle_user_agreement(message: Message, **kwargs):
    try:
        text = ("<b>📜 Пользовательское соглашение</b>\n\nПеред использованием бота, пожалуйста, ознакомьтесь с нашим\n\n🇷🇺 Ru: <b><a href='https://telegra.ph/Polzovatelskoe-Soglashenie-PurifyAi-04-13-2'>Пользовательское Соглашение</a> </b>.\n\n🇺🇸 En: <b><a href='https://telegra.ph/User-Agreement-PurifyAi-04-13'>User Agreement</a> </b>.\n\n🇺🇿 Uz: <b><a href='https://telegra.ph/Foydalanuvchi-Shartnomasi-PurifyAi-04-13'>Foydalanuvchi Shartnomasi</a> </b>.\n\nВы согласны с условиями?")
        mes = await message.bot.send_message(message.from_user.id, text, reply_markup=agreement_keyboard(), parse_mode="HTML", disable_web_page_preview=True)
        usersmodel: UsersModel = kwargs['usersmodel']

        await usersmodel.update_agreement_mesid(message.from_user.id, mes.message_id)
    except Exception as e:
        logging.error(f'"handle_user_agreement error": {e}')

async def handle_user_agreement_selected(callback_query: CallbackQuery, **kwargs):
    userid = callback_query.from_user.id
    selected = callback_query.data.replace('agreement_', '')
    try:

        usersmodel: UsersModel = kwargs['usersmodel']

        if selected == 'yes':
            res = await usersmodel.agreement_yes(userid)
            if res['status'] == 'ok':
                await callback_query.message.edit_text("<b>✅ Вы успешно подтвердили соглашение.</b>\n\nСпасибо за согласие!",parse_mode="HTML")
            else:
                await callback_query.answer("❌ Ошибка: доступ не разрешён. Повторите попытку.",show_alert=True)
        elif selected == 'no':
            await callback_query.message.edit_text("<b>❌ Вы отклонили пользовательское соглашение.</b>\n\nК сожалению, вы не можете использовать бота без согласия.",parse_mode="HTML")
    except Exception as e:
        logging.error(f'"handle_user_agreement_selected error": {e}')
        await callback_query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)