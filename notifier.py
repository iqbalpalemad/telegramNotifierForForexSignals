from pushover_client import PushoverClient
import os

pushover = PushoverClient(
    user_key = os.getenv("PUSHOVER_KEY"),
    app_token = os.getenv("PUSHOVER_TOKEN")
)

def notify_signal(channel,direction, entry, sl, tp):
    msg = f"📩 Signal Received\nChannel: {channel}\nDirection: {direction}\nEntry: {entry}\nSL: {sl}\nTP: {tp}"
    pushover.notify_info(msg)

def notify_order_placed(symbol, price, order_id):
    msg = f"📈 Trade Executed\nSymbol: {symbol}\nPrice: {price}\nOrder ID: {order_id}"
    pushover.notify_info(msg)

def notify_trade_closed(symbol, result):
    msg = f"📌 Trade Closed: {symbol}\nResult: {result}"
    pushover.notify_info(msg)

def send_notification(message):
    msg = f"{message}"
    pushover.notify_info(msg)
