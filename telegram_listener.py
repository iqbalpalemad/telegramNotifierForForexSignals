import asyncio
import importlib
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel
from dotenv import load_dotenv
import os
from channels_config import CHANNELS
load_dotenv()
from notifier import notify_signal, notify_order_placed, notify_trade_closed, send_notification
from metaApi import MetaApiStreamClient


API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "user_session")
META_API_TOKEN = os.getenv("META_API_TOKEN")
META_API_ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
async def handle_message(channel_name, parser_module, message_text, meta_api_client):
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
        notify_signal(channel_name,parsed['entry'], parsed['stop_loss'], parsed['target'])
        await meta_api_client.place_market_order(parsed['symbol'],parsed['action'],parsed['stop_loss'],parsed['target'])

    except Exception as e:
        print(f"❌ Error parsing message from {channel_name}: {e}")

async def start():
    await client.start()
    meta_api_client = MetaApiStreamClient(META_API_TOKEN, META_API_ACCOUNT_ID)
    await meta_api_client.connect()
    print("🚀 Listening for signals...")

    for ch in CHANNELS:
        entity = InputPeerChannel(ch["id"], ch["access_hash"])

        @client.on(events.NewMessage(chats=entity))
        async def handler(event, ch=ch):
            text = event.message.message
            print(f"✅ Signale recieved from {text}")
            await handle_message(ch["name"], ch["parser"], text,meta_api_client)

    print("✅ Ready to receive messages.")
    await client.run_until_disconnected()

