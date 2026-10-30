"""The Glade — a living pixel-art desktop, and the game that lives in it (world.py).

Run:  python glade/main.py            the desktop (desktop.py; Ctrl+Q quits)
      python glade/main.py --game     the game (game.py), on its own
      python glade/main.py --shots DIR   (renders a picture of every place, then exits)

This module is what the two share: the name boards, the views, and main.Glade.
"""

import glob
import math
import os
import re
import shlex
import subprocess
import sys
import threading
import time

import pygame

import art
from battle import Perched, animal_under, cloth
import storm
import hiding
import badges
import loading
import resume
from art import H, W, mix
from life import swell
from lower import Lower
from claude_panel import Panel
from scenes import BUILDERS

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
MIST = dict(go=(110, 255, 180), app=(196, 140, 255), grow=(190, 255, 120), tower=(255, 150, 214), boxes=(255, 214, 120))


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
    """What the desktop and the game share (world.py): the views, the places and their lower
    screens, the name boards and opening apps, the animals coming and going, Thunderstorm,
    hiding for games and Hide animals, the squid trees, the Claude panel and updates.
    desktop.Desktop and game.Game each build on this through the hooks at the end; nothing
    here plays (no battles, cards, Dex, boards, minimap or far places)."""

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
        self.building = threading.Lock()  # one place at a time: builds share some drawing state (art)
        self.signs = Signs()
        self.panel = Panel()  # the Claude panel: a minimised way of talking to Claude (claude_panel.py)
        self.show_panel = True  # (not in the game's window: that is for any computer, not his desktop)
        self.here = self.scene(HOME)
        self.fade, self.fade_to = 0.0, None
        self.flash = None
        self.t0 = time.monotonic()
        self.history = []  # the places you came from, for Backspace
        self.picked = None  # (view, spot) chosen with Tab
        self.keys_on = False  # the keyboard is steering the glade (the dock shows the hint)
        self.on_launch = None  # called whenever an app is opened
        self.on_listen = None  # called when the moon starts listening for typing (the game's)
        self.on_heard = None   # ... and when it has heard the word
        self.held = None  # (view, content, spot, where it was pressed): a squid being dragged
        self.popup = None  # the right-click menu, while it is open
        self.storm = None  # a thunderstorm (storm.py): the animals take turns
        self.storm_scratch = art.solid()
        self.lifespans = storm.Lifespans()  # each animal is out a while, then a new one takes its place
        self.hiding = None  # the animals hiding while he plays a game (hiding.py)
        self.hide = hiding.load_hide()  # his "Hide animals" switch
        self.covered = set()  # the views a full-screen window is hiding: not drawn (set by wayland.py)
        self.game_since = None  # when a full-screen window last came up
        self.updater = resume.Updater()  # after a rebuild: Thunderstorm switches to the new glade
        if self.bottom:
            self.lower()

    def set_covered(self, views):
        """Which screens a full-screen window (a game) now fills: those are not drawn."""
        views = set(views)
        if views and not self.covered:
            self.game_since = self.now()
        self.covered = views

    def hide_for_games(self, t):
        """A game full screen for half a minute, or his "Hide animals" switch: everyone hides; when
        he is back (and the switch is off), out they come."""
        h = self.hiding
        if h is not None:
            if h.scene is not self.here or self.storm is not None:
                h.finish()  # he went elsewhere, or a storm came: they are simply out again
                self.hiding = None
            elif h.done:
                self.hiding = None
            else:
                if not self.covered and not self.hide:
                    h.come_back(t)
                h.update(t)
        elif self.storm is None and not self.fade_to and (self.hide or self.covered
                and self.game_since is not None and t - self.game_since >= hiding.WAIT):
            self.lifespans.settle()
            self.hiding = hiding.Hiding(self, t, self.lifespans.keep(self))

    def now(self):
        """The glade's own clock: seconds since it started."""
        return time.monotonic() - self.t0

    def scene(self, key):
        if key not in self.scenes:
            with loading.Rush(), self.building:
                if key not in self.scenes:
                    self.scenes[key] = self.home_only(BUILDERS[key]())
        return self.scenes[key]

    def lower(self):
        key = self.here.key
        if key not in self.lowers:
            with loading.Rush(), self.building:
                if key not in self.lowers:
                    self.lowers[key] = self.home_only(Lower(self.here, self.bottom.w, self.bottom.h))
        return self.lowers[key]

    def map_view(self):
        """The corner boards (and the game's minimap) sit on the lower screen, which has room."""
        return self.bottom or self.top

    def views(self):
        yield self.top, self.here
        if self.bottom:
            yield self.bottom, self.lower()

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
        if self.activate_play(view, content, sp, t):
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

    def scroll(self, dy):
        """The mouse wheel: only the Claude panel's cards scroll (his ask, 2026-10-30)."""
        panel_view = self.bottom or self.top
        if self.show_panel:
            self.panel.scroll(panel_view, panel_view.mouse(), dy)

    def click(self, t):
        panel_view = self.bottom or self.top
        if self.show_panel and self.panel.click(panel_view, panel_view.mouse()):
            return
        if self.fade_to:
            return
        view = self.map_view()  # the boards in the corner
        m = view.mouse() if view is not None else None
        if m and self.corner_free():
            if hiding.keep_rect(view).collidepoint(m):
                self.hide = not self.hide  # his switch: everyone hides until he shows them again
                hiding.save_hide(self.hide)
                return
            if badges.rect(view).collidepoint(m):
                if badges.lid(view).collidepoint(m):
                    badges.toggle(t)  # the badge case drops down, or shuts
                    return
                place = badges.at(view, m)
                if place is not None:  # a gem or an empty slot: go there, like the minimap
                    self.to_place(place, t)
                return
            if self.corner_click(view, m, t):
                return
        view = self.storm_view()
        if view is not None:  # the Thunderstorm button
            m = view.mouse()
            if m and storm.button_rect(view).collidepoint(m):
                if self.updater.load(self):  # a newer glade is waiting: the button loads it
                    return
                self.lifespans.settle()
                self.storm = storm.Storm(self, t)
                self.storm_started()
                return
        if self.play_click(t):
            return
        if self.popup is not None:  # a click chooses from the open menu, or just closes it
            pop, self.popup = self.popup, None
            i = pop.at(pop.view.mouse())
            if i is not None:
                pop.choices[i][1](t)
            return
        if self.play_click_late(t):
            return
        for view, content in self.views():
            m = view.mouse()
            if not m:
                continue
            for sp in content.spots:
                self.signs.prepare(sp, view.w, view.h)
            if self.map_click(view, content, m, t):
                return
            sp = self.unless_animal(view, view.hovered(content.spots), m, t)
            moon = getattr(content, "moon", None)
            if sp is None and moon and math.hypot(m[0] - moon[0], m[1] - moon[1]) < moon[2] + 6:
                self.moon_clicked(t)  # its secrets are the game's
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
        """Right-click an animal to see its battle stats; right-click a squid to open or
        remove it (or see its stats); right-click a tree he grew to take it away."""
        self.popup = None
        if self.play_right_click(t):
            return
        if self.fade_to:
            return
        for view, content in self.views():
            m = view.mouse()
            if not m:
                continue
            if self.zoomed(view):  # (what is under the pointer is not where it looks)
                continue
            colony = getattr(content, "colony", None)
            for sp in content.spots:
                self.signs.prepare(sp, view.w, view.h)
            sp = self.unless_animal(view, view.hovered(content.spots), m, t)
            choices = []
            if sp is not None and getattr(sp, "squid", None) and colony is not None:
                sq = sp.squid
                gone = "Remove (to Trash)" if sq.item.get("path") else "Remove from the trees"
                choices = [("Open", lambda t, v=view, c=content, s=sp: self.activate(v, c, s, t)),
                           (gone, lambda t, sq=sq: colony.remove(sq)),
                           ("Battle stats", lambda t, v=view, m=m, sq=sq: self.show_card(
                               v, m, "Moonhoot" if getattr(sq, "kind", "squid") == "owlet" else "Canopod", t,
                               Perched(sq)))]
            elif sp is None:
                low = self.lower() if self.bottom else None
                found = animal_under(self.here, low, m, view is self.bottom, t)
                if found is not None:
                    self.show_card(view, m, found[1], t, found[0])
                    return
                tree = colony.tree_at(m) if colony is not None else None
                if tree is not None:
                    choices = [("Remove this tree", lambda t, g=tree: colony.cut(g, t))]
            if choices:
                self.popup = Popup(self.signs.font, view, m, choices, t)
            return

    def unless_animal(self, view, sp, m, t):
        """A path's wide clickable area gives way to an animal drawn right under the
        pointer (the Mossdelve lives inside the Mossy Rocks path's); its sign never does."""
        if sp is None or sp.kind != "go" or sp.boards[2].collidepoint(m):
            return sp
        low = self.lower() if self.bottom else None
        return None if animal_under(self.here, low, m, view is self.bottom, t, exact=True) else sp

    def storm_view(self):
        """Where the Thunderstorm button is, while it is shown (else None). With a newer glade
        waiting it is always there, battle or not: it is the only way to load it."""
        if self.updater.waiting:
            return self.bottom or self.top
        if self.storm is not None or self.storm_blocked():  # (shown the rest of the time, his ask)
            return None
        return self.bottom or self.top

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
        if self.zoomed(view):  # (its path signs are drawn after the battle, on top)
            return
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
        self.map_overlay(view, t)
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
        self.screen.fill(INK)
        for view, _ in self.views():
            view.present(self.screen)
            if self.screen.get_masks()[3]:  # composited screen: make sure no pixel is see-through
                self.screen.fill((0, 0, 0, 255), view.rect, special_flags=pygame.BLEND_RGBA_MAX)
        pygame.display.flip()

    def render(self, dt):
        """Advance everything by dt and paint each view's canvas (without showing it)."""
        t = time.monotonic() - self.t0
        self.updater.tick(self, t)
        # a quick fade, so clicking through the places never feels slow
        if self.fade_to:
            self.fade += dt / 0.15
            if self.fade >= 1:
                self.here = self.scene(self.fade_to)
                self.fade_to = None
        elif self.fade > 0:
            self.fade = max(0.0, self.fade - dt / 0.15)
        elif t > 2:
            self.idle_work(t)
        self.here.update(dt)
        self.update_play(dt, t)
        if self.fade_to:
            self.lifespans.settle()
        elif self.storm is None and self.hiding is None:
            self.lifespans.update(self, t)
        if self.storm is not None:
            if self.storm.scene is not self.here:
                self.storm.finish()  # he walked off: it is over, and settled as it would have been
                self.storm = None
            elif self.storm.done:
                self.storm = None
            else:
                self.storm.update(t)
        self.hide_for_games(t)
        self.update_play_late(dt, t)
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
            if view in self.covered:  # under a full-screen game: nobody can see it, so it waits
                continue
            content.draw(view.canvas, t)
            self.under(view, content, t)
            if self.storm is not None:
                self.storm.draw(view.canvas, view is self.bottom, t, self.storm_scratch)
            self.seen(view, content, t)
            self.lifespans.draw(view.canvas, view is self.bottom, t, self.storm_scratch)
            if self.hiding is not None:
                self.hiding.draw(view.canvas, view is self.bottom, t, self.storm_scratch)
            self.overlay(view, content, t)
            self.above(view, content, t)
            if self.storm_view() is view:
                storm.draw_button(view.canvas, view, self.signs.font)
                if self.updater.waiting:  # the notice: a newer glade to check out
                    b = storm.button_rect(view)
                    msg = "Newer glade ready! Thunderstorm loads it"
                    w = self.signs.font.size(msg)[0] + 14
                    r = pygame.Rect(b.x - w - 6, b.y, w, b.h)
                    cloth(view.canvas, r, (255, 206, 90), hot=True, alpha=235)
                    img = self.signs.font.render(msg, False, (255, 255, 255))
                    view.canvas.blit(img, (r.x + 7, r.centery - img.get_height() // 2))
            if view is (self.bottom or self.top) and self.show_panel:
                self.panel.draw(view.canvas, view, self.signs.font, t, self.storm_view() is view)
            if view is self.map_view() and self.corner_free():
                self.corner(view, t)
            if self.fade > 0:
                veil = art.solid()
                veil.fill(INK)
                veil.set_alpha(int(255 * min(1.0, self.fade)))
                view.canvas.blit(veil, (0, 0))
            m = view.mouse()
            if m:
                view.canvas.blit(CURSOR, (int(m[0]), int(m[1])))

    # --- hooks: what the desktop and the game each add (desktop.py, game.py) -----------------
    def home_only(self, content):
        return content

    def idle_work(self, t):
        """Between fades: the game loads its far places."""

    def update_play(self, dt, t):
        """Before the animals' comings and goings."""

    def update_play_late(self, dt, t):
        """After them."""

    def under(self, view, content, t):
        """Drawn just after the place itself."""

    def seen(self, view, content, t):
        """Drawn over the weather, before the animals coming and going."""

    def above(self, view, content, t):
        """Drawn over the name boards: battles, cards, the Dex, boards."""

    def map_overlay(self, view, t):
        """With the name boards: the game's minimap."""

    def corner(self, view, t):
        """The boards in the lower screen's top-left corner (corner.py)."""

    def corner_free(self):
        """Whether the corner boards are shown and clickable now."""
        return True

    def corner_click(self, view, m, t):
        return False

    def to_place(self, key, t):
        """A badge-case gem was clicked."""

    def storm_started(self):
        pass

    def storm_blocked(self):
        return False

    def play_click(self, t):
        return False

    def play_click_late(self, t):
        return False

    def map_click(self, view, content, m, t):
        return False

    def moon_clicked(self, t):
        pass

    def activate_play(self, view, content, sp, t):
        return False

    def play_right_click(self, t):
        return False

    def show_card(self, view, m, species, t, animal=None):
        pass

    def typed(self, ch, t):
        pass

    def zoomed(self, view):
        return False


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
    from game import Minimap
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


def loop(glade):
    clock = pygame.time.Clock()
    while getattr(glade, "running", True):
        dt = clock.tick(30) / 1000
        frame_start = time.monotonic()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.VIDEORESIZE and hasattr(glade, "resized"):  # the game's window
                glade.resized(e.size)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_q and e.mod & pygame.KMOD_CTRL:
                return
            if e.type == pygame.KEYDOWN and glade.panel.typing:  # a reply to Claude, being typed
                names = {pygame.K_RETURN: "return", pygame.K_KP_ENTER: "return", pygame.K_ESCAPE: "escape",
                         pygame.K_BACKSPACE: "backspace"}
                glade.panel.key(names.get(e.key, ""), e.unicode)
                continue
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
            if e.type == pygame.MOUSEWHEEL and hasattr(glade, "scroll"):
                glade.scroll(-e.y)
        glade.frame(min(dt, 0.1))
        loading.between_frames(frame_start + 1 / 30)  # the far places load in the time left over


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--shots":
        return shots(sys.argv[2])
    if "--game" in sys.argv:
        import game  # the game: all the play (world.py)
        return game.run()
    import world
    from desktop import Desktop
    world.claim(world.DESKTOP_PID)  # (so the game knows it has a desktop to stand in for)
    if os.environ.get("WAYLAND_DISPLAY") and "--x11" not in sys.argv:
        import wayland  # Hyprland: the glade as the desktop layer, one surface per monitor
        return wayland.run(Desktop)
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
    glade = Desktop(screen, fit(mons[0], W, H), mons[1] if len(mons) > 1 else None)
    loop(glade)


if __name__ == "__main__":
    main()
