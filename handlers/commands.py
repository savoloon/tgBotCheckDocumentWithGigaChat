from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import (
    create_user, is_admin, get_user_free_checks, 
    get_all_tariffs, create_tariff, can_user_check_document,
    get_user
)
from keyboards.main_menu import (
    get_main_menu, get_admin_menu, get_tariffs_inline_keyboard,
    get_admin_tariff_keyboard
)
from states.user_states import UserStates, AdminStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()  # Очищаем состояние
    
    user_id = message.from_user.id
    
    # Создаем пользователя, если его нет
    await create_user(user_id)
    
    free_checks = await get_user_free_checks(user_id)
    remaining_free = max(0, 3 - free_checks)
    
    welcome_text = f"""
👋 Добро пожаловать в бота для проверки документов!

📄 Вы можете отправить PDF документ, и я проверю его на:
• Морфологические ошибки
• Синтаксические ошибки  
• Логические ошибки

🎁 У вас осталось бесплатных проверок: {remaining_free}

Используйте кнопки меню для навигации:
"""
    
    # Проверяем, является ли пользователь администратором
    admin_status = await is_admin(user_id)
    keyboard = get_admin_menu() if admin_status else get_main_menu()
    
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

1. Отправьте PDF файл боту для проверки
2. Бот проверит документ на ошибки через AI
3. Вы получите детальный отчет

Команды:
/start - начать работу
/help - эта справка
/tariffs - посмотреть доступные тарифы
/my_stats - моя статистика
/debug_user - проверить свои данные в БД

Для администраторов:
/admin - панель администратора

Для первоначальной настройки:
/make_me_admin - назначить себя админом (только если нет других админов)
"""
    await message.answer(help_text)


@router.message(Command("tariffs"))
async def cmd_tariffs(message: Message, state: FSMContext):
    """Показать доступные тарифы"""
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


@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message):
    """Показать статистику пользователя"""
    user_id = message.from_user.id
    free_checks = await get_user_free_checks(user_id)
    remaining_free = max(0, 3 - free_checks)
    can_check = await can_user_check_document(user_id)
    
    text = f"""
📊 Ваша статистика:

🎁 Бесплатных проверок использовано: {free_checks}/3
🎁 Осталось бесплатных: {remaining_free}

{"✅ Вы можете проверить документ" if can_check else "❌ У вас закончились проверки. Купите тариф!"}

Используйте /tariffs для просмотра доступных тарифов.
"""
    await message.answer(text)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора"""
    user_id = message.from_user.id
    
    # Отладочная информация
    from database import get_user
    user_data = await get_user(user_id)
    print(f"DEBUG: User ID: {user_id}")
    print(f"DEBUG: User data: {user_data}")
    
    admin_status = await is_admin(user_id)
    print(f"DEBUG: Is admin: {admin_status}")
    
    if not admin_status:
        await message.answer(f"❌ У вас нет прав администратора.\nВаш ID: {user_id}\nДанные: {user_data}")
        return
    
    admin_text = """
🔧 Панель администратора:

Команды для создания тарифа:
/create_tariff название|цена|количество_проверок

Пример:
/create_tariff Базовый|500|10

/create_tariff Премиум|1500|50
"""
    await message.answer(admin_text)


@router.message(Command("create_tariff"))
async def cmd_create_tariff(message: Message):
    """Создать новый тариф (только для админов)"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Парсим команду: /create_tariff название|цена|количество
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды.\n"
            "Используйте: /create_tariff название|цена|количество_проверок\n"
            "Пример: /create_tariff Базовый|500|10"
        )
        return
    
    try:
        parts = args[1].split("|")
        if len(parts) != 3:
            raise ValueError
        
        name = parts[0].strip()
        price = float(parts[1].strip())
        checks_count = int(parts[2].strip())
        
        tariff_id = await create_tariff(name, price, checks_count)
        
        await message.answer(
            f"✅ Тариф успешно создан!\n"
            f"ID: {tariff_id}\n"
            f"Название: {name}\n"
            f"Цена: {price} руб.\n"
            f"Проверок: {checks_count}"
        )
    except (ValueError, IndexError):
        await message.answer(
            "❌ Ошибка в формате команды.\n"
            "Используйте: /create_tariff название|цена|количество_проверок\n"
            "Пример: /create_tariff Базовый|500|10"
        )


@router.message(Command("debug_user"))
async def cmd_debug_user(message: Message):
    """Отладочная команда для проверки данных пользователя"""
    user_id = message.from_user.id
    
    # Получаем данные пользователя
    user_data = await get_user(user_id)
    admin_status = await is_admin(user_id)
    
    debug_text = f"""
🔍 Отладочная информация:

👤 Ваш Telegram ID: {user_id}
📊 Данные в БД: {user_data}
👑 Статус администратора: {admin_status}

Если вы должны быть администратором, но статус False, 
проверьте значение поля 'isadmin' в базе данных.
"""
    
    await message.answer(debug_text)


@router.message(Command("make_me_admin"))
async def cmd_make_me_admin(message: Message):
    """Временная команда для назначения себя администратором (только для отладки)"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли уже администраторы
    from database import get_connection
    conn = await get_connection()
    try:
        admin_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE isadmin = 1")
        
        if admin_count == 0:
            # Если нет администраторов, назначаем текущего пользователя
            await conn.execute("UPDATE users SET isadmin = 1 WHERE id = $1", user_id)
            await message.answer(f"✅ Вы назначены администратором! ID: {user_id}")
        else:
            await message.answer("❌ В системе уже есть администраторы. Обратитесь к ним.")
    finally:
        await conn.close()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    
    user_id = message.from_user.id
    admin_status = await is_admin(user_id)
    keyboard = get_admin_menu() if admin_status else get_main_menu()
    
    await message.answer(
        "❌ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=keyboard
    )

