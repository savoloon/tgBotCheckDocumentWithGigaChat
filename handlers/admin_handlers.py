from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import create_tariff, is_admin
from keyboards.main_menu import get_admin_menu, get_cancel_keyboard
from states.user_states import AdminStates

router = Router()


@router.message(AdminStates.creating_tariff_name)
async def admin_tariff_name(message: Message, state: FSMContext):
    """Обработка ввода названия тарифа"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        await state.clear()
        return
    
    tariff_name = message.text.strip()
    
    if len(tariff_name) < 2:
        await message.answer(
            "❌ Название тарифа слишком короткое. Введите название (минимум 2 символа):",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(tariff_name=tariff_name)
    await state.set_state(AdminStates.creating_tariff_price)
    
    await message.answer(
        f"✅ Название: {tariff_name}\n\n"
        "Введите стоимость тарифа (в рублях):",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminStates.creating_tariff_price)
async def admin_tariff_price(message: Message, state: FSMContext):
    """Обработка ввода цены тарифа"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        await state.clear()
        return
    
    try:
        price = float(message.text.strip())
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены. Введите число (например: 500 или 1500.50):",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(tariff_price=price)
    await state.set_state(AdminStates.creating_tariff_checks)
    
    data = await state.get_data()
    
    await message.answer(
        f"✅ Название: {data['tariff_name']}\n"
        f"✅ Цена: {price} руб.\n\n"
        "Введите количество проверок в тарифе:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminStates.creating_tariff_checks)
async def admin_tariff_checks(message: Message, state: FSMContext):
    """Обработка ввода количества проверок"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора.")
        await state.clear()
        return
    
    try:
        checks_count = int(message.text.strip())
        if checks_count <= 0:
            raise ValueError("Количество проверок должно быть больше 0")
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите целое число больше 0:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    tariff_name = data['tariff_name']
    tariff_price = data['tariff_price']
    
    try:
        tariff_id = await create_tariff(tariff_name, tariff_price, checks_count)
        
        await message.answer(
            f"✅ Тариф успешно создан!\n\n"
            f"🆔 ID: {tariff_id}\n"
            f"📝 Название: {tariff_name}\n"
            f"💰 Цена: {tariff_price} руб.\n"
            f"📊 Проверок: {checks_count}",
            reply_markup=get_admin_menu()
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при создании тарифа: {str(e)}",
            reply_markup=get_admin_menu()
        )
    
    await state.clear()
