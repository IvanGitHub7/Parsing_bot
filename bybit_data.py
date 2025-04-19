import aiohttp
import time
from datetime import datetime

def format_time_diff(timestamp):
    """Форматирование времени до выплаты"""
    remaining = max(0, timestamp - time.time())
    h, remainder = divmod(int(remaining), 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

async def get_bybit_data(session, symbol='BTCUSDT'):
    try:
        url = "https://api.bybit.com/v5/market/tickers"
        params = {'category': 'linear', 'symbol': symbol}

        async with session.get(url, params=params, timeout=3) as response:
            if response.status != 200:
                raise Exception(f"Bybit API error: {response.status}")

            data = await response.json()
            if not data.get('result') or not data['result'].get('list'):
                raise Exception("Invalid Bybit response format")

            ticker = data['result']['list'][0]
            return {
                'price': float(ticker['lastPrice']),
                'funding': float(ticker['fundingRate']) * 100,
                'time_to_payment': format_time_diff(int(ticker['nextFundingTime'])/1000)
            }
    except Exception as e:
        print(f"Bybit error: {str(e)[:100]}")
        return None
