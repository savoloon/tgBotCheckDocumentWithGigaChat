import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в .env файле. Формат: postgresql://user:password@host:port/database")

# GigaChat Configuration
GIGACHAT_AUTHORIZATION_KEY = os.getenv("Authorization_Key")
GIGACHAT_CLIENT_ID = os.getenv("Client_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("Client_Secret")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")

# File Storage
FILES_DIR = "downloaded_files"
os.makedirs(FILES_DIR, exist_ok=True)

# Free checks limit
FREE_CHECKS_LIMIT = 3

