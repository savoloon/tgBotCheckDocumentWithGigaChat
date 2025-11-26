import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db
from handlers import commands, files, callbacks, menu_handlers, admin_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    await init_db()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Регистрация роутеров (порядок важен!)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(menu_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(files.router)  # Файлы в конце, чтобы не перехватывать другие сообщения
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

