import aiohttp
from datetime import datetime

async def get_bybit_data(symbol='BTCUSDT'):
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.bybit.com/v5/market/tickers"
            params = {'category': 'linear', 'symbol': symbol}
            
            async with session.get(url, params=params, timeout=1) as response:
                data = await response.json()
                ticker = data['result']['list'][0]
                
                next_funding = int(ticker['nextFundingTime'])/1000
                now = datetime.now().timestamp()
                remaining = max(0, next_funding - now)
                h, m = divmod(int(remaining)//60, 60)
                s = int(remaining)%60
                
                return {
                    'price': float(ticker['lastPrice']),
                    'funding': float(ticker['fundingRate'])*100,
                    'time_to_payment': f"{h:02d}:{m:02d}:{s:02d}"
                }
    except Exception as e:
        print(f"Bybit error: {str(e)[:100]}")
        return None