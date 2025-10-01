import os
import time
import asyncio 
import nest_asyncio
from telethon import TelegramClient
# Вам нужно добавить сюда импорты для requests и GetHistoryRequest, если они нужны
# import requests 
# from telethon.tl.functions.messages import GetHistoryRequest 

# Применяем nest_asyncio для корректного запуска
nest_asyncio.apply()

# ---------------------------------------------
# 1. СЕКРЕТНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ---------------------------------------------

API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')
AUTH_CODE_INPUT = os.environ.get('GITHUB_AUTH_CODE', '')

if not API_ID or not API_HASH or not PHONE_NUMBER:
    print("FATAL ERROR: API_ID, API_HASH, or PHONE_NUMBER is missing.")
    exit(1)


# ---------------------------------------------
# 2. ИНИЦИАЛИЗАЦИЯ КЛИЕНТА
# ---------------------------------------------

# Инициализируем клиента.
client = TelegramClient('my_session', API_ID, API_HASH)


# ---------------------------------------------
# 3. ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КОДА (ИСПРАВЛЯЕТ EOFError)
# ---------------------------------------------

async def get_auth_code():
    """Получает код авторизации из переменной окружения GITHUB_AUTH_CODE."""
    print("--- ОЖИДАНИЕ КОДА АВТОРИЗАЦИИ ---")
    print("ACTION: Проверьте Telegram, скопируйте код и запустите Action повторно, вставив код в поле 'auth_code'.")
    
    # Даем 120 секунд на ввод кода на GitHub
    for i in range(120):
        code = os.environ.get('GITHUB_AUTH_CODE')
        if code:
            print(f"Код получен: {code}. Выполняю авторизацию...")
            return code
        
        if i % 30 == 0:
             print(f"Прошло {i} секунд. Код не введен.")
        time.sleep(1)

    raise TimeoutError("Код авторизации не был предоставлен в течение 120 секунд. Скрипт завершен.")


# ---------------------------------------------
# 4. ОСНОВНАЯ ЛОГИКА
# ---------------------------------------------

async def run_parser_logic():
    """Основная функция для запуска клиента и парсинга."""
    
    # --- САМЫЙ ПРЯМОЙ ВЫЗОВ START ДЛЯ АВТОРИЗАЦИИ ---
    if not await client.is_user_authorized():
        print("Клиент не авторизован. Инициирую процесс авторизации.")
        try:
            # ПРЯМОЙ ВЫЗОВ client.start() с указанием всех параметров
            await client.start(
                phone=PHONE_NUMBER, 
                code_callback=get_auth_code, # Наша функция для кода
                # НЕ УКАЗЫВАЕМ password, если у вас нет 2FA. Иначе добавьте: password='your_2fa_password'
                is_bot=False
            )
            print("--- КЛИЕНТ УСПЕШНО АВТОРИЗОВАН! ---")
        except TimeoutError as e:
            print(f"Ошибка авторизации (Таймаут): {e}")
            exit(1)
        except Exception as e:
            # Ловит ошибки, включая AuthKeyUnregisteredError и другие ошибки Telethon
            print(f"Критическая ошибка Telethon во время старта: {e}")
            exit(1)
    
    # ----------------------------------------------------------------
    # ВАШ КОД ПАРСИНГА И ОТПРАВКИ ДАННЫХ (вставьте его здесь)
    # ----------------------------------------------------------------
    
    print("Клиент авторизован. Начинаю парсинг.")
    # ... Ваша логика парсинга
    
    
    # В конце, чтобы не завершать скрипт мгновенно (можно удалить, если не нужно)
    # await client.run_until_disconnected() 
    # print("Скрипт завершен.")


if __name__ == '__main__':
    # Запускаем, используя простой run_until_complete (без with client)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.connect())
    loop.run_until_complete(run_parser_logic())
