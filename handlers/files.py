from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import os
import aiofiles
import aiohttp
from database import (
    create_user, can_user_check_document, get_user_free_checks,
    increment_free_checks, save_file, save_analytics, is_admin
)
from utils.pdf_handler import save_pdf_file, validate_pdf, extract_text_from_pdf
from utils.llm_handler import check_document_with_llm
from keyboards.main_menu import get_main_menu, get_admin_menu
from states.user_states import UserStates

router = Router()


@router.message(F.document, UserStates.waiting_for_document)
async def handle_document(message: Message, state: FSMContext):
    """Обработчик отправки документа"""
    user_id = message.from_user.id
    
    # Создаем пользователя, если его нет
    await create_user(user_id)
    
    # Проверяем, может ли пользователь проверить документ
    if not await can_user_check_document(user_id):
        await message.answer(
            "❌ У вас закончились бесплатные проверки.\n"
            "Используйте /tariffs для просмотра доступных тарифов."
        )
        return
    
    # Проверяем, что это PDF
    document = message.document
    if not document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ Пожалуйста, отправьте PDF файл.")
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer("⏳ Обрабатываю документ...")
    
    try:
        # Подготавливаем путь для сохранения файла
        files_dir = "downloaded_files"
        os.makedirs(files_dir, exist_ok=True)
        user_dir = os.path.join(files_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, document.file_name)
        
        # Получаем информацию о файле
        file = await message.bot.get_file(document.file_id)
        # Получаем URL файла через Telegram API
        from config import BOT_TOKEN
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        
        # Скачиваем файл напрямую через HTTP
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    file_bytes = await response.read()
                    # Сохраняем файл
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(file_bytes)
                else:
                    raise Exception(f"Не удалось скачать файл. Статус: {response.status}")
        
        # Валидируем PDF
        is_valid, error_msg = validate_pdf(file_bytes)
        if not is_valid:
            await processing_msg.edit_text(f"❌ {error_msg}")
            # Удаляем невалидный файл
            try:
                os.remove(file_path)
            except:
                pass
            return
        
        # Сохраняем информацию о файле в БД
        file_id = await save_file(user_id, file_path, document.file_name)
        
        # Извлекаем текст из PDF
        await processing_msg.edit_text("📄 Извлекаю текст из PDF...")
        text = await extract_text_from_pdf(file_path)
        
        if not text.strip():
            await processing_msg.edit_text("❌ Не удалось извлечь текст из PDF.")
            await save_analytics(user_id, file_id, "error", "Не удалось извлечь текст")
            return
        
        # Отправляем в LLM
        await processing_msg.edit_text("🤖 Проверяю документ через AI...")
        response = await check_document_with_llm(text)
        
        # Увеличиваем счетчик бесплатных проверок
        free_checks = await get_user_free_checks(user_id)
        if free_checks < 3:
            await increment_free_checks(user_id)
        
        # Сохраняем аналитику
        await save_analytics(user_id, file_id, "success", response)
        
        # Отправляем результат пользователю
        result_text = f"✅ Проверка завершена!\n\n{response}"
        
        # Разбиваем на части, если сообщение слишком длинное
        max_length = 4000
        if len(result_text) > max_length:
            parts = [result_text[i:i+max_length] for i in range(0, len(result_text), max_length)]
            await processing_msg.edit_text(parts[0])
            for part in parts[1:]:
                await message.answer(part)
        else:
            await processing_msg.edit_text(result_text)
        
        # Обновляем статистику
        new_free_checks = await get_user_free_checks(user_id)
        remaining = max(0, 3 - new_free_checks)
        await message.answer(f"📊 Осталось бесплатных проверок: {remaining}/3")
        
        # Возвращаем в главное меню
        await state.clear()
        admin_status = await is_admin(user_id)
        keyboard = get_admin_menu() if admin_status else get_main_menu()
        await message.answer("Выберите действие:", reply_markup=keyboard)
        
    except Exception as e:
        error_msg = f"❌ Произошла ошибка при обработке документа: {str(e)}"
        await processing_msg.edit_text(error_msg)
        
        # Сохраняем ошибку в аналитику
        if 'file_id' in locals():
            await save_analytics(user_id, file_id, "error", str(e))
        
        # Возвращаем в главное меню при ошибке
        await state.clear()
        admin_status = await is_admin(user_id)
        keyboard = get_admin_menu() if admin_status else get_main_menu()
        await message.answer("Выберите действие:", reply_markup=keyboard)


@router.message(F.photo)
async def handle_photo(message: Message):
    """Обработчик отправки фото (не PDF)"""
    await message.answer("❌ Пожалуйста, отправьте PDF файл, а не изображение.")


@router.message()
async def handle_other_messages(message: Message, state: FSMContext):
    """Обработчик остальных сообщений"""
    current_state = await state.get_state()
    
    if current_state == UserStates.waiting_for_document:
        await message.answer(
            "📄 Пожалуйста, отправьте PDF файл для проверки.\n"
            "Для отмены используйте /cancel"
        )
    else:
        await message.answer(
            "Используйте кнопки меню для навигации или команду /help для справки."
        )

