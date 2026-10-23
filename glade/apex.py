"""The apex — an easter egg.

Click the moon (its halo swells: it is listening) and type "apex". The moon dims, two
glowing eyes open at the edge of the dark, and something small, quick and very hungry
creeps in. In under a minute it hunts down every animal in the place and on the ground
below it, gets visibly rounder with each one, then waddles off the edge, full. Within
twenty seconds of it leaving, every animal glows gently back into being.

It looks like nothing real: a dark violet dumpling on four stubby feet, with enormous
eyes, a crest of three floppy feelers tipped with beads of fluorescent goo, and a short
tail ending in a glowing bulb. It drips that goo wherever it goes. Its ways:

- things in the air (squid): it puffs its cheeks and spits a homing glob of goo; the
  squid, wrapped in a glowing cocoon, drops to the ground and it gulps it down;
- things on the ground (slugs, snails, millipedes, the critter): it stalks in low, wiggles
  its rear like a cat, pounces and bites;
- the koi: it sits at the pond's edge disguised as a lily pad and dangles its glowing
  tail in the water as bait, then snaps up each fish that comes close;
- the fireflies, last: a quick spray of droplets that puts them out one by one.

While stalking it mimics its target like a cuttlefish: it takes on its colours in
rippling bands, half-closes its eyes, and grows a disguise to match — eye stalks for a
slug, dangling tendrils for a squid, ears for the critter, a lily-pad green by the pond.
After every kill it squints happily; sometimes it burps a little glowing bubble.

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
SKIN_HI = (104, 76, 146)
BELLY = (124, 98, 160)
EYE = (238, 255, 226)
LILY = (70, 150, 110)

TIME_LIMIT = 40               # after this, whatever is left is finished off in a volley
WORD = "apex"


def ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


# --- the animals it can eat ------------------------------------------------------------

class Prey:
    """One animal: where it is (shared coordinates), how to make it vanish and come back."""

    def __init__(self, obj, low, kind):
        self.obj, self.low, self.kind = obj, low, kind
        name = type(obj).__name__
        if kind == "fish":
            self.color = obj.colors[0]
        else:
            self.color = getattr(obj, "color", None) or getattr(obj, "body", None) or (200, 200, 220)
        self.mimic = {"Slug": "slug", "Millipede": "slug", "Critter": "ears", "Fish": "lily"}.get(name, "tendrils")
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
    """A squid wrapped in goo: it swells over the animal, then drops to the ground."""

    def __init__(self, prey, t, floor):
        self.prey, self.t0 = prey, t
        self.x, self.y = prey.pos()
        self.floor, self.vy = floor, 0.0
        self.landed = False
        self.eaten_at = None

    def update(self, dt, t):
        a = t - self.t0
        if a > 0.35 and not self.prey.eaten:
            self.prey.hide()  # covered by the goo by now
        if a > 0.5 and not self.landed:
            self.vy += 300 * dt
            self.y += self.vy * dt
            if self.y >= self.floor:
                self.y, self.landed = self.floor, True
        elif a <= 0.5:
            self.x, self.y = self.prey.pos() if not self.prey.eaten else (self.x, self.y)
        return self.eaten_at is None or t - self.eaten_at < 0.3

    def draw(self, s, ox, oy, t):
        a = t - self.t0
        r = 7 * ease(a / 0.35)
        if self.eaten_at is not None:
            r *= 1 - ease((t - self.eaten_at) / 0.3)
        if r < 0.5:
            return
        x, y = self.x - ox, self.y - oy
        pygame.draw.circle(s, mix(GOO, (40, 60, 40), 0.35), (round(x), round(y)), round(r))
        pygame.draw.circle(s, GOO, (round(x - r * 0.25), round(y - r * 0.25)), max(1, round(r * 0.6)))
        s.set_at((round(x - r * 0.4), round(y - r * 0.5)), (255, 255, 255))
        glow(s, x, y, int(r * 2.5) + 4, GOO, q(60 + 30 * math.sin(t * 6)))


class Bubble:
    """A little glowing burp that floats up, wobbling, and pops softly."""

    def __init__(self, x, y, t):
        self.x, self.y, self.t0 = x, y, t

    def update(self, dt, t):
        self.y -= 14 * dt
        return t - self.t0 < 1.6

    def draw(self, s, ox, oy, t):
        a = t - self.t0
        k = swell(a, 0.3, 1.3)
        x, y = self.x - ox + math.sin(a * 6) * 1.5, self.y - oy
        r = 2 + a
        pygame.draw.circle(s, mix((20, 30, 20), GOO, k), (round(x), round(y)), round(r), 1)
        s.set_at((round(x - 1), round(y - 1)), GOO_HI)
        glow(s, x, y, 6, GOO, q(50 * k))


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
    def __init__(self, x, y):
        self.x, self.y = x, y            # where its feet touch the ground
        self.face = 1                    # 1: looking right
        self.fat = 1.0
        self.crouch = 0.0                # 0..1, low and flat when stalking
        self.wiggle = 0.0                # 0..1, rear end wiggling before a pounce
        self.puff = 0.0                  # 0..1, cheeks full of goo
        self.mouth = 0.0                 # 0..1, how wide its mouth is open
        self.squint = 0.0                # 0..1, happy ^ ^ eyes
        self.mimic = 0.0                 # 0..1, how far into its disguise it is
        self.mimic_color, self.mimic_kind = SKIN, None
        self.lift = 0.0                  # height off the ground (leaps)
        self.gait = 0.0
        self.lurk = 0.0                  # 1: only its eyes show, in the dark
        self.look = 0.0                  # looking back over its shoulder
        self.waddle = 0.0
        self.ground = None               # while leaping: where the ground is, for its shadow

    def size(self):
        rx = 7 * self.fat * (1 + 0.15 * self.crouch)
        ry = 5 * (1 + (self.fat - 1) * 0.55) * (1 - 0.3 * self.crouch)
        return rx, ry

    def mouth_at(self):
        rx, ry = self.size()
        return self.x + self.face * rx * 0.9, self.y - self.lift - 2 - ry * 0.7

    def beads(self, t):
        """Where the three goo beads on its feelers hang (shared coordinates)."""
        rx, ry = self.size()
        cx, cy = self.x, self.y - self.lift - 2 - ry
        fold = 1 - 0.6 * self.mimic
        out = []
        for i in range(3):
            base = cx + self.face * (rx * 0.25 - i * 2.5)
            sway = math.sin(t * 3 + i * 1.7) * 1.5
            out.append((base - self.face * (4 + i * 2) * fold + sway, cy - ry - (5 - i) * fold + 2))
        return out

    def draw(self, s, ox, oy, t):
        f = self.face
        rx, ry = self.size()
        bob = abs(math.sin(self.gait * 0.5)) * 1.0 + math.sin(t * 9) * 0.6 * self.waddle
        x = self.x - ox + math.sin(t * 5) * 1.5 * self.waddle
        foot = self.y - oy - self.lift
        cy = foot - 2 - ry - bob
        lean = math.sin(t * 22) * 2.2 * self.wiggle  # the rear wiggles before a pounce
        if self.lurk >= 1:
            self.draw_eyes(s, x, cy, rx, ry, t, glow_only=True)
            return
        skin = mix(SKIN, mix(self.mimic_color, (20, 14, 40), 0.35), self.mimic)
        if self.mimic_kind == "lily":
            skin = mix(SKIN, LILY, self.mimic)
        hi = mix(skin, (255, 255, 255), 0.22)
        # shadow
        gy = (self.ground if self.ground is not None else self.y) - oy
        pygame.draw.ellipse(s, (10, 8, 20), (round(x - rx), round(gy - 1), round(rx * 2), 3))
        # tail with its glowing bulb
        tx, ty = x - f * rx + lean, cy + ry * 0.2
        sw = math.sin(t * 2.5) * 2
        pts = [(tx, ty), (tx - f * 4, ty - 2 + sw * 0.3), (tx - f * 7, ty - 5 + sw), (tx - f * 8, ty - 9 + sw)]
        pygame.draw.lines(s, INK, False, [(px, py + 1) for px, py in pts], 2)
        pygame.draw.lines(s, skin, False, pts, 2)
        bx, by = pts[-1]
        pygame.draw.circle(s, GOO, (round(bx), round(by)), 2)
        s.set_at((round(bx) - 1, round(by) - 1), GOO_HI)
        glow(s, bx, by, 8, GOO, 60)
        # four stubby feet
        for i, lx in enumerate((-0.6, -0.2, 0.2, 0.6)):
            up = max(0.0, math.sin(self.gait + i * math.pi)) * 1.5 if self.lift == 0 else 1.5
            fx = x + lx * rx + (lean if lx * f < 0 else 0)
            pygame.draw.rect(s, INK, (round(fx - 1), round(cy + ry - 1 - up), 3, 4))
            pygame.draw.rect(s, skin, (round(fx - 1), round(cy + ry - 1 - up), 2, 3))
        # body: an ink outline, the skin, a paler belly, a sheen
        body = pygame.Rect(0, 0, round(rx * 2), round(ry * 2))
        body.center = (round(x + lean * 0.4), round(cy))
        pygame.draw.ellipse(s, INK, body.inflate(2, 2))
        pygame.draw.ellipse(s, skin, body)
        belly = pygame.Rect(0, 0, round(rx * 1.3), round(ry * 0.9))
        belly.midbottom = (round(x + f * rx * 0.15), body.bottom - 1)
        pygame.draw.ellipse(s, mix(BELLY, skin, 0.5 * self.mimic), belly)
        pygame.draw.line(s, hi, (body.x + 3, body.y + 1), (body.right - 4, body.y + 1))
        # chromatophore bands, rippling over it as it shifts colour
        if self.mimic > 0.05:
            band = mix(self.mimic_color, (255, 255, 255), 0.2)
            for i in range(4):
                bxp = body.x + 1 + ((i * 5 + t * 14) % max(1, body.w - 2))
                h = ry * math.sqrt(max(0.0, 1 - ((bxp - body.centerx) / max(rx, 1)) ** 2))
                if h > 1:
                    c = mix(skin, band, self.mimic * (0.5 + 0.5 * math.sin(t * 7 + i)))
                    pygame.draw.line(s, c, (bxp, body.centery - h + 1), (bxp, body.centery + h - 2))
        # cheeks full of goo
        if self.puff > 0.05:
            pr = ry * 0.55 * self.puff
            pygame.draw.circle(s, INK, (round(x + f * rx * 0.75), round(cy + 1)), round(pr + 1))
            pygame.draw.circle(s, mix(skin, GOO, 0.25 * self.puff), (round(x + f * rx * 0.75), round(cy + 1)), round(pr))
        # disguises
        dk = ease((self.mimic - 0.4) / 0.6)
        if dk > 0:
            mc = mix(self.mimic_color, (255, 255, 255), 0.2)
            if self.mimic_kind == "slug":
                for dx in (0.45, 0.8):
                    sx = x + f * rx * dx
                    pygame.draw.line(s, mc, (sx, body.y + 1), (sx + f, body.y - 4 * dk))
                    s.set_at((round(sx + f), round(body.y - 4 * dk)), (255, 255, 255))
            elif self.mimic_kind == "ears":
                for dx in (0.3, 0.75):
                    ex = x + f * rx * dx
                    pygame.draw.polygon(s, mc, [(ex - 2, body.y + 2), (ex + 2, body.y + 2), (ex, body.y - 4 * dk)])
            elif self.mimic_kind == "tendrils":
                for i in range(3):
                    tx0 = x + f * rx * (0.2 + i * 0.25)
                    pygame.draw.line(s, mc, (tx0, body.bottom - 1),
                                     (tx0 + math.sin(t * 4 + i) * 2, body.bottom + 4 * dk))
        # the crest: three floppy feelers, each tipped with a bead of goo
        top = (x + f * rx * 0.25, cy - ry + 1)
        for i, (bx_, by_) in enumerate(self.beads(t)):
            bx_, by_ = bx_ - ox, by_ - oy
            mid = ((top[0] + bx_) / 2 + f, min(top[1], by_) - 3)
            pygame.draw.lines(s, skin if i else hi, False, [top, mid, (bx_, by_)])
            pygame.draw.circle(s, GOO, (round(bx_), round(by_)), 1)
            glow(s, bx_, by_, 5, GOO, 48)
        self.draw_eyes(s, x, cy, rx, ry, t)
        # mouth
        mx, my = x + f * rx * 0.88, cy + ry * 0.3
        if self.mouth > 0.08:
            o = 2 + 5 * self.mouth
            pygame.draw.polygon(s, INK, [(mx - f * 3, my), (mx + f * 2, my - o * 0.5), (mx + f * 2, my + o * 0.5)])
            s.set_at((round(mx), round(my - o * 0.4)), (255, 255, 255))   # tiny teeth
            s.set_at((round(mx + f), round(my - o * 0.4)), (255, 255, 255))
            s.set_at((round(mx), round(my + o * 0.4)), (255, 255, 255))
            pygame.draw.line(s, GOO, (mx, my - o * 0.3), (mx - f, my + o * 0.3))
        else:
            pygame.draw.line(s, INK, (mx - f * 2, my), (mx, my + 1))

    def draw_eyes(self, s, x, cy, rx, ry, t, glow_only=False):
        f = self.face if self.look < 0.5 else -self.face
        blink = (t % 3.7) < 0.12
        for i, (dx, r) in enumerate(((0.38, 2), (0.72, 2))):
            ex, ey = round(x + f * rx * dx), round(cy - ry * 0.25)
            glow(s, ex, ey, 5, GOO, 36 if not glow_only else q(70 * min(1.0, self.lurk)))
            if glow_only:
                if not blink:
                    s.set_at((ex, ey), GOO_HI)
                continue
            if blink or self.squint > 0.5:
                pts = [(ex - 2, ey), (ex, ey - 2), (ex + 2, ey)] if self.squint > 0.5 else [(ex - 2, ey), (ex + 2, ey)]
                pygame.draw.lines(s, INK, False, pts, 1)
                continue
            pygame.draw.circle(s, INK, (ex, ey), r + 1)
            pygame.draw.circle(s, EYE, (ex, ey), r)
            pygame.draw.rect(s, INK, (ex + (f > 0), ey - 1, 1, 3))  # pupil, looking ahead
            s.set_at((ex - 1, ey - 1), (255, 255, 255))
            if self.mimic > 0.5:  # half-closed: innocent
                pygame.draw.line(s, mix(SKIN, self.mimic_color, self.mimic), (ex - 2, ey - 2), (ex + 2, ey - 2))
                pygame.draw.line(s, mix(SKIN, self.mimic_color, self.mimic), (ex - 2, ey - 1), (ex + 2, ey - 1))


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
        self.apex.lurk = 0.0
        self.firefly_out = {}   # (swarm index, firefly index) -> time it was put out
        self.firefly_back = {}  # same -> time it starts coming back
        self.done = False
        self.target = None      # what it is going after right now (for the camera)
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
        """Scurry toward aim() in quick bursts; when stalking, the last stretch is slow,
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
            v = speed * (0.55 + 0.45 * abs(math.sin(self.t * 5.5)))
            if stalk and d < 70:
                v = 90
                a.crouch += (1 - a.crouch) * min(1.0, self.dt * 4)
                a.mimic += (stalk - a.mimic) * min(1.0, self.dt * 2.5)
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
        a.crouch, a.wiggle, a.puff, a.mouth = 0.0, 0.0, 0.0, 0.0

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
        self.target = p
        self.start_mimic(p)

        def spot():
            x, y = p.pos()
            gx, gy = self.ground_spot(x, y)
            return gx + (-34 if a.x < x else 34), gy
        yield from self.go(spot, stalk=1.0, near=6)
        a.face = 1 if p.pos()[0] > a.x else -1
        # the rear end wiggles, like a cat about to spring
        yield from self.wait(0.45, lambda k: setattr(a, "wiggle", ease(k * 3) * (1 - ease((k - 0.8) * 5))))
        a.wiggle, a.crouch = 0.0, 0.3
        x0, y0 = a.x, a.y
        a.ground = y0

        def arc(k):
            tx, ty = p.pos()
            k = ease(k)
            a.x = x0 + (tx - x0) * k
            a.y = y0 + (ty + 2 - y0) * k - math.sin(k * math.pi) * (16 + max(0.0, y0 - ty) * 0.25)
            a.mouth = k
        yield from self.wait(0.32, arc)
        p.hide()
        a.mimic = 0.0
        for i in range(6):
            self.bits.append(Drop(a.x, a.y - 4, self.floor(a.x, y0), self.rng.uniform(-60, 60), self.rng.uniform(-90, -30)))
        yield from self.wait(0.45, lambda k: setattr(a, "mouth", abs(math.sin(k * math.pi * 2))))
        if a.y < y0 - 2:  # it was up the tree: drop back down
            y1 = a.y
            yield from self.wait(0.3, lambda k: setattr(a, "y", y1 + (y0 - y1) * k * k))
        a.y, a.ground = max(a.y, y0) if a.y < y0 else a.y, None
        yield from self.gulp()

    def shoot(self, p):
        a = self.apex
        self.target = p
        self.start_mimic(p)
        px, py = p.pos()
        spot = self.ground_spot(px + self.rng.uniform(-40, 40), py + (150 if py < 400 or p.low else 0))
        yield from self.go(lambda: spot, stalk=0.6)
        a.face = 1 if px > a.x else -1
        yield from self.wait(0.3, lambda k: setattr(a, "puff", ease(k)))
        hit = {}
        mx, my = a.mouth_at()
        self.bits.append(Glob(mx, my, p.pos, lambda t: hit.setdefault("t", t)))
        a.puff, a.mouth, a.lift = 0.0, 1.0, 3.0  # recoil hop
        yield from self.wait(0.15)
        a.lift, a.mouth = 0.0, 0.0
        while "t" not in hit:
            yield
        a.mimic = 0.0
        x, y = p.pos()
        c = Cocoon(p, hit["t"], max(y + 4, self.ground_spot(x, y + 120)[1]))
        self.bits.append(c)
        yield from self.wait(0.2)
        side = -8 if a.x < c.x else 8
        yield from self.go(lambda: self.ground_spot(c.x + side, c.floor), near=8)
        while not c.landed:
            yield
        yield from self.wait(0.25, lambda k: setattr(a, "mouth", ease(k)))
        c.eaten_at = self.t
        yield from self.gulp()

    def gulp(self):
        a = self.apex
        self.target = None
        a.mouth = 0.0
        self.relax()
        yield from self.wait(0.2, lambda k: setattr(a, "fat", min(2.6, a.fat + 0.075 * self.dt / 0.2)))
        a.squint = 1.0
        if self.rng.random() < 0.35:
            mx, my = a.mouth_at()
            self.bits.append(Bubble(mx, my - 2, self.t))
        yield from self.wait(0.3)
        a.squint = 0.0

    def fishing(self, fish):
        """By the pond, disguised as a lily pad, its back to the water and its glowing
        tail dangling in as bait. When a koi comes close it whips round and snaps."""
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
            bait = (a.x - a.face * 12, a.y + 4)
            for f in fish:
                if not f.eaten:
                    f.obj.lure(bait[0] - OFFSET[0], bait[1] - OFFSET[1])
            close = [f for f in fish if not f.eaten and math.dist(f.pos(), bait) < 22]
            if close:
                f = close[0]
                a.face = -a.face  # whips round
                x0, fx = a.x, f.pos()[0]
                yield from self.wait(0.18, lambda k: (setattr(a, "x", x0 + (fx - x0) * 0.4 * math.sin(k * math.pi)),
                                                      setattr(a, "mouth", math.sin(k * math.pi))))
                f.hide()
                x, y = f.pos()
                for i in range(4):
                    self.bits.append(Drop(x, y - 2, y + 1, self.rng.uniform(-40, 40), self.rng.uniform(-80, -40), life=1.2))
                a.fat = min(2.6, a.fat + 0.06)
                a.squint = 1.0
                yield from self.wait(0.25)
                a.squint = 0.0
            elif self.t - start > 7:  # the shy ones get spat at instead
                yield from self.volley([f for f in fish if not f.eaten])
                break
            yield
        a.mimic = 0.0
        yield from self.gulp()

    def volley(self, rest):
        """Out of time: finish them all in one breath."""
        a = self.apex
        a.mimic = 0.0
        yield from self.wait(0.3, lambda k: setattr(a, "puff", ease(k)))
        for p in rest:
            mx, my = a.mouth_at()
            a.face = 1 if p.pos()[0] > a.x else -1

            def splat(t, p=p):
                p.hide()
                x, y = p.pos()
                for i in range(5):
                    self.bits.append(Drop(x, y, self.ground_spot(x, y)[1] if y < 400 else y + 2,
                                          self.rng.uniform(-50, 50), self.rng.uniform(-60, 0)))
            self.bits.append(Glob(mx, my, p.pos, splat, speed=520))
            a.mouth = 1.0
            yield from self.wait(0.22)
            a.mouth = 0.0
            yield
        a.puff = 0.0
        while any(isinstance(b, Glob) for b in self.bits):
            yield
        a.fat += 0.05 * len(rest)
        yield from self.gulp()

    def fireflies(self):
        """Last, the fireflies: a quick spray of droplets, putting them out one by one."""
        a = self.apex
        spot = self.ground_spot(480, 470)
        yield from self.go(lambda: spot)
        yield from self.wait(0.3, lambda k: setattr(a, "puff", ease(k)))
        for si, (swarm, low) in enumerate(self.swarms):
            for i in range(len(swarm.items)):
                def where(swarm=swarm, i=i, low=low):
                    if i < len(swarm.now) and swarm.now[i][0] > -50:
                        x, y = swarm.now[i][:2]
                        return (x + OFFSET[0], y + OFFSET[1]) if low else (x, y)
                    return a.mouth_at()
                mx, my = a.mouth_at()
                a.face = 1 if where()[0] > a.x else -1
                self.bits.append(Glob(mx, my, where, lambda t, k=(si, i): self.firefly_out.setdefault(k, t),
                                      speed=560, small=True))
                a.mouth = 1.0 if i % 2 else 0.5
                yield from self.wait(0.05)
        a.puff = a.mouth = 0.0
        while any(isinstance(b, Glob) for b in self.bits):
            yield
        yield from self.gulp()

    def leave(self):
        """Full. It waddles off the nearest side, glancing back once on the way."""
        a = self.apex
        self.relax()
        a.mimic = 0.0
        a.waddle = 1.0
        if a.y >= OFFSET[1]:
            left, right = OFFSET[0] - 24, OFFSET[0] + self.low_w + 24
        else:
            left, right = -30, 990
        exit_x = left if a.x - left < right - a.x else right
        y, half = a.y, (a.x + exit_x) / 2
        yield from self.go(lambda: (half, y), speed=55, near=3)
        a.squint = 1.0  # a smug look back
        yield from self.wait(0.9, lambda k: setattr(a, "look", 1.0 if k < 0.8 else 0.0))
        a.squint = 0.0
        yield from self.go(lambda: (exit_x, y), speed=55, near=3)
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
            bx, by = self.rng.choice(a.beads(t) + [(a.x, a.y - 2 - a.lift)])
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

    def focus(self, low):
        """What the camera on one screen should keep in frame: the creature, whatever it
        is after, and any goo on its way there — so a long-range kill is never missed.
        In that screen's own coordinates; empty if nothing is happening there."""
        a = self.apex
        if a is None:
            return []
        on_low = a.y >= OFFSET[1]
        if on_low != low:
            return []
        ox, oy = OFFSET if low else (0, 0)
        pts = [(a.x, a.y - 2 - a.lift), (a.x, a.y - 28 - a.lift)]  # its feet, the tip of its crest
        if self.target is not None and not self.target.eaten:
            pts.append(self.target.pos())
        for b in self.bits:
            if isinstance(b, (Glob, Cocoon)):
                pts.append((b.x, b.y))
            if isinstance(b, Glob):
                pts.append(b.aim())  # and where it is going
        return [(x - ox, y - oy) for x, y in pts if (y >= OFFSET[1]) == low]

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
