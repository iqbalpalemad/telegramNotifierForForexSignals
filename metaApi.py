import asyncio
from metaapi_cloud_sdk import MetaApi, SynchronizationListener
import traceback

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
        self._lock = asyncio.Lock()

        self.watchdog_task = None
        self.stop_flag = False

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

        self.ready = True

        self.watchdog_task = asyncio.create_task(self._watchdog_loop())
        print("🐶 Watchdog started")

    async def _watchdog_loop(self):
        """Ensures connection stays alive."""
        while not self.stop_flag:
            try:
                # Status check using safe parameters
                print("🐶 Watchdog : status check started")
                status = self.connection.account.connection_status
                hs = self.connection.health_monitor.health_status

                connected = hs.get("connected", True)
                broker_connected = hs.get("connectedToBroker", True)

                if status != "CONNECTED" or not connected or not broker_connected:
                    print(f"⚠️ MetaApi connection lost (status={status}). Reconnecting...")

                    async with self._lock:  # prevent concurrent reconnect
                        await self._safe_reconnect()
                else :
                    print("🐶 Watchdog : connection active")

                await asyncio.sleep(30)

            except Exception as e:
                print("❌ Watchdog error:", e)
                print(traceback.format_exc())
                await asyncio.sleep(30)

    async def _safe_reconnect(self):
        """Reconnect logic with synchronization."""
        try:
            print("🔄 Reconnecting to MetaApi...")

            try:
                await self.connection.disconnect()
            except:
                pass  # ignore disconnect errors

            await asyncio.sleep(1)

            await self.connection.connect()
            await self.connection.wait_synchronized()

            print("✅ Reconnected and synchronized")
            self.ready = True

        except Exception as e:
            print("❌ Reconnect failed:", e)
            self.ready = False

    # -------------------------------------------------------
    #                      TRADE METHODS
    # -------------------------------------------------------
    async def place_market_order(self, symbol, direction, sl=None, tp=None, volume=None):
        """Place a BUY/SELL market order."""

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
