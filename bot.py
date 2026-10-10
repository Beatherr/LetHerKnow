import os
import time
import json
import asyncio
from datetime import datetime

import discord
from discord.ext import commands, tasks
from aiohttp import web

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "change_this_to_your_bot_token")
ACTIVITY_KEY = os.getenv("ACTIVITY_KEY", "01171120")
PORT = int(os.getenv("ACTIVITY_PORT", "8765"))

STATUS_CHANNEL_ID = 1546911935159730287

ALLOWED_USER_IDS = [
    938000353474007092,
    1386274640229568572
]

RELATIONSHIP_START_DATE = datetime(2026, 8, 17)  # Çıkma tarihiniz
SONG_URL = "https://open.spotify.com/intl-tr/track/4cUO8hsSg24RxA0mr3k9Nl?si=3c4a43c7c36f4ada"  # Özel şarkınızın linki

# Belirttiğin Hassas Konum Koordinatları
WEATHER_COORDS = "40.707285,30.114843"

# --- EMBED GÖRSEL LİNKLERİ (İstediğin GIF/Fotoğraf Linkleriyle Değiştirebilirsin) ---
THUMBNAIL_ONLINE = "https://cdn.discordapp.com/attachments/1533821318175264879/1554148400864301137/9CBCDFC8-4AE4-4BB2-8B39-D9DE734E339B.jpg?ex=6abd267d&is=6abbd4fd&hm=86c8009b05b70d64e65b89b2b653953f07c2db50f030a9ffe176b35705d0da87&"
THUMBNAIL_OFFLINE = "https://klipy.com/gifs/cat-kitty-575"
BANNER_URL = "https://cdn.discordapp.com/attachments/1533821318175264879/1554148400864301137/9CBCDFC8-4AE4-4BB2-8B39-D9DE734E339B.jpg?ex=6abd267d&is=6abbd4fd&hm=86c8009b05b70d64e65b89b2b653953f07c2db50f030a9ffe176b35705d0da87&"  # Veya tatlı bir anime/aesthetic banner linki

latest = {
    "online": False,
    "username": "Unknown",
    "hostname": "Unknown",
    "active_window": "Unknown",
    "process": "Unknown",
    "game": None,
    "game_started": None,
    "cpu": None,
    "ram": None,
    "uptime": None,
    "idle_seconds": 0,
    "open_windows": [],
    "media": None,
    "updated": None,
}

weather_cache = {"temp": "Unknown", "condition": "Unknown", "last_fetch": 0}

last_seen = 0
status_message_id = None
MESSAGE_FILE = "status_message.json"
is_shutting_down_mode = False

update_lock = asyncio.Lock()

# Pembe Renk Paleti (Hex)
PINK_OFFLINE = 0xF47FFF   # Yumuşak Pembe/Mor (Offline)
PINK_ACTIVE = 0xFF69B4    # Canlı Pembe (Active)
PINK_AFK = 0xFFB6C1       # Pastel Pembe (AFK)

def load_message_id():
    global status_message_id
    if os.path.exists(MESSAGE_FILE):
        try:
            with open(MESSAGE_FILE, "r") as f:
                status_message_id = json.load(f).get("message_id")
        except Exception:
            pass

def save_message_id(msg_id):
    global status_message_id
    status_message_id = msg_id
    with open(MESSAGE_FILE, "w") as f:
        json.dump({"message_id": msg_id}, f)

def duration(seconds):
    if seconds is None:
        return "Unknown"
    seconds = max(0, int(seconds))
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h > 0:
        return f"{h}h {m}m"
    elif m > 0:
        return f"{m}s"
    return f"{s}s"

async def fetch_weather():
    now = time.time()
    if now - weather_cache["last_fetch"] < 900 and weather_cache["temp"] != "Unknown":
        return weather_cache

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{WEATHER_COORDS}?format=%C+%t", timeout=5) as resp:
                if resp.status == 200:
                    text = (await resp.text()).strip()
                    parts = text.split(" ")
                    if len(parts) >= 2:
                        weather_cache["condition"] = " ".join(parts[:-1])
                        weather_cache["temp"] = parts[-1]
                    else:
                        weather_cache["temp"] = text
                    weather_cache["last_fetch"] = now
    except Exception:
        pass
    return weather_cache

def build_embed():
    is_pc_online = latest["online"] and (time.time() - last_seen < 10)
    idle_time = latest.get("idle_seconds", 0)
    is_afk = is_pc_online and (idle_time > 180)

    if not is_pc_online:
        embed = discord.Embed(
            title="🎀 ── PC Offline ── 🎀",
            description="*Poyraz is currently away from his PC, missing you!* ✨\n\n🌸 ────────────────────── 🌸",
            color=PINK_OFFLINE
        )
        embed.set_thumbnail(url=THUMBNAIL_OFFLINE)
        embed.set_footer(text="Te iubesc Andrea 💕 • Waiting for him to come back...")
        return embed

    if is_afk:
        title = "🥐 ── PC Online (Taking a Break) ── 🎀"
        color = PINK_AFK
    else:
        title = "🌸 ── PC Online & Active ── 🎀"
        color = PINK_ACTIVE

    embed = discord.Embed(
        title=title,
        description="*Press Refresh below to update status* ✨\n\n🌸 ────────────────────── 🌸",
        color=color
    )
    embed.set_thumbnail(url=THUMBNAIL_ONLINE)

    days_together = (datetime.now() - RELATIONSHIP_START_DATE).days
    embed.add_field(
        name="💞 Love Counter",
        value=f"Together for **{days_together}** magical days 💖",
        inline=False
    )

    embed.add_field(
        name="🎮 Currently Playing",
        value=f"**{latest['game']}**" if latest["game"] else "Not playing anything 🧸",
        inline=True
    )
    embed.add_field(
        name="🪟 Active Window",
        value=f"`{latest['active_window']}`" if latest["active_window"] else "Unknown",
        inline=True
    )

    if latest["media"]:
        embed.add_field(
            name="🎶 Listening / Watching",
            value=f"```{latest['media']}```",
            inline=False
        )

    if latest["open_windows"]:
        windows_str = "\n".join([f"🌸 {w}" for w in latest["open_windows"]])
        embed.add_field(
            name="📋 Open Windows & Apps",
            value=f"```\n{windows_str}\n```",
            inline=False
        )

    if latest["game"] and latest["game_started"]:
        embed.add_field(
            name="⏱️ Playtime",
            value=f"**{duration(time.time() - latest['game_started'])}**",
            inline=True
        )

    if is_afk:
        embed.add_field(
            name="💤 AFK Duration",
            value=f"**{duration(idle_time)}**",
            inline=True
        )

    embed.add_field(
        name="⚡ CPU Usage",
        value=f"`{latest['cpu']:.1f}%`" if latest["cpu"] is not None else "Unknown",
        inline=True
    )
    embed.add_field(
        name="🧠 RAM Usage",
        value=f"`{latest['ram']:.1f}%`" if latest["ram"] is not None else "Unknown",
        inline=True
    )
    embed.add_field(
        name="⏳ PC Uptime",
        value=f"`{duration(latest['uptime'])}`",
        inline=True
    )

    if weather_cache["temp"] != "Unknown":
        embed.add_field(
            name="🌤️ Local Weather",
            value=f"{weather_cache['condition']} **{weather_cache['temp']}**",
            inline=True
        )

    current_hour = datetime.now().hour
    if current_hour >= 23 or current_hour < 6:
        embed.add_field(
            name="🌙 Late Night Alert",
            value="It's getting late, Poyraz is still awake! Send him to sleep 😴💖",
            inline=False
        )

    embed.add_field(
        name="💻 User / Hostname",
        value=f"`{latest['username']}` @ `{latest['hostname']}`",
        inline=False
    )

    embed.set_footer(
        text=f'Last Update: {latest["updated"] or "Never"} • Te iubesc Andrea 💕'
    )
    return embed

class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.update_buttons()

    def update_buttons(self):
        current_hour = datetime.now().hour
        is_late_night = current_hour >= 23 or current_hour < 6

        bedtime_btn_exists = any(item.custom_id == "bedtime_btn" for item in self.children)

        if is_late_night and not bedtime_btn_exists:
            bedtime_button = discord.ui.Button(
                label="🛌 Send Him to Bed",
                style=discord.ButtonStyle.danger,
                custom_id="bedtime_btn",
                row=1
            )
            bedtime_button.callback = self.bedtime_button_callback
            self.add_item(bedtime_button)
        elif not is_late_night and bedtime_btn_exists:
            for child in self.children:
                if child.custom_id == "bedtime_btn":
                    self.remove_item(child)

    @discord.ui.button(label="🔄 Refresh Status", style=discord.ButtonStyle.secondary, custom_id="refresh_status_btn", row=0)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if is_shutting_down_mode:
            await interaction.response.send_message("PC is shut down! 💕", ephemeral=True)
            return
        self.update_buttons()
        await interaction.response.edit_message(embed=build_embed(), view=self)

    @discord.ui.button(label="👉 Touch Him", style=discord.ButtonStyle.danger, custom_id="nudge_btn", row=0)
    async def nudge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_client_action(interaction, "/nudge", "Successfully touched Poyraz! 💖👉", "Touch could not be sent!")

    @discord.ui.button(label="🎵 Play Our Song", style=discord.ButtonStyle.primary, custom_id="song_btn", row=1)
    async def song_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        import urllib.parse
        encoded_url = urllib.parse.quote(SONG_URL, safe="")
        await self.send_client_action(interaction, f"/playsong?url={encoded_url}", "Our special song is playing on his PC now! 🎶💕", "Could not play song.")

    async def bedtime_button_callback(self, interaction: discord.Interaction):
        current_hour = datetime.now().hour
        if not (current_hour >= 23 or current_hour < 6):
            await interaction.response.send_message("Poyraz can only be sent to bed between 23:00 and 06:00! ☀️", ephemeral=True)
            return
        await self.send_client_action(interaction, "/sleep_alert", "Sent bedtime reminder to Poyraz! 🛌💖", "Could not send bedtime alert.")

    async def send_client_action(self, interaction: discord.Interaction, endpoint: str, success_msg: str, fail_msg: str):
        if ALLOWED_USER_IDS and interaction.user.id not in ALLOWED_USER_IDS:
            await interaction.response.send_message("Only designated users can press this button! 💖", ephemeral=True)
            return

        is_pc_online = latest["online"] and (time.time() - last_seen < 10)
        if not is_pc_online or is_shutting_down_mode:
            await interaction.response.send_message(f"PC is offline. {fail_msg} 🎀", ephemeral=True)
            return

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(f"http://127.0.0.1:8766{endpoint}", timeout=3) as resp:
                    if resp.status == 200:
                        await interaction.response.send_message(success_msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(fail_msg, ephemeral=True)
        except Exception:
            await interaction.response.send_message("Could not communicate with the client.", ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def update_discord_message():
    global status_message_id
    if is_shutting_down_mode:
        return

    async with update_lock:
        channel = bot.get_channel(STATUS_CHANNEL_ID)
        if not channel:
            return

        await fetch_weather()
        embed = build_embed()
        view = StatusView()

        if status_message_id:
            try:
                msg = await channel.fetch_message(status_message_id)
                await msg.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                status_message_id = None
            except Exception as e:
                if latest["online"] and (time.time() - last_seen < 10):
                    print(f"[UPDATE ERROR] {e}")

        try:
            await channel.purge(limit=10)
            msg = await channel.send(embed=embed, view=view)
            save_message_id(msg.id)
        except Exception as e:
            print(f"[INIT ERROR] {e}")

@tasks.loop(seconds=15)
async def auto_update_status():
    await update_discord_message()

@bot.event
async def on_ready():
    bot.add_view(StatusView())
    load_message_id()
    print(f"Logged in as: {bot.user}")
    print(f"API Listening on: http://0.0.0.0:{PORT}")

    if not auto_update_status.is_running():
        auto_update_status.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.channel.id == STATUS_CHANNEL_ID:
        await asyncio.sleep(5)
        try:
            await message.delete()
        except Exception:
            pass

    await bot.process_commands(message)

async def activity_endpoint(request):
    global last_seen, is_shutting_down_mode

    if request.headers.get("X-Activity-Key") != ACTIVITY_KEY:
        return web.Response(status=401, text="Unauthorized")

    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    if data.get("online") is False:
        latest["online"] = False
        last_seen = 0
        bot.loop.create_task(update_discord_message())
        return web.json_response({"ok": True})

    is_shutting_down_mode = False

    latest.update({
        "online": True,
        "username": data.get("username", "Unknown"),
        "hostname": data.get("hostname", "Unknown"),
        "active_window": data.get("active_window", "Unknown"),
        "process": data.get("process", "Unknown"),
        "game": data.get("game"),
        "game_started": data.get("game_started"),
        "cpu": data.get("cpu"),
        "ram": data.get("ram"),
        "uptime": data.get("uptime"),
        "idle_seconds": data.get("idle_seconds", 0),
        "open_windows": data.get("open_windows", []),
        "media": data.get("media"),
        "updated": datetime.now().strftime("%H:%M:%S"),
    })
    last_seen = time.time()

    return web.json_response({"ok": True})

async def shutdown_endpoint(request):
    global last_seen, is_shutting_down_mode, status_message_id
    is_shutting_down_mode = True

    channel = bot.get_channel(STATUS_CHANNEL_ID)
    now_str = datetime.now().strftime("%d.%m.%Y - %H:%M:%S")

    if channel and status_message_id:
        try:
            msg = await channel.fetch_message(status_message_id)
            embed = discord.Embed(
                title="🎀 ── PC Shut Down ── 🎀",
                description=f"The computer was shut down at **{now_str}**. See you soon! 💕\n\n🌸 ────────────────────── 🌸",
                color=PINK_OFFLINE
            )
            embed.set_thumbnail(url=THUMBNAIL_OFFLINE)
            embed.set_footer(text="Te iubesc Andrea 💕")
            await msg.edit(embed=embed, view=None)
        except Exception as e:
            print(f"[SHUTDOWN MSG ERROR] {e}")

    latest["online"] = False
    last_seen = 0

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:8766/shutdown", timeout=3) as resp:
                pass
    except Exception:
        pass

    return web.json_response({"ok": True})

async def health(request):
    return web.json_response({"ok": True})

async def start_api():
    app = web.Application()
    app.router.add_post("/activity", activity_endpoint)
    app.router.add_post("/shutdown", shutdown_endpoint)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_api()
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())