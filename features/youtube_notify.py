FEATURE_ID = "youtube_notify"
FEATURE_NAME = "YouTube Notifications"
CATEGORY = "Utility"
DESCRIPTION = "Get notified in Discord when a YouTube channel uploads"
ENV_VARS = ["YOUTUBE_CHECK_INTERVAL"]
DEPENDENCIES = ["requests"]

BLOCK_CODE = r'''
class YouTubeNotifyCog(commands.Cog):
    """YouTube upload notifications via RSS."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/youtube_subs.json")
        self._subs = {}
        self._last_videos = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(self.data_file.read_text())
            self._subs = data.get("subs", {})
            self._last_videos = data.get("last_videos", {})
        except Exception:
            self._subs = {}
            self._last_videos = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps({"subs": self._subs, "last_videos": self._last_videos}, indent=2))

    @commands.hybrid_command(name="youtube", description="Manage YouTube notifications")
    @commands.has_permissions(manage_guild=True)
    async def youtube(self, ctx, action: str, channel_id: str = None, discord_channel: discord.TextChannel = None):
        if action.lower() == "add":
            if not channel_id or not discord_channel:
                await ctx.send("Usage: `/youtube add <youtube_channel_id> <discord_channel>`", delete_after=20)
                return

            gid = str(ctx.guild.id)
            self._subs.setdefault(gid, {})
            self._subs[gid][channel_id] = {
                "discord_channel_id": discord_channel.id,
                "added_by": ctx.author.id,
            }
            self._save()
            await ctx.send(f"Now watching YouTube channel `{channel_id}` → {discord_channel.mention}")

        elif action.lower() == "remove":
            if not channel_id:
                await ctx.send("Usage: `/youtube remove <youtube_channel_id>`", delete_after=20)
                return
            gid = str(ctx.guild.id)
            if gid in self._subs and channel_id in self._subs[gid]:
                del self._subs[gid][channel_id]
                self._save()
                await ctx.send(f"Stopped watching `{channel_id}`")
            else:
                await ctx.send("Channel not found in subscriptions.")

        elif action.lower() == "list":
            gid = str(ctx.guild.id)
            subs = self._subs.get(gid, {})
            if not subs:
                await ctx.send("No YouTube subscriptions.")
                return
            lines = [f"**{cid}** → <#{info['discord_channel_id']}>" for cid, info in subs.items()]
            await ctx.send("\n".join(lines))

    async def _check_youtube(self):
        try:
            import requests
        except ImportError:
            return

        for gid, channels in self._subs.items():
            for yt_channel_id, info in channels.items():
                try:
                    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={yt_channel_id}"
                    resp = requests.get(rss_url, timeout=15)
                    if resp.status_code != 200:
                        continue

                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}

                    entries = root.findall("atom:entry", ns)
                    if not entries:
                        continue

                    latest = entries[0]
                    video_id_elem = latest.find("atom:id", ns)
                    if video_id_elem is None:
                        continue
                    video_id = video_id_elem.text

                    if video_id == self._last_videos.get(yt_channel_id):
                        continue

                    self._last_videos[yt_channel_id] = video_id
                    self._save()

                    title = latest.find("atom:title", ns).text if latest.find("atom:title", ns) is not None else "New Video"
                    link = latest.find("atom:link", ns).attrib.get("href", "")
                    author = latest.find("atom:author/atom:name", ns)
                    author_name = author.text if author is not None else "Unknown"

                    guild = self.bot.get_guild(int(gid))
                    if guild:
                        channel = guild.get_channel(info["discord_channel_id"])
                        if channel:
                            msg = f"🎬 **{author_name}** uploaded a new video!\n📺 **{title}**\n{link}"
                            try:
                                await channel.send(msg)
                            except Exception:
                                pass
                except Exception:
                    continue

    @commands.Cog.listener()
    async def on_ready(self):
        interval = int(os.getenv("YOUTUBE_CHECK_INTERVAL", "300"))
        self.bot.loop.create_task(self._yt_loop(interval))

    async def _yt_loop(self, interval):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self._check_youtube()
            await asyncio.sleep(interval)

async def setup(bot):
    await bot.add_cog(YouTubeNotifyCog(bot))
'''
