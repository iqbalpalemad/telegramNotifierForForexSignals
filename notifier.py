from telethon.tl.types import InputPeerChannel
from dotenv import load_dotenv
import os

load_dotenv()

NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))
NOTIFY_CHANNEL_HASH = int(os.getenv("NOTIFY_CHANNEL_HASH"))

async def send_notification(client, message: str):
    """
    Uses the already running Telegram client (passed in) to send the notification.
    """
    channel = InputPeerChannel(NOTIFY_CHANNEL_ID, NOTIFY_CHANNEL_HASH)
    await client.send_message(channel, message)
