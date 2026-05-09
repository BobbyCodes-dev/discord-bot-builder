FEATURE_ID = "forms"
FEATURE_NAME = "Forms & Applications"
CATEGORY = "Utility"
DESCRIPTION = "Create multi-question forms, collect responses to mod log"
ENV_VARS = ["FORMS_LOG_CHANNEL"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class FormsCog(commands.Cog):
    """Application forms system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/forms.json")
        self.log_channel_id = int(os.getenv("FORMS_LOG_CHANNEL", "0"))
        self._forms = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(self.data_file.read_text())
            self._forms = data.get("forms", {})
            self._responses = data.get("responses", {})
        except Exception:
            self._forms = {}
            self._responses = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps({"forms": self._forms, "responses": self._responses}, indent=2))

    @commands.hybrid_command(name="form", description="Create/manage forms")
    @commands.has_permissions(manage_messages=True)
    async def form(self, ctx, action: str, *, arg: str = None):
        gid = str(ctx.guild.id)

        if action.lower() == "create" and arg:
            await ctx.send(f"Creating form **{arg}**. Send one question per message. Type `done` when finished.")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            questions = []
            while True:
                try:
                    msg = await self.bot.wait_for("message", timeout=120, check=check)
                    if msg.content.lower() == "done":
                        break
                    questions.append(msg.content[:256])
                except asyncio.TimeoutError:
                    break

            if not questions:
                await ctx.send("No questions added. Form cancelled.")
                return

            fid = str(len(self._forms) + 1)
            self._forms.setdefault(gid, {})
            self._forms[gid][fid] = {
                "title": arg,
                "questions": questions,
                "created_by": ctx.author.id,
                "created_at": discord.utils.utcnow().isoformat(),
            }
            self._save()
            await ctx.send(f"✅ Form **{arg}** created with {len(questions)} questions! ID: `{fid}`\nUsers submit with: `/form submit {fid} <answer1> | <answer2> | ...`")

        elif action.lower() == "list":
            forms = self._forms.get(gid, {})
            if not forms:
                await ctx.send("No forms yet.")
                return
            lines = [f"**[{fid}] {info['title']}** — {len(info['questions'])} questions" for fid, info in forms.items()]
            await ctx.send("\n".join(lines))

        elif action.lower() == "submit" and arg:
            parts = arg.split("|")
            if len(parts) < 2:
                await ctx.send("Usage: `/form submit <form_id> <answer1> | <answer2> | ...`", delete_after=20)
                return

            fid = parts[0].strip()
            answers = [a.strip() for a in parts[1:]]

            form = self._forms.get(gid, {}).get(fid)
            if not form:
                await ctx.send(f"Form `{fid}` not found.", delete_after=10)
                return

            if len(answers) < len(form["questions"]):
                answers.extend([""] * (len(form["questions"]) - len(answers)))

            self._responses.setdefault(gid, {})
            self._responses[gid].setdefault(fid, [])
            response = {
                "user_id": ctx.author.id,
                "username": str(ctx.author),
                "answers": answers[:len(form["questions"])],
                "submitted_at": discord.utils.utcnow().isoformat(),
            }
            self._responses[gid][fid].append(response)
            self._save()

            # Log to forms channel
            log_ch = ctx.guild.get_channel(self.log_channel_id) if self.log_channel_id else None
            if log_ch:
                embed = discord.Embed(title=f"📋 Form Submission: {form['title']}", description=f"**Submitted by:** {ctx.author.mention}", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
                for i, q in enumerate(form["questions"]):
                    embed.add_field(name=q, value=answers[i] if i < len(answers) else "No answer", inline=False)
                embed.set_footer(text=f"Form ID: {fid}")
                await log_ch.send(embed=embed)

            await ctx.send("✅ Form submitted! Staff will review your response.")

        elif action.lower() == "responses" and arg:
            fid = arg.strip()
            responses = self._responses.get(gid, {}).get(fid, [])
            form = self._forms.get(gid, {}).get(fid)

            if not form:
                await ctx.send(f"Form `{fid}` not found.", delete_after=10)
                return
            if not responses:
                await ctx.send(f"No responses for **{form['title']}** yet.")
                return

            await ctx.send(f"**{form['title']}** — {len(responses)} responses. Sending summary...")

            for i, resp in enumerate(responses[-5:], 1):  # Latest 5
                lines = [f"**Q: {q}**\nA: {a}" for q, a in zip(form["questions"], resp["answers"])]
                embed = discord.Embed(title=f"Response #{i} from {resp['username']}", description="\n".join(lines), color=discord.Color.blue())
                embed.set_footer(text=f"Submitted {discord.utils.format_dt(datetime.fromisoformat(resp['submitted_at']), 'R')}")
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FormsCog(bot))
'''
