from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📄 Начать проверку документа"))
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="📂 История"))
    builder.add(KeyboardButton(text="💰 Тарифы"))
    builder.add(KeyboardButton(text="ℹ️ Инструкция"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📄 Начать проверку документа"))
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="📂 История"))
    builder.add(KeyboardButton(text="💰 Тарифы"))
    builder.add(KeyboardButton(text="ℹ️ Инструкция"))
    
    builder.add(KeyboardButton(text="🔧 Админ панель"))
    builder.add(KeyboardButton(text="➕ Создать тариф"))
    
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_tariffs_inline_keyboard(tariffs: list, user_current_tariff_id: int = None) -> InlineKeyboardMarkup:
    """Инлайн клавиатура с тарифами"""
    builder = InlineKeyboardBuilder()
    
    for tariff in tariffs:
        text = f"{'✅ ' if tariff['id'] == user_current_tariff_id else ''}{tariff['name']} - {tariff['price']}₽ ({tariff['checks_count']} проверок)"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"select_tariff_{tariff['id']}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)
    
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


def get_work_type_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-выбор типа учебной работы перед загрузкой PDF.

    callback_data формат: select_work_type_<id>
    """
    builder = InlineKeyboardBuilder()
    options = [
        (1, "📘 Курсовая работа"),
        (2, "🎓 Дипломная работа"),
        (3, "🧪 Лабораторная работа"),
        (4, "📄 Реферат"),
    ]

    for work_type_id, label in options:
        builder.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"select_work_type_{work_type_id}",
            )
        )

    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="cancel_work_type_selection",
        )
    )

    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_history_inline_keyboard(history_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Инлайн-список последних проверок.

    Ожидаемые поля в item: analytics_id, created_at, work_type, status
    """
    builder = InlineKeyboardBuilder()
    for item in history_items:
        analytics_id = item.get("analytics_id") or item.get("id")
        if analytics_id is None:
            continue

        created = item.get("created_at")
        if hasattr(created, "strftime"):
            created_text = created.strftime("%d.%m.%Y")
        else:
            created_text = str(created) if created is not None else ""

        work_type = item.get("work_type") or "Неизвестно"
        status = item.get("status") or "unknown"
        status_icon = "✅" if status == "success" else "❌"

        response_preview = (item.get("responseFromAI") or "").strip()
        if response_preview:
            preview_line = response_preview.splitlines()[0].strip()
        else:
            preview_line = ""
        preview_brief = (preview_line[:28] + "...") if len(preview_line) > 28 else preview_line

        text = f"{status_icon} {created_text} • {work_type} — {preview_brief}"
        builder.add(
            InlineKeyboardButton(
                text=text[:60],
                callback_data=f"view_history_{analytics_id}",
            )
        )

    builder.add(
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="back_to_menu",
        )
    )
    builder.adjust(1)
    return builder.as_markup()
