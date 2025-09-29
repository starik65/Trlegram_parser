import os
import json
import asyncio
import requests
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, MessageMediaWebPage, MessageMediaContact

# --- Конфигурация ---
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

# Замените на фактическое имя канала (или ID)
CHANNEL_USERNAME = 't_klych_a' 
BATCH_SIZE = 500  # Разделяем сообщения на пакеты по 500

# --- Функции ---

def clean_message(msg):
    """Преобразует объект сообщения Telethon в чистый словарь JSON."""
    if not msg.message:
        return None # Пропускаем системные сообщения без текста

    data = {
        'message_id': msg.id,
        'channel_id': msg.peer_id.channel_id if hasattr(msg.peer_id, 'channel_id') else None,
        'channel_name': CHANNEL_USERNAME,
        'text': msg.message,
        'date': str(msg.date),
        'has_media': msg.media is not None,
        'media_type': None,
        'file_name': None
    }

    if msg.media:
        data['media_type'] = type(msg.media).__name__
        
        # Обработка документов для получения имени файла
        if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
            for attr in msg.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    data['file_name'] = attr.file_name
                    break
        elif isinstance(msg.media, MessageMediaWebPage) and hasattr(msg.media.webpage, 'site_name'):
            # Для ссылок можно сохранить название сайта или заголовок
            data['file_name'] = msg.media.webpage.site_name
            
    return data

def send_to_webhook(batch):
    """Отправляет пакет сообщений в n8n."""
    if not batch:
        return

    print(f"Отправка пакета из {len(batch)} сообщений в n8n...")
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=batch, # Отправляем список словарей как JSON
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status() # Вызывает исключение для статусов 4xx/5xx
        print(f"Пакет успешно отправлен. Статус: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке пакета в n8n: {e}")

async def main():
    if not all([API_ID, API_HASH, PHONE_NUMBER, N8N_WEBHOOK_URL]):
        print("Ошибка: Отсутствуют необходимые переменные окружения.")
        return

    client = TelegramClient('my_session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)

    print(f"Клиент Telethon запущен. Начинаем парсинг канала {CHANNEL_USERNAME}...")
    
    # --- Логика пакетной обработки и отправки ---
    message_buffer = []
    
    # Используем client.iter_messages для получения сообщений
    # Парсим последние 1000 сообщений для примера
    async for msg in client.iter_messages(CHANNEL_USERNAME, limit=1000): 
        cleaned_data = clean_message(msg)
        
        if cleaned_data:
            message_buffer.append(cleaned_data)
            
            # Если буфер достиг размера пакета, отправляем его
            if len(message_buffer) >= BATCH_SIZE:
                send_to_webhook(message_buffer)
                message_buffer = [] # Очищаем буфер
                
    # Отправляем оставшиеся сообщения, если они есть
    if message_buffer:
        send_to_webhook(message_buffer)

    print("Парсинг завершен. Все сообщения отправлены или обработаны.")
    await client.run_until_disconnected()


if __name__ == '__main__':
    # Очищаем старую сессию, чтобы избежать проблем с авторизацией
    if os.path.exists('my_session.session'):
        os.remove('my_session.session') 
        
    asyncio.run(main())


### ❓ Ваш следующий шаг

1.  **Создайте** файл **`main_parser.py`** в корневой папке вашего репозитория.
2.  **Зафиксируйте (Commit)** это изменение на GitHub.
3.  **Запустите Action** вручную.

**Вы хотите, чтобы я ждал, пока вы зафиксируете файл?**
