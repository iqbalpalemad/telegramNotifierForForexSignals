import asyncio
from metaapi_cloud_sdk import MetaApi, SynchronizationListener

SYMBOL_MAP = {
    "XAUUSD": "XAUUSD_i",
}

class MetaApiStreamClient(SynchronizationListener):

    def __init__(self, api_token: str, account_id: str, default_lot: float = 0.01):
        self.api_token = api_token
        self.account_id = account_id
        self.default_lot = default_lot

        self.api = MetaApi(api_token)
        self.account = None
        self.connection = None
        self.stream = None
        self.rpc = None
        self.ready = False

    # -----------------------------
    #         CONNECTION
    # -----------------------------
    async def connect(self):
        print("🔌 Connecting to MetaApi...")

        self.account = await self.api.metatrader_account_api.get_account(self.account_id)

        print("⏳ Waiting for account to connect...")
        await self.account.wait_connected()
        print("✅ Account connected!")

        # STREAMING CONNECTION (Events + sync updates)
        print("🔁 Connecting streaming listener...")
        self.stream = self.account.get_streaming_connection()
        self.stream.add_synchronization_listener(self)
        await self.stream.connect()
        print("🔁 Streaming connected.")

        # RPC (TRADING) CONNECTION
        print("⚙️ Connecting trading (RPC) interface...")
        self.rpc = self.account.get_rpc_connection()
        await self.rpc.connect()
        print("🟢 Trading RPC connected!")

        print("⏳ Waiting for full synchronization...")
        await self.stream.wait_synchronized()
        print("🎯 Streaming synchronized successfully!")

        if not self.ready:
            self.ready = True
            print("🎯 MetaApi synchronized and ready.")

    async def is_ready(self):
        return self.ready

    # -----------------------------
    #          TRADE METHODS
    # -----------------------------
    async def place_market_order(self, symbol: str, direction: str, sl=None, tp=None, volume=None):
        """Place a market order."""
        if not await self.is_ready():
            raise Exception("❌ MetaApi connection not ready yet.")

        volume = volume or self.default_lot

        print(f"\n📌 MARKET ORDER → {direction.upper()} {symbol} ({volume} lots)")
        print(f"   SL: {sl}, TP: {tp}")

        try:
            order = await self.rpc.trade.create_market_order(
                symbol=SYMBOL_MAP.get(symbol, symbol),
                volume=volume,
                side=direction.lower(),
                stop_loss_price=sl,
                take_profit_price=tp
            )
            print("✅ Market order placed successfully.")
            return order

        except Exception as err:
            print("❌ Error placing market order:", err)
            return None

    async def place_limit_order(self, symbol: str, direction: str, entry_price: float, sl=None, tp=None, volume=None):
        """Place a pending limit order."""
        if not await self.is_ready():
            raise Exception("❌ MetaApi connection not ready yet.")

        volume = volume or self.default_lot

        print(f"\n📌 LIMIT ORDER → {direction.upper()} {symbol} @ {entry_price} ({volume} lots)")
        print(f"   SL: {sl}, TP: {tp}")

        try:
            order = await self.rpc.trade.create_limit_order(
                symbol=symbol,
                volume=volume,
                side=direction.lower(),
                open_price=entry_price,
                stop_loss_price=sl,
                take_profit_price=tp
            )
            print("📎 Limit order created successfully.")
            return order

        except Exception as err:
            print("❌ Error placing limit order:", err)
            return None

    # -----------------------------
    #     STREAM LISTENER HOOKS
    # -----------------------------

    async def on_order_added(self, instance_index, order):
        print("\n🔵 NEW ORDER CREATED -----------------------")
        print(order)

    async def on_order_updated(self, instance_index, order):
        print("\n🟡 ORDER UPDATED -----------------------")
        print(order)

    async def on_order_removed(self, instance_index, order):
        print("\n🔴 ORDER REMOVED -----------------------")
        print(order)

    async def on_position_added(self, instance_index, position):
        print("\n🟢 POSITION OPENED -----------------------")
        print(f"Symbol: {position.symbol}")
        print(f"Direction: {position.type}")
        print(f"Volume: {position.volume}")
        print(f"Entry Price: {position.price}")

    async def on_position_updated(self, instance_index, position):
        print("\n🟠 POSITION UPDATED -----------------------")
        print(f"{position.symbol} running profit: {position.unrealized_profit}")

    async def on_position_removed(self, instance_index, position):
        print("\n🚨 POSITION CLOSED -----------------------")
        print(f"Symbol: {position.symbol}")
        print(f"Volume: {position.volume}")
        print(f"Close Price: {position.price}")

        pnl = position.realized_profit or position.unrealized_profit or 0

        if pnl >= 0:
            print(f"💰 PROFIT: {pnl}")
        else:
            print(f"❌ LOSS: {pnl}")

    async def on_deal_added(self, instance_index, deal):
        print("\n💥 DEAL EXECUTED -----------------------")
        print(deal)

    async def on_synchronization_completed(self, instance_index, specifications, positions, orders, historyOrders,
                                           historyDeals):
        print("🎉 MetaApi synchronization completed — trading enabled!")
        self.ready = True

