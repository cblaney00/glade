"""The apex — an easter egg.

Click the moon (its halo swells: it is listening) and type "apex". The moon dims, two
glowing eyes open at the edge of the dark, and something small, quick and very hungry
oozes in. In under a minute it hunts down every animal in the place and on the ground
below it, gets visibly rounder with each one, then waddles off the edge, full. Within
twenty seconds of it leaving, every animal glows gently back into being.

It looks like nothing real: a soft, wobbling blob of dark violet jelly with two big eyes
and nothing else — no legs, no ears, no tail. It oozes along the ground, stretching
forward and catching up with itself, and drips fluorescent goo wherever it goes.
Everything it eats stays visible inside it for a while, glowing through its skin in the
animal's own colours, so its belly fills up with little lights as the hunt goes on.
Its ways:

- things in the air (squid): it swells and spits a homing glob of goo; the squid,
  wrapped in a glowing cocoon, drops to the ground; it flicks out a long sticky tongue,
  reels the cocoon into its mouth, chews, and you see it go down;
- things on the ground (slugs, snails, millipedes, the critter): it creeps in low,
  flattens and quivers, springs, and comes down with the animal in its mouth;
- the koi: it sits at the pond's edge disguised as a lily pad and dangles a glowing
  bead of itself in the water as bait, then snaps up each fish that comes close;
- the fireflies, last: a quick spray of droplets sticks them in goo, and then one huge
  breath in sucks every one of them, still glowing, into its mouth.

While stalking it mimics its target like a cuttlefish: it takes on its colours in
slow ripples and half-closes its eyes (lily-pad green by the pond).
When it is full it does not just leave: it sighs, waddles, hiccups, flops down for a
rest, heaves itself up, burps an enormous bubble, winks back at you, and wobbles off.

Everything here is in one shared coordinate space: the top screen's canvas as it is, and
the lower screen's canvas below it, shifted by OFFSET (the scenes are drawn to that
layout: lower x = upper x - 80).
"""

import math
import random

import pygame

from art import glow, mix
from life import q, swell

OFFSET = (80, 540)

GOO = (170, 255, 90)          # fluorescent acid green
GOO_HI = (232, 255, 200)
INK = (14, 8, 24)
SKIN = (58, 38, 88)           # deep night violet
EYE = (238, 255, 226)
LILY = (70, 150, 110)

TIME_LIMIT = 30               # after this, whatever is left is finished off in a volley
WORD = "apex"


def ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


# --- the animals it can eat ------------------------------------------------------------

class Prey:
    """One animal: where it is (shared coordinates), how to make it vanish and come back."""

    def __init__(self, obj, low, kind):
        self.obj, self.low, self.kind = obj, low, kind
        if kind == "fish":
            self.color = obj.colors[0]
        else:
            self.color = getattr(obj, "color", None) or getattr(obj, "body", None) or (200, 200, 220)
        self.mimic = "lily" if kind == "fish" else None
        self.eaten = False

    def pos(self):
        o = self.obj
        name = type(o).__name__
        if name == "Slug":
            x, y = o.track.at(o.d)[:2]
        elif name in ("Millipede", "Critter", "Fish"):
            pts = getattr(o, "pts", None)
            x, y = pts[0][:2] if pts else o.track.at(o.d)[:2]
        elif name == "HollowSquid":
            x, y = o.x, o.y - 12
        else:
            x, y = o.x, o.y
        if self.low:
            return x + OFFSET[0], y + OFFSET[1]
        return x, y

    def hide(self):
        self.obj.gone = True
        self.eaten = True

    def show(self):
        self.obj.gone = False


def find_prey(scene, lower):
    prey, swarms = [], []
    for content, low in ((scene, False), (lower, True)):
        if content is None:
            continue
        things = list(getattr(content, "lives", [])) + list(getattr(content, "parts", []))
        seen = set()
        for o in things:
            if id(o) in seen:
                continue
            seen.add(id(o))
            name = type(o).__name__
            if name in ("Squid", "Nibbler", "HollowSquid"):
                prey.append(Prey(o, low, "fly"))
            elif name in ("Slug", "Millipede", "Critter"):
                prey.append(Prey(o, low, "crawl"))
            elif name == "Fireflies":
                swarms.append((o, low))
        pond = getattr(content, "pond", None)
        if pond is not None and hasattr(pond, "fish"):
            for f in pond.fish:
                prey.append(Prey(f, low, "fish"))
    return prey, swarms


# --- bits of goo -----------------------------------------------------------------------

class Drop:
    """A drip of goo: falls to `floor`, then lies there glowing and fades away."""

    def __init__(self, x, y, floor, vx=0.0, vy=0.0, life=2.5):
        self.x, self.y, self.floor, self.vx, self.vy = x, y, floor, vx, vy
        self.landed, self.life = None, life

    def update(self, dt, t):
        if self.landed is None:
            self.vy += 260 * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.y >= self.floor:
                self.y, self.landed = self.floor, t
        return self.landed is None or t - self.landed < self.life

    def draw(self, s, ox, oy, t):
        x, y = self.x - ox, self.y - oy
        if self.landed is None:
            s.set_at((round(x), round(y)), GOO_HI)
            glow(s, x, y, 4, GOO, 48)
        else:
            k = 1 - ease((t - self.landed) / self.life)
            if k > 0.05:
                pygame.draw.line(s, mix((24, 30, 30), GOO, 0.55 * k), (round(x) - 1, round(y)), (round(x) + 1, round(y)))
                glow(s, x, y, 5, GOO, q(36 * k))


class Glob:
    """A glob of goo spat at something; it homes in on `aim()` and calls `hit()` on arrival."""

    def __init__(self, x, y, aim, hit, speed=420, small=False):
        self.x, self.y, self.aim, self.hit, self.speed, self.small = x, y, aim, hit, speed, small
        tx, ty = aim()
        d = math.hypot(tx - x, ty - y) or 1
        self.vx, self.vy = (tx - x) / d * speed, (ty - y) / d * speed - 120
        self.trail = []
        self.done = False
        self.age = 0.0

    def update(self, dt, t):
        tx, ty = self.aim()
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        self.age += dt
        if self.age > 1.2:  # never circle a target: after a moment, go straight in
            k = min(1.0, dt * 10)
            self.x, self.y = self.x + dx * k, self.y + dy * k
            d = math.hypot(tx - self.x, ty - self.y)
        if d < max(6.0, self.speed * dt * 1.2):
            self.done = True
            self.hit(t)
            return False
        # it never misses: steer harder the closer it gets
        k = min(1.0, dt * (5 + 400 / max(d, 20)))
        self.vx += (dx / d * self.speed - self.vx) * k
        self.vy += (dy / d * self.speed - self.vy) * k
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.trail = ([(self.x, self.y)] + self.trail)[:6]
        return True

    def draw(self, s, ox, oy, t):
        r = 1 if self.small else 2
        for i, (x, y) in enumerate(self.trail[1:]):
            if i % 2 == 0:
                s.set_at((round(x - ox), round(y - oy)), GOO)
        pygame.draw.circle(s, GOO, (round(self.x - ox), round(self.y - oy)), r)
        s.set_at((round(self.x - ox) - 1, round(self.y - oy) - 1), GOO_HI)
        glow(s, self.x - ox, self.y - oy, 6 if self.small else 10, GOO, 72)


class Cocoon:
    """An animal wrapped in goo: it swells over the animal, which still shows through in
    its own colours, then drops to the ground — and waits there to be eaten. Or, once
    `aim` is set, it is sucked through the air into the mouth at aim()."""

    def __init__(self, prey, t, floor):
        self.prey, self.t0 = prey, t
        self.x, self.y = prey.pos()
        self.floor, self.vy = floor, 0.0
        self.landed = False
        self.size = 1.0     # shrinks as it is pulled into the mouth
        self.gone = False   # swallowed
        self.aim, self.v = None, 0.0

    def update(self, dt, t):
        a = t - self.t0
        if a > 0.35 and not self.prey.eaten:
            self.prey.hide()  # covered by the goo by now
        if self.aim is not None and a > 0.35:
            tx, ty = self.aim()
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            self.v = min(480.0, self.v + 650 * dt)
            if d < max(4.0, self.v * dt):
                self.gone = True
                return False
            step = max(0.0, self.v) * dt
            self.x += (dx / d - dy / d * 0.3) * step   # a little swirl as it goes in
            self.y += (dy / d + dx / d * 0.3) * step
            self.size = max(0.5, min(1.0, d / 50))
            self.landed = True
        elif a > 0.5 and not self.landed:
            self.vy += 300 * dt
            self.y += self.vy * dt
            if self.y >= self.floor:
                self.y, self.landed = self.floor, True
        elif a <= 0.5:
            self.x, self.y = self.prey.pos() if not self.prey.eaten else (self.x, self.y)
        return not self.gone

    def draw(self, s, ox, oy, t):
        a = t - self.t0
        r = 7 * ease(a / 0.35) * self.size
        if r < 0.5:
            return
        x, y = self.x - ox, self.y - oy
        pygame.draw.circle(s, mix(GOO, (40, 60, 40), 0.35), (round(x), round(y)), round(r))
        # the animal inside, still in its own colours
        pygame.draw.circle(s, mix(self.prey.color, GOO, 0.25), (round(x + r * 0.1), round(y + r * 0.1)),
                           max(1, round(r * 0.55)))
        s.set_at((round(x - r * 0.4), round(y - r * 0.5)), (255, 255, 255))
        glow(s, x, y, int(r * 2.5) + 4, GOO, q(60 + 30 * math.sin(t * 6)))


class Morsel:
    """A firefly stuck in a speck of goo: it sinks slowly, still glowing, until the apex
    breathes in — then it is sucked, faster and faster, into its mouth."""

    def __init__(self, x, y, color, aim):
        self.x, self.y, self.color, self.aim = x, y, color, aim
        self.pull = False
        self.v = 0.0
        self.eaten = False

    def update(self, dt, t):
        if not self.pull:
            self.y += 6 * dt
            self.x += math.sin(t * 3 + self.y) * 4 * dt
            return True
        tx, ty = self.aim()
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        self.v = min(520.0, self.v + 700 * dt)
        if d < max(3.0, self.v * dt):
            self.eaten = True
            return False
        # a little swirl as it goes in
        self.x += (dx / d - dy / d * 0.35) * self.v * dt
        self.y += (dy / d + dx / d * 0.35) * self.v * dt
        return True

    def draw(self, s, ox, oy, t):
        x, y = round(self.x - ox), round(self.y - oy)
        s.set_at((x, y), mix(self.color, (255, 255, 255), 0.5))
        glow(s, x, y, 5, self.color, 70)
        glow(s, x, y, 3, GOO, 36)


class Bubble:
    """A glowing burp that floats up, wobbling, and pops softly."""

    def __init__(self, x, y, t, size=2):
        self.x, self.y, self.t0, self.size = x, y, t, size
        self.life = 1.6 + size * 0.3

    def update(self, dt, t):
        self.y -= (14 - self.size) * dt
        return t - self.t0 < self.life

    def draw(self, s, ox, oy, t):
        a = t - self.t0
        k = swell(a, 0.3, self.life - 0.3)
        x, y = self.x - ox + math.sin(a * 6) * 1.5, self.y - oy
        r = self.size + a * (1 + self.size * 0.4)
        pygame.draw.circle(s, mix((20, 30, 20), GOO, k), (round(x), round(y)), round(r), 1)
        s.set_at((round(x - r * 0.4), round(y - r * 0.4)), GOO_HI)
        glow(s, x, y, round(r * 2 + 4), GOO, q(50 * k))


class Sparkle:
    """An animal coming back: a soft glow that swells where it is and fades again; the
    animal appears at the brightest moment."""

    def __init__(self, prey, t):
        self.prey, self.t0 = prey, t
        self.shown = False

    def update(self, dt, t):
        if not self.shown and t - self.t0 > 0.9:
            self.prey.show()
            self.shown = True
        return t - self.t0 < 2.4

    def draw(self, s, ox, oy, t):
        k = swell(t - self.t0, 0.9, 1.5)
        if k <= 0:
            return
        x, y = self.prey.pos()
        x, y = x - ox, y - oy
        glow(s, x, y, 18, (236, 240, 255), q(90 * k))
        for i in range(4):
            a = t * 1.5 + i / 4 * math.tau
            s.set_at((round(x + math.cos(a) * 9 * k), round(y + math.sin(a) * 5 * k)), (255, 255, 240))


# --- the creature ----------------------------------------------------------------------

class Apex:
    """A wobbling blob of jelly with two eyes. Its shape is a ring of points around an
    ellipse, each pushed in and out by slow ripples, with the bottom flattened onto the
    ground — so it never quite holds still, and has no legs, ears or tail to read as a
    cat."""

    POINTS = 20

    def __init__(self, x, y):
        self.x, self.y = x, y            # where it touches the ground
        self.face = 1                    # 1: looking right
        self.fat = 1.0
        self.crouch = 0.0                # 0..1, low and flat when stalking
        self.coil = 0.0                  # 0..1, quivering, about to spring
        self.puff = 0.0                  # 0..1, swollen with goo, about to spit
        self.mouth = 0.0                 # 0..1, how wide its mouth is open
        self.squint = 0.0                # 0..1, happy ^ ^ eyes
        self.wink = False                # one eye shut, one open
        self.mimic = 0.0                 # 0..1, how far into its disguise it is
        self.mimic_color, self.mimic_kind = SKIN, None
        self.lift = 0.0                  # height off the ground (leaps, hiccups)
        self.gait = 0.0                  # how far it has oozed (drives its rhythm)
        self.stretch = 0.0               # 0..1, front reaching ahead as it moves
        self.squash = 0.0                # -1 tall and thin .. 1 flat and wide
        self.sway = 0.0                  # sideways lean (its top leans, its base stays)
        self.lurk = 0.0                  # 1: only its eyes show, in the dark
        self.look = 0.0                  # looking back over its shoulder
        self.waddle = 0.0                # 0..1, the heavy rocking walk of a full belly
        self.ground = None               # while leaping: where the ground is, for its shadow
        self.tongue = None               # where the tip of its tongue is (shared coords)
        self.bait = 0.0                  # 0..1, a dangling glowing bead of itself
        self.held = None                 # the colour of what is in its mouth
        self.lumps = []                  # meals glowing inside it: [time, colour, dx, dy]

    def size(self):
        pulse = math.sin(self.gait * 0.45) * 0.1   # it oozes: squeeze, spread, squeeze
        sq = self.squash + pulse + 0.15 * self.puff
        rx = 9 * self.fat * (1 + 0.3 * self.crouch + 0.2 * sq + 0.15 * self.puff)
        ry = 7 * (1 + (self.fat - 1) * 0.6) * (1 - 0.35 * self.crouch - 0.25 * sq + 0.15 * self.puff)
        return rx, max(2.0, ry)

    def centre(self):
        rx, ry = self.size()
        return self.x, self.y - self.lift - ry * 0.85

    def mouth_at(self):
        rx, ry = self.size()
        cx, cy = self.centre()
        return cx + self.face * rx * 0.85, cy + ry * 0.2

    def drips(self):
        """Where goo can drip from (shared coordinates): along its underside."""
        rx, _ = self.size()
        base = self.y - self.lift
        return [(self.x - rx * 0.6, base), (self.x + rx * 0.5, base), (self.x, base - 1)]

    def outline(self, x, base, rx, ry, t):
        f = self.face
        cy = base - ry * 0.85
        rock = self.sway + math.sin(self.gait * 0.22) * 0.45 * self.waddle
        rock += math.sin(t * 40) * 0.25 * self.coil  # quivering
        pts = []
        for i in range(self.POINTS):
            th = i / self.POINTS * math.tau
            wob = 1 + 0.12 * math.sin(3 * th + t * 2.3) + 0.07 * math.sin(5 * th - t * 3.1 + 1)
            px = math.cos(th) * rx * wob
            py = math.sin(th) * ry * wob
            if px * f > 0:   # the front reaches ahead as it moves, the back trails
                px *= 1 + 0.35 * self.stretch
            else:
                px *= 1 - 0.1 * self.stretch
            py = min(py, ry * 0.85)   # flat underneath: it sits on the ground like jelly
            px += rock * (ry * 0.85 - py) * 0.5
            pts.append((x + px, cy + py))
        return pts

    def draw(self, s, ox, oy, t):
        f = self.face
        rx, ry = self.size()
        x = self.x - ox
        base = self.y - oy - self.lift
        cy = base - ry * 0.85
        if self.lurk >= 1:
            self.draw_eyes(s, x, cy, rx, ry, t, glow_only=True)
            return
        skin = mix(SKIN, mix(self.mimic_color, (20, 14, 40), 0.35),
                   self.mimic * (0.8 + 0.2 * math.sin(t * 6)))  # colour comes in slow ripples
        if self.mimic_kind == "lily":
            skin = mix(SKIN, LILY, self.mimic)
        shade = mix(skin, INK, 0.5)
        hi = mix(skin, (255, 255, 255), 0.25)
        # shadow
        gy = (self.ground if self.ground is not None else self.y) - oy
        pygame.draw.ellipse(s, (10, 8, 20), (round(x - rx), round(gy - 1), round(rx * 2), 3))
        # a glowing bead of itself, dangled behind it as bait
        if self.bait > 0.05:
            sx, sy = x - f * rx * 0.7, cy + ry * 0.3
            ex = sx - f * 10 * self.bait + math.sin(t * 2) * 1.5
            ey = base + 4 * self.bait
            pygame.draw.lines(s, skin, False, [(sx, sy), ((sx + ex) / 2 - f * 2, sy + 1), (ex, ey)], 2)
            pygame.draw.circle(s, GOO, (round(ex), round(ey)), 2)
            glow(s, ex, ey, 9, GOO, q(70 * self.bait))
        # the body: a shaded jelly, lit from above, no outline
        pts = self.outline(x, base, rx, ry, t)
        pygame.draw.polygon(s, shade, pts)
        lit = [(px + (x - px) * 0.18, py + (cy - ry * 0.25 - py) * 0.22) for px, py in pts]
        pygame.draw.polygon(s, skin, lit)
        # a thin moonlit rim along its top, so it stands out from the dark ground
        rim = [p for p in pts if p[1] < cy - ry * 0.35]
        if len(rim) > 1:
            pygame.draw.lines(s, mix(skin, (190, 200, 255), 0.35), False, rim)
        hx, hy = x - f * rx * 0.2, cy - ry * 0.5
        pygame.draw.line(s, hi, (round(hx - rx * 0.3), round(hy)), (round(hx + rx * 0.2), round(hy)))
        # everything it has eaten, glowing through its skin
        for lump in self.lumps:
            self.draw_lump(s, lump, x, cy, rx, ry, t, skin)
        self.draw_eyes(s, x, cy, rx, ry, t)
        # mouth
        mx, my = x + f * rx * 0.85, cy + ry * 0.2
        if self.mouth > 0.08:
            h = 2 + 6 * self.mouth
            w = 3 + 2 * self.mouth
            r = pygame.Rect(0, 0, round(w), round(h))
            r.center = (round(mx), round(my))
            pygame.draw.ellipse(s, INK, r)
            glow(s, mx, my, round(h), GOO, 30)
            if self.held is not None:
                pygame.draw.circle(s, self.held, (round(mx), round(my)), max(1, round(h * 0.3)))
                glow(s, mx, my, 6, self.held, 50)
        else:
            pygame.draw.line(s, shade, (round(mx - f * 2), round(my)), (round(mx), round(my)))
            if self.held is not None:  # something still sticking out
                pygame.draw.circle(s, self.held, (round(mx + f), round(my)), 1)
        # the tongue: a long sticky strand of goo
        if self.tongue is not None:
            tx, ty = self.tongue[0] - ox, self.tongue[1] - oy
            pygame.draw.line(s, mix(GOO, SKIN, 0.3), (round(mx), round(my)), (round(tx), round(ty)), 2)
            pygame.draw.line(s, GOO_HI, (round(mx), round(my) - 1), (round(tx), round(ty) - 1))
            glow(s, tx, ty, 7, GOO, 70)

    def draw_lump(self, s, lump, x, cy, rx, ry, t, skin):
        t0, color, dx, dy = lump
        a = t - t0
        k = ease(a / 0.8)   # slides from the mouth to its place in the belly
        mx = x + self.face * rx * 0.75
        lx = mx + (x + dx * rx - mx) * k
        ly = cy + ry * 0.2 + (dy * ry - ry * 0.2) * k
        fresh = 1 - 0.4 * ease((a - 1) / 5)  # bright going down, a softer glow after
        r = 3 if k < 1 else 2.5
        pygame.draw.circle(s, mix(skin, color, 0.85 * fresh), (round(lx), round(ly)), round(r))
        s.set_at((round(lx) - 1, round(ly) - 1), mix(color, (255, 255, 255), 0.5 * fresh))
        if a < 2.5:  # the big glow only while it goes down, or a full belly turns white
            glow(s, lx, ly, 9, color, q(90 * (1 - ease((a - 1) / 1.5))))
        glow(s, lx, ly, 4, color, 30)

    def draw_eyes(self, s, x, cy, rx, ry, t, glow_only=False):
        f = self.face if self.look < 0.5 else -self.face
        blink = (t % 3.7) < 0.12
        for i, dx in enumerate((0.15, 0.5)):
            ex, ey = round(x + f * rx * dx), round(cy - ry * 0.3)
            glow(s, ex, ey, 5, GOO, 36 if not glow_only else q(70 * min(1.0, self.lurk)))
            if glow_only:
                if not blink:
                    s.set_at((ex, ey), GOO_HI)
                continue
            shut = self.squint > 0.5 or (self.wink and i == 0)
            if blink or shut:
                pts = [(ex - 2, ey), (ex, ey - 2), (ex + 2, ey)] if shut else [(ex - 2, ey), (ex + 2, ey)]
                pygame.draw.lines(s, INK, False, pts, 1)
                continue
            pygame.draw.circle(s, EYE, (ex, ey), 2)
            pygame.draw.rect(s, INK, (ex + (f > 0) - (f < 0), ey - 1, 1, 2))  # pupil, looking ahead
            if self.mimic > 0.5:  # half-closed: innocent
                lid = mix(SKIN, self.mimic_color if self.mimic_kind != "lily" else LILY, self.mimic)
                pygame.draw.line(s, lid, (ex - 2, ey - 2), (ex + 2, ey - 2))
                pygame.draw.line(s, lid, (ex - 2, ey - 1), (ex + 2, ey - 1))


# --- the hunt --------------------------------------------------------------------------

class Hunt:
    """Runs the whole thing as a little script (a generator that advances a frame at a
    time), and draws the creature and all its goo on both screens."""

    def __init__(self, scene, lower, low_size, t, seed=None):
        self.scene, self.lower = scene, lower
        self.low_w, self.low_h = low_size if lower is not None else (0, 0)
        self.prey, self.swarms = find_prey(scene, lower)
        self.rng = random.Random(seed)
        self.t0 = self.t = t
        self.dt = 0.0
        self.bits = []
        self.apex = Apex(-14, 470)
        self.firefly_out = {}   # (swarm index, firefly index) -> time it was put out
        self.firefly_back = {}  # same -> time it starts coming back
        self.done = False
        self.script = self.run()
        self.next_drip = 0.0

    # walking ------------------------------------------------------------------------
    def floor(self, x, y):
        """Where a drip at (x, y) lands: the ground under it."""
        if y < OFFSET[1]:
            return min(OFFSET[1] - 4, max(y + 3, 440))
        return y + 3

    def ground_spot(self, x, y):
        """The nearest place it can stand to get at something at (x, y)."""
        if y < OFFSET[1] or self.lower is None:
            return max(20.0, min(940.0, x)), max(420.0, min(526.0, y if y >= 420 else 440))
        lx0, lx1 = OFFSET[0] + 16, OFFSET[0] + self.low_w - 16
        return max(lx0, min(lx1, x)), max(OFFSET[1] + 10, min(OFFSET[1] + self.low_h - 10, y))

    def go(self, aim, speed=380.0, stalk=0.0, near=4.0):
        """Ooze toward aim() in quick surges; when stalking, the last stretch is slow,
        low, and in disguise."""
        a = self.apex
        seam = OFFSET[1]
        cross = None
        while True:
            tx, ty = aim()
            via = self.lower is not None and (a.y < seam) != (ty < seam)
            if not via:
                cross = None
            else:
                # between the screens it crosses where the lower one is, at a spot chosen
                # once per crossing
                if cross is None:
                    cross = max(OFFSET[0] + 30, min(OFFSET[0] + self.low_w - 30, (a.x + tx) / 2))
                sx = cross
                if abs(a.x - sx) > 4 or abs(a.y - seam) > 8:
                    tx, ty = sx, (seam - 4 if a.y < seam else seam + 4)
                else:
                    tx, ty = sx, (seam + 6 if a.y < seam else seam - 6)
            dx, dy = tx - a.x, ty - a.y
            d = math.hypot(dx, dy)
            if d <= near and not via:
                return
            if abs(dx) > 1:
                a.face = 1 if dx > 0 else -1
            surge = abs(math.sin(self.t * 5.5))
            v = speed * (0.55 + 0.45 * surge)
            reach = 0.25 + 0.6 * surge if speed > 100 else 0.25
            if stalk and d < 70:
                v, reach = 90, 0.3
                a.crouch += (1 - a.crouch) * min(1.0, self.dt * 4)
                a.mimic += (stalk - a.mimic) * min(1.0, self.dt * 2.5)
            a.stretch = max(a.stretch, reach)
            step = min(d, v * self.dt)
            if d > 0:
                a.x += dx / d * step
                a.y += dy / d * step
            a.gait += step * 0.6
            yield

    def wait(self, secs, each=None):
        end = self.t + secs
        while self.t < end:
            if each:
                each(1 - (end - self.t) / secs)
            yield

    def relax(self):
        a = self.apex
        a.crouch, a.coil, a.puff, a.mouth, a.squash = 0.0, 0.0, 0.0, 0.0, 0.0

    # the moves ----------------------------------------------------------------------
    def arrive(self):
        a = self.apex
        a.lurk = 1.0
        a.x, a.y = 10, 476
        yield from self.wait(1.3)  # just two eyes in the dark, blinking
        a.lurk = 0.0
        a.x = -16
        yield from self.go(lambda: (60, 476), speed=90)
        yield from self.wait(0.5, lambda k: setattr(a, "look", 1.0 if 0.2 < k < 0.6 else 0.0))

    def start_mimic(self, p):
        a = self.apex
        a.mimic_color, a.mimic_kind = p.color, p.mimic
        a.mimic = 0.0

    def pounce(self, p):
        a = self.apex
        self.start_mimic(p)

        def spot():
            x, y = p.pos()
            gx, gy = self.ground_spot(x, y)
            return gx + (-34 if a.x < x else 34), gy
        yield from self.go(spot, stalk=1.0, near=6)
        a.face = 1 if p.pos()[0] > a.x else -1
        # it flattens right down and quivers, gathering itself to spring
        yield from self.wait(0.5, lambda k: (setattr(a, "coil", ease(k * 3) * (1 - ease((k - 0.85) * 7))),
                                             setattr(a, "squash", 0.5 * ease(k * 2))))
        a.coil, a.crouch = 0.0, 0.2
        x0, y0 = a.x, a.y
        a.ground = y0

        def arc(k):
            tx, ty = p.pos()
            k = ease(k)
            a.x = x0 + (tx - x0) * k
            a.y = y0 + (ty + 2 - y0) * k - math.sin(k * math.pi) * (16 + max(0.0, y0 - ty) * 0.25)
            a.mouth = k
            a.squash = -0.6 * math.sin(k * math.pi)  # long and thin in the air
            a.stretch = 0.8
        yield from self.wait(0.32, arc)
        p.hide()
        a.mimic = 0.0
        a.held = p.color   # it has the animal in its mouth
        a.mouth = 0.4
        for i in range(6):
            self.bits.append(Drop(a.x, a.y - 4, self.floor(a.x, y0), self.rng.uniform(-60, 60), self.rng.uniform(-90, -30)))
        yield from self.wait(0.2, lambda k: setattr(a, "squash", 0.5 * (1 - k)))  # lands with a splat
        if a.y < y0 - 2:  # it was up the tree: drop back down
            y1 = a.y
            yield from self.wait(0.3, lambda k: setattr(a, "y", y1 + (y0 - y1) * k * k))
        a.y, a.ground = max(a.y, y0) if a.y < y0 else a.y, None
        yield from self.gulp(p.color)

    def shoot(self, p):
        a = self.apex
        self.start_mimic(p)
        px, py = p.pos()
        spot = self.ground_spot(px + self.rng.uniform(-40, 40), py + (150 if py < 400 or p.low else 0))
        yield from self.go(lambda: spot, stalk=0.6)
        a.face = 1 if px > a.x else -1
        yield from self.wait(0.35, lambda k: setattr(a, "puff", ease(k)))  # swells with goo
        hit = {}
        mx, my = a.mouth_at()
        self.bits.append(Glob(mx, my, p.pos, lambda t: hit.setdefault("t", t)))
        a.puff, a.mouth, a.lift, a.squash = 0.0, 1.0, 3.0, -0.4  # recoil hop
        yield from self.wait(0.15)
        a.lift, a.mouth, a.squash = 0.0, 0.0, 0.0
        while "t" not in hit:
            yield
        a.mimic = 0.0
        x, y = p.pos()
        c = Cocoon(p, hit["t"], max(y + 4, self.ground_spot(x, y + 120)[1]))
        self.bits.append(c)
        yield from self.eat(c)

    def eat(self, c):
        """Eat a cocoon: get within reach, open wide, flick the tongue out, reel it in."""
        a = self.apex
        while not c.landed:
            yield
        if math.dist((a.x, a.y), (c.x, c.floor)) > 60 or (a.y < OFFSET[1]) != (c.floor < OFFSET[1]):
            side = -34 if a.x < c.x else 34
            yield from self.go(lambda: self.ground_spot(c.x + side, c.floor), near=8)
        a.face = 1 if c.x > a.x else -1
        # it rears up and opens wide
        yield from self.wait(0.35, lambda k: (setattr(a, "mouth", max(a.mouth, ease(k))), setattr(a, "squash", -0.3 * ease(k))))
        # out goes the tongue...
        x0, y0 = a.mouth_at()
        yield from self.wait(0.15, lambda k: setattr(a, "tongue", (x0 + (c.x - x0) * ease(k), y0 + (c.y - y0) * ease(k))))
        yield from self.wait(0.12)
        # ...and in comes the cocoon, stretching as it goes
        cx0, cy0 = c.x, c.y

        def reel(k):
            mx, my = a.mouth_at()
            e = ease(k) ** 1.4
            c.x, c.y = cx0 + (mx - cx0) * e, cy0 + (my - cy0) * e - math.sin(k * math.pi) * 6
            c.size = 1 - 0.55 * e
            a.tongue = (c.x, c.y)
        yield from self.wait(0.5, reel)
        c.gone = True
        a.tongue = None
        a.held = mix(c.prey.color, GOO, 0.3)
        a.mouth = 0.0  # CHOMP
        a.squash = 0.4
        yield from self.wait(0.1)
        yield from self.gulp(c.prey.color)

    def gulp(self, color, chews=3, lump=True):
        """Chew, then swallow: you see it go down, a glowing lump in its belly (`lump`
        False: those went down already, this is just the chewing)."""
        a = self.apex
        a.crouch = a.coil = a.puff = 0.0
        if chews:
            yield from self.wait(0.22 * chews, lambda k: (setattr(a, "mouth", 0.55 * abs(math.sin(k * chews * math.pi))),
                                                          setattr(a, "squash", 0.25 * math.sin(k * chews * math.pi * 2))))
        a.mouth, a.held = 0.0, None
        if lump:
            a.lumps.append([self.t, color, self.rng.uniform(-0.45, 0.35), self.rng.uniform(-0.1, 0.45)])
        fat0 = a.fat if lump else a.fat - 0.075
        # a gulp ripples right through it, and it ends up a bit rounder
        yield from self.wait(0.35, lambda k: (setattr(a, "fat", min(2.6, fat0 + 0.075 * ease(k))),
                                              setattr(a, "squash", -0.3 * math.sin(k * math.pi * 2) * (1 - k))))
        a.squash = 0.0
        a.squint = 1.0
        if self.rng.random() < 0.35:
            mx, my = a.mouth_at()
            self.bits.append(Bubble(mx, my - 2, self.t))
        yield from self.wait(0.3)
        a.squint = 0.0

    def fishing(self, fish):
        """By the pond, disguised as a lily pad, its back to the water and a glowing bead
        of itself dangling in as bait. When a koi comes close it whips round and snaps."""
        a = self.apex
        w = self.lower.pond.water
        cx, cy = w.cx + OFFSET[0], w.cy + OFFSET[1]
        ang = math.atan2(a.y - cy, a.x - cx)
        edge = (cx + math.cos(ang) * (w.rx - 6), cy + math.sin(ang) * (w.ry - 6))
        self.start_mimic(fish[0])
        yield from self.go(lambda: edge, stalk=1.0)
        start = self.t
        while any(not f.eaten for f in fish):
            a.face = -1 if cx > a.x else 1  # back to the pond
            a.mimic += (1 - a.mimic) * min(1.0, self.dt * 3)
            a.crouch += (0.8 - a.crouch) * min(1.0, self.dt * 3)
            a.bait += (1 - a.bait) * min(1.0, self.dt * 3)
            bait = (a.x - a.face * 12, a.y + 4)
            for f in fish:
                if not f.eaten:
                    f.obj.lure(bait[0] - OFFSET[0], bait[1] - OFFSET[1])
            close = [f for f in fish if not f.eaten and math.dist(f.pos(), bait) < 22]
            if close:
                f = close[0]
                a.face = -a.face  # whips round
                a.bait = 0.0
                x0, fx = a.x, f.pos()[0]
                yield from self.wait(0.18, lambda k: (setattr(a, "x", x0 + (fx - x0) * 0.4 * math.sin(k * math.pi)),
                                                      setattr(a, "mouth", math.sin(k * math.pi)),
                                                      setattr(a, "stretch", 0.8)))
                f.hide()
                a.held = f.color
                x, y = f.pos()
                for i in range(4):
                    self.bits.append(Drop(x, y - 2, y + 1, self.rng.uniform(-40, 40), self.rng.uniform(-80, -40), life=1.2))
                yield from self.gulp(f.color, chews=1)
            elif self.t - start > 7:  # the shy ones get spat at instead
                a.bait = 0.0
                yield from self.volley([f for f in fish if not f.eaten])
                break
            yield
        a.mimic = a.bait = 0.0
        self.relax()

    def volley(self, rest):
        """Out of time: spit at them all in one breath, then one enormous breath in sucks
        every cocoon through the air into its mouth, gulp after gulp."""
        a = self.apex
        a.mimic = 0.0
        yield from self.wait(0.3, lambda k: setattr(a, "puff", ease(k)))
        cocoons = []
        for p in rest:
            mx, my = a.mouth_at()
            a.face = 1 if p.pos()[0] > a.x else -1

            def wrap(t, p=p):
                x, y = p.pos()
                c = Cocoon(p, t, max(y + 4, self.ground_spot(x, y + 120)[1]) if p.kind != "fish" else y + 1)
                cocoons.append(c)
                self.bits.append(c)
            self.bits.append(Glob(mx, my, p.pos, wrap, speed=520))
            a.mouth = 1.0
            yield from self.wait(0.22)
            a.mouth = 0.0
            yield
        a.puff = 0.0
        while any(isinstance(b, Glob) for b in self.bits):
            yield
        if not cocoons:
            return
        yield from self.wait(0.4)  # a moment to see them all wrapped up
        yield from self.wait(0.35, lambda k: (setattr(a, "mouth", ease(k)), setattr(a, "squash", -0.35 * ease(k))))
        for n, c in enumerate(sorted(cocoons, key=lambda c: math.dist((c.x, c.y), a.mouth_at()))):
            c.aim, c.v = a.mouth_at, -160.0 * n  # nearest first, the rest one after another
        waiting = list(cocoons)
        while waiting:
            for c in [c for c in waiting if c.gone]:  # in it goes: gulp
                waiting.remove(c)
                a.lumps.append([self.t, c.prey.color, self.rng.uniform(-0.45, 0.35), self.rng.uniform(-0.1, 0.45)])
                a.fat = min(2.6, a.fat + 0.075)
                a.squash = -0.1
            a.squash += (-0.35 - a.squash) * min(1.0, self.dt * 6)
            yield
        a.mouth = 0.0  # CHOMP
        yield from self.gulp(GOO, chews=4, lump=False)  # one big chew of the lot

    def fireflies(self):
        """Last, the fireflies: a quick spray of droplets sticks each one in a speck of
        goo, then one enormous breath in sucks them all into its mouth."""
        a = self.apex
        spot = self.ground_spot(480, 470)
        yield from self.go(lambda: spot)
        yield from self.wait(0.3, lambda k: setattr(a, "puff", ease(k)))
        morsels = []
        for si, (swarm, low) in enumerate(self.swarms):
            for i in range(len(swarm.items)):
                def where(swarm=swarm, i=i, low=low):
                    if i < len(swarm.now) and swarm.now[i][0] > -50:
                        x, y = swarm.now[i][:2]
                        return (x + OFFSET[0], y + OFFSET[1]) if low else (x, y)
                    return a.mouth_at()

                def stuck(t, k=(si, i), where=where, swarm=swarm):
                    self.firefly_out.setdefault(k, t)
                    x, y = where()
                    m = Morsel(x, y, swarm.color, a.mouth_at)
                    morsels.append(m)
                    self.bits.append(m)
                mx, my = a.mouth_at()
                a.face = 1 if where()[0] > a.x else -1
                self.bits.append(Glob(mx, my, where, stuck, speed=560, small=True))
                a.mouth = 1.0 if i % 2 else 0.5
                yield from self.wait(0.035)
        a.puff = a.mouth = 0.0
        while any(isinstance(b, Glob) for b in self.bits):
            yield
        yield from self.wait(0.5)  # a moment to see them all hanging there, stuck
        # the big breath in: it swells, mouth wide, and they all come streaming in
        yield from self.wait(0.4, lambda k: (setattr(a, "mouth", ease(k)), setattr(a, "squash", -0.35 * ease(k))))
        for n, m in enumerate(sorted(morsels, key=lambda m: math.dist((m.x, m.y), a.mouth_at()))):
            m.pull = True
            m.v = -40.0 * min(n, 12)  # nearest first, the rest close behind
        while any(not m.eaten for m in morsels):
            a.puff = min(1.0, a.puff + self.dt * 0.6)
            yield
        color = self.swarms[0][0].color if self.swarms else GOO
        a.held = color
        a.mouth = 0.0  # CHOMP
        yield from self.gulp(color)
        for _ in range(2):  # a few more little lights, settling in its belly
            a.lumps.append([self.t, color, self.rng.uniform(-0.5, 0.3), self.rng.uniform(0.0, 0.5)])

    def leave(self):
        """Full. It does not just walk away: it sighs, waddles, hiccups, flops down for a
        rest, heaves itself up, burps a huge bubble, winks back at you, and wobbles off."""
        a = self.apex
        self.relax()
        a.mimic = 0.0
        if a.y >= OFFSET[1]:
            left, right = OFFSET[0] - 24, OFFSET[0] + self.low_w + 24
        else:
            left, right = -30, 990
        exit_x = left if a.x - left < right - a.x else right
        y = a.y
        d = exit_x - a.x

        def sag(k):  # a deep breath in... and a long, contented sigh out
            a.squash = -0.35 * ease(k / 0.4) if k < 0.4 else -0.35 + 0.8 * ease((k - 0.4) / 0.6)
            a.squint = 1.0 if k > 0.4 else 0.0
        yield from self.wait(1.2, sag)
        yield from self.wait(0.3, lambda k: setattr(a, "squash", 0.45 * (1 - ease(k))))
        a.squint = 0.0
        a.waddle = 1.0
        x0 = a.x
        yield from self.go(lambda: (x0 + d * 0.3, y), speed=55, near=3)
        # hic! ... hic!
        for _ in range(2):
            def hic(k):
                a.lift = 6 * math.sin(k * math.pi)
                a.squash = -0.5 * math.sin(k * math.pi)
            yield from self.wait(0.25, hic)
            a.lift = a.squash = 0.0
            mx, my = a.mouth_at()
            self.bits.append(Bubble(mx, my - 3, self.t, size=1))
            yield from self.wait(0.55)
        yield from self.go(lambda: (x0 + d * 0.55, y), speed=55, near=3)
        # too full: it flops down for a rest, rocking gently
        a.waddle = 0.0
        yield from self.wait(0.3, lambda k: setattr(a, "squash", 0.65 * ease(k)))
        a.squint = 1.0
        yield from self.wait(1.1, lambda k: setattr(a, "sway", 0.35 * math.sin(k * math.tau * 1.5)))
        a.sway, a.squint = 0.0, 0.0
        # ...and heaves itself back up
        yield from self.wait(0.35, lambda k: setattr(a, "squash", 0.65 - 1.05 * ease(k)))
        yield from self.wait(0.2, lambda k: setattr(a, "squash", -0.4 * (1 - ease(k))))
        # an enormous burp
        a.face = 1 if d > 0 else -1
        yield from self.wait(0.25, lambda k: (setattr(a, "mouth", ease(k)), setattr(a, "squash", -0.3 * ease(k))))
        mx, my = a.mouth_at()
        self.bits.append(Bubble(mx, my - 4, self.t, size=5))
        yield from self.wait(0.5, lambda k: setattr(a, "squash", -0.3 + 0.5 * math.sin(k * math.pi)))
        a.mouth, a.squash = 0.0, 0.0
        a.squint = 1.0
        yield from self.wait(0.6)
        a.squint = 0.0
        # a look back at you, and a wink
        a.look, a.wink = 1.0, True
        yield from self.wait(1.0, lambda k: setattr(a, "sway", -0.15 * math.sin(k * math.pi)))
        a.look, a.wink, a.sway = 0.0, False, 0.0
        a.waddle = 1.0
        yield from self.go(lambda: (exit_x, y), speed=62, near=3)
        a.waddle = 0.0
        self.apex = None

    def respawn(self):
        """Within twenty seconds, everything comes back."""
        start = self.t
        when = [(self.rng.uniform(1.0, 16.0), p) for p in self.prey if p.eaten]
        for k in self.firefly_out:
            self.firefly_back[k] = start + self.rng.uniform(1.0, 16.0)
        when.sort(key=lambda w: w[0])
        for delay, p in when:
            while self.t - start < delay:
                yield
            self.bits.append(Sparkle(p, self.t))
        while self.t - start < 19.5 or self.bits:
            yield

    def run(self):
        yield from self.wait(1.4)  # the moon goes dark first
        yield from self.arrive()
        a = self.apex
        fish = [p for p in self.prey if p.kind == "fish"]
        rest = [p for p in self.prey if p.kind != "fish"]
        did_fish = not fish
        while rest or not did_fish:
            if self.t - self.t0 > TIME_LIMIT:
                yield from self.volley(rest + [f for f in fish if not f.eaten])
                rest, did_fish = [], True
                break
            # the nearest meal next; the pond counts as one stop
            options = [(math.dist((a.x, a.y), p.pos()), p) for p in rest]
            if not did_fish:
                w = self.lower.pond.water
                options.append((math.dist((a.x, a.y), (w.cx + OFFSET[0], w.cy + OFFSET[1])), None))
            _, p = min(options, key=lambda o: o[0])
            if p is None:
                yield from self.fishing(fish)
                did_fish = True
                continue
            rest.remove(p)
            if p.obj.__dict__.get("gone"):
                continue
            if p.kind == "fly":
                yield from self.shoot(p)
            else:
                yield from self.pounce(p)
        if self.swarms:
            yield from self.fireflies()
        yield from self.leave()
        yield from self.respawn()
        self.finish()

    # every frame --------------------------------------------------------------------
    def update(self, dt, t):
        self.dt, self.t = dt, t
        a = self.apex
        if a is not None:
            a.stretch *= 1 - min(1.0, dt * 6)   # it catches up with itself when it stops
        if not self.done and t - self.t0 > 120:  # whatever happened, never let it linger
            self.apex = None
            self.finish()
        if not self.done:
            try:
                next(self.script)
            except StopIteration:
                self.finish()
        self.bits = [b for b in self.bits if b.update(dt, t)]
        a = self.apex
        if a is not None and a.lurk < 1 and t > self.next_drip:  # it drips as it goes
            self.next_drip = t + self.rng.uniform(0.12, 0.3)
            bx, by = self.rng.choice(a.drips())
            self.bits.append(Drop(bx, by, self.floor(bx, a.y), self.rng.uniform(-6, 6), 0.0))
        if self.done:
            return
        # fireflies going out, and coming back
        for (si, i), t_out in self.firefly_out.items():
            swarm = self.swarms[si][0]
            back = self.firefly_back.get((si, i))
            m = 1 - ease((t - t_out) / 0.5)
            if back is not None and t > back:
                m = ease((t - back) / 2.0)
            swarm.mult[i] = m

    def finish(self):
        for p in self.prey:
            p.show()
        for swarm, _ in self.swarms:
            swarm.mult.clear()
        self.done = True

    def draw(self, s, low, t):
        ox, oy = OFFSET if low else (0, 0)
        for b in self.bits:
            b.draw(s, ox, oy, t)
        a = self.apex
        if a is not None:
            on_low = a.y >= OFFSET[1]
            if on_low == low:
                a.draw(s, ox, oy, t)


# --- listening for the word ------------------------------------------------------------

class Listener:
    """After a click on the moon: collects what is typed for a while."""

    LISTEN = 10.0

    def __init__(self):
        self.until = -1.0
        self.typed = ""
        self.heard_at = -99.0

    def start(self, t):
        self.until, self.typed = t + self.LISTEN, ""

    def listening(self, t):
        return t < self.until

    def key(self, ch, t):
        """Returns True when the word has just been typed."""
        if not self.listening(t):
            return False
        self.typed = (self.typed + ch.lower())[-len(WORD):]
        if self.typed == WORD:
            self.until, self.heard_at = -1.0, t
            return True
        return False

    def draw_moon(self, s, moon, t):
        """The moon's halo swells while it listens, and dims for a moment once it hears."""
        if moon is None:
            return
        x, y, r = moon
        if self.listening(t):
            k = 0.6 + 0.4 * math.sin(t * 2.2)
            glow(s, x, y, r * 3, (200, 210, 255), q(60 * k))
        k = swell(t - self.heard_at, 0.6, 1.6)
        if k > 0:
            # the moon goes dark for a moment
            pygame.draw.circle(s, mix((236, 236, 255), (20, 18, 50), k), (x, y), r)
