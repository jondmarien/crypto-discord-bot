import discord
from discord.ext import commands, tasks
import requests
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
API_URL = "https://deep-index.moralis.io/api/v2/erc20/{}/price"
API_HEADERS = {"X-API-Key": os.getenv('MORALIS_API_KEY')}
CHECK_INTERVAL = 300  # 5 minutes

class CryptoPortfolio:
    def __init__(self):
        self.tracked_coins = {}

    async def get_crypto_data(self, symbol, chain='eth'):
        try:
            response = requests.get(
                API_URL.format(symbol),
                headers=API_HEADERS,
                params={'chain': chain}
            )
            data = response.json()
            return float(data['usdPrice'])
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def calculate_rsi(self, prices, period=14):
        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])
        
        for i in range(period, len(prices)-1):
            avg_gain = (avg_gain * (period-1) + gain[i])/period
            avg_loss = (avg_loss * (period-1) + loss[i])/period
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        return 100 - (100 / (1 + rs))

portfolio = CryptoPortfolio()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    price_check.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def price_check():
    for guild in bot.guilds:
        for symbol, data in portfolio.tracked_coins.items():
            current_price = await portfolio.get_crypto_data(symbol)
            if current_price:
                # Generate trading signal
                prices = data['history'][-14:]
                if len(prices) >= 14:
                    rsi = portfolio.calculate_rsi(prices)
                    if rsi > 70:
                        signal = "SELL"
                    elif rsi < 30:
                        signal = "BUY"
                    else:
                        signal = "HOLD"
                else:
                    signal = "HOLD (insufficient data)"
                
                channel = bot.get_channel(data['channel_id'])
                await channel.send(
                    f"**{symbol.upper()} Alert**\n"
                    f"Current Price: ${current_price:.2f}\n"
                    f"RSI: {rsi:.2f if 'rsi' in locals() else 'N/A'}\n"
                    f"Signal: {signal}"
                )

@bot.command()
async def track(ctx, symbol: str, lower: float, upper: float):
    portfolio.tracked_coins[symbol.lower()] = {
        'channel_id': ctx.channel.id,
        'thresholds': (lower, upper),
        'history': []
    }
    await ctx.send(f"Now tracking {symbol.upper()} in this channel")

@bot.command()
async def price(ctx, symbol: str):
    current_price = await portfolio.get_crypto_data(symbol)
    if current_price:
        await ctx.send(f"Current {symbol.upper()} price: ${current_price:.2f}")
    else:
        await ctx.send("Could not retrieve price data")

@bot.command()
async def chart(ctx, symbol: str, days: int = 7):
    prices = portfolio.tracked_coins.get(symbol.lower(), {}).get('history', [])
    if prices:
        plt.figure(figsize=(10,5))
        plt.plot(prices[-days*24:])
        plt.title(f"{symbol.upper()} Price History")
        plt.xlabel("Hours")
        plt.ylabel("Price (USD)")
        plt.savefig('chart.png')
        await ctx.send(file=discord.File('chart.png'))
    else:
        await ctx.send("No historical data available")

bot.run(os.getenv('DISCORD_TOKEN'))
