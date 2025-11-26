import aiohttp
import base64
import uuid
import time
from config import (
    GIGACHAT_AUTHORIZATION_KEY,
    GIGACHAT_CLIENT_ID,
    GIGACHAT_CLIENT_SECRET,
    GIGACHAT_SCOPE,
    GIGACHAT_MODEL
)

# Кэш для Access Token
_access_token = None
_token_expires_at = 0


async def get_gigachat_access_token() -> str:
    """Получить Access Token для GigaChat API"""
    global _access_token, _token_expires_at
    
    # Проверяем, есть ли валидный токен в кэше
    if _access_token and time.time() < _token_expires_at:
        return _access_token
    
    # Если Authorization_Key указан, используем его
    if GIGACHAT_AUTHORIZATION_KEY:
        auth_header = f"Basic {GIGACHAT_AUTHORIZATION_KEY}"
    elif GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET:
        # Кодируем Client_ID:Client_Secret в base64
        credentials = f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"
    else:
        raise ValueError("Не указаны GIGACHAT_AUTHORIZATION_KEY или GIGACHAT_CLIENT_ID/GIGACHAT_CLIENT_SECRET")
    
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    # Генерируем уникальный RqUID
    rquid = str(uuid.uuid4())
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rquid,
        'Authorization': auth_header
    }
    
    payload = {
        'scope': GIGACHAT_SCOPE
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ошибка получения токена: {response.status} - {error_text}")
            
            data = await response.json()
            _access_token = data.get('access_token')
            
            if not _access_token:
                raise Exception(f"Не удалось получить access_token: {data}")
            
            # Сохраняем время истечения токена (обычно токен действует 30 минут)
            # В ответе может быть expires_in (секунды) или expires_at (timestamp)
            expires_in = data.get('expires_in', data.get('expires_at', 1800))
            if expires_in > 1000000000:  # Если это timestamp, а не секунды
                _token_expires_at = expires_in - 60
            else:  # Если это секунды до истечения
                _token_expires_at = time.time() + expires_in - 60  # Вычитаем минуту для запаса
            
            return _access_token


async def check_document_with_llm(text: str) -> str:
    """Отправить документ в GigaChat для проверки на ошибки"""
    # Получаем Access Token
    access_token = await get_gigachat_access_token()
    
    prompt = f"""Проверь следующий текст на наличие ошибок:

1. Морфологические ошибки (неправильные формы слов, склонения, спряжения)
2. Синтаксические ошибки (неправильное построение предложений, пунктуация)
3. Логические ошибки (нарушение логики изложения, противоречия)

Текст для проверки:
{text}

Предоставь детальный анализ с указанием:
- Типа ошибки (морфологическая/синтаксическая/логическая)
- Места ошибки (примерный контекст)
- Правильного варианта
- Общей оценки качества текста

Ответ должен быть структурированным и понятным."""
    
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты опытный преподаватель русского языка, специализирующийся на проверке текстов на ошибки."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ошибка при обращении к GigaChat API: {response.status} - {error_text}")
                
                data = await response.json()
                
                # Извлекаем ответ из структуры GigaChat
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0].get('message', {})
                    content = message.get('content', '')
                    if content:
                        return content
                    else:
                        raise Exception(f"Пустой ответ от GigaChat: {data}")
                else:
                    raise Exception(f"Неожиданный формат ответа от GigaChat: {data}")
                    
    except aiohttp.ClientError as e:
        raise Exception(f"Ошибка сети при обращении к GigaChat: {str(e)}")
    except Exception as e:
        raise Exception(f"Ошибка при обращении к LLM: {str(e)}")
