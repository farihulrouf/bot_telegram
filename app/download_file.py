import asyncio
import os
from telethon.sync import TelegramClient

# API credentials and session file path
API_ID = '22346896'
API_HASH = '468c3ff322a27be3a054a4f2c057f177'
PHONE_NUMBER = '+6285280933757'
SESSION_NAME = 'sessions/+6285280933757'

async def test_download_media():
    # Initialize the client with the session file
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    async with client:
        # Make sure to connect
        await client.start(PHONE_NUMBER)

        # Use the correct channel username
        chat_username = '@kopi_dampit'
        
        try:
            chat = await client.get_entity(chat_username)
            messages = await client.get_messages(chat, limit=1)  # Get the latest message
            
            if messages:
                message = messages[0]  # Get the first (and only) message
                if message.media:
                    # Ensure the output directory exists
                    output_dir = os.path.join(os.path.dirname(__file__), '../media/test/')
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)

                    media_path = await client.download_media(message, file=output_dir)
                    print(f"Test media path: {media_path}")
                else:
                    print("No media found in the latest message.")
            else:
                print("No messages found.")
        except ValueError as e:
            print(f"Error: {e}")

# Run the test function
if __name__ == '__main__':
    asyncio.run(test_download_media())
