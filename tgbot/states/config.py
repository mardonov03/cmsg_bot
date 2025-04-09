from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    select_group_state = State()
    get_ban_list_state = State()
    get_ban_list_state_2 = State()

class SettingsState(StatesGroup):
    settngs_select_group_state = State()