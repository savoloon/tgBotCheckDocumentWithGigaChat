from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import (
    get_all_tariffs, assign_tariff_to_user, get_user, 
    create_tariff, is_admin, get_user_history, get_history_item
)
from keyboards.main_menu import (
    get_main_menu, get_admin_menu, get_tariffs_inline_keyboard,
    get_confirm_tariff_keyboard, get_admin_tariff_keyboard,
    get_history_inline_keyboard, get_cancel_keyboard
)
from states.user_states import UserStates, AdminStates

router = Router()


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    user_id = callback.from_user.id
    admin_status = await is_admin(user_id)
    
    keyboard = get_admin_menu() if admin_status else get_main_menu()
    
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=None
    )
    
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("select_tariff_"))
async def callback_select_tariff(callback: CallbackQuery, state: FSMContext):
    """Выбор тарифа"""
    tariff_id = int(callback.data.split("_")[2])
    
    tariffs = await get_all_tariffs()
    selected_tariff = next((t for t in tariffs if t['id'] == tariff_id), None)
    
    if not selected_tariff:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    await state.update_data(selected_tariff_id=tariff_id)
    await state.set_state(UserStates.selecting_tariff)
    
    text = f"""
🎯 Вы выбрали тариф: **{selected_tariff['name']}**

💰 Стоимость: {selected_tariff['price']} руб.
📊 Количество проверок: {selected_tariff['checks_count']}

Подтвердите выбор тарифа:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_confirm_tariff_keyboard(tariff_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_tariff_"))
async def callback_confirm_tariff(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора тарифа"""
    tariff_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    try:
        await assign_tariff_to_user(user_id, tariff_id)
        
        tariffs = await get_all_tariffs()
        selected_tariff = next((t for t in tariffs if t['id'] == tariff_id), None)
        
        await callback.message.edit_text(
            f"✅ Тариф **{selected_tariff['name']}** успешно активирован!\n\n"
            f"📊 Доступно проверок: {selected_tariff['checks_count']}\n"
            f"💰 Стоимость: {selected_tariff['price']} руб.",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
        admin_status = await is_admin(user_id)
        keyboard = get_admin_menu() if admin_status else get_main_menu()
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка при активации тарифа: {str(e)}", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "cancel_tariff_selection")
async def callback_cancel_tariff_selection(callback: CallbackQuery, state: FSMContext):
    """Отмена выбора тарифа"""
    await state.clear()
    
    user_id = callback.from_user.id
    user = await get_user(user_id)
    current_tariff_id = user.get('id_tarif') if user else None
    
    tariffs = await get_all_tariffs()
    
    if not tariffs:
        await callback.message.edit_text("📦 Тарифы пока не созданы.")
        return
    
    text = "💰 Доступные тарифы:\n\nВыберите тариф для активации:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_tariffs_inline_keyboard(tariffs, current_tariff_id)
    )
    
    await callback.answer()


@router.callback_query(F.data == "admin_create_tariff")
async def callback_admin_create_tariff(callback: CallbackQuery, state: FSMContext):
    """Начало создания тарифа"""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    await state.set_state(AdminStates.creating_tariff_name)
    
    await callback.message.edit_text(
        "➕ Создание нового тарифа\n\n"
        "Введите название тарифа:"
    )
    
    await callback.answer()


@router.callback_query(F.data == "admin_list_tariffs")
async def callback_admin_list_tariffs(callback: CallbackQuery):
    """Список тарифов для администратора"""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    tariffs = await get_all_tariffs()
    
    if not tariffs:
        text = "📦 Тарифы пока не созданы."
    else:
        text = "📋 Список всех тарифов:\n\n"
        for tariff in tariffs:
            text += f"🆔 ID: {tariff['id']}\n"
            text += f"📝 Название: {tariff['name']}\n"
            text += f"💰 Цена: {tariff['price']} руб.\n"
            text += f"📊 Проверок: {tariff['checks_count']}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_tariff_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("select_work_type_"))
async def callback_select_work_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа учебной работы перед загрузкой PDF."""
    user_id = callback.from_user.id
    work_type_id = int(callback.data.split("_")[-1])

    work_type_map = {
        1: "Курсовая работа",
        2: "Дипломная работа",
        3: "Лабораторная работа",
        4: "Реферат",
    }
    work_type = work_type_map.get(work_type_id)

    if not work_type:
        await callback.answer("❌ Тип работы не найден", show_alert=True)
        return
    await state.update_data(selected_work_type=work_type)
    await state.set_state(UserStates.waiting_for_document)

    await callback.message.edit_text(
        f"🎯 Вы выбрали тип работы: {work_type}\n\n"
        "📄 Отправьте PDF файл для проверки.\n"
        "Для отмены используйте /cancel"
    )

    await callback.message.answer(
        "Нажмите кнопку ниже для отмены",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_work_type_selection")
async def callback_cancel_work_type_selection(callback: CallbackQuery, state: FSMContext):
    """Отмена выбора типа работы."""
    await state.clear()
    user_id = callback.from_user.id
    admin_status = await is_admin(user_id)
    keyboard = get_admin_menu() if admin_status else get_main_menu()

    await callback.message.edit_text("❌ Выбор типа работы отменен.", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("view_history_"))
async def callback_view_history_item(callback: CallbackQuery, state: FSMContext):
    """Просмотр детального результата из истории проверок."""
    user_id = callback.from_user.id
    analytics_id = int(callback.data.split("_")[-1])

    item = await get_history_item(user_id, analytics_id)
    if not item or not item.get("responsefromai"):
        await callback.answer("❌ Запись не найдена или нет данных", show_alert=True)
        return

    created_at = item.get("created_at")
    created_text = created_at.strftime("%d.%m.%Y %H:%M") if hasattr(created_at, "strftime") else str(created_at)
    work_type = item.get("work_type") or "Неизвестно"
    status = item.get("status") or "unknown"

    response_text = item.get("responsefromai") or ""
    text = f"📄 Подробный результат\n\nДата: {created_text}\nТип: {work_type}\nСтатус: {status}\n\n{response_text}"

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку истории", callback_data="show_history")]
        ]
    )

    max_length = 4000
    if len(text) > max_length:
        text = text[:max_length - 20] + "\n\n...(обрезано до 4000 символов)..."

    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "show_history")
async def callback_show_history(callback: CallbackQuery, state: FSMContext):
    """Показать список истории проверок."""
    user_id = callback.from_user.id
    history = await get_user_history(user_id, limit=10)
    if not history:
        await callback.message.edit_text("📂 История проверок пуста.", reply_markup=None)
        await callback.answer()
        return

    await callback.message.edit_text(
        "📂 Последние проверки (нажмите на запись для подробного результата):",
        reply_markup=get_history_inline_keyboard(history),
    )
    await callback.answer()
