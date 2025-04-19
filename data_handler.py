import asyncio
import aiosqlite
from datetime import datetime

class DataHandler:
    def __init__(self):
        self.current_data = {
            'bybit': {'price': 0, 'funding': 0, 'next_funding': 0},
            'okx': {'price': 0, 'funding': 0, 'next_funding': 0},
            'spreads': {'price': 0, 'funding': 0},
            'timestamp': ''
        }
        self.selected_pair = 'BTCUSDT'
        self.update_callback = None
        self.stop_event = asyncio.Event()
        self.active_pair = None

    def format_time(self, timestamp):
        remaining = max(0, timestamp - datetime.now().timestamp())
        h, remainder = divmod(int(remaining), 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    async def get_sorted_pairs(self, sort_by='price'):
        async with aiosqlite.connect('arbitrage.db') as db:
            if sort_by == 'price':
                query = '''SELECT pair FROM pairs
                          WHERE price_spread >= 0.1
                          ORDER BY price_spread DESC LIMIT 50'''
            else:
                query = '''SELECT pair FROM pairs
                          WHERE abs(funding_spread) >= 0.05
                          ORDER BY abs(funding_spread) DESC LIMIT 50'''

            cursor = await db.execute(query)
            pairs = await cursor.fetchall()
            return [f"{pair[0]}USDT" for pair in pairs] if pairs else ['BTCUSDT']

    async def update_data(self):
        self.active_pair = self.selected_pair
        pair_clean = self.active_pair.replace('USDT', '')

        while not self.stop_event.is_set() and self.active_pair == self.selected_pair:
            try:
                async with aiosqlite.connect('arbitrage.db') as db:
                    cursor = await db.execute(
                        '''SELECT * FROM pairs WHERE pair = ?''',
                        (pair_clean,))
                    data = await cursor.fetchone()

                    if data and self.active_pair == self.selected_pair:
                        self.current_data = {
                            'bybit': {
                                'price': data[1],
                                'funding': data[3],
                                'next_funding': 0
                            },
                            'okx': {
                                'price': data[2],
                                'funding': data[4],
                                'next_funding': 0
                            },
                            'spreads': {
                                'price': data[5],
                                'funding': data[6]
                            },
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        }

                        if self.update_callback:
                            self.update_callback()

            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Update error: {e}")

            await asyncio.sleep(1)

    def start(self, loop):
        self.stop_event.clear()
        asyncio.run_coroutine_threadsafe(self.update_data(), loop)

    def stop(self):
        self.stop_event.set()

    def set_callback(self, callback):
        self.update_callback = callback

    def set_pair(self, pair):
        self.selected_pair = pair
        self.stop()
        self.start(asyncio.get_event_loop())

    def get_data(self):
        # Убедитесь, что 'timestamp' всегда присутствует
        if 'timestamp' not in self.current_data:
            self.current_data['timestamp'] = datetime.now().strftime('%H:%M:%S')
        data = self.current_data.copy()
        data['bybit']['time_to_payment'] = self.format_time(0)
        data['okx']['time_to_payment'] = self.format_time(0)
        return data
