"""The tree squid: his desktop icons.

Every app, and everything in his Desktop folder, is a little glowing squid holding on
to one of the trees on the left of the Glade, with that thing's picture in its arms.
The name shows on a glowing banner while he points at it. Clicking the picture (or the
squid) opens it.

- Each tree holds four squid. When the trees are full, the ones that don't fit wait,
  and the seed sign on the ground says how many: clicking it grows another tree.
- Right-click a squid to open or remove it (a Desktop shortcut goes to the Trash, an
  app just leaves the trees); right-click a tree he grew to take it away again.
- The more he clicks a squid, the better its spot: the most-used squid sit nearest the
  middle of the picture (clicks are counted in ~/.local/state/glade/squids.json).
- When a squid is added or taken away the others move to make room: up or down their
  own trunk they climb, hand over hand; to another tree they let go and swim across.
- He can drag a squid onto another spot. It stays there (a "pin"), and whoever was
  there swaps with it.

The Desktop folder is looked at every few seconds on a background thread, so looking
never stalls a frame.
"""

import json
import math
import os
import random
import subprocess
import threading
import time

import pygame

import art
from art import GLOW, glow, mix
from life import q, swell
from beasts import owlet
from orchard import app_command

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local/state"), "glade", "squids.json")
LOOK_EVERY = 5  # seconds between looks at the Desktop folder
RERANK_EVERY = 60  # seconds: clicks reorder the squid at most this often, so nothing jumps away mid-click

# His apps, in the order they get a spot before he has clicked anything. The keys are
# main.APPS's (the squid holds that app's little picture).
APPS = [("files", "Files"), ("browser", "Web Browser"), ("terminal", "Terminal"), ("music", "Music"),
        ("games", "Games"), ("discord", "Discord"), ("code", "Code Editor")]
SKIP = {"The Glade"}  # the glade's own pictures folder: he asked for its squid to go

COLORS = dict(app=GLOW["violet"], shortcut=GLOW["cyan"], folder=GLOW["amber"], file=GLOW["pink"])

SIZE = 0.7  # how big the squid are
PER_TREE = 4  # squid on each tree
GROUND = 392  # where the trunks meet the meadow
# where he can grow new trees (x, and how high the tree reaches), in the order they grow:
# in the open between the left trees and the signpost, short enough to stay under the moon
GROW_AT = [(372, 150), (420, 175)]
SEED = (206, 400)  # the seed sign's sapling, on the meadow under the left trees
ICON = 16  # pictures are this many pixels square

CLIMB, SWIM = 34.0, 80.0  # pixels a second


def ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


# --- pictures -----------------------------------------------------------------------------

def _icon_dirs():
    data = [os.environ.get("XDG_DATA_HOME") or os.path.join(HOME, ".local/share")]
    data += (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    return [d for d in dict.fromkeys(data) if d]


SIZES = ("64x64", "48x48", "96x96", "128x128", "256x256", "32x32", "scalable", "24x24")


def find_icon(name):
    """The file for a .desktop Icon= value: a path, or a name in the hicolor theme."""
    if not name:
        return None
    if os.path.isabs(name):
        return name if os.path.isfile(name) else None
    for d in _icon_dirs():
        for size in SIZES:
            for ext in ("png", "svg"):
                p = os.path.join(d, "icons", "hicolor", size, "apps", f"{name}.{ext}")
                if os.path.isfile(p):
                    return p
        for ext in ("png", "svg"):
            p = os.path.join(d, "pixmaps", f"{name}.{ext}")
            if os.path.isfile(p):
                return p
    return None


_PICS = {}


def picture(path):
    """A picture file scaled down to ICON x ICON (cached); None if it can't be read."""
    if path in _PICS:
        return _PICS[path]
    pic = None
    try:
        img = pygame.image.load(path)
        if img.get_bitsize() != 32:
            img = img.convert(32, pygame.SRCALPHA) if hasattr(img, "convert") else img
        w, h = img.get_size()
        k = ICON / max(w, h)
        img = pygame.transform.smoothscale(img, (max(1, round(w * k)), max(1, round(h * k))))
        pic = pygame.Surface((ICON, ICON), pygame.SRCALPHA)
        pic.blit(img, img.get_rect(center=(ICON // 2, ICON // 2)))
    except Exception:  # a strange or broken picture: the squid gets a plain one
        pic = None
    _PICS[path] = pic
    return pic


def folder_icon():
    s = pygame.Surface((ICON, ICON), pygame.SRCALPHA)
    pygame.draw.rect(s, (200, 140, 60), (1, 3, 7, 3), border_radius=1)
    pygame.draw.rect(s, (246, 190, 92), (1, 5, 14, 9), border_radius=1)
    pygame.draw.line(s, (255, 226, 150), (2, 6), (13, 6))
    return s


def page_icon():
    s = pygame.Surface((ICON, ICON), pygame.SRCALPHA)
    pygame.draw.polygon(s, (236, 230, 250), [(3, 1), (10, 1), (13, 4), (13, 15), (3, 15)])
    pygame.draw.polygon(s, (180, 170, 210), [(10, 1), (10, 4), (13, 4)])
    for y in (7, 9, 11):
        pygame.draw.line(s, (150, 140, 190), (5, y), (11, y))
    return s


def sprout_icon():
    s = pygame.Surface((ICON, 14), pygame.SRCALPHA)
    pygame.draw.line(s, (120, 210, 120), (8, 13), (8, 5), 2)
    pygame.draw.ellipse(s, (150, 240, 140), (1, 3, 7, 5))
    pygame.draw.ellipse(s, (170, 255, 160), (8, 0, 7, 5))
    return s


# --- what is on the Desktop ---------------------------------------------------------------

def read_entry(path):
    e = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            section = None
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


def desktop_items():
    try:
        names = sorted(os.listdir(DESKTOP), key=str.lower)
    except OSError:
        return []
    out = []
    for n in names:
        if n.startswith(".") or n in SKIP:
            continue
        path = os.path.join(DESKTOP, n)
        if n.endswith(".desktop"):
            e = read_entry(path)
            if not e.get("Exec") or e.get("Hidden") == "true":
                continue
            try:
                cmd = app_command(e)
            except ValueError:
                continue
            out.append(dict(id="desktop:" + n, name=e.get("Name") or n[:-8], kind="shortcut", cmd=cmd,
                            path=path, icon=find_icon(e.get("Icon"))))
        elif os.path.isdir(path):
            out.append(dict(id="desktop:" + n, name=n, kind="folder", cmd=["xdg-open", path], path=path))
        else:
            out.append(dict(id="desktop:" + n, name=os.path.splitext(n)[0] or n, kind="file",
                            cmd=["xdg-open", path], path=path))
    return out


def app_items():
    return [dict(id="app:" + key, name=name, kind="app", key=key) for key, name in APPS]


class Looker:
    """Keeps `items` up to date with the Desktop folder, on its own thread."""

    def __init__(self):
        self.items = app_items() + desktop_items()
        threading.Thread(target=self.run, daemon=True).start()

    def look(self):
        self.items = app_items() + desktop_items()

    def run(self):
        while True:
            time.sleep(LOOK_EVERY)
            try:
                self.look()
            except Exception:  # never let a strange file kill the looking
                pass


# --- trees he grows -------------------------------------------------------------------

class GrownTree:
    """A tree he grew with the seed sign: it rises out of the meadow over a couple of
    seconds, and sinks back into it when he takes it away."""

    GROW, SHRINK = 2.6, 1.6  # seconds

    def __init__(self, scene, x, top, born):
        self.x, self.top, self.born, self.dying = x, top, born, None
        rng = random.Random(x * 7 + 1)
        lay = art.plane()
        self.lean = art.trunk(lay, rng, x, top, GROUND, 12, scene.col("wood", 0.5), branches=1, pal=scene.pal)
        cx = x + (GROUND - top) * self.lean
        for r, dy, c in ((20, -2, "leaf3"), (16, 8, "leaf"), (13, -10, "leaf")):
            art.clump(lay, rng, round(cx), top + dy, r, scene.col(c, 0.5))
        art.finish(lay, scene.pal, 0.5, rng)
        self.pic = art.trimmed(lay)

    def k(self, t):
        if self.dying is not None:
            return 1 - ease((t - self.dying) / self.SHRINK)
        return ease((t - self.born) / self.GROW)

    def gone(self, t):
        return self.dying is not None and t - self.dying > self.SHRINK

    def draw(self, s, t):
        k = self.k(t)
        if k <= 0.01 or not self.pic:
            return
        surf, (px, py) = self.pic
        w, h = surf.get_size()
        hk = max(1, round(h * k))
        wk = max(1, round(w * (0.5 + 0.5 * k)))
        s.blit(pygame.transform.scale(surf, (wk, hk)), (px + (w - wk) // 2, py + h - hk))

    def light(self, lm, t):
        k = self.k(t)
        if k > 0.05:
            glow(lm, self.x, GROUND - 4, int(34 * k), GLOW["moss"], 40)




# --- one squid ------------------------------------------------------------------------

class TreeSquid:
    def __init__(self, item, x, y, size):
        self.item = item
        self.color = COLORS[item["kind"]]
        self.body = mix(self.color, (255, 255, 255), 0.35)
        self.dark = mix(self.color, (30, 20, 70), 0.45)
        self.x, self.y, self.size = x, y, size
        self.route = []  # [(x, y, how)], how: "climb" or "swim"
        self.slot = None
        self.phase = (hash(item["id"]) % 1000) / 1000 * math.tau
        self.poked = -10.0
        self.fade = 1.0  # 0..1: how much of the squid is there (only one per tree shows)
        self.shown = True

    def go(self, slot, size, trunk_of):
        """Make its way to `slot` (trunk, x, y)."""
        old, self.slot, self.target_size = self.slot, slot, size
        if old is None:
            self.x, self.y, self.size, self.route = slot[1], slot[2], size, []
            return
        if old == slot and not self.route:
            return
        here = trunk_of(self.x, self.y)
        if here is not None and here == slot[0]:
            self.route = [(slot[1], slot[2], "climb")]
        else:
            # let go, swim up and over in a gentle arc, take hold of the other trunk
            mx, my = (self.x + slot[1]) / 2, min(self.y, slot[2]) - 30 - abs(self.x - slot[1]) * 0.15
            self.route = [(mx, my, "swim"), (slot[1], slot[2], "swim")]

    def moving(self):
        return self.route[0][2] if self.route else None

    def update(self, dt, t):
        self.size += (getattr(self, "target_size", self.size) - self.size) * min(1.0, dt * 2)
        self.fade += ((1.0 if self.shown else 0.0) - self.fade) * min(1.0, dt * 3)
        if not self.route:
            return
        tx, ty, how = self.route[0]
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if how == "climb":  # hand over hand: a pull, then a pause to take a new grip
            speed = CLIMB * 2 * max(0.0, math.sin(t * 5 + self.phase)) ** 2
        else:  # swims in pulses, like the squid in the air
            speed = SWIM * (0.45 + 0.9 * max(0.0, math.sin(t * 4 + self.phase)) ** 2)
        step = speed * dt
        if d <= max(step, 0.5):
            self.x, self.y = tx, ty
            self.route.pop(0)
        else:
            self.x += dx / d * step
            self.y += dy / d * step

    def light(self, lm, t):
        if self.fade < 0.05:
            return
        glow(lm, self.x, self.y - 8 * self.size, int(34 * self.size * self.fade), self.color, q(70 + 15 * math.sin(t * 1.1 + self.phase)))

    def shine(self, s, t, trunk_w):
        if self.fade < 0.05:
            return
        sz, x, y = self.size * self.fade, self.x, self.y
        how = self.moving()
        if getattr(self, "kind", "squid") == "owlet":  # a Moonhoot holds this one (beasts.py)
            owlet(s, x, y, sz, self.color, t, self.phase, how, self.poked, getattr(self, "stage", 1))
            return
        breathe = math.sin(t * 1.1 + self.phase)
        k = swell(t - self.poked, 0.35, 1.2, wait=0.15)  # opening it: a gentle wiggle and glow
        wig = math.sin((t - self.poked) * 14) * 2 * k
        glow(s, x, y - 10 * sz, int(16 * sz), self.color, q(48 + 12 * breathe + 60 * k))
        # arms: wrapped round the trunk while it holds on, trailing while it swims
        grip = trunk_w / 2 + 1
        for side in (-1, 1):
            for j, (down, ph) in enumerate(((7, 0.0), (13, 1.4))):
                pts = []
                for i in range(7):
                    f = i / 6
                    if how == "swim":
                        px = x + side * (2 + j * 2) * sz + math.sin(t * 6 + ph + f * 3) * 2 * f * sz
                        py = y + 3 * sz + f * (down + 6) * sz
                    else:
                        reach = math.sin(t * 5 + self.phase + side + j) * 3 * sz if how == "climb" else 0
                        px = x + side * (2 * sz + math.sin(f * 2.6) * (grip - 2 * sz + 2))
                        py = y + 3 * sz + f * down * sz + reach * f
                    pts.append((px, py))
                pygame.draw.lines(s, self.dark, False, [(px + 1, py) for px, py in pts], 2 if sz > 0.75 else 1)
                pygame.draw.lines(s, self.color, False, pts, 2 if sz > 0.75 else 1)
        # the mantle, pointing up the trunk, with two fins near its tip
        ln = 22 * sz
        sway = math.sin(t * 0.8 + self.phase) * 1.5 * sz + wig
        squeeze = 1 - (0.12 * max(0.0, math.sin(t * 4 + self.phase)) if how == "swim" else 0.06 * breathe)
        left, right = [], []
        for i in range(9):
            f = i / 8
            r = 5.5 * sz * (1 - f ** 2.2) * squeeze + 0.5
            cx, cy = x + sway * f, y - 3 * sz - f * ln
            left.append((cx - r, cy))
            right.append((cx + r, cy))
        outline = left + right[::-1]
        pygame.draw.polygon(s, self.dark, [(px + 1, py) for px, py in outline])
        pygame.draw.polygon(s, self.body, outline)
        tx, ty = x + sway * 0.85, y - 3 * sz - ln * 0.82
        flap = (6 + math.sin(t * (6 if how == "swim" else 3) + self.phase) * 1.2) * sz
        for side in (-1, 1):
            pygame.draw.polygon(s, self.color, [(tx, ty - 4 * sz), (tx + side * flap, ty + 1), (tx, ty + 4 * sz)])
        pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.5), (round(x - 2 * sz), round(y - 6 * sz)),
                         (round(tx - 2 * sz), round(ty + 3 * sz)))
        stage = getattr(self, "stage", 1)
        if stage > 1:  # Boughgrip: bark plates down its mantle, leaves budding on its fins
            bark = (150, 104, 120)
            for i in range(2, 8, 2):
                f = i / 8
                r = 5.5 * sz * (1 - f ** 2.2) * squeeze
                cx, cy = x + sway * f, y - 3 * sz - f * ln
                pygame.draw.line(s, bark, (round(cx - r + 1), round(cy)), (round(cx + r - 1), round(cy - sz)), max(1, round(sz)))
            for side in (-1, 1):
                pygame.draw.ellipse(s, (110, 210, 150), (tx + side * flap - 2 * sz, ty - 1.5 * sz, 4 * sz, 3 * sz))
        if stage > 2:  # Canopolis: a whole little canopy grows from its crown, hung with glowing fruit
            for j in range(9):
                a = j / 9 * math.tau + 0.3
                lx, ly = tx + math.cos(a) * 8 * sz, ty - 8 * sz + math.sin(a) * 4.5 * sz
                c = (70, 160, 130) if j % 3 else (110, 210, 150)
                pygame.draw.circle(s, mix(c, (20, 30, 50), 0.35), (round(lx), round(ly + 1)), max(2, round(4 * sz)))
                pygame.draw.circle(s, c, (round(lx), round(ly)), max(2, round(3.6 * sz)))
            pygame.draw.circle(s, (130, 225, 165), (round(tx), round(ty - 10 * sz)), max(2, round(4.5 * sz)))
            for j, fx in enumerate((-6, 1, 6)):
                b = 0.6 + 0.4 * math.sin(t * 1.6 + j * 2 + self.phase)
                fy = ty - 3 * sz + (j % 2) * 2 * sz
                pygame.draw.line(s, (90, 150, 120), (round(tx + fx * sz), round(fy - 2 * sz)), (round(tx + fx * sz), round(fy)))
                glow(s, tx + fx * sz, fy + sz, int(5 * sz), (255, 200, 120), q(110 * b))
                s.set_at((round(tx + fx * sz), round(fy + sz)), (255, 236, 170))
            for j in range(-2, 3):  # a beard of moss under its head
                pygame.draw.line(s, (100, 200, 150), (round(x + j * 2 * sz), round(y + 3 * sz)),
                                 (round(x + j * 2 * sz + math.sin(t * 2 + j) * sz), round(y + (6 + abs(j)) * sz)))
        for j in range(3):  # spots down its back that blink
            if math.sin(t * 2 + j * 1.7 + self.phase * 3) > 0:
                s.set_at((round(x + 2 * sz + sway * 0.4), round(y - 8 * sz - j * 5 * sz)), (255, 255, 255))
        # head and big eyes; it blinks every few seconds
        hw, hh = 16 * sz, 9 * sz
        pygame.draw.ellipse(s, self.dark, (x - hw / 2 + 1, y - hh / 2 + 1, hw, hh))
        pygame.draw.ellipse(s, self.body, (x - hw / 2, y - hh / 2, hw, hh))
        blink = (t + self.phase * 2) % 4.7 < 0.15
        e = max(2, round(3.5 * sz))
        for ex in (x - 5 * sz, x + 2 * sz):
            ex, ey = round(ex), round(y)
            if blink:
                pygame.draw.line(s, (24, 16, 50), (ex, ey), (ex + e - 1, ey))
            else:
                pygame.draw.rect(s, (24, 16, 50), (ex, ey - e // 2, e, e))
                s.set_at((ex + 1, ey - e // 2 + 1), (255, 255, 255))


# --- the colony ---------------------------------------------------------------------

class Colony:
    """All the tree squid of one place, the trees he grew, and the clickable spots that go
    with them.

    `trunks`: dicts with the trunk's `x`, `bottom` and `lean` (as art.trunk returned it),
    its width `w`, and the stretch of it squid may sit on, `lo` to `hi` (y)."""

    def __init__(self, scene, spot_type, trunks):
        self.scene, self.Spot, self.base = scene, spot_type, trunks
        self.looker = Looker()
        self.squid = {}  # item id -> TreeSquid
        self.mine = []  # the spots this colony put into the scene
        self.shown = None
        self.ranked_at = -RERANK_EVERY
        self.dragging = None  # (TreeSquid, where it was grabbed from)
        self.waiting = 0  # squid with no room on the trees
        self.state = self.load()
        self.t = 0.0
        self.clock = None
        self.grown = [GrownTree(scene, x, top, -99.0) for x, top in GROW_AT if x in self.state["trees"]]
        self.dying = []  # trees sinking back into the meadow
        self.trunks = []
        self.retrunk()
        self.sprout = sprout_icon()

    # remembering ---------------------------------------------------------------------
    def load(self):
        try:
            with open(STATE) as f:
                st = json.load(f)
            return dict(clicks=dict(st.get("clicks", {})), pins=dict(st.get("pins", {})),
                        hidden=list(st.get("hidden", [])), trees=list(st.get("trees", [])))
        except (OSError, ValueError, AttributeError):
            return dict(clicks={}, pins={}, hidden=[], trees=[])

    def save(self):
        try:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE + ".tmp", "w") as f:
                json.dump(self.state, f)
            os.replace(STATE + ".tmp", STATE)
        except OSError:
            pass

    # the trees -----------------------------------------------------------------------
    def retrunk(self):
        self.trunks = list(self.base) + [
            dict(x=g.x, w=10, lo=g.top + 34, hi=GROUND - 56, bottom=GROUND, lean=g.lean, grown=g)
            for g in self.grown]

    def grow(self, t):
        """The seed sign was clicked: a new tree grows in the next free place."""
        have = {g.x for g in self.grown}
        for x, top in GROW_AT:
            if x not in have:
                self.grown.append(GrownTree(self.scene, x, top, t))
                self.state["trees"] = [g.x for g in self.grown]
                self.save()
                self.retrunk()
                self.shown = None  # rearrange now: the waiting squid swim over
                return

    def cut(self, tree, t):
        """Take a grown tree away; its squid look for room elsewhere."""
        if tree in self.grown:
            self.grown.remove(tree)
            tree.dying = t
            self.dying.append(tree)
            self.state["trees"] = [g.x for g in self.grown]
            self.save()
            self.retrunk()
            self.shown = None

    def tree_at(self, m):
        """The grown tree under the pointer `m`, or None."""
        if not m:
            return None
        for i, tr in enumerate(self.trunks):
            g = tr.get("grown")
            if g and g.top - 20 <= m[1] <= GROUND and abs(self.x_at(i, m[1]) - m[0]) < 14:
                return g
        return None

    # the squid --------------------------------------------------------------------------
    def remove(self, sq):
        """Right-click → Remove. A Desktop shortcut or file goes to the Trash (so it can be
        got back); an app only leaves the trees."""
        it = sq.item
        if it.get("path"):
            try:
                subprocess.run(["gio", "trash", it["path"]], timeout=5, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError):
                return
            self.state["clicks"].pop(it["id"], None)
            self.state["pins"].pop(it["id"], None)
            try:
                self.looker.look()
            except Exception:
                pass
        elif it["id"] not in self.state["hidden"]:
            self.state["hidden"].append(it["id"])
        self.save()
        self.shown = None

    # where squid can sit --------------------------------------------------------------
    def x_at(self, i, y):
        tr = self.trunks[i]
        return tr["x"] + (tr["bottom"] - y) * tr["lean"]

    def slots(self):
        out = []
        for i, tr in enumerate(self.trunks):
            gap = (tr["hi"] - tr["lo"]) / (PER_TREE - 0.5)
            shift = gap / 2 if i % 2 else 0  # neighbouring trees take turns, so pictures don't meet
            mine = [(i, round(self.x_at(i, y)), round(y))
                    for y in (tr["lo"] + shift + k * gap for k in range(PER_TREE))]
            # on each tree the middle of its stretch fills first
            mid = (tr["lo"] + tr["hi"]) / 2
            mine.sort(key=lambda sl: abs(sl[2] - mid))
            out += [(k, sl) for k, sl in enumerate(mine)]
        # every tree gets one before any gets two, so they spread out; among equals the
        # best spots are nearest the middle of the picture
        out.sort(key=lambda ks: (ks[0], math.hypot(ks[1][1] - 480, (ks[1][2] - 230) * 1.5)))
        return [sl for _, sl in out]

    def trunk_of(self, x, y):
        for i, tr in enumerate(self.trunks):
            if abs(self.x_at(i, y) - x) < 3 and tr["lo"] - 30 <= y <= tr["hi"] + 30:
                return i
        return None

    def layout(self, items):
        free = self.slots()
        clicks, pins = self.state["clicks"], self.state["pins"]
        order = {it["id"]: k for k, it in enumerate(items)}
        ranked = sorted(items, key=lambda it: (-clicks.get(it["id"], 0), order[it["id"]]))
        placed = {}
        for it in ranked:  # pinned squid first, to the free spot nearest where he left them
            pin = pins.get(it["id"])
            if pin and free:
                ti, py = pin
                best = min(free, key=lambda sl: (sl[0] != ti, abs(sl[2] - py)))
                placed[it["id"]] = best
                free.remove(best)
        for it in ranked:
            if it["id"] not in placed and free:
                placed[it["id"]] = free.pop(0)
        return placed

    # keeping up -----------------------------------------------------------------------
    def items(self):
        hidden = set(self.state["hidden"])
        return [it for it in self.looker.items if it["id"] not in hidden]

    def refresh(self, t):
        items = self.items()
        key = tuple(it["id"] for it in items)
        if key == self.shown and t - self.ranked_at < RERANK_EVERY:
            return
        if self.dragging:
            return
        self.shown, self.ranked_at = key, t
        self.arrange(items)

    def tile_of(self, it):
        if it["kind"] == "folder":
            return folder_icon()
        if it.get("icon"):
            pic = picture(it["icon"])
            if pic is not None:
                return pic
        return None if it["kind"] == "app" else page_icon()  # apps: main.ICONS draws theirs

    def arrange(self, items):
        placed = self.layout(items)
        self.waiting = len(items) - len(placed)
        byid = {it["id"]: it for it in items}
        for gone in [i for i in self.squid if i not in byid or i not in placed]:
            del self.squid[gone]
        spots = []
        for iid, slot in placed.items():
            it = byid[iid]
            sq = self.squid.get(iid)
            if sq is None:
                sq = self.squid[iid] = TreeSquid(it, slot[1], slot[2], SIZE)
                sq.kind = random.choice(("squid", "owlet"))  # the trees' dwellers are a mix (storm.py)
                if self.clock is not None:  # someone new: it swims down from the canopy
                    sq.x, sq.y = slot[1], 20
                    sq.slot = (None, slot[1], 20)
            sq.item, sq.shown = it, True
            sq.go(slot, SIZE, self.trunk_of)
            _, x, y = slot
            # the squid's picture sits in its arms, just under its head
            sp = self.Spot("app", (x - 9, y - 22, 18, 26), it["name"], it.get("key"), (x, y + 18),
                           sign=(x, y + 19))
            sp.cmd = None if it.get("key") else it["cmd"]
            sp.full, sp.squid = it["name"], sq
            sp.tile = self.tile_of(it) or True  # True: use the app's own pixel icon
            spots.append(sp)
        if len(self.grown) < len(GROW_AT):  # the seed sign: grows a tree for the squid waiting
            label = "Grow a tree" + (f" ({self.waiting} waiting)" if self.waiting else "")
            sp = self.Spot("grow", (SEED[0] - 12, SEED[1] - 14, 24, 20), label, None, SEED,
                           sign=(SEED[0], SEED[1] - 24))
            sp.icon = self.sprout
            spots.append(sp)
        self.scene.spots[:] = [sp for sp in self.scene.spots if sp not in self.mine] + spots
        self.mine = spots

    # being clicked and dragged ----------------------------------------------------------
    def clicked(self, sq, t):
        sq.poked = t
        clicks = self.state["clicks"]
        clicks[sq.item["id"]] = clicks.get(sq.item["id"], 0) + 1
        self.save()

    def grab(self, sp, t):
        sq = getattr(sp, "squid", None)
        if sq is None or sp not in self.mine:
            return False
        self.dragging = (sq, (sq.x, sq.y))
        return True

    def drag(self, m):
        """Called every frame while a squid is held: it follows the pointer."""
        if self.dragging and m:
            sq = self.dragging[0]
            sq.route = [(m[0], m[1] + 6 * sq.size, "swim")]

    def drop(self, m):
        """Let go of the held squid over `m`. It stays where it is dropped (if that is
        a spot on a tree), swapping with whoever was there."""
        sq, _ = self.dragging
        self.dragging = None
        near = [sl for sl in self.slots() if m and math.hypot(sl[1] - m[0], sl[2] - m[1]) < 36]
        pins = self.state["pins"]
        if near:
            new = min(near, key=lambda sl: math.hypot(sl[1] - m[0], sl[2] - m[1]))
            old = sq.slot
            for other in self.squid.values():  # whoever was there takes its old place
                if other is not sq and other.slot is not None and other.slot[1:] == new[1:]:
                    if old and old[0] is not None:
                        pins[other.item["id"]] = [old[0], old[2]]
                    break
            pins[sq.item["id"]] = [new[0], new[2]]
            self.save()
        sq.route = []
        sq.slot = (self.trunk_of(sq.x, sq.y), sq.x, sq.y)
        self.arrange(self.items())

    # drawing -----------------------------------------------------------------------------
    def draw(self, s, t):
        dt = 0.0 if self.clock is None else max(0.0, min(0.1, t - self.clock))
        self.refresh(t)  # before the clock starts, so the first squid are simply there
        self.clock = t
        self.dying = [g for g in self.dying if not g.gone(t)]
        for g in self.grown + self.dying:
            g.draw(s, t)
        for sq in self.squid.values():
            sq.update(dt, t)

    def light(self, lm, t):
        for g in self.grown + self.dying:
            g.light(lm, t)
        if len(self.grown) < len(GROW_AT):
            glow(lm, SEED[0], SEED[1] - 4, 22, GLOW["lime"], q(60 + 20 * math.sin(t * 1.3)))
        for sq in self.squid.values():
            if not getattr(sq, "gone", False):  # away in a battle (battle.py)
                sq.light(lm, t)

    def shine(self, s, t):
        if len(self.grown) < len(GROW_AT):  # the sapling under the seed sign, softly glowing
            glow(s, SEED[0], SEED[1] - 5, 9, GLOW["lime"], q(40 + 15 * math.sin(t * 1.3)))
            s.blit(self.sprout, (SEED[0] - 8, SEED[1] - 13))
        held = self.dragging[0] if self.dragging else None
        for sq in sorted(self.squid.values(), key=lambda sq: sq is held):  # the held one on top
            if getattr(sq, "gone", False):  # away in a battle (battle.py)
                continue
            i = sq.slot[0] if sq.slot else None
            w = self.trunks[i]["w"] if i is not None and i < len(self.trunks) and not sq.route else 12
            sq.shine(s, t, w)
