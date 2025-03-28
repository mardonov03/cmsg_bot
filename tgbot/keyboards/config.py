from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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