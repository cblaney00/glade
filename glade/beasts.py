"""The second wave of the glade's animals (see battle.py for what they are in a battle).

Two kinds of mover, each drawing one of several animals:
- `Flier`: Gloomflit, Lanternwing, Glimmerfly (a dragonfly) and Mistwisp, roaming a
  patch of sky;
- `Walker`: Brawlhop, Mossdelve, Sporeling (a walking mushroom), Rimeslink and
  Coppernib, wandering along the ground.
Plus `owlet()`, which draws a Moonhoot where a tree squid would be (squids.py): the
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
    bat=dict(species="Gloomflit", body=(86, 64, 128), color=(255, 120, 190), speed=80, turn=0.9),
    moth=dict(species="Lanternwing", body=(250, 214, 170), color=GLOW["amber"], speed=34, turn=1.6),
    drake=dict(species="Glimmerfly", body=(110, 220, 210), color=GLOW["cyan"], speed=110, turn=1.2),
    wisp=dict(species="Mistwisp", body=(214, 220, 255), color=(170, 190, 255), speed=16, turn=4.0),
    # the far places (2026-10-27): the Snowy Ridge and the Hot Springs
    finch=dict(species="Shimmerchirp", body=(236, 240, 255), color=(150, 255, 210), speed=70, turn=1.0),
    jelly=dict(species="Vaporwobble", body=(196, 228, 255), color=(255, 236, 120), speed=12, turn=3.5),
    # the third wave (2026-10-27): the Forest and the Waterfall
    thistle=dict(species="Thistlume", body=(236, 228, 255), color=(200, 150, 255), speed=14, turn=4.5),
    spark=dict(species="Sparkfly", body=(84, 100, 190), color=(255, 246, 130), speed=95, turn=0.7),
)
AURORA = [(140, 255, 200), (120, 220, 255), (190, 150, 255), (255, 150, 220)]
LIT = set()  # kinds added in grown.py / wave4.py that light up their surroundings
PRISM = [(255, 130, 150), (255, 190, 110), (255, 240, 130), (140, 255, 170), (120, 210, 255), (180, 150, 255)]


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
            acc = self.speed * (3 if self.kind not in ("wisp", "jelly") else 1)
            self.vx += dx / d * acc * dt
            self.vy += dy / d * acc * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > self.speed:
                self.vx, self.vy = self.vx / sp * self.speed, self.vy / sp * self.speed
            if self.kind == "moth":  # fluttering: it never goes quite straight
                self.vy += math.sin(t * 7 + self.phase) * 40 * dt
            if self.kind == "jelly":  # it swims in slow pulses: a push up, then a sink
                self.vy += (-60 if math.sin(t * 1.6 + self.phase) > 0.85 else 9) * dt
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
        grow = getattr(self, "grow_" + self.kind, None)  # a later stage's extras (grown.py)
        if grow and getattr(self, "stage", 1) > 1:
            grow(s, t, self.stage)

    # the bat: a velvet body, pointed ears, wings that beat fast
    def draw_bat(self, s, t):
        z, x, y = self.size, self.x, self.y
        st = getattr(self, "stage", 1)  # Gloomglide and Nightshroud: broader wings, slower beats, gliding
        span = 1 + 0.15 * (st - 1)
        beat = math.sin(t * 16 / (1 + 0.7 * (st - 1)) + self.phase) * (1 - 0.25 * (st - 1))
        self._wings = []
        if st > 1:  # a membrane between its legs, like a cape
            cape = [(x - 3 * z, y + 2 * z), (x + 3 * z, y + 2 * z), (x + 1.5 * z * math.sin(t * 3), y + (8 + 2 * st) * z)]
            pygame.draw.polygon(s, mix(self.body, INK, 0.45), cape)
        for side in (-1, 1):
            tip = (x + side * 13 * z * span, y - 7 * z * beat)
            elbow = (x + side * 7 * z * span, y - 4 * z * beat - 2 * z)
            pts = [(x + side * 2 * z, y - 2 * z), elbow, tip, (x + side * 10 * z * span, y + 2 * z),
                   (x + side * 6 * z * span, y + (1 + st) * z), (x + side * 3 * z, y + 3 * z)]
            self._wings.append(pts)
            pygame.draw.polygon(s, mix(self.body, INK, 0.35), pts)
            pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.25), (x + side * 2 * z, y - 2 * z), elbow)
            pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.25), elbow, tip)
        pygame.draw.ellipse(s, self.body, (x - 4 * z, y - 4 * z, 8 * z, 8 * z))
        pygame.draw.ellipse(s, mix(self.body, (255, 220, 240), 0.3), (x - 2 * z, y, 4 * z, 3 * z))
        ear = 8 + 2 * (st - 1)
        for ex in (-2, 2):
            pygame.draw.polygon(s, self.body, [(x + ex * z - 1.5 * z, y - 3 * z), (x + ex * z + 1.5 * z, y - 3 * z),
                                               (x + ex * z * 1.5, y - ear * z)])

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
        big = getattr(self, "stage", 1) > 1  # Beaconwing, its evolution (evolve.py)
        if big:  # bands of colour across the wings
            for side in (-1, 1):
                w1 = 10 * z * open_
                band = (x + (w1 * 0.35 if side > 0 else -w1 * 0.65), y - 6 * z, w1 * 0.3, 6 * z)
                pygame.draw.ellipse(s, mix(wing, (200, 90, 80), 0.45), band)
        if getattr(self, "stage", 1) > 2:  # Hearthwing: tongues of flame along its wings' edges
            for side in (-1, 1):
                w1 = 10 * z * open_
                for j in range(4):
                    fx = x + side * w1 * (0.2 + j * 0.22)
                    h = (2 + 1.5 * abs(math.sin(t * 8 + j * 1.7 + side))) * z
                    pygame.draw.polygon(s, (255, 150, 80) if j % 2 else (255, 200, 110),
                                        [(fx - z, y - 7 * z), (fx + z, y - 7 * z), (fx, y - 7 * z - h)])
        pygame.draw.ellipse(s, self.body, (x - 2 * z, y - 5 * z, 4 * z, 10 * z))
        for side in (-1, 1):  # feathery antennae
            tip = (x + side * (5 if big else 4) * z, y - (12 if big else 10) * z)
            pygame.draw.line(s, mix(self.body, INK, 0.3), (x, y - 5 * z), tip)
            if big:  # plumed: little barbs along them
                for k in (0.4, 0.6, 0.8):
                    bx, by = x + (tip[0] - x) * k, y - 5 * z + (tip[1] - y + 5 * z) * k
                    pygame.draw.line(s, mix(self.body, INK, 0.2), (bx, by), (bx + side * 1.5 * z, by + 1 * z))

    # the dragonfly: a long glinting body and four wings, a blur when it hovers
    def draw_drake(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        bob = math.sin(t * 3 + self.phase) * z
        st = getattr(self, "stage", 1)
        n = (9, 13, 16)[st - 1]
        for i in range(n):  # the tail, behind the head (a wyrm's winds like a ribbon)
            px = x - f * (4 + i * 2.2) * z
            wave = math.sin(t * 4 - i * 0.6 + self.phase) * (st - 1) * 1.2 * z * i / n
            col = PRISM[(i + int(t * 6)) % len(PRISM)] if st > 2 else mix(self.body, (150, 110, 255), i / n)
            pygame.draw.circle(s, col, (round(px), round(y + bob * i / n + wave)), max(1, round((1.6 + 0.4 * (st - 1) - i * 1.4 / n) * z)))
        pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round(2.6 * z)))
        if st > 1:  # horns swept back
            for k in (-1, 1):
                pygame.draw.line(s, (236, 244, 255), (x - f * z, y - 2 * z), (x - f * 4 * z, y - (4 + k) * z))
        s.set_at((round(x + f * z), round(y - z)), (255, 255, 255))
        blur = self.hover > 0 or (t * 30) % 2 < 1
        wing = mix(self.body, (255, 255, 255), 0.7)
        for k, ln in ((1, 9 + 2 * (st - 1)), (3, 8 + 2 * (st - 1))):
            if st > 2:
                wing = PRISM[(k + int(t * 4)) % len(PRISM)]
            for up in (-1, 1):
                end = (x - f * k * z + (2 * f * z if blur else 0), y + up * (3 if blur else 2) * z - ln * z * (0.6 if up < 0 else -0.2))
                pygame.draw.line(s, wing, (x - f * k * z, y - z), end)

    # the wisp: a ghostly little flame with a tail of mist; it is almost all light
    def draw_wisp(self, s, t):
        pass  # all of it shines (below)

    # the finch: a round little snowbird; its long tail streams out behind in aurora colours
    def draw_finch(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        flap = math.sin(t * 18 + self.phase)
        dark = mix(self.body, INK, 0.35)
        pygame.draw.ellipse(s, dark, (x - 5 * z, y - 4 * z + 1, 10 * z, 8 * z))
        pygame.draw.ellipse(s, self.body, (x - 5 * z, y - 4 * z, 10 * z, 8 * z))
        pygame.draw.ellipse(s, (255, 214, 226), (x - 2 * z + f * z, y - 1 * z, 5 * z, 4 * z))  # a rosy breast
        pygame.draw.polygon(s, mix(self.body, (150, 190, 255), 0.4),
                            [(x - f * z, y - z), (x - f * 6 * z, y - (5 + 4 * flap) * z), (x - f * 7 * z, y + z)])
        pygame.draw.polygon(s, (255, 200, 120), [(x + f * 4.5 * z, y - 1.5 * z), (x + f * 7 * z, y - z),
                                                 (x + f * 4.5 * z, y)])
        pygame.draw.rect(s, INK, (round(x + f * 2.5 * z), round(y - 2.5 * z), max(1, round(z)), max(1, round(z))))
        for side in (-1, 0):  # a crest of two feathers
            pygame.draw.line(s, self.body, (x + f * z, y - 4 * z), (x + f * (side - 1) * z, y - 7 * z))

    # the jelly: a see-through bell of steam, drifting in pulses, trailing tentacles that crackle
    def draw_jelly(self, s, t):
        pass  # it is made of light (below)

    # the third wave (2026-10-27): the Forest's thistlume and the Waterfall's sparkfly

    # the thistlume: a puff of thistledown drifting on the night air, one big dreamy eye in it
    def draw_thistle(self, s, t):
        z, x, y = self.size, self.x, self.y
        sway = math.sin(t * 1.3 + self.phase)
        down = mix(self.body, (120, 110, 190), 0.45)
        pygame.draw.line(s, (150, 120, 170), (x, y + 3 * z), (x + sway * z, y + 9 * z))  # its seed, hanging below
        pygame.draw.ellipse(s, (150, 110, 150), (x + sway * z - z, y + 8 * z, 2 * z, 3 * z))
        for i in range(14):  # the fine hairs of the down, gently waving
            a = i / 14 * math.tau + sway * 0.25 + math.sin(t * 2 + i) * 0.06
            ln = (7 + i % 3) * z
            ex, ey = x + math.cos(a) * ln, y + math.sin(a) * ln * 0.9
            pygame.draw.line(s, down, (round(x), round(y)), (round(ex), round(ey)))
            s.set_at((round(ex), round(ey)), self.body)
        pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round(4 * z)))

    # the sparkfly: a little night-blue bug on buzzing wings; its tail flashes like lightning
    def draw_spark(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        dark = mix(self.body, INK, 0.3)
        buzz = (t * 40) % 2 < 1
        wing = mix(self.body, (220, 230, 255), 0.6)
        for up in (0, 1):  # two pairs of wings, a buzzing blur
            wx = x - f * up * 2 * z
            r = (wx - 2.5 * z, y - (8 if buzz else 6.5) * z - up * z, 5 * z, 6.5 * z)
            pygame.draw.ellipse(s, mix(wing, INK, 0.45), r)
            pygame.draw.ellipse(s, wing, r, 1)
        for i in range(3):  # its tail: three segments, the last one the lamp
            pygame.draw.circle(s, dark, (round(x - f * (2 + i * 2) * z), round(y + i * 0.6 * z)), max(1, round((2.6 - i * 0.3) * z)))
        pygame.draw.circle(s, self.body, (round(x + f * 1.5 * z), round(y - 0.5 * z)), max(2, round(2.8 * z)))
        for side in (-1, 1):  # antennae, bent like lightning
            pygame.draw.lines(s, dark, False, [(x + f * 3 * z, y - 2 * z), (x + f * 4 * z, y - 4 * z + side * z * 0.5),
                                               (x + f * 5 * z, y - 4 * z), (x + f * 6 * z, y - 6 * z + side * z)])
        s.set_at((round(x + f * 2.5 * z), round(y - z)), (255, 255, 255))

    def light(self, lm, t):
        if self.kind in ("moth", "wisp", "drake", "jelly", "finch", "thistle", "spark") or self.kind in LIT:
            glow(lm, self.x, self.y, int(30 * self.size), self.color, q(60 + 20 * math.sin(t * 2 + self.phase)))

    def shine(self, s, t):
        self.shine_flier(s, t)
        lit = getattr(self, "glow_" + self.kind, None)  # a later stage's own lights (grown.py)
        if lit and (getattr(self, "stage", 1) > 1 or self.kind in LIT):
            lit(s, t, getattr(self, "stage", 1), swell(t - self.poked, 0.1, 0.6))

    def shine_flier(self, s, t):
        z, x, y = self.size, self.x, self.y
        k = swell(t - self.poked, 0.1, 0.6)
        if self.kind == "bat":
            st = getattr(self, "stage", 1)
            for ex in (-1.5, 1.5):  # little glowing eyes
                s.set_at((round(x + ex * z), round(y - 1 * z)), self.color)
                if st > 1:
                    glow(s, x + ex * z, y - z, int(3 * z), self.color, q(70 + 50 * k))
            if st > 2:  # Nightshroud: stars twinkling in its wings, a crescent moon on its chest
                for w, pts in enumerate(getattr(self, "_wings", [])):
                    for j in range(5):
                        a, b = pts[1 + j % 3], pts[3 + j % 2]
                        f = 0.3 + 0.15 * j
                        sx, sy = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                        if math.sin(t * 3 + j * 1.9 + w) > -0.3:
                            s.set_at((round(sx), round(sy)), (230, 230, 255))
                cx, cy = x, y + 1.5 * z
                pygame.draw.circle(s, (255, 236, 180), (round(cx), round(cy)), max(1, round(1.6 * z)))
                pygame.draw.circle(s, self.body, (round(cx + 0.8 * z), round(cy - 0.4 * z)), max(1, round(1.4 * z)))
                glow(s, cx, cy, int(5 * z), (255, 236, 180), q(70 + 60 * k))
        elif self.kind == "moth":
            glow(s, x, y, int(10 * z), self.color, q(70 + 50 * k))
            if getattr(self, "stage", 1) > 1:  # a lantern of a belly, and embers trailing behind
                b = 0.7 + 0.3 * math.sin(t * 3 + self.phase)
                glow(s, x, y + 3 * z, int(9 * z), (255, 170, 90), q(140 * b))
                pygame.draw.ellipse(s, (255, 214, 140), (x - 1.5 * z, y + 1 * z, 3 * z, 4 * z))
                for i, (px, py) in enumerate(self.trail[2::2]):
                    s.set_at((round(px), round(py + 3 * z + i)), mix((255, 170, 90), (60, 30, 50), i / 4))
                if getattr(self, "stage", 1) > 2:  # a hearth's warmth all round it
                    glow(s, x, y - 2 * z, int(18 * z), (255, 150, 80), q(60 + 30 * b + 50 * k))
            for side in (-1, 1):  # eye-spots on the wings glow like embers
                s.set_at((round(x + side * 5 * z), round(y - 4 * z)), (255, 210, 120))
        elif self.kind == "drake":
            st = getattr(self, "stage", 1)
            tx = x - self.facing * (4 + (9, 13, 16)[st - 1] * 2.2) * z
            if st > 2:
                glow(s, x, y, int(12 * z), PRISM[int(t * 3) % len(PRISM)], q(60 + 40 * k))
            glow(s, tx, y, int(6 * z), self.color, q(90 + 60 * k))
        elif self.kind == "finch":
            for i, (px, py) in enumerate(self.trail[1:]):  # the streamer of a tail
                c = AURORA[(i + int(t * 3)) % len(AURORA)]
                c = mix(c, (40, 40, 90), i / 9)
                tx = px - self.facing * 6 * z
                s.set_at((round(tx), round(py + 0.5 * z)), c)
                if i < 4:
                    s.set_at((round(tx), round(py + 1.5 * z)), c)
            glow(s, x - self.facing * 6 * z, y, int(6 * z), AURORA[int(t * 2) % 4], q(50 + 60 * k))
        elif self.kind == "jelly":
            pulse = 0.5 + 0.5 * math.sin(t * 1.6 + self.phase)
            bw = (9 + 2 * pulse) * z
            bh = (8 - 1.5 * pulse) * z
            glow(s, x, y, int(16 * z), (150, 200, 255), q(50 + 40 * k))
            for i in range(5):  # tentacles, swaying
                tx = x + (i - 2) * 3 * z
                pts = [(tx + math.sin(t * 2.4 + i + j * 0.9 + self.phase) * 1.6 * z, y + 2 * z + j * 3 * z) for j in range(5)]
                for j in range(len(pts) - 1):
                    pygame.draw.line(s, mix(self.body, (60, 70, 150), j / 5), pts[j], pts[j + 1])
            if math.sin(t * 5.3 + self.phase) * math.sin(t * 3.1) > 0.55 or k > 0.3:  # a spark crackles down one
                i = int(t * 7) % 5
                sx = x + (i - 2) * 3 * z
                for j in range(3):
                    s.set_at((round(sx + (j % 2) * z), round(y + (4 + j * 3) * z)), self.color)
                glow(s, sx, y + 8 * z, int(5 * z), self.color, q(110))
            dome = pygame.Rect(0, 0, round(bw * 2), round(bh * 2))
            dome.center = (round(x), round(y + bh * 0.5))
            edge = mix(self.body, (40, 50, 120), 0.45)
            was = s.get_clip()  # only the top half of the ellipse: a bell
            s.set_clip(pygame.Rect(dome.x - 2, dome.y - 2, dome.w + 4, dome.h // 2 + 2).clip(was))
            pygame.draw.ellipse(s, edge, dome)
            pygame.draw.ellipse(s, mix(self.body, (120, 150, 230), 0.35), dome.inflate(-2 * z, -2 * z))
            s.set_clip(was)
            pygame.draw.ellipse(s, self.body, (x - bw * 0.55, y - bh * 0.4, bw * 1.1, bh * 0.9))  # a glowing heart
            for i in range(-4, 5):  # the bell's frilly rim
                s.set_at((round(x + i * bw / 4.6), round(y + 2 * z + (i % 2) * z * 0.8)), edge)
            pygame.draw.line(s, (255, 255, 255), (x - bw * 0.6, y - bh * 0.1), (x - bw * 0.4, y - bh * 0.4))
            for ex in (-2, 2):
                s.set_at((round(x + ex * z), round(y - z)), INK)
        elif self.kind == "thistle":
            glow(s, x, y, int(14 * z), self.color, q(50 + 70 * k))
            if (t * 0.7 + self.phase) % 6 < 0.25:  # a slow blink
                pygame.draw.line(s, INK, (x - 2 * z, y), (x + 2 * z, y))
            else:
                pygame.draw.circle(s, (255, 255, 255), (round(x), round(y)), max(2, round(2.6 * z)))
                ix = round(x + self.facing * 0.6 * z)
                pygame.draw.circle(s, self.color, (ix, round(y)), max(1, round(1.6 * z)))
                s.set_at((ix, round(y)), INK)
            if k > 0:  # poked: a ripple of thought spreads out
                pygame.draw.circle(s, mix(self.color, (255, 255, 255), 0.4), (round(x), round(y)), round((6 + 14 * (1 - k)) * z), 1)
        elif self.kind == "spark":
            f = self.facing
            tx, ty = x - f * 6 * z, y + 1.2 * z
            flash = math.sin(t * 6 + self.phase) * math.sin(t * 2.3) > 0.4 or k > 0.2
            glow(s, tx, ty, int((10 if flash else 6) * z), self.color, q((140 if flash else 50) + 60 * k))
            pygame.draw.circle(s, mix(self.color, (255, 255, 255), 0.5 if flash else 0), (round(tx), round(ty)), max(1, round(1.8 * z)))
            if flash:  # a crackle jumps off its tail
                px, py = tx, ty
                for j in range(3):
                    nx, ny = px - f * 2 * z, py + (1 if (j + int(t * 13)) % 2 else -1) * 2 * z
                    pygame.draw.line(s, self.color, (px, py), (nx, ny))
                    px, py = nx, ny
        elif self.kind == "wisp":
            flick = 0.75 + 0.25 * math.sin(t * 11 + self.phase) * math.sin(t * 7.3)
            st = getattr(self, "stage", 1)
            if st > 1:  # misty arms (and, for Mistwraith, the tatters of a cloak) trailing behind
                for side in ((-1, 1) if st == 2 else (-1.4, -0.5, 0.5, 1.4)):
                    for i, (px, py) in enumerate(self.trail[::-1]):
                        c = mix((150, 140, 220) if st > 2 else self.color, (40, 40, 100), 1 - i / 8)
                        off = side * (2 + i * 0.9) * z
                        pygame.draw.circle(s, c, (round(px + off), round(py + i * 0.6 * z)), max(1, round((0.6 + i * 0.25) * z)))
            for i, (px, py) in enumerate(self.trail[::-1]):
                r = max(1, round((1 + i * 0.6) * z))
                c = mix(self.color, (60, 60, 140), 1 - i / 8)
                pygame.draw.circle(s, c, (round(px), round(py - i * 0.4)), r)
            glow(s, x, y, int(16 * z), self.color, q(90 * flick + 60 * k))
            if st > 1:  # a hood of shadow
                pygame.draw.circle(s, (70, 60, 130), (round(x), round(y - z)), max(3, round(6 * z)))
            pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round(5 * z)))
            pygame.draw.circle(s, (255, 255, 255), (round(x - z), round(y - 2 * z)), max(1, round(2 * z)))
            if st > 2:  # a crown of three cold flames
                for j in (-1, 0, 1):
                    fx, fy = x + j * 3 * z, y - (6 + (j == 0)) * z
                    h = (2.5 + math.sin(t * 9 + j * 2) * 0.8) * z
                    glow(s, fx, fy - h / 2, int(4 * z), self.color, q(90 * flick))
                    pygame.draw.polygon(s, (220, 230, 255), [(fx - z, fy), (fx + z, fy), (fx, fy - h)])
            for ex in (-2, 2):
                s.set_at((round(x + ex * z), round(y)), INK)
                if st > 2:  # glowing eyes
                    s.set_at((round(x + ex * z), round(y)), (150, 255, 240))


# --- on the ground ----------------------------------------------------------------------

WALKERS = dict(
    toad=dict(species="Brawlhop", body=(96, 176, 128), color=(255, 120, 110), speed=26),
    mole=dict(species="Mossdelve", body=(96, 76, 120), color=(255, 150, 200), speed=12),
    sporeling=dict(species="Sporeling", body=(240, 232, 214), color=(200, 140, 255), speed=10),
    newt=dict(species="Rimeslink", body=(150, 210, 245), color=(200, 245, 255), speed=14),
    beetle=dict(species="Coppernib", body=(214, 128, 78), color=(255, 236, 120), speed=9),
    # the far places (2026-10-27): the Snowy Ridge and the Hot Springs
    fox=dict(species="Frostpaw", body=(232, 240, 255), color=(150, 255, 210), speed=22),
    goat=dict(species="Fluffhorn", body=(246, 240, 232), color=(170, 220, 255), speed=8),
    capy=dict(species="Steambara", body=(176, 124, 112), color=(255, 186, 90), speed=5),
    gecko=dict(species="Embercling", body=(118, 88, 112), color=(255, 140, 70), speed=30),
    # the third wave (2026-10-27): the Forest, the Waterfall and the River
    bramble=dict(species="Bramblit", body=(78, 96, 92), color=(255, 90, 130), speed=14),
    rune=dict(species="Runelet", body=(132, 128, 170), color=(140, 255, 240), speed=5),
    murk=dict(species="Murkling", body=(70, 58, 110), color=(170, 255, 110), speed=7),
    glint=dict(species="Glintshell", body=(186, 196, 222), color=(130, 200, 255), speed=8),
    # the three starters (starter.py): not found in the wild, only chosen
    fawn=dict(species="Mossprance", body=(222, 190, 160), color=(150, 255, 190), speed=16),
    pangolin=dict(species="Kindlet", body=(156, 104, 120), color=(255, 150, 80), speed=10),
    axolotl=dict(species="Pippalotl", body=(255, 184, 214), color=(255, 120, 200), speed=9),
)


class Walker(Clock):
    """Something that wanders along the ground `ground(x)` between x_range: a toad in
    hops, a mole that never strays far from its hole, a waddling mushroom, a newt with a
    long wriggling tail, a beetle on six busy legs. Click it and it reacts."""

    # Its drawn size is its own size times how near it is (his ask, 2026-10-27: further back is
    # smaller). `persp(y)` gives that for where it stands; evolving sets the own size.
    size = property(lambda self: self._size * self.depth, lambda self, v: setattr(self, "_size", v))

    def __init__(self, rng, ground, x_range, kind, size=1.0, roam=None, avoid=None, persp=None):
        """`roam`: every stretch of ground in its place, [(ground, x_range)], for it to wander
        between; `avoid(x, y)`: somewhere it must not cross (a pond); `persp(y)`: how big it
        looks standing at y (1 at the front)."""
        self.depth, self.persp = 1.0, persp
        self.roam, self.avoid, self.blend = roam, avoid, None
        spec = WALKERS[kind]
        self.rng, self.ground, self.xr, self.kind, self.size = rng, ground, x_range, kind, size
        self.species, self.body, self.color, self.speed = spec["species"], spec["body"], spec["color"], spec["speed"]
        self.x = rng.uniform(*x_range)
        self.y = ground(self.x)
        if persp:
            self.depth = persp(self.y)
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

    def retarget(self):
        """Somewhere new to go: along this stretch of ground, or now and then over to another
        anywhere in its place (walking across between them)."""
        self.target = self.rng.uniform(*self.xr)
        if not self.roam or self.rng.random() > 0.45:
            return
        for _ in range(6):
            ground, xr = self.rng.choice(self.roam)
            if self.kind == "mole":
                xr = (xr[0] + 12, xr[1] - 12)
                if xr[0] >= xr[1]:
                    continue
            tx = self.rng.uniform(*xr)
            x0, y0, ty = self.x, self.ground(self.x), ground(tx)
            if self.avoid and any(self.avoid(x0 + (tx - x0) * k / 8, y0 + (ty - y0) * k / 8) for k in range(9)):
                continue
            old = self.ground
            span = (tx - x0) or 1.0

            def between(x, old=old, new=ground, x0=x0, span=span):
                f = max(0.0, min(1.0, (x - x0) / span))
                return old(x) * (1 - f) + new(x) * f
            near = (tx - 10 * self.size, tx + 10 * self.size) if self.kind == "mole" else xr
            self.blend = (between, ground, tx, near)
            self.ground, self.target = between, tx
            self.xr = (min(self.xr[0], tx - 1), max(self.xr[1], tx + 1))
            return

    def update(self, dt, t):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.retarget()
        else:
            d = self.target - self.x
            if abs(d) < 2:
                self.wait = self.rng.uniform(1.5, 6)
                if self.blend is not None:  # it has arrived on its new stretch of ground
                    self.ground, self.xr = self.blend[1], self.blend[3]
                    self.blend = None
                    if self.kind == "mole":  # and digs a new hole there
                        self.home = self.x
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
        if self.persp:
            self.depth = self.persp(self.ground(self.x))
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
        stage = getattr(self, "stage", 1)
        fn = getattr(self, f"draw_{self.kind}{stage}", None) if stage > 1 else None
        (fn or getattr(self, "draw_" + self.kind))(s, t)
        grow = getattr(self, "grow_" + self.kind, None)  # a later stage's extras (grown.py)
        if grow and stage > 1:
            grow(s, t, stage)

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
        if getattr(self, "stage", 1) > 1:  # Thudhop, its evolution (evolve.py)
            for i in range(3):  # stripes down its back
                bx = x - f * (3 - i * 2.5) * z
                pygame.draw.line(s, dark, (bx, y - 9 * z), (bx - f * z, y - 6 * z))
            for side in (-1, 1):  # fierce brows
                ex = hx + side * 2 * z
                pygame.draw.line(s, INK, (ex - 1.5 * z, y - (13 if side * f < 0 else 12.5) * z),
                                 (ex + 1.5 * z, y - (12.5 if side * f < 0 else 13) * z))
            for i in range(2):  # the headband's tails stream out behind
                wave = math.sin(t * 6 + i * 1.5) * 1.5 * z
                pygame.draw.line(s, (230, 80, 90), (hx - f * 4 * z, y - 8 * z), (hx - f * 10 * z, y - (8 - i * 2) * z + wave))
            punch = max(0.0, math.sin(t * 2 + self.phase)) ** 8 * 3 * z  # a jab now and then
            for side, c in ((-1, dark), (1, self.body)):  # burly arms with bandaged fists
                sx, sy = x + f * 3 * z, y - (4 if side > 0 else 5) * z
                fx, fy = x + f * (9 * z + (punch if side > 0 else 0)), y - (3 if side > 0 else 5) * z
                pygame.draw.line(s, c, (sx, sy), (fx, fy), max(2, round(1.6 * z)))
                pygame.draw.circle(s, (238, 226, 206), (round(fx), round(fy)), max(2, round(2.2 * z)))
                pygame.draw.line(s, (200, 186, 170), (fx - z, fy), (fx + z, fy))

    # Titanhop: Thudhop grown huge, stone plates down its back, a champion's golden belt
    def draw_toad3(self, s, t):
        self.draw_toad(s, t)
        z, x, y, f = self.size, self.x, self.y, self.facing
        stone, sd = (150, 144, 176), (96, 88, 126)
        for j in range(3):
            bx = x - f * (5 - j * 3.2) * z
            by = y - (9.5 + (j == 1)) * z
            pts = [(bx - 2 * z, by + 2 * z), (bx - 1 * z, by - 1.5 * z), (bx + 1.5 * z, by - 2 * z), (bx + 2.2 * z, by + 1.5 * z)]
            pygame.draw.polygon(s, sd, [(px, py + 1) for px, py in pts])
            pygame.draw.polygon(s, stone, pts)
            s.set_at((round(bx), round(by - z)), (220, 216, 240))
        pygame.draw.line(s, (240, 190, 70), (x - 7 * z, y - 3 * z), (x + 7 * z, y - 3 * z), max(2, round(1.4 * z)))
        bx = x + f * 2 * z
        pygame.draw.rect(s, (255, 226, 120), (bx - 1.5 * z, y - 4.5 * z, 3 * z, 3 * z))
        s.set_at((round(bx), round(y - 3 * z)), (255, 255, 255))

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
        st = getattr(self, "stage", 1)
        if st > 1:  # Mossburrow: moss over its back; Mossquake: a whole mossy hill
            hill = 3 if st > 2 else 0
            if hill:
                pygame.draw.ellipse(s, (66, 140, 110), (x - 7 * z, y - 13 * z, 13 * z, 7 * z))
            for j in range(6):
                mx = x - 6 * z + j * 2.2 * z
                my = y - 9 * z - math.sin(j / 5 * math.pi) * (1 + hill) * z
                pygame.draw.circle(s, (100, 200, 150) if j % 2 else (80, 176, 132), (round(mx), round(my)), max(1, round(1.8 * z)))
            if st > 2:
                for j, (cx, ch) in enumerate(((-3, 5), (-1, 7), (2, 4))):  # crystal shards through the moss
                    pygame.draw.polygon(s, (160, 230, 255), [(x + cx * z - z, y - 12 * z), (x + cx * z + z, y - 12 * z),
                                                             (x + cx * z, y - (12 + ch) * z)])
                    pygame.draw.line(s, (240, 252, 255), (x + cx * z, y - 12 * z), (x + cx * z, y - (12 + ch * 0.7) * z))
                sx = x - f * 4 * z  # and a sapling
                pygame.draw.line(s, (130, 96, 120), (sx, y - 12 * z), (sx, y - 18 * z), max(1, round(z * 0.7)))
                for k in (-1, 1):
                    pygame.draw.ellipse(s, (120, 220, 160), (sx + (k - 1) * 1.5 * z, y - 19.5 * z + (k > 0) * z, 3 * z, 2 * z))
        claw = (236, 220, 230) if st < 3 else (200, 196, 230)
        for c in (-1, 0, 1)[:2 + (st > 1)]:  # big digging claws
            cx = x + f * 6 * z + c * 2 * z
            pygame.draw.line(s, claw, (cx, y - 1 * z), (cx + f * (2 + st) * z, y), max(1, round(z * 0.5 * st)))
        s.set_at((round(x + f * 4 * z), round(y - 6 * z)), INK)

    # the sporeling: a mushroom cap on a little stem, waddling, its spots aglow
    def draw_sporeling(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        big = getattr(self, "stage", 1) > 1  # Sporestride, its evolution (evolve.py): up on longer legs
        moving = self.wait <= 0
        tilt = math.sin(self.step) * 1.5 * z if moving else 0
        for k in (0, math.pi):  # feet (and, grown, long thin legs)
            lift = max(0.0, math.sin(self.step + k)) * 2 * z if moving else 0
            fx = x - 2 * z + (2 * z if k else -2 * z)
            if big:
                pygame.draw.line(s, mix(self.body, INK, 0.2), (fx + 1.5 * z, y - 2 * z - lift), (fx + 1.5 * z, y - 6 * z), max(1, round(z)))
            pygame.draw.rect(s, mix(self.body, INK, 0.3), (fx, y - 2 * z - lift, 3 * z, 2 * z))
        if big:
            y -= 4 * z
            for side in (-1, 1):  # tassels of spores hanging from under the cap (no arms: his rule)
                ax, ay = x + side * 7 * z, y - 9 * z
                sway = math.sin(t * 2 + side) * z
                pygame.draw.line(s, mix(self.color, INK, 0.3), (ax, ay), (ax + sway, ay + 5 * z))
                pygame.draw.circle(s, mix(self.color, (255, 255, 255), 0.3), (round(ax + sway), round(ay + 5.5 * z)), max(1, round(z)))
        pygame.draw.rect(s, self.body, (x - 3 * z, y - 10 * z, 6 * z, 9 * z), border_radius=max(1, round(2 * z)))
        cap = [(x - 9 * z + tilt, y - 9 * z), (x + 9 * z + tilt, y - 9 * z)]
        pygame.draw.ellipse(s, mix(self.color, INK, 0.35), (cap[0][0], y - 17 * z + 1, 18 * z, 10 * z))
        pygame.draw.ellipse(s, mix(self.color, (255, 255, 255), 0.15), (cap[0][0], y - 17 * z, 18 * z, 10 * z))
        pygame.draw.line(s, mix(self.color, INK, 0.5), cap[0], cap[1])
        if big:
            for i in range(-3, 4, 2):  # gills under the cap
                pygame.draw.line(s, mix(self.color, INK, 0.55), (x + i * 2 * z + tilt, y - 9 * z), (x + i * 1.6 * z + tilt, y - 8 * z))
            sx = x - f * 7 * z + tilt  # a second, smaller cap sprouting from the first
            pygame.draw.ellipse(s, mix(self.color, INK, 0.35), (sx - 4 * z, y - 21 * z + 1, 8 * z, 5 * z))
            pygame.draw.ellipse(s, mix(self.color, (255, 255, 255), 0.25), (sx - 4 * z, y - 21 * z, 8 * z, 5 * z))
            pygame.draw.line(s, mix(self.body, INK, 0.2), (sx, y - 16.5 * z), (sx + f * 2 * z, y - 15 * z))
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

    # the frost kit: a snow-white fox cub, ears up, its huge fluffy tail tipped with aurora light
    def draw_fox(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        shade = mix(self.body, (120, 140, 220), 0.35)
        sway = math.sin(t * 2 + self.phase) * 1.5 * z
        tail = [(x - f * 6 * z, y - 5 * z), (x - f * 11 * z, y - 9 * z + sway), (x - f * 12 * z, y - 15 * z + sway)]
        for i, (px, py) in enumerate(tail):
            pygame.draw.circle(s, shade, (round(px), round(py + 1)), max(2, round((3.6 - i * 0.4) * z)))
        for i, (px, py) in enumerate(tail):
            pygame.draw.circle(s, self.body, (round(px), round(py)), max(2, round((3.4 - i * 0.4) * z)))
        for i in range(4):  # four little legs, trotting
            lx = x + (i - 1.5) * 2.6 * z
            lift = max(0.0, math.sin(self.step * 1.4 + i * 1.6)) * 1.5 * z if moving else 0
            pygame.draw.line(s, shade, (lx, y - 3 * z), (lx, y - lift), max(1, round(z)))
        pygame.draw.ellipse(s, shade, (x - 6 * z, y - 8 * z + 1, 12 * z, 6 * z))
        pygame.draw.ellipse(s, self.body, (x - 6 * z, y - 8 * z, 12 * z, 6 * z))
        hx, hy = x + f * 6 * z, y - 9 * z
        pygame.draw.circle(s, self.body, (round(hx), round(hy)), max(2, round(3.4 * z)))
        pygame.draw.polygon(s, self.body, [(hx + f * 2 * z, hy - z), (hx + f * 6.5 * z, hy + 1 * z), (hx + f * 2 * z, hy + 2.4 * z)])
        s.set_at((round(hx + f * 6.5 * z), round(hy + 1 * z)), INK)
        for e in (-1, 1):  # ears, with a blush of pink inside
            ex = hx + e * 2 * z
            pygame.draw.polygon(s, self.body, [(ex - 1.5 * z, hy - 2 * z), (ex + 1.5 * z, hy - 2 * z), (ex, hy - 7 * z)])
            pygame.draw.line(s, (255, 196, 220), (ex, hy - 3 * z), (ex, hy - 5.5 * z))
        self.eyes(s, hx + f * 1.5 * z, hy - 0.5 * z, 0.1)

    # the fluffhorn: a wee mountain goat, a cloud of wool on spindly legs, frost on its curled horns
    def draw_goat(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        bob = abs(math.sin(self.step * 0.8)) * 1.2 * z if moving else 0
        leg = (90, 82, 110)
        for i in range(4):
            lx = x + (i - 1.5) * 3 * z
            kick = math.sin(self.step + i * 1.7) * 1.2 * z if moving else 0
            pygame.draw.line(s, leg, (lx, y - 5 * z), (lx + kick, y), max(1, round(z)))
        y -= bob
        wool = mix(self.body, (150, 150, 200), 0.3)
        puffs = [(-4, -9, 4), (0, -10, 4.4), (4, -9, 4), (-2, -7, 4), (2, -7, 4)]
        for px, py, r in puffs:
            pygame.draw.circle(s, wool, (round(x + px * z), round(y + py * z + 1)), round(r * z))
        for px, py, r in puffs:
            pygame.draw.circle(s, self.body, (round(x + px * z), round(y + py * z)), round(r * z - 0.6))
        for px, py in ((-3, -11), (2, -12), (4, -8)):
            s.set_at((round(x + px * z), round(y + py * z)), (255, 255, 255))
        hx, hy = x + f * 7 * z, y - 11 * z
        face = (96, 90, 124)
        pygame.draw.ellipse(s, face, (hx - 2.5 * z, hy - 2 * z, 5 * z, 6 * z))
        pygame.draw.circle(s, self.body, (round(hx - f * 0.5 * z), round(hy - 2.4 * z)), max(2, round(2 * z)))  # a woolly fringe
        horn, horn_d = (226, 220, 246), (150, 140, 190)
        for side in (-1, 1):  # curled horns sweeping back over the fringe
            hx0 = hx + side * 1.4 * z
            pts = [(hx0, hy - 3 * z), (hx0 - f * 1.5 * z, hy - 6 * z), (hx0 - f * 4 * z, hy - 6.5 * z),
                   (hx0 - f * 5 * z, hy - 4.5 * z), (hx0 - f * 4 * z, hy - 3 * z)]
            pygame.draw.lines(s, horn_d if side < 0 else horn, False, pts, max(1, round(1.2 * z)))
        pygame.draw.line(s, face, (hx + f * 2 * z, hy - z), (hx + f * 3.5 * z, hy))  # an ear
        s.set_at((round(hx + f * z), round(hy)), (255, 236, 160))
        s.set_at((round(hx), round(hy + 3 * z)), (40, 30, 60))

    # the steambara: a round, sleepy capybara of the hot springs with a little glowing yuzu on its head
    def draw_capy(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.35)
        for i in range(2):
            lx = x + (i * 2 - 1) * 4 * z
            lift = max(0.0, math.sin(self.step + i * math.pi)) * z if moving else 0
            pygame.draw.rect(s, dark, (lx - z, y - 3 * z - lift, 2.4 * z, 3 * z))
        body = pygame.Rect(0, 0, round(16 * z), round(10 * z))
        body.midbottom = (round(x), round(y - 1 * z))
        pygame.draw.rect(s, dark, body.move(0, 1), border_radius=round(4 * z))
        pygame.draw.rect(s, self.body, body, border_radius=round(4 * z))
        pygame.draw.line(s, mix(self.body, (255, 230, 210), 0.3), (body.x + 3 * z, body.y + z), (body.right - 4 * z, body.y + z))
        head = pygame.Rect(0, 0, round(8 * z), round(7 * z))
        head.midbottom = (round(x + f * 8 * z), round(y - 3 * z))
        pygame.draw.rect(s, self.body, head, border_radius=round(2.5 * z))
        pygame.draw.rect(s, dark, (head.right - 2 * z if f > 0 else head.x, head.y + 3 * z, 2 * z, 2 * z))  # its nose
        ex = head.centerx + f * z
        pygame.draw.line(s, INK, (ex - z, head.y + 2 * z), (ex + z, head.y + 2 * z))  # eyes half shut, content
        pygame.draw.rect(s, dark, (head.centerx - f * 2 * z, head.y - z, 2 * z, 1.6 * z))  # a little ear
        yx, yy = head.centerx - f * z, head.y - 2.5 * z
        pygame.draw.circle(s, (255, 190, 80), (round(yx), round(yy)), max(2, round(2 * z)))
        pygame.draw.line(s, (120, 200, 110), (yx, yy - 2 * z), (yx + 1.5 * z, yy - 3 * z))

    # the ember gecko: a charcoal lizard with cracks of lava glowing through, quick on splayed feet
    def draw_gecko(self, s, t):
        z, f, pts = self.size, self.facing, self.tail
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.4)
        radii = [3.2, 3.4, 3.2, 2.7, 2.2, 1.8, 1.4, 1.1, 0.9, 0.7]
        for i in (1, 3):  # splayed legs, scuttling
            px, py = pts[i]
            for side in (-1, 1):
                step = math.sin(self.step * 1.5 + i + side) * 2 * z if moving else 0
                pygame.draw.line(s, dark, (px, py - 2 * z), (px + f * step + side * z, py), max(1, round(z)))
        for i, (px, py) in reversed(list(enumerate(pts))):
            r = max(1, radii[i] * z)
            pygame.draw.circle(s, dark, (round(px), round(py - 2 * z + 1)), round(r))
        for i, (px, py) in reversed(list(enumerate(pts))):
            pygame.draw.circle(s, self.body, (round(px), round(py - 2 * z)), round(max(1, radii[i] * z)))
        hx, hy = pts[0]
        hx += f * 3 * z
        pygame.draw.ellipse(s, dark, (hx - 4 * z, hy - 6 * z + 1, 9 * z, 5.5 * z))
        pygame.draw.ellipse(s, self.body, (hx - 4 * z, hy - 6 * z, 9 * z, 5.5 * z))
        pygame.draw.line(s, mix(self.body, (255, 220, 200), 0.3), (hx - 2 * z, hy - 5.5 * z), (hx + 2 * z, hy - 5.5 * z))
        ex, ey = round(hx + f * 1.6 * z), round(hy - 4.5 * z)
        pygame.draw.rect(s, (255, 214, 120), (ex - 1, ey - 1, 2, 2))
        s.set_at((ex, ey), INK)

    # Mossprance: a slender fawn with a mantle of moss down its back, dappled with glowing
    # spots, and a lichen sprout between its ears that will one day be a whole tree
    def draw_fawn(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.35)
        for i, lx in enumerate((-4, -2, 3, 5)):
            kick = math.sin(self.step * 1.2 + i * 1.6) * 1.4 * z if moving else 0
            pygame.draw.line(s, dark if i % 2 else mix(self.body, INK, 0.2), (x + lx * z, y - 6 * z),
                             (x + lx * z + kick, y), max(1, round(z)))
        pygame.draw.ellipse(s, dark, (x - 7 * z, y - 11 * z + 1, 14 * z, 7 * z))
        pygame.draw.ellipse(s, self.body, (x - 7 * z, y - 11 * z, 14 * z, 7 * z))
        moss = (110, 176, 130)
        pygame.draw.ellipse(s, moss, (x - 6 * z, y - 11.5 * z, 11 * z, 3.5 * z))  # the moss mantle
        for i in range(5):
            s.set_at((round(x - 5 * z + i * 2.4 * z), round(y - 9 * z + (i % 2))), mix(moss, INK, 0.3))
        pygame.draw.ellipse(s, (250, 240, 226), (x - 3 * z, y - 7 * z, 7 * z, 2.5 * z))  # a pale belly
        pygame.draw.line(s, self.body, (x - f * 7 * z, y - 9 * z), (x - f * 9 * z, y - 11 * z), max(1, round(z)))  # tail
        nx, ny = x + f * 6 * z, y - 12 * z
        pygame.draw.line(s, self.body, (x + f * 4 * z, y - 10 * z), (nx, ny), max(2, round(2.2 * z)))  # neck
        hx, hy = nx + f * 1.5 * z, ny - 2 * z
        pygame.draw.ellipse(s, self.body, (hx - 3 * z, hy - 2.5 * z, 6 * z, 5 * z))
        pygame.draw.ellipse(s, self.body, (hx + f * 1.5 * z - 1.5 * z, hy - 0.5 * z, 4 * z, 3 * z))  # muzzle
        s.set_at((round(hx + f * 3.3 * z), round(hy + 0.5 * z)), INK)
        for e in (-1, 1):  # big soft ears
            ex = hx - f * 1.5 * z + e * 1.2 * z
            pygame.draw.ellipse(s, self.body, (ex - (4 * z if e < 0 else 0), hy - 4 * z, 4 * z, 2.2 * z))
        self.eyes(s, hx + f * 0.8 * z, hy - 0.5 * z, 0.1)
        sx, sy = hx - f * 0.5 * z, hy - 3 * z  # the sprout
        pygame.draw.line(s, moss, (sx, sy), (sx, sy - 3 * z))
        for side in (-1, 1):
            pygame.draw.ellipse(s, (150, 230, 160), (sx + (side - 1) * 1.6 * z + (1 if side > 0 else 0), sy - 4.5 * z, 3.2 * z, 1.8 * z))

    # Kindlet: a tiny pangolin, rows of scales over its back with embers glowing between
    # them; a curled tail with a hot tip. One day it is a knight in molten armour.
    def draw_pangolin(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.4)
        for i in range(2):
            lx = x + (i * 2 - 1) * 3.5 * z
            lift = max(0.0, math.sin(self.step * 1.4 + i * math.pi)) * z if moving else 0
            pygame.draw.rect(s, dark, (lx - z, y - 3 * z - lift, 2.2 * z, 3 * z))
            pygame.draw.line(s, (240, 220, 210), (lx + f * z, y - lift), (lx + f * 2.2 * z, y - lift))  # claws
        tx = x - f * 8 * z
        pygame.draw.circle(s, dark, (round(tx), round(y - 5 * z)), max(2, round(3.4 * z)))  # the curled tail
        pygame.draw.circle(s, self.body, (round(tx), round(y - 5 * z)), max(1, round(2.4 * z)))
        pygame.draw.ellipse(s, dark, (x - 7 * z, y - 11 * z + 1, 14 * z, 10 * z))
        pygame.draw.ellipse(s, self.body, (x - 7 * z, y - 11 * z, 14 * z, 10 * z))
        for row in range(3):  # overlapping scales, row on row
            ry = y - (9.5 - row * 2.6) * z
            n = 3 + row
            for k in range(n):
                cx_ = x - 5 * z + (k + 0.5) * 10 * z / n
                pygame.draw.arc(s, mix(self.body, (255, 230, 220), 0.25), (cx_ - 2 * z, ry - z, 4 * z, 3 * z), 0.2, 2.9, 1)
        hx, hy = x + f * 7 * z, y - 5 * z
        pygame.draw.polygon(s, mix(self.body, (255, 220, 210), 0.35),
                            [(hx - f * 2 * z, hy - 2.5 * z), (hx + f * 4 * z, hy + 0.5 * z), (hx - f * 2 * z, hy + 2 * z)])
        s.set_at((round(hx + f * 4 * z), round(hy + 0.5 * z)), INK)
        self.eyes(s, hx + f * 0.5 * z, hy - 1 * z, 0.1)

    # Pippalotl: a pastel axolotl with a wide smile and three feathery glowing gills on each
    # side of its head; a soft fin down its tail. One day a river dragon wearing them as a crown.
    def draw_axolotl(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.3)
        sway = math.sin(t * 2.5 + self.phase) * z
        tail = [(x - f * (4 + i * 2.2) * z, y - 4 * z + math.sin(t * 3 + i * 0.8 + self.phase) * 0.8 * z * i / 3) for i in range(5)]
        for i, (px, py) in enumerate(tail):  # tail with its fin
            pygame.draw.circle(s, mix(self.body, (255, 255, 255), 0.25), (round(px), round(py - 1.5 * z)), max(1, round((2.6 - i * 0.4) * z)))
            pygame.draw.circle(s, self.body, (round(px), round(py)), max(1, round((2.2 - i * 0.35) * z)))
        for i, lx in enumerate((-3, 3)):
            kick = math.sin(self.step + i * math.pi) * 1.2 * z if moving else 0
            pygame.draw.line(s, dark, (x + lx * z, y - 3 * z), (x + lx * z + kick + f * z, y), max(1, round(z)))
        pygame.draw.ellipse(s, dark, (x - 6 * z, y - 7 * z + 1, 12 * z, 6 * z))
        pygame.draw.ellipse(s, self.body, (x - 6 * z, y - 7 * z, 12 * z, 6 * z))
        hx, hy = x + f * 6 * z, y - 6 * z
        for g in range(3):  # gills, drawn behind the head
            for side in (-1, 1):
                a = -math.pi / 2 - f * 0.9 + side * (0.35 + g * 0.4)
                ln = (5 - g) * z
                gx, gy = hx - f * 2 * z + math.cos(a) * ln, hy - 1 * z + math.sin(a) * ln * (1 if side < 0 else -0.6) + sway * 0.4
                pygame.draw.line(s, (255, 140, 200), (hx - f * 2 * z, hy - 1 * z), (gx, gy), max(1, round(z)))
        pygame.draw.ellipse(s, self.body, (hx - 4.5 * z, hy - 3.5 * z, 9 * z, 6 * z))
        pygame.draw.arc(s, dark, (hx - 2 * z + f * z, hy - 0.5 * z, 4 * z, 2.5 * z), math.pi + 0.3, 2 * math.pi - 0.3)  # smile
        for e in (-1.5, 1.8):
            pygame.draw.circle(s, INK, (round(hx + e * z + f * 0.5 * z), round(hy - 1.5 * z)), max(1, round(0.8 * z)))

    # --- the third wave (2026-10-27): the Forest's bramblit, the Waterfall's runelet, the
    # River's murkling and glintshell ---------------------------------------------------------

    # the bramblit: a ball of tangled bramble on twig legs, two berry-red eyes glinting from inside
    def draw_bramble(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.45)
        for k in (0, math.pi):  # twiggy legs
            lift = max(0.0, math.sin(self.step + k)) * 1.5 * z if moving else 0
            lx = x + (-2 if k else 2) * z
            pygame.draw.line(s, dark, (lx, y - 3 * z), (lx + f * z, y - lift), max(1, round(z)))
        cx, cy, r = x, y - 7 * z, 5.5 * z
        pygame.draw.circle(s, dark, (round(cx), round(cy + 1)), round(r))
        pygame.draw.circle(s, mix(self.body, INK, 0.2), (round(cx), round(cy)), round(r))
        spin = -f * self.x / r * 0.5  # it turns over as it goes
        for i in range(7):  # the stems, looping round and round
            a = spin + i * 0.9
            p = [(cx + math.cos(a + j * 0.7) * r * (0.35 + 0.25 * ((i + j) % 3)),
                  cy + math.sin(a + j * 0.7) * r * (0.35 + 0.25 * ((i + j) % 3))) for j in range(4)]
            pygame.draw.lines(s, self.body if i % 2 else mix(self.body, (150, 210, 160), 0.3), False, p)
        for i in range(8):  # thorns
            a = spin + i * math.tau / 8
            bx, by = cx + math.cos(a) * r, cy + math.sin(a) * r
            pygame.draw.line(s, (220, 200, 210), (bx, by), (bx + math.cos(a + 0.4) * 2 * z, by + math.sin(a + 0.4) * 2 * z))
        pygame.draw.ellipse(s, (110, 200, 140), (cx - f * z - 1.5 * z, cy - r - 2 * z, 3 * z, 2 * z))  # one leaf on top

    # the runelet: a little standing stone on stubby feet, mossy on top, a rune carved in its
    # face that glows, and a ghost-light flickering over its head
    def draw_rune(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        rock, dark = self.body, mix(self.body, INK, 0.4)
        for k in (0, math.pi):
            lift = max(0.0, math.sin(self.step * 0.8 + k)) * 1.2 * z if moving else 0
            pygame.draw.rect(s, dark, (x + (-3 if k else 1) * z, y - 2 * z - lift, 2.5 * z, 2 * z))
        lean = math.sin(self.step * 0.8) * 0.8 * z if moving else 0
        pts = [(x - 5 * z, y - 2 * z), (x - 5.5 * z + lean, y - 11 * z), (x - 2 * z + lean, y - 15 * z),
               (x + 3 * z + lean, y - 14 * z), (x + 5 * z + lean, y - 10 * z), (x + 5 * z, y - 2 * z)]
        pygame.draw.polygon(s, dark, [(px, py + 1) for px, py in pts])
        pygame.draw.polygon(s, rock, pts)
        pygame.draw.line(s, mix(rock, (255, 255, 255), 0.3), pts[1], pts[2])  # a moonlit edge
        pygame.draw.polygon(s, (90, 190, 140), [(x - 4 * z + lean, y - 12.5 * z), (x - 2 * z + lean, y - 14.8 * z),
                                                (x + 3 * z + lean, y - 13.8 * z), (x + 4 * z + lean, y - 11.5 * z),
                                                (x + lean, y - 12 * z)])  # its cap of moss
        self.eyes(s, x + f * z - 1.5 * z + lean, y - 10 * z, 3 * z)

    # the murkling: a blob of night-dark ink that glides along, rippling; two stalk eyes with
    # glowing green tips, and bubbles of something unwholesome rising off it
    def draw_murk(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        dark = mix(self.body, INK, 0.4)
        w = 8 * z + (math.sin(self.step * 1.2) * 1.2 * z if moving else math.sin(t * 1.5 + self.phase) * 0.6 * z)
        h = 7 * z - (w - 8 * z) * 0.6
        pygame.draw.ellipse(s, dark, (x - w, y - h + 1, 2 * w, h))
        pygame.draw.ellipse(s, self.body, (x - w, y - h, 2 * w, h))
        for i in range(-3, 4):  # a rippling skirt where it meets the ground
            pygame.draw.circle(s, self.body, (round(x + i * w / 3.6), round(y - z)),
                               max(1, round((1.2 + 0.5 * math.sin(t * 4 + i + self.step)) * z)))
        pygame.draw.ellipse(s, mix(self.body, (160, 230, 220), 0.35), (x - w * 0.6, y - h * 0.9, w * 0.7, h * 0.3))  # a wet sheen
        sway = math.sin(t * 2.2 + self.phase) * z
        self._tips = []
        for side in (0, 1):
            bx, by = x + f * (2 + side * 2.5) * z, y - h + 1.5 * z
            tip = (bx + f * z + sway * (1 if side else -0.6), by - (5 + side) * z)
            pygame.draw.line(s, dark, (bx, by), tip, max(1, round(z)))
            self._tips.append(tip)

    # the glintshell: a shy little thing under a dome of hammered silver, rivets round its rim
    # and a gleam of moonlight sliding over it; poke it and it pulls in underneath
    def draw_glint(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        shy = swell(t - self.poked, 0.1, 2.0)
        dark = mix(self.body, INK, 0.5)
        skin = (120, 96, 150)
        if shy < 0.9:
            for i in range(4):
                lx = x + (i - 1.5) * 3 * z
                kick = math.sin(self.step * 1.3 + i * 1.6) * 1.2 * z if moving else 0
                pygame.draw.line(s, skin, (lx, y - 3 * z), (lx + kick, y), max(1, round(z)))
            hx, hy = x + f * (9.5 - 6 * shy) * z, y - 3.5 * z
            pygame.draw.ellipse(s, skin, (hx - 2.5 * z, hy - 2.5 * z, 5 * z, 4 * z))
            self.eyes(s, hx - z + f * 0.5 * z, hy - 1.2 * z, 2 * z)
        dome = pygame.Rect(round(x - 8 * z), round(y - 12 * z), round(16 * z), round(18 * z))
        was = s.get_clip()  # only its top: a dome
        s.set_clip(pygame.Rect(dome.x - 1, dome.y - 1, dome.w + 2, round(10 * z) + 2).clip(was))
        pygame.draw.ellipse(s, dark, dome.move(0, 1))
        pygame.draw.ellipse(s, self.body, dome)
        for dx, dy in ((-3, -8), (2, -9), (-1, -5), (4, -6)):  # hammered dimples
            s.set_at((round(x + dx * z), round(y + dy * z)), mix(self.body, INK, 0.25))
        g = (t * 0.25 + self.phase) % 1.6 - 0.3  # now and then a gleam slides across
        if 0 <= g <= 1:
            gx = dome.x + g * dome.w
            pygame.draw.line(s, (255, 255, 255), (gx, dome.y + 2 * z), (gx - 2 * z, dome.y + 8 * z))
        s.set_clip(was)
        pygame.draw.line(s, dark, (x - 8 * z, y - 2 * z), (x + 8 * z, y - 2 * z), max(1, round(z)))
        for i in range(-3, 4, 2):  # rivets round the rim
            s.set_at((round(x + i * 2 * z), round(y - 3 * z)), (240, 244, 255))

    def light(self, lm, t):
        if self.kind in ("fawn", "pangolin", "axolotl"):
            glow(lm, self.x, self.y - 8 * self.size, int(22 * self.size), self.color, q(40 + 12 * math.sin(t * 2 + self.phase)))
        if self.kind in ("fox", "gecko", "capy"):
            glow(lm, self.x, self.y - 6 * self.size, int(20 * self.size), self.color, q(36 + 12 * math.sin(t * 2 + self.phase)))
        if self.kind in ("sporeling", "beetle", "mole", "bramble", "rune", "murk", "glint") or self.kind in LIT:
            glow(lm, self.x, self.y - 8 * self.size, int(22 * self.size), self.color, q(40 + 15 * math.sin(t * 2 + self.phase)))

    def shine(self, s, t):
        stage = getattr(self, "stage", 1)
        fn = getattr(self, f"shine_{self.kind}{stage}", None) if stage > 1 else None
        if fn:
            fn(s, t, swell(t - self.poked, 0.1, 0.8))
        else:
            self.shine_base(s, t)
        lit = getattr(self, "glow_" + self.kind, None)
        if lit and (stage > 1 or self.kind in LIT):
            lit(s, t, stage, swell(t - self.poked, 0.1, 0.8))

    def shine_base(self, s, t, _k=None):
        z, x, y, f = self.size, self.x, self.y, self.facing
        k = swell(t - self.poked, 0.1, 0.8)
        if self.kind == "sporeling":
            big = getattr(self, "stage", 1) > 1
            if big:
                y -= 4 * z
                sx0 = x - f * 7 * z
                for i in range(3):
                    b = 0.5 + 0.5 * math.sin(t * 2.4 + i * 2 + self.phase)
                    s.set_at((round(sx0 + (i - 1) * 2 * z), round(y - 19.5 * z)), mix(self.color, (255, 255, 255), 0.4 + 0.5 * b))
            for i, (sx, sy) in enumerate(((-5, -14), (0, -15), (4, -13), (-2, -12), (6, -11), (-6, -11), (2, -16))[:7 if big else 5]):
                b = 0.5 + 0.5 * math.sin(t * 2 + i * 1.3 + self.phase)
                s.set_at((round(x + sx * z), round(y + sy * z)), mix(self.color, (255, 255, 255), 0.4 + 0.5 * b))
            glow(s, x, y - 13 * z, int(10 * z), self.color, q(40 + 90 * k))
        elif self.kind == "mole":
            st = getattr(self, "stage", 1)
            if st > 1:  # glowing mushrooms in its moss
                for j, mx in enumerate((-4, 1, 4)[:2 + (st > 2)]):
                    b = 0.6 + 0.4 * math.sin(t * 1.8 + j * 2 + self.phase)
                    my = y - (10 + (st > 2) * 3) * z
                    pygame.draw.ellipse(s, mix(self.color, (255, 255, 255), 0.3), (x + mx * z - 1.5 * z, my - 1.5 * z, 3 * z, 1.6 * z))
                    glow(s, x + mx * z, my, int(4 * z), self.color, q(70 * b))
            if st > 2 and self.wait <= 0:  # the ground cracks with light as it walks
                for j in range(3):
                    cx = x - f * (4 + j * 4) * z
                    if math.sin(t * 5 + j) > 0:
                        pygame.draw.line(s, (160, 230, 255), (cx, y), (cx + 2 * z, y + 1.5 * z))
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
        elif self.kind == "fox":
            sway = math.sin(t * 2 + self.phase) * 1.5 * z
            tx, ty = x - f * 12 * z, y - 15 * z + sway
            c = AURORA[int(t * 0.8 + self.phase) % len(AURORA)]
            glow(s, tx, ty, int(9 * z), c, q(80 + 60 * k))
            pygame.draw.circle(s, mix(c, (255, 255, 255), 0.4), (round(tx), round(ty)), max(1, round(2 * z)))
        elif self.kind == "goat":
            hx, hy = x + f * 7 * z, y - 11 * z
            for side in (-1, 1):  # frost glittering on its horns
                if math.sin(t * 2.2 + side + self.phase) > 0:
                    s.set_at((round(hx + side * 2.5 * z), round(hy - 5 * z)), (220, 245, 255))
            if k > 0:
                glow(s, hx, hy - 4 * z, int(8 * z), self.color, q(90 * k))
        elif self.kind == "capy":
            hx = x + f * 8 * z - f * z
            yy = y - 3 * z - 7 * z - 2.5 * z
            glow(s, hx, yy, int(7 * z), self.color, q(70 + 20 * math.sin(t * 1.5 + self.phase) + 60 * k))
            for i in range(2):  # a wisp of steam off its warm back
                kk = (t * 0.4 + i * 0.5 + self.phase) % 1.0
                s.set_at((round(x - f * 2 * z + math.sin(t + i * 3) * 2 * z), round(y - 12 * z - kk * 10 * z)),
                         mix((230, 226, 255), (40, 30, 70), kk))
        elif self.kind == "gecko":
            for i in (0, 2, 4, 6):  # lava glowing through the cracks down its back
                px, py = self.tail[i]
                b = 0.5 + 0.5 * math.sin(t * 2.5 - i * 0.8 + self.phase)
                c = mix(self.color, (255, 236, 160), b * 0.6)
                s.set_at((round(px), round(py - 2 * z - (2.6 - i * 0.25) * z * 0.6)), c)
                if i < 4:
                    s.set_at((round(px + z), round(py - 2 * z)), mix(c, self.body, 0.4))
            glow(s, x, y - 3 * z, int(10 * z), self.color, q(40 + 80 * k))
        elif self.kind == "fawn":  # its dapples and its sprout glow
            hx, hy = x + f * 7.5 * z, y - 14 * z
            b = 0.5 + 0.5 * math.sin(t * 1.8 + self.phase)
            glow(s, hx - f * 0.5 * z, hy - 6 * z, int(7 * z), self.color, q(60 + 40 * b + 60 * k))
            for i, (dx, dy) in enumerate(((-4, -9.5), (-1, -10), (2, -9.5), (-2.5, -8))):
                if math.sin(t * 1.3 + i * 1.7 + self.phase) > -0.3:
                    s.set_at((round(x + dx * z), round(y + dy * z)), mix(self.color, (255, 255, 255), 0.5))
        elif self.kind == "pangolin":  # embers between its scales
            for row in range(3):
                ry = y - (8.5 - row * 2.6) * z
                n = 3 + row
                for kk in range(n):
                    b = 0.5 + 0.5 * math.sin(t * 2.2 + row + kk * 1.3 + self.phase)
                    if b > 0.35:
                        s.set_at((round(x - 5 * z + (kk + 0.5) * 10 * z / n + 2 * z), round(ry)), mix(self.color, (255, 236, 160), b * 0.5))
            tx = x - f * 8 * z
            glow(s, tx, y - 7 * z, int(6 * z), self.color, q(70 + 60 * k))
            s.set_at((round(tx), round(y - 8 * z)), (255, 220, 140))
        elif self.kind == "axolotl":  # the gill tips glow
            hx, hy = x + f * 6 * z, y - 6 * z
            sway = math.sin(t * 2.5 + self.phase) * z
            for g in range(3):
                for side in (-1, 1):
                    a = -math.pi / 2 - f * 0.9 + side * (0.35 + g * 0.4)
                    ln = (5 - g) * z
                    gx, gy = hx - f * 2 * z + math.cos(a) * ln, hy - 1 * z + math.sin(a) * ln * (1 if side < 0 else -0.6) + sway * 0.4
                    s.set_at((round(gx), round(gy)), (255, 200, 236))
            glow(s, hx - f * 2 * z, hy - 4 * z, int(8 * z), self.color, q(50 + 70 * k))
        elif self.kind == "bramble":  # its berry eyes, glinting from inside the tangle
            cx, cy = x + f * 1.5 * z, y - 7 * z
            if (t * 0.5 + self.phase) % 4 > 0.15:
                for ex in (-1.6, 1.6):
                    pygame.draw.circle(s, self.color, (round(cx + ex * z), round(cy)), max(1, round(z)))
                    s.set_at((round(cx + ex * z), round(cy - z * 0.5)), (255, 220, 230))
            glow(s, cx, cy, int(7 * z), self.color, q(40 + 80 * k))
        elif self.kind == "rune":  # the rune on its face, and the ghost-light over its head
            b = 0.6 + 0.4 * math.sin(t * 1.7 + self.phase)
            c = mix(self.color, (255, 255, 255), 0.3 * b)
            rx, ry = x + f * 0.5 * z, y - 6 * z
            for (ax, ay), (bx, by) in (((0, -2.5), (0, 2.5)), ((0, -1), (1.5, -2.5)), ((0, 0.5), (-1.5, -1))):
                pygame.draw.line(s, c, (rx + ax * z, ry + ay * z), (rx + bx * z, ry + by * z))
            glow(s, rx, ry, int(8 * z), self.color, q(50 * b + 70 * k))
            fx, fy = x + math.sin(t * 2 + self.phase) * z, y - 18 * z - abs(math.sin(t * 3)) * z
            flick = 0.7 + 0.3 * math.sin(t * 9 + self.phase)
            glow(s, fx, fy, int(7 * z), self.color, q(70 * flick + 60 * k))
            pygame.draw.circle(s, mix(self.color, (255, 255, 255), 0.5), (round(fx), round(fy)), max(1, round(1.4 * z)))
            s.set_at((round(fx), round(fy - 2 * z)), self.color)
        elif self.kind == "murk":  # glowing eye-tips, and bubbles rising off it
            for tx, ty in getattr(self, "_tips", ()):
                glow(s, tx, ty, int(5 * z), self.color, q(90 + 60 * k))
                pygame.draw.circle(s, self.color, (round(tx), round(ty)), max(1, round(1.2 * z)))
                s.set_at((round(tx + f * 0.5 * z), round(ty)), INK)
            for i in range(3):
                kk = (t * 0.5 + i / 3 + self.phase) % 1.0
                bx = x - f * 2 * z + math.sin(t * 1.7 + i * 2) * 3 * z
                pygame.draw.circle(s, mix(self.color, (40, 30, 70), kk), (round(bx), round(y - 6 * z - kk * 12 * z)),
                                   max(1, round((1.4 - kk * 0.6) * z)), 1)
        elif self.kind == "glint":  # a blue seam of light glows round its rim
            b = 0.5 + 0.5 * math.sin(t * 1.4 + self.phase)
            for i in range(-6, 7):
                if (i + int(t * 4)) % 4 == 0 or k > 0:
                    s.set_at((round(x + i * z), round(y - 2 * z)), mix(self.color, (255, 255, 255), 0.4))
            glow(s, x, y - 3 * z, int(9 * z), self.color, q(30 + 30 * b + 80 * k))
        elif self.kind == "toad" and k > 0:
            glow(s, x, y - 6 * z, int(12 * z), self.color, q(80 * k))

    # --- the starters' later stages (2026-10-27) ------------------------------------------
    # Each is drawn by draw_<kind><stage> / shine_<kind><stage> when there is one.

    def antler(self, s, x, y, ln, ang, depth, color, tips):
        """One branching antler tine; its ends are collected in `tips`."""
        ex, ey = x + math.cos(ang) * ln, y + math.sin(ang) * ln
        pygame.draw.line(s, color, (round(x), round(y)), (round(ex), round(ey)), max(1, round(self.size * (0.5 + depth * 0.35))))
        if depth <= 0:
            tips.append((ex, ey))
            return
        self.antler(s, ex, ey, ln * 0.72, ang - 0.45, depth - 1, color, tips)
        self.antler(s, ex, ey, ln * 0.62, ang + 0.5, depth - 1, color, tips)

    def head_of_fawn(self):
        z, x, y, f = self.size, self.x, self.y, self.facing
        nx, ny = x + f * 6 * z, y - 12 * z
        return nx + f * 1.5 * z, ny - 2 * z

    # Lichenmane: the fawn grown into a young stag, its first antlers hung with moss
    def draw_fawn2(self, s, t):
        self.draw_fawn(s, t)
        z, f = self.size, self.facing
        hx, hy = self.head_of_fawn()
        bone, moss = (232, 218, 196), (120, 186, 136)
        self.tips = []
        for side in (-1, 1):
            bx = hx - f * 0.5 * z + side * 1.2 * z
            self.antler(s, bx, hy - 2.5 * z, 3.4 * z, -math.pi / 2 + side * 0.35 - f * 0.25, 1, bone, self.tips)
        for i, (tx, ty) in enumerate(self.tips):  # moss draped from the tines
            if i % 2 == 0:
                sway = math.sin(t * 1.5 + i) * 0.6 * z
                pygame.draw.line(s, moss, (round(tx), round(ty)), (round(tx + sway), round(ty + 3 * z)))
        x, y = self.x, self.y
        for i in range(4):  # lichen patches on the mantle
            s.set_at((round(x - 4 * z + i * 2.5 * z), round(y - 10.5 * z)), (200, 236, 190))

    # Eldermane: an ancient spirit stag, grey-green and half there, its antlers a whole moss-hung
    # tree with little spirit lanterns at the tips, mist where its hooves should be
    def draw_fawn3(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        moving = self.wait <= 0
        coat = (176, 196, 186)
        dark = mix(coat, INK, 0.4)
        moss = (96, 160, 122)
        for i, lx in enumerate((-5, -2.5, 3, 5.5)):  # long legs fading into mist
            kick = math.sin(self.step * 1.0 + i * 1.6) * 1.2 * z if moving else 0
            top = (x + lx * z, y - 8 * z)
            foot = (x + lx * z + kick, y - 1 * z)
            pygame.draw.line(s, dark if i % 2 else coat, top, foot, max(1, round(1.1 * z)))
        pygame.draw.ellipse(s, dark, (x - 9 * z, y - 15 * z + 1, 18 * z, 8 * z))
        pygame.draw.ellipse(s, coat, (x - 9 * z, y - 15 * z, 18 * z, 8 * z))
        # its mantle: a heavy fall of moss over the back, hanging in strands
        pygame.draw.ellipse(s, moss, (x - 8 * z, y - 16 * z, 15 * z, 5 * z))
        for i in range(7):
            sx = x - 7 * z + i * 2.2 * z
            ln = (3 + (i * 5) % 4) * z
            sway = math.sin(t * 1.2 + i * 0.9) * 0.5 * z
            pygame.draw.line(s, mix(moss, INK, 0.2), (sx, y - 12.5 * z), (sx + sway, y - 12.5 * z + ln))
        pygame.draw.line(s, coat, (x - f * 9 * z, y - 13 * z), (x - f * 11 * z, y - 14 * z), max(1, round(z)))
        nx, ny = x + f * 7 * z, y - 17 * z
        pygame.draw.line(s, coat, (x + f * 5 * z, y - 13 * z), (nx, ny), max(2, round(2.4 * z)))
        hx, hy = nx + f * 1.5 * z, ny - 2 * z
        pygame.draw.ellipse(s, coat, (hx - 3 * z, hy - 2.5 * z, 6 * z, 5 * z))
        pygame.draw.ellipse(s, coat, (hx + f * 1.5 * z - 1.5 * z, hy - 0.5 * z, 4.5 * z, 3 * z))
        s.set_at((round(hx + f * 3.6 * z), round(hy + 0.5 * z)), INK)
        for e in (-1, 1):
            ex = hx - f * 1.5 * z + e * 1.4 * z
            pygame.draw.ellipse(s, coat, (ex - (4 * z if e < 0 else 0), hy - 3.5 * z, 4 * z, 2 * z))
        # the antlers: a tree of tines
        bone = (214, 206, 190)
        self.tips = []
        for side in (-1, 1):
            bx = hx - f * 0.5 * z + side * 1.2 * z
            self.antler(s, bx, hy - 2.5 * z, 4.6 * z, -math.pi / 2 + side * 0.4 - f * 0.2, 3, bone, self.tips)
        for i, (tx, ty) in enumerate(self.tips):  # moss hanging off the antlers
            if i % 3 == 0:
                sway = math.sin(t * 1.3 + i) * 0.7 * z
                pygame.draw.line(s, moss, (round(tx), round(ty)), (round(tx + sway), round(ty + 4 * z)))

    def shine_fawn3(self, s, t, k):
        z, x, y, f = self.size, self.x, self.y, self.facing
        hx, hy = self.head_of_fawn()
        hx, hy = x + f * 8.5 * z, y - 19 * z
        for e in (0.3, 2.2):  # pale glowing eyes
            s.set_at((round(hx + f * e * z - f * z), round(hy - 0.5 * z)), (200, 255, 236))
        for i, (tx, ty) in enumerate(getattr(self, "tips", [])):  # spirit lanterns on the tines
            if i % 2:
                continue
            b = 0.6 + 0.4 * math.sin(t * 1.6 + i * 1.3 + self.phase)
            c = (150, 255, 210) if i % 4 == 0 else (190, 170, 255)
            ly = ty + 2 * z + math.sin(t * 1.4 + i) * 0.5 * z
            glow(s, tx, ly, int(5 * z), c, q(70 * b + 50 * k))
            s.set_at((round(tx), round(ly)), mix(c, (255, 255, 255), 0.6))
        for i in range(4):  # mist curling round its hooves
            kk = (t * 0.5 + i * 0.25 + self.phase) % 1.0
            mx = x + (i - 1.5) * 3.2 * z + math.sin(t + i) * z
            my = y - 1 * z - kk * 3 * z
            glow(s, mx, my, int(3 * z), (190, 230, 220), q(60 * (1 - kk)))

    # Smoldershell and Pyreclad (his pick, 2026-10-27: "volcanic armadillo knight", on 2 or 4
    # legs like Swampert or Typhlosion): obsidian scales cracked with glowing lava. It walks on
    # all fours and rises onto its hind legs whenever it stops (and in a battle, it stands tall).
    # Pyreclad is the grown knight: a crown of scale spikes, a cape of plates down its back, and
    # long bone-white claws like blades.

    def knight(self, t):
        """Where its body is: (hip, chest, head, back normal, torso dir, how upright 0..1)."""
        z, x, y, f = self.size, self.x, self.y, self.facing
        now = t
        dt = max(0.0, min(0.1, now - getattr(self, "_rt", now)))
        self._rt = now
        want = 0.0  # it stays on all fours (his rule, 2026-10-27: no creature stands like a person)
        self.rear = getattr(self, "rear", want)
        self.rear += (want - self.rear) * min(1.0, dt * 2.5)
        r = self.rear * self.rear * (3 - 2 * self.rear)
        big = getattr(self, "stage", 1) >= 3
        L = (10 if big else 8.5) * z
        a = r * 1.2
        hip = (x - f * 3 * z, y - 6 * z - r * 1.5 * z)
        d = (f * math.cos(a), -math.sin(a))
        chest = (hip[0] + d[0] * L, hip[1] + d[1] * L)
        n = (-f * math.sin(a), -math.cos(a))
        ha = a * 0.15  # the head looks ahead, whichever way it stands
        head = (chest[0] + f * math.cos(ha) * 4 * z + n[0] * 1.5 * z, chest[1] - math.sin(ha) * 4 * z + n[1] * 1.5 * z)
        return hip, chest, head, n, d, r

    def draw_pangolin2(self, s, t):
        self.draw_knight(s, t)

    def draw_pangolin3(self, s, t):
        self.draw_knight(s, t)

    def draw_knight(self, s, t):
        z, x, y, f = self.size, self.x, self.y, self.facing
        big = getattr(self, "stage", 1) >= 3
        hip, chest, head, n, d, r = self.knight(t)
        moving = self.wait <= 0
        rock, rock_l, rock_d = ((92, 84, 116), (150, 140, 176), (46, 40, 62)) if big else ((112, 88, 106), (166, 138, 154), (58, 42, 58))
        bone = (236, 226, 214)
        w = max(1, round((2.2 if big else 1.8) * z))
        # the tail: thick at the hip, resting on the ground behind, an ember at its tip
        tail = []
        for i in range(6):
            k = i / 5
            tail.append((hip[0] - f * (1.5 + i * (2.2 if big else 1.8)) * z, hip[1] + (y - 1.5 * z - hip[1]) * k ** 0.8))
        self.tail_tip = tail[-1]
        for i, (px, py) in enumerate(tail):
            pygame.draw.circle(s, rock_d, (round(px), round(py) + 1), max(1, round((3.4 - i * 0.5) * z * (1.15 if big else 1))))
            pygame.draw.circle(s, rock, (round(px), round(py)), max(1, round((3.2 - i * 0.5) * z * (1.15 if big else 1))))
        # hind legs: thigh, knee, a broad foot, always on the ground
        for k, side in ((0.0, 1), (math.pi, -1)):
            step = math.sin(self.step * 1.3 + k) * 1.5 * z if moving else 0
            knee = (hip[0] + f * 2 * z, hip[1] + 3 * z)
            foot = (hip[0] + f * 0.5 * z + step, y)
            c = rock_d if side < 0 else rock
            pygame.draw.line(s, c, hip, knee, w + 1)
            pygame.draw.line(s, c, knee, foot, w)
            pygame.draw.line(s, c, (foot[0] - f * z, y), (foot[0] + f * 2 * z, y), w)
        # the torso: a chain of discs from hip to chest, scaled on its back
        R0, R1 = (5.4 if big else 4.4) * z, (5.0 if big else 4.0) * z
        steps = 7
        for i in range(steps + 1):
            k = i / steps
            px, py = hip[0] + (chest[0] - hip[0]) * k, hip[1] + (chest[1] - hip[1]) * k
            pygame.draw.circle(s, rock_d, (round(px), round(py) + 1), round(R0 + (R1 - R0) * k))
        for i in range(steps + 1):
            k = i / steps
            px, py = hip[0] + (chest[0] - hip[0]) * k, hip[1] + (chest[1] - hip[1]) * k
            pygame.draw.circle(s, rock, (round(px), round(py)), round(R0 + (R1 - R0) * k))
        # its pale, plated underside
        for i in range(1, steps):
            k = i / steps
            px, py = hip[0] + (chest[0] - hip[0]) * k, hip[1] + (chest[1] - hip[1]) * k
            rr = R0 + (R1 - R0) * k
            bx, by = px - n[0] * rr * 0.65, py - n[1] * rr * 0.65
            pygame.draw.line(s, rock_l, (bx - d[0] * z, by - d[1] * z), (bx + d[0] * z, by + d[1] * z), max(1, round(z)))
        # scales: rows of overlapping arcs down the back
        for i in range(steps):
            k = (i + 0.5) / steps
            px, py = hip[0] + (chest[0] - hip[0]) * k, hip[1] + (chest[1] - hip[1]) * k
            rr = R0 + (R1 - R0) * k
            for row in (0.45, 0.85):  # each scale: a lit upper edge with a dark seam under it
                sx, sy = px + n[0] * rr * row, py + n[1] * rr * row
                a0 = (sx - d[0] * 1.3 * z, sy - d[1] * 1.3 * z)
                a1 = (sx + d[0] * 1.3 * z + n[0] * 0.8 * z, sy + d[1] * 1.3 * z + n[1] * 0.8 * z)
                pygame.draw.line(s, rock_l, a0, a1)
                pygame.draw.line(s, rock_d, (a0[0] - n[0], a0[1] - n[1]), (a1[0] - n[0], a1[1] - n[1]))
        if big:  # the cape: a fall of plates from the shoulders down its back
            cape = [(chest[0] + n[0] * R1, chest[1] + n[1] * R1),
                    (hip[0] + n[0] * (R0 + 2.5 * z) - d[0] * 2 * z, hip[1] + n[1] * (R0 + 2.5 * z) - d[1] * 2 * z),
                    (hip[0] - d[0] * 5 * z, hip[1] + 4 * z), (hip[0] + n[0] * R0 * 0.3, hip[1] + n[1] * R0 * 0.3)]
            pygame.draw.polygon(s, mix(rock, rock_d, 0.5), cape)
            pygame.draw.lines(s, rock_l, False, cape[:2])
            for k in range(1, 4):  # its plate lines
                a0 = cape[0][0] + (cape[1][0] - cape[0][0]) * k / 4, cape[0][1] + (cape[1][1] - cape[0][1]) * k / 4
                pygame.draw.line(s, rock_l, a0, (a0[0] - d[0] * 3 * z + n[0] * z, a0[1] - d[1] * 3 * z + n[1] * z))
        # front limbs: legs to the ground on all fours, clawed arms when it stands
        for side in (1, -1):
            sh = (chest[0] - n[0] * 1.5 * z + side * 0.6 * z, chest[1] - n[1] * 1.5 * z)
            ground = (chest[0] + f * (1 + (math.sin(self.step * 1.3 + side) * 1.5 if moving else 0)) * z, y)
            arm = (sh[0] + f * 3.5 * z, sh[1] + 3 * z)
            hand = (ground[0] + (arm[0] - ground[0]) * r, ground[1] + (arm[1] - ground[1]) * r)
            elbow = ((sh[0] + hand[0]) / 2 - f * r * 1.2 * z, (sh[1] + hand[1]) / 2 + r * 0.8 * z)
            c = rock_d if side < 0 else rock
            pygame.draw.line(s, c, sh, elbow, w)
            pygame.draw.line(s, c, elbow, hand, w)
            ln = (4.5 if big else 2.2) * z  # claws: blades on the knight
            for cl in (-1, 0, 1):
                tip = (hand[0] + f * ln, hand[1] + cl * 0.9 * z + (0.8 * z if r < 0.5 else 0))
                pygame.draw.line(s, bone, hand, tip, max(1, round(0.6 * z)))
        # the head: a long armoured snout, pointed forward
        hx, hy = head
        hr = (3.2 if big else 2.8) * z
        pygame.draw.circle(s, rock_d, (round(hx), round(hy) + 1), round(hr))
        pygame.draw.circle(s, rock, (round(hx), round(hy)), round(hr))
        snout = [(hx + f * hr * 0.6, hy - hr * 0.6), (hx + f * (hr + 3.6 * z), hy + 0.6 * z), (hx + f * hr * 0.6, hy + hr * 0.7)]
        pygame.draw.polygon(s, rock, snout)
        pygame.draw.line(s, rock_l, snout[0], snout[1])
        s.set_at((round(snout[1][0]), round(snout[1][1])), (20, 12, 20))
        if big:  # a crown of scale spikes sweeping back
            for i, (ln, up) in enumerate(((5, 0.9), (6.5, 0.5), (5, 0.15))):
                base = (hx - f * 0.5 * z, hy - hr * 0.7)
                tip = (base[0] - f * ln * z * math.cos(up), base[1] - ln * z * math.sin(up) - 1.5 * z)
                pygame.draw.polygon(s, rock_l if i == 1 else rock, [(base[0] - f * z, base[1] + z), (base[0] + f * z, base[1]), tip])
        else:  # a brow plate
            pygame.draw.polygon(s, rock_l, [(hx - f * 2 * z, hy - hr * 0.8), (hx + f * 1.5 * z, hy - hr), (hx - f * 0.5 * z, hy - hr - 2 * z)])
        self.knight_head = (hx, hy, hr)

    def shine_pangolin2(self, s, t, k):
        self.shine_knight(s, t, k)

    def shine_pangolin3(self, s, t, k):
        self.shine_knight(s, t, k)

    def shine_knight(self, s, t, k):
        if not hasattr(self, "knight_head"):
            return
        z, f = self.size, self.facing
        big = getattr(self, "stage", 1) >= 3
        hip, chest, head, n, d, r = self.knight(t)
        lava, hot = self.color, (255, 232, 150)
        # lava glowing through the cracks between its scales
        for i in range(9):
            kk = (i + 0.5) / 9
            px, py = hip[0] + (chest[0] - hip[0]) * kk, hip[1] + (chest[1] - hip[1]) * kk
            off = (0.3 + 0.35 * ((i * 7) % 3) / 2) * (5 if big else 4) * z
            cx, cy = px + n[0] * off, py + n[1] * off
            b = 0.5 + 0.5 * math.sin(t * 2.2 + i * 1.3 + self.phase)
            c = mix(lava, hot, b * 0.6)
            s.set_at((round(cx), round(cy)), c)
            s.set_at((round(cx + d[0] * z), round(cy + d[1] * z + (1 if i % 2 else -1))), mix(c, (60, 20, 20), 0.3))
        hx, hy, hr = self.knight_head
        ex, ey = round(hx + f * hr * 0.3), round(hy - hr * 0.25)
        pygame.draw.rect(s, (255, 200, 90), (ex - 1, ey, 2 if not big else 3, 1))  # a burning eye
        glow(s, ex, ey, int(4 * z), lava, q(70 + 40 * k))
        tx, ty = getattr(self, "tail_tip", (hip[0], hip[1]))
        for i in range(4 if big else 3):  # the tail tip smoulders
            a = t * 7 + i * 1.7 + self.phase
            pygame.draw.line(s, mix(hot, (255, 90, 40), i / 4), (tx, ty), (tx + math.sin(a) * z, ty - (2.5 + abs(math.cos(a)) * 2) * z), 1)
        glow(s, tx, ty - 2 * z, int((8 if big else 6) * z), lava, q(90 + 50 * k))
        if big:  # a molten heart in its chest
            glow(s, chest[0] - n[0] * 2 * z, chest[1] - n[1] * 2 * z, int(9 * z), lava, q(60 + 30 * math.sin(t * 2) + 50 * k))

    # Frillotl: the axolotl grown longer, a second, bigger ruff of gills and a fin down its back
    def draw_axolotl2(self, s, t):
        self.draw_axolotl(s, t)
        z, x, y, f = self.size, self.x, self.y, self.facing
        hx, hy = x + f * 6 * z, y - 6 * z
        sway = math.sin(t * 2.5 + self.phase) * z
        for g in range(4):  # the bigger outer gills
            for side in (-1, 1):
                a = -math.pi / 2 - f * 1.0 + side * (0.3 + g * 0.36)
                ln = (7 - g) * z
                gx = hx - f * 2.5 * z + math.cos(a) * ln
                gy = hy - 1.5 * z + math.sin(a) * ln * (1 if side < 0 else -0.6) + sway * 0.5
                pygame.draw.line(s, (240, 110, 190), (hx - f * 2.5 * z, hy - 1.5 * z), (gx, gy), max(1, round(z)))
        for i in range(5):  # a soft fin along the back
            fx = x - f * (i * 2.2 - 3) * z
            pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.35), (fx, y - 7 * z), (fx - f * z, y - (9 - i * 0.3) * z))

    def shine_axolotl2(self, s, t, k):
        self.shine_base(s, t, k)
        z, x, y = self.size, self.x, self.y
        for i in range(4):  # teal spots down its sides
            b = 0.5 + 0.5 * math.sin(t * 1.8 + i * 1.6 + self.phase)
            s.set_at((round(x - 4 * z + i * 2.6 * z), round(y - 4 * z)), mix((120, 240, 230), (255, 255, 255), b * 0.4))

    # Leviolotl: a great river dragon, long and sinuous, the axolotl's gills now a crown of
    # glowing fronds, with little horns, whiskers, and a fin all down its back
    def draw_axolotl3(self, s, t):
        z, f, pts = self.size, self.facing, self.tail
        body, belly = (232, 150, 200), (255, 214, 232)
        dark = mix(body, INK, 0.35)
        n = len(pts)
        wave = [math.sin(t * 2.4 - i * 0.7 + self.phase) * 1.6 * z * (i / n) for i in range(n)]
        radii = [3.4, 3.8, 3.8, 3.6, 3.3, 3.0, 2.6, 2.2, 1.8, 1.4]
        for i in (1, 4):  # four stubby legs
            px, py = pts[i]
            for side in (-1, 1):
                step = math.sin(self.step + i + side) * 1.5 * z if self.wait <= 0 else 0
                pygame.draw.line(s, dark, (px, py - 2 * z + wave[i]), (px + f * step + side * 1.2 * z, py), max(1, round(1.2 * z)))
        for i in reversed(range(n)):
            px, py = pts[i]
            pygame.draw.circle(s, dark, (round(px), round(py - 3 * z + wave[i] + 1)), max(1, round(radii[i] * z)))
        for i in reversed(range(n)):
            px, py = pts[i]
            r = max(1, round(radii[i] * z))
            pygame.draw.circle(s, body, (round(px), round(py - 3 * z + wave[i])), r)
            pygame.draw.circle(s, belly, (round(px), round(py - 3 * z + wave[i] + r * 0.5)), max(1, round(r * 0.45)))
        for i in range(1, n - 1):  # the fin along its back
            px, py = pts[i]
            top = py - 3 * z + wave[i] - radii[i] * z
            pygame.draw.line(s, (130, 220, 230), (round(px), round(top)), (round(px - f * z), round(top - (2.4 - i * 0.15) * z)))
        hx, hy = pts[0]
        hx, hy = hx + f * 4 * z, hy - 5 * z + wave[0]
        pygame.draw.ellipse(s, dark, (hx - 5 * z, hy - 3.5 * z + 1, 11 * z, 7 * z))
        pygame.draw.ellipse(s, body, (hx - 5 * z, hy - 3.5 * z, 11 * z, 7 * z))
        pygame.draw.ellipse(s, body, (hx + f * 3 * z - 2.5 * z, hy - 1 * z, 6 * z, 4 * z))  # snout
        for side in (-1, 1):  # horns
            hb = hx - f * 1 * z + side * 1.5 * z
            pygame.draw.line(s, (250, 236, 220), (hb, hy - 3 * z), (hb - f * 2 * z, hy - 6 * z), max(1, round(z)))
        for i in range(2):  # whiskers
            w_ = math.sin(t * 2 + i) * z
            pygame.draw.line(s, belly, (hx + f * 5 * z, hy + 1 * z), (hx + f * 9 * z, hy + (1.5 + i * 1.5) * z + w_))
        pygame.draw.rect(s, INK, (round(hx + f * 2 * z) - 1, round(hy - 1.5 * z), 2, 2))
        s.set_at((round(hx + f * 2 * z), round(hy - 1.5 * z)), (255, 255, 255))

    def shine_axolotl3(self, s, t, k):
        z, f = self.size, self.facing
        hx, hy = self.tail[0]
        wave0 = math.sin(t * 2.4 + self.phase) * 1.6 * z * 0
        hx, hy = hx + f * 4 * z, hy - 5 * z + wave0
        sway = math.sin(t * 2 + self.phase) * z
        for g in range(5):  # the crown of glowing gill-fronds
            for side in (-1, 1):
                a = -math.pi / 2 - f * 0.9 + side * (0.25 + g * 0.32)
                ln = (8 - g) * z
                gx = hx - f * 2 * z + math.cos(a) * ln
                gy = hy - 2 * z + math.sin(a) * ln * (1 if side < 0 else -0.55) + sway * 0.5
                c = mix((255, 120, 200), (150, 240, 255), g / 4)
                pygame.draw.line(s, c, (hx - f * 2 * z, hy - 2 * z), (gx, gy), max(1, round(z)))
                s.set_at((round(gx), round(gy)), (255, 240, 250))
        glow(s, hx - f * 2 * z, hy - 6 * z, int(12 * z), self.color, q(70 + 70 * k))


# --- the owlet: a tree dweller --------------------------------------------------------

def owlet(s, x, y, sz, color, t, phase, how, poked, stage=1):
    """A Moonhoot perched where a tree squid would be, the app icon (drawn below it,
    at y + 19) gripped in its talons. It blinks slowly, turns its head now and then, and
    flaps when it is moving to another tree."""
    body = mix((200, 186, 230), color, 0.25)
    if stage > 1:  # Duskhoot: dusk-violet plumage; Lunarch: the deep blue of the night sky
        body = (150, 128, 200) if stage == 2 else (96, 104, 190)
    dark = mix(body, INK, 0.4)
    k = swell(t - poked, 0.35, 1.2, wait=0.15)
    if stage > 2:  # Lunarch: a crescent moon behind its head, and long tail plumes
        hx, hy = x, y - 14 * sz
        glow(s, hx, hy, int(14 * sz), (255, 236, 180), q(60 + 60 * k))
        pygame.draw.circle(s, (255, 240, 190), (round(hx), round(hy)), max(3, round(9 * sz)))
        pygame.draw.circle(s, (40, 40, 90), (round(hx + 3 * sz), round(hy - 2 * sz)), max(3, round(8 * sz)))
        for side in (-1, 0, 1):
            pygame.draw.line(s, (130, 140, 230), (x + side * 2 * sz, y + 2 * sz), (x + side * 4 * sz, y + 14 * sz), max(1, round(sz)))
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
    tuft = 13 + 3 * (stage - 1)
    for side in (-1, 1):  # ear tufts
        pygame.draw.polygon(s, body, [(x + side * 3 * sz + turn, by - 8 * sz), (x + side * 7 * sz + turn, by - 8 * sz),
                                      (x + side * (7 + stage - 1) * sz + turn, by - tuft * sz)])
    if stage > 1:  # wings folded at its sides, edged pale
        for side in (-1, 1):
            pygame.draw.polygon(s, dark, [(x + side * 7 * sz, by - 4 * sz), (x + side * 9 * sz, by + 2 * sz), (x + side * 6 * sz, by + 9 * sz)])
            pygame.draw.line(s, mix(body, (255, 255, 255), 0.5), (x + side * 9 * sz, by + 2 * sz), (x + side * 6 * sz, by + 9 * sz))
    blink = (t + phase * 2) % 6.1 < 0.2
    for side in (-1, 1):
        ex, ey = x + side * 3.5 * sz + turn, by - 4 * sz
        pygame.draw.circle(s, (255, 236, 160) if stage < 3 else (180, 240, 255), (round(ex), round(ey)), max(2, round(2.8 * sz)))
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


import grown  # noqa: E402,F401  (later stages and page three's creatures; they add to the classes above)
