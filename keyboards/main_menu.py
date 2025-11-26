from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    # Основные функции
    builder.add(KeyboardButton(text="📄 Проверить документ"))
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="💰 Тарифы"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    
    # Располагаем кнопки по 2 в ряд
    builder.adjust(2, 2)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    
    # Основные функции
    builder.add(KeyboardButton(text="📄 Проверить документ"))
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="💰 Тарифы"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    
    # Админские функции
    builder.add(KeyboardButton(text="🔧 Админ панель"))
    builder.add(KeyboardButton(text="➕ Создать тариф"))
    
    # Располагаем кнопки
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_tariffs_inline_keyboard(tariffs: list, user_current_tariff_id: int = None) -> InlineKeyboardMarkup:
    """Инлайн клавиатура с тарифами"""
    builder = InlineKeyboardBuilder()
    
    for tariff in tariffs:
        # Добавляем эмодзи для текущего тарифа
        text = f"{'✅ ' if tariff['id'] == user_current_tariff_id else ''}{tariff['name']} - {tariff['price']}₽ ({tariff['checks_count']} проверок)"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"select_tariff_{tariff['id']}"
        ))
    
    # Кнопка назад
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)  # По одной кнопке в ряд
    
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отменить"))
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_admin_tariff_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для админ панели тарифов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="➕ Создать тариф",
        callback_data="admin_create_tariff"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Список тарифов",
        callback_data="admin_list_tariffs"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_confirm_tariff_keyboard(tariff_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения выбора тарифа"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Подтвердить",
        callback_data=f"confirm_tariff_{tariff_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="cancel_tariff_selection"
    ))
    
    builder.adjust(2)
    
    return builder.as_markup()
