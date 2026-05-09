FEATURE_ID = "economy"
FEATURE_NAME = "Economy System"
CATEGORY = "Economy"
DESCRIPTION = "Virtual currency with daily, shop, gambling, transfers"
ENV_VARS = ["ECONOMY_CURRENCY_NAME", "ECONOMY_CURRENCY_SYMBOL"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class EconomyCog(commands.Cog):
    """Virtual currency economy system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/economy.json")
        self.currency_name = os.getenv("ECONOMY_CURRENCY_NAME", "Coins")
        self.currency_symbol = os.getenv("ECONOMY_CURRENCY_SYMBOL", "🪙")
        self._data = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._data = json.loads(self.data_file.read_text())
        except Exception:
            self._data = {}
            self._init_shop()

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._data, indent=2))

    def _init_shop(self):
        self._data["shop"] = [
            {"id": "rankup", "name": "Level-Up Boost", "price": 500, "description": "Boost yourself to the next level instantly"},
            {"id": "customcmd", "name": "Custom Command", "price": 2000, "description": "Create a custom text command for yourself"},
            {"id": "colorname", "name": "Colored Name", "price": 3000, "description": "Get a custom color for your name"},
            {"id": "spotlight", "name": "Member Spotlight", "price": 1000, "description": "Get announced to the whole server"},
            {"id": "vip", "name": "VIP Role (24h)", "price": 5000, "description": "Get the VIP role for 24 hours"},
        ]

    def _get_balance(self, user_id, guild_id):
        gid = str(guild_id)
        uid = str(user_id)
        self._data.setdefault(gid, {})
        self._data[gid].setdefault(uid, {"balance": 100, "last_daily": None, "inventory": []})
        return self._data[gid][uid]

    @commands.hybrid_command(name="balance", aliases=["bal"], description="Check your balance")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = self._get_balance(member.id, ctx.guild.id)
        embed = discord.Embed(title=f"{member.display_name}'s Balance", description=f"{self.currency_symbol} **{data['balance']:,}** {self.currency_name}", color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Claim your daily reward")
    async def daily(self, ctx):
        data = self._get_balance(ctx.author.id, ctx.guild.id)
        now = discord.utils.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        if data["last_daily"] == today_str:
            next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            await ctx.send(f"Already claimed today! Come back {discord.utils.format_dt(next_reset, 'R')}.", delete_after=10)
            return

        streak = self._data.get("streaks", {}).get(str(ctx.author.id), 0)
        if data["last_daily"] and (now - datetime.fromisoformat(f"{data['last_daily']}T00:00:00")).days == 1:
            streak += 1
        else:
            streak = 1

        reward = 100 + (streak * 25)
        data["balance"] += reward
        data["last_daily"] = today_str

        self._data.setdefault("streaks", {})
        self._data["streaks"][str(ctx.author.id)] = streak
        self._save()

        embed = discord.Embed(title="📅 Daily Reward", description=f"You received **{self.currency_symbol} {reward:,}** {self.currency_name}!", color=discord.Color.green())
        embed.add_field(name="Streak", value=f"🔥 {streak} day{'s' if streak > 1 else ''}", inline=True)
        embed.add_field(name="New Balance", value=f"{self.currency_symbol} **{data['balance']:,}**", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="give", description="Give coins to someone")
    async def give(self, ctx, member: discord.Member, amount: int):
        if member.bot or member == ctx.author:
            await ctx.send("Can't give coins to yourself or bots.", delete_after=10)
            return
        if amount < 1:
            await ctx.send("Amount must be at least 1.", delete_after=10)
            return

        sender = self._get_balance(ctx.author.id, ctx.guild.id)
        if sender["balance"] < amount:
            await ctx.send(f"You don't have enough {self.currency_name}!", delete_after=10)
            return

        receiver = self._get_balance(member.id, ctx.guild.id)
        sender["balance"] -= amount
        receiver["balance"] += amount
        self._save()

        await ctx.send(f"💸 {ctx.author.mention} gave {self.currency_symbol} **{amount:,}** to {member.mention}!")

    @commands.hybrid_command(name="rob", description="Try to rob someone")
    async def rob(self, ctx, member: discord.Member):
        if member.bot or member == ctx.author:
            await ctx.send("Can't rob bots or yourself.", delete_after=10)
            return

        thief = self._get_balance(ctx.author.id, ctx.guild.id)
        target = self._get_balance(member.id, ctx.guild.id)

        if target["balance"] < 100:
            await ctx.send(f"{member.display_name} is broke!", delete_after=10)
            return

        success = random.random() < 0.4
        if success:
            stolen = min(min(random.randint(50, 300), target["balance"]), int(target["balance"] * 0.3))
            thief["balance"] += stolen
            target["balance"] -= stolen
            self._save()
            await ctx.send(f"🕵️ You robbed {self.currency_symbol} **{stolen:,}** from {member.mention}!")
        else:
            fine = min(random.randint(50, 150), thief["balance"])
            thief["balance"] -= fine
            target["balance"] += fine
            self._save()
            await ctx.send(f"🚨 Caught! You got fined {self.currency_symbol} **{fine:,}** which went to {member.mention}!")

    @commands.hybrid_command(name="slots", description="Play slots")
    async def slots(self, ctx, bet: int = 50):
        data = self._get_balance(ctx.author.id, ctx.guild.id)
        if data["balance"] < bet:
            await ctx.send(f"Not enough {self.currency_name}!", delete_after=10)
            return

        emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "⭐"]
        result = [random.choice(emojis) for _ in range(3)]

        if result[0] == result[1] == result[2]:
            if result[0] == "💎":
                multiplier = 10
            elif result[0] == "7️⃣":
                multiplier = 7
            elif result[0] == "⭐":
                multiplier = 5
            else:
                multiplier = 3
            winnings = bet * multiplier
            data["balance"] += winnings
            outcome = f"JACKPOT! 🎉 Won **{self.currency_symbol} {winnings:,}**"
        elif result[0] == result[1] or result[1] == result[2]:
            winnings = bet * 2
            data["balance"] += winnings
            outcome = f"Two match! Won **{self.currency_symbol} {winnings:,}**"
        else:
            data["balance"] -= bet
            outcome = f"Lost **{self.currency_symbol} {bet:,}**"

        self._save()
        await ctx.send(f"🎰 | {' | '.join(result)} |\n{outcome}")

    @commands.hybrid_command(name="coinflip", description="Bet on a coinflip")
    async def coinflip_bet(self, ctx, side: str, bet: int = 50):
        side = side.lower()
        if side not in ("heads", "tails"):
            await ctx.send("Choose heads or tails.", delete_after=10)
            return

        data = self._get_balance(ctx.author.id, ctx.guild.id)
        if data["balance"] < bet:
            await ctx.send(f"Not enough {self.currency_name}!", delete_after=10)
            return

        result = random.choice(["heads", "tails"])
        if side == result:
            winnings = bet * 2
            data["balance"] += winnings
            await ctx.send(f"🪙 It's **{result}**! You won {self.currency_symbol} **{winnings:,}**!")
        else:
            data["balance"] -= bet
            await ctx.send(f"🪙 It's **{result}**! You lost {self.currency_symbol} **{bet:,}**.")

        self._save()

    @commands.hybrid_command(name="shop", description="View the shop")
    async def shop(self, ctx):
        items = self._data.get("shop", [])
        lines = [f"**{item['name']}** — {self.currency_symbol} {item['price']:,}\n↳ {item['description']}" for item in items]
        embed = discord.Embed(title="🛒 Shop", description="\n\n".join(lines), color=discord.Color.gold())
        embed.set_footer(text="Use /buy <item_id> to purchase")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Buy an item from the shop")
    async def buy(self, ctx, item_id: str):
        shop = self._data.get("shop", [])
        item = next((i for i in shop if i["id"] == item_id.lower()), None)
        if not item:
            await ctx.send(f"Item not found. Shop items: {', '.join(i['id'] for i in shop)}", delete_after=15)
            return

        data = self._get_balance(ctx.author.id, ctx.guild.id)
        if data["balance"] < item["price"]:
            await ctx.send(f"Not enough {self.currency_name}! You need {self.currency_symbol} {item['price']:,}.", delete_after=10)
            return

        data["balance"] -= item["price"]
        data["inventory"].append({"item_id": item["id"], "purchased_at": discord.utils.utcnow().isoformat()})
        self._save()
        await ctx.send(f"🎁 Purchased **{item['name']}** for {self.currency_symbol} {item['price']:,}!")

    @commands.hybrid_command(name="rich", aliases=["baltop"], description="Server wealth leaderboard")
    async def rich(self, ctx):
        gid = str(ctx.guild.id)
        guild_data = self._data.get(gid, {})
        top = sorted([(uid, info) for uid, info in guild_data.items() if uid != "shop"], key=lambda x: x[1].get("balance", 0), reverse=True)[:10]

        if not top:
            await ctx.send("No economy data yet.", delete_after=10)
            return

        lines = [f"**#{i}** <@{uid}> — {self.currency_symbol} **{info['balance']:,}**" for i, (uid, info) in enumerate(top, 1)]
        embed = discord.Embed(title=f"🏆 Richest in {ctx.guild.name}", description="\n".join(lines), color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
'''
