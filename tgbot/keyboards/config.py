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

def cancel():
    return ReplyKeyboardRemove()

def settings_keyboard(settings: dict):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📜 Логи: {'✅' if settings.get('logs') else '❌'}", callback_data='toggle_logs')],
        [InlineKeyboardButton(text=f"📸 Фото с OpenCV: {'✅' if settings.get('photo_with_opencv') else '❌'}", callback_data='toggle_photo_with_opencv')],
        [InlineKeyboardButton(text=f"🔞 NSFW Пороги: {settings.get('nsfw_prots')}", callback_data='toggle_nsfw_prots')],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data='close_settings')]
    ])
