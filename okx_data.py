import aiohttp
import time
from datetime import datetime

async def get_okx_data(symbol='BTC-USDT-SWAP'):
    try:
        async with aiohttp.ClientSession() as session:
            price_url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
            funding_url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={symbol}&limit=1"
            next_funding_url = f"https://www.okx.com/api/v5/public/funding-rate?instId={symbol}"
            
            async with session.get(price_url, timeout=1) as price_resp, \
                     session.get(funding_url, timeout=1) as funding_resp, \
                     session.get(next_funding_url, timeout=1) as next_funding_resp:
                
                price_data = await price_resp.json()
                funding_data = await funding_resp.json()
                next_funding_data = await next_funding_resp.json()

            btc_price = float(price_data['data'][0]['last'])
            funding_rate = float(funding_data['data'][0]['fundingRate']) * 100
            next_time = int(next_funding_data['data'][0]['fundingTime']) / 1000
            
            time_left = max(0, next_time - time.time())
            hours, remainder = divmod(int(time_left), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                'price': btc_price,
                'funding': funding_rate,
                'time_to_payment': f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            }
    except Exception as e:
        print(f"OKX error: {str(e)[:100]}")
        return None