#!/usr/bin/env python3
"""
Discord Bot Builder - Modular TUI Wizard
Generates a complete discord.py bot from modular feature files.

Usage: python build_bot.py
Output: A fully functional Discord bot with selected cogs.
"""

import sys, os, json, time, importlib.util
from pathlib import Path
from collections import OrderedDict

# === Auto-install deps ===
def _ensure(*packages):
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages"] + missing)

_ensure("questionary", "rich")

import questionary
from questionary import confirm, select, text, checkbox
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.rule import Rule
from rich.text import Text

console = Console()

FEATURES_DIR = Path(__file__).parent / "features"

# === Feature Discovery ===

def load_all_features():
    """Import all feature files from features/ and return their metadata."""
    features = {}
    if not FEATURES_DIR.exists():
        console.print(f"[red]Error:[/] features directory not found at {FEATURES_DIR}")
        sys.exit(1)

    for fp in sorted(FEATURES_DIR.glob("*.py")):
        if fp.name.startswith("_"):
            continue

        spec = importlib.util.spec_from_file_location(fp.stem, fp)
        mod = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(mod)
        except (SyntaxError, ImportError) as e:
            console.print(f"[yellow]Warning:[/] Skipping {fp.name} — {e}")
            continue

        fid = getattr(mod, "FEATURE_ID", None)
        if not fid:
            continue

        features[fid] = {
            "id": fid,
            "name": getattr(mod, "FEATURE_NAME", fid),
            "category": getattr(mod, "CATEGORY", "Other"),
            "description": getattr(mod, "DESCRIPTION", ""),
            "code": getattr(mod, "BLOCK_CODE", ""),
            "env_vars": getattr(mod, "ENV_VARS", []),
            "dependencies": getattr(mod, "DEPENDENCIES", []),
        }

    return features


# === TUI Steps ===

def step_intro():
    console.print(Panel.fit(
        "[bold cyan]Discord Bot Builder[/]\n\n"
        "Build a feature-rich Discord bot in minutes.\n"
        "Select features, review, generate — done.",
        border_style="cyan", box=box.DOUBLE,
    ))

def step_bot_name():
    console.print(Rule("[bold cyan]Step 1 — Bot Identity[/]"))
    name = text(
        "Bot name (2-32 chars)",
        default="MyAwesomeBot",
        validate=lambda s: 2 <= len(s) <= 32,
    ).ask()
    return name

def step_prefix():
    console.print(Rule("[bold cyan]Step 2 — Command Prefix[/]"))
    prefix = text(
        "Text command prefix",
        default="!",
        validate=lambda s: 0 < len(s) <= 5,
    ).ask()
    return prefix

def step_features(all_features):
    """Category-based feature selection with toggles and count."""
    console.print(Rule("[bold cyan]Step 3 — Feature Selection[/]"))

    # Show category toggle first
    method = select(
        "How would you like to select features?",
        choices=[
            {"name": "By Category (select whole categories)", "value": "category"},
            {"name": "Full Checklist (pick individual features)", "value": "full"},
            {"name": "Quick Presets", "value": "preset"},
        ],
    ).ask()

    if method == "preset":
        return step_presets(all_features)

    # Organize by category
    categories = OrderedDict()
    for fid, feat in sorted(all_features.items()):
        cat = feat["category"]
        categories.setdefault(cat, [])
        categories[cat].append(feat)

    if method == "category":
        selected = []
        # Show categories for bulk-select
        cat_choices = []
        for cat_name, feats in categories.items():
            feat_list = ", ".join(f["name"] for f in feats)
            cat_choices.append({"name": f"{cat_name} ({len(feats)} features: {feat_list})", "value": cat_name})

        chosen_cats = checkbox(
            "Select categories (Space to toggle, Enter to confirm)",
            choices=cat_choices,
        ).ask()

        for cat in chosen_cats or []:
            for feat in categories.get(cat, []):
                selected.append(feat["id"])

        # Show count
        console.print(f"\n  [green]{len(selected)} features selected[/] from {len(chosen_cats or [])} categories")
        return selected

    else:
        # Full checklist
        all_choices = []
        current_cat = None
        for cat_name, feats in categories.items():
            if cat_name != current_cat:
                # Add a separator-like choice
                all_choices.append(questionary.Choice(
                    title=[("class:bold", f"▸ {cat_name}")],
                    disabled="───────────────"
                ))
                current_cat = cat_name
            for feat in feats:
                all_choices.append({
                    "name": f"  {feat['name']} — {feat['description'][:60]}",
                    "value": feat["id"],
                })

        # Toggle ALL option
        all_choices.insert(0, {"name": "[bold yellow]🌟 SELECT ALL FEATURES[/]", "value": "__ALL__"})
        all_choices.insert(1, {"name": "[dim]❌ DESELECT ALL[/]", "value": "__NONE__"})

        selected = checkbox(
            f"Select features ({len(all_features)} available)",
            choices=all_choices,
            validate=lambda xs: len([x for x in xs if not x.startswith("__")]) >= 1 if xs else False,
        ).ask()

        if "__ALL__" in (selected or []):
            return [f["id"] for f in all_features.values()]
        if "__NONE__" in (selected or []):
            return []

        # Remove special markers
        selected = [s for s in (selected or []) if not s.startswith("__")]
        console.print(f"\n  [green]{len(selected)} features selected[/]")
        return selected


def step_presets(all_features):
    """Quick preset selection."""
    presets = {
        "Minimal": ["moderation", "welcome", "logging"],
        "Community": ["moderation", "welcome", "logging", "automod", "polls", "leveling", "fun", "starboard", "tickets", "announce", "autoroles", "reaction_roles", "afk"],
        "Gaming": ["moderation", "welcome", "leveling", "fun", "polls", "giveaways", "economy", "counting_game", "roleplay", "temp_voice", "server_stats"],
        "Business": ["moderation", "welcome", "logging", "tickets", "announce", "forms", "scheduled_msgs", "tags", "suggestions", "role_management"],
        "Production": ["moderation", "welcome", "logging", "tickets", "polls", "starboard", "announce", "scheduled_msgs", "forms", "autoroles", "reaction_roles", "reminders"],
        "Music-Focused": ["music", "moderation", "welcome", "playlists", "temp_voice", "fun"],
        "Economy Server": ["economy", "giveaways", "leveling", "shop", "fun", "moderation", "welcome", "daily"],
        "Everything": list(all_features.keys()),
    }

    chosen = select(
        "Choose a preset",
        choices=[{"name": f"{name} ({len(ids)} features)", "value": name} for name, ids in presets.items()] +
                [{"name": "Custom Selection", "value": "__CUSTOM__"}],
    ).ask()

    if chosen == "__CUSTOM__":
        return step_features(all_features)

    result = [fid for fid in presets[chosen] if fid in all_features]
    console.print(f"\n  [green]{len(result)} features selected[/] from preset '{chosen}'")
    return result


def step_review(config, all_features):
    """Review selections before generating."""
    console.print(Rule("[bold cyan]Step 4 — Review[/]"))

    table = Table(title="Configuration Summary", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Bot Name", config["bot_name"])
    table.add_row("Prefix", config["prefix"])
    table.add_row("Features", f"{len(config['features'])} selected")

    console.print(table)

    # Feature breakdown by category
    categories = OrderedDict()
    for fid in sorted(config["features"]):
        feat = all_features.get(fid)
        if feat:
            categories.setdefault(feat["category"], [])
            categories[feat["category"]].append(feat["name"])

    console.print()
    for cat, names in categories.items():
        console.print(f"  [bold]{cat}[/]: {', '.join(names)}")

    console.print()
    proceed = confirm("Generate bot?", default=True).ask()
    return proceed


# === Code Generation ===

def _collect_imports(config, all_features):
    """Determine needed imports."""
    imports = {
        "os": "import os",
        "json": "import json",
        "random": "import random",
        "time": "import time",
        "logging": "import logging",
        "asyncio": "import asyncio",
        "pathlib": "from pathlib import Path",
        "datetime": "from datetime import timedelta, datetime",
        "discord": "import discord",
        "commands": "from discord.ext import commands",
    }

    # Check if any feature uses app_commands
    extra = set()
    for fid in config["features"]:
        code = all_features[fid]["code"]
        if "commands.hybrid_command" in code or "app_commands" in code:
            extra.add("from discord import app_commands")
        if "requests" in code:
            extra.add("import requests")

    return imports, extra


def _get_intent_flags(config, all_features):
    """Determine which intents are needed."""
    intents = ["discord.Intents.default()"]
    needs = {"message_content": False, "members": False, "presences": False}

    combined_code = " ".join(all_features[fid]["code"] for fid in config["features"])

    if "on_message" in combined_code or "message.content" in combined_code:
        needs["message_content"] = True
    if "on_member_join" in combined_code or "on_member_remove" in combined_code or "on_member_update" in combined_code or "edit(nick=" in combined_code:
        needs["members"] = True
    if "presences" in combined_code or "on_presence_update" in combined_code:
        needs["presences"] = True

    for flag, needed in needs.items():
        if needed:
            intents.append(f"intents.{flag} = True")

    return intents


def _collect_requirements(config, all_features):
    """Collect pip dependencies from selected features."""
    deps = set()
    for fid in config["features"]:
        for dep in all_features[fid].get("dependencies", []):
            deps.add(dep)
        # Special handling
        code = all_features[fid]["code"]
        if "from deep_translator" in code:
            deps.add("deep-translator")
        if "yfinance" in code:
            deps.add("yfinance")
        if "flask" in code.lower():
            deps.add("flask")
    deps.discard("requests")  # bundled with Python
    return sorted(deps)


def _collect_env_vars(config, all_features):
    """Collect all env vars from selected features."""
    envs = ["DISCORD_BOT_TOKEN"]
    for fid in config["features"]:
        for var in all_features[fid].get("env_vars", []):
            if var not in envs:
                envs.append(var)
    return envs


def generate_bot_code(config, all_features):
    """Generate the full bot.py code from selected features."""
    imports, extra_imports = _collect_imports(config, all_features)
    intents = _get_intent_flags(config, all_features)
    deps = _collect_requirements(config, all_features)
    env_vars = _collect_env_vars(config, all_features)
    features_list = config["features"]

    lines = []

    # === HEADER ===
    lines.append("#!/usr/bin/env python3")
    lines.append('"""')
    lines.append(f"Generated by Discord Bot Builder")
    lines.append(f"Bot: {config['bot_name']} | Prefix: {config['prefix']}")
    lines.append(f"Features ({len(features_list)}): {', '.join(sorted(features_list))}")
    lines.append('"""')
    lines.append("")

    # === IMPORTS ===
    for key in sorted(imports.keys()):
        lines.append(imports[key])
    for ext in sorted(extra_imports):
        lines.append(ext)
    lines.append("")
    lines.append("from dotenv import load_dotenv")
    lines.append("load_dotenv()")
    lines.append("")

    # === LOGGING ===
    lines.append("# === Logging ===")
    lines.append("logging.basicConfig(")
    lines.append("    level=logging.INFO,")
    lines.append("    format='[%(asctime)s] %(levelname)s: %(message)s',")
    lines.append("    datefmt='%H:%M:%S',")
    lines.append(")")
    lines.append("log = logging.getLogger(__name__)")
    lines.append("")

    # === CONFIG ===
    lines.append("# === Config ===")
    lines.append(f'BOT_NAME = os.getenv("BOT_NAME", "{config["bot_name"]}")')
    lines.append(f'PREFIX = os.getenv("PREFIX", "{config["prefix"]}")')
    lines.append('TOKEN = os.getenv("DISCORD_BOT_TOKEN")')
    lines.append("")
    lines.append("if not TOKEN:")
    lines.append('    log.critical("DISCORD_BOT_TOKEN not set in environment or .env file!")')
    lines.append("    sys.exit(1)")
    lines.append("")
    lines.append("# Create data directory")
    lines.append("Path('data').mkdir(parents=True, exist_ok=True)")
    lines.append("")

    # === INTENTS ===
    lines.append("# === Intents ===")
    for line in intents:
        lines.append(line)
    lines.append("")

    # === BOT CLASS ===
    lines.append("# === Bot ===  ")
    lines.append("class Bot(commands.Bot):")
    lines.append("    def __init__(self):")
    lines.append("        super().__init__(")
    lines.append("            command_prefix=PREFIX,")
    lines.append("            intents=intents,")
    lines.append("            help_command=None,")
    lines.append("        )")
    lines.append("        self.start_time = None")
    lines.append("")
    lines.append("    async def setup_hook(self):")
    lines.append("        self.start_time = discord.utils.utcnow()")
    lines.append(f"        log.info(f\'{{BOT_NAME}} is starting...\')")
    lines.append("")

    # Load each selected feature as a cog
    for fid in sorted(features_list):
        feat = all_features.get(fid, {})
        name = feat.get("name", fid)
        lines.append(f"        # Loading: {name}")
        lines.append(f"        try:")
        lines.append(f"            await self.load_extension('builtin_cogs.{fid}')")
        lines.append(f"            log.info(f'  ✅ {name}')")
        lines.append(f"        except Exception as exc:")
        lines.append(f"            log.warning(f'  ⚠️ {name}: {{exc}}')")
        lines.append("")

    lines.append("    async def on_ready(self):")
    lines.append("        log.info(f'Logged in as {self.user} (ID: {self.user.id})')")
    lines.append("        log.info(f'Latency: {round(self.latency * 1000)}ms')")
    lines.append("        log.info(f'Servers: {len(self.guilds)}')")
    lines.append("        log.info(f'Cogs loaded: {len(self.cogs)}')")
    lines.append("        await self.change_presence(")
    pfx = config['prefix']
    lines.append('            activity=discord.Activity(type=discord.ActivityType.listening, name=f"' + pfx + 'help"),')
    lines.append("            status=discord.Status.online")
    lines.append("        )")
    lines.append("        # Sync commands")
    lines.append("        try:")
    lines.append("            synced = await self.tree.sync()")
    lines.append("            log.info(f'Synced {len(synced)} slash commands')")
    lines.append("        except Exception as e:")
    lines.append("            log.error(f'Failed to sync commands: {e}')")
    lines.append("")
    lines.append("    def run_bot(self):")
    lines.append("        self.run(TOKEN, reconnect=True)")
    lines.append("")

    lines.append("bot = Bot()")
    lines.append("")

    # === HELP COMMAND ===
    lines.append("# === Built-in Help ===")
    lines.append("@bot.command(name='help', aliases=['h'])")
    lines.append("async def help_cmd(ctx: commands.Context):")
    lines.append("    \"\"\"Show all available commands by category.\"\"\"")
    lines.append('    embed = discord.Embed(')
    bname = config['bot_name']
    pfx = config['prefix']
    lines.append('        title=f"' + bname + ' Help",')
    lines.append('        description=f\'Prefix: `' + pfx + '` | ' + str(len(features_list)) + ' features active\',')
    lines.append("        color=discord.Color.blue(),")
    lines.append("        timestamp=discord.utils.utcnow(),")
    lines.append("    )")

    # Group commands by category
    categories = OrderedDict()
    for fid in sorted(features_list):
        feat = all_features.get(fid, {})
        cat = feat.get("category", "Other")
        name = feat.get("name", fid)
        categories.setdefault(cat, [])
        categories[cat].append(f"`/{fid}` {name}")

    for cat, items in categories.items():
        items_str = '\\n'.join(items)
        lines.append("    embed.add_field(name='" + cat.replace(chr(39), '\\' + chr(39)) + "', value='" + items_str.replace(chr(39), '\\' + chr(39)) + "', inline=False)")

    lines.append("    embed.set_footer(text='Built with Discord Bot Builder')")
    lines.append("    await ctx.send(embed=embed)")
    lines.append("")

    # === MAIN GUARD ===
    lines.append("# === Run ===  ")
    lines.append("if __name__ == '__main__':")
    lines.append("    try:")
    lines.append("        bot.run_bot()")
    lines.append("    except KeyboardInterrupt:")
    lines.append("        log.info('Shutting down...')")
    lines.append("    except discord.LoginFailure:")
    lines.append("        log.critical('Invalid token. Check your DISCORD_BOT_TOKEN.')")
    lines.append("    except Exception as e:")
    lines.append("        log.critical(f'Fatal error: {e}')")

    return "\n".join(lines)


def generate_cog_wrapper(feature_id, code_block):
    """Wrap a feature code block as a proper cog module file."""
    return f'''"""
{feature_id} cog — auto-generated by Discord Bot Builder
"""
import discord
from discord.ext import commands
import os, json, random, time, asyncio, logging
from pathlib import Path
from datetime import timedelta, datetime

{code_block.strip()}
'''


def generate_env_file(env_vars):
    """Generate .env file with all needed variables."""
    lines = ["# Environment variables for your Discord bot", ""]

    if "DISCORD_BOT_TOKEN" in env_vars:
        lines.append("# Bot token (REQUIRED)")
        lines.append("DISCORD_BOT_TOKEN=your_bot_token_here")
        lines.append("")

    sections = {
        "WELCOME_CHANNEL_ID": ("# Welcome", "WELCOME_CHANNEL_ID=0", "LEAVE_CHANNEL_ID=0", 'WELCOME_MSG=Welcome {user} to {server}!', 'LEAVE_MSG={user} has left the server.'),
        "LOG_CHANNEL_ID": ("# Logging", "LOG_CHANNEL_ID=0"),
        "STARBOARD_CHANNEL": ("# Starboard", "STARBOARD_CHANNEL=0", "STAR_TRIGGER=3"),
        "TICKET_CATEGORY_ID": ("# Tickets", "TICKET_CATEGORY_ID=0", "TICKET_LOG_CH=0", "TICKET_STAFF_ROLE=0"),
        "LAVALINK_HOST": ("# Lavalink (Music)", "LAVALINK_HOST=localhost", "LAVALINK_PORT=2333", "LAVALINK_PASSWORD=youshallnotpass"),
        "BAD_WORDS": ("# Auto-Mod", "BAD_WORDS=", "ANTI_SPAM_MAX=5", "ANTI_SPAM_SECS=10", "BLOCK_LINKS=false", "BLOCK_INVITES=false", "AUTOMOD_IGNORE_CHANNELS="),
        "ECONOMY_CURRENCY_NAME": ("# Economy", 'ECONOMY_CURRENCY_NAME=Coins', 'ECONOMY_CURRENCY_SYMBOL=🪙'),
        "BIRTHDAY_CHANNEL_ID": ("# Birthday", "BIRTHDAY_CHANNEL_ID=0"),
        "SUGGESTIONS_CHANNEL_ID": ("# Suggestions", "SUGGESTIONS_CHANNEL_ID=0"),
        "DASHBOARD_PORT": ("# Dashboard", "DASHBOARD_PORT=5000", "DASHBOARD_HOST=0.0.0.0"),
        "TEMP_VOICE_CATEGORY_ID": ("# Temp Voice", "TEMP_VOICE_CATEGORY_ID=0"),
        "YOUTUBE_CHECK_INTERVAL": ("# YouTube Notifications", "YOUTUBE_CHECK_INTERVAL=300"),
        "FORMS_LOG_CHANNEL": ("# Forms", "FORMS_LOG_CHANNEL=0"),
        "AUTO_THREAD_CHANNELS": ("# Thread Management", "AUTO_THREAD_CHANNELS="),
        "VOICE_LINK_CATEGORY_ID": ("# Voice Text Linking", "VOICE_LINK_CATEGORY_ID=0"),
        "CHATBOT_CHANNELS": ("# Chatbot", "CHATBOT_CHANNELS="),
        "LEVELING_COOLDOWN": ("# Leveling", "LEVELING_COOLDOWN=60", "LEVELING_XP_MIN=15", "LEVELING_XP_MAX=25"),
    }

    done_sections = set()
    for var in env_vars:
        for trigger_var, section_data in sections.items():
            if trigger_var in done_sections:
                continue
            if any(trigger_var in d for d in section_data):
                done_sections.add(trigger_var)
                lines.append(section_data[0])
                for d in section_data[1:]:
                    if d.split("=")[0] in env_vars:
                        lines.append(d)
                lines.append("")

    # Any leftover env vars not in sections
    remaining = [v for v in env_vars if v != "DISCORD_BOT_TOKEN" and not any(v in " ".join(s) for s in sections.values())]
    if remaining:
        lines.append("# Other")
        for var in remaining:
            lines.append(f"{var}=")
        lines.append("")

    lines.append("# Bot config")
    lines.append("PREFIX=" + (config.get("prefix", "!") if 'config' in dir() else "!"))
    lines.append("BOT_NAME=" + (config.get("bot_name", "MyBot") if 'config' in dir() else "MyBot"))

    return "\n".join(lines)


def generate_env_file_final(env_vars, prefix="!", bot_name="MyBot"):
    """Generate .env file with actual config values."""
    lines = ["# Environment variables for your Discord bot", ""]
    lines.append("# Bot token (REQUIRED)")
    lines.append("DISCORD_BOT_TOKEN=your_bot_token_here")
    lines.append("")

    var_sections = {
        "WELCOME_CHANNEL_ID": ("# Welcome System", ["WELCOME_CHANNEL_ID=0", "LEAVE_CHANNEL_ID=0",
            'WELCOME_MSG=Welcome {user} to {server}!', 'LEAVE_MSG={user} has left the server.']),
        "LOG_CHANNEL_ID": ("# Logging", ["LOG_CHANNEL_ID=0"]),
        "STARBOARD_CHANNEL": ("# Starboard", ["STARBOARD_CHANNEL=0", "STAR_TRIGGER=3", 'STAR_EMOJI=⭐']),
        "TICKET_CATEGORY_ID": ("# Ticket System", ["TICKET_CATEGORY_ID=0", "TICKET_LOG_CH=0", "TICKET_STAFF_ROLE=0"]),
        "LAVALINK_HOST": ("# Lavalink (Music)", ["LAVALINK_HOST=localhost", "LAVALINK_PORT=2333", "LAVALINK_PASSWORD=youshallnotpass"]),
        "BAD_WORDS": ("# Auto-Moderation", ["BAD_WORDS=", "ANTI_SPAM_MAX=5", "ANTI_SPAM_SECS=10", "BLOCK_LINKS=false", "BLOCK_INVITES=false", "AUTOMOD_IGNORE_CHANNELS="]),
        "ECONOMY_CURRENCY_NAME": ("# Economy", ['ECONOMY_CURRENCY_NAME=Coins', 'ECONOMY_CURRENCY_SYMBOL=🪙']),
        "BIRTHDAY_CHANNEL_ID": ("# Birthdays", ["BIRTHDAY_CHANNEL_ID=0"]),
        "SUGGESTIONS_CHANNEL_ID": ("# Suggestions", ["SUGGESTIONS_CHANNEL_ID=0"]),
        "DASHBOARD_PORT": ("# Web Dashboard", ["DASHBOARD_PORT=5000", "DASHBOARD_HOST=0.0.0.0"]),
        "TEMP_VOICE_CATEGORY_ID": ("# Temporary Voice Channels", ["TEMP_VOICE_CATEGORY_ID=0"]),
        "YOUTUBE_CHECK_INTERVAL": ("# YouTube Notifications", ["YOUTUBE_CHECK_INTERVAL=300"]),
        "FORMS_LOG_CHANNEL": ("# Forms/Applications", ["FORMS_LOG_CHANNEL=0"]),
        "AUTO_THREAD_CHANNELS": ("# Thread Management", ["AUTO_THREAD_CHANNELS="]),
        "VOICE_LINK_CATEGORY_ID": ("# Voice-Text Linking", ["VOICE_LINK_CATEGORY_ID=0"]),
        "CHATBOT_CHANNELS": ("# Chatbot", ["CHATBOT_CHANNELS="]),
        "LEVELING_COOLDOWN": ("# Leveling System", ["LEVELING_COOLDOWN=60", "LEVELING_XP_MIN=15", "LEVELING_XP_MAX=25"]),
    }

    shown_sections = set()
    for var in env_vars:
        if var == "DISCORD_BOT_TOKEN":
            continue
        for trigger, (section_title, var_lines) in var_sections.items():
            if trigger in shown_sections:
                continue
            if any(l.startswith(var) for l in var_lines):
                shown_sections.add(trigger)
                lines.append(section_title)
                filtered = [l for l in var_lines if l.split("=")[0] in env_vars or l.split("=")[0].upper() in [v.upper() for v in env_vars]]
                for fl in filtered:
                    lines.append(fl)
                lines.append("")

    # Remaining env vars
    done_vars = set()
    for section_vars in var_sections.values():
        for vl in section_vars[1]:
            done_vars.add(vl.split("=")[0])
    remaining = [v for v in env_vars if v != "DISCORD_BOT_TOKEN" and v not in done_vars]
    if remaining:
        lines.append("# Additional")
        for var in remaining:
            lines.append(f"{var}=")
        lines.append("")

    lines.append("# Bot Configuration")
    lines.append(f"PREFIX={prefix}")
    lines.append(f"BOT_NAME={bot_name}")

    return "\n".join(lines)


def generate_requirements(depts):
    """Generate requirements.txt."""
    base = [
        "discord.py>=2.3.0",
        "python-dotenv>=1.0.0",
    ]
    return "\n".join(base + depts) + "\n"


# === Main Generator ===

def do_generate(output_dir, config, all_features):
    """Generate the complete bot project."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    features_list = config["features"]

    # 1. Write bot.py
    console.print("\n[bold]Generating bot.py...[/]")
    bot_code = generate_bot_code(config, all_features)
    (out / "bot.py").write_text(bot_code)
    console.print(f"  [green]✓[/] bot.py ({len(bot_code.splitlines())} lines)")

    # 2. Write cog files into builtin_cogs/
    cogs_dir = out / "builtin_cogs"
    cogs_dir.mkdir(parents=True, exist_ok=True)
    (cogs_dir / "__init__.py").write_text("# Built-in cogs generated by Discord Bot Builder\n")

    for fid in sorted(features_list):
        feat = all_features.get(fid)
        if not feat:
            continue
        code = feat["code"]
        cog_path = cogs_dir / f"{fid}.py"
        cog_path.write_text(generate_cog_wrapper(fid, code))
    console.print(f"  [green]✓[/] {len(features_list)} cog files in builtin_cogs/")

    # 3. Write .env
    env_vars = _collect_env_vars(config, all_features)
    env_content = generate_env_file_final(env_vars, config["prefix"], config["bot_name"])
    (out / ".env").write_text(env_content)
    console.print(f"  [green]✓[/] .env")

    # 4. Write requirements.txt
    deps = _collect_requirements(config, all_features)
    (out / "requirements.txt").write_text(generate_requirements(deps))
    console.print(f"  [green]✓[/] requirements.txt ({len(deps) + 2} packages)")

    # 5. Write README
    readme_content = generate_readme(config, features_list, all_features, deps)
    (out / "README.md").write_text(readme_content)
    console.print(f"  [green]✓[/] README.md")

    # Summary
    console.print(Panel.fit(
        "[green bold]Bot generated successfully![/]\n\n"
        f"Output: {out.resolve()}\n"
        f"Features: {len(features_list)}\n"
        f"Files: bot.py, builtin_cogs/, .env, requirements.txt, README.md\n\n"
        "Next steps:\n"
        f"  1. cd {out}\n"
        "  2. pip install -r requirements.txt\n"
        "  3. Edit .env with your bot token\n"
        "  4. python bot.py",
        border_style="green", box=box.DOUBLE,
    ))


def generate_readme(config, features_list, all_features, deps):
    """Generate a helpful README."""
    feature_names = [all_features[fid]["name"] for fid in sorted(features_list) if fid in all_features]

    return f"""# {config['bot_name']}

Generated by **Discord Bot Builder** — a modular Discord bot with {len(features_list)} features.

## Features ({len(features_list)})

{chr(10).join(f'- {name}' for name in feature_names)}

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your bot
cp .env.example .env  # or edit .env directly
nano .env  # Add your DISCORD_BOT_TOKEN

# Run the bot
python bot.py
```

## Configuration

Edit `.env` to customize your bot:

| Variable | Description |
|----------|-------------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token (required) |
| `PREFIX` | Text command prefix (default: `{config['prefix']}`) |
| `BOT_NAME` | Display name |

See `.env` for all configuration options.

## Dependencies

{chr(10).join(f'- `{d}`' for d in sorted(['discord.py', 'python-dotenv'] + deps))}

## Project Structure

```
.
├── bot.py              # Main bot entry point
├── builtin_cogs/       # Feature cogs (auto-generated)
├── data/               # Persistent data storage (created at runtime)
├── .env                # Environment configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

Built with ❤️ using Discord Bot Builder
"""


# === Main Entry Point ===

def main():
    os.system("cls" if os.name == "nt" else "clear")
    step_intro()

    all_features = load_all_features()
    if not all_features:
        console.print("[red]No features found![/] Check the features/ directory.")
        sys.exit(1)

    # Step 1: Bot name
    bot_name = step_bot_name()

    # Step 2: Prefix
    prefix = step_prefix()

    # Step 3: Features
    selected = step_features(all_features)
    if not selected:
        console.print("[yellow]No features selected. Exiting.[/]")
        return

    # Config
    config = {"bot_name": bot_name, "prefix": prefix, "features": selected}

    # Step 4: Review
    if not step_review(config, all_features):
        console.print("[yellow]Cancelled.[/]")
        return

    # Ask for output directory
    console.print(Rule("[bold cyan]Output Directory[/]"))
    default_dir = os.path.join(os.getcwd(), bot_name.replace(" ", "_").lower())
    output_dir = text("Where to generate the bot?", default=default_dir).ask()
    output_dir = os.path.expanduser(output_dir)

    # Generate!
    do_generate(output_dir, config, all_features)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        import traceback
        traceback.print_exc()
