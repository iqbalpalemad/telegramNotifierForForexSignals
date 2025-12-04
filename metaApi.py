import asyncio
from metaapi_cloud_sdk import MetaApi, SynchronizationListener
import traceback
from datetime import datetime
WATCHDOG_INTERVAL = 30
RECONNECT_COOLDOWN  = 10
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


        self.watchdog_task = None
        self._reconnecting = False

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


        self.watchdog_task = asyncio.create_task(self._watchdog())
        print("🐶 Watchdog started")

    def is_connection_healthy(self) -> bool:
        try:
            return (
                    self.connection is not None and
                    self.account.connection_status == "CONNECTED" and
                    self.connection.synchronized is True
            )
        except Exception as e:
            return False

    async def _watchdog(self):
        print("🐕 Watchdog started")

        while True:
            try:
                if not self.is_connection_healthy():
                    print("⚠ Connection unhealthy detected. Reconnecting...")
                    await self._safe_reconnect()
                else:
                    print(f"✅ [{datetime.utcnow()}] Connection healthy")

            except Exception as e:
                print("❌ Watchdog error:", e)
                traceback.print_exc()

            await asyncio.sleep(WATCHDOG_INTERVAL)

    async def _safe_reconnect(self):
        if self._reconnecting:
            return

        self._reconnecting = True

        try:
            print("🔁 Performing safe reconnect...")

            # 1️⃣ Close old connection
            try:
                if self.connection:
                    await self.connection.close()
            except Exception:
                pass

            # 2️⃣ Cooldown
            await asyncio.sleep(RECONNECT_COOLDOWN)

            # 3️⃣ Re-fetch account
            self.account = await self.api.metatrader_account_api.get_account(self.account_id)
            await self.account.wait_connected()

            # 4️⃣ Create fresh connection
            self.connection = self.account.get_streaming_connection()
            self.connection.add_synchronization_listener(self)

            # 5️⃣ Connect & sync
            await self.connection.connect()
            await self.connection.wait_synchronized()

            print("✅ Reconnected & synchronized successfully")

        except Exception as e:
            print("❌ Reconnect failed:", str(e))
            traceback.print_exc()
        finally:
            self._reconnecting = False

    # -------------------------------------------------------
    #                      TRADE METHODS
    # -------------------------------------------------------
    async def place_market_order(self, symbol, direction, sl=None, tp=None, volume=None):
        """Place a BUY/SELL market order."""
        if not self.is_connection_healthy():
            print("⚠ Trade blocked — connection NOT healthy")
            return None

        volume = volume or self.default_lot
        symbol = SYMBOL_MAP.get(symbol, symbol)

        print(f"\n📌 MARKET ORDER → {direction.upper()} {symbol} ({volume} lot). SL: {sl} TP: {tp}")

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
        if not self.is_connection_healthy():
            print("⚠ Trade blocked — connection NOT healthy")
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
