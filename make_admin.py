import asyncio
import sys
from database import init_db, get_connection


async def make_admin(user_id: int):
    """Назначить пользователя администратором"""
    await init_db()
    
    conn = await get_connection()
    try:
        # Создаем пользователя, если его нет
        await conn.execute(
            "INSERT INTO users (id, isadmin) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
            user_id, 0
        )
        
        # Назначаем администратором
        await conn.execute(
            "UPDATE users SET isadmin = 1 WHERE id = $1",
            user_id
        )
        
        # Проверяем результат
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if row and row["isadmin"] == 1:
            print(f"Пользователь {user_id} успешно назначен администратором!")
        else:
            print(f"Ошибка при назначении администратора для пользователя {user_id}")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python make_admin.py YOUR_TELEGRAM_USER_ID")
        print("Пример: python make_admin.py 123456789")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        asyncio.run(make_admin(user_id))
    except ValueError:
        print("Ошибка: ID пользователя должен быть числом")
        sys.exit(1)
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        sys.exit(1)
