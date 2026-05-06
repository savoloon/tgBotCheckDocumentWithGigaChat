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
    
    if _access_token and time.time() < _token_expires_at:
        return _access_token
    
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
            
            expires_in = data.get('expires_in', data.get('expires_at', 1800))
            if expires_in > 1000000000:  
                _token_expires_at = expires_in - 60
            else:  
                _token_expires_at = time.time() + expires_in - 60  
            
            return _access_token


async def check_document_with_llm(text: str, work_type: str) -> str:
    """
    Отправить документ в GigaChat для проверки на ошибки.

    Возвращает структурированный отчет с цветовыми индикаторами эмодзи.
    """
    access_token = await get_gigachat_access_token()
    
    work_type_normalized = (work_type or "").strip()
    work_type_examples = {
        "Курсовая работа": "ожидаются: введение (цель, задачи), теоретическая часть, практическая/аналитическая часть, заключение и список литературы",
        "Дипломная работа": "ожидаются: обоснование актуальности, цель/задачи, научная новизна (если требуется), практическая значимость, анализ результатов, заключение и список литературы",
        "Лабораторная работа": "ожидаются: цель работы, методика/ход работы, результаты измерений/наблюдений, выводы по результатам",
        "Реферат": "ожидаются: структура обзора источников, логика изложения, корректность ссылок/цитирования (если присутствуют), обобщающие выводы",
    }

    work_expectations = work_type_examples.get(work_type_normalized, "учитывай особенности учебной работы выбранного типа")
    
    prompt = f"""
ТЫ ДОЛЖЕН ВОЗВРАТИТЬ ОТЧЕТ В СЛЕДУЮЩЕМ ФОРМАТЕ (строго):

🧾 Отчет по проверке ({work_type_normalized})

1) Актуальность темы: [🟢/🟡/🔴] кратко почему
2) Структура и логика: [🟢/🟡/🔴] кратко, есть ли ввод/цели/задачи/разделы/заключение (или их аналоги для типа работы)
3) Стиль и оформление: [🟢/🟡/🔴] кратко (язык, термины, связность, оформление)

4) Ошибки:
   4.1 Морфологические ошибки: список (каждый пункт начинается с "🟢" или "🟡" или "🔴", затем описание и примерный контекст)
   4.2 Синтаксические ошибки: список (аналогично)
   4.3 Логические ошибки (противоречия/несостыковки): список (аналогично)

5) Рекомендации по доработке: список конкретных шагов (каждый пункт начинается с "🟢"/"🟡"/"🔴")

6) Общий вывод: [🟢/🟡/🔴] краткое резюме (готовность к сдаче и что исправить в первую очередь)

Учитывай тип работы: {work_expectations}.

Текст для проверки:
{text}

Требования:
- Не пиши общие рассуждения без конкретики: давай примеры/фразы из текста (краткий контекст).
- Для каждого типа ошибок включи: описание, примерный контекст и возможный исправленный вариант (если применимо).
- Если ошибок мало, все равно заполни разделы и укажи что соответствует требованиям.
""".strip()
    
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
                "content": "Ты опытный преподаватель русского языка. Твоя задача - проверять тексты учебных работ и формировать структурированный отчет в указанном формате. Используй эмодзи-цвета 🟢/🟡/🔴 строго для оценки уровня проблем."
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
