import os

class ChainConfig:
    ETHEREUM = 'eth'
    BINANCE = 'bsc'
    POLYGON = 'polygon'
    BITCOIN = 'btc'

API_URL = f"https://deep-index.moralis.io/api/v2/erc20/{{}}/price"
API_HEADERS = {"X-API-Key": os.getenv('MORALIS_API_KEY')}
CHECK_INTERVAL = 300  # 5 minutes
MAX_HISTORY_HOURS = 720  # 30 days
RSI_PERIOD = 14
