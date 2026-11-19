import ctypes
import html
import io
import json
import os
import queue
import re
import shutil
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk
from ctypes import wintypes

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageTk
except ImportError:
    import tkinter.messagebox as mb
    tk.Tk().withdraw()
    mb.showerror(APP_NAME, "Falta Pillow / Pillow is missing.\n\npip install pillow")
    raise SystemExit(1)

try:
    import pystray
except ImportError:
    pystray = None

try:
    import winreg
except ImportError:
    winreg = None

FROZEN = getattr(sys, "frozen", False)
APP_NAME = "osu!rankstats"
APP_ID = "osu-rankstats"
APP_VERSION = "1.0.0"
APP_DIR = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA") or APP_DIR, APP_ID)
DB_PATH = os.path.join(DATA_DIR, "data.db")
LEGACY_DB = os.path.join(APP_DIR, "osu_stats.db")
OLD_CONFIG = os.path.join(APP_DIR, "config.json")
UA = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) {APP_ID}/{APP_VERSION}"
MODES = [("osu", "osu!"), ("taiko", "taiko"), ("fruits", "catch"), ("mania", "mania")]
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = APP_ID

DEFAULTS = {
    "user_query": "",
    "username": "",
    "mode": "osu",
    "lang": "en",
    "refresh_minutes": 5,
    "x": 100,
    "y": 100,
    "topmost": True,
    "expanded": False,
    "alpha": 1.0,
    "tray_notified": False,
    "hide_fullscreen": True,
    "obs_enabled": False,
    "obs_port": 52700,
    "mania_view": "stats",
}
MT_API = "https://api.mania-tracker.com/api/profiles/{}/skills"
MT_PAGE = "https://mania-tracker.com/player/{}/skills"
MT_RATINGS = [("Stream", "Stream"), ("Jumpstream", "Jumpstream"), ("Handstream", "Handstream"),
              ("Stamina", "Stamina"), ("JackSpeed", "Jack speed"), ("Chordjack", "Chordjack"),
              ("Technical", "Technical")]
MT_PATTERNS = {"ln": "LN", "tech": "Tech", "jumpstream": "Jumpstream", "handstream": "Handstream",
               "jack": "Jack", "quadstream": "Quadstream", "chordjack": "Chordjack"}
PURPLE = "#a98bff"

BG = "#17151f"
PANEL = "#221f2e"
FIELD = "#2a2638"
FG = "#f4f2fb"
SOFT = "#d9d5ea"
DIM = "#9a95b4"
PINK = "#ff66aa"
YELLOW = "#ffd23f"
GREEN = "#6fdc8c"
RED = "#ff6b6b"
ORANGE = "#ffb35c"
KEY = "#010203"
GRADE_COLORS = {"ssh": "#eef0ff", "ss": "#ffd84a", "sh": "#c3c9e0", "s": "#ffad3b", "a": "#7be08f"}
GRADE_NAMES = [("ssh", "SS+"), ("ss", "SS"), ("sh", "S+"), ("s", "S"), ("a", "A")]

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
FONT_FILES = {
    "regular": ["segoeui.ttf", "arial.ttf"],
    "semibold": ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"],
    "bold": ["segoeuib.ttf", "arialbd.ttf"],
    "light": ["segoeuil.ttf", "segoeui.ttf", "arial.ttf"],
    "icons": ["SegoeIcons.ttf", "segmdl2.ttf"],
}
ICONS = {"refresh": ("\uE72C", "⟳"), "down": ("\uE70D", "▾"), "up": ("\uE70E", "▴"),
         "close": ("\uE711", "✕")}

STR = {
    "es": {
        "performance": "Performance", "accuracy": "Precisión", "in": "en",
        "updating": "actualizando…", "updated": "actualizado {t}",
        "offline": "sin conexión · datos del {t}", "cached": "datos guardados del {t}",
        "err_notfound": "Usuario no encontrado", "err_ratelimit": "Demasiadas consultas, espera",
        "err_offline": "Sin conexión", "err_parse": "No se pudo leer el perfil",
        "err_http": "Error del servidor", "no_user": "Clic derecho → Configuración",
        "ranked_score": "Ranked score", "total_score": "Total score", "play_count": "Partidas",
        "play_time": "Tiempo jugado", "max_combo": "Combo máximo", "total_hits": "Total hits",
        "replays": "Replays vistos", "peak_rank": "Mejor rank",
        "history": "Rank · últimos 90 días", "best": "mejor {r}", "no_history": "Sin historial",
        "refresh": "Actualizar", "open_profile": "Abrir perfil en el navegador",
        "topmost": "Siempre visible", "startup": "Iniciar con Windows",
        "hide_fs": "Ocultar en juegos a pantalla completa",
        "obs": "Modo OBS (mostrar en el stream)",
        "obs_hint": "Imagen: OBS → Fuente → Imagen → pega la ruta\nNavegador: OBS → Fuente → Navegador → pega el link (480 × 440)",
        "obs_copy": "Copiar link de OBS", "copy": "Copiar link", "copy_path": "Copiar ruta de imagen", "copied": "¡Copiado!",
        "settings": "Configuración…", "show_hide": "Mostrar / ocultar", "quit": "Salir",
        "set_title": "Configuración",
        "profile": "Nombre de usuario", "profile_ph": "Tu nombre en osu!",
        "profile_hint": "",
        "link": "Link del perfil", "link_ph": "https://osu.ppy.sh/users/…",
        "link_hint": "Pega el link de tu perfil (tiene prioridad sobre el nombre)",
        "bad_link": "✗ No es un link de perfil de osu!", "or": "o",
        "det_user": "✓ Usuario: {u}", "det_id": "✓ Perfil con ID {u}", "det_mode": "  ·  modo {m}",
        "need_profile": "Escribe tu usuario o pega el link de tu perfil",
        "language": "Idioma", "refresh_every": "Actualizar cada", "opacity": "Opacidad",
        "save": "Guardar", "cancel": "Cancelar",
        "tray_hidden": "Sigo en la bandeja. Haz clic en el icono para mostrarme.",
        "skills_btn": "skills", "mt_loading": "Cargando skills de mania-tracker…",
        "mt_untracked": "Este perfil no está registrado en mania-tracker",
        "mt_computed": "calculado", "mt_plays": "jugadas analizadas", "top": "top {p}%",
        "skillsets": "Skillsets", "patterns": "Patrones", "open_mt": "Abrir en mania-tracker",
    },
    "en": {
        "performance": "Performance", "accuracy": "Accuracy", "in": "in",
        "updating": "updating…", "updated": "updated {t}",
        "offline": "offline · data from {t}", "cached": "saved data from {t}",
        "err_notfound": "User not found", "err_ratelimit": "Too many requests, wait",
        "err_offline": "No connection", "err_parse": "Couldn't read the profile",
        "err_http": "Server error", "no_user": "Right click → Settings",
        "ranked_score": "Ranked score", "total_score": "Total score", "play_count": "Play count",
        "play_time": "Play time", "max_combo": "Max combo", "total_hits": "Total hits",
        "replays": "Replays watched", "peak_rank": "Peak rank",
        "history": "Rank · last 90 days", "best": "best {r}", "no_history": "No history",
        "refresh": "Refresh", "open_profile": "Open profile in browser",
        "topmost": "Always on top", "startup": "Start with Windows",
        "hide_fs": "Hide during fullscreen games",
        "obs": "OBS mode (show on stream)",
        "obs_hint": "Image: OBS → Source → Image → paste the path\nBrowser: OBS → Source → Browser → paste the link (480 × 440)",
        "obs_copy": "Copy OBS link", "copy": "Copy link", "copy_path": "Copy image path", "copied": "Copied!",
        "settings": "Settings…", "show_hide": "Show / hide", "quit": "Quit",
        "set_title": "Settings",
        "profile": "Username", "profile_ph": "Your osu! username",
        "profile_hint": "",
        "link": "Profile link", "link_ph": "https://osu.ppy.sh/users/…",
        "link_hint": "Paste your profile link (takes priority over the username)",
        "bad_link": "✗ Not an osu! profile link", "or": "or",
        "det_user": "✓ User: {u}", "det_id": "✓ Profile ID {u}", "det_mode": "  ·  mode {m}",
        "need_profile": "Type your username or paste your profile link",
        "language": "Language", "refresh_every": "Refresh every", "opacity": "Opacity",
        "save": "Save", "cancel": "Cancel",
        "tray_hidden": "Still running in the tray. Click the icon to show me.",
        "skills_btn": "skills", "mt_loading": "Loading mania-tracker skills…",
        "mt_untracked": "This player isn't tracked on mania-tracker",
        "mt_computed": "computed", "mt_plays": "plays analyzed", "top": "top {p}%",
        "skillsets": "Skillsets", "patterns": "Patterns", "open_mt": "Open on mania-tracker",
    },
}
LANG = ["es"]


def T(key, **kw):
    s = STR.get(LANG[0], STR["es"]).get(key) or STR["es"].get(key, key)
    return s.format(**kw) if kw else s


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS profiles (
                user_key TEXT, mode TEXT, data TEXT, updated REAL,
                PRIMARY KEY (user_key, mode));
            CREATE TABLE IF NOT EXISTS images (url TEXT PRIMARY KEY, data BLOB, updated REAL);
        """)
        self.db.commit()

    def load_settings(self):
        cfg = dict(DEFAULTS)
        rows = self.db.execute("SELECT key, value FROM settings").fetchall()
        if not rows:
            self._migrate_json(cfg)
        for k, v in rows:
            try:
                cfg[k] = json.loads(v)
            except ValueError:
                pass
        return cfg

    def _migrate_json(self, cfg):
        try:
            with open(OLD_CONFIG, "r", encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, ValueError):
            return
        for k in ("mode", "refresh_minutes", "x", "y", "topmost", "expanded", "alpha"):
            if k in old:
                cfg[k] = old[k]
        if old.get("username"):
            cfg["username"] = old["username"]
            cfg["user_query"] = "@" + old["username"]
        self.save_settings(cfg)

    def save_settings(self, cfg):
        self.db.executemany("INSERT OR REPLACE INTO settings VALUES (?, ?)",
                            [(k, json.dumps(v)) for k, v in cfg.items()])
        self.db.commit()

    def save_profile(self, user_key, mode, data):
        clean = {k: v for k, v in data.items() if not k.startswith("_")}
        self.db.execute("INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?)",
                        (user_key, mode, json.dumps(clean), time.time()))
        self.db.commit()

    def load_profiles(self, user_key):
        out = {}
        for mode, data, updated in self.db.execute(
                "SELECT mode, data, updated FROM profiles WHERE user_key = ?", (user_key,)):
            try:
                d = json.loads(data)
            except ValueError:
                continue
            d["_t"] = updated
            out[mode] = d
        return out

    def save_image(self, url, raw):
        self.db.execute("INSERT OR REPLACE INTO images VALUES (?, ?, ?)", (url, raw, time.time()))
        self.db.execute("DELETE FROM images WHERE url NOT IN "
                        "(SELECT url FROM images ORDER BY updated DESC LIMIT 4)")
        self.db.commit()

    def load_image(self, url):
        row = self.db.execute("SELECT data FROM images WHERE url = ?", (url,)).fetchone()
        if not row:
            return None
        try:
            return Image.open(io.BytesIO(row[0])).convert("RGB")
        except Exception:
            return None

    def close(self):
        self.db.close()


class FetchError(Exception):
    pass


def http_get(url, timeout=15, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise FetchError({404: "notfound", 429: "ratelimit"}.get(e.code, "http"))
    except (urllib.error.URLError, TimeoutError, OSError):
        raise FetchError("offline")


def parse_profile_input(text):
    t = text.strip()
    m = re.search(r"osu\.ppy\.sh/(?:users|u)/([^/?#\s]+)(?:/(osu|taiko|fruits|mania))?", t)
    if m:
        ident = urllib.parse.unquote(m.group(1)).lstrip("@")
        if ident.isdigit():
            return ident, ident, m.group(2), True
        return "@" + ident, ident, m.group(2), False
    t = t.lstrip("@")
    return ("@" + t if t else ""), t, None, False


def is_profile_link(text):
    return bool(re.search(r"osu\.ppy\.sh/(?:users|u)/[^/?#\s]+", text))


def fetch_profile(query, mode):
    if query.startswith("@"):
        path = "@" + urllib.parse.quote(query[1:], safe="")
    else:
        path = urllib.parse.quote(query, safe="")
    page = http_get(f"https://osu.ppy.sh/users/{path}/{mode}").decode("utf-8", "replace")
    m = re.search(r'data-initial-data="([^"]*)"', page)
    if not m:
        raise FetchError("parse")
    u = json.loads(html.unescape(m.group(1)))["user"]
    del page, m
    st = u.get("statistics") or {}
    lv = st.get("level") or {}
    return {
        "id": u.get("id"),
        "username": u.get("username", query.lstrip("@")),
        "avatar_url": u.get("avatar_url"),
        "cover_url": (u.get("cover") or {}).get("url") or u.get("cover_url"),
        "country": u.get("country_code", ""),
        "country_name": (u.get("country") or {}).get("name", ""),
        "supporter": bool(u.get("is_supporter")),
        "pp": st.get("pp") or 0,
        "rank": st.get("global_rank"),
        "country_rank": st.get("country_rank"),
        "acc": st.get("hit_accuracy") or 0,
        "level": lv.get("current", 0),
        "level_progress": lv.get("progress", 0),
        "play_count": st.get("play_count") or 0,
        "play_time": st.get("play_time") or 0,
        "ranked_score": st.get("ranked_score") or 0,
        "total_score": st.get("total_score") or 0,
        "max_combo": st.get("maximum_combo") or 0,
        "total_hits": st.get("total_hits") or 0,
        "replays": st.get("replays_watched_by_others") or 0,
        "grades": st.get("grade_counts") or {},
        "peak_rank": (u.get("rank_highest") or {}).get("rank"),
        "history": [r for r in ((u.get("rank_history") or {}).get("data") or []) if r],
        "variants": [
            {"v": v.get("variant", ""), "rank": v.get("global_rank"), "pp": v.get("pp") or 0}
            for v in (st.get("variants") or []) if v.get("pp")
        ],
    }


def fetch_mt_skills(uid):
    try:
        raw = json.loads(http_get(MT_API.format(int(uid)), headers={
            "Accept": "application/json", "Origin": "https://mania-tracker.com",
            "Referer": "https://mania-tracker.com/"}))
    except FetchError as e:
        if str(e) == "notfound":
            return {"tracked": False}
        raise
    except ValueError:
        raise FetchError("parse")
    modes = [m for m in (raw.get("modes") or []) if m.get("ratings")]
    if not modes:
        return {"tracked": False}
    main = raw.get("mainKeyCount")
    m = (next((x for x in modes if x.get("keyCount") == main), None)
         or max(modes, key=lambda x: x.get("analyzedPlays") or 0))
    dan = m.get("dan") or {}
    rank = (m.get("ranks") or {}).get("Overall") or {}
    return {
        "tracked": True,
        "computed": raw.get("computedAt"),
        "plays": m.get("analyzedPlays") or 0,
        "key": m.get("keyCount"),
        "ratings": m.get("ratings") or {},
        "patterns": [[p.get("id"), p.get("rating") or 0, p.get("plays") or 0]
                     for p in (m.get("patterns") or [])],
        "dan_rc": (dan.get("rc") or {}).get("label"),
        "dan_ln": (dan.get("ln") or {}).get("label"),
        "pct": {k: v.get("value") for k, v in (m.get("percentiles") or {}).items()
                if isinstance(v, dict)},
        "rank": rank.get("global"),
        "country_rank": rank.get("countryRank"),
        "country": rank.get("country"),
    }


def fmt_iso(s):
    try:
        from datetime import datetime
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone().strftime("%d/%m %H:%M")
    except Exception:
        return "-"


def download_image(url, max_w, max_h):
    im = Image.open(io.BytesIO(http_get(url))).convert("RGB")
    im.thumbnail((max_w, max_h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return im, buf.getvalue()


def fmt_int(n):
    return f"{int(n):,}" if n is not None else "-"


def fmt_rank(n):
    return f"#{int(n):,}" if n else "#-"


def fmt_time(seconds):
    h, rem = divmod(int(seconds), 3600)
    return f"{h:,}h {rem // 60}m"


def fmt_when(ts):
    return time.strftime("%d/%m %H:%M", time.localtime(ts))


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_icon(size=64):
    k = 4
    s = size * k
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, s - 1, s - 1), fill=PINK)
    d.ellipse((s * .09, s * .09, s * .91, s * .91), outline="white", width=int(s * .06))
    pts = [(s * .27, s * .63), (s * .43, s * .48), (s * .55, s * .57), (s * .73, s * .35)]
    d.line(pts, fill="white", width=int(s * .08), joint="curve")
    r = s * .06
    d.ellipse((pts[-1][0] - r, pts[-1][1] - r, pts[-1][0] + r, pts[-1][1] + r), fill="white")
    return im.resize((size, size), Image.LANCZOS)


def command_line():
    if FROZEN:
        return f'"{sys.executable}"'
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return f'"{pyw if os.path.exists(pyw) else sys.executable}" "{os.path.abspath(__file__)}"'


def startup_enabled():
    if not winreg:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
            return True
    except OSError:
        return False


def set_startup(on):
    if not winreg:
        return
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, command_line())
            else:
                try:
                    winreg.DeleteValue(k, RUN_NAME)
                except OSError:
                    pass
    except OSError:
        pass


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class LayeredWindow:

    def __init__(self, root):
        u, g = ctypes.windll.user32, ctypes.windll.gdi32
        self.u, self.g = u, g
        H = ctypes.c_void_p
        u.GetAncestor.argtypes = [H, wintypes.UINT]
        u.GetAncestor.restype = H
        u.GetWindowLongPtrW.argtypes = [H, ctypes.c_int]
        u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        u.SetWindowLongPtrW.argtypes = [H, ctypes.c_int, ctypes.c_ssize_t]
        u.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        u.GetDC.argtypes = [H]
        u.GetDC.restype = H
        u.ReleaseDC.argtypes = [H, H]
        u.UpdateLayeredWindow.argtypes = [H, H, ctypes.POINTER(POINT), ctypes.POINTER(SIZE), H,
                                          ctypes.POINTER(POINT), wintypes.DWORD,
                                          ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
        u.UpdateLayeredWindow.restype = wintypes.BOOL
        g.CreateCompatibleDC.argtypes = [H]
        g.CreateCompatibleDC.restype = H
        g.CreateDIBSection.argtypes = [H, ctypes.c_void_p, wintypes.UINT,
                                       ctypes.POINTER(ctypes.c_void_p), H, wintypes.DWORD]
        g.CreateDIBSection.restype = H
        g.SelectObject.argtypes = [H, H]
        g.SelectObject.restype = H
        g.DeleteObject.argtypes = [H]
        g.DeleteDC.argtypes = [H]
        root.update_idletasks()
        self.hwnd = u.GetAncestor(root.winfo_id(), 2)
        self.apply_style()

    def apply_style(self):
        ex = self.u.GetWindowLongPtrW(self.hwnd, -20)
        self.u.SetWindowLongPtrW(self.hwnd, -20, ex | 0x80000 | 0x80)

    def show(self, img, opacity):
        w, h = img.size
        r, g_, b, a = img.split()
        r, g_, b = (ImageChops.multiply(c, a) for c in (r, g_, b))
        data = Image.merge("RGBA", (b, g_, r, a)).tobytes()
        bmi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        screen = self.u.GetDC(None)
        mem = self.g.CreateCompatibleDC(screen)
        bits = ctypes.c_void_p()
        bmp = self.g.CreateDIBSection(mem, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
        ok = False
        if bmp and bits:
            ctypes.memmove(bits, data, len(data))
            old = self.g.SelectObject(mem, bmp)
            blend = BLENDFUNCTION(0, 0, max(30, min(255, int(opacity * 255))), 1)
            ok = bool(self.u.UpdateLayeredWindow(self.hwnd, screen, None, ctypes.byref(SIZE(w, h)),
                                                 mem, ctypes.byref(POINT(0, 0)), 0,
                                                 ctypes.byref(blend), 2))
            self.g.SelectObject(mem, old)
            self.g.DeleteObject(bmp)
        self.g.DeleteDC(mem)
        self.u.ReleaseDC(None, screen)
        return ok


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD)]


class FullscreenWatcher:
    SHELL = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}

    def __init__(self):
        u = ctypes.windll.user32
        H = ctypes.c_void_p
        u.GetForegroundWindow.restype = H
        u.GetWindowRect.argtypes = [H, ctypes.POINTER(RECT)]
        u.MonitorFromWindow.argtypes = [H, wintypes.DWORD]
        u.MonitorFromWindow.restype = H
        u.GetMonitorInfoW.argtypes = [H, ctypes.POINTER(MONITORINFO)]
        u.GetClassNameW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
        u.GetWindowLongPtrW.argtypes = [H, ctypes.c_int]
        u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        u.GetWindowThreadProcessId.argtypes = [H, ctypes.POINTER(wintypes.DWORD)]
        u.GetAncestor.argtypes = [H, wintypes.UINT]
        u.GetAncestor.restype = H
        self.u = u
        self.pid = os.getpid()
        self.buf = ctypes.create_unicode_buffer(64)
        self.shell32 = ctypes.windll.shell32

    def exclusive(self):
        state = ctypes.c_int(0)
        try:
            if self.shell32.SHQueryUserNotificationState(ctypes.byref(state)) == 0:
                return state.value == 3
        except Exception:
            pass
        return False

    def active(self, own_hwnd):
        u = self.u
        fg = u.GetForegroundWindow()
        if not fg:
            return False
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(fg, ctypes.byref(pid))
        if pid.value == self.pid:
            return False
        u.GetClassNameW(fg, self.buf, 64)
        if self.buf.value in self.SHELL:
            return False
        if self.exclusive():
            return True
        mon = u.MonitorFromWindow(fg, 2)
        if own_hwnd and u.MonitorFromWindow(own_hwnd, 2) != mon:
            return False
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not u.GetMonitorInfoW(mon, ctypes.byref(mi)):
            return False
        r = RECT()
        u.GetWindowRect(fg, ctypes.byref(r))
        m = mi.rcMonitor
        if r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom:
            return (u.GetWindowLongPtrW(fg, -16) & 0x00C00000) != 0x00C00000
        return False


class ObsServer:
    FILE = os.path.join(DATA_DIR, "obs_card.png")
    PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent;overflow:hidden}img{width:100%;display:block}
</style></head><body><img id="c" alt="" src="/card.png"><script>
let v=-1;const img=document.getElementById("c");
async function tick(){try{const r=await fetch("/version",{cache:"no-store"});const n=+(await r.text());
if(n!==v&&n>0){const i=new Image();i.onload=()=>{img.src=i.src;v=n};i.src="/card.png?v="+n}}catch(e){}
setTimeout(tick,3000)}tick();
</script></body></html>"""

    def __init__(self):
        self.png = b""
        self.version = 0
        self.httpd = None
        self.port = None

    @property
    def running(self):
        return self.httpd is not None

    def url(self, port=None):
        return f"http://127.0.0.1:{self.port or port}/"

    def start(self, port):
        if self.httpd:
            return True
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        srv = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    body, ctype = srv.PAGE.encode(), "text/html; charset=utf-8"
                elif path == "/version":
                    body, ctype = str(srv.version).encode(), "text/plain"
                elif path == "/card.png" and srv.png:
                    body, ctype = srv.png, "image/png"
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        for p in range(int(port), int(port) + 10):
            try:
                self.httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
                self.httpd.daemon_threads = True
                self.port = p
                break
            except OSError:
                continue
        if not self.httpd:
            return False
        threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 1},
                         daemon=True).start()
        return True

    def stop(self):
        if self.httpd:
            httpd, self.httpd, self.port = self.httpd, None, None
            threading.Thread(target=lambda: (httpd.shutdown(), httpd.server_close()),
                             daemon=True).start()
        self.png = b""
        try:
            os.remove(self.FILE)
        except OSError:
            pass

    def update(self, img):
        buf = io.BytesIO()
        img.save(buf, "PNG", compress_level=1)
        self.png = buf.getvalue()
        self.version += 1
        try:
            tmp = self.FILE + ".tmp"
            with open(tmp, "wb") as f:
                f.write(self.png)
            os.replace(tmp, self.FILE)
        except OSError:
            pass


def dark_title_bar(win):
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        val = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                break
    except Exception:
        pass


class Card:
    W = 480
    SS = 2

    def __init__(self, dpi):
        self.dpi = dpi
        self.k = dpi * self.SS
        self._fonts = {}
        self.has_icons = True
        self.d = None

    def S(self, v):
        return int(round(v * self.k))

    def font(self, style, size):
        key = (style, size)
        f = self._fonts.get(key)
        if f is None:
            px = max(6, int(size * self.k))
            for name in FONT_FILES[style]:
                try:
                    f = ImageFont.truetype(os.path.join(FONT_DIR, name), px)
                    break
                except OSError:
                    continue
            if f is None:
                if style == "icons":
                    self.has_icons = False
                f = ImageFont.load_default(px)
            self._fonts[key] = f
        return f

    def tw(self, text, f):
        return self.d.textlength(text, font=f) / self.k

    def fit(self, text, style, size, max_w):
        while size > 9 and self.tw(text, self.font(style, size)) > max_w:
            size -= 1
        return self.font(style, size)

    def text(self, x, y, s, f, fill, anchor="lm"):
        self.d.text((self.S(x), self.S(y)), s, font=f, fill=fill, anchor=anchor)

    def rrect(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle([self.S(v) for v in box], radius=self.S(r), fill=fill,
                                 outline=outline, width=max(1, self.S(width)) if outline else 0)

    @staticmethod
    def round_mask(size, r):
        m = Image.new("L", size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=r, fill=255)
        return m

    def background(self, size, cover):
        w, h = size
        base = Image.new("RGB", size, BG)
        hcov = min(h, self.S(210))
        if cover:
            cw, ch = cover.size
            sc = max(w / cw, hcov / ch)
            im = cover.resize((max(w, int(cw * sc) + 1), max(hcov, int(ch * sc) + 1)), Image.BILINEAR)
            left = (im.width - w) // 2
            im = im.crop((left, 0, left + w, hcov)).filter(ImageFilter.GaussianBlur(self.k * 1.3))
        else:
            im = Image.new("RGB", (w, hcov), "#3b2a5c")
        base.paste(im, (0, 0))
        dark = Image.new("RGB", size, BG)
        vals = [int(150 + 105 * (y / hcov) ** 1.6) if y < hcov else 255 for y in range(h)]
        mask = Image.new("L", (1, h))
        mask.putdata(vals)
        return Image.composite(dark, base, mask.resize(size))

    def icon(self, cx, cy, name, size=11):
        glyph, fallback = ICONS[name]
        f = self.font("icons", size)
        if not self.has_icons:
            glyph, f = fallback, self.font("regular", size + 2)
        self.text(cx, cy, glyph, f, FG, "mm")

    def render(self, d, mode, expanded, status, status_kind, avatar, cover,
               mania_view="stats", mt=None, mt_state=None, controls=True):
        if not controls:
            status = ""
        W = self.W
        skills_view = expanded and mode == "mania" and mania_view == "skills"
        variants = bool(d and mode == "mania" and d.get("variants")) and not skills_view
        if not expanded:
            H = 172
        elif skills_view:
            H = 434
        else:
            H = 440 if variants else 420
        size = (self.S(W), self.S(H))
        base = self.background(size, cover)
        self.d = ImageDraw.Draw(base, "RGBA")
        regions = []

        ax, ay, asz = 18, 18, 96
        if avatar:
            av = avatar.resize((self.S(asz), self.S(asz)), Image.LANCZOS)
            base.paste(av, (self.S(ax), self.S(ay)), self.round_mask(av.size, self.S(18)))
        else:
            self.rrect((ax, ay, ax + asz, ay + asz), 18, fill=(255, 255, 255, 22))
        self.rrect((ax, ay, ax + asz, ay + asz), 18, outline=(255, 255, 255, 70), width=1.5)

        x = 130
        name = d["username"] if d else APP_NAME
        fn = self.fit(name, "bold", 22, 150)
        self.text(x, 30, name, fn, FG)
        if d and d.get("country"):
            px = x + self.tw(name, fn) + 8
            fc = self.font("bold", 9)
            w = self.tw(d["country"], fc) + 12
            self.rrect((px, 22, px + w, 38), 8, fill=(255, 255, 255, 40))
            self.text(px + w / 2, 30, d["country"], fc, FG, "mm")
            if d.get("supporter"):
                self.text(px + w + 6, 30, "♥", self.font("bold", 13), PINK)

        fl, fv = self.font("regular", 12), self.font("semibold", 14)
        for yy, label, val in ((58, T("performance"), f"{d['pp']:,.0f}pp" if d else "-"),
                               (80, T("accuracy"), f"{d['acc']:.2f}%" if d else "-")):
            self.text(x, yy, label, fl, DIM)
            self.text(x + self.tw(label, fl) + 7, yy, val, fv, FG)

        flv = self.font("bold", 13)
        lvt = f"Lv{d['level']}" if d else "Lv-"
        self.text(x, 104, lvt, flv, FG)
        bx0, bx1 = x + self.tw(lvt, flv) + 8, 296
        self.rrect((bx0, 101, bx1, 107), 3, fill=(255, 255, 255, 45))
        prog = (d["level_progress"] if d else 0) / 100
        if prog > 0:
            self.rrect((bx0, 101, bx0 + max(6, (bx1 - bx0) * prog), 107), 3, fill=YELLOW)

        rx = W - 18
        rank = fmt_rank(d["rank"] if d else None)
        self.text(rx, 38, rank, self.fit(rank, "light", 44, 162), FG, "rm")
        if d and d.get("_delta"):
            txt, col = d["_delta"]
            self.text(rx, 72, txt, self.font("semibold", 11), col, "rm")
        if d and d.get("country_rank"):
            ctext = f"{fmt_rank(d['country_rank'])} {T('in')} {d.get('country_name') or d['country']}"
            self.text(rx, 92, ctext, self.fit(ctext, "regular", 12, 165), SOFT, "rm")
        if status:
            col = {"err": RED, "warn": ORANGE}.get(status_kind, DIM)
            self.text(rx, 112, status, self.fit(status, "regular", 9, 200), col, "rm")

        tx = 18
        ft = self.font("semibold", 11)
        for key, label in MODES:
            w = self.tw(label, ft) + 24
            active = key == mode
            self.rrect((tx, 132, tx + w, 158), 13,
                       fill=hex_rgb(PINK) + (255,) if active else (255, 255, 255, 24))
            self.text(tx + w / 2, 145, label, ft, "#ffffff" if active else SOFT, "mm")
            regions.append((tx, 132, tx + w, 158, ("mode", key)))
            tx += w + 6

        if mode == "mania":
            tx += 4
            w = self.tw(T("skills_btn"), ft) + 22
            self.rrect((tx, 132, tx + w, 158), 13,
                       fill=hex_rgb(PURPLE) + (255,) if skills_view else (169, 139, 255, 40),
                       outline=None if skills_view else hex_rgb(PURPLE) + (170,), width=1)
            self.text(tx + w / 2, 145, T("skills_btn"), ft, "#ffffff", "mm")
            regions.append((tx, 132, tx + w, 158, ("skills", None)))

        for i, (icon, action) in enumerate((("close", "close"),
                                            ("up" if expanded else "down", "expand"),
                                            ("refresh", "refresh")) if controls else ()):
            cx = rx - 13 - i * 32
            self.d.ellipse([self.S(cx - 13), self.S(132), self.S(cx + 13), self.S(158)],
                           fill=(255, 80, 110, 70) if action == "close" else (255, 255, 255, 24))
            self.icon(cx, 145, icon)
            regions.append((cx - 13, 132, cx + 13, 158, (action, None)))

        if skills_view:
            self._render_skills(mt, mt_state, regions)
        elif expanded:
            self._render_details(d, variants)

        self.d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=self.S(16),
                                 outline=(255, 255, 255, 38), width=max(1, int(self.k)))
        self.d = None
        base.putalpha(self.round_mask(size, self.S(16)))
        out = base.resize((int(W * self.dpi), int(H * self.dpi)), Image.LANCZOS)
        return out, regions

    def _render_skills(self, mt, state, regions):
        W = self.W
        self.d.line([self.S(18), self.S(170), self.S(W - 18), self.S(170)],
                    fill=(255, 255, 255, 28), width=max(1, int(self.k)))
        fs = self.font("regular", 9)
        link = "mania-tracker.com →"

        if not mt or not mt.get("tracked"):
            if mt and not mt.get("tracked"):
                msg, col = T("mt_untracked"), ORANGE
            elif state and state != "loading":
                msg, col = T("err_" + state), RED
            else:
                msg, col = T("mt_loading"), DIM
            self.text(W / 2, 285, msg, self.font("regular", 12), col, "mm")
            fl = self.font("semibold", 11)
            self.text(W / 2, 315, link, fl, PURPLE, "mm")
            lw = self.tw(link, fl)
            regions.append((W / 2 - lw / 2, 305, W / 2 + lw / 2, 325, ("open_mt", None)))
            return

        self.text(18, 184, f"mania-tracker · {mt.get('key') or 4}K skills", fs, DIM)
        if mt.get("rank"):
            r = f"#{mt['rank']:,} global"
            if mt.get("country_rank"):
                r += f"  ·  #{mt['country_rank']:,} {mt.get('country') or ''}"
            self.text(W - 18, 184, r, fs, DIM, "rm")

        self.rrect((18, 194, W - 18, 248), 12, fill=(255, 255, 255, 10))
        ratings, pct = mt.get("ratings") or {}, mt.get("pct") or {}
        ov, et = ratings.get("Overall"), ratings.get("EtternaOverall")
        self.text(30, 206, "Overall", fs, DIM)
        fv = self.font("semibold", 20)
        ovt = f"{ov:.2f}" if ov is not None else "-"
        self.text(30, 229, ovt, fv, FG)
        if pct.get("Overall") is not None:
            self.text(30 + self.tw(ovt, fv) + 8, 232, T("top", p=f"{100 - pct['Overall']:.1f}"),
                      fs, GREEN)
        self.text(170, 206, "Etterna", fs, DIM)
        self.text(170, 229, f"{et:.2f}" if et is not None else "-", self.font("semibold", 16), SOFT)

        fd = self.font("bold", 11)
        px = W - 30
        for kind, label in (("LN", mt.get("dan_ln")), ("RC", mt.get("dan_rc"))):
            if not label:
                continue
            txt = f"{kind}  {label}"
            w = self.tw(txt, fd) + 22
            self.rrect((px - w, 208, px, 234), 13, fill=(255, 102, 170, 45),
                       outline=hex_rgb(PINK) + (150,), width=1)
            self.text(px - w / 2, 221, txt, fd, FG, "mm")
            px -= w + 8
        if px < W - 30:
            self.text(px + 4, 221, "dan", fs, DIM, "rm")

        rows_r = [(name, ratings[k]) for k, name in MT_RATINGS if ratings.get(k) is not None]
        rows_p = [(MT_PATTERNS.get(p[0], str(p[0]).title()), p[1]) for p in (mt.get("patterns") or [])]
        vmax = max([v for _, v in rows_r + rows_p] or [1]) * 1.05
        half = (W - 36 - 8) / 2
        for x0, title, rows, color in ((18, T("skillsets"), rows_r, PINK),
                                       (18 + half + 8, T("patterns"), rows_p, PURPLE)):
            x1 = x0 + half
            self.rrect((x0, 256, x1, 412), 12, fill=(255, 255, 255, 10))
            self.text(x0 + 12, 268, title, fs, DIM)
            fl, fn = self.font("regular", 10), self.font("semibold", 10)
            for i, (label, val) in enumerate(rows[:7]):
                y = 288 + i * 18
                self.text(x0 + 12, y, label, fl, SOFT)
                bx0, bx1 = x0 + 88, x1 - 44
                self.rrect((bx0, y - 3, bx1, y + 3), 3, fill=(255, 255, 255, 28))
                self.rrect((bx0, y - 3, bx0 + max(6, (bx1 - bx0) * val / vmax), y + 3), 3, fill=color)
                self.text(x1 - 12, y, f"{val:.1f}", fn, FG, "rm")

        self.text(18, 422, f"{T('mt_computed')} {fmt_iso(mt.get('computed') or '')}  ·  "
                           f"{mt.get('plays', 0):,} {T('mt_plays')}", fs, DIM)
        fl = self.font("semibold", 9)
        self.text(W - 18, 422, link, fl, PURPLE, "rm")
        lw = self.tw(link, fl)
        regions.append((W - 18 - lw, 414, W - 18, 430, ("open_mt", None)))

    def _render_details(self, d, variants):
        W = self.W
        self.d.line([self.S(18), self.S(170), self.S(W - 18), self.S(170)],
                    fill=(255, 255, 255, 28), width=max(1, int(self.k)))

        g = d["grades"] if d else {}
        cw = (W - 36) / 5
        fg_, fc = self.font("bold", 15), self.font("semibold", 14)
        for i, (key, label) in enumerate(GRADE_NAMES):
            cx = 18 + cw * (i + 0.5)
            self.rrect((cx - 27, 180, cx + 27, 206), 9, fill=(255, 255, 255, 16),
                       outline=hex_rgb(GRADE_COLORS[key]) + (90,), width=1)
            self.text(cx, 193, label, fg_, GRADE_COLORS[key], "mm")
            self.text(cx, 223, fmt_int(g.get(key, 0)) if d else "-", fc, FG, "mm")

        self.rrect((18, 244, W - 18, 336), 12, fill=(255, 255, 255, 10))
        fl, fv = self.font("regular", 11), self.font("semibold", 12)

        def val(k, f=fmt_int):
            return f(d[k]) if d and d.get(k) is not None else "-"

        cols = [
            [("ranked_score", val("ranked_score")), ("total_score", val("total_score")),
             ("play_count", val("play_count")), ("play_time", val("play_time", fmt_time))],
            [("max_combo", val("max_combo", lambda n: f"{n:,}x")), ("total_hits", val("total_hits")),
             ("replays", val("replays")), ("peak_rank", val("peak_rank", fmt_rank))],
        ]
        half = (W - 36) / 2
        for c, rows in enumerate(cols):
            x0 = 30 + c * half
            x1 = 18 + (c + 1) * half - 12
            for r, (key, value) in enumerate(rows):
                y = 257 + r * 22
                self.text(x0, y, T(key), fl, DIM)
                self.text(x1, y, value, fv, FG, "rm")

        self.rrect((18, 346, W - 18, 406), 12, fill=(255, 255, 255, 10))
        fs = self.font("regular", 9)
        self.text(30, 357, T("history"), fs, DIM)
        hist = d.get("history") if d else []
        if hist and len(hist) >= 2:
            lo, hi = min(hist), max(hist)
            self.text(W - 30, 357, T("best", r=fmt_rank(lo)), fs, DIM, "rm")
            span = max(1, hi - lo)
            x0, x1, y0, y1 = 30, W - 30, 368, 398
            pts = [(self.S(x0 + (x1 - x0) * i / (len(hist) - 1)),
                    self.S(y0 + (y1 - y0) * (r - lo) / span)) for i, r in enumerate(hist)]
            self.d.polygon(pts + [(pts[-1][0], self.S(y1 + 2)), (pts[0][0], self.S(y1 + 2))],
                           fill=hex_rgb(PINK) + (40,))
            self.d.line(pts, fill=PINK, width=max(2, self.S(1.8)), joint="curve")
            ex, ey = pts[-1]
            r_ = self.S(3)
            self.d.ellipse([ex - r_, ey - r_, ex + r_, ey + r_], fill="#ffffff")
        else:
            self.text(W / 2, 384, T("no_history"), self.font("regular", 11), DIM, "mm")

        if variants:
            txt = "     ".join(f"{v['v'].upper()}  {fmt_rank(v['rank'])} · {v['pp']:,.0f}pp"
                               for v in d["variants"])
            self.text(18, 422, txt, self.font("semibold", 11), PINK)


class Pills:

    def __init__(self):
        self.cache = {}

    def get(self, w, h, r, fill, outline=None, ow=1):
        key = (w, h, r, fill, outline, ow)
        if key not in self.cache:
            k = 3
            im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle(
                (0, 0, w * k - 1, h * k - 1), radius=r * k, fill=fill,
                outline=outline, width=ow * k if outline else 0)
            self.cache[key] = ImageTk.PhotoImage(im.resize((w, h), Image.LANCZOS))
        return self.cache[key]


class Segmented(tk.Canvas):
    def __init__(self, parent, pills, dpi, options, value, width, on_change=None):
        self.h = int(34 * dpi)
        super().__init__(parent, width=width, height=self.h, bg=BG, highlightthickness=0,
                         bd=0, cursor="hand2")
        self.pills, self.opts, self.value, self.w, self.cb = pills, options, value, width, on_change
        self.pad = int(3 * dpi)
        self.bind("<Button-1>", self._click)
        self.draw()

    def draw(self):
        self.delete("all")
        h, p = self.h, self.pad
        self.create_image(0, 0, anchor="nw", image=self.pills.get(self.w, h, h // 2, FIELD))
        cw = (self.w - 2 * p) / len(self.opts)
        for i, (v, label) in enumerate(self.opts):
            x0 = p + i * cw
            if v == self.value:
                self.create_image(int(x0), p, anchor="nw",
                                  image=self.pills.get(int(cw), h - 2 * p, (h - 2 * p) // 2, PINK))
            self.create_text(x0 + cw / 2, h / 2, text=label, font=("Segoe UI Semibold", 10),
                             fill="#ffffff" if v == self.value else SOFT)

    def _click(self, e):
        cw = (self.w - 2 * self.pad) / len(self.opts)
        i = min(len(self.opts) - 1, max(0, int((e.x - self.pad) // cw)))
        self.value = self.opts[i][0]
        self.draw()
        if self.cb:
            self.cb(self.value)


class Toggle(tk.Canvas):
    def __init__(self, parent, pills, dpi, value, on_change=None):
        self.cb = on_change
        self.w, self.h = int(44 * dpi), int(24 * dpi)
        super().__init__(parent, width=self.w, height=self.h, bg=BG, highlightthickness=0,
                         bd=0, cursor="hand2")
        self.pills, self.value = pills, value
        self.bind("<Button-1>", self._click)
        self.draw()

    def _click(self, _):
        self.set(not self.value)
        if self.cb:
            self.cb(self.value)

    def set(self, v):
        self.value = v
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.w, self.h
        self.create_image(0, 0, anchor="nw",
                          image=self.pills.get(w, h, h // 2, PINK if self.value else "#3d3852"))
        k = h - 6
        x = w - k - 3 if self.value else 3
        self.create_image(x, 3, anchor="nw", image=self.pills.get(k, k, k // 2, "#ffffff"))


class Slider(tk.Canvas):
    def __init__(self, parent, pills, dpi, lo, hi, value, width, on_change=None):
        self.w, self.h = width, int(24 * dpi)
        super().__init__(parent, width=self.w, height=self.h, bg=BG, highlightthickness=0,
                         bd=0, cursor="hand2")
        self.pills, self.lo, self.hi, self.value, self.cb = pills, lo, hi, value, on_change
        self.kn = int(18 * dpi)
        self.th = max(4, int(6 * dpi))
        self.bind("<Button-1>", self._move)
        self.bind("<B1-Motion>", self._move)
        self.draw()

    def draw(self):
        self.delete("all")
        kn, th, w, h = self.kn, self.th, self.w, self.h
        span = w - kn
        x = int(span * (self.value - self.lo) / (self.hi - self.lo))
        y = (h - th) // 2
        self.create_image(kn // 2, y, anchor="nw", image=self.pills.get(span, th, th // 2, FIELD))
        if x > 0:
            self.create_image(kn // 2, y, anchor="nw", image=self.pills.get(max(th, x), th, th // 2, PINK))
        self.create_image(x, (h - kn) // 2, anchor="nw",
                          image=self.pills.get(kn, kn, kn // 2, "#ffffff"))

    def _move(self, e):
        span = self.w - self.kn
        v = self.lo + (self.hi - self.lo) * (e.x - self.kn / 2) / span
        self.value = int(min(self.hi, max(self.lo, round(v))))
        self.draw()
        if self.cb:
            self.cb(self.value)


class Button(tk.Canvas):
    def __init__(self, parent, pills, dpi, text, command, primary=True):
        self.h = int(36 * dpi)
        self.w = int((len(text) * 8 + 44) * dpi)
        super().__init__(parent, width=self.w, height=self.h, bg=BG, highlightthickness=0,
                         bd=0, cursor="hand2")
        self.pills, self.text, self.primary = pills, text, primary
        self.colors = (PINK, "#ff85bc") if primary else (FIELD, "#36314a")
        self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self.draw(True))
        self.bind("<Leave>", lambda e: self.draw(False))
        self.draw(False)

    def draw(self, hover):
        self.delete("all")
        self.create_image(0, 0, anchor="nw",
                          image=self.pills.get(self.w, self.h, self.h // 2, self.colors[hover]))
        self.create_text(self.w / 2, self.h / 2, text=self.text, font=("Segoe UI Semibold", 10),
                         fill="#ffffff" if self.primary else SOFT)


class TextField:

    def __init__(self, parent, pills, dpi, width, placeholder, value="", on_change=None):
        self.pills, self.ph, self.cb = pills, placeholder, on_change
        self.w, self.h = width, int(40 * dpi)
        self.canvas = tk.Canvas(parent, width=self.w, height=self.h, bg=BG,
                                highlightthickness=0, bd=0)
        self.bg = self.canvas.create_image(0, 0, anchor="nw", image=self._img(False))
        self.entry = tk.Entry(self.canvas, bg=FIELD, fg=FG, insertbackground=FG, relief="flat",
                              font=("Segoe UI", 11), bd=0)
        self.canvas.create_window(int(14 * dpi), self.h // 2, anchor="w", window=self.entry,
                                  width=self.w - int(28 * dpi))
        self.placeholder = False
        if value:
            self.entry.insert(0, value)
        else:
            self._show_placeholder()
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.entry.bind("<KeyRelease>", lambda e: self.cb and self.cb(self))
        self.entry.bind("<<Paste>>", lambda e: self.entry.after(1, lambda: self.cb and self.cb(self)))

    def pack(self, **kw):
        self.canvas.pack(**kw)

    def _img(self, focused):
        return self.pills.get(self.w, self.h, 12, FIELD, PINK if focused else None, 1)

    def _show_placeholder(self):
        self.placeholder = True
        self.entry.config(fg=DIM)
        self.entry.insert(0, self.ph)

    def _focus_in(self, _):
        if self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=FG)
            self.placeholder = False
        self.canvas.itemconfig(self.bg, image=self._img(True))

    def _focus_out(self, _):
        if not self.entry.get().strip():
            self._show_placeholder()
        self.canvas.itemconfig(self.bg, image=self._img(False))

    def get(self):
        return "" if self.placeholder else self.entry.get().strip()

    def set(self, text):
        focused = self.entry.focus_get() is self.entry
        self.entry.delete(0, "end")
        self.placeholder = False
        self.entry.config(fg=FG)
        if text:
            self.entry.insert(0, text)
        elif not focused:
            self._show_placeholder()

    def focus(self):
        self.entry.focus_set()


class SettingsWindow:
    def __init__(self, app):
        self.app = app
        cfg = app.cfg
        dpi = app.dpi
        self.pills = Pills()
        self.orig_alpha = cfg["alpha"]
        cw = int(372 * dpi)

        win = self.win = tk.Toplevel(app.root)
        win.title(f"{APP_NAME} · {T('set_title')}")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.iconphoto(False, app.icon_photo)
        win.protocol("WM_DELETE_WINDOW", self.cancel)
        dark_title_bar(win)

        body = tk.Frame(win, bg=BG, padx=int(24 * dpi), pady=int(20 * dpi))
        body.pack()

        def label(text, top=14):
            tk.Label(body, text=text, fg=SOFT, bg=BG, font=("Segoe UI Semibold", 10),
                     anchor="w").pack(fill="x", pady=(int(top * dpi), int(6 * dpi)))

        tk.Label(body, text=APP_NAME, fg=PINK, bg=BG, font=("Segoe UI Semibold", 20),
                 anchor="w").pack(fill="x")

        label(T("profile"), top=12)
        current = cfg["username"] or ("" if cfg["user_query"].isdigit() else cfg["user_query"].lstrip("@"))
        self.user_f = TextField(body, self.pills, dpi, cw, T("profile_ph"), current, self._user_changed)
        self.user_f.pack()
        self.user_hint = tk.Label(body, text=T("profile_hint"), fg=DIM, bg=BG,
                                  font=("Segoe UI", 9), anchor="w")
        self.user_hint.pack(fill="x", pady=(int(5 * dpi), 0))

        sep = tk.Frame(body, bg=BG)
        sep.pack(fill="x", pady=(int(8 * dpi), 0))
        tk.Frame(sep, bg="#2c2839", height=1).pack(side="left", fill="x", expand=True)
        tk.Label(sep, text=T("or"), fg=DIM, bg=BG, font=("Segoe UI", 9)).pack(side="left", padx=8)
        tk.Frame(sep, bg="#2c2839", height=1).pack(side="left", fill="x", expand=True)

        label(T("link"), top=4)
        uid = next((d.get("id") for d in app.cache.values() if d.get("id")), None)
        if not uid and cfg["user_query"].isdigit():
            uid = cfg["user_query"]
        link = f"https://osu.ppy.sh/users/{uid}" if uid else ""
        self.link_f = TextField(body, self.pills, dpi, cw, T("link_ph"), link, self._link_changed)
        self.link_f.pack()
        self.link_hint = tk.Label(body, text=T("link_hint"), fg=DIM, bg=BG,
                                  font=("Segoe UI", 9), anchor="w")
        self.link_hint.pack(fill="x", pady=(int(5 * dpi), 0))
        self.source = "user"

        label(T("language"))
        self.lang = Segmented(body, self.pills, dpi, [("es", "Español"), ("en", "English")],
                              cfg["lang"], cw)
        self.lang.pack()

        label(T("refresh_every"))
        opts = [(m, f"{m} min") for m in (2, 5, 10, 30)]
        cur = cfg["refresh_minutes"] if cfg["refresh_minutes"] in (2, 5, 10, 30) else 5
        self.refresh = Segmented(body, self.pills, dpi, opts, cur, cw)
        self.refresh.pack()

        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(int(14 * dpi), int(6 * dpi)))
        tk.Label(row, text=T("opacity"), fg=SOFT, bg=BG, font=("Segoe UI Semibold", 10)).pack(side="left")
        self.alpha_lbl = tk.Label(row, text="", fg=DIM, bg=BG, font=("Segoe UI", 10))
        self.alpha_lbl.pack(side="right")
        self.alpha = Slider(body, self.pills, dpi, 30, 100, int(cfg["alpha"] * 100), cw,
                            self._alpha_changed)
        self.alpha.pack()
        self._alpha_changed(self.alpha.value, preview=False)

        tk.Frame(body, bg="#2c2839", height=1).pack(fill="x", pady=(int(18 * dpi), int(6 * dpi)))
        self.t_top = self._toggle_row(body, T("topmost"), cfg["topmost"])
        self.t_start = self._toggle_row(body, T("startup"), startup_enabled())
        self.t_fs = self._toggle_row(body, T("hide_fs"), cfg["hide_fullscreen"])
        self.t_obs = self._toggle_row(body, T("obs"), cfg["obs_enabled"], self._obs_toggled)
        obs_wrap = tk.Frame(body, bg=BG)
        obs_wrap.pack(fill="x")
        self.obs_box = tk.Frame(obs_wrap, bg=BG)
        self.obs_hint = tk.Label(self.obs_box, text=T("obs_hint"), fg=DIM, bg=BG,
                                 font=("Segoe UI", 9), anchor="w", justify="left", wraplength=cw)
        self.obs_hint.pack(fill="x", pady=(int(4 * dpi), 0))
        obs_row = tk.Frame(self.obs_box, bg=BG)
        obs_row.pack(fill="x", pady=(int(8 * dpi), 0))
        if cfg["obs_enabled"]:
            self.obs_box.pack(fill="x")
        Button(obs_row, self.pills, dpi, T("copy"), self._copy_obs, primary=False).pack(side="right")
        Button(obs_row, self.pills, dpi, T("copy_path"), self._copy_path, primary=False).pack(
            side="right", padx=(0, int(8 * dpi)))

        btns = tk.Frame(body, bg=BG)
        btns.pack(fill="x", pady=(int(18 * dpi), 0))
        Button(btns, self.pills, dpi, T("save"), self.save).pack(side="right")
        Button(btns, self.pills, dpi, T("cancel"), self.cancel, primary=False).pack(
            side="right", padx=(0, int(8 * dpi)))

        win.bind("<Return>", lambda e: self.save())
        win.bind("<Escape>", lambda e: self.cancel())
        self._user_changed(self.user_f, initial=True)
        win.update_idletasks()
        x = app.root.winfo_x() if app.root.winfo_viewable() else win.winfo_screenwidth() // 3
        y = max(0, app.root.winfo_y() - 40) if app.root.winfo_viewable() else 100
        x = min(max(0, x), win.winfo_screenwidth() - win.winfo_width())
        y = min(y, win.winfo_screenheight() - win.winfo_height() - 60)
        win.geometry(f"+{x}+{max(0, y)}")
        win.focus_force()
        if not current and not link:
            self.user_f.focus()

    def _obs_toggled(self, on):
        self.app.set_obs(on)
        if on:
            self.obs_box.pack(fill="x")
        else:
            self.obs_box.pack_forget()

    def _copy_obs(self):
        self.t_obs.set(True)
        self.app.set_obs(True)
        self._copy_text(self.app.obs.url(self.app.cfg["obs_port"]))

    def _copy_path(self):
        self.t_obs.set(True)
        self.app.set_obs(True)
        self._copy_text(ObsServer.FILE)

    def _copy_text(self, text):
        self.win.clipboard_clear()
        self.win.clipboard_append(text)
        self.obs_hint.config(text=T("copied"), fg=GREEN)
        self.win.after(1500, lambda: self.obs_hint.winfo_exists()
                       and self.obs_hint.config(text=T("obs_hint"), fg=DIM))

    def _toggle_row(self, parent, text, value, on_change=None):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=int(5 * self.app.dpi))
        tk.Label(row, text=text, fg=SOFT, bg=BG, font=("Segoe UI", 10)).pack(side="left")
        t = Toggle(row, self.pills, self.app.dpi, value, on_change)
        t.pack(side="right")
        return t

    def _user_changed(self, field, initial=False):
        text = field.get()
        if not initial:
            self.source = "user"
            if self.link_f.get():
                self.link_f.set("")
                self.link_hint.config(text=T("link_hint"), fg=DIM)
        if not text:
            self.user_hint.config(text=T("profile_hint"), fg=DIM)
        else:
            _, shown, _, _ = parse_profile_input(text)
            self.user_hint.config(text=T("det_user", u=shown), fg=GREEN)

    def _link_changed(self, field):
        text = field.get()
        if not text:
            self.source = "user"
            self.link_hint.config(text=T("link_hint"), fg=DIM)
            return
        self.source = "link"
        if not is_profile_link(text):
            self.link_hint.config(text=T("bad_link"), fg=RED)
            return
        _, shown, mode, is_id = parse_profile_input(text)
        msg = T("det_id", u=shown) if is_id else T("det_user", u=shown)
        if mode:
            msg += T("det_mode", m=dict(MODES)[mode])
        self.link_hint.config(text=msg, fg=GREEN)
        if not is_id:
            self.user_f.set(shown)
            self.user_hint.config(text=T("det_user", u=shown), fg=GREEN)

    def _alpha_changed(self, v, preview=True):
        self.alpha_lbl.config(text=f"{v}%")
        if preview:
            self.app.cfg["alpha"] = v / 100
            self.app.redraw()

    def cancel(self):
        if self.app.cfg["alpha"] != self.orig_alpha:
            self.app.cfg["alpha"] = self.orig_alpha
            self.app.redraw()
        self.close()

    def close(self):
        self.app.settings = None
        self.win.destroy()

    def save(self):
        link, name = self.link_f.get(), self.user_f.get()
        if self.source == "link" and link:
            if not is_profile_link(link):
                self.link_hint.config(text=T("bad_link"), fg=RED)
                self.link_f.focus()
                return
            text = link
        elif name:
            text = name
        else:
            self.user_hint.config(text=T("need_profile"), fg=RED)
            self.user_f.focus()
            return
        query, shown, mode, is_id = parse_profile_input(text)
        cfg = self.app.cfg
        same = (shown.lower() == (cfg["username"] or "").lower()
                or query.lower() == cfg["user_query"].lower())
        if not same:
            self.app.change_user(query, "" if is_id else shown)
        if mode:
            cfg["mode"] = mode
        cfg["lang"] = self.lang.value
        cfg["refresh_minutes"] = self.refresh.value
        cfg["alpha"] = self.alpha.value / 100
        cfg["topmost"] = self.t_top.value
        set_startup(self.t_start.value)
        cfg["hide_fullscreen"] = self.t_fs.value
        cfg["obs_enabled"] = self.t_obs.value
        self.close()
        self.app.apply_settings()


class Widget:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(DB_PATH) and os.path.exists(LEGACY_DB):
            shutil.copy2(LEGACY_DB, DB_PATH)
        self.store = Store(DB_PATH)
        self.cfg = self.store.load_settings()
        LANG[0] = self.cfg["lang"]
        self.cache, self.baseline = {}, {}
        self.avatar = self.cover = None
        self.avatar_url = self.cover_url = None
        self.status, self.status_kind = "", "ok"
        self.results = queue.Queue()
        self.pending = 0
        self.refresh_job = None
        self.regions = []
        self._press = None
        self.settings = None
        self.tray = None
        self.visible = True
        self.mt, self.mt_state, self.mt_t = None, None, 0
        self._load_cached()

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", self.cfg["topmost"])
        self.root.geometry(f"1x1+{self.cfg['x']}+{self.cfg['y']}")
        self.icon_photo = ImageTk.PhotoImage(make_icon(32))
        self.root.iconphoto(True, self.icon_photo)

        self.dpi = self.root.winfo_fpixels("1i") / 96
        self.card = Card(self.dpi)

        self.surface = tk.Label(self.root, bg=KEY, bd=0, highlightthickness=0)
        self.surface.pack(fill="both", expand=True)
        for seq, fn in (("<ButtonPress-1>", self._on_press), ("<B1-Motion>", self._on_drag),
                        ("<ButtonRelease-1>", self._on_release), ("<Motion>", self._on_hover),
                        ("<Button-3>", self._on_menu)):
            self.surface.bind(seq, fn)

        try:
            self.layered = LayeredWindow(self.root)
        except Exception:
            self.layered = None
            self.root.attributes("-transparentcolor", KEY)

        self.game_hidden = False
        self.fs_override = False
        self._refresh_due = False
        try:
            self.fs = FullscreenWatcher()
        except Exception:
            self.fs = None
        self.root.after(1500, self._watch_fullscreen)
        self.obs = ObsServer()
        self._obs_job = None
        if self.cfg["obs_enabled"]:
            self.obs.start(self.cfg["obs_port"])

        self._build_menu()
        self._start_tray()
        if self.cache.get(self.cfg["mode"]):
            self.status, self.status_kind = T("cached", t=fmt_when(self.cache[self.cfg["mode"]]["_t"])), "ok"
        self.redraw()

        if not self.cfg["user_query"]:
            self.root.after(200, self.open_settings)
            self.status, self.status_kind = T("no_user"), "warn"
            self.redraw()
        else:
            self.refresh()

    def _user_key(self):
        return self.cfg["user_query"].lower()

    def _load_cached(self):
        if not self.cfg["user_query"]:
            return
        self.cache = self.store.load_profiles(self._user_key())
        mt = self.cache.pop("mt_skills", None)
        if mt:
            self.mt, self.mt_t = mt, mt.get("_t", 0)
        self.baseline = {m: (d.get("rank"), d.get("pp")) for m, d in self.cache.items()}
        any_d = next(iter(self.cache.values()), None)
        if any_d:
            if any_d.get("avatar_url"):
                self.avatar = self.store.load_image(any_d["avatar_url"])
                self.avatar_url = any_d["avatar_url"] if self.avatar else None
            if any_d.get("cover_url"):
                self.cover = self.store.load_image(any_d["cover_url"])
                self.cover_url = any_d["cover_url"] if self.cover else None

    def change_user(self, query, display):
        self.cfg["user_query"] = query
        self.cfg["username"] = display
        self.cache, self.baseline = {}, {}
        self.avatar = self.cover = self.avatar_url = self.cover_url = None
        self.mt, self.mt_state, self.mt_t = None, None, 0
        self._load_cached()

    def save_cfg(self):
        self.store.save_settings(self.cfg)

    def _hwnd(self):
        if self.layered:
            return self.layered.hwnd
        return self.fs.u.GetAncestor(self.root.winfo_id(), 2) if self.fs else None

    def _watch_fullscreen(self):
        try:
            full = bool(self.fs and self.cfg["hide_fullscreen"] and self.fs.active(self._hwnd()))
        except Exception:
            full = False
        if full:
            if not self.game_hidden and not self.fs_override:
                self.game_hidden = True
                if self.visible:
                    self.root.withdraw()
        else:
            self.fs_override = False
            if self.game_hidden:
                self.game_hidden = False
                if self.visible:
                    self.show(user=False)
                if self._refresh_due:
                    self._refresh_due = False
                    self.refresh()
        self.root.after(1500, self._watch_fullscreen)

    def toggle_hide_fs(self):
        self.cfg["hide_fullscreen"] = not self.cfg["hide_fullscreen"]
        self.save_cfg()
        if self.tray:
            self.tray.update_menu()

    def _render_args(self):
        return (self.cache.get(self.cfg["mode"]), self.cfg["mode"], self.cfg["expanded"],
                self.status, self.status_kind, self.avatar, self.cover,
                self.cfg["mania_view"], self.mt, self.mt_state)

    def _schedule_obs(self):
        if self.obs.running and not self._obs_job:
            self._obs_job = self.root.after(400, self._render_obs)

    def _render_obs(self):
        self._obs_job = None
        if self.obs.running:
            img, _ = self.card.render(*self._render_args(), controls=False)
            self.obs.update(img)

    def set_obs(self, on):
        self.cfg["obs_enabled"] = bool(on)
        if on:
            self.obs.start(self.cfg["obs_port"])
            self._schedule_obs()
        else:
            self.obs.stop()
        self.save_cfg()
        if self.tray:
            self.tray.update_menu()

    def copy_obs_link(self):
        if not self.obs.running:
            self.set_obs(True)
        self.root.clipboard_clear()
        self.root.clipboard_append(self.obs.url(self.cfg["obs_port"]))

    def redraw(self):
        self._schedule_obs()
        if self.game_hidden or not self.visible:
            return
        img, self.regions = self.card.render(*self._render_args())
        w, h = img.size
        self.root.geometry(f"{w}x{h}")
        self.root.update_idletasks()
        if self.layered and self.layered.show(img, self.cfg["alpha"]):
            return
        if self.layered:
            self.layered = None
            self.root.attributes("-transparentcolor", KEY)
        self.root.attributes("-alpha", self.cfg["alpha"])
        a = img.getchannel("A").point(lambda v: 255 if v > 127 else 0)
        flat = Image.new("RGB", img.size, KEY)
        flat.paste(img.convert("RGB"), (0, 0), a)
        self.photo = ImageTk.PhotoImage(flat)
        self.surface.config(image=self.photo)

    def set_status(self, text, kind="ok"):
        self.status, self.status_kind = text, kind
        self.redraw()

    def _build_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, bg="#24212f", fg=FG, activebackground=PINK,
                            activeforeground="white", bd=0, relief="flat",
                            font=("Segoe UI", 10))
        self.topmost_var = tk.BooleanVar(value=self.cfg["topmost"])
        self.startup_var = tk.BooleanVar(value=startup_enabled())
        self.menu.add_command(label="  " + T("refresh"), command=self.refresh)
        self.menu.add_command(label="  " + T("open_profile"), command=self.open_profile)
        self.menu.add_command(label="  " + T("open_mt"), command=self.open_mt)
        self.menu.add_separator()
        self.menu.add_checkbutton(label="  " + T("topmost"), variable=self.topmost_var,
                                  command=lambda: self.set_topmost(self.topmost_var.get()))
        self.menu.add_checkbutton(label="  " + T("startup"), variable=self.startup_var,
                                  command=lambda: set_startup(self.startup_var.get()))
        self.menu.add_command(label="  " + T("settings"), command=self.open_settings)
        self.menu.add_separator()
        self.menu.add_command(label="  " + T("quit"), command=self.quit)

    def _on_menu(self, e):
        self.topmost_var.set(self.cfg["topmost"])
        self.startup_var.set(startup_enabled())
        self.menu.tk_popup(e.x_root, e.y_root)

    def _start_tray(self):
        if pystray is None:
            return
        ui = self.ui
        menu = pystray.Menu(
            pystray.MenuItem(lambda i: T("show_hide"), lambda: ui(self.toggle_visible), default=True),
            pystray.MenuItem(lambda i: T("refresh"), lambda: ui(self.refresh)),
            pystray.MenuItem(lambda i: T("settings"), lambda: ui(self.open_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda i: T("topmost"), lambda: ui(lambda: self.set_topmost(not self.cfg["topmost"])),
                             checked=lambda i: self.cfg["topmost"]),
            pystray.MenuItem(lambda i: T("startup"), lambda: set_startup(not startup_enabled()),
                             checked=lambda i: startup_enabled()),
            pystray.MenuItem(lambda i: T("hide_fs"), lambda: ui(self.toggle_hide_fs),
                             checked=lambda i: self.cfg["hide_fullscreen"]),
            pystray.MenuItem(lambda i: T("obs"), lambda: ui(lambda: self.set_obs(not self.cfg["obs_enabled"])),
                             checked=lambda i: self.cfg["obs_enabled"]),
            pystray.MenuItem(lambda i: T("obs_copy"), lambda: ui(self.copy_obs_link)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda i: T("quit"), lambda: ui(self.quit)),
        )
        try:
            self.tray = pystray.Icon(APP_ID, make_icon(64), APP_NAME, menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            self.tray = None

    def ui(self, fn):
        try:
            self.root.after(0, fn)
        except RuntimeError:
            pass

    def _hit(self, e):
        x, y = e.x / self.dpi, e.y / self.dpi
        for x0, y0, x1, y1, action in self.regions:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return action
        return None

    def _on_hover(self, e):
        cur = "hand2" if self._hit(e) else ""
        if self.surface.cget("cursor") != cur:
            self.surface.config(cursor=cur)

    def _on_press(self, e):
        self._press = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(), False)

    def _on_drag(self, e):
        if not self._press:
            return
        sx, sy, wx, wy, moved = self._press
        dx, dy = e.x_root - sx, e.y_root - sy
        if moved or abs(dx) + abs(dy) > 4:
            self._press = (sx, sy, wx, wy, True)
            self.root.geometry(f"+{wx + dx}+{wy + dy}")

    def _on_release(self, e):
        press, self._press = self._press, None
        if not press:
            return
        if press[4]:
            self.cfg["x"], self.cfg["y"] = self.root.winfo_x(), self.root.winfo_y()
            self.save_cfg()
            return
        hit = self._hit(e)
        if not hit:
            return
        action, arg = hit
        if action == "mode":
            self.set_mode(arg)
        elif action == "expand":
            self.cfg["expanded"] = not self.cfg["expanded"]
            self.save_cfg()
            self.redraw()
        elif action == "refresh":
            self.refresh()
            if self._skills_visible():
                self.refresh_skills(force=True)
        elif action == "close":
            self.hide()
        elif action == "skills":
            self.toggle_skills()
        elif action == "open_mt":
            self.open_mt()

    def set_mode(self, mode):
        if mode == self.cfg["mode"]:
            return
        self.cfg["mode"] = mode
        self.save_cfg()
        d = self.cache.get(mode)
        if d and self.status_kind == "ok":
            self.status = T("updated", t=time.strftime("%H:%M", time.localtime(d["_t"])))
        self.redraw()
        self.refresh(only_if_stale=True)

    def _skills_visible(self):
        return (self.cfg["mode"] == "mania" and self.cfg["expanded"]
                and self.cfg["mania_view"] == "skills")

    def _user_id(self):
        return next((d.get("id") for d in self.cache.values() if d.get("id")), None)

    def toggle_skills(self):
        if self._skills_visible():
            self.cfg["mania_view"] = "stats"
        else:
            self.cfg["mania_view"] = "skills"
            self.cfg["expanded"] = True
            self.refresh_skills()
        self.save_cfg()
        self.redraw()

    def refresh_skills(self, force=False):
        if not force and self.mt and time.time() - self.mt_t < 1800:
            return
        self.mt_state = "loading"
        uid = self._user_id()
        if not uid:
            return
        self.pending += 1
        threading.Thread(target=self._mt_worker, args=(uid, self.cfg["user_query"]),
                         daemon=True).start()
        if self.pending == 1:
            self.root.after(150, self._poll)

    def _mt_worker(self, uid, query):
        try:
            self.results.put(("mt", "mania", query, fetch_mt_skills(uid), None))
        except FetchError as e:
            self.results.put(("mterr", "mania", query, str(e), None))
        except Exception:
            self.results.put(("mterr", "mania", query, "parse", None))

    def open_mt(self):
        d = self.cache.get("mania") or next(iter(self.cache.values()), None)
        name = (d or {}).get("username") or self.cfg["username"]
        if name:
            webbrowser.open(MT_PAGE.format(urllib.parse.quote(name, safe="")))

    def set_topmost(self, on):
        self.cfg["topmost"] = bool(on)
        self.root.attributes("-topmost", self.cfg["topmost"])
        self.save_cfg()
        if self.tray:
            self.tray.update_menu()

    def hide(self):
        if not self.tray:
            self.quit()
            return
        self.root.withdraw()
        self.visible = False
        if not self.cfg["tray_notified"]:
            self.cfg["tray_notified"] = True
            self.save_cfg()
            try:
                self.tray.notify(T("tray_hidden"), APP_NAME)
            except Exception:
                pass

    def show(self, user=True):
        if user and self.game_hidden:
            self.game_hidden = False
            self.fs_override = True
        self.root.deiconify()
        self.visible = True
        if self.layered:
            self.layered.apply_style()
        self.root.attributes("-topmost", self.cfg["topmost"])
        self.redraw()

    def toggle_visible(self):
        if self.visible and not self.game_hidden:
            self.hide()
        else:
            self.show()

    def open_profile(self):
        d = self.cache.get(self.cfg["mode"])
        if d and d.get("id"):
            webbrowser.open(f"https://osu.ppy.sh/users/{d['id']}/{self.cfg['mode']}")
        elif self.cfg["user_query"]:
            webbrowser.open(f"https://osu.ppy.sh/users/{self.cfg['user_query']}")

    def open_settings(self):
        if not self.visible or self.game_hidden:
            self.show()
        if self.settings is not None:
            try:
                self.settings.win.lift()
                self.settings.win.focus_force()
                return
            except tk.TclError:
                self.settings = None
        self.settings = SettingsWindow(self)

    def apply_settings(self):
        LANG[0] = self.cfg["lang"]
        if self.cfg["obs_enabled"] != self.obs.running:
            self.set_obs(self.cfg["obs_enabled"])
        self.save_cfg()
        self.root.attributes("-topmost", self.cfg["topmost"])
        self._build_menu()
        if self.tray:
            self.tray.update_menu()
        self.refresh()

    def quit(self):
        self.save_cfg()
        self.obs.stop()
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        self.store.close()
        self.root.destroy()

    def refresh(self, only_if_stale=False):
        if not self.cfg["user_query"]:
            return
        mode = self.cfg["mode"]
        cached = self.cache.get(mode)
        if only_if_stale and cached and not cached.get("_stale") and time.time() - cached["_t"] < 60:
            return
        if self.game_hidden and not self.obs.running:
            self._refresh_due = True
            self._schedule_refresh()
            return
        self.set_status(T("updating"))
        self.pending += 1
        threading.Thread(target=self._worker, args=(mode, self.cfg["user_query"]),
                         daemon=True).start()
        if self.pending == 1:
            self.root.after(150, self._poll)
        self._schedule_refresh()
        if self._skills_visible():
            self.refresh_skills()

    def _schedule_refresh(self):
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
        minutes = max(1, int(self.cfg.get("refresh_minutes", 5)))
        self.refresh_job = self.root.after(minutes * 60_000, self.refresh)

    def _worker(self, mode, query):
        try:
            data = fetch_profile(query, mode)
            k = self.card.k
            imgs = {}
            for kind, url, mw, mh in (("avatar", data["avatar_url"], 96 * k, 96 * k),
                                      ("cover", data["cover_url"], Card.W * k, 400 * k)):
                if url and url != getattr(self, kind + "_url"):
                    try:
                        imgs[kind] = (url,) + download_image(url, int(mw), int(mh))
                    except Exception:
                        pass
            self.results.put(("ok", mode, query, data, imgs))
        except FetchError as e:
            self.results.put(("err", mode, query, str(e), None))
        except Exception:
            self.results.put(("err", mode, query, "parse", None))

    def _poll(self):
        changed = False
        while True:
            try:
                kind, mode, query, payload, imgs = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending -= 1
            if query != self.cfg["user_query"]:
                continue
            changed = True
            if kind == "mt":
                payload["_t"] = self.mt_t = time.time()
                self.mt, self.mt_state = payload, None
                self.store.save_profile(self._user_key(), "mt_skills", payload)
                continue
            if kind == "mterr":
                self.mt_state = payload
                continue
            if kind == "err":
                cached = self.cache.get(mode)
                if cached and payload in ("offline", "http", "ratelimit"):
                    self.status, self.status_kind = T("offline", t=fmt_when(cached["_t"])), "warn"
                else:
                    self.status, self.status_kind = T("err_" + payload), "err"
                continue
            payload["_t"] = time.time()
            payload["_delta"] = self._delta(payload, mode)
            self.cache[mode] = payload
            self.store.save_profile(self._user_key(), mode, payload)
            if not self.cfg["username"]:
                self.cfg["username"] = payload["username"]
                self.save_cfg()
            for name, (url, im, raw) in (imgs or {}).items():
                setattr(self, name, im)
                setattr(self, name + "_url", url)
                self.store.save_image(url, raw)
            self.status, self.status_kind = T("updated", t=time.strftime("%H:%M")), "ok"
            if self.mt_state == "loading" and not self.mt and self._skills_visible():
                self.refresh_skills()
        if changed:
            self.redraw()
        if self.pending > 0:
            self.root.after(150, self._poll)

    def _delta(self, d, mode):
        base = self.baseline.get(mode)
        if base is None:
            self.baseline[mode] = (d["rank"], d["pp"])
            return None
        b_rank, b_pp = base
        if not (b_rank and d["rank"]):
            return None
        diff = b_rank - d["rank"]
        dpp = d["pp"] - (b_pp or d["pp"])
        if not diff and abs(dpp) < 0.5:
            return None
        arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "•")
        col = GREEN if diff > 0 else (RED if diff < 0 else DIM)
        return f"{arrow} {abs(diff):,}   {dpp:+,.0f}pp", col

    def run(self):
        self.root.mainloop()


def single_instance():
    try:
        k = ctypes.windll.kernel32
        k.CreateMutexW.restype = ctypes.c_void_p
        single_instance.handle = k.CreateMutexW(None, False, APP_ID + "-single")
        return k.GetLastError() != 183
    except Exception:
        return True


if __name__ == "__main__":
    if single_instance():
        Widget().run()
