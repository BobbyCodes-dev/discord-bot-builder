FEATURE_ID = "dashboard"
FEATURE_NAME = "Web Dashboard"
CATEGORY = "Utility"
DESCRIPTION = "Flask web dashboard showing guild info, member counts, feature toggles"
ENV_VARS = ["DASHBOARD_PORT", "DASHBOARD_HOST"]
DEPENDENCIES = ["flask"]

BLOCK_CODE = r'''
class DashboardCog(commands.Cog):
    _doc_ = "Web dashboard for bot stats."

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        port = int(os.getenv("DASHBOARD_PORT", "5000"))
        host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.bot.loop.create_task(self._run_dashboard(host, port))

    async def _run_dashboard(self, host, port):
        try:
            from flask import Flask, jsonify, render_template_string
        except ImportError:
            log.warning("Flask not installed for dashboard. Install: pip install flask")
            return

        app = Flask(__name__)
        bot = self.bot

        DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head><title>Bot Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#1a1b1e;color:#e0e0e0;min-height:100vh}
.container{max-width:1200px;margin:0 auto;padding:20px}
.header{background:#2c2d31;padding:20px;border-radius:12px;margin-bottom:20px}
.header h1{color:#7289da;margin-bottom:8px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:20px}
.stat-card{background:#2c2d31;padding:20px;border-radius:10px;text-align:center}
.stat-card .value{font-size:2em;font-weight:bold;color:#7289da}
.stat-card .label{color:#999;margin-top:5px}
.guild-card{background:#2c2d31;padding:15px;border-radius:10px;margin-bottom:10px;display:flex;align-items:center;gap:15px}
.guild-icon{width:48px;height:48px;border-radius:50%;background:#7289da;display:flex;align-items:center;justify-content:center;font-size:24px}
.guild-info{flex:1}
.guild-info h3{margin-bottom:4px}
.guild-info span{color:#999;font-size:.9em}
</style></head>
<body>
<div class="container">
<div class="header"><h1>Bot Dashboard</h1><p id="status">Loading...</p></div>
<div class="stats">
<div class="stat-card"><div class="value" id="guildCount">-</div><div class="label">Servers</div></div>
<div class="stat-card"><div class="value" id="memberCount">-</div><div class="label">Total Members</div></div>
<div class="stat-card"><div class="value" id="latency">-</div><div class="label">Latency (ms)</div></div>
<div class="stat-card"><div class="value" id="commands">-</div><div class="label">Commands</div></div>
</div>
<div id="guilds"></div>
</div>
<script>
async function load(){try{let r=await fetch('/api/stats');let d=await r.json();
document.getElementById('status').textContent='Online as '+d.bot_name;
document.getElementById('guildCount').textContent=d.guild_count;
document.getElementById('memberCount').textContent=d.total_members.toLocaleString();
document.getElementById('latency').textContent=d.latency;
document.getElementById('commands').textContent=d.command_count;
let ghtml='';for(let g of d.guilds){ghtml+=
'<div class="guild-card"><div class="guild-icon">'+(g.icon?'<img src="'+g.icon+'" style="width:48px;height:48px;border-radius:50%">':'')+'</div>'
+'<div class="guild-info"><h3>'+g.name+'</h3><span>'+g.member_count+' members &middot; '+g.channel_count+' channels</span></div></div>';}
document.getElementById('guilds').innerHTML=ghtml;}catch(e){document.getElementById('status').textContent='Error: '+e.message;}}
load();setInterval(load,30000);
</script></body></html>"""

        @app.route('/')
        def index():
            return render_template_string(DASHBOARD_HTML)

        @app.route('/api/stats')
        def stats():
            total_members = sum(g.member_count or 0 for g in bot.guilds)
            return jsonify({
                "bot_name": str(bot.user),
                "guild_count": len(bot.guilds),
                "total_members": total_members,
                "latency": round(bot.latency * 1000),
                "command_count": len(bot.tree.get_commands()),
                "guilds": [{
                    "name": g.name,
                    "id": str(g.id),
                    "member_count": g.member_count,
                    "channel_count": len(g.channels),
                    "icon": str(g.icon.url) if g.icon else None,
                } for g in bot.guilds[:25]],
            })

        log.info(f"Dashboard starting on http://{host}:{port}")
        from threading import Thread
        Thread(target=app.run, kwargs={"host": host, "port": port, "debug": False, "use_reloader": False}, daemon=True).start()

async def setup(bot):
    await bot.add_cog(DashboardCog(bot))
'''
