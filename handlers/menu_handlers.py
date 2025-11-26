from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import (
    get_user_free_checks, can_user_check_document, get_all_tariffs,
    get_user, is_admin
)
from keyboards.main_menu import (
    get_main_menu, get_admin_menu, get_tariffs_inline_keyboard,
    get_admin_tariff_keyboard, get_cancel_keyboard
)
from states.user_states import UserStates, AdminStates

router = Router()


@router.message(F.text == "📄 Проверить документ")
async def menu_check_document(message: Message, state: FSMContext):
    """Обработчик кнопки 'Проверить документ'"""
    user_id = message.from_user.id
    
    # Проверяем, может ли пользователь проверить документ
    if not await can_user_check_document(user_id):
        await message.answer(
            "❌ У вас закончились бесплатные проверки.\n"
            "Выберите тариф для продолжения работы.",
            reply_markup=get_main_menu()
        )
        return
    
    await state.set_state(UserStates.waiting_for_document)
    
    await message.answer(
        "📄 Отправьте PDF файл для проверки.\n\n"
        "Бот проверит документ на:\n"
        "• Морфологические ошибки\n"
        "• Синтаксические ошибки\n"
        "• Логические ошибки\n\n"
        "Для отмены используйте /cancel",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.text == "📊 Моя статистика")
async def menu_my_stats(message: Message):
    """Обработчик кнопки 'Моя статистика'"""
    user_id = message.from_user.id
    
    user = await get_user(user_id)
    free_checks = await get_user_free_checks(user_id)
    remaining_free = max(0, 3 - free_checks)
    can_check = await can_user_check_document(user_id)
    
    # Информация о тарифе
    tariff_info = "Не активирован"
    if user and user.get('id_tarif'):
        tariffs = await get_all_tariffs()
        current_tariff = next((t for t in tariffs if t['id'] == user['id_tarif']), None)
        if current_tariff:
            tariff_info = f"{current_tariff['name']} ({current_tariff['checks_count']} проверок)"
    
    text = f"""
📊 Ваша статистика:

👤 Telegram ID: {user_id}
🎁 Бесплатных проверок использовано: {free_checks}/3
🎁 Осталось бесплатных: {remaining_free}
💰 Текущий тариф: {tariff_info}

{"✅ Вы можете проверить документ" if can_check else "❌ У вас закончились проверки. Выберите тариф!"}
"""
    
    await message.answer(text)


@router.message(F.text == "💰 Тарифы")
async def menu_tariffs(message: Message, state: FSMContext):
    """Обработчик кнопки 'Тарифы'"""
    await state.clear()
    
    user_id = message.from_user.id
    user = await get_user(user_id)
    current_tariff_id = user.get('id_tarif') if user else None
    
    tariffs = await get_all_tariffs()
    
    if not tariffs:
        await message.answer("📦 Тарифы пока не созданы. Обратитесь к администратору.")
        return
    
    text = "💰 Доступные тарифы:\n\nВыберите тариф для активации:"
    
    await state.set_state(UserStates.viewing_tariffs)
    
    await message.answer(
        text,
        reply_markup=get_tariffs_inline_keyboard(tariffs, current_tariff_id)
    )


@router.message(F.text == "ℹ️ Помощь")
async def menu_help(message: Message):
    """Обработчик кнопки 'Помощь'"""
    help_text = """
📖 Справка по использованию бота:

🔹 **Проверка документов:**
1. Нажмите "📄 Проверить документ"
2. Отправьте PDF файл
3. Получите детальный анализ ошибок

🔹 **Тарифы:**
• 3 бесплатных проверки для каждого пользователя
• Дополнительные проверки по тарифам
• Смена тарифа в любое время

🔹 **Команды:**
/start - главное меню
/cancel - отменить текущее действие
/help - эта справка

🔹 **Что проверяется:**
• Морфологические ошибки
• Синтаксические ошибки
• Логические ошибки и противоречия
"""
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text == "🔧 Админ панель")
async def menu_admin_panel(message: Message, state: FSMContext):
    """Обработчик кнопки 'Админ панель'"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await state.set_state(AdminStates.admin_panel)
    
    text = """
🔧 Панель администратора:

Выберите действие:
"""
    
    await message.answer(
        text,
        reply_markup=get_admin_tariff_keyboard()
    )


@router.message(F.text == "➕ Создать тариф")
async def menu_create_tariff(message: Message, state: FSMContext):
    """Обработчик кнопки 'Создать тариф'"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await state.set_state(AdminStates.creating_tariff_name)
    
    await message.answer(
        "➕ Создание нового тарифа\n\n"
        "Введите название тарифа:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.text == "❌ Отменить")
async def menu_cancel(message: Message, state: FSMContext):
    """Обработчик кнопки 'Отменить'"""
    await state.clear()
    
    user_id = message.from_user.id
    admin_status = await is_admin(user_id)
    keyboard = get_admin_menu() if admin_status else get_main_menu()
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=keyboard
    )
