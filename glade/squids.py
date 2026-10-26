"""The tree squid: his desktop icons.

Every app, and everything in his Desktop folder, is a little glowing squid holding on
to one of the trees on the left of the Glade, its name on a glowing banner underneath.
Only one squid shows on each tree; the other banners float by the trunk on their own.
Clicking a banner opens what it stands for.

- The more he clicks a squid, the better its spot: the most-used squid sit nearest the
  middle of the picture (clicks are counted in ~/.local/state/glade/squids.json).
- When a squid is added or taken away the others move to make room: up or down their
  own trunk they climb, hand over hand; to another tree they let go and swim across.
- When there are too many for the trees, they all get smaller and sit closer together.
- He can drag a squid onto another spot. It stays there (a "pin"), and whoever was
  there swaps with it.

The Desktop folder is looked at every few seconds on a background thread, so looking
never stalls a frame.
"""

import json
import math
import os
import threading
import time

import pygame

from art import GLOW, glow, mix
from life import q, swell
from orchard import app_command, short

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local/state"), "glade", "squids.json")
LOOK_EVERY = 5  # seconds between looks at the Desktop folder
RERANK_EVERY = 60  # seconds: clicks reorder the squid at most this often, so nothing jumps away mid-click

# His apps, in the order they get a spot before he has clicked anything. The keys are
# main.APPS's (the board shows that app's little picture).
APPS = [("files", "Files"), ("browser", "Web Browser"), ("terminal", "Terminal"), ("music", "Music"),
        ("games", "Games"), ("discord", "Discord"), ("code", "Code Editor")]
SKIP = {"The Glade"}  # the glade's own pictures folder: he asked for its squid to go

COLORS = dict(app=GLOW["violet"], shortcut=GLOW["cyan"], folder=GLOW["amber"], file=GLOW["pink"])

# How big the squid are, how far apart they sit on a trunk, and how much of a name fits
# on a board: the first that has room for everyone is used.
LEVELS = [(0.7, 58, 7), (0.6, 52, 6), (0.52, 47, 6), (0.46, 42, 5)]

CLIMB, SWIM = 34.0, 80.0  # pixels a second


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
            out.append(dict(id="desktop:" + n, name=e.get("Name") or n[:-8], kind="shortcut", cmd=cmd))
        elif os.path.isdir(path):
            out.append(dict(id="desktop:" + n, name=n, kind="folder", cmd=["xdg-open", path]))
        else:
            out.append(dict(id="desktop:" + n, name=os.path.splitext(n)[0] or n, kind="file", cmd=["xdg-open", path]))
    return out


def app_items():
    return [dict(id="app:" + key, name=name, kind="app", key=key) for key, name in APPS]


class Looker:
    """Keeps `items` up to date with the Desktop folder, on its own thread."""

    def __init__(self):
        self.items = app_items() + desktop_items()
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while True:
            time.sleep(LOOK_EVERY)
            try:
                self.items = app_items() + desktop_items()
            except Exception:  # never let a strange file kill the looking
                pass


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
    """All the tree squid of one place, and the clickable spots that go with them.

    `trunks`: dicts with the trunk's `x`, `bottom` and `lean` (as art.trunk returned it),
    its width `w`, and the stretch of it squid may sit on, `lo` to `hi` (y)."""

    def __init__(self, scene, spot_type, trunks):
        self.scene, self.Spot, self.trunks = scene, spot_type, trunks
        self.looker = Looker()
        self.squid = {}  # item id -> TreeSquid
        self.mine = []  # the spots this colony put into the scene
        self.shown = None
        self.ranked_at = -RERANK_EVERY
        self.dragging = None  # (TreeSquid, where it was grabbed from)
        self.gap = LEVELS[0][1]
        self.state = self.load()
        self.t = 0.0
        self.clock = None

    # remembering ---------------------------------------------------------------------
    def load(self):
        try:
            with open(STATE) as f:
                st = json.load(f)
            return dict(clicks=dict(st.get("clicks", {})), pins=dict(st.get("pins", {})))
        except (OSError, ValueError, AttributeError):
            return dict(clicks={}, pins={})

    def save(self):
        try:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE + ".tmp", "w") as f:
                json.dump(self.state, f)
            os.replace(STATE + ".tmp", STATE)
        except OSError:
            pass

    # where squid can sit --------------------------------------------------------------
    def x_at(self, i, y):
        tr = self.trunks[i]
        return tr["x"] + (tr["bottom"] - y) * tr["lean"]

    def slots(self, gap):
        out = []
        for i, tr in enumerate(self.trunks):
            mine = []
            y = tr["lo"] + (gap / 2 if i % 2 else 0)  # neighbouring trees take turns, so boards don't meet
            while y <= tr["hi"]:
                mine.append((i, round(self.x_at(i, y)), round(y)))
                y += gap
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
        n = len(items)
        for size, gap, chars in LEVELS:
            free = self.slots(gap)
            if len(free) >= n:
                break
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
        return placed, size, gap, chars

    # keeping up -----------------------------------------------------------------------
    def refresh(self, t):
        items = self.looker.items
        key = tuple(it["id"] for it in items)
        if key == self.shown and t - self.ranked_at < RERANK_EVERY:
            return
        if self.dragging:
            return
        self.shown, self.ranked_at = key, t
        self.arrange(items)

    def arrange(self, items):
        placed, size, self.gap, chars = self.layout(items)
        byid = {it["id"]: it for it in items}
        for gone in [i for i in self.squid if i not in byid or i not in placed]:
            del self.squid[gone]
        firsts = {}
        for sl in self.slots(self.gap):
            firsts.setdefault(sl[0], sl)
        held = self.dragging[0] if self.dragging else None
        spots = []
        for iid, slot in placed.items():
            it = byid[iid]
            sq = self.squid.get(iid)
            if sq is None:
                sq = self.squid[iid] = TreeSquid(it, slot[1], slot[2], size)
                if self.clock is not None:  # someone new: it swims down from the canopy
                    sq.x, sq.y = slot[1], 20
                    sq.slot = (None, slot[1], 20)
            sq.item = it
            sq.shown = sq is held or firsts.get(slot[0]) == slot
            if self.clock is None:
                sq.fade = 1.0 if sq.shown else 0.0
            sq.go(slot, size, self.trunk_of)
            _, x, y = slot
            sp = self.Spot("app", (x - 13 * size, y - 30 * size, 26 * size, 48 * size), short(it["name"], chars),
                           it.get("key"), (x, y - 6 * size), sign=(x, y + 24 * size + 11))
            sp.cmd = None if it.get("key") else it["cmd"]
            sp.full, sp.squid = it["name"], sq
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
        sq.shown = True
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
        gap = self.gap
        near = [sl for sl in self.slots(gap) if m and math.hypot(sl[1] - m[0], sl[2] - m[1]) < gap * 0.8]
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
        self.arrange(self.looker.items)

    # drawing -----------------------------------------------------------------------------
    def draw(self, s, t):
        dt = 0.0 if self.clock is None else max(0.0, min(0.1, t - self.clock))
        self.refresh(t)  # before the clock starts, so the first squid are simply there
        self.clock = t
        for sq in self.squid.values():
            sq.update(dt, t)

    def light(self, lm, t):
        for sq in self.squid.values():
            sq.light(lm, t)

    def shine(self, s, t):
        held = self.dragging[0] if self.dragging else None
        for sq in sorted(self.squid.values(), key=lambda sq: sq is held):  # the held one on top
            i = sq.slot[0] if sq.slot else None
            w = self.trunks[i]["w"] if i is not None and not sq.route else 12
            sq.shine(s, t, w)
