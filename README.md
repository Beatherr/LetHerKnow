# PC Activity Monitor v2

A lightweight, consent-based Windows activity monitor.

## What it reports

- Current game
- Active window title
- Active process
- Game session duration
- CPU usage
- RAM usage
- PC uptime
- Computer/user name
- Last update time

## Performance

The client is intentionally lightweight:

- Network update every 5 seconds
- Process/game scan every 5 seconds
- Active window check once per update
- CPU sampling uses only a short 0.1 second interval
- No screen recording
- No screenshots
- No keylogging
- No password/browser-history collection
- No file uploading

## Automatic startup

The first time `client.py` runs, it creates a per-user Windows Startup entry under:

`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

This means it starts automatically when that Windows account logs in.

After testing, you can rename `client.py` to `client.pyw` to avoid a console window.

## Setup

### 1. Install dependencies

```powershell
py -m pip install -r requirements.txt
```

### 2. Bot configuration

In `bot.py` set:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
ACTIVITY_KEY = "YOUR_LONG_RANDOM_SECRET"

ALLOWED_USER_IDS = {
    YOUR_FRIEND_DISCORD_ID,
}
```

A Discord User ID can be copied with Developer Mode enabled in Discord.

### 3. Client configuration

If bot and client are on the same PC:

```python
SERVER_URL = "http://127.0.0.1:8765/activity"
```

If the client is on another PC, replace it with the private IP/VPN address of the computer running the bot.

The `ACTIVITY_KEY` must be identical in both files.

### 4. Run

Terminal 1:

```powershell
py bot.py
```

Terminal 2:

```powershell
py client.py
```

Then use `/status` in Discord.

## Add more games

Find the game's `.exe` in Task Manager > Details.

Then add:

```python
"Game.exe": "Game Name",
```

to `GAME_PROCESSES`.

## Recommended networking

If the bot is on a different computer, avoid exposing port 8765 directly to the public internet. A private VPN such as Tailscale is preferable.

## Privacy

Only users explicitly listed in `ALLOWED_USER_IDS` can use the status commands.
