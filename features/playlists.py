FEATURE_ID = "playlists"
FEATURE_NAME = "Music Playlists"
CATEGORY = "Fun"
DESCRIPTION = "Save and load music queue playlists"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class PlaylistsCog(commands.Cog):
    """Saved music playlists system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/playlists.json")
        self._playlists = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._playlists = json.loads(self.data_file.read_text())
        except Exception:
            self._playlists = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._playlists, indent=2))

    @commands.hybrid_command(name="playlist", description="Manage saved music playlists")
    async def playlist(self, ctx, action: str = None, *, name: str = None):
        gid = str(ctx.guild.id)
        self._playlists.setdefault(gid, {})

        if action and name:
            if action.lower() == "save":
                # Get current queue from music cog
                music_cog = self.bot.get_cog("MusicCog")
                if not music_cog:
                    await ctx.send("Music system not active. Enable the Music feature.", delete_after=15)
                    return

                try:
                    import lavalink
                    player = lavalink.get_player(ctx.guild.id)
                    if not player or not player.queue:
                        await ctx.send("Queue is empty! Queue up some songs first.", delete_after=15)
                        return
                    tracks = [{"title": t.title, "uri": t.uri, "author": t.author} for t in player.queue]
                except Exception:
                    await ctx.send("Could not access queue. Make sure Lavalink is running.", delete_after=15)
                    return

                self._playlists[gid][name.lower()] = {
                    "name": name,
                    "tracks": tracks,
                    "saved_by": ctx.author.id,
                    "saved_at": discord.utils.utcnow().isoformat(),
                }
                self._save()
                await ctx.send(f"💾 Saved playlist **{name}** with {len(tracks)} tracks!")

            elif action.lower() == "load":
                playlist = self._playlists[gid].get(name.lower())
                if not playlist:
                    await ctx.send(f"Playlist `{name}` not found.", delete_after=10)
                    return

                music_cog = self.bot.get_cog("MusicCog")
                if not music_cog:
                    await ctx.send("Music system not active.", delete_after=15)
                    return

                if not ctx.author.voice:
                    await ctx.send("Join a voice channel first!", delete_after=10)
                    return

                try:
                    import lavalink
                    lavalink.initialize(bot=self.bot)
                    node = lavalink.get_best_node()
                    if not node:
                        await ctx.send("No music node available.", delete_after=10)
                        return

                    player = node.get_player(ctx.guild.id)
                    if not player.is_connected:
                        await player.connect(ctx.author.voice.channel.id)

                    count = 0
                    for track in playlist["tracks"]:
                        results = await node.fetch_tracks(f"ytsearch:{track['title']} {track['author']}")
                        if results:
                            player.add_track(results[0])
                            count += 1

                    if not player.is_playing:
                        await player.play()

                    await ctx.send(f"📂 Loaded {count}/{len(playlist['tracks'])} tracks from **{name}**!")
                except Exception as e:
                    await ctx.send(f"Could not load playlist: {e}", delete_after=15)

            elif action.lower() == "delete":
                if name.lower() in self._playlists[gid]:
                    del self._playlists[gid][name.lower()]
                    self._save()
                    await ctx.send(f"🗑️ Deleted playlist **{name}**.")
                else:
                    await ctx.send(f"Playlist `{name}` not found.", delete_after=10)

        else:  # List
            playlists = self._playlists.get(gid, {})
            if not playlists:
                await ctx.send("No saved playlists. Save one with `/playlist save <name>`", delete_after=15)
                return

            lines = [f"**{info['name']}** — {len(info['tracks'])} tracks (saved <t:{int(datetime.fromisoformat(info['saved_at']).timestamp())}:R>)" for info in playlists.values()]
            embed = discord.Embed(title=f"📂 Playlists in {ctx.guild.name}", description="\n".join(lines), color=discord.Color.blue())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PlaylistsCog(bot))
'''
