"""The second wave of the glade's animals (see battle.py for what they are in a battle).

Two kinds of mover, each drawing one of several animals:
- `Flier`: Dusk Bat, Lantern Moth, Glimmer Drake (a dragonfly) and Mist Wisp, roaming a
  patch of sky;
- `Walker`: Brawl Toad, Moss Mole, Sporeling (a walking mushroom), Rime Newt and
  Copper Beetle, wandering along the ground.
Plus `owlet()`, which draws a Moon Owlet where a tree squid would be (squids.py): the
trees' other dwellers, holding the app icons in their talons.

They are not all out at once: a place's animals take turns (storm.py), so most of these
start hidden (`gone`) until a thunderstorm brings them out.
"""

import math

import pygame

from art import GLOW, glow, mix
from life import Clock, q, swell

INK = (24, 16, 50)


def ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


# --- in the air -------------------------------------------------------------------------

FLIERS = dict(
    bat=dict(species="Dusk Bat", body=(86, 64, 128), color=(255, 120, 190), speed=80, turn=0.9),
    moth=dict(species="Lantern Moth", body=(250, 214, 170), color=GLOW["amber"], speed=34, turn=1.6),
    drake=dict(species="Glimmer Drake", body=(110, 220, 210), color=GLOW["cyan"], speed=110, turn=1.2),
    wisp=dict(species="Mist Wisp", body=(214, 220, 255), color=(170, 190, 255), speed=16, turn=4.0),
)


class Flier(Clock):
    """Something small that roams a patch of sky (x, y, w, h): a bat flits about in quick
    jinks, a moth flutters, a dragonfly darts and hovers, a wisp drifts. Click it and it
    darts away."""

    def __init__(self, rng, region, kind, size=1.0):
        spec = FLIERS[kind]
        self.rng, self.region, self.kind, self.size = rng, region, kind, size
        self.species, self.body, self.color = spec["species"], spec["body"], spec["color"]
        self.speed, self.every = spec["speed"], spec["turn"]
        x0, y0, w, h = region
        self.x, self.y = x0 + rng.random() * w, y0 + rng.random() * h
        self.vx, self.vy = 0.0, 0.0
        self.target, self.next = self.pick(), 0.0
        self.hover = 0.0
        self.facing = 1
        self.phase = rng.random() * 10
        self.trail = [(self.x, self.y)] * 8
        self.poked = -10.0

    def pick(self):
        x0, y0, w, h = self.region
        return x0 + self.rng.random() * w, y0 + self.rng.random() * h

    def poke(self, x, y, t):
        if abs(x - self.x) > 14 * self.size or abs(y - self.y) > 12 * self.size:
            return False
        dx, dy = self.x - x, self.y - y
        d = math.hypot(dx, dy) or 1
        self.vx += dx / d * self.speed * 1.5
        self.vy += dy / d * self.speed * 1.5 - 20
        self.target, self.poked = self.pick(), t
        return True

    def update(self, dt, t):
        tx, ty = self.target
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy) or 1
        self.next -= dt
        if self.kind == "drake" and self.hover > 0:  # hovering, wings a blur, then a dart
            self.hover -= dt
            self.vx *= 1 - min(1.0, dt * 6)
            self.vy *= 1 - min(1.0, dt * 6)
        else:
            acc = self.speed * (3 if self.kind != "wisp" else 1)
            self.vx += dx / d * acc * dt
            self.vy += dy / d * acc * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > self.speed:
                self.vx, self.vy = self.vx / sp * self.speed, self.vy / sp * self.speed
            if self.kind == "moth":  # fluttering: it never goes quite straight
                self.vy += math.sin(t * 7 + self.phase) * 40 * dt
            if self.kind == "bat" and self.rng.random() < dt * 1.5:  # sudden jinks
                self.vx += self.rng.uniform(-60, 60)
                self.vy += self.rng.uniform(-40, 40)
        if d < 10 or self.next <= 0:
            self.target, self.next = self.pick(), self.every * self.rng.uniform(1.5, 4)
            if self.kind == "drake":
                self.hover = self.rng.uniform(0.6, 2.0)
        self.x += self.vx * dt
        self.y += self.vy * dt
        if abs(self.vx) > 4:
            self.facing = 1 if self.vx > 0 else -1
        self.trail = [(self.x, self.y)] + self.trail[:7]

    def draw(self, s, t):
        self.update(self.tick(t), t)
        getattr(self, "draw_" + self.kind)(s, t)

    # the bat: a velvet body, pointed ears, wings that beat fast
    def draw_bat(self, s, t):
        z, x, y = self.size, self.x, self.y
        beat = math.sin(t * 16 + self.phase)
        for side in (-1, 1):
            tip = (x + side * 13 * z, y - 7 * z * beat)
            elbow = (x + side * 7 * z, y - 4 * z * beat - 2 * z)
            pts = [(x + side * 2 * z, y - 2 * z), elbow, tip, (x + side * 10 * z, y + 2 * z),
                   (x + side * 6 * z, y + 1 * z), (x + side * 3 * z, y + 3 * z)]
            pygame.draw.polygon(s, mix(self.body, INK, 0.35), pts)
            pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.25), (x + side * 2 * z, y - 2 * z), elbow)
            pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.25), elbow, tip)
        pygame.draw.ellipse(s, self.body, (x - 4 * z, y - 4 * z, 8 * z, 8 * z))
        pygame.draw.ellipse(s, mix(self.body, (255, 220, 240), 0.3), (x - 2 * z, y, 4 * z, 3 * z))
        for ex in (-2, 2):
            pygame.draw.polygon(s, self.body, [(x + ex * z - 1.5 * z, y - 3 * z), (x + ex * z + 1.5 * z, y - 3 * z),
                                               (x + ex * z * 1.5, y - 8 * z)])

    # the moth: four soft wings with eye-spots, a furry body
    def draw_moth(self, s, t):
        z, x, y = self.size, self.x, self.y
        open_ = 0.35 + 0.65 * abs(math.cos(t * 9 + self.phase))
        wing = mix(self.body, (255, 170, 110), 0.35)
        for side in (-1, 1):
            w1 = 10 * z * open_
            pygame.draw.ellipse(s, wing, (x + (0 if side > 0 else -w1), y - 8 * z, w1, 9 * z))
            w2 = 7 * z * open_
            pygame.draw.ellipse(s, mix(wing, INK, 0.2), (x + (0 if side > 0 else -w2), y - 1 * z, w2, 6 * z))
        pygame.draw.ellipse(s, self.body, (x - 2 * z, y - 5 * z, 4 * z, 10 * z))
        for side in (-1, 1):  # feathery antennae
            pygame.draw.line(s, mix(self.body, INK, 0.3), (x, y - 5 * z), (x + side * 4 * z, y - 10 * z))

    # the dragonfly: a long glinting body and four wings, a blur when it hovers
    def draw_drake(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        bob = math.sin(t * 3 + self.phase) * z
        for i in range(9):  # the tail, behind the head
            px = x - f * (4 + i * 2.2) * z
            col = mix(self.body, (150, 110, 255), i / 9)
            pygame.draw.circle(s, col, (round(px), round(y + bob * i / 9)), max(1, round((1.6 - i * 0.08) * z)))
        pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round(2.6 * z)))
        s.set_at((round(x + f * z), round(y - z)), (255, 255, 255))
        blur = self.hover > 0 or (t * 30) % 2 < 1
        wing = mix(self.body, (255, 255, 255), 0.7)
        for k, ln in ((1, 9), (3, 8)):
            for up in (-1, 1):
                end = (x - f * k * z + (2 * f * z if blur else 0), y + up * (3 if blur else 2) * z - ln * z * (0.6 if up < 0 else -0.2))
                pygame.draw.line(s, wing, (x - f * k * z, y - z), end)

    # the wisp: a ghostly little flame with a tail of mist; it is almost all light
    def draw_wisp(self, s, t):
        pass  # all of it shines (below)

    def light(self, lm, t):
        if self.kind in ("moth", "wisp", "drake"):
            glow(lm, self.x, self.y, int(30 * self.size), self.color, q(60 + 20 * math.sin(t * 2 + self.phase)))

    def shine(self, s, t):
        z, x, y = self.size, self.x, self.y
        k = swell(t - self.poked, 0.1, 0.6)
        if self.kind == "bat":
            for ex in (-1.5, 1.5):  # little glowing eyes
                s.set_at((round(x + ex * z), round(y - 1 * z)), self.color)
        elif self.kind == "moth":
            glow(s, x, y, int(10 * z), self.color, q(70 + 50 * k))
            for side in (-1, 1):  # eye-spots on the wings glow like embers
                s.set_at((round(x + side * 5 * z), round(y - 4 * z)), (255, 210, 120))
        elif self.kind == "drake":
            tx = x - self.facing * 22 * z
            glow(s, tx, y, int(6 * z), self.color, q(90 + 60 * k))
        else:  # the wisp
            flick = 0.75 + 0.25 * math.sin(t * 11 + self.phase) * math.sin(t * 7.3)
            for i, (px, py) in enumerate(self.trail[::-1]):
                r = max(1, round((1 + i * 0.6) * z))
                c = mix(self.color, (60, 60, 140), 1 - i / 8)
                pygame.draw.circle(s, c, (round(px), round(py - i * 0.4)), r)
            glow(s, x, y, int(16 * z), self.color, q(90 * flick + 60 * k))
            pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round(5 * z)))
            pygame.draw.circle(s, (255, 255, 255), (round(x - z), round(y - 2 * z)), max(1, round(2 * z)))
            for ex in (-2, 2):
                s.set_at((round(x + ex * z), round(y)), INK)


# --- on the ground ----------------------------------------------------------------------

WALKERS = dict(
    toad=dict(species="Brawl Toad", body=(96, 176, 128), color=(255, 120, 110), speed=26),
    mole=dict(species="Moss Mole", body=(96, 76, 120), color=(255, 150, 200), speed=12),
    sporeling=dict(species="Sporeling", body=(240, 232, 214), color=(200, 140, 255), speed=10),
    newt=dict(species="Rime Newt", body=(150, 210, 245), color=(200, 245, 255), speed=14),
    beetle=dict(species="Copper Beetle", body=(214, 128, 78), color=(255, 236, 120), speed=9),
)


class Walker(Clock):
    """Something that wanders along the ground `ground(x)` between x_range: a toad in
    hops, a mole that never strays far from its hole, a waddling mushroom, a newt with a
    long wriggling tail, a beetle on six busy legs. Click it and it reacts."""

    def __init__(self, rng, ground, x_range, kind, size=1.0):
        spec = WALKERS[kind]
        self.rng, self.ground, self.xr, self.kind, self.size = rng, ground, x_range, kind, size
        self.species, self.body, self.color, self.speed = spec["species"], spec["body"], spec["color"], spec["speed"]
        self.x = rng.uniform(*x_range)
        self.y = ground(self.x)
        self.home = self.x  # the mole's hole
        if kind == "mole":
            self.xr = (self.home - 10 * size, self.home + 10 * size)  # never far from its hole
        self.target, self.wait = self.x, rng.uniform(0.5, 3)
        self.facing = rng.choice((-1, 1))
        self.step, self.hop, self.lift = 0.0, 0.0, 0.0
        self.phase = rng.random() * 10
        self.poked = -10.0
        self.tail = [(self.x - self.facing * i * 3 * size, self.y) for i in range(10)]

    def poke(self, x, y, t):
        if abs(x - self.x) > 14 * self.size or not -16 * self.size < y - self.y < 6 * self.size:
            return False
        self.poked = t
        if self.kind == "toad":
            self.hop = 0.01
        return True

    def update(self, dt, t):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.target = self.rng.uniform(*self.xr)
        else:
            d = self.target - self.x
            if abs(d) < 2:
                self.wait = self.rng.uniform(1.5, 6)
            else:
                self.facing = 1 if d > 0 else -1
                if self.kind == "toad":  # it gets about in hops
                    if self.hop <= 0:
                        self.hop = 0.01
                else:
                    self.x += self.facing * self.speed * self.size * dt
                    self.step += dt * (14 if self.kind == "beetle" else 8)
        if self.hop > 0:
            self.hop += dt / 0.45
            if self.kind == "toad" and self.wait <= 0:
                self.x += self.facing * 40 * self.size * dt
            self.lift = math.sin(min(1.0, self.hop) * math.pi) * 9 * self.size
            if self.hop >= 1:
                self.hop, self.lift = 0.0, 0.0
        self.y = self.ground(self.x) - self.lift
        # the newt's tail follows its body
        self.tail[0] = (self.x, self.y)
        seg = 3 * self.size
        for i in range(1, len(self.tail)):
            px, py = self.tail[i - 1]
            x, y = self.tail[i]
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy) or 1
            x, y = px + dx / d * seg, py + dy / d * seg
            self.tail[i] = (x, min(y, self.ground(x)))

    def draw(self, s, t):
        self.update(self.tick(t), t)
        getattr(self, "draw_" + self.kind)(s, t)

    def eyes(self, s, x, y, gap, r=1):
        blink = (self.phase * 3 + getattr(self, "_t", 0.0)) % 5 < 0.12  # every few seconds
        for ex in (x, x + gap):
            if blink:
                pygame.draw.line(s, INK, (round(ex) - r, round(y)), (round(ex) + r, round(y)))
            else:
                pygame.draw.rect(s, INK, (round(ex) - r // 2, round(y) - r // 2, r + 1, r + 1))
                s.set_at((round(ex), round(y) - r // 2), (255, 255, 255))

    # the toad: squat and warty, a little red band round its head (it is a fighter)
    def draw_toad(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        legs = 1 if self.hop > 0 else 0
        dark = mix(self.body, INK, 0.35)
        pygame.draw.line(s, dark, (x - f * 5 * z, y - 2 * z), (x - f * (9 + 5 * legs) * z, y + legs * 2 * z), 2)
        pygame.draw.ellipse(s, dark, (x - 8 * z, y - 9 * z + 1, 16 * z, 10 * z))
        pygame.draw.ellipse(s, self.body, (x - 8 * z, y - 10 * z, 16 * z, 10 * z))
        pygame.draw.ellipse(s, mix(self.body, (255, 250, 220), 0.45), (x - 5 * z + f * 2 * z, y - 4 * z, 9 * z, 4 * z))
        for wx, wy in ((-4, -7), (1, -8), (-1, -5)):
            s.set_at((round(x + wx * z * f), round(y + wy * z)), dark)
        hx = x + f * 4 * z
        for ex in (-2, 2):  # eye bumps
            pygame.draw.circle(s, self.body, (round(hx + ex * z), round(y - 10 * z)), max(2, round(2.4 * z)))
            pygame.draw.circle(s, (255, 214, 110), (round(hx + ex * z), round(y - 10 * z)), max(1, round(1.4 * z)))
            s.set_at((round(hx + ex * z), round(y - 10 * z)), INK)
        pygame.draw.line(s, (230, 80, 90), (hx - 4 * z, y - 8 * z), (hx + 4 * z, y - 8 * z), max(1, round(z)))
        pygame.draw.line(s, (230, 80, 90), (hx - f * 4 * z, y - 8 * z), (hx - f * 7 * z, y - 6 * z), 1)
        pygame.draw.line(s, dark, (hx + f * z, y - 5 * z), (hx + f * 4 * z, y - 5 * z))

    # the mole: velvet, with a pink star of a nose that glows, by its hole
    def draw_mole(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        hx, hy = self.home, self.ground(self.home)
        pygame.draw.ellipse(s, (146, 112, 132), (hx - 11 * z, hy - 4 * z, 22 * z, 8 * z))  # its hole: a mound of earth
        pygame.draw.ellipse(s, (110, 84, 108), (hx - 9 * z, hy - 3 * z, 18 * z, 6 * z))
        pygame.draw.ellipse(s, (20, 12, 28), (hx - 6 * z, hy - 2 * z, 12 * z, 4 * z))
        duck = swell(t - self.poked, 0.15, 1.6)  # poked: it ducks low
        y += duck * 4 * z
        pygame.draw.ellipse(s, mix(self.body, INK, 0.3), (x - 8 * z, y - 8 * z + 1, 16 * z, 9 * z))
        pygame.draw.ellipse(s, self.body, (x - 8 * z, y - 9 * z, 16 * z, 9 * z))
        pygame.draw.ellipse(s, mix(self.body, (255, 255, 255), 0.25), (x - 5 * z, y - 8 * z, 8 * z, 3 * z))
        for c in (-1, 1):  # big digging claws
            cx = x + f * 6 * z + c * 2 * z
            pygame.draw.line(s, (236, 220, 230), (cx, y - 1 * z), (cx + f * 2 * z, y), 1)
        s.set_at((round(x + f * 4 * z), round(y - 6 * z)), INK)

    # the sporeling: a mushroom cap on a little stem, waddling, its spots aglow
    def draw_sporeling(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        tilt = math.sin(self.step) * 1.5 * z if moving else 0
        for k in (0, math.pi):  # feet
            lift = max(0.0, math.sin(self.step + k)) * 2 * z if moving else 0
            pygame.draw.rect(s, mix(self.body, INK, 0.3), (x - 2 * z + (2 * z if k else -2 * z), y - 2 * z - lift, 3 * z, 2 * z))
        pygame.draw.rect(s, self.body, (x - 3 * z, y - 10 * z, 6 * z, 9 * z), border_radius=max(1, round(2 * z)))
        cap = [(x - 9 * z + tilt, y - 9 * z), (x + 9 * z + tilt, y - 9 * z)]
        pygame.draw.ellipse(s, mix(self.color, INK, 0.35), (cap[0][0], y - 17 * z + 1, 18 * z, 10 * z))
        pygame.draw.ellipse(s, mix(self.color, (255, 255, 255), 0.15), (cap[0][0], y - 17 * z, 18 * z, 10 * z))
        pygame.draw.line(s, mix(self.color, INK, 0.5), cap[0], cap[1])
        self.eyes(s, x - 1.5 * z + f * z, y - 6 * z, 3 * z)

    # the newt: an icy-blue body and long tail, a pale belly, frost spikes down its back,
    # four little legs and a round head with a bright eye
    def draw_newt(self, s, t):
        z, f, pts = self.size, self.facing, self.tail
        dark = mix(self.body, INK, 0.4)
        belly = mix(self.body, (255, 255, 255), 0.5)
        radii = [3.0, 3.4, 3.3, 3.0, 2.6, 2.1, 1.7, 1.3, 1.0, 0.8]
        w = max(1, round(z))
        for i in (1, 4):  # legs, bent at the knee
            px, py = pts[i]
            step = math.sin(self.step + i * 1.7) * 2 * z if self.wait <= 0 else 0
            knee = (px + f * z + step, py - z)
            pygame.draw.line(s, dark, (px, py - 2 * z), knee, w)
            pygame.draw.line(s, dark, knee, (knee[0] + f * 1.5 * z, py + 0.5 * z), w)
        for i, (px, py) in reversed(list(enumerate(pts))):
            r = max(1, radii[i] * z)
            pygame.draw.circle(s, dark, (round(px), round(py - 2 * z + 1)), round(r))
        for i, (px, py) in reversed(list(enumerate(pts))):
            r = max(1, radii[i] * z)
            pygame.draw.circle(s, self.body, (round(px), round(py - 2 * z)), round(r))
            pygame.draw.circle(s, belly, (round(px), round(py - 2 * z + r * 0.5)), max(1, round(r * 0.45)))
            if i in (2, 5, 7):
                s.set_at((round(px), round(py - 2 * z - r * 0.3)), dark)
        for i in range(1, 7):  # frost spikes down the back
            px, py = pts[i]
            top = py - 2 * z - radii[i] * z
            pygame.draw.line(s, (236, 250, 255), (round(px), round(top)), (round(px), round(top - (2 if i % 2 else 1) * z)))
        hx, hy = pts[0]
        hx += f * 2.5 * z
        pygame.draw.ellipse(s, dark, (hx - 4 * z, hy - 6 * z + 1, 8 * z, 6 * z))
        pygame.draw.ellipse(s, self.body, (hx - 4 * z, hy - 6 * z, 8 * z, 6 * z))
        ex, ey = round(hx + f * 1.5 * z), round(hy - 4.5 * z)
        e = max(2, round(1.8 * z))
        pygame.draw.rect(s, (255, 255, 255), (ex - e // 2, ey - e // 2, e, e))
        s.set_at((ex + (1 if f > 0 else -1) * (e // 2 - 1 if e > 2 else 0), ey), INK)
        pygame.draw.line(s, dark, (hx + f * 1 * z, hy - 2 * z), (hx + f * 3.5 * z, hy - 2.5 * z))

    # the beetle: a copper dome on six busy legs, its antennae crackling
    def draw_beetle(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        dark = mix(self.body, INK, 0.5)
        for i in range(3):
            for side in (-1, 1):
                lx = x + (i - 1) * 4 * z
                w = math.sin(self.step + i * 2 + side) * 1.5 * z if self.wait <= 0 else 0
                pygame.draw.line(s, dark, (lx, y - 3 * z), (lx + w + side * z, y), 1)
        pygame.draw.ellipse(s, dark, (x - 7 * z, y - 10 * z + 1, 14 * z, 9 * z))
        pygame.draw.ellipse(s, self.body, (x - 7 * z, y - 10 * z, 14 * z, 9 * z))
        pygame.draw.line(s, dark, (x, y - 10 * z), (x, y - 2 * z))
        pygame.draw.ellipse(s, (255, 214, 170), (x - 4 * z, y - 9 * z, 4 * z, 2 * z))
        hx = x + f * 7 * z
        pygame.draw.circle(s, dark, (round(hx), round(y - 5 * z)), max(2, round(2.5 * z)))
        for side in (-1, 1):
            pygame.draw.line(s, dark, (hx, y - 6 * z), (hx + f * 4 * z, y - (8 + side * 2) * z))

    def light(self, lm, t):
        if self.kind in ("sporeling", "beetle", "mole"):
            glow(lm, self.x, self.y - 8 * self.size, int(22 * self.size), self.color, q(40 + 15 * math.sin(t * 2 + self.phase)))

    def shine(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        k = swell(t - self.poked, 0.1, 0.8)
        if self.kind == "sporeling":
            for i, (sx, sy) in enumerate(((-5, -14), (0, -15), (4, -13), (-2, -12), (6, -11))):
                b = 0.5 + 0.5 * math.sin(t * 2 + i * 1.3 + self.phase)
                s.set_at((round(x + sx * z), round(y + sy * z)), mix(self.color, (255, 255, 255), 0.4 + 0.5 * b))
            glow(s, x, y - 13 * z, int(10 * z), self.color, q(40 + 90 * k))
        elif self.kind == "mole":
            nx, ny = x + f * 9 * z, y - 5 * z
            glow(s, nx, ny, int(5 * z), self.color, q(90 + 60 * k))
            pygame.draw.circle(s, (255, 180, 220), (round(nx), round(ny)), max(1, round(1.5 * z)))
        elif self.kind == "beetle":
            hx = x + f * 11 * z
            for side in (-1, 1):
                if math.sin(t * 13 + side * 2 + self.phase) > 0.3 or k > 0:
                    glow(s, hx, y - (8 + side * 2) * z, int(4 * z), self.color, q(110 + 80 * k))
        elif self.kind == "newt":
            for i in range(1, 7, 2):
                px, py = self.tail[i]
                if math.sin(t * 1.5 + i + self.phase) > -0.2:
                    s.set_at((round(px), round(py - 4 * z)), (240, 252, 255))
            if k > 0:
                glow(s, x, y - 3 * z, int(12 * z), self.color, q(120 * k))
        elif self.kind == "toad" and k > 0:
            glow(s, x, y - 6 * z, int(12 * z), self.color, q(80 * k))


# --- the owlet: a tree dweller --------------------------------------------------------

def owlet(s, x, y, sz, color, t, phase, how, poked):
    """A Moon Owlet perched where a tree squid would be, the app icon (drawn below it,
    at y + 19) gripped in its talons. It blinks slowly, turns its head now and then, and
    flaps when it is moving to another tree."""
    body = mix((200, 186, 230), color, 0.25)
    dark = mix(body, INK, 0.4)
    k = swell(t - poked, 0.35, 1.2, wait=0.15)
    glow(s, x, y - 8 * sz, int(15 * sz), color, q(40 + 50 * k))
    by = y - 6 * sz
    if how == "swim":  # flying to its new tree
        flap = math.sin(t * 12 + phase)
        for side in (-1, 1):
            pygame.draw.polygon(s, dark, [(x + side * 5 * sz, by - 2 * sz), (x + side * 16 * sz, by - 8 * sz * flap),
                                          (x + side * 12 * sz, by + 4 * sz)])
    pygame.draw.ellipse(s, dark, (x - 8 * sz + 1, by - 9 * sz + 1, 16 * sz, 18 * sz))
    pygame.draw.ellipse(s, body, (x - 8 * sz, by - 9 * sz, 16 * sz, 18 * sz))
    pygame.draw.ellipse(s, mix(body, (255, 255, 255), 0.45), (x - 5 * sz, by - 1 * sz, 10 * sz, 9 * sz))
    for i in range(3):  # speckled chest
        s.set_at((round(x - 2 * sz + i * 2 * sz), round(by + 3 * sz + (i % 2) * sz)), dark)
    turn = math.sin(t * 0.4 + phase) * 1.5 * sz
    for side in (-1, 1):  # ear tufts
        pygame.draw.polygon(s, body, [(x + side * 3 * sz + turn, by - 8 * sz), (x + side * 7 * sz + turn, by - 8 * sz),
                                      (x + side * 7 * sz + turn, by - 13 * sz)])
    blink = (t + phase * 2) % 6.1 < 0.2
    for side in (-1, 1):
        ex, ey = x + side * 3.5 * sz + turn, by - 4 * sz
        pygame.draw.circle(s, (255, 236, 160), (round(ex), round(ey)), max(2, round(2.8 * sz)))
        if blink:
            pygame.draw.line(s, dark, (ex - 2 * sz, ey), (ex + 2 * sz, ey), max(1, round(sz)))
        else:
            pygame.draw.circle(s, INK, (round(ex), round(ey)), max(1, round(1.4 * sz)))
    pygame.draw.polygon(s, (240, 190, 110), [(x + turn - 1.2 * sz, by - 2 * sz), (x + turn + 1.2 * sz, by - 2 * sz),
                                             (x + turn, by + 1 * sz)])
    for side in (-1, 1):  # talons, gripping the icon's pad
        tx = x + side * 3 * sz
        pygame.draw.line(s, (240, 190, 110), (tx, by + 8 * sz), (tx, y + 8 * sz), max(1, round(sz)))
        pygame.draw.line(s, (240, 190, 110), (tx - sz, y + 8 * sz), (tx + sz, y + 8 * sz))
