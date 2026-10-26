"""The Glade — a living pixel-art desktop.

Run:  python glade/main.py            (Ctrl+Q quits)
      python glade/main.py --shots DIR   (renders a picture of every place, then exits)
"""

import glob
import math
import os
import re
import shlex
import subprocess
import sys
import time

import pygame

import art
from apex import Hunt, Listener
from battle import Arena
from art import H, W, mix
from life import swell
from lower import Lower
from scenes import BUILDERS, MAP

HOME = "glade"

# What each object in the glade opens.
APPS = {
    "files": "dolphin",
    "terminal": "kitty",
    "music": "spotify",
    "games": "steam",
    "browser": "flatpak run org.chromium.Chromium",
    "discord": "flatpak run com.discordapp.Discord",
    "code": "code",
}

INK = (34, 24, 58)

CURSOR = art.sprite([
    "11..........",
    "131.........",
    "1331........",
    "13331.......",
    "133331......",
    "1333331.....",
    "13333331....",
    "133333331...",
    "1333333331..",
    "1333331111..",
    "1331331.....",
    "131.1331....",
    "11..1331....",
    ".....111....",
], {"1": INK, "3": (255, 250, 240)})


# --- the little pictures of each app, 16 x 14 -------------------------------------------

def _icon(fn):
    s = pygame.Surface((16, 14), pygame.SRCALPHA)
    fn(s)
    return s


def _files(s):
    o, back, front, hi = (150, 90, 50), (255, 214, 120), (255, 192, 86), (255, 238, 176)
    pygame.draw.rect(s, o, (0, 1, 7, 4))
    pygame.draw.rect(s, back, (1, 2, 5, 3))
    pygame.draw.rect(s, o, (0, 3, 16, 11))
    pygame.draw.rect(s, back, (1, 4, 14, 2))
    pygame.draw.rect(s, front, (1, 6, 14, 6))
    pygame.draw.line(s, hi, (1, 6), (14, 6))
    pygame.draw.line(s, (220, 146, 66), (1, 12), (14, 12))


def _terminal(s):
    k, bar, scr, g = (40, 32, 70), (120, 108, 180), (26, 22, 50), (150, 255, 180)
    pygame.draw.rect(s, k, (0, 0, 16, 13))
    pygame.draw.rect(s, bar, (1, 1, 14, 2))
    for x, c in ((2, (255, 120, 150)), (4, (255, 220, 110)), (6, (150, 255, 180))):
        s.set_at((x, 1), c)
    pygame.draw.rect(s, scr, (1, 4, 14, 8))
    pygame.draw.lines(s, g, False, [(3, 5), (5, 7), (3, 9)])
    pygame.draw.line(s, g, (7, 10), (11, 10))


def _music(s):
    n, hi = (204, 146, 255), (240, 214, 255)
    pygame.draw.rect(s, n, (5, 0, 10, 2))
    pygame.draw.line(s, n, (5, 0), (5, 10))
    pygame.draw.line(s, n, (14, 0), (14, 9))
    pygame.draw.ellipse(s, n, (1, 9, 6, 5))
    pygame.draw.ellipse(s, n, (10, 8, 6, 5))
    s.set_at((3, 10), hi)
    s.set_at((12, 9), hi)


def _games(s):
    c, d = (124, 150, 240), (80, 96, 190)
    pygame.draw.rect(s, d, (0, 4, 16, 8), border_radius=3)
    pygame.draw.rect(s, c, (0, 3, 16, 8), border_radius=3)
    pygame.draw.rect(s, d, (1, 10, 4, 3), border_radius=1)
    pygame.draw.rect(s, d, (11, 10, 4, 3), border_radius=1)
    w = (255, 255, 255)
    pygame.draw.line(s, w, (2, 7), (6, 7))
    pygame.draw.line(s, w, (4, 5), (4, 9))
    s.set_at((11, 6), (255, 140, 170))
    s.set_at((13, 6), (150, 255, 180))
    s.set_at((12, 5), (255, 220, 110))
    s.set_at((12, 7), (140, 220, 255))
    pygame.draw.line(s, (180, 196, 255), (3, 3), (12, 3))


def _browser(s):
    b, g, line = (96, 176, 255), (130, 230, 150), (200, 230, 255)
    pygame.draw.circle(s, b, (8, 7), 7)
    pygame.draw.polygon(s, g, [(4, 2), (7, 3), (6, 6), (3, 8), (2, 5)])
    pygame.draw.polygon(s, g, [(10, 6), (13, 5), (14, 9), (11, 12), (9, 9)])
    pygame.draw.ellipse(s, line, (5, 0, 7, 15), 1)
    pygame.draw.line(s, line, (1, 7), (15, 7))
    s.set_at((4, 3), (230, 245, 255))


def _discord(s):
    p, w, d = (140, 130, 255), (255, 255, 255), (90, 80, 200)
    pygame.draw.ellipse(s, p, (0, 2, 16, 11))
    pygame.draw.rect(s, p, (2, 1, 3, 3))
    pygame.draw.rect(s, p, (11, 1, 3, 3))
    pygame.draw.rect(s, w, (4, 5, 2, 3))
    pygame.draw.rect(s, w, (10, 5, 2, 3))
    pygame.draw.lines(s, d, False, [(5, 9), (7, 10), (9, 10), (11, 9)])


def _code(s):
    c, hi = (90, 200, 255), (200, 240, 255)
    pygame.draw.lines(s, c, False, [(4, 3), (1, 7), (4, 11)], 2)
    pygame.draw.lines(s, c, False, [(11, 3), (14, 7), (11, 11)], 2)
    pygame.draw.line(s, hi, (9, 1), (7, 12), 2)


ICONS = {}
ICON_PAINTERS = dict(files=_files, terminal=_terminal, music=_music, games=_games, browser=_browser,
                     discord=_discord, code=_code)


def font_path():
    """Departure Mono, the same pixel font as the bar. The package passes it in."""
    path = os.environ.get("GLADE_FONT")
    if path and os.path.exists(path):
        return path
    found = glob.glob("/nix/store/*-departure-mono-*/share/fonts/otf/DepartureMono-Regular.otf")
    return found[0] if found else None


# --- signs: the name of every place you can go and every app you can open -------------------

WOOD = (66, 42, 78)
WOOD_HI = (112, 80, 122)
WOOD_LO = (36, 22, 48)
EDGE = (24, 14, 34)
TEXT = (255, 238, 214)
HOT = (255, 172, 228)
# the glow inside each kind of banner: paths to other places, and apps / files
MIST = dict(go=(110, 255, 180), app=(196, 140, 255), grow=(190, 255, 120))


class Signs:
    """Glowing banners with each target's name (and its picture, for apps). They
    are always shown and never move, so they are easy to click; the banner itself is
    part of what you can click (for a tree squid, all of it). Hovering lights it up."""

    def __init__(self):
        pygame.font.init()
        path = font_path()
        self.font = pygame.font.Font(path, 11) if path else pygame.font.Font(None, 16)
        if not ICONS:
            ICONS.update({k: _icon(f) for k, f in ICON_PAINTERS.items()})

    def chevron(self, direction, color):
        s = pygame.Surface((9, 9), pygame.SRCALPHA)
        dx, dy = direction
        if abs(dx) >= abs(dy):
            pts = [(2, 0), (6, 4), (2, 8)] if dx > 0 else [(6, 0), (2, 4), (6, 8)]
        else:
            pts = [(0, 6), (4, 2), (8, 6)] if dy < 0 else [(0, 2), (4, 6), (8, 2)]
        pygame.draw.lines(s, color, False, pts, 2)
        return s

    def tile(self, spot, hot):
        """The picture a tree squid holds: the app's own icon on a small glowing pad in
        the squid's colour."""
        pic = spot.tile if isinstance(spot.tile, pygame.Surface) else ICONS.get(spot.target)
        tint = spot.squid.color if getattr(spot, "squid", None) else MIST["app"]
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        r = pygame.Rect(1, 1, 22, 22)
        pygame.draw.rect(s, (*mix(tint, EDGE, 0.7), 215 if hot else 185), r, border_radius=5)
        for i in range(r.h - 4):  # lit from above, like the banners
            a = round((80 if hot else 50) * (1 - i / r.h))
            pygame.draw.line(s, (*tint, a), (r.x + 2, r.y + 2 + i), (r.right - 3, r.y + 2 + i))
        pygame.draw.rect(s, (*((255, 255, 255) if hot else mix(tint, (255, 255, 255), 0.4)), 235 if hot else 170),
                         r, 1, border_radius=5)
        if pic is not None:
            s.blit(pic, pic.get_rect(center=r.center))
        return s

    def board(self, spot, direction, hot, label=None):
        """A banner of glowing spirit-cloth, not wood: see-through, softly lit from
        inside, its lower edge frayed into wisps. Paths are a mossy mint green, apps
        and files a soft violet, so the two kinds are easy to tell apart."""
        label = label or spot.label
        tint = MIST.get(spot.kind, MIST["app"])
        text = self.font.render(label, False, (255, 255, 255) if hot else TEXT)
        shade = self.font.render(label, False, mix(tint, EDGE, 0.75))
        tw, th = text.get_size()
        icon = getattr(spot, "icon", None) or (ICONS.get(spot.target) if spot.kind == "app" else None)
        lead = 0
        if icon:
            lead = 20
        elif spot.kind == "go":
            lead = 12
        w, h = tw + lead + 12, max(th, 14) + 8
        top = 3  # room for the motes above the banner
        s = pygame.Surface((w + 4, h + top + 6), pygame.SRCALPHA)
        r = pygame.Rect(2, top, w, h)
        rim = (255, 255, 255) if hot else mix(tint, (255, 255, 255), 0.45)
        pygame.draw.rect(s, (*mix(tint, EDGE, 0.6), 200 if hot else 165), r, border_radius=4)
        cloth = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        for i in range(h):  # brighter at the top, fading into the dark below
            a = round((90 if hot else 60) * (1 - i / h))
            pygame.draw.line(cloth, (*tint, a), (r.x + 2, r.y + i), (r.right - 3, r.y + i))
        # the lower edge frays into little wisps
        for gx in range(r.x + 3, r.right - 3, 5):
            ln = 2 + (gx * 7) % 4
            for dy in range(ln):
                cloth.set_at((gx, r.bottom + dy), (*tint, round(130 * (1 - dy / ln))))
        s.blit(cloth, (0, 0))
        pygame.draw.rect(s, (*rim, 230 if hot else 170), r, 1, border_radius=4)
        x = r.x + 6
        cy = r.centery
        if icon:
            s.blit(icon, (x, cy - 7))
            x += 20
        elif spot.kind == "go":
            s.blit(self.chevron(direction, HOT if hot else TEXT), (x - 1, cy - 4))
            x += 12
        ty = cy - th // 2
        s.blit(shade, (x + 1, ty + 1))
        s.blit(text, (x, ty))
        # a few motes of light caught along the top
        for dx, dy in ((4, -1), (9, -2), (w - 8, -1), (w // 2, -2)):
            s.set_at((r.x + dx, r.y + dy), (255, 255, 255))
        return s

    def prepare(self, spot, w, h):
        """Draw a spot's boards once, place them, and make them clickable."""
        if getattr(spot, "boards", None) is not None:
            return
        if getattr(spot, "tile", None) is not None:  # a tree squid: its picture, its name on hover
            cold, warm = self.tile(spot, False), self.tile(spot, True)
            rect = cold.get_rect(center=spot.sign)
            rect.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
            name = self.board(spot, None, True, spot.full)
            below = name.get_rect(midtop=(rect.centerx, rect.bottom + 1))
            below.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
            spot.boards, spot.namebox = (cold, warm, rect, rect), (name, below)
            spot.hits = [rect.inflate(6, 6), spot.rect]
            return
        direction = go_direction(spot, w, h)
        # a board whose name is cut short shows all of it while you point at it
        full = getattr(spot, "full", None)
        cold, hot = self.board(spot, direction, False), self.board(spot, direction, True, full)
        rect = cold.get_rect(center=spot.sign)
        rect.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
        wide = hot.get_rect(midleft=rect.midleft)
        wide.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
        spot.boards = (cold, hot, rect, wide)
        # paths get a generous margin, so you can click through the places quickly
        spot.hits = [spot.rect.inflate(40, 40) if spot.kind == "go" else spot.rect, rect.inflate(8, 8)]
        if getattr(spot, "squid", None):  # a tree squid's banner is what he clicks, not the squid
            spot.hits = [rect.inflate(8, 8)]

    def draw(self, s, spot, hot, t):
        cold, warm, rect, wide = spot.boards
        if hot:
            art.glow(s, *wide.center, max(wide.w, wide.h) // 2 + 18, (255, 150, 220), 120)
        s.blit(warm if hot else cold, wide if hot else rect)
        if hot and getattr(spot, "namebox", None):
            s.blit(*spot.namebox)


class Popup:
    """The right-click menu: a small glowing banner with one choice on each line. It eases
    in rather than appearing at once, and any click closes it."""

    LINE = 16

    def __init__(self, font, view, at, choices, t):
        self.font, self.view, self.choices, self.t = font, view, choices, t
        w = max(font.size(label)[0] for label, _ in choices) + 16
        self.rect = pygame.Rect(round(at[0]) + 4, round(at[1]) + 4, w, self.LINE * len(choices) + 6)
        self.rect.clamp_ip(pygame.Rect(2, 2, view.w - 4, view.h - 4))

    def at(self, m):
        if not m or not self.rect.collidepoint(m):
            return None
        i = int((m[1] - self.rect.y - 3) // self.LINE)
        return i if 0 <= i < len(self.choices) else None

    def draw(self, s, m, t):
        f = max(0.0, min(1.0, (t - self.t - 0.05) / 0.22))
        k = f * f * (3 - 2 * f)
        if k <= 0:
            return
        r = self.rect
        tint = MIST["app"]
        surf = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*mix(tint, EDGE, 0.7), 235), surf.get_rect(), border_radius=4)
        pick = self.at(m)
        for i, (label, _) in enumerate(self.choices):
            y = 3 + i * self.LINE
            if i == pick:
                pygame.draw.rect(surf, (*mix(tint, HOT, 0.5), 120), (2, y, r.w - 4, self.LINE), border_radius=3)
            text = self.font.render(label, False, (255, 255, 255) if i == pick else TEXT)
            surf.blit(text, (8, y + (self.LINE - text.get_height()) // 2))
        pygame.draw.rect(surf, (*mix(tint, (255, 255, 255), 0.45), 220), surf.get_rect(), 1, border_radius=4)
        surf.set_alpha(round(255 * k))
        s.blit(surf, r)


class Minimap:
    """A little carved board in the corner with every place laid out the way the paths
    run (scenes.MAP): the place you are in glows, and its name is written underneath.
    Pointing at another place shows its name; clicking it goes there."""

    NAMES = dict(glade="The Glade", waterfall="The Waterfall", river="The River", forest="The Forest",
                 rocks="The Mossy Rocks")
    COLORS = dict(glade=(255, 150, 214), waterfall=(140, 226, 255), river=(110, 170, 255),
                  forest=(160, 236, 140), rocks=(196, 160, 255))
    CELL = 22  # canvas pixels between neighbouring places

    def __init__(self, font):
        self.font = font
        xs = [x for x, _ in MAP.values()]
        ys = [y for _, y in MAP.values()]
        self.x0, self.y0 = min(xs), min(ys)
        cols, rows = max(xs) - self.x0 + 1, max(ys) - self.y0 + 1
        name_w = max(font.size(n)[0] for n in self.NAMES.values())
        self.w = max(cols * self.CELL + 16, name_w + 16)
        self.map_h = rows * self.CELL + 6
        self.h = self.map_h + font.get_height() + 10
        self.cache = {}
        self.rect = None

    def place(self, view):
        """Bottom-right of the view."""
        self.rect = pygame.Rect(0, 0, self.w + 4, self.h + 7)
        self.rect.bottomright = (view.w - 6, view.h - 30)
        return self.rect

    def node(self, key):
        """Centre of a place's stone, in board coordinates."""
        gx, gy = MAP[key]
        cols = max(x for x, _ in MAP.values()) - self.x0 + 1
        left = 2 + (self.w - cols * self.CELL) // 2
        return (left + (gx - self.x0) * self.CELL + self.CELL // 2, 4 + 3 + (gy - self.y0) * self.CELL + self.CELL // 2)

    def at(self, m):
        """The place under the pointer `m` (canvas coordinates), or None."""
        if self.rect is None or m is None or not self.rect.collidepoint(m):
            return None
        bx, by = m[0] - self.rect.x, m[1] - self.rect.y
        for key in MAP:
            nx, ny = self.node(key)
            if abs(bx - nx) <= self.CELL // 2 and abs(by - ny) <= self.CELL // 2:
                return key
        return None

    def board(self, here, pointed):
        key = (here, pointed)
        if key in self.cache:
            return self.cache[key]
        s = pygame.Surface((self.w + 4, self.h + 7), pygame.SRCALPHA)
        r = pygame.Rect(2, 4, self.w, self.h)
        pygame.draw.rect(s, EDGE, r.inflate(2, 2), border_radius=3)
        pygame.draw.rect(s, WOOD, r, border_radius=2)
        pygame.draw.line(s, WOOD_HI, (r.x + 2, r.y), (r.right - 3, r.y))
        pygame.draw.line(s, WOOD_LO, (r.x + 2, r.bottom - 1), (r.right - 3, r.bottom - 1))
        for gx in range(r.x + 4, r.right - 3, 7):  # wood grain
            s.set_at((gx, r.bottom - 5), WOOD_LO)
        # the paths between places: every place is one step from the glade
        trail = (150, 112, 150)
        for k in MAP:
            if k != "glade":
                pygame.draw.line(s, trail, self.node("glade"), self.node(k), 3)
        for k in MAP:
            nx, ny = self.node(k)
            c = self.COLORS[k]
            stone = pygame.Rect(0, 0, 12, 10)
            stone.center = (nx, ny)
            if k == here:
                pygame.draw.rect(s, (255, 255, 255), stone.inflate(4, 4), border_radius=3)
                pygame.draw.rect(s, c, stone, border_radius=2)
                s.set_at((stone.x + 2, stone.y + 2), (255, 255, 255))
            else:
                pygame.draw.rect(s, HOT if k == pointed else EDGE, stone.inflate(2, 2), border_radius=3)
                pygame.draw.rect(s, mix(c, WOOD, 0.55), stone, border_radius=2)
        label = self.NAMES[pointed or here]
        text = self.font.render(label, False, HOT if pointed and pointed != here else TEXT)
        shade = self.font.render(label, False, EDGE)
        tx, ty = r.centerx - text.get_width() // 2, r.y + self.map_h + 2
        s.blit(shade, (tx + 1, ty + 1))
        s.blit(text, (tx, ty))
        moss = (150, 255, 200)  # a tuft of glowing moss on the top-left corner
        for dx, dy in ((0, 0), (1, -1), (2, -1), (3, 0), (4, -1), (5, 0), (2, -2), (6, 0)):
            s.set_at((r.x + 3 + dx, r.y + dy), moss if dy < 0 else (90, 190, 150))
        self.cache[key] = s
        return s

    def draw(self, s, view, here, pointed, t):
        rect = self.place(view)
        s.blit(self.board(here, pointed), rect)
        # you-are-here: a soft glow breathing slowly over the place you are in
        nx, ny = self.node(here)
        k = 0.5 + 0.5 * math.sin(t * 1.8)
        art.glow(s, rect.x + nx, rect.y + ny, 11, self.COLORS[here], int(50 + 50 * k) // 10 * 10)


def sparkle(s, x, y, t, color=(255, 255, 240)):
    """Twinkling little stars circling a spot you are pointing at."""
    for i in range(6):
        a = t * 1.6 + i / 6 * math.tau
        px, py = x + math.cos(a) * 20, y + math.sin(a) * 10 - 4
        tw = 0.5 + 0.5 * math.sin(t * 6 + i * 1.7)
        art.glow(s, px, py, 5, color, int(80 * tw) // 10 * 10)
        s.set_at((int(px), int(py)), color)


def go_direction(spot, w, h):
    if spot.direction:
        return spot.direction
    cx, cy = spot.mark
    if cx < 120:
        return (-1, 0)
    if cx > w - 120:
        return (1, 0)
    return (0, -1) if cy < h * 0.75 else (0, 1)


def monitors():
    """Every lit monitor as pygame.Rects, the main one (top-left of the X screen) first."""
    found = []
    try:
        out = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, timeout=3).stdout
        for m in re.finditer(r" connected (?:primary )?(\d+)x(\d+)\+(\d+)\+(\d+)", out):
            w, h, x, y = map(int, m.groups())
            found.append(pygame.Rect(x, y, w, h))
    except (OSError, subprocess.SubprocessError):
        pass
    if not found:
        found = [pygame.Rect(0, 0, 1920, 1080)]
    found.sort(key=lambda r: (r.topleft != (0, 0), r.y, r.x))
    return found


def fit(mon, w, h):
    """The biggest whole-number scale-up of a w x h canvas that fits the monitor, centred."""
    scale = max(1, min(mon.w // w, mon.h // h))
    r = pygame.Rect(0, 0, w * scale, h * scale)
    r.center = mon.center
    return r


def keep_at_back(area):
    """Ask the window manager to treat us as the desktop: exactly over `area`, behind
    every window, on every workspace, and not in the taskbar or alt-tab. (XFCE ignores
    the position we ask for when the window opens, so it is moved explicitly.)"""
    try:
        wid = pygame.display.get_wm_info().get("window")
        if not wid:
            return
        geom = f"0,{area.x},{area.y},{area.w},{area.h}"
        for _ in range(3):
            pygame.event.pump()
            subprocess.run(["wmctrl", "-i", "-r", str(wid), "-e", geom], timeout=3)
            time.sleep(0.2)
        subprocess.run(["wmctrl", "-i", "-r", str(wid), "-b", "add,below,sticky"], timeout=3)
        subprocess.run(["wmctrl", "-i", "-r", str(wid), "-b", "add,skip_taskbar,skip_pager"], timeout=3)
    except (OSError, subprocess.SubprocessError):
        pass


def launch(key, args=None):
    """Open an app by its key in APPS, or run `args` (a fruit's own command)."""
    cmd = APPS.get(key)
    if not cmd and not args:
        return
    try:
        subprocess.Popen(args or shlex.split(cmd), start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


class View:
    """One monitor's worth of glade: a small canvas, and where it is shown on screen."""

    def __init__(self, rect, w, h):
        self.rect, self.w, self.h = rect, w, h
        self.canvas = art.solid()  # always full size so every brush works; only w x h is shown
        # Where the pointer is, in this view's own surface pixels. The X11 window reads
        # it from pygame; under Wayland each monitor is its own surface and its backend
        # sets this (None when the pointer is elsewhere).
        self.external = False
        self.pointer = None

    def shown(self):
        """The part of the canvas on screen: all of it (the picture never zooms)."""
        return pygame.Rect(0, 0, self.w, self.h)

    def mouse(self):
        if self.external:
            if self.pointer is None:
                return None
            mx, my = self.pointer
        else:
            mx, my = pygame.mouse.get_pos()
        if not self.rect.collidepoint(mx, my):
            return None
        r = self.shown()
        return r.x + (mx - self.rect.x) * r.w / self.rect.w, r.y + (my - self.rect.y) * r.h / self.rect.h

    def hovered(self, spots):
        m = self.mouse()
        if m:
            for sp in spots:
                if sp.hit(m):
                    return sp
        return None

    def present(self, screen):
        shown = self.canvas.subsurface(self.shown())
        screen.blit(pygame.transform.scale(shown, self.rect.size), self.rect.topleft)


class Glade:
    def __init__(self, screen, rect, lower=None):
        """`rect`: where the glade goes on screen. `lower`: a second monitor, if any —
        it shows the ground in front of you, below whichever place you are in."""
        self.screen = screen
        self.top = View(rect, W, H)
        self.bottom = None
        if lower is not None:
            scale = rect.w // W
            pw, ph = min(W, lower.w // scale), min(H, lower.h // scale)
            self.bottom = View(fit(lower, pw, ph), pw, ph)
        self.scenes, self.lowers = {}, {}
        self.signs = Signs()
        self.minimap = Minimap(self.signs.font)
        self.here = self.scene(HOME)
        self.fade, self.fade_to = 0.0, None
        self.flash = None
        self.t0 = time.monotonic()
        self.history = []  # the places you came from, for Backspace
        self.picked = None  # (view, spot) chosen with Tab
        self.keys_on = False  # the keyboard is steering the glade (the dock shows the hint)
        self.on_launch = None  # called whenever an app is opened
        # the easter egg (apex.py): click the moon, type the word
        self.listener = Listener()
        self.on_listen = None  # called when the moon starts listening for typing
        self.on_heard = None   # ... and when it has heard the word
        self.hunt = None
        self.arena = None  # the battle (battle.py): click the moon, type "battle"
        self.held = None  # (view, content, spot, where it was pressed): a squid being dragged
        self.popup = None  # the right-click menu, while it is open

    def scene(self, key):
        if key not in self.scenes:
            self.scenes[key] = BUILDERS[key]()
        return self.scenes[key]

    def lower(self):
        key = self.here.key
        if key not in self.lowers:
            self.lowers[key] = Lower(self.here, self.bottom.w, self.bottom.h)
        return self.lowers[key]

    def map_view(self):
        """The minimap sits on the lower screen, which has room in its corner."""
        return self.bottom or self.top

    def views(self):
        yield self.top, self.here
        if self.bottom:
            yield self.bottom, self.lower()

    def warm(self):
        """Build the next place nobody has visited yet, so going there is instant."""
        for key in BUILDERS:
            if key not in self.scenes:
                self.scene(key)
                return True
            if self.bottom and key not in self.lowers:
                self.lowers[key] = Lower(self.scenes[key], self.bottom.w, self.bottom.h)
                return True
        return False

    def go(self, key, remember=True):
        if self.fade_to or key == self.here.key:
            return
        self.popup = None
        if remember:
            self.history.append(self.here.key)
        self.fade_to, self.picked = key, None

    def activate(self, view, content, sp, t):
        if sp.kind == "grow":  # the seed sign: grow another tree for the squid
            content.colony.grow(t)
            return
        if sp.kind == "go":
            self.go(sp.target)
            return
        launch(sp.target, getattr(sp, "cmd", None))
        self.flash = (view, sp, t)
        colony = getattr(content, "colony", None)
        if colony and getattr(sp, "squid", None):
            colony.clicked(sp.squid, t)  # it counts towards the squid's spot
        if self.on_launch:
            self.on_launch()

    def click(self, t):
        if self.fade_to:
            return
        if self.popup is not None:  # a click chooses from the open menu, or just closes it
            pop, self.popup = self.popup, None
            i = pop.at(pop.view.mouse())
            if i is not None:
                pop.choices[i][1](t)
            return
        if self.arena is not None and self.arena.click(self, t):
            return
        for view, content in self.views():
            m = view.mouse()
            if not m:
                continue
            for sp in content.spots:
                self.signs.prepare(sp, view.w, view.h)
            if view is self.map_view():
                place = self.minimap.at(m)
                if place is not None:
                    self.go(place)
                    return
                if self.minimap.rect and self.minimap.rect.collidepoint(m):
                    return
            sp = view.hovered(content.spots)
            moon = getattr(content, "moon", None)
            if sp is None and moon and math.hypot(m[0] - moon[0], m[1] - moon[1]) < moon[2] + 6:
                self.listener.start(t)  # the moon listens...
                if self.on_listen:
                    self.on_listen()
                return
            if sp is None:
                for c in content.creatures:
                    if not getattr(c, "gone", False) and c.poke(*m, t):
                        return
                for b in content.bugs:
                    b.scatter(*m, t)
            else:
                colony = getattr(content, "colony", None)
                if colony and colony.grab(sp, t):
                    self.held = (view, content, sp, m)  # a click or a drag: the release decides
                else:
                    self.activate(view, content, sp, t)
            return

    def right_click(self, t):
        """Right-click a squid to open or remove it; right-click a tree he grew to take
        it away."""
        self.popup = None
        if self.fade_to:
            return
        for view, content in self.views():
            m = view.mouse()
            colony = getattr(content, "colony", None)
            if not m or colony is None:
                continue
            for sp in content.spots:
                self.signs.prepare(sp, view.w, view.h)
            sp = view.hovered(content.spots)
            choices = []
            if sp is not None and getattr(sp, "squid", None):
                sq = sp.squid
                gone = "Remove (to Trash)" if sq.item.get("path") else "Remove from the trees"
                choices = [("Open", lambda t, v=view, c=content, s=sp: self.activate(v, c, s, t)),
                           (gone, lambda t, sq=sq: colony.remove(sq))]
            elif sp is None:
                tree = colony.tree_at(m)
                if tree is not None:
                    choices = [("Remove this tree", lambda t, g=tree: colony.cut(g, t))]
            if choices:
                self.popup = Popup(self.signs.font, view, m, choices, t)
            return

    def release(self, t):
        """The mouse button comes up. A squid that was barely moved was clicked; one that
        was carried somewhere is put down there."""
        if self.held is None:
            return
        view, content, sp, start = self.held
        self.held = None
        m = view.mouse()
        if m and math.hypot(m[0] - start[0], m[1] - start[1]) > 6:
            content.colony.drop(m)
        else:
            content.colony.dragging = None
            self.activate(view, content, sp, t)

    def typed(self, ch, t):
        """A letter typed while the moon is listening."""
        word = self.listener.key(ch, t)
        if word:
            if self.on_heard:
                self.on_heard()
            if word == "battle":
                if self.arena is None:
                    low = self.lower() if self.bottom else None
                    self.arena = Arena(self.here, low, self.signs.font, t)
                    self.arena.mouse = self.top.mouse
            elif self.hunt is None:
                low = self.lower() if self.bottom else None
                size = (self.bottom.w, self.bottom.h) if self.bottom else (0, 0)
                self.hunt = Hunt(self.here, low, size, t)

    # --- the keyboard ----------------------------------------------------------------
    # Commands: left/right/up/down walk along the path that goes that way; next/prev
    # choose the next board (Tab); open opens the chosen one; home and back go places.
    def key(self, cmd, t):
        if self.fade_to:
            return
        if cmd in ("left", "right", "up", "down"):
            want = dict(left=(-1, 0), right=(1, 0), up=(0, -1), down=(0, 1))[cmd]
            for view, content in self.views():
                for sp in content.spots:
                    if sp.kind == "go" and tuple(go_direction(sp, view.w, view.h)) == want:
                        self.go(sp.target)
                        return
        elif cmd in ("next", "prev"):
            choices = [(view, content, sp) for view, content in self.views()
                       for sp in sorted(content.spots, key=lambda sp: (sp.sign[1] // 48, sp.sign[0]))]
            if not choices:
                return
            now = [c[::2] for c in choices]
            i = now.index(self.picked) if self.picked in now else (-1 if cmd == "next" else 0)
            self.picked = now[(i + (1 if cmd == "next" else -1)) % len(now)]
        elif cmd == "open" and self.picked:
            view, sp = self.picked
            for v, content in self.views():
                if v is view and sp in content.spots:
                    self.activate(view, content, sp, t)
        elif cmd == "home":
            self.go(HOME)
        elif cmd == "back" and self.history:
            self.go(self.history.pop(), remember=False)

    def overlay(self, view, content, t):
        s = view.canvas
        for sp in content.spots:
            self.signs.prepare(sp, view.w, view.h)
        hot = None if self.fade_to or self.popup is not None else view.hovered(content.spots)
        if hot is None and self.picked and self.picked[0] is view and self.picked[1] in content.spots:
            hot = self.picked[1]
        for sp in content.spots:
            if sp is not hot:
                self.signs.draw(s, sp, False, t)
        if hot is not None:  # last, so a long name is drawn over its neighbours
            self.signs.draw(s, hot, True, t)
        if hot is not None and hot.kind == "app":
            sparkle(s, *hot.mark, t)
        if view is self.map_view():
            pointed = None if self.fade_to else self.minimap.at(view.mouse())
            self.minimap.draw(s, view, self.here.key, pointed, t)
        if self.popup is not None and self.popup.view is view:
            self.popup.draw(s, view.mouse(), t)
        if self.flash and self.flash[0] is view:
            # what you opened glows softly for a moment, easing in and out
            a = t - self.flash[2]
            k = swell(a, 0.3, 0.9)
            if k > 0:
                art.glow(s, *self.flash[1].mark, int(24 + 30 * min(1.0, a)), (255, 250, 220), int(110 * k) // 10 * 10)

    def frame(self, dt):
        self.render(dt)
        for view, _ in self.views():
            view.present(self.screen)
            if self.screen.get_masks()[3]:  # composited screen: make sure no pixel is see-through
                self.screen.fill((0, 0, 0, 255), view.rect, special_flags=pygame.BLEND_RGBA_MAX)
        pygame.display.flip()

    def render(self, dt):
        """Advance everything by dt and paint each view's canvas (without showing it)."""
        t = time.monotonic() - self.t0
        # a quick fade, so clicking through the places never feels slow
        if self.fade_to:
            self.fade += dt / 0.15
            if self.fade >= 1:
                self.here = self.scene(self.fade_to)
                self.fade_to = None
        elif self.fade > 0:
            self.fade = max(0.0, self.fade - dt / 0.15)
        elif t > 2:
            self.warm()
        self.here.update(dt)
        if self.hunt is not None:
            if self.hunt.done or self.hunt.scene is not self.here:
                self.hunt.finish()  # finished, or he went elsewhere: everyone is back
                self.hunt = None
            else:
                self.hunt.update(dt, t)
        if self.arena is not None:
            if self.arena.done or self.arena.scene is not self.here:
                self.arena.finish()  # closed, or he walked somewhere else: everyone goes home
                self.arena = None
            else:
                self.arena.update(dt, t)
        if self.held is not None:
            view, content, _, start = self.held
            if content is not self.here:
                content.colony.dragging, self.held = None, None
            else:
                m = view.mouse()
                if m and math.hypot(m[0] - start[0], m[1] - start[1]) > 6:
                    content.colony.drag(m)  # the held squid follows the pointer
        for view, content in self.views():
            if content is not self.here:
                content.update(dt, t)
            content.draw(view.canvas, t)
            if view is self.top:
                self.listener.draw_moon(view.canvas, getattr(content, "moon", None), t)
            if self.hunt is not None:
                self.hunt.draw(view.canvas, view is self.bottom, t)
            self.overlay(view, content, t)
            if self.arena is not None:
                self.arena.draw(view.canvas, view is self.bottom, t)
            if self.fade > 0:
                veil = art.solid()
                veil.fill(INK)
                veil.set_alpha(int(255 * min(1.0, self.fade)))
                view.canvas.blit(veil, (0, 0))
            m = view.mouse()
            if m:
                view.canvas.blit(CURSOR, (int(m[0]), int(m[1])))


KEYS = {pygame.K_LEFT: "left", pygame.K_a: "left", pygame.K_RIGHT: "right", pygame.K_d: "right",
        pygame.K_UP: "up", pygame.K_w: "up", pygame.K_DOWN: "down", pygame.K_s: "down",
        pygame.K_TAB: "next", pygame.K_RETURN: "open", pygame.K_KP_ENTER: "open", pygame.K_SPACE: "open",
        pygame.K_HOME: "home", pygame.K_h: "home", pygame.K_BACKSPACE: "back"}


def shots(out):
    """A picture of every place with its lower screen under it, laid out as on his desk
    (the lower monitor is 80 canvas pixels in from the left), plus timings."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((W, H))
    os.makedirs(out, exist_ok=True)
    lw, lh, lx = 800, 450, 80
    signs = Signs()
    minimap = Minimap(signs.font)
    only = os.environ.get("GLADE_ONLY")
    for key, build in BUILDERS.items():
        if only and key != only:
            continue
        t0 = time.monotonic()
        sc = build()
        low = Lower(sc, lw, lh)
        built = time.monotonic() - t0
        top, bot = art.solid(), art.solid()
        for i in range(40):
            sc.update(0.1)
            low.update(0.1, i / 10)
            sc.draw(top, i / 10)
            low.draw(bot, i / 10)
        t0 = time.monotonic()
        for i in range(30):
            sc.draw(top, 4.0 + i / 30)
            low.draw(bot, 4.0 + i / 30)
        per = (time.monotonic() - t0) / 30
        for content, s, w, h in ((sc, top, W, H), (low, bot, lw, lh)):
            for spot in content.spots:
                signs.prepare(spot, w, h)
                signs.draw(s, spot, False, 5.0)
        minimap.draw(bot, type("V", (), dict(w=lw, h=lh))(), key, None, 5.0)
        sheet = pygame.Surface((W, H + lh))
        sheet.fill((20, 16, 34))
        sheet.blit(top, (0, 0))
        sheet.blit(bot, (lx, H), (0, 0, lw, lh))
        pygame.image.save(sheet, os.path.join(out, f"{key}.png"))
        print(f"{key}: built in {built:.2f}s, {per * 1000:.1f} ms/frame")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--shots":
        return shots(sys.argv[2])
    if os.environ.get("WAYLAND_DISPLAY") and "--x11" not in sys.argv:
        import wayland  # Hyprland: the glade as the desktop layer, one surface per monitor
        return wayland.run()
    pygame.init()
    mons = monitors()
    # One window covering every monitor; the bits of it that no monitor shows are unseen.
    area = mons[0].unionall(mons[1:]) if len(mons) > 1 else mons[0]
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{area.x},{area.y}"
    pygame.display.set_caption("The Glade")
    screen = pygame.display.set_mode(area.size, pygame.NOFRAME)
    pygame.mouse.set_visible(False)
    keep_at_back(area)
    mons = [r.move(-area.x, -area.y) for r in mons]
    screen.fill(INK)
    glade = Glade(screen, fit(mons[0], W, H), mons[1] if len(mons) > 1 else None)
    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(30) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_q and e.mod & pygame.KMOD_CTRL:
                return
            if e.type == pygame.KEYDOWN and glade.listener.listening(time.monotonic() - glade.t0) \
                    and e.unicode.isalpha():
                glade.typed(e.unicode, time.monotonic() - glade.t0)
            elif e.type == pygame.KEYDOWN and e.key in KEYS:
                cmd = KEYS[e.key]
                if cmd == "next" and e.mod & pygame.KMOD_SHIFT:
                    cmd = "prev"
                glade.key(cmd, time.monotonic() - glade.t0)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                glade.click(time.monotonic() - glade.t0)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                glade.right_click(time.monotonic() - glade.t0)
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                glade.release(time.monotonic() - glade.t0)
        glade.frame(min(dt, 0.1))


if __name__ == "__main__":
    main()
