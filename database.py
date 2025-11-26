import asyncpg
import os
from config import DATABASE_URL
from urllib.parse import urlparse


def parse_database_url(url: str) -> dict:
    """Парсинг строки подключения к PostgreSQL"""
    parsed = urlparse(url)
    params = {
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:] if parsed.path else None,  # Убираем первый слэш
        'host': parsed.hostname,
        'port': parsed.port or 5432
    }
    
    # Обработка дополнительных параметров (например, sslmode)
    if parsed.query:
        query_params = {}
        for param in parsed.query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
        # Добавляем параметры SSL если есть
        if 'sslmode' in query_params:
            sslmode = query_params['sslmode']
            if sslmode == 'require':
                params['ssl'] = True
            elif sslmode == 'disable':
                params['ssl'] = False
            # Для других режимов можно добавить более детальную настройку
    
    return params


async def get_connection():
    """Получить подключение к базе данных"""
    db_params = parse_database_url(DATABASE_URL)
    return await asyncpg.connect(**db_params)


async def init_db():
    """Инициализация базы данных и создание таблиц"""
    conn = await get_connection()
    try:
        # Таблица тарифов
        await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tariffs (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        checks_count INTEGER NOT NULL
                    )
                """)

        # Таблица пользователей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                isadmin INTEGER DEFAULT 0,
                password TEXT,
                id_tarif INTEGER,
                free_checks_used INTEGER DEFAULT 0,
                FOREIGN KEY (id_tarif) REFERENCES tariffs(id)
            )
        """)

        # Таблица файлов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        

        # Таблица аналитики
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                status TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                responseFromAI TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        

        
        print("База данных инициализирована успешно")
    finally:
        await conn.close()


async def get_user(user_id: int):
    """Получить пользователя по ID"""
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None
    finally:
        await conn.close()


async def create_user(user_id: int, is_admin: bool = False):
    """Создать нового пользователя"""
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO users (id, isadmin) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
            user_id, 1 if is_admin else 0
        )
    finally:
        await conn.close()


async def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    user = await get_user(user_id)
    return user and user.get("isadmin") == 1


async def get_user_free_checks(user_id: int) -> int:
    """Получить количество использованных бесплатных проверок"""
    user = await get_user(user_id)
    return user.get("free_checks_used", 0) if user else 0


async def increment_free_checks(user_id: int):
    """Увеличить счетчик бесплатных проверок"""
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE users SET free_checks_used = free_checks_used + 1 WHERE id = $1",
            user_id
        )
    finally:
        await conn.close()


async def get_user_tariff_checks(user_id: int) -> int:
    """Получить количество оставшихся проверок по тарифу"""
    user = await get_user(user_id)
    if not user or not user.get("id_tarif"):
        return 0
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT checks_count FROM tariffs WHERE id = $1",
            user.get("id_tarif")
        )
        if row:
            # Здесь можно добавить логику подсчета использованных проверок
            # Для упрощения возвращаем общее количество
            return row["checks_count"]
    finally:
        await conn.close()
    return 0


async def can_user_check_document(user_id: int) -> bool:
    """Проверить, может ли пользователь проверить документ"""
    free_checks = await get_user_free_checks(user_id)
    if free_checks < 3:  # FREE_CHECKS_LIMIT
        return True
    
    tariff_checks = await get_user_tariff_checks(user_id)
    return tariff_checks > 0


async def save_file(user_id: int, file_path: str, file_name: str) -> int:
    """Сохранить информацию о файле в БД"""
    conn = await get_connection()
    try:
        file_id = await conn.fetchval(
            "INSERT INTO files (user_id, file_path, file_name) VALUES ($1, $2, $3) RETURNING id",
            user_id, file_path, file_name
        )
        return file_id
    finally:
        await conn.close()


async def save_analytics(user_id: int, file_id: int, status: str, response: str = None):
    """Сохранить аналитику проверки"""
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO analytics (user_id, status, file_id, responseFromAI) VALUES ($1, $2, $3, $4)",
            user_id, status, file_id, response
        )
    finally:
        await conn.close()


async def create_tariff(name: str, price: float, checks_count: int) -> int:
    """Создать новый тариф"""
    conn = await get_connection()
    try:
        tariff_id = await conn.fetchval(
            "INSERT INTO tariffs (name, price, checks_count) VALUES ($1, $2, $3) RETURNING id",
            name, price, checks_count
        )
        return tariff_id
    finally:
        await conn.close()


async def get_all_tariffs():
    """Получить все тарифы"""
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM tariffs")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def assign_tariff_to_user(user_id: int, tariff_id: int):
    """Назначить тариф пользователю"""
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE users SET id_tarif = $1 WHERE id = $2",
            tariff_id, user_id
        )
    finally:
        await conn.close()
