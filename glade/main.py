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
from pond import Pond
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
], {"1": (46, 36, 84), "3": (255, 250, 240)})


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

    def draw(self, s, text, x, y, glow_t):
        img = self.cache.get(text)
        if img is None:
            img = self.font.render(text, False, (255, 252, 244))
            self.cache[text] = img
        w, h = img.get_size()
        bx = max(2, min(W - w - 8, int(x - w / 2 - 3)))
        by = max(2, int(y - h - 10))
        box = pygame.Surface((w + 6, h + 3), pygame.SRCALPHA)
        box.fill((46, 36, 84, 190))
        s.blit(box, (bx, by))
        pygame.draw.line(s, (255, 190, 226), (bx, by + h + 2), (bx + w + 5, by + h + 2))
        s.blit(img, (bx + 3, by + 2))


def sparkle(s, x, y, t, color=(255, 255, 240)):
    """Twinkling little stars circling a spot you can click."""
    for i in range(5):
        a = t * 1.6 + i / 5 * math.tau
        px, py = x + math.cos(a) * 9, y + math.sin(a) * 5 - 2
        tw = 0.5 + 0.5 * math.sin(t * 6 + i * 1.7)
        art.glow(s, px, py, 3, color, int(80 * tw))
        s.set_at((int(px), int(py)), color)
        if tw > 0.7:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s.set_at((int(px) + dx, int(py) + dy), mix(color, (255, 190, 230), 0.4))


def arrow(s, x, y, t, target_dir, color=(255, 252, 240), bob=2):
    """A bobbing chevron pointing the way down a path."""
    dx, dy = target_dir
    bob = math.sin(t * 4) * bob
    cx, cy = x + dx * bob, y + dy * bob
    for k in (0, 3):
        ax, ay = cx + dx * k, cy + dy * k
        px, py = -dy, dx
        pygame.draw.lines(s, color, False, [
            (ax - dx * 3 + px * 3, ay - dy * 3 + py * 3), (ax, ay), (ax - dx * 3 - px * 3, ay - dy * 3 - py * 3)])


def go_direction(spot):
    cx, cy = spot.mark
    if cx < 60:
        return (-1, 0)
    if cx > W - 60:
        return (1, 0)
    return (0, -1) if cy < H * 0.75 else (0, 1)


class Glade:
    def __init__(self, screen, rect, lower=None):
        """`rect`: where the glade goes on screen. `lower`: the second monitor, if any,
        which gets the lily pond."""
        self.screen, self.rect = screen, rect
        self.canvas = art.solid()
        self.pond = None
        if lower is not None:
            scale = rect.w // W
            pw, ph = lower.w // scale, lower.h // scale
            self.pond = Pond(pw, ph)
            self.pond_canvas = art.solid((pw, ph))
            self.pond_rect = fit(lower, pw, ph)
        self.scenes = {}
        self.here = self.scene(HOME)
        self.label = Label()
        self.fade, self.fade_to = 0.0, None
        self.t0 = time.monotonic()

    def scene(self, key):
        if key not in self.scenes:
            self.scenes[key] = BUILDERS[key]()
        return self.scenes[key]

    def mouse(self):
        mx, my = pygame.mouse.get_pos()
        x0, y0, w, h = self.rect
        return (mx - x0) * W / w, (my - y0) * H / h

    def hovered(self):
        x, y = self.mouse()
        for sp in self.here.spots:
            if sp.rect.collidepoint(x, y):
                return sp
        return None

    def pond_mouse(self):
        if not self.pond:
            return None
        mx, my = pygame.mouse.get_pos()
        r = self.pond_rect
        if not r.collidepoint(mx, my):
            return None
        return (mx - r.x) * self.pond.w / r.w, (my - r.y) * self.pond.h / r.h

    def click(self, t):
        pm = self.pond_mouse()
        if pm:
            self.pond.click(*pm, t)
            return
        if self.fade_to:
            return
        x, y = self.mouse()
        c = self.here.critter
        if c and c.hit(x, y):
            c.hop()
            return
        sp = self.hovered()
        if sp is None:
            for b in self.here.bugs:
                b.scatter(x, y, t)
            return
        if sp.kind == "go":
            self.fade_to = sp.target
        else:
            launch(sp.target)
            self.flash = (sp, t)

    def frame(self, dt):
        t = time.monotonic() - self.t0
        if self.fade_to:
            self.fade += dt / 0.45
            if self.fade >= 1:
                self.here = self.scene(self.fade_to)
                self.fade_to = None
        elif self.fade > 0:
            self.fade = max(0.0, self.fade - dt / 0.45)
        self.here.update(dt)
        s = self.canvas
        self.here.draw(s, t)
        sp = None if self.fade_to else self.hovered()
        for other in self.here.spots:  # faint, always-on hints of where the paths go
            if other.kind == "go" and other is not sp:
                k = 0.5 + 0.5 * math.sin(t * 1.5 + other.mark[0])
                c = mix(self.here.pal["mist"], (255, 255, 250), 0.3 + 0.5 * k)
                arrow(s, *other.mark, t * 0.5, go_direction(other), c, bob=1)
        if sp:
            if sp.kind == "go":
                arrow(s, *sp.mark, t, go_direction(sp))
            else:
                sparkle(s, *sp.mark, t)
            self.label.draw(s, sp.label, sp.mark[0], sp.mark[1] - 6, t)
        flash = getattr(self, "flash", None)
        if flash and t - flash[1] < 0.6:
            k = 1 - (t - flash[1]) / 0.6
            art.glow(s, *flash[0].mark, int(10 + 30 * (1 - k)), (255, 250, 220), int(160 * k))
        if self.fade > 0:
            veil = art.solid()
            veil.fill(self.here.pal["mist"])
            veil.set_alpha(int(255 * min(1.0, self.fade)))
            s.blit(veil, (0, 0))
        mx, my = self.mouse()
        if 0 <= mx < W and 0 <= my < H:
            s.blit(CURSOR, (int(mx), int(my)))
        self.screen.blit(pygame.transform.scale(s, self.rect.size), self.rect.topleft)
        shown = [self.rect]
        if self.pond:
            ps = self.pond_canvas
            self.pond.update(dt, t)
            self.pond.draw(ps, t)
            pm = self.pond_mouse()
            if pm:
                ps.blit(CURSOR, (int(pm[0]), int(pm[1])))
            self.screen.blit(pygame.transform.scale(ps, self.pond_rect.size), self.pond_rect.topleft)
            shown.append(self.pond_rect)
        if self.screen.get_masks()[3]:  # composited screen: make sure no pixel is see-through
            for r in shown:
                self.screen.fill((0, 0, 0, 255), r, special_flags=pygame.BLEND_RGBA_MAX)
        pygame.display.flip()


def shots(out):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((W, H))
    os.makedirs(out, exist_ok=True)
    for key, build in BUILDERS.items():
        t0 = time.monotonic()
        sc = build()
        built = time.monotonic() - t0
        s = art.solid()
        for i in range(40):
            sc.update(0.1)
        t0 = time.monotonic()
        for i in range(30):
            sc.draw(s, 4.0 + i / 30)
        per = (time.monotonic() - t0) / 30
        pygame.image.save(pygame.transform.scale(s, (W * 3, H * 3)), os.path.join(out, f"{key}.png"))
        print(f"{key}: built in {built:.2f}s, {per * 1000:.1f} ms/frame")
    t0 = time.monotonic()
    pond = Pond(400, 225)
    built = time.monotonic() - t0
    s = art.solid((400, 225))
    for i in range(60):
        pond.update(0.1, i / 10)
    pond.click(200, 120, 5.0)
    pond.update(0.1, 5.6)
    t0 = time.monotonic()
    for i in range(30):
        pond.draw(s, 6.0 + i / 30)
    per = (time.monotonic() - t0) / 30
    pygame.image.save(pygame.transform.scale(s, (1200, 675)), os.path.join(out, "pond.png"))
    print(f"pond: built in {built:.2f}s, {per * 1000:.1f} ms/frame")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--shots":
        return shots(sys.argv[2])
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
    screen.fill((46, 36, 84))
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
