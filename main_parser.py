import os
import time
import asyncio
import nest_asyncio
import requests
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# Применяем nest_asyncio для корректного запуска в синхронной среде (на всякий случай)
nest_asyncio.apply()

# ---------------------------------------------
# 1. СЕКРЕТНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ---------------------------------------------

# Получаем переменные из GitHub Secrets / main.yml
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')
AUTH_CODE_INPUT = os.environ.get('GITHUB_AUTH_CODE', '') # Код авторизации

# Проверка, что ID и HASH присутствуют
if not API_ID or not API_HASH:
    print("FATAL ERROR: API_ID or API_HASH is missing in environment variables.")
    exit(1)


# ---------------------------------------------
# 2. ИНИЦИАЛИЗАЦИЯ КЛИЕНТА
# ---------------------------------------------

# Инициализируем клиента. 'my_session' — имя файла сессии.
client = TelegramClient('my_session', API_ID, API_HASH)


# ---------------------------------------------
# 3. ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КОДА (ИСПРАВЛЕНИЕ EOFError)
# ---------------------------------------------

async def get_auth_code():
    """Получает код авторизации из переменной окружения GITHUB_AUTH_CODE."""
    print("--- ОЖИДАНИЕ КОДА АВТОРИЗАЦИИ ---")
    print("ACTION: Нажмите 'Run workflow' еще раз и вставьте код из Telegram в поле 'auth_code'.")
    
    # Мы даем 120 секунд, чтобы вы успели скопировать и вставить код на GitHub
    for i in range(120):
        # Получаем переменную внутри цикла, чтобы она обновилась при повторном запуске Action
        code = os.environ.get('GITHUB_AUTH_CODE')
        if code:
            print(f"Код получен из переменной окружения. Авторизация...")
            return code
        
        if i % 30 == 0:
             print(f"Прошло {i} секунд. Код не введен. Action завершится через {120 - i} секунд.")
        time.sleep(1)

    raise TimeoutError("Код авторизации не был предоставлен в течение 120 секунд. Скрипт завершен.")


# ---------------------------------------------
# 4. ОСНОВНАЯ ЛОГИКА (ВАШ КОД ПАРСИНГА ЗДЕСЬ)
# ---------------------------------------------

async def run_parser_logic():
    """Ваша логика парсинга и отправки данных Webhook."""
    
    # --- 1. АВТОРИЗАЦИЯ ---
    if not await client.is_user_authorized():
        print("Клиент не авторизован. Инициирую процесс авторизации.")
        try:
            await client.start(
                phone=PHONE_NUMBER, 
                code_callback=get_auth_code # Используем нашу функцию вместо стандартного input()
            )
            print("--- КЛИЕНТ УСПЕШНО АВТОРИЗОВАН! ---")
            # Новый файл my_session.session должен быть создан
        except TimeoutError as e:
            print(f"Ошибка авторизации: {e}")
            exit(1)
        except Exception as e:
            # Сюда попадет, если Telethon прислал код, но не смог его обработать
            print(f"Ошибка авторизации: {e}. Возможно, нужно повторить попытку с новым кодом.")
            exit(1)
    
    print("Клиент авторизован. Начинаю парсинг.")
    
    # --- 2. ВАШ КОД ПАРСИНГА (ПРИМЕР) ---
    # *Вставьте сюда вашу логику получения данных, обработки постов и формирования JSON*
    # 
    # ПРИМЕР:
    # entity = await client.get_entity('t.me/your_channel_name')
    # posts = await client(GetHistoryRequest(
    #     peer=entity,
    #     limit=5,
    #     offset_date=None,
    #     offset_id=0,
    #     max_id=0,
    #     min_id=0,
    #     add_offset=0,
    #     hash=0
    # ))
    #
    # processed_data = []
    # for msg in posts.messages:
    #     processed_data.append({
    #         'title': msg.date.strftime('%Y-%m-%d'),
    #         'text': msg.message[:50],
    #         'url': f"https://t.me/channel_name/{msg.id}"
    #     })
    
    # --- 3. ОТПРАВКА НА WEBHOOK (ПРИМЕР) ---
    # if processed_data and N8N_WEBHOOK_URL:
    #     print(f"Отправка {len(processed_data)} элементов на Webhook...")
    #     response = requests.post(N8N_WEBHOOK_URL, json=processed_data)
    #     print(f"Webhook response status: {response.status_code}")
    # else:
    #     print("Нет новых данных для отправки.")

    await client.run_until_disconnected()


# ---------------------------------------------
# 5. ТОЧКА ВХОДА
# ---------------------------------------------

if __name__ == '__main__':
    # Запускаем асинхронную функцию в синхронном блоке
    with client:
        client.loop.run_until_complete(run_parser_logic())
