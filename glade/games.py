# ~/nixos-config/modules/home-manager/hyprland/desktops/glade/games.py
#
# glade-games: the Games tab on the glade's bar. A panel of box art for every game on the
# computer, wherever it came from — Steam, Heroic (Epic, GOG), Lutris (the EA app), other
# installed games, and emulator games in ~/Games/ROMs — most recently played first, with a
# search box. Clicking one starts it through its own launcher (steam://, heroic://,
# lutris:, the emulator), so the client opens first and then the game.
#
# It is a layer-shell overlay with a dimmed backdrop: a click outside the panel, Esc, or
# clicking Games again closes it. Like everything in the glade it eases in, never pops.
import glob
import hashlib
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, GtkLayerShell  # noqa: E402

HOME = os.path.expanduser("~")
ROMS = os.path.join(HOME, "Games", "ROMs")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.join(HOME, ".cache"), "glade-games")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local/state"), "glade", "games.json")
ART_W, ART_H = 120, 180

# emulator games: file ending -> (badge, emulator command, libretro thumbnail set)
EMULATED = {
    ".nds": ("DS", ["desmume"], "Nintendo - Nintendo DS"),
    ".gba": ("GBA", ["mgba-qt"], "Nintendo - Game Boy Advance"),
    ".gbc": ("GBC", ["mgba-qt"], "Nintendo - Game Boy Color"),
    ".gb": ("GB", ["mgba-qt"], "Nintendo - Game Boy"),
    ".iso": ("GC/Wii", ["dolphin-emu", "-e"], "Nintendo - GameCube"),
    ".rvz": ("GC/Wii", ["dolphin-emu", "-e"], "Nintendo - GameCube"),
    ".gcm": ("GC", ["dolphin-emu", "-e"], "Nintendo - GameCube"),
    ".wbfs": ("Wii", ["dolphin-emu", "-e"], "Nintendo - Wii"),
}

# Steam's own tools that sit in its library like games
STEAM_TOOLS = re.compile(r"^(Proton|Steam Linux Runtime|Steamworks Common|SteamVR)", re.I)
# app entries that are launchers or tools, not games
NOT_GAMES = {"steam", "heroic", "lutris", "protonup-qt", "r2modman", "partydeck", "quiver-launcher"}


def stamp(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# --- finding games ------------------------------------------------------------------------

def vdf_values(text, key):
    return re.findall(r'"%s"\s+"([^"]*)"' % re.escape(key), text)


def steam_games():
    root = os.path.join(HOME, ".local/share/Steam")
    libs = [root]
    try:
        with open(os.path.join(root, "steamapps/libraryfolders.vdf")) as f:
            libs += vdf_values(f.read(), "path")
    except OSError:
        pass
    out, seen = [], set()
    for lib in dict.fromkeys(libs):
        for acf in glob.glob(os.path.join(lib, "steamapps", "appmanifest_*.acf")):
            try:
                with open(acf, errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            appid = (vdf_values(text, "appid") or [""])[0]
            name = (vdf_values(text, "name") or [""])[0]
            flags = int((vdf_values(text, "StateFlags") or ["0"])[0] or 0)
            if not appid or appid in seen or not name or STEAM_TOOLS.match(name) or appid == "228980":
                continue
            if not flags & 4:  # not fully installed
                continue
            seen.add(appid)
            last = int((vdf_values(text, "LastPlayed") or ["0"])[0] or 0)
            cache = os.path.join(root, "appcache/librarycache", appid)
            art = (glob.glob(os.path.join(cache, "library_600x900.jpg"))
                   + glob.glob(os.path.join(cache, "*", "library_600x900.jpg"))
                   + glob.glob(os.path.join(root, "appcache/librarycache", appid + "_library_600x900.jpg")))
            header = glob.glob(os.path.join(cache, "header.jpg")) + glob.glob(os.path.join(cache, "*", "header.jpg"))
            out.append(dict(id="steam:" + appid, name=name, badge="Steam", last=last,
                            art=art[0] if art else None, fallback=header[0] if header else None,
                            art_url=f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                            cmd=["steam", f"steam://rungameid/{appid}"]))
    return out


def heroic_games():
    base = os.path.join(HOME, ".config/heroic")
    played = read_json(os.path.join(base, "store/timestamp.json"), {}) or {}
    out = []

    def art_for(library_file, key):
        lib = read_json(os.path.join(base, "store_cache", library_file), {}) or {}
        for g in lib.get("library", lib.get("games", [])) if isinstance(lib, dict) else []:
            if isinstance(g, dict) and g.get("app_name") == key:
                return g.get("art_square") or g.get("art_cover")
        return None

    epic = read_json(os.path.join(base, "legendaryConfig/legendary/installed.json"), {}) or {}
    for key, g in epic.items():
        out.append(dict(id="epic:" + key, name=g.get("title") or key, badge="Epic",
                        last=stamp((played.get(key) or {}).get("lastPlayed")), art_url=art_for("legendary_library.json", key),
                        cmd=["heroic", f"heroic://launch?appName={key}&runner=legendary"]))
    gog = read_json(os.path.join(base, "gog_store/installed.json"), {}) or {}
    titles = {}
    for g in (read_json(os.path.join(base, "store_cache/gog_library.json"), {}) or {}).get("games", []):
        if isinstance(g, dict):
            titles[g.get("app_name")] = (g.get("title"), g.get("art_square") or g.get("art_cover"))
    for g in gog.get("installed", []) if isinstance(gog, dict) else []:
        key = g.get("appName")
        if not key:
            continue
        title, art = titles.get(key, (None, None))
        out.append(dict(id="gog:" + key, name=title or key, badge="GOG",
                        last=stamp((played.get(key) or {}).get("lastPlayed")), art_url=art,
                        cmd=["heroic", f"heroic://launch?appName={key}&runner=gog"]))
    return out


def lutris_games():
    db = os.path.join(HOME, ".local/share/lutris/pga.db")
    if not os.path.exists(db):
        return []
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1)
        rows = con.execute("select id, name, slug, runner, lastplayed from games where installed = 1").fetchall()
        con.close()
    except sqlite3.Error:
        return []
    out = []
    for gid, name, slug, runner, last in rows:
        if runner == "steam":  # Steam's own games are already listed, straight from Steam
            continue
        art = os.path.join(HOME, ".local/share/lutris/coverart", f"{slug}.jpg")
        badge = "EA" if "ea" in (slug or "").split("-") else "Lutris"
        out.append(dict(id=f"lutris:{gid}", name=name, badge=badge, last=int(last or 0),
                        art=art if os.path.exists(art) else None, cmd=["lutris", f"lutris:rungameid/{gid}"]))
    return out


def entry(path):
    e, section = {}, None
    try:
        with open(path, errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.startswith("["):
                    section = line
                elif section == "[Desktop Entry]" and "=" in line:
                    k, v = line.split("=", 1)
                    e.setdefault(k, v)
    except OSError:
        pass
    return e


def other_games():
    """Installed apps that are games but come from none of the launchers above."""
    dirs = [os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(HOME, ".local/share"), "applications")]
    dirs += [os.path.join(d, "applications") for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/share").split(":") if d]
    out, seen = [], set()
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.desktop"))):
            name = os.path.basename(path)
            if name in seen:
                continue
            seen.add(name)
            e = entry(path)
            cats = e.get("Categories", "").split(";")
            ex = e.get("Exec", "")
            if ("Game" not in cats or "Emulator" in cats or "Discord" in cats or "Utility" in cats
                    or e.get("NoDisplay") == "true" or e.get("Hidden") == "true" or "steam://" in ex or not ex):
                continue
            try:
                args = [a for a in shlex.split(ex) if not (len(a) == 2 and a[0] == "%") and not a.startswith("@@")]
            except ValueError:
                continue
            if not args or os.path.basename(args[0]) in NOT_GAMES:
                continue
            out.append(dict(id="app:" + name, name=e.get("Name") or name, badge="PC", last=0,
                            icon=e.get("Icon"), cmd=args))
    return out


def rom_games():
    out = []
    for path in sorted(glob.glob(os.path.join(ROMS, "**", "*"), recursive=True)):
        ext = os.path.splitext(path)[1].lower()
        if ext not in EMULATED or not os.path.isfile(path):
            continue
        badge, emu, system = EMULATED[ext]
        title = os.path.splitext(os.path.basename(path))[0]
        # libretro's box art, named exactly like No-Intro ROM files ("&" and friends become "_")
        named = re.sub(r'[&*/:`<>?\\|"]', "_", title)
        url = ("https://raw.githubusercontent.com/libretro-thumbnails/" + urllib.parse.quote(system.replace(" ", "_"))
               + "/master/Named_Boxarts/" + urllib.parse.quote(named) + ".png")
        nice = re.sub(r"\s*\([^)]*\)", "", title).strip() or title
        nice = nice.replace(" - ", " ")  # "Pokemon Platinum Version"
        out.append(dict(id="rom:" + path, name=nice, full=title, badge=badge, last=0, art_url=url,
                        cmd=emu + [path], wide=True))
    return out


def all_games():
    games = []
    for finder in (steam_games, heroic_games, lutris_games, other_games, rom_games):
        try:
            games += finder()
        except Exception as err:  # one broken launcher must not hide the rest
            print(f"glade-games: {finder.__name__}: {err}", file=sys.stderr)
    mine = (read_json(STATE, {}) or {}).get("played", {})
    for g in games:
        g["name"] = re.sub(r"\s*[\u00ae\u2122\u00a9]", "", g["name"])  # ® ™ © aren't in the pixel font
        g["last"] = max(g["last"], mine.get(g["id"], 0))
    # recently played first, the rest A-Z
    return sorted(games, key=lambda g: (-g["last"], g["name"].lower()))


def remember(game):
    st = read_json(STATE, {}) or {}
    st.setdefault("played", {})[game["id"]] = int(time.time())
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE + ".tmp", "w") as f:
            json.dump(st, f)
        os.replace(STATE + ".tmp", STATE)
    except OSError:
        pass


# --- box art ------------------------------------------------------------------------------

def fetch(url):
    """A remote picture, downloaded once into the cache; None if it can't be had."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest())
    if os.path.exists(path):
        return path if os.path.getsize(path) else None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "glade-games"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
    except Exception:
        data = b""  # remember the miss, so it isn't asked for every time
    with open(path, "wb") as f:
        f.write(data)
    return path if data else None


def cover(path, wide=False):
    """A picture fitted into the card: box art fills it, anything else sits in the middle."""
    pb = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pb.get_width(), pb.get_height()
    k = min(ART_W / w, ART_H / h) if wide or abs(w / h - ART_W / ART_H) > 0.12 else max(ART_W / w, ART_H / h)
    pb = pb.scale_simple(max(1, round(w * k)), max(1, round(h * k)), GdkPixbuf.InterpType.BILINEAR)
    w, h = pb.get_width(), pb.get_height()
    if w > ART_W or h > ART_H:
        pb = pb.new_subpixbuf(max(0, (w - ART_W) // 2), max(0, (h - ART_H) // 2), min(w, ART_W), min(h, ART_H))
    return pb


# --- the panel ------------------------------------------------------------------------------

class Panel:
    def __init__(self, app):
        self.app = app
        self.games = all_games()
        self.closing = False

        win = self.win = Gtk.Window()
        app.add_window(win)
        win.set_name("backdrop")
        GtkLayerShell.init_for_window(win)
        GtkLayerShell.set_namespace(win, "glade-games")
        GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(win, edge, True)
        GtkLayerShell.set_exclusive_zone(win, -1)
        visual = win.get_screen().get_rgba_visual()  # so the dimmed backdrop is see-through
        if visual:
            win.set_visual(visual)
        mon = pointer_monitor(win.get_display())  # open on the screen he clicked from
        if mon is not None:
            GtkLayerShell.set_monitor(win, mon)
        win.connect("key-press-event", self.key)
        win.connect("button-press-event", self.backdrop_click)

        panel = self.panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.set_name("panel")
        panel.set_halign(Gtk.Align.CENTER)
        panel.set_valign(Gtk.Align.CENTER)
        panel.connect("button-press-event", lambda *_: True)  # clicks on the panel never close it
        ev = Gtk.EventBox()
        ev.add(panel)
        ev.connect("button-press-event", lambda *_: True)
        win.add(ev)

        head = Gtk.Box(spacing=10)
        title = Gtk.Label(label="🎮 Games")
        title.set_name("title")
        head.pack_start(title, False, False, 0)
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("type to search, or just click")
        self.search.connect("search-changed", lambda *_: self.flow.invalidate_filter())
        self.search.connect("activate", self.first)
        head.pack_start(self.search, True, True, 0)
        count = Gtk.Label(label=f"{len(self.games)} games")
        count.set_name("count")
        head.pack_end(count, False, False, 0)
        panel.pack_start(head, False, False, 0)

        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_homogeneous(True)
        self.flow.set_min_children_per_line(3)
        self.flow.set_max_children_per_line(8)
        self.flow.set_row_spacing(12)
        self.flow.set_column_spacing(12)
        self.flow.set_filter_func(self.matches)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.flow)
        panel.pack_start(scroll, True, True, 0)

        hint = Gtk.Label(label="Games you played lately come first.  Emulator games go in Games/ROMs in your home folder.")
        hint.set_name("hint")
        panel.pack_end(hint, False, False, 0)

        self.pics = {}
        for g in self.games:
            self.flow.add(self.card(g))
        if not self.games:
            self.flow.add(Gtk.Label(label="No games found yet"))

        mon = mon or win.get_display().get_monitor(0)
        geo = mon.get_geometry() if mon else None
        w = min(1180, int((geo.width if geo else 1600) * 0.8))
        h = min(760, int((geo.height if geo else 900) * 0.82))
        panel.set_size_request(w, h)

        win.show_all()
        self.search.grab_focus()
        GLib.timeout_add(60, lambda: win.get_style_context().add_class("shown") or False)
        threading.Thread(target=self.load_art, daemon=True).start()

    def card(self, g):
        btn = Gtk.Button()
        btn.get_style_context().add_class("game")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(f"{g.get('full') or g['name']}  ·  {g['badge']}")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        frame = Gtk.Overlay()
        art = Gtk.Image()
        art.set_size_request(ART_W, ART_H)
        art.get_style_context().add_class("art")
        frame.add(art)
        initial = Gtk.Label(label=g["name"][:1].upper())  # until the box art arrives
        initial.get_style_context().add_class("initial")
        frame.add_overlay(initial)
        badge = Gtk.Label(label=g["badge"])
        badge.get_style_context().add_class("badge")
        badge.get_style_context().add_class("b-" + re.sub(r"[^a-z]", "", g["badge"].lower()))
        badge.set_halign(Gtk.Align.START)
        badge.set_valign(Gtk.Align.START)
        frame.add_overlay(badge)
        box.pack_start(frame, False, False, 0)
        name = Gtk.Label(label=g["name"])
        name.set_max_width_chars(14)
        name.set_ellipsize(3)  # Pango.EllipsizeMode.END
        name.get_style_context().add_class("name")
        box.pack_start(name, False, False, 0)
        btn.add(box)
        btn.connect("clicked", lambda *_: self.launch(g, btn))
        child = Gtk.FlowBoxChild()
        child.add(btn)
        child.game = g
        self.pics[g["id"]] = (art, initial)
        return child

    def load_art(self):
        for g in list(self.games):
            path = g.get("art")
            if not path and g.get("art_url"):
                path = fetch(g["art_url"])
            if not path and g.get("fallback"):  # Steam's wide banner, when it has no box art
                path, g["wide"] = g["fallback"], True
            if not path and g.get("icon"):
                path = icon_path(g["icon"])
            if path:
                GLib.idle_add(self.set_art, g, path)

    def set_art(self, g, path):
        try:
            pb = cover(path, g.get("wide") or bool(g.get("icon") and not g.get("art")))
        except GLib.Error:
            return False
        art, initial = self.pics[g["id"]]
        art.set_from_pixbuf(pb)
        initial.hide()
        return False

    def matches(self, child):
        q = self.search.get_text().strip().lower()
        g = getattr(child, "game", None)
        return not q or g is None or q in g["name"].lower() or q in g["badge"].lower()

    def first(self, *_):
        for child in self.flow.get_children():
            if child.get_child_visible() and self.matches(child) and getattr(child, "game", None):
                self.launch(child.game, child.get_child())
                return

    def launch(self, g, btn):
        if self.closing:
            return
        btn.get_style_context().add_class("launching")
        remember(g)
        try:
            subprocess.Popen(g["cmd"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
        GLib.timeout_add(350, self.close)

    def close(self, *_):
        if self.closing:
            return False
        self.closing = True
        self.win.get_style_context().remove_class("shown")
        GLib.timeout_add(260, self.app.quit)
        return False

    def key(self, w, ev):
        if ev.keyval == 0xFF1B:  # Escape
            self.close()
            return True
        return False

    def backdrop_click(self, w, ev):
        self.close()
        return True


def pointer_monitor(display):
    """The monitor the mouse is on (Hyprland knows; GTK on Wayland does not)."""
    try:
        x, y = (int(v) for v in subprocess.run(["hyprctl", "cursorpos"], capture_output=True, text=True,
                                                timeout=2).stdout.split(","))
        return display.get_monitor_at_point(x, y)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def icon_path(name):
    if os.path.isabs(name):
        return name if os.path.isfile(name) else None
    info = Gtk.IconTheme.get_default().lookup_icon(name, 256, 0)
    return info.get_filename() if info else None


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="glade.games", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.panel = None

    def do_activate(self):
        if self.panel is None:
            css = Gtk.CssProvider()
            css.load_from_path(sys.argv[1])
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            self.hold()
            self.panel = Panel(self)
            self.release()
        else:  # clicking Games again closes it
            self.panel.close()


if __name__ == "__main__":
    App().run([sys.argv[0]])
