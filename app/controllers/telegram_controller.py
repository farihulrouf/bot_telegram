import logging
from telethon.errors import SessionPasswordNeededError
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetHistoryRequest
from app.models.telegram_model import PhoneNumber, VerificationCode, create_client, sessions
import asyncio
import os
logging.basicConfig(level=logging.DEBUG)

media_dirs = ['media/photos/', 'media/videos/', 'media/files/']
for media_dir in media_dirs:
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)

async def send_message(phone: str, recipient: str, message: str):
    client = sessions.get(phone)
    if not client:
        raise Exception("Session not found")

    if not client.is_connected():
        await client.connect()

    try:
        if recipient.startswith('@'):
            recipient = recipient[1:]

        entity = await client.get_entity(recipient)
        await client.send_message(entity, message)
        return {"status": "message_sent"}
    except Exception as e:
        raise Exception(f"Failed to send message: {str(e)}")

async def login(phone: PhoneNumber):
    client = create_client(phone.phone)
    await client.connect()

    try:
        await client.send_code_request(phone.phone)
        sessions[phone.phone] = client
        logging.debug(f"Session created and stored for phone: {phone.phone}")
        return {"status": "code_sent"}
    except Exception as e:
        await client.disconnect()
        raise Exception(f"Failed to send code: {str(e)}")

async def verify(code: VerificationCode):
    client = sessions.get(code.phone)
    if not client:
        raise Exception("Session not found")

    if not client.is_connected():
        await client.connect()

    try:
        await client.sign_in(code.phone, code.code)
        if client.is_user_authorized():
            me = await client.get_me()
            logging.debug(f"User logged in: {me}")
            return {"status": "logged_in", "user": me.to_dict()}
        else:
            if code.password:
                await client.sign_in(password=code.password)
                me = await client.get_me()
                logging.debug(f"User logged in with 2FA: {me}")
                return {"status": "logged_in", "user": me.to_dict()}
            else:
                raise Exception("2FA required")
    except SessionPasswordNeededError:
        return {"status": "2fa_required"}
    except Exception as e:
        await client.disconnect()
        raise Exception(f"Failed to verify code: {str(e)}")

    
async def get_channel_messages(phone: str, channel_username: str, limit: int = 10):
    client = sessions.get(phone)
    if not client:
        raise Exception("Session not found")
    logging.debug(f"Session found for phone: {phone}")

    if not client.is_connected():
        await client.connect()

    try:
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]

        entity = await client.get_entity(channel_username)

        messages = await client(GetHistoryRequest(
            peer=entity,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))

        result = []
        for message in messages.messages:
            message_data = {
                "sender_id": message.sender_id,
                "chat_id": message.chat_id,
                "text": message.message if message.message else "",
                "date": message.date.isoformat(),  # Menambahkan tanggal dalam format ISO
                "media": None
            }

            try:
                if message.photo:
                    media_path = await message.download_media(file="media/photos/")
                    logging.debug(f"Downloaded photo to: {media_path}")
                    message_data["media"] = {"type": "photo", "path": media_path}
                elif message.video:
                    media_path = await message.download_media(file="media/videos/")
                    logging.debug(f"Downloaded video to: {media_path}")
                    message_data["media"] = {"type": "video", "path": media_path}
                elif message.document:
                    media_path = await message.download_media(file="media/files/")
                    logging.debug(f"Downloaded document to: {media_path}")
                    message_data["media"] = {"type": "document", "path": media_path}
                elif message.media:
                    media_path = await message.download_media(file="media/files/")
                    logging.debug(f"Downloaded unknown media to: {media_path}")
                    message_data["media"] = {"type": "unknown", "path": media_path}
            except Exception as e:
                logging.error(f"Error downloading media: {e}")
                message_data["media"] = {"type": "error", "path": None}

            result.append(message_data)

        await client.disconnect()
        return {"status": "messages_received", "messages": result}

    except Exception as e:
        await client.disconnect()
        raise Exception(f"Failed to get messages: {str(e)}")