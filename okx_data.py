import aiohttp
import time
from datetime import datetime
from bybit_data import format_time_diff

async def get_okx_data(session, symbol='BTC-USDT-SWAP'):
    try:
        timeout = aiohttp.ClientTimeout(total=2)
        price_url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
        funding_url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={symbol}&limit=1"
        next_funding_url = f"https://www.okx.com/api/v5/public/funding-rate?instId={symbol}"

        async with session.get(price_url, timeout=timeout) as price_resp, \
                 session.get(funding_url, timeout=timeout) as funding_resp, \
                 session.get(next_funding_url, timeout=timeout) as next_funding_resp:

            if any(resp.status != 200 for resp in [price_resp, funding_resp, next_funding_resp]):
                raise Exception("One or more OKX API requests failed")

            price_data = await price_resp.json()
            funding_data = await funding_resp.json()
            next_funding_data = await next_funding_resp.json()

            if not all('data' in d and d['data'] for d in [price_data, funding_data, next_funding_data]):
                raise Exception("Invalid OKX response format")

            btc_price = float(price_data['data'][0]['last'])
            funding_rate = float(funding_data['data'][0]['fundingRate']) * 100
            next_time = int(next_funding_data['data'][0]['fundingTime']) / 1000

            return {
                'price': btc_price,
                'funding': funding_rate,
                'time_to_payment': format_time_diff(next_time)
            }
    except Exception as e:
        print(f"OKX error: {str(e)[:100]}")
        return None