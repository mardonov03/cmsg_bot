from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    select_group_state = State()