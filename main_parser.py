import os
import time
import asyncio
import nest_asyncio
from telethon import TelegramClient

# Применяем nest_asyncio для корректного запуска
nest_asyncio.apply()

# ---------------------------------------------
# 1. СЕКРЕТНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ---------------------------------------------

# Получаем переменные из GitHub Secrets / main.yml
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')

# Код авторизации, который вы вводите вручную
AUTH_CODE_INPUT = os.environ.get('GITHUB_AUTH_CODE', '') 

if not API_ID or not API_HASH or not PHONE_NUMBER:
    print("FATAL ERROR: API_ID, API_HASH, or PHONE_NUMBER is missing.")
    exit(1)


# ---------------------------------------------
# 2. ИНИЦИАЛИЗАЦИЯ КЛИЕНТА
# ---------------------------------------------

client = TelegramClient('my_session', API_ID, API_HASH)


# ---------------------------------------------
# 3. ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КОДА (ИСПРАВЛЯЕТ EOFError)
# ---------------------------------------------

async def get_auth_code():
    """Получает код авторизации из переменной окружения GITHUB_AUTH_CODE."""
    print("--- ОЖИДАНИЕ КОДА АВТОРИЗАЦИИ ---")
    print("ACTION: Проверьте Telegram. Скрипт будет ждать 120 секунд. Запускайте Action повторно с кодом.")
    
    for i in range(1, 121):
        # Перечитываем переменную на случай повторного запуска
        code = os.environ.get('GITHUB_AUTH_CODE')
        if code:
            print(f"Код получен. Авторизация...")
            return code
        
        if i % 30 == 0:
             print(f"Прошло {i} секунд. Код не введен.")
        time.sleep(1)

    # Если таймаут, вызываем ошибку, чтобы Action упал
    raise TimeoutError("Код авторизации не был предоставлен в течение 120 секунд.")


# ---------------------------------------------
# 4. ОСНОВНАЯ ЛОГИКА
# ---------------------------------------------

async def run_parser_logic():
    """Основная функция для запуска клиента и парсинга."""
    
    # --- 1. ПРЯМОЙ ВЫЗОВ START ДЛЯ АВТОРИЗАЦИИ ---
    if not await client.is_user_authorized():
        print("Клиент не авторизован. Инициирую процесс авторизации.")
        try:
            # УБРАЛ is_bot=False и другие лишние аргументы
            await client.start(
                phone=PHONE_NUMBER, 
                code_callback=get_auth_code 
            )
            print("--- КЛИЕНТ УСПЕШНО АВТОРИЗОВАН! ---")
            # Новый файл my_session.session должен быть создан
        except TimeoutError as e:
            print(f"Ошибка авторизации (Таймаут): {e}")
            exit(1)
        except Exception as e:
            # Ловит ошибки, включая AuthKeyUnregisteredError.
            # Если это AuthKeyUnregisteredError, это значит, что Telethon отправил код,
            # но не смог завершить процесс без ввода.
            print(f"Критическая ошибка Telethon во время старта: {e}")
            print("--- ПОЖАЛУЙСТА, ПРОВЕРЬТЕ СВОЙ TELEGRAM. КОД ДОЛЖЕН БЫТЬ ОТПРАВЛЕН. ---")
            exit(1)
            
    # ----------------------------------------------------------------
    # ВАШ КОД ПАРСИНГА И ОТПРАВКИ ДАННЫХ (вставьте его здесь)
    # ----------------------------------------------------------------
    
    print("Клиент авторизован. Начинаю парсинг.")
    
    # ... Ваш код парсинга
    
    # await client.run_until_disconnected() # Опционально


if __name__ == '__main__':
    # Используем with client для правильной обработки соединения
    with client:
        client.loop.run_until_complete(run_parser_logic())
