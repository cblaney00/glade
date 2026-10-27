"""Thunderstorms, and the animals taking turns.

Not every animal is out at once. Each place (and the ground below it on the lower
screen) has a roster; most of the second wave (beasts.py) starts out sheltering
(`gone`). While an animal's battle stats are on screen (its card, or the Forest Dex), a
**Thunderstorm** button shows in the lower screen's top-right corner. Click it and the
sky darkens, rain sets in and lightning flashes: every animal in sight shelters —
crawlers and walkers sink into a hole in the ground, anything in the air flies off, the
koi dive — then, under a flash, a new mix comes out (as many as were out before, picked at
random from everyone who lives there). The trees' dwellers are re-mixed too: tree squid and Moon
Owlets side by side, holding the same icons. The places not on screen are re-shuffled at the same moment.
Animals in a battle (battle.py) stay out of it.
"""

import math
import random

import pygame

import art
from apex import OFFSET, Prey, ease
from art import glow, mix
from battle import TEXT, cloth, draw_elsewhere
from life import q

ROTATE = ("Squid", "Nibbler", "HollowSquid", "Slug", "Millipede", "Critter", "Flier", "Walker")
AIR = ("Squid", "Nibbler", "HollowSquid", "Flier")
RAIN = (176, 186, 240)
STORM = (150, 170, 255)
LENGTH = 10.0


def newcomer(thing):
    """An animal that starts out sheltering, for a storm to bring out."""
    thing.gone = True
    return thing


def roster(content):
    """Every animal of a place (or of the ground below it) that takes turns being out."""
    if content is None:
        return []
    out, seen = [], set()
    for o in list(getattr(content, "lives", [])) + list(getattr(content, "parts", [])):
        if id(o) not in seen and type(o).__name__ in ROTATE and not getattr(o, "caught", False):  # caught: in your boxes
            seen.add(id(o))
            out.append(o)
    return out


def choose(animals, rng, n=None, before=None):
    """Who comes out after a storm: `n` of them (as many as were out before), a random mix
    of everyone who lives there, old and new alike."""
    if n is None:
        n = sum(1 for o in animals if not getattr(o, "gone", False))
    return rng.sample(animals, min(n, len(animals)))


def dwellers(colony, rng):
    """Mix up who holds the icons in the trees: each one is a tree squid or a Moon Owlet,
    with always some of both when there are two or more."""
    squid = list(colony.squid.values())
    for sq in squid:
        sq.kind = rng.choice(("squid", "owlet"))
    if len(squid) > 1 and len({sq.kind for sq in squid}) == 1:
        sq = rng.choice(squid)
        sq.kind = "owlet" if sq.kind == "squid" else "squid"


def reshuffle(content, rng, keep):
    """A storm somewhere he is not looking: the change happens at once."""
    animals = [o for o in roster(content) if not any(o is k for k in keep)]
    pick = choose(animals, rng)
    for o in animals:
        o.gone = not any(o is p for p in pick)
    colony = getattr(content, "colony", None)
    if colony is not None:
        dwellers(colony, rng)


class Shelter:
    """One animal going into hiding (`out`) or coming back out."""

    DUR = 1.5

    def __init__(self, obj, low, out, start, rng):
        self.obj, self.low, self.out, self.start = obj, low, out, start
        name = type(obj).__name__
        self.mode = "dive" if name == "Fish" else "fly" if name in AIR else "dig"
        self.a = Prey(obj, low, "storm")
        self.side = rng.choice((-1, 1))
        self.begun = self.done = False

    def update(self, t):
        if not self.begun and t >= self.start:
            self.begun = True
            self.obj.gone = True  # the storm draws it from now on, until it is settled
        if self.begun and not self.done and t >= self.start + self.DUR:
            self.done = True
            self.obj.gone = self.out

    def draw(self, s, low, t, scratch):
        if not self.begun or self.done or low != self.low:
            return
        k = ease((t - self.start) / self.DUR)
        h = k if self.out else 1 - k  # how far into hiding
        x, y = self.a.pos()
        if self.low:
            x, y = x - OFFSET[0], y - OFFSET[1]
        z = getattr(self.obj, "size", 1.0)
        if self.mode == "dig":
            # a hole opens under it, it sinks into the ground, and the hole closes over
            hy = y + 3 * z
            o = min(1.0, (t - self.start) / 0.3, (self.start + self.DUR - t) / 0.3)
            w, hh = 26 * z * o, 7 * z * o
            if w > 2:
                pygame.draw.ellipse(s, (120, 92, 120), (x - w / 2 - 2, hy - hh / 2 - 1, w + 4, hh + 2))
                pygame.draw.ellipse(s, (16, 10, 24), (x - w / 2, hy - hh / 2, w, hh))
            draw_elsewhere(s, self.a, (x, y + h * 30 * z), t, scratch, cut=hy)
            if 0.1 < k < 0.9:  # earth flicked up
                for i in range(5):
                    f = (k * 3 + i * 0.2) % 1
                    s.set_at((round(x + (i - 2) * 4 * z), round(hy - 10 * z * math.sin(f * math.pi))), (150, 116, 140))
        elif self.mode == "fly":
            draw_elsewhere(s, self.a, (x + self.side * h * 160, y - h * 240), t, scratch, alpha=round(255 * (1 - h)))
        else:  # a koi diving deep
            draw_elsewhere(s, self.a, (x, y), t, scratch, alpha=round(255 * (1 - h)))
            pygame.draw.ellipse(s, mix(RAIN, (255, 255, 255), 0.3), (x - 8 - k * 10, y - 3 - k * 3, 16 + k * 20, 6 + k * 6), 1)


EVERY = 300.0  # seconds a set of animals is out before a new one takes its place


def renew(content):
    """New animals, not the same ones back: every one in this place gets fresh IVs, and the
    ones you caught are replaced by wild ones again. Returns how many were caught."""
    n = 0
    for o in list(getattr(content, "lives", [])) + list(getattr(content, "parts", [])):
        if type(o).__name__ in ROTATE:
            if getattr(o, "caught", False):
                o.caught, o.gone = False, True
                n += 1
            o.ivs = None  # rolled again when anything asks (team.ivs_of)
    return n


class Turnover:
    """Every five minutes the animals change: the ones out quietly slip away (dig in, fly
    off, dive) and a new set comes out — new individuals with new IVs, so a strong one is
    only around for a while. No rain: it simply happens. Elsewhere it happens at once."""

    def __init__(self, glade, t):
        self.t0 = self.now = t
        self.rng = random.Random()
        self.scene = glade.here
        self.low = glade.lower() if glade.bottom else None
        arena = glade.arena
        self.keep = [f.a.obj for f in arena.fighters] + [p[0].obj for p in arena.picked] if arena else []
        if arena is not None and arena.foe:
            self.keep.append(arena.foe[0].obj)
        if glade.evolution is not None:
            self.keep.append(glade.evolution.obj)
        self.moves = []
        self.chosen = False
        self.colony = None
        self.before = {}
        n = 0
        for content, low in ((self.scene, False), (self.low, True)):
            out = [o for o in roster(content) if not getattr(o, "gone", False) and not self.kept(o)]
            self.before[id(content)] = len(out) + sum(1 for o in getattr(content, "lives", []) + list(getattr(content, "parts", []))
                                                      if getattr(o, "caught", False))
            for o in out:
                self.moves.append(Shelter(o, low, True, t + n * 0.35 + self.rng.uniform(0, 0.4), self.rng))
                n += 1
        self.out_at = t + n * 0.35 + Shelter.DUR + 1.0
        for sc in glade.scenes.values():  # elsewhere: at once
            if sc is not self.scene:
                self.elsewhere(sc)
        for lw in glade.lowers.values():
            if lw is not self.low:
                self.elsewhere(lw)

    def elsewhere(self, content):
        n = renew(content)
        animals = [o for o in roster(content) if not self.kept(o)]
        count = sum(1 for o in animals if not getattr(o, "gone", False)) + n
        pick = choose(animals, self.rng, count)
        for o in animals:
            o.gone = not any(o is p for p in pick)

    def kept(self, o):
        return any(o is k for k in self.keep)

    def update(self, t):
        if not self.chosen and t >= self.out_at:
            self.chosen = True
            self.come_out(t)
        for m in self.moves:
            m.update(t)

    def come_out(self, t):
        n = 0
        for content, low in ((self.scene, False), (self.low, True)):
            renew(content)
            animals = [o for o in roster(content) if not self.kept(o)]
            for o in choose(animals, self.rng, self.before.get(id(content), 0)):
                self.moves.append(Shelter(o, low, False, t + n * 0.4 + self.rng.uniform(0, 0.4), self.rng))
                n += 1

    @property
    def done(self):
        return self.chosen and all(m.done for m in self.moves)

    def finish(self, t=None):
        if not self.chosen:
            self.chosen = True
            self.come_out(self.t0)
        for m in self.moves:
            m.begun, m.done = True, True
            m.obj.gone = m.out

    def draw(self, s, low, t, scratch):
        self.now = t
        for m in self.moves:
            m.draw(s, low, t, scratch)


class Storm:
    def __init__(self, glade, t):
        self.t0 = self.now = t
        self.rng = random.Random()
        self.scene = glade.here
        self.low = glade.lower() if glade.bottom else None
        arena = glade.arena
        self.keep = [f.a.obj for f in arena.fighters] + [p[0].obj for p in arena.picked] if arena else []
        self.moves = []
        self.chosen = False
        self.colony = getattr(self.scene, "colony", None)
        self.bolts = [t + 0.7, t + 2.4, t + 4.4, t + 6.6, t + 8.4]
        self.strikes = {}
        self.veils = {}
        self.drops = [(self.rng.uniform(0, 1000), self.rng.uniform(0, 600), self.rng.uniform(380, 520),
                       self.rng.uniform(6, 12)) for _ in range(220)]
        # everyone in sight shelters, one after another
        n = 0
        self.before = {}  # who was out in each, so as many come back
        for content, low in ((self.scene, False), (self.low, True)):
            self.before[id(content)] = [o for o in roster(content) if not getattr(o, "gone", False) and not self.kept(o)]
            for o in roster(content):
                if not getattr(o, "gone", False) and not self.kept(o):
                    self.moves.append(Shelter(o, low, True, t + 1.0 + n * 0.22 + self.rng.uniform(0, 0.3), self.rng))
                    n += 1
            pond = getattr(content, "pond", None)
            for f in getattr(pond, "fish", []) if pond is not None else []:
                if not getattr(f, "gone", False):
                    self.moves.append(Shelter(f, low, True, t + 1.4 + self.rng.uniform(0, 1), self.rng))
        # elsewhere the change happens at once
        for sc in glade.scenes.values():
            if sc is not self.scene:
                reshuffle(sc, self.rng, self.keep)
        for lw in glade.lowers.values():
            if lw is not self.low:
                reshuffle(lw, self.rng, self.keep)

    def kept(self, o):
        return any(o is k for k in self.keep)

    def update(self, t):
        if not self.chosen and t >= self.bolts[2]:
            self.chosen = True
            self.come_out(t)
        if self.colony is not None:
            hide = self.bolts[1] <= t < self.bolts[3]  # the trees' dwellers change under the flashes
            if hide and not getattr(self.colony, "storm_hid", False):
                self.colony.storm_hid = True
                for sq in self.colony.squid.values():
                    sq.gone = True
            elif not hide and getattr(self.colony, "storm_hid", False) and t >= self.bolts[3]:
                self.colony.storm_hid = False
                for sq in self.colony.squid.values():
                    sq.gone = False
        for m in self.moves:
            m.update(t)

    def come_out(self, t):
        n = 0
        for content, low in ((self.scene, False), (self.low, True)):
            animals = [o for o in roster(content) if not self.kept(o)]
            before = self.before.get(id(content), [])
            for o in choose(animals, self.rng, len(before), before):
                self.moves.append(Shelter(o, low, False, t + 0.6 + n * 0.3 + self.rng.uniform(0, 0.3), self.rng))
                n += 1
            pond = getattr(content, "pond", None)
            for f in getattr(pond, "fish", []) if pond is not None else []:
                self.moves.append(Shelter(f, low, False, t + 1.6 + self.rng.uniform(0, 1.2), self.rng))
        if self.colony is not None:
            dwellers(self.colony, self.rng)

    @property
    def done(self):
        return self.chosen and all(m.done for m in self.moves) and self.now > self.t0 + LENGTH

    def finish(self, t=None):
        """He walked away mid-storm: settle everything as it would have ended."""
        if not self.chosen:
            self.chosen = True
            self.come_out(self.t0)
        for m in self.moves:
            m.begun, m.done = True, True
            m.obj.gone = m.out
        if self.colony is not None:
            self.colony.storm_hid = False
            for sq in self.colony.squid.values():
                sq.gone = False

    # --- drawing ---
    def draw(self, s, low, t, scratch):
        self.now = t
        for m in self.moves:
            m.draw(s, low, t, scratch)
        k = ease((t - self.t0) / 1.5) * ease((self.t0 + LENGTH - t) / 1.5)
        if k <= 0:
            return
        w, h = s.get_size()
        veil = self.veils.get((w, h))
        if veil is None:
            veil = self.veils[(w, h)] = art.solid((w, h))
            veil.fill((10, 8, 30))
        veil.set_alpha(round(110 * k))
        s.blit(veil, (0, 0))
        n = round(len(self.drops) * k)
        for x0, y0, sp, ln in self.drops[:n]:  # rain, slanting a little in the wind
            y = (y0 + sp * t) % (h + 40) - 20
            x = (x0 - y * 0.18) % w
            pygame.draw.line(s, mix((40, 40, 80), RAIN, 0.5 + 0.3 * k), (round(x), round(y)),
                             (round(x - ln * 0.18), round(y + ln)))
        for b in self.bolts:
            f = t - b
            if 0 <= f < 0.5:
                flash = (1 - f / 0.5) * (0.6 + 0.4 * (f < 0.08 or 0.14 < f < 0.2))
                if not low:
                    self.bolt(s, b, flash)
                lit = self.veils.get(("lit", w, h))
                if lit is None:
                    lit = self.veils[("lit", w, h)] = art.solid((w, h))
                    lit.fill((210, 220, 255))
                lit.set_alpha(round(120 * flash))
                s.blit(lit, (0, 0))

    def bolt(self, s, b, flash):
        """A fork of lightning down the sky."""
        if b not in self.strikes:
            rng = random.Random(int(b * 1000))
            x, y, pts = rng.uniform(150, 810), 0.0, []
            while y < rng.uniform(200, 320):
                pts.append((x, y))
                x += rng.uniform(-22, 22)
                y += rng.uniform(14, 30)
            pts.append((x, y))
            self.strikes[b] = pts
        pts = self.strikes[b]
        for x, y in pts[::2]:
            glow(s, x, y, 26, STORM, q(80 * flash))
        pygame.draw.lines(s, mix(STORM, (255, 255, 255), 0.7), False, pts, 2)


def button_rect(view):
    return pygame.Rect(view.w - 152, 8, 144, 22)


def draw_button(s, view, font):
    """The Thunderstorm button: a storm-blue board with a little lightning bolt."""
    r = button_rect(view)
    m = view.mouse()
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, STORM, hot=hot, alpha=230)
    bx, by = r.x + 10, r.y + 4
    pygame.draw.polygon(s, (255, 240, 150), [(bx + 5, by), (bx + 1, by + 8), (bx + 4, by + 8), (bx + 2, by + 14),
                                             (bx + 8, by + 5), (bx + 5, by + 5), (bx + 7, by)])
    img = font.render("Thunderstorm", False, (255, 255, 255) if hot else TEXT)
    s.blit(img, (r.x + 24, r.centery - img.get_height() // 2))
