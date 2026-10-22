"""The Glade — a living pixel-art desktop.

Run:  python glade/main.py            (Ctrl+Q quits)
      python glade/main.py --shots DIR   (renders a picture of every place, then exits)
"""

import math
import os
import re
import shlex
import subprocess
import sys
import time

import pygame

import art
from art import H, W, mix
from lower import Lower
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

INK = (46, 36, 84)

CURSOR = art.sprite([
    "11.......",
    "131......",
    "1331.....",
    "13331....",
    "133331...",
    "1333331..",
    "13333331.",
    "1333311..",
    "131131...",
    "11.131...",
    "....11...",
], {"1": INK, "3": (255, 250, 240)})

# Little pictures of each app, shown on a wooden plaque over the thing that opens it.
ICONS = {k: art.sprite(rows, pal) for k, (rows, pal) in {
    "files": ([
        ".yyy.....",
        "yyyyyyyyy",
        "YYYYYYYYY",
        "YYYYYYYYY",
        "YYYYYYYYY",
        "YYYYYYYYY",
        "ooooooooo",
    ], {"y": (255, 222, 120), "Y": (255, 196, 90), "o": (214, 140, 70)}),
    "terminal": ([
        "kkkkkkkkk",
        "kgkkkkkkk",
        "kkgkkkkkk",
        "kkkgkkkkk",
        "kkgkkkkkk",
        "kgkkkgggk",
        "kkkkkkkkk",
    ], {"k": (52, 44, 92), "g": (150, 255, 180)}),
    "music": ([
        "....nnnnn",
        "....nnnnn",
        "....n...n",
        "....n...n",
        "..nnn.nnn",
        ".nnnnnnnn",
        "..nn..nn.",
    ], {"n": (190, 120, 255)}),
    "games": ([
        ".........",
        ".ccccccc.",
        "ccwcccrcc",
        "cwwwcrcrc",
        "ccwcccrcc",
        "cc.....cc",
        ".........",
    ], {"c": (120, 150, 240), "w": (255, 255, 255), "r": (255, 140, 170)}),
    "browser": ([
        "..bbbbb..",
        ".bggbbbb.",
        "bgggbbgbb",
        "bbggbgggb",
        "bbbgbbggb",
        ".bbbbbgb.",
        "..bbbbb..",
    ], {"b": (110, 190, 255), "g": (130, 230, 150)}),
    "discord": ([
        ".ppppppp.",
        "ppppppppp",
        "ppwpppwpp",
        "ppppppppp",
        "pwwwwwwwp",
        ".ppppppp.",
        "..pp.....",
    ], {"p": (140, 130, 255), "w": (255, 255, 255)}),
    "code": ([
        "......c..",
        "..c..c...",
        ".c...c.c.",
        "c...c...c",
        ".c..c..c.",
        "..cc...c.",
        "..c......",
    ], {"c": (90, 200, 255)}),
}.items()}


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


def launch(key):
    cmd = APPS.get(key)
    if not cmd:
        return
    try:
        subprocess.Popen(shlex.split(cmd), start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


class Label:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, 14)
        self.cache = {}

    def draw(self, s, text, x, y, width):
        img = self.cache.get(text)
        if img is None:
            img = self.font.render(text, False, (255, 252, 244))
            self.cache[text] = img
        w, h = img.get_size()
        bx = max(2, min(width - w - 8, int(x - w / 2 - 3)))
        by = max(2, int(y - h - 4))
        box = pygame.Surface((w + 6, h + 3), pygame.SRCALPHA)
        box.fill((*INK, 190))
        s.blit(box, (bx, by))
        pygame.draw.line(s, (255, 190, 226), (bx, by + h + 2), (bx + w + 5, by + h + 2))
        s.blit(img, (bx + 3, by + 2))


def plaque(s, spot, t, hot):
    """A small wooden plaque with the app's picture, floating over the thing it opens."""
    x, y = spot.mark
    py = int(y - 17 + math.sin(t * 1.6 + x * 0.1) * 1.5)
    art.glow(s, x, py, 13 if hot else 10, (255, 246, 210), 110 if hot else 55)
    wood, face = (176, 110, 120), (255, 246, 232) if hot else (250, 236, 222)
    r = pygame.Rect(0, 0, 13, 11)
    r.center = (x, py)
    pygame.draw.rect(s, wood, r.inflate(2, 2), border_radius=2)
    pygame.draw.rect(s, face, r, border_radius=2)
    pygame.draw.line(s, (255, 255, 255), (r.x + 1, r.y), (r.right - 2, r.y))
    pygame.draw.line(s, wood, (x, r.bottom + 1), (x, r.bottom + 3))  # a little hanging string
    icon = ICONS.get(spot.target)
    if icon:
        s.blit(icon, (r.x + 2, r.y + 2))
    return py


def sparkle(s, x, y, t, color=(255, 255, 240)):
    """Twinkling little stars circling a spot you can click."""
    for i in range(5):
        a = t * 1.6 + i / 5 * math.tau
        px, py = x + math.cos(a) * 9, y + math.sin(a) * 5 - 2
        tw = 0.5 + 0.5 * math.sin(t * 6 + i * 1.7)
        art.glow(s, px, py, 3, color, int(80 * tw))
        s.set_at((int(px), int(py)), color)


def arrow(s, x, y, t, direction, color=(255, 252, 240), bob=2):
    """A bobbing chevron pointing the way down a path."""
    dx, dy = direction
    b = math.sin(t * 4) * bob
    cx, cy = x + dx * b, y + dy * b
    for k in (0, 3):
        ax, ay = cx + dx * k, cy + dy * k
        px, py = -dy, dx
        pygame.draw.lines(s, color, False, [
            (ax - dx * 3 + px * 3, ay - dy * 3 + py * 3), (ax, ay), (ax - dx * 3 - px * 3, ay - dy * 3 - py * 3)])


def go_direction(spot, w, h):
    if spot.direction:
        return spot.direction
    cx, cy = spot.mark
    if cx < 60:
        return (-1, 0)
    if cx > w - 60:
        return (1, 0)
    return (0, -1) if cy < h * 0.75 else (0, 1)


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

    def mouse(self):
        if self.external:
            if self.pointer is None:
                return None
            mx, my = self.pointer
        else:
            mx, my = pygame.mouse.get_pos()
        if not self.rect.collidepoint(mx, my):
            return None
        return (mx - self.rect.x) * self.w / self.rect.w, (my - self.rect.y) * self.h / self.rect.h

    def hovered(self, spots):
        m = self.mouse()
        if m:
            for sp in spots:
                if sp.rect.collidepoint(m):
                    return sp
        return None

    def present(self, screen):
        shown = self.canvas.subsurface((0, 0, self.w, self.h))
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
        self.here = self.scene(HOME)
        self.label = Label()
        self.fade, self.fade_to = 0.0, None
        self.flash = None
        self.t0 = time.monotonic()

    def scene(self, key):
        if key not in self.scenes:
            self.scenes[key] = BUILDERS[key]()
        return self.scenes[key]

    def lower(self):
        key = self.here.key
        if key not in self.lowers:
            self.lowers[key] = Lower(self.here, self.bottom.w, self.bottom.h)
        return self.lowers[key]

    def views(self):
        yield self.top, self.here
        if self.bottom:
            yield self.bottom, self.lower()

    def click(self, t):
        if self.fade_to:
            return
        for view, content in self.views():
            m = view.mouse()
            if not m:
                continue
            c = getattr(content, "critter", None)
            if c and c.hit(*m):
                c.hop()
                return
            sp = view.hovered(content.spots)
            if sp is None:
                if hasattr(content, "click"):
                    content.click(*m, t)
                else:
                    for b in content.bugs:
                        b.scatter(*m, t)
            elif sp.kind == "go":
                self.fade_to = sp.target
            else:
                launch(sp.target)
                self.flash = (view, sp, t)
            return

    def overlay(self, view, content, t):
        s = view.canvas
        sp = None if self.fade_to else view.hovered(content.spots)
        for other in content.spots:
            if other.kind == "go" and other is not sp:  # faint, always-on hints of where paths go
                k = 0.5 + 0.5 * math.sin(t * 1.5 + other.mark[0])
                arrow(s, *other.mark, t * 0.5, go_direction(other, view.w, view.h),
                      mix(content.pal["mist"], (255, 255, 250), 0.3 + 0.5 * k), bob=1)
        label_y = None
        for other in content.spots:
            if other.kind == "app":
                py = plaque(s, other, t, other is sp)
                if other is sp:
                    label_y = py - 7
        if sp:
            if sp.kind == "go":
                arrow(s, *sp.mark, t, go_direction(sp, view.w, view.h))
                label_y = sp.mark[1] - 6
            else:
                sparkle(s, *sp.mark, t)
            self.label.draw(s, sp.label, sp.mark[0], label_y, view.w)
        if self.flash and self.flash[0] is view and t - self.flash[2] < 0.6:
            k = 1 - (t - self.flash[2]) / 0.6
            art.glow(s, *self.flash[1].mark, int(10 + 30 * (1 - k)), (255, 250, 220), int(160 * k))

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
        if self.fade_to:
            self.fade += dt / 0.45
            if self.fade >= 1:
                self.here = self.scene(self.fade_to)
                self.fade_to = None
        elif self.fade > 0:
            self.fade = max(0.0, self.fade - dt / 0.45)
        self.here.update(dt)
        for view, content in self.views():
            if content is not self.here:
                content.update(dt, t)
            content.draw(view.canvas, t)
            self.overlay(view, content, t)
            if self.fade > 0:
                veil = art.solid()
                veil.fill(self.here.pal["mist"])
                veil.set_alpha(int(255 * min(1.0, self.fade)))
                view.canvas.blit(veil, (0, 0))
            m = view.mouse()
            if m:
                view.canvas.blit(CURSOR, (int(m[0]), int(m[1])))


def shots(out):
    """A picture of every place with its lower screen under it, laid out as on his desk
    (the lower monitor is 40 canvas pixels in from the left), plus timings."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((W, H))
    os.makedirs(out, exist_ok=True)
    lw, lh, lx = 400, 225, 40
    for key, build in BUILDERS.items():
        t0 = time.monotonic()
        sc = build()
        low = Lower(sc, lw, lh)
        built = time.monotonic() - t0
        top, bot = art.solid(), art.solid()
        for i in range(40):
            sc.update(0.1)
            low.update(0.1, i / 10)
        t0 = time.monotonic()
        for i in range(30):
            sc.draw(top, 4.0 + i / 30)
            low.draw(bot, 4.0 + i / 30)
        per = (time.monotonic() - t0) / 30
        for content, s, w, h in ((sc, top, W, H), (low, bot, lw, lh)):
            for spot in content.spots:
                if spot.kind == "app":
                    plaque(s, spot, 4.0, False)
                else:
                    arrow(s, *spot.mark, 4.0, go_direction(spot, w, h))
        sheet = pygame.Surface((W, H + lh))
        sheet.fill((30, 26, 50))
        sheet.blit(top, (0, 0))
        sheet.blit(bot, (lx, H), (0, 0, lw, lh))
        pygame.image.save(pygame.transform.scale(sheet, (W * 2, (H + lh) * 2)), os.path.join(out, f"{key}.png"))
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
            if e.type == pygame.KEYDOWN and e.key == pygame.K_HOME:
                glade.fade_to = HOME
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                glade.click(time.monotonic() - glade.t0)
        glade.frame(min(dt, 0.1))


if __name__ == "__main__":
    main()
