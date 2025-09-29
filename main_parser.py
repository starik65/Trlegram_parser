import os
import json
import asyncio
import requests
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, MessageMediaWebPage, MessageMediaContact

# --- Configuration ---
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

# Replace with the actual channel username or ID
CHANNEL_USERNAME = 't_klych_a' 
BATCH_SIZE = 500  # Split messages into batches of 500

# --- Functions ---

def clean_message(msg):
    """Converts a Telethon message object into a clean JSON dictionary."""
    if not msg.message:
        return None 

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
        
        if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
            for attr in msg.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    data['file_name'] = attr.file_name
                    break
        elif isinstance(msg.media, MessageMediaWebPage) and hasattr(msg.media.webpage, 'site_name'):
            data['file_name'] = msg.media.webpage.site_name
            
    return data

def send_to_webhook(batch):
    """Sends a batch of messages to n8n."""
    if not batch:
        return

    print(f"Sending batch of {len(batch)} messages to n8n...")
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=batch, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status() 
        print(f"Batch successfully sent. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending batch to n8n: {e}")

async def main():
    if not all([API_ID, API_HASH, PHONE_NUMBER, N8N_WEBHOOK_URL]):
        print("Error: Required environment variables are missing.")
        return

    client = TelegramClient('my_session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)

    print(f"Telethon client started. Starting to parse channel {CHANNEL_USERNAME}...")
    
    message_buffer = []
    
    # Iterate over the last 1000 messages for testing
    async for msg in client.iter_messages(CHANNEL_USERNAME, limit=1000): 
        cleaned_data = clean_message(msg)
        
        if cleaned_data:
            message_buffer.append(cleaned_data)
            
            if len(message_buffer) >= BATCH_SIZE:
                send_to_webhook(message_buffer)
                message_buffer = [] 
                
    if message_buffer:
        send_to_webhook(message_buffer)

    print("Parsing complete. All messages sent or processed.")
    await client.run_until_disconnected()


if __name__ == '__main__':
    # Clean up old session file to avoid authentication issues
    if os.path.exists('my_session.session'):
        os.remove('my_session.session') 
        
    asyncio.run(main())


### ❓ Ваш следующий шаг

1.  **Замените** содержимое файла **`main_parser.py`** на код выше и **зафиксируйте (Commit)** его на GitHub.
2.  **Запустите Action** вручную.

**Вы хотите, чтобы я ждал, пока вы зафиксируете файл?**
