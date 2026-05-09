FEATURE_ID = "music"
FEATURE_NAME = "Music Player"
CATEGORY = "Fun"
DESCRIPTION = "Music playback via Lavalink with play, skip, queue, pause, resume"
ENV_VARS = ["LAVALINK_HOST", "LAVALINK_PORT", "LAVALINK_PASSWORD"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class MusicCog(commands.Cog):
    """Music playback via Lavalink."""

    def __init__(self, bot):
        self.bot = bot
        self.lavalink_host = os.getenv("LAVALINK_HOST", "localhost")
        self.lavalink_port = int(os.getenv("LAVALINK_PORT", "2333"))
        self.lavalink_pass = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
        self._connected = False

    def _get_lavalink(self):
        try:
            import lavalink
            return lavalink
        except ImportError:
            return None

    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song")
    async def play(self, ctx, *, query: str):
        lavalink = self._get_lavalink()
        if not lavalink:
            await ctx.send("Lavalink not installed. Install with: `pip install lavalink.py`", delete_after=15)
            return
        if not ctx.author.voice:
            await ctx.send("Join a voice channel first!", delete_after=10)
            return

        if not self._connected:
            await lavalink.initialize(
                bot=self.bot,
                host=self.lavalink_host,
                port=self.lavalink_port,
                password=self.lavalink_pass,
            )
            self._connected = True

        node = lavalink.get_best_node()
        if not node:
            await ctx.send("No music nodes available. Start Lavalink first.", delete_after=10)
            return

        player = node.get_player(ctx.guild.id)
        if not player.is_connected:
            await player.connect(ctx.author.voice.channel.id)

        results = await node.fetch_tracks(f"ytsearch:{query}")
        if not results:
            await ctx.send("No results found.", delete_after=10)
            return

        track = results[0]
        player.add_track(track)
        await ctx.send(f"🎵 Added to queue: **{track.title}**", delete_after=15)

        if not player.is_playing:
            await player.play()

    @commands.hybrid_command(name="skip", aliases=["s"], description="Skip current song")
    async def skip(self, ctx):
        lavalink = self._get_lavalink()
        if not lavalink:
            return
        player = lavalink.get_player(ctx.guild.id)
        if player and player.is_playing:
            await player.skip()
            await ctx.send("⏭️ Skipped.", delete_after=10)

    @commands.hybrid_command(name="pause", description="Pause playback")
    async def pause(self, ctx):
        lavalink = self._get_lavalink()
        if not lavalink:
            return
        player = lavalink.get_player(ctx.guild.id)
        if player and player.is_playing:
            await player.pause()
            await ctx.send("⏸️ Paused.", delete_after=10)

    @commands.hybrid_command(name="resume", description="Resume playback")
    async def resume(self, ctx):
        lavalink = self._get_lavalink()
        if not lavalink:
            return
        player = lavalink.get_player(ctx.guild.id)
        if player and player.paused:
            await player.resume()
            await ctx.send("▶️ Resumed.", delete_after=10)

    @commands.hybrid_command(name="queue", aliases=["q"], description="Show queue")
    async def queue(self, ctx):
        lavalink = self._get_lavalink()
        if not lavalink:
            return
        player = lavalink.get_player(ctx.guild.id)
        if not player or not player.queue:
            await ctx.send("Queue is empty.", delete_after=10)
            return
        items = "\n".join(f"{i+1}. {t.title}" for i, t in enumerate(player.queue[:10]))
        remaining = f"\n... and {len(player.queue)-10} more" if len(player.queue) > 10 else ""
        await ctx.send(f"**Queue:**\n{items}{remaining}", delete_after=30)

    @commands.hybrid_command(name="disconnect", aliases=["dc"], description="Disconnect from voice")
    async def disconnect(self, ctx):
        lavalink = self._get_lavalink()
        if not lavalink:
            return
        player = lavalink.get_player(ctx.guild.id)
        if player:
            await player.stop()
            await player.disconnect()
            await ctx.send("👋 Disconnected.", delete_after=10)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
'''
