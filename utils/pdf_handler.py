import os
import aiofiles
from PyPDF2 import PdfReader
from io import BytesIO


async def save_pdf_file(file_content: bytes, user_id: int, file_name: str) -> str:
    """Сохранить PDF файл на локальный компьютер"""
    files_dir = "downloaded_files"
    os.makedirs(files_dir, exist_ok=True)
    
    # Создаем папку для пользователя
    user_dir = os.path.join(files_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Сохраняем файл
    file_path = os.path.join(user_dir, file_name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return file_path


def validate_pdf(file_content: bytes) -> tuple[bool, str]:
    """Проверить, является ли файл валидным PDF"""
    try:
        pdf_reader = PdfReader(BytesIO(file_content))
        if len(pdf_reader.pages) == 0:
            return False, "PDF файл пустой"
        
        # Пытаемся прочитать первую страницу
        first_page = pdf_reader.pages[0]
        text = first_page.extract_text()
        
        if not text.strip():
            return False, "PDF файл не содержит текста"
        
        return True, "PDF файл валиден"
    except Exception as e:
        return False, f"Ошибка при проверке PDF: {str(e)}"


async def extract_text_from_pdf(file_path: str) -> str:
    """Извлечь текст из PDF файла"""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        raise Exception(f"Ошибка при извлечении текста из PDF: {str(e)}")

