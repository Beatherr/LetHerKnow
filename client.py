import os
import time
import getpass
import socket
import atexit
import threading
import winsound
import ctypes
import webbrowser
from urllib.parse import parse_qs, urlparse, unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
import psutil
import pygetwindow as gw

try:
    from plyer import notification
except Exception:
    notification = None

API_URL = "http://127.0.0.1:8765/activity"
ACTIVITY_KEY = "01171120"

is_shutting_down = False

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_seconds():
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return millis / 1000.0
    except Exception:
        pass
    return 0

VIDEO_KEYWORDS = [
    "youtube", "netflix", "prime video", "disney+", "twitch", 
    "blutv", "gain", "kick", "vlc", "media player", "mpv", "potplayer"
]

def is_watching_video(active_window_title):
    if not active_window_title:
        return False
    title_lower = active_window_title.lower()
    return any(keyword in title_lower for keyword in VIDEO_KEYWORDS)

class NudgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global is_shutting_down
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/shutdown":
            is_shutting_down = True
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            
            send_offline_signal()
            os.system("shutdown /s /t 5")
            return

        if path == "/nudge":
            if notification:
                try:
                    notification.notify(
                        title="❤️ You got touched!",
                        message="She touched you.",
                        app_name="PC Activity Monitor",
                        timeout=10
                    )
                except Exception:
                    pass

            winsound.MessageBeep(winsound.MB_ICONASTERISK)

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if path == "/sleep_alert":
            if notification:
                try:
                    notification.notify(
                        title="🛌 Time to Sleep!",
                        message="She says it's getting late. Go to sleep! 😴💖",
                        app_name="PC Activity Monitor",
                        timeout=15
                    )
                except Exception:
                    pass

            winsound.MessageBeep(winsound.MB_ICONHAND)
            time.sleep(0.3)
            winsound.MessageBeep(winsound.MB_ICONHAND)

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if path == "/playsong":
            query = parse_qs(parsed_url.query)
            song_url = query.get("url", [None])[0]
            if song_url:
                decoded_url = unquote(song_url)
                webbrowser.open(decoded_url)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")
                return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return

def start_nudge_listener():
    try:
        server = HTTPServer(('127.0.0.1', 8766), NudgeHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[Nudge Listener Error] {e}")

GAME_PROCESSES = {
    "WARNO-Win64-Shipping.exe": "WARNO",
    "WARNO.exe": "WARNO",
    "VALORANT-Win64-Shipping.exe": "VALORANT",
    "Squad.exe": "Squad",
    "SquadGame.exe": "Squad",
    "Minecraft.exe": "Minecraft",
    "javaw.exe": "Minecraft / Java App",
    "aces.exe": "War Thunder",
    "RobloxPlayerBeta.exe": "Roblox",
    "Among Us.exe": "Among Us",
    "PeoplePlayground.exe": "People Playground",
    "Rematch.exe": "Rematch",
    "Rematch-Win64-Shipping.exe": "Rematch",
    "BeamNG.drive.x64.exe": "BeamNG.drive / BeamMP",
    "BeamNG.drive.ui.exe": "BeamNG.drive / BeamMP",
    "BeamMP-Launcher.exe": "BeamMP",
} #You can change them or add them if you want

IGNORED_TITLES = {
    "Program Manager",
    "Windows Input Experience",
    "Windows Giriş Deneyimi",
    "NVIDIA GeForce Overlay",
    "Settings",
    "Ayarlar",
    "Calculator",
    "",
} #You can change them or add them if you want

current_game = None
game_started_time = None
last_game_detected_time = 0

def is_valid_window(title):
    if not title:
        return False
    title = title.strip()
    if title in IGNORED_TITLES:
        return False
    if "cmd.exe" in title.lower() or "powershell.exe" in title.lower():
        return False
    return True

def get_active_window_title():
    try:
        win = gw.getActiveWindow()
        if win and win.title and is_valid_window(win.title):
            return win.title.strip()
    except Exception:
        pass
    return "Desktop / Idle"

def get_open_windows():
    titles = []
    try:
        for win in gw.getAllWindows():
            if win.title:
                title = win.title.strip()
                if is_valid_window(title) and title not in titles:
                    titles.append(title)
    except Exception:
        pass
    return titles

def detect_game():
    global current_game, game_started_time, last_game_detected_time
    
    running_games = {}
    active_win_title = get_active_window_title().lower()

    # 1. Çalışan tüm oyun işlemlerini tespit et
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name']
            if pname in GAME_PROCESSES:
                game_name = GAME_PROCESSES[pname]
                running_games[game_name] = pname
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    now = time.time()
    detected = None

    if running_games:
        # Önceliği o an aktif pencerede açık olan oyuna ver
        for g_name in running_games:
            if g_name.lower() in active_win_title:
                detected = g_name
                break
        
        # Aktif pencerede oyun yoksa, halihazırda oynanan oyunu koru veya ilkini seç
        if not detected:
            if current_game in running_games:
                detected = current_game
            else:
                detected = list(running_games.keys())[0]

    if detected:
        last_game_detected_time = now
        # Sadece seçilen oyun gerçekten değiştiğinde süreyi yeniden başlat
        if current_game != detected:
            current_game = detected
            game_started_time = now
    else:
        # Oyun görünmüyorsa anlık takılmalara karşı 15 saniye bekle
        if current_game and (now - last_game_detected_time > 15):
            current_game = None
            game_started_time = None

    return current_game, game_started_time

def send_offline_signal():
    try:
        requests.post(
            API_URL,
            headers={"X-Activity-Key": ACTIVITY_KEY},
            json={"online": False},
            timeout=2
        )
    except Exception:
        pass

atexit.register(send_offline_signal)

def main():
    threading.Thread(target=start_nudge_listener, daemon=True).start()
    print("Client started. Nudge listener active on port 8766. Sending metrics to bot...")

    psutil.cpu_percent(interval=None)

    while True:
        if is_shutting_down:
            break

        try:
            game_name, game_time = detect_game()
            active_win = get_active_window_title()
            open_wins = get_open_windows()

            calculated_idle = get_idle_seconds()

            if is_watching_video(active_win) or game_name is not None:
                calculated_idle = 0

            payload = {
                "online": True,
                "username": getpass.getuser(),
                "hostname": socket.gethostname(),
                "active_window": active_win,
                "process": "python.exe",
                "game": game_name,
                "game_started": game_time,
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent,
                "uptime": time.time() - psutil.boot_time(),
                "idle_seconds": calculated_idle,
                "open_windows": open_wins,
                "media": f"🎬 Watching Video ({active_win})" if is_watching_video(active_win) else None
            }

            headers = {"X-Activity-Key": ACTIVITY_KEY}
            requests.post(API_URL, json=payload, headers=headers, timeout=3)

        except Exception as e:
            print(f"[Client Loop Error] {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
