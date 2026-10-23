"""The fruit in the big blossom tree: each one is something he used lately.

The lower canopy holds the apps and files he used most recently (violet plums are
apps, amber peaches are files); the crown holds golden fruit for anything new in his
Downloads. Each has its own fixed name board and opens what it stands for. Now and then
a little squid swims over and nibbles one.

Where the lists come from:
- files: ~/.local/share/recently-used.xbel, which file pickers and most apps write;
- apps: under Hyprland, the glade notes every app whose window he is using (it looks
  every few seconds) in ~/.local/state/glade/apps.json, matched to its .desktop entry;
- downloads: ~/Downloads, anything from the last week.
They are gathered on a background thread, so looking never stalls a frame.
"""

import glob
import json
import math
import os
import shlex
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

import pygame

from art import glow, mix
from life import Squid, q

HOME = os.path.expanduser("~")
XBEL = os.path.join(HOME, ".local/share/recently-used.xbel")
DOWNLOADS = os.path.join(HOME, "Downloads")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local/state"), "glade", "apps.json")

RECENT, NEW = 6, 3  # how many fruit of each
NEW_FOR = 7 * 86400  # a download counts as new for a week
LOOK_EVERY = 5  # seconds between looks

KINDS = {  # fruit colour, its shine, the dark side
    "app": ((186, 140, 255), (236, 214, 255), (92, 60, 160)),
    "file": ((255, 176, 110), (255, 230, 190), (170, 92, 70)),
    "new": ((255, 226, 110), (255, 250, 210), (180, 130, 50)),
}

# The fixed places in the canopy: (where its board hangs, where the fruit hangs).
XS = (644, 744, 844)
NEW_SLOTS = [((x, 92), (x, 116)) for x in XS]
RECENT_SLOTS = [((x, y), (x, y + 24)) for y in (148, 204) for x in XS]


# --- what he used ---------------------------------------------------------------------

def desktop_entries():
    """Every installed app's .desktop entry, found by the names a window might give."""
    dirs = [os.path.join(HOME, ".local/share")] + (os.environ.get("XDG_DATA_DIRS") or "/run/current-system/sw/share").split(":")
    found = {}
    for d in dirs:
        for path in glob.glob(os.path.join(d, "applications", "*.desktop")):
            app_id = os.path.basename(path)[:-8]
            e = dict(id=app_id, path=path)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    section = None
                    for line in f:
                        line = line.strip()
                        if line.startswith("["):
                            section = line
                        elif section == "[Desktop Entry]" and "=" in line:
                            k, v = line.split("=", 1)
                            if k in ("Name", "Exec", "StartupWMClass", "NoDisplay"):
                                e.setdefault(k, v)
            except OSError:
                continue
            if "Exec" not in e or "Name" not in e:
                continue
            for key in (e.get("StartupWMClass"), app_id, app_id.rsplit(".", 1)[-1]):
                if key and (key.lower() not in found or found[key.lower()].get("NoDisplay") == "true"):
                    found[key.lower()] = e
    return found


def recent_files():
    try:
        root = ET.parse(XBEL).getroot()
    except (OSError, ET.ParseError):
        return []
    out = []
    for b in root.iter("bookmark"):
        url = urlparse(b.get("href", ""))
        if url.scheme != "file":
            continue
        path = unquote(url.path)
        if not os.path.isfile(path):
            continue
        when = max(b.get("modified", ""), b.get("visited", ""))
        try:
            ts = time.mktime(time.strptime(when[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
        except ValueError:
            continue
        out.append(dict(kind="file", name=os.path.splitext(os.path.basename(path))[0], when=ts,
                        cmd=["xdg-open", path]))
    return out


def new_downloads(now):
    out = []
    try:
        names = os.listdir(DOWNLOADS)
    except OSError:
        return []
    for n in names:
        path = os.path.join(DOWNLOADS, n)
        if n.startswith(".") or n.endswith((".part", ".crdownload", ".tmp")):
            continue
        try:
            ts = os.path.getmtime(path)
        except OSError:
            continue
        if now - ts < NEW_FOR:
            out.append(dict(kind="new", name=os.path.splitext(n)[0] if os.path.isfile(path) else n, when=ts,
                            cmd=["xdg-open", path]))
    return sorted(out, key=lambda e: -e["when"])[:NEW]


def app_command(e):
    """The entry's Exec line, without the %f/%u/... placeholders (and flatpak's @@ ones)."""
    return [a for a in shlex.split(e["Exec"]) if not (len(a) == 2 and a[0] == "%") and not a.startswith("@@")]


class Watcher:
    """Looks at what he uses, every few seconds, on its own thread."""

    def __init__(self):
        self.entries = desktop_entries()
        self.seen = {}  # .desktop id -> when he last used it
        try:
            with open(STATE) as f:
                self.seen = {k: float(v) for k, v in json.load(f).items()}
        except (OSError, ValueError, AttributeError):
            pass
        self.result = self.gather()
        threading.Thread(target=self.run, daemon=True).start()

    def note_app(self):
        """Remember the app whose window he is in right now (Hyprland only)."""
        if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return
        try:
            out = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, timeout=3).stdout
            cls = (json.loads(out) or {}).get("class", "")
        except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
            return
        e = self.entries.get(cls.lower()) if cls else None
        if e is None or e["id"] == "glade":
            return
        self.seen[e["id"]] = time.time()
        try:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE + ".tmp", "w") as f:
                json.dump(self.seen, f)
            os.replace(STATE + ".tmp", STATE)
        except OSError:
            pass

    def gather(self):
        now = time.time()
        byid = {e["id"]: e for e in self.entries.values()}
        apps = [dict(kind="app", name=byid[i]["Name"], when=w, cmd=app_command(byid[i]))
                for i, w in self.seen.items() if i in byid]
        new = new_downloads(now)
        shown = {tuple(n["cmd"]) for n in new}
        recent = sorted((r for r in apps + recent_files() if tuple(r["cmd"]) not in shown), key=lambda e: -e["when"])
        return recent[:RECENT], new

    def run(self):
        while True:
            time.sleep(LOOK_EVERY)
            try:
                self.note_app()
                self.result = self.gather()
            except Exception:  # never let a bad file kill the looking
                pass


# --- the fruit ------------------------------------------------------------------------

def short(name, n=9):
    return name if len(name) <= n else name[:n - 1].rstrip() + "…"


def fruit_icon(kind):
    """The little fruit on its board, 16 x 14."""
    c, hi, lo = KINDS[kind]
    s = pygame.Surface((16, 14), pygame.SRCALPHA)
    pygame.draw.line(s, (90, 60, 70), (8, 0), (8, 3))
    pygame.draw.ellipse(s, (110, 220, 160), (9, 0, 5, 3))  # a leaf
    pygame.draw.circle(s, lo, (8, 8), 5)
    pygame.draw.circle(s, c, (7, 8), 4)
    s.set_at((6, 6), hi)
    s.set_at((5, 7), hi)
    return s


class Orchard:
    """Draws the fruit and keeps the scene's clickable spots in step with them."""

    def __init__(self, scene, spot_type):
        self.scene, self.Spot = scene, spot_type
        self.base = list(scene.spots)
        self.watch = Watcher()
        self.shown = None
        self.fruit = []  # (x, y, kind, phase)
        self.bites = {}  # fruit index -> when it was last bitten
        self.icons = {k: fruit_icon(k) for k in KINDS}

    def refresh(self):
        if not self.base:  # the scene's own spots are set after the orchard is made
            self.base = list(self.scene.spots)
        result = self.watch.result
        if result == self.shown:
            return
        self.shown = result
        recent, new = result
        self.fruit, spots = [], []
        crown = [NEW_SLOTS[1]] if len(new) == 1 else NEW_SLOTS[::2] if len(new) == 2 else NEW_SLOTS
        for (sign, (x, y)), e in list(zip(crown, new)) + list(zip(RECENT_SLOTS, recent)):
            sp = self.Spot("app", (x - 10, y - 12, 20, 24), short(e["name"]), None, (x, y + 2), sign=sign)
            sp.cmd, sp.icon = e["cmd"], self.icons[e["kind"]]
            spots.append(sp)
            self.fruit.append((x, y, e["kind"], (x * 7 + y) % 10 / 10 * math.tau))
        self.bites = {}
        self.scene.spots[:] = self.base + spots

    def where(self, i, t):
        x, y, _, ph = self.fruit[i]
        sway = math.sin(t * 0.9 + ph) * 1.2
        bitten = t - self.bites.get(i, -99)
        if bitten < 3:
            sway += math.sin(bitten * 18) * 2 * (1 - bitten / 3)
        return x + sway, y + abs(sway) * 0.3

    def draw(self, s, t):
        self.refresh()
        for i, (x, y, kind, _) in enumerate(self.fruit):
            c, hi, lo = KINDS[kind]
            fx, fy = self.where(i, t)
            pygame.draw.line(s, (90, 56, 76), (x, y - 11), (round(fx), round(fy) - 5))
            pygame.draw.ellipse(s, (96, 200, 150), (x + 1, y - 11, 6, 3))  # its leaf
            fx, fy = round(fx), round(fy)
            pygame.draw.circle(s, lo, (fx, fy), 6)
            pygame.draw.circle(s, c, (fx - 1, fy - 1), 5)
            pygame.draw.line(s, hi, (fx - 3, fy - 3), (fx - 2, fy - 4))
            s.set_at((fx - 4, fy - 2), hi)
            if t - self.bites.get(i, -99) < 40:  # a bite out of the side, until it heals
                pygame.draw.circle(s, (40, 24, 50), (fx + 5, fy - 2), 3)
                pygame.draw.circle(s, hi, (fx + 4, fy - 1), 1)

    def light(self, lm, t):
        for i, (_, _, kind, _) in enumerate(self.fruit):
            glow(lm, *self.where(i, t), 16, KINDS[kind][0], 48)

    def shine(self, s, t):
        for i, (_, _, kind, ph) in enumerate(self.fruit):
            fx, fy = self.where(i, t)
            glow(s, fx, fy, 11, KINDS[kind][0], q(48 + 12 * math.sin(t * 1.3 + ph)))
            if kind == "new":  # new fruit twinkle
                a = t * 2 + ph
                px, py = fx + math.cos(a) * 8, fy + math.sin(a) * 5
                glow(s, px, py, 3, (255, 255, 230), q(60 + 40 * math.sin(t * 5 + ph)))
            bitten = t - self.bites.get(i, -99)
            if bitten < 1.6:  # crumbs falling from the bite
                for k in range(4):
                    cy = fy + bitten * (14 + k * 6) + bitten * bitten * 12
                    s.set_at((round(fx + 3 + (k - 1.5) * 2), round(cy)), KINDS[kind][1])

    def bite(self, i, t):
        if i < len(self.fruit):
            self.bites[i] = t


class Nibbler(Squid):
    """A small squid that swims about the tree and, every so often, goes over to a
    piece of fruit and nibbles at it."""

    def __init__(self, rng, orchard, region, color):
        self.orchard = orchard
        self.meal, self.eating, self.next_meal = None, None, rng.uniform(8, 20)
        super().__init__(rng, region, color, size=1.0)

    def draw(self, s, t):
        o = self.orchard
        dt = max(0.0, min(0.1, t - getattr(self, "_t", t)))
        if self.meal is not None and self.meal >= len(o.fruit):
            self.meal, self.eating = None, None
        if self.meal is None and t > self.next_meal and o.fruit:
            self.meal = self.rng.randrange(len(o.fruit))
        if self.meal is not None:
            fx, fy = o.where(self.meal, t)
            self.target = (fx, fy + 10)
        super().draw(s, t)
        if self.meal is None:
            return
        # squid only ever swim upward, so it drifts over to its meal (and down, if need
        # be), settling just under the fruit with its arms around it
        fx, fy = o.where(self.meal, t)
        k = min(1.0, dt * (6 if self.eating is not None else 1.2))
        self.x += (fx - self.x) * k
        self.y += (fy + 9 - self.y) * k
        self.vx *= 1 - k
        self.vy *= 1 - k
        if self.eating is None and math.hypot(self.x - fx, self.y - fy - 9) < 6:
            self.eating = t
        if self.eating is not None:
            if t - o.bites.get(self.meal, -99) > 1.0:
                o.bite(self.meal, t)  # a nibble every second
            if t - self.eating > 3.2:
                self.meal, self.eating = None, None
                self.next_meal = t + self.rng.uniform(25, 60)
                self.target = self.pick()
