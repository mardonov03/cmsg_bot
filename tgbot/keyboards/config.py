from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import logging

def group_list(list):
    try:
        if not list:
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='отмена')]], resize_keyboard=True)

        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='отмена')]] + [[KeyboardButton(text=f'{i}') for i in list[j:j + 2]] for j in range(0, len(list), 2)], resize_keyboard=True)
    except Exception as e:
        logging.error(f'error652745612: {e}')
        return None

def group_ban_list(list):
    try:
        if not list:
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='отмена')]], resize_keyboard=True)

        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='отмена'), KeyboardButton(text='все')]] + [[KeyboardButton(text=f'{i}') for i in list[j:j + 2]] for j in range(0, len(list), 2)], resize_keyboard=True)
    except Exception as e:
        logging.error(f'error652745612: {e}')
        return None


def cancel():
    return ReplyKeyboardRemove()

def settings_keyboard(settings: dict):
    prots_list = {20: 'строгий', 40: 'средный', 60: 'не строгий'}
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📜 Логи: {'✅' if settings.get('logs') else '❌'}",callback_data=f"toggle_logs_{str(settings.get('logs'))}_gid_{str(settings.get('groupid'))}")],
        [InlineKeyboardButton(text=f"🔞 NSFW: {prots_list[int(settings.get('nsfw_prots'))]}",callback_data=f"toggle_nsfw_prots_{str(settings.get('nsfw_prots'))}_gid_{str(settings.get('groupid'))}")],
        [InlineKeyboardButton(text="❌ Закрыть",callback_data=f"toggle_close_settings_gid_{str(settings.get('groupid'))}")]])


def agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, я согласен", callback_data="agreement_yes"),
            InlineKeyboardButton(text="❌ Нет, я не согласен", callback_data="agreement_no")
        ]
    ])

def cencel_add_or_remove(data):
    chatid = data[0]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_|{chatid}")]
    ])
