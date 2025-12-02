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
        self.ready = False

    # -------------------------------------------------------
    #                 CONNECTION & STREAM SETUP
    # -------------------------------------------------------
    async def connect(self):
        print("🔌 Connecting to MetaApi...")

        self.account = await self.api.metatrader_account_api.get_account(self.account_id)

        print("⏳ Waiting for account to connect...")
        await self.account.wait_connected()
        print("✅ Account connected!")

        self.connection = self.account.get_streaming_connection()

        # Register listener BEFORE connecting
        self.connection.add_synchronization_listener(self)

        await self.connection.connect()

        print("⏳ Waiting for initial streaming sync...")
        await self.connection.wait_synchronized()
        print("⚠️ Waiting for synchronization callback... (will signal readiness)")

    async def is_ready(self):
        return self.ready

    # -------------------------------------------------------
    #                      TRADE METHODS
    # -------------------------------------------------------
    async def place_market_order(self, symbol, direction, sl=None, tp=None, volume=None):
        """Place a BUY/SELL market order."""
        if not await self.is_ready():
            print("⛔ MetaApi not ready — ignoring trade request.")
            return None

        volume = volume or self.default_lot
        symbol = SYMBOL_MAP.get(symbol, symbol)

        print(f"\n📌 MARKET ORDER → {direction.upper()} {symbol} ({volume} lot)")

        try:
            if direction.lower() == "buy":
                result = await self.connection.create_market_buy_order(
                    symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                )
            else:
                result = await self.connection.create_market_sell_order(
                    symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                )

            print("✅ Market order placed successfully")
            return result

        except Exception as err:
            print(f"❌ Error placing market order: {err}")
            return None

    async def place_limit_order(self, symbol, direction, price, sl=None, tp=None, volume=None):
        """Place pending limit order."""
        if not await self.is_ready():
            print("⛔ MetaApi not ready — ignoring trade request.")
            return None

        volume = volume or self.default_lot
        symbol = SYMBOL_MAP.get(symbol, symbol)

        print(f"\n📌 LIMIT ORDER → {direction.upper()} {symbol} @ {price}")

        try:
            if direction.lower() == "buy":
                result = await self.connection.create_limit_buy_order(
                    symbol=symbol, volume=volume, open_price=price,
                    stop_loss=sl, take_profit=tp
                )
            else:
                result = await self.connection.create_limit_sell_order(
                    symbol=symbol, volume=volume, open_price=price,
                    stop_loss=sl, take_profit=tp
                )

            print("📎 Limit order created successfully")
            return result

        except Exception as err:
            print(f"❌ Error placing limit order: {err}")
            return None

    # -------------------------------------------------------
    #                  LISTENER CALLBACKS
    # -------------------------------------------------------

    @staticmethod
    async def on_order_added(instance_index, order):
        print("\n🔵 ORDER ADDED -----------------------")
        print(order)

    @staticmethod
    async def on_order_updated(instance_index, order):
        print("\n🟡 ORDER UPDATED -----------------------")
        print(order)

    @staticmethod
    async def on_order_removed(instance_index, order):
        print("\n🔴 ORDER REMOVED -----------------------")
        print(order)

    @staticmethod
    async def on_position_added(instance_index, position):
        print("\n🟢 POSITION OPENED -----------------------")
        print(position)

    async def on_position_updated(self, instance_index, position):
        print("\n🟠 POSITION UPDATED -----------------------")
        print(position)

    async def on_position_removed(self, instance_index, position):
        pnl = position.realized_profit or position.unrealized_profit or 0
        print("\n🚨 POSITION CLOSED -----------------------")
        print(position)
        print(f"📊 PNL: {'💰 PROFIT' if pnl >= 0 else '❌ LOSS'} {pnl}")

    async def on_deal_added(self, instance_index, deal):
        print("\n💥 DEAL EXECUTED -----------------------")
        print(deal)

    async def on_synchronization_started(self, instance_index):
        print("🔄 Synchronization started...")

    async def on_synchronization_completed(self, instance_index, specs_updated):
        print("🚀 Synchronization callback received. Trading READY!")
        self.ready = True
