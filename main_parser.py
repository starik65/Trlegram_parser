import os
import json
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# --- КОНСТАНТЫ И КОНФИГУРАЦИЯ ---
try:
    # Обязательные переменные из GitHub Secrets
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    # Переменные из INPUTS Workflow для авторизации
    AUTH_CODE = os.getenv('AUTH_CODE')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER')

    # Имя файла сессии, который будет создан после успешной авторизации. 
    SESSION_NAME = 'sochi_llm_fresh_session'
    SESSION_FILE = f'{SESSION_NAME}.session'
    
    if not API_ID or not API_HASH:
        raise ValueError("API_ID или API_HASH не найдены в переменных среды.")
        
except Exception as e:
    print(f"ОШИБКА КОНФИГУРАЦИИ: {e}")
    exit(1)


# Список каналов для сбора данных.
CHANNELS = [
    'sochi24tv', 
    'tipich_sochi', 
]
LIMIT = 200
OUTPUT_FILE = 'telegram_data_for_training.jsonl'


def collect_data(client, channels, limit):
    """Собирает сообщения из списка каналов."""
    all_messages = []
    
    for channel_id in channels:
        try:
            print(f"--> Начинаем сбор данных из канала: {channel_id}")
            
            entity = client.get_entity(channel_id)
            
            messages = client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0,
            )).messages
            
            print(f"    Собрано {len(messages)} сообщений.")
            
            for message in messages:
                if message.message and message.id:
                    all_messages.append({
                        'id': message.id,
                        'channel': channel_id,
                        'date': str(message.date),
                        'text': message.message,
                        'views': message.views,
                    })

        except Exception as e:
            print(f"!!! Ошибка при обработке канала {channel_id}: {e}")
            continue

    return all_messages


def save_data(data, filename):
    """Сохраняет данные в формат JSONL (JSON Lines)."""
    print(f"\n--> Сохраняем {len(data)} сообщений в файл {filename}")
    with open(filename, 'a', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print("Сохранение завершено.")


# --- ОСНОВНАЯ ЛОГИКА ---
if __name__ == '__main__':
    client = None
    auth_successful = False
    try:
        print(f"*** НАЧАЛО: АВТОРИЗАЦИЯ И СБОР ДАННЫХ ***")
        
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        # 1. ПЕРВЫЙ ЗАПУСК: Авторизация по коду (только если нет сессии)
        if not os.path.exists(SESSION_FILE):
            print("--- Сессионный файл не найден. Требуется одноразовая авторизация. ---")
            
            if not PHONE_NUMBER:
                raise ValueError("Отсутствует PHONE_NUMBER в входных параметрах Workflow.")

            client.connect()
            
            # А) Запрашиваем код (Telegram отправляет КОД 1)
            print("Отправляем запрос на получение кода...")
            client.send_code_request(PHONE_NUMBER) 
            
            if not AUTH_CODE:
                # Action завершается, чтобы вы успели скопировать Код 1 
                print("\n!!! ПЕРВЫЙ ЭТАП ЗАВЕРШЕН. СКОПИРУЙТЕ КОД ИЗ TELEGRAM И ЗАПУСТИТЕ ACTION ПОВТОРНО, ВВЕДЯ КОД В INPUTS. !!!")
                client.disconnect()
                exit(0)
            
            # Б) Вводим код (это происходит во ВТОРОМ ЗАПУСКЕ)
            print(f"Попытка входа с кодом: {AUTH_CODE}")
            client.sign_in(PHONE_NUMBER, AUTH_CODE)

            # Если sign_in успешен, сессия создана
            auth_successful = True
        
        # 2. ПОСЛЕДУЮЩИЕ ЗАПУСКИ: Используем сохраненную сессию
        if os.path.exists(SESSION_FILE) and not auth_successful:
            client.start() 
            auth_successful = True # Сессия загружена

        
        if auth_successful and client.is_user_authorized():
            print("--- АВТОРИЗАЦИЯ ПРОШЛА УСПЕШНО! ---")
            
            scraped_data = collect_data(client, CHANNELS, LIMIT)
            
            if scraped_data:
                save_data(scraped_data, OUTPUT_FILE)
            else:
                print("Сбор данных завершен, но сообщений не найдено.")
                
        elif not auth_successful:
             print("!!! АВТОРИЗАЦИЯ НЕ УДАЛАСЬ. ПРОВЕРЬТЕ API_HASH ИЛИ УДАЛИТЕ ФАЙЛ СЕССИИ.")
            
    except Exception as e:
        print(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА ВЫПОЛНЕНИЯ: {e}")
        
    finally:
        if client and client.is_connected():
            client.disconnect()
            print("\n*** КОНЕЦ: КЛИЕНТ TELETHON ОТКЛЮЧЕН. ***")
