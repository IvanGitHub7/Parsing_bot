import aiohttp
import asyncio
import aiosqlite
from datetime import datetime

async def fetch_bybit_data(session):
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        async with session.get(url, timeout=10) as resp:
            data = await resp.json()
            return {
                item['symbol']: {
                    'price': float(item['lastPrice']),
                    'funding': float(item['fundingRate']) * 100,
                    'next_funding': int(item['nextFundingTime'])/1000
                }
                for item in data.get('result', {}).get('list', [])
                if item['symbol'].endswith('USDT')
            }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bybit error: {e}")
        return {}

async def fetch_okx_data(session):
    url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
    try:
        async with session.get(url, timeout=10) as resp:
            data = await resp.json()
            return {
                item['instId'].replace('-USDT-SWAP', ''): {
                    'price': float(item['last']),
                    'funding': float(item['fundingRate']) * 100,
                    'next_funding': int(item['fundingTime'])/1000
                }
                for item in data.get('data', [])
                if item['instId'].endswith('-USDT-SWAP')
            }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OKX error: {e}")
        return {}

async def update_database():
    async with aiohttp.ClientSession() as session:
        bybit_data, okx_data = await asyncio.gather(
            fetch_bybit_data(session),
            fetch_okx_data(session)
        )
        
        common_pairs = set(bybit_data.keys()) & set(okx_data.keys())
        
        async with aiosqlite.connect('arbitrage.db') as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS pairs (
                pair TEXT PRIMARY KEY,
                bybit_price REAL,
                okx_price REAL,
                bybit_funding REAL,
                okx_funding REAL,
                price_spread REAL,
                funding_spread REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            for pair in common_pairs:
                max_price = max(bybit_data[pair]['price'], okx_data[pair]['price'])
                min_price = min(bybit_data[pair]['price'], okx_data[pair]['price'])
                price_spread = (max_price/min_price - 1) * 100
                funding_spread = bybit_data[pair]['funding'] - okx_data[pair]['funding']
                
                await db.execute('''
                INSERT OR REPLACE INTO pairs VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ''', (
                    pair,
                    bybit_data[pair]['price'],
                    okx_data[pair]['price'],
                    bybit_data[pair]['funding'],
                    okx_data[pair]['funding'],
                    round(price_spread, 4),
                    round(funding_spread, 6)
                ))
            
            await db.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] DB updated")

async def main():
    while True:
        try:
            await update_database()
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())