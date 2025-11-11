import asyncio
import importlib
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel
from dotenv import load_dotenv
import os
from channels_config import CHANNELS
from notifier import send_notification

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "user_session")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def handle_message(channel_name, parser_module, message_text):
    try:
        parser = importlib.import_module(f"parsers.{parser_module}")
        parsed = parser.parse_message(message_text)
        if not parsed:
            return  # ignore non-signal messages

        msg = (
            f"📢 *Signal from {channel_name}*\n"
            f"Pair: {parsed['symbol']}\n"
            f"Direction: {parsed['action']}\n"
            f"Entry: {parsed['entry']}\n"
            f"TP: {parsed['target']}\n"
            f"SL: {parsed['stop_loss']}"
        )

        # ✅ Use the same Telethon client
        await send_notification(client, msg)
        print(f"✅ Sent signal notification from {channel_name}")

    except Exception as e:
        print(f"❌ Error parsing message from {channel_name}: {e}")

async def start():
    await client.start()
    print("🚀 Listening for signals...")

    for ch in CHANNELS:
        entity = InputPeerChannel(ch["id"], ch["access_hash"])

        @client.on(events.NewMessage(chats=entity))
        async def handler(event, ch=ch):
            text = event.message.message
            await handle_message(ch["name"], ch["parser"], text)

    print("✅ Ready to receive messages.")
    await client.run_until_disconnected()
