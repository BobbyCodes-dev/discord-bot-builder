FEATURE_ID = "tickets"
FEATURE_NAME = "Ticket System"
CATEGORY = "Utility"
DESCRIPTION = "Support ticket system with categories, transcripts, and staff management"
ENV_VARS = ["TICKET_CATEGORY_ID", "TICKET_LOG_CH", "TICKET_STAFF_ROLE"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class TicketCog(commands.Cog):
    """Support ticket system."""

    def __init__(self, bot):
        self.bot = bot
        self.category_id = int(os.getenv("TICKET_CATEGORY_ID", "0"))
        self.log_ch_id = int(os.getenv("TICKET_LOG_CH", "0"))
        self.staff_role_id = int(os.getenv("TICKET_STAFF_ROLE", "0"))
        self._open_tickets = {}

    @commands.hybrid_command(name="ticket", description="Open a support ticket")
    async def ticket(self, ctx, *, subject: str = "General Support"):
        uid = str(ctx.author.id)
        if uid in self._open_tickets:
            await ctx.send("You already have an open ticket.", delete_after=10)
            return

        cat = None
        if self.category_id:
            cat = ctx.guild.get_channel(self.category_id)

        staff_role = None
        if self.staff_role_id:
            staff_role = ctx.guild.get_role(self.staff_role_id)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ch = await ctx.guild.create_text_channel(
            f"ticket-{ctx.author.name}", category=cat, overwrites=overwrites,
            topic=f"Ticket by {ctx.author} | {subject}"
        )

        self._open_tickets[uid] = ch.id

        embed = discord.Embed(title="🎫 Ticket Created", description=f"**Subject:** {subject}\n**Created by:** {ctx.author.mention}\n\nPlease describe your issue. Staff will assist you shortly.", color=discord.Color.green())
        embed.set_footer(text="Use /close to close this ticket")
        await ch.send(content=ctx.author.mention, embed=embed)
        await ctx.send(f"Ticket created: {ch.mention}", delete_after=10)

    @commands.hybrid_command(name="close", description="Close the current ticket")
    async def close(self, ctx):
        if str(ctx.author.id) not in self._open_tickets and not ctx.author.guild_permissions.manage_messages:
            return

        ticket_owner = None
        for uid, ch_id in self._open_tickets.items():
            if ch_id == ctx.channel.id:
                ticket_owner = uid
                break

        if not ticket_owner:
            await ctx.send("This is not a ticket channel.", delete_after=10)
            return

        await ctx.send("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)

        if self.log_ch_id:
            log_ch = ctx.guild.get_channel(self.log_ch_id)
            if log_ch:
                messages = [msg async for msg in ctx.channel.history(limit=100, oldest_first=True)]
                transcript = "\n".join(f"[{m.created_at.strftime('%H:%M')}] {m.author}: {m.content}" for m in messages if m.content)
                log_embed = discord.Embed(title="Ticket Transcript", description=f"**User:** <@{ticket_owner}>\n**Channel:** {ctx.channel.name}", color=discord.Color.blurple())
                await log_ch.send(embed=log_embed)
                if transcript:
                    await log_ch.send(f"```\n{transcript[:1900]}\n```")

        del self._open_tickets[ticket_owner]
        await ctx.channel.delete()

    @commands.hybrid_command(name="adduser", description="Add a user to the ticket")
    @commands.has_permissions(manage_messages=True)
    async def adduser(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(f"Added {member.mention} to the ticket.", delete_after=10)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
'''
