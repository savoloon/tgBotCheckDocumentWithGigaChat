from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния пользователя"""
    waiting_for_document = State()
    viewing_tariffs = State()
    selecting_tariff = State()


class AdminStates(StatesGroup):
    """Состояния администратора"""
    creating_tariff_name = State()
    creating_tariff_price = State()
    creating_tariff_checks = State()
    admin_panel = State()
