import logging
from tgbot.keyboards.config import group_list, cancel
from aiogram.types import Message, ChatMemberUpdated
from tgbot.models.config import UsersModel, GroupModel, MessagesModel
from aiogram.fsm.context import FSMContext
from tgbot.states.config import UserState
import opennsfw2 as n2
import os

async def handle_start(message: Message, state: FSMContext, **kwargs) -> None:
    if message.chat.type in ['group', 'supergroup']:
        try:
            groupid = message.chat.id

            if not message.text.startswith('/start@cleanermsgbot'):
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

            user_groups = await usersmodel.get_user_groups(userid)

            if not user_groups or not user_groups['status'] == 'ok':
                await message.answer('У вас пока нет груп')
                return

            await message.answer('Выберите группу', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.set_state(UserState.select_group_state)
        except Exception as e:
            logging.error(f'"handle_start error (private": {e}')

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
            usersmodel: UsersModel = kwargs['usersmodel']

            restult = await usersmodel.last_group_update(groupid, message.from_user.id)
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

            if not message.text.startswith('/stop@cleanermsgbot'):
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
    async def check_message(message: Message) -> None:
        print('check_message')
        print(message.chat.type)


class RegisterMessage():
    @staticmethod
    async def register_message_test(message: Message) -> None:
        print('type:', message.content_type)
        if message.content_type == 'text':
            print('\ntext:', message.text)
        if message.content_type == 'sticker':
            print('sticker:', message.sticker)
            print('sticker:', message.sticker.file_unique_id)
        if message.content_type == 'video':
            print('video:', message.video)
            print('video:', message.video.file_unique_id)
        if message.content_type == 'animation':
            print('animation:', message.animation)
            print('animation:', message.animation.file_unique_id)
        if message.content_type == 'voice':
            print('voice:', message.voice)
            print('voice:', message.voice.file_unique_id)
        if message.content_type == 'document':
            print('document:', message.document)
            print('document:', message.document.file_unique_id)
        if message.content_type == 'photo':
            print('photo:', message.photo)
        if message.content_type == 'video_note':
            print('video_note:', message.video_note)

        if message.content_type == 'photo':
            os.makedirs("photos", exist_ok=True)
            photo = message.photo[-1]
            file_info = await message.bot.get_file(photo.file_id)
            file_path = file_info.file_path

            local_path = f"photos/temp_{photo.file_unique_id}.jpg"
            await message.bot.download_file(file_path, local_path)

            nsfw_probability = n2.predict_image(local_path)

            os.remove(local_path)
            print(f"NSFW: {nsfw_probability:.2%}")
            nsfw, prots = f'{nsfw_probability * 100}'.split('.')
            print(nsfw)
            if int(nsfw) >= 20:
                photo_id = photo.file_unique_id
                await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    ## Бу хаммаси тест учун ози ботта сообщениялани регистрация клнади очрб ташалмили очрш групада болади
        # try:
        #     if event.new_chat_member.user.id == event.bot.id:
        #         groupid = event.chat.id
        #
        #         try:
        #             groupmodel: GroupModel = kwargs['groupmodel']
        #
        #             result = await groupmodel.get_group(groupid)
        #             if not result:
        #                 await groupmodel.add_group(groupid)
        #         except Exception as e:
        #             logging.error(f'"register_creator (add bot to db) error": {e}')
        #
        #         admins = await event.bot.get_chat_administrators(groupid)
        #
        #         creator = next((i for i in admins if i.status == 'creator'), None)
        #
        #         if not creator:
        #             await event.bot.send_message(event.chat.id, 'Нам не удалось найти создателья группы.')
        #             return
        #
        #         usersmodel: UsersModel = kwargs['usersmodel']
        #
        #         res = await usersmodel.add_creator(groupid, creator.user.id)
        #
        #         if not res:
        #             await event.bot.send_message(event.chat.id, 'Не удалось назначит администратора. Попробуйте заново')
        #             return
        # except Exception as e:
        #     logging.error(f'"on_bot_added error": {e}')


    @staticmethod
    async def register_message(message: Message, state:FSMContext, bot, **kwargs) -> None:
        userid = message.from_user.id

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

            await message.answer('старих данних не нашли пожалюста выберите группу', reply_markup=group_list([i['name'] for i in user_groups['groups']]))
            await state.update_data(g_list=[[i['name'], i['groupid']] for i in user_groups['groups']])
            await state.set_state(UserState.select_group_state)
            return

        is_user_creator = await groupmodel.is_user_creator(last_group['last_group_update'], message.from_user.id)

        if is_user_creator['result'] == 'creator':
            group = await groupmodel.get_group(last_group['last_group_update'])
            invite_link = await bot.export_chat_invite_link(last_group['last_group_update'])

            if message.content_type == 'text':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.text)
                if result['status'] == 'ok':
                    await message.answer(f'📄 Слово "<b>{message.text}</b>" добавлено в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить слово в запреты.')
                return

            elif message.content_type == 'sticker':
                result= await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.sticker.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'🔮 Стикер добавлен в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.sticker.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить стикер в запреты.')
                return

            elif message.content_type == 'animation':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.animation.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'🎞 Гиф добавлен в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.animation.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить гиф в запреты.')
                return

            elif message.content_type == 'voice':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.voice.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'🎙 Голосовое добавлено в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.voice.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить голосовое в запреты.')
                return

            elif message.content_type == 'document':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.document.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'💾 Документ добавлен в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.document.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить документ в запреты.')
                return

            elif message.content_type == 'photo':
                photo = message.photo[-1]
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,photo.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'🖼 Фото добавлено в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{photo.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить фото в запреты.')
                return

            elif message.content_type == 'video':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.video.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'📹 Видео добавлено в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить видео в запреты.')
                return

            elif message.content_type == 'video_note':
                result = await messagesmodel.register_ban_message(last_group['last_group_update'], message.content_type,message.video_note.file_unique_id)
                if result['status'] == 'ok':
                    await message.answer(f'📷 Кружок добавлен в запреты для <a href="{invite_link}"><b>{group["name"]}</b></a>.\n\nID: <b>{message.video_note.file_unique_id}</b>',parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await message.answer('❌ Не удалось добавить кружок в запреты.')
                return