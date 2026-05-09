FEATURE_ID = "market_data"
FEATURE_NAME = "Market Data"
CATEGORY = "Utility"
DESCRIPTION = "Stock, crypto, and forex price lookups with charts"
ENV_VARS = []
DEPENDENCIES = ["yfinance", "requests"]

BLOCK_CODE = r'''
class MarketDataCog(commands.Cog):
    """Stock, crypto, and forex market data."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="stock", description="Get stock price info")
    async def stock(self, ctx, symbol: str):
        """Fetch stock data via Yahoo Finance."""
        await ctx.defer()
        try:
            import yfinance as yf
        except ImportError:
            await ctx.send("Install yfinance: `pip install yfinance`", delete_after=15)
            return

        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            if not info or "regularMarketPrice" not in info:
                await ctx.send(f"Could not find stock: {symbol.upper()}", delete_after=10)
                return

            price = info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", price)
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            embed = discord.Embed(
                title=f"{info.get('longName', symbol.upper())} ({symbol.upper()})",
                description=f"💵 **${price:,.2f}** {info.get('currency', 'USD')}",
                color=discord.Color.green() if change >= 0 else discord.Color.red(),
            )
            sign = "+" if change >= 0 else ""
            embed.add_field(name="Change", value=f"{sign}${change:,.2f} ({sign}{change_pct:.2f}%)", inline=True)
            embed.add_field(name="Volume", value=f"{info.get('volume', 0):,}", inline=True)
            embed.add_field(name="Market Cap", value=f"${info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A", inline=True)
            embed.add_field(name="Day Range", value=f"${info.get('dayLow', 0):,.2f} - ${info.get('dayHigh', 0):,.2f}", inline=True)
            embed.add_field(name="52W Range", value=f"${info.get('fiftyTwoWeekLow', 0):,.2f} - ${info.get('fiftyTwoWeekHigh', 0):,.2f}", inline=True)
            embed.set_footer(text="Data from Yahoo Finance • Prices delayed")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching stock data: {e}", delete_after=15)

    @commands.hybrid_command(name="crypto", description="Get cryptocurrency price")
    async def crypto(self, ctx, coin: str, currency: str = "usd"):
        """Fetch crypto data via CoinGecko."""
        await ctx.defer()
        try:
            import requests
        except ImportError:
            await ctx.send("Install requests: `pip install requests`", delete_after=15)
            return

        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 404:
                # Try search
                search_url = f"https://api.coingecko.com/api/v3/search?query={coin}"
                search_resp = requests.get(search_url, timeout=10)
                search_data = search_resp.json()
                if search_data.get("coins"):
                    coin_id = search_data["coins"][0]["id"]
                    resp = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}", timeout=10)
                else:
                    await ctx.send(f"Could not find cryptocurrency: {coin}", delete_after=10)
                    return
            data = resp.json()

            market = data.get("market_data", {})
            current = market.get("current_price", {}).get(currency.lower(), 0)
            change_24h = market.get("price_change_percentage_24h", 0) or 0
            high_24h = market.get("high_24h", {}).get(currency.lower(), 0)
            low_24h = market.get("low_24h", {}).get(currency.lower(), 0)
            volume = market.get("total_volume", {}).get(currency.lower(), 0)

            embed = discord.Embed(
                title=f"{data.get('name', coin)} ({data.get('symbol', '').upper()})",
                description=f"🪙 **{current:,.6f}** {currency.upper()}",
                color=discord.Color.green() if change_24h >= 0 else discord.Color.red(),
            )
            sign = "+" if change_24h >= 0 else ""
            embed.add_field(name="24h Change", value=f"{sign}{change_24h:.2f}%", inline=True)
            embed.add_field(name="24h High", value=f"{high_24h:,.6f}", inline=True)
            embed.add_field(name="24h Low", value=f"{low_24h:,.6f}", inline=True)
            embed.add_field(name="Volume", value=f"{volume:,.0f} {currency.upper()}", inline=True)
            embed.add_field(name="Market Cap Rank", value=f"#{data.get('market_cap_rank', 'N/A')}", inline=True)
            if data.get("image", {}).get("small"):
                embed.set_thumbnail(url=data["image"]["small"])
            embed.set_footer(text="Data from CoinGecko")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching crypto data: {e}", delete_after=15)

    @commands.hybrid_command(name="forex", description="Get forex exchange rate")
    async def forex(self, ctx, base: str, target: str = "USD"):
        """Fetch forex rate."""
        await ctx.defer()
        try:
            import requests
        except ImportError:
            await ctx.send("Install requests: `pip install requests`", delete_after=15)
            return

        try:
            url = f"https://open.er-api.com/v6/latest/{base.upper()}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            rates = data.get("rates", {})
            rate = rates.get(target.upper())
            if not rate:
                await ctx.send(f"Could not find rate for {base}/{target}", delete_after=10)
                return

            embed = discord.Embed(
                title=f"💱 {base.upper()}/{target.upper()}",
                description=f"**1 {base.upper()} = {rate:,.4f} {target.upper()}**",
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Last updated: {data.get('time_last_update_utc', 'Unknown')}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching forex data: {e}", delete_after=15)

async def setup(bot):
    await bot.add_cog(MarketDataCog(bot))
'''
