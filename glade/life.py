"""Everything in the glade that moves.

Each class takes its layout once, then `draw(canvas, t)` paints it for time t
(seconds). Rain World's world feels alive because almost everything sways, drifts
or breathes a little; these are the pieces that do that here.
"""

import math
import random

import pygame

from art import H, W, glow, mix


def wind(t):
    """Gusts: a slow swell plus a little flutter."""
    return 0.65 + 0.35 * math.sin(t * 0.37) + 0.12 * math.sin(t * 1.9)


class Blades:
    """Swaying grass blades / reeds / fern fronds."""

    def __init__(self, rng, rect, n, colors, hmin=4, hmax=12, stiff=1.0):
        x0, y0, w, h = rect
        self.items = []
        for _ in range(n):
            y = y0 + rng.randrange(max(1, h))
            self.items.append((
                x0 + rng.randrange(w), y, rng.randint(hmin, hmax),
                rng.choice(colors), rng.random() * math.tau,
            ))
        self.items.sort(key=lambda b: b[1])
        self.stiff = stiff

    def draw(self, s, t):
        wk = wind(t) / self.stiff
        for x, y, h, c, ph in self.items:
            sway = math.sin(t * 1.4 + ph + x * 0.035) * h * 0.28 * wk + h * 0.12 * wk
            mx, my = x + sway * 0.35, y - h * 0.55
            pygame.draw.line(s, c, (x, y), (mx, my))
            pygame.draw.line(s, c, (mx, my), (x + sway, y - h))


class Vines:
    """Vines hanging from above, swinging more toward their tips."""

    def __init__(self, rng, xs, top, lengths, color, leaf, flower=None):
        self.items = []
        for x in xs:
            top_y = top(x) if callable(top) else top
            self.items.append((x, top_y, rng.randint(*lengths), rng.random() * math.tau,
                               flower if flower and rng.random() < 0.4 else None))
        self.color, self.leaf = color, leaf

    def draw(self, s, t):
        wk = wind(t)
        for x, top, ln, ph, fl in self.items:
            px, py = x, top
            for i in range(1, ln + 1, 2):
                f = i / ln
                off = math.sin(t * 0.9 + ph + i * 0.06) * f ** 1.5 * 4 * wk + f * f * 2 * wk
                nx, ny = x + off, top + i
                pygame.draw.line(s, self.color, (px, py), (nx, ny))
                if i % 6 == 1:
                    side = 1 if (i // 6) % 2 else -1
                    s.set_at((int(nx) + side, int(ny)), self.leaf)
                    s.set_at((int(nx) + side * 2, int(ny) - 1), self.leaf)
                px, py = nx, ny
            if fl:
                s.set_at((int(px), int(py) + 1), fl)
                s.set_at((int(px) - 1, int(py)), fl)
                s.set_at((int(px) + 1, int(py)), fl)


class Motes:
    """Pollen and dust drifting through the light."""

    def __init__(self, rng, rect, n, color, rise=-2.0, glowing=False):
        self.rect = rect
        self.items = [(rng.random(), rng.random(), rng.random() * math.tau, rng.uniform(0.5, 1.5)) for _ in range(n)]
        self.color, self.rise, self.glowing = color, rise, glowing

    def draw(self, s, t):
        x0, y0, w, h = self.rect
        for fx, fy, ph, sp in self.items:
            x = x0 + (fx * w + t * 3 * sp + math.sin(t * 0.7 * sp + ph) * 6) % w
            y = y0 + (fy * h + t * self.rise * sp + math.cos(t * 0.5 + ph) * 4) % h
            tw = 0.5 + 0.5 * math.sin(t * 2.3 * sp + ph)
            if self.glowing:
                glow(s, x, y, 3, self.color, int(40 + 60 * tw))
            if tw > 0.25:
                s.set_at((int(x), int(y)), self.color)


class Bugs:
    """Little glowing bugs that bob around a spot, wings flickering."""

    def __init__(self, rng, spots, color, wing=(255, 255, 255)):
        self.items = [(x, y, rng.random() * 100, rng.uniform(8, 22)) for x, y in spots]
        self.color, self.wing = color, wing
        self.scatter_until = 0.0
        self.scatter_from = (0, 0)

    def pos(self, item, t):
        x, y, ph, rad = item
        px = x + math.sin(t * 0.6 + ph) * rad + math.sin(t * 1.7 + ph * 2) * rad * 0.3
        py = y + math.sin(t * 0.8 + ph * 1.3) * rad * 0.5 + math.cos(t * 2.1 + ph) * 2
        if t < self.scatter_until:
            k = (self.scatter_until - t) / 1.5
            dx, dy = px - self.scatter_from[0], py - self.scatter_from[1]
            d = math.hypot(dx, dy) or 1
            px += dx / d * 30 * k
            py += dy / d * 30 * k - 10 * k
        return px, py

    def scatter(self, x, y, t):
        self.scatter_from = (x, y)
        self.scatter_until = t + 1.5

    def draw(self, s, t):
        for item in self.items:
            x, y = self.pos(item, t)
            pulse = 0.6 + 0.4 * math.sin(t * 3 + item[2])
            glow(s, x, y, 5, self.color, int(70 * pulse))
            s.set_at((int(x), int(y)), mix(self.color, (255, 255, 255), 0.6))
            if int(t * 14 + item[2]) % 2:
                s.set_at((int(x) - 1, int(y) - 1), self.wing)
                s.set_at((int(x) + 1, int(y) - 1), self.wing)
            else:
                s.set_at((int(x) - 1, int(y)), self.wing)
                s.set_at((int(x) + 1, int(y)), self.wing)


class Petals:
    """Petals drifting down from a crown to the ground, twirling."""

    def __init__(self, rng, rect, floor, n, colors):
        self.rect, self.floor = rect, floor
        self.items = [(rng.random(), rng.random(), rng.random() * math.tau, rng.choice(colors), rng.uniform(0.6, 1.3))
                      for _ in range(n)]

    def draw(self, s, t):
        x0, y0, w, h = self.rect
        fall = self.floor - y0
        for fx, fy, ph, c, sp in self.items:
            k = (fy + t * 0.06 * sp) % 1.0
            y = y0 + k * fall
            x = x0 + fx * w + math.sin(t * 1.1 * sp + ph) * 8 + k * 30 * wind(t)
            if x >= W:
                x -= W
            s.set_at((int(x), int(y)), c)
            if int(t * 4 + ph) % 2:
                s.set_at((int(x) + 1, int(y)), mix(c, (60, 30, 80), 0.25))


class Shafts:
    """God-rays: pale slanted beams that slowly breathe."""

    def __init__(self, beams, color, alpha=34):
        self.layers = []
        for (x_top, w_top, x_bot, w_bot, ph) in beams:
            surf = pygame.Surface((W, H), pygame.SRCALPHA)
            for i in range(6):  # soft edges: several nested beams
                k = i / 6
                ww_t, ww_b = w_top * (1 - k), w_bot * (1 - k)
                pygame.draw.polygon(surf, (*color, int(alpha / 6 * (0.6 + k))), [
                    (x_top - ww_t / 2, 0), (x_top + ww_t / 2, 0), (x_bot + ww_b / 2, H), (x_bot - ww_b / 2, H)])
            self.layers.append((surf, ph))

    def draw(self, s, t):
        for surf, ph in self.layers:
            surf.set_alpha(int(255 * (0.55 + 0.45 * math.sin(t * 0.25 + ph))))
            s.blit(surf, (0, 0))


class Waterfall:
    """Falling water: bright streaks racing down a column, foam and spray at the foot."""

    def __init__(self, rng, x0, x1, top, bottom, body, light, foam):
        self.x0, self.x1, self.top, self.bottom = x0, x1, top, bottom
        self.body, self.light, self.foam = body, light, foam
        self.streaks = [(rng.uniform(x0, x1), rng.random(), rng.randint(4, 14), rng.uniform(70, 110),
                         rng.random() < 0.35) for _ in range(int((x1 - x0) * 2.2))]
        self.bubbles = [(rng.uniform(x0 - 14, x1 + 14), rng.random(), rng.uniform(0.6, 1.4)) for _ in range(40)]

    def draw(self, s, t):
        span = self.bottom - self.top
        for x, off, ln, sp, white in self.streaks:
            y = self.top + (off * span + t * sp) % span
            wob = math.sin(y * 0.1 + x) * 0.6
            pygame.draw.line(s, self.foam if white else self.light, (x + wob, y),
                             (x + wob, min(self.bottom, y + ln)))
        # foam churning at the foot
        for x, ph, sp in self.bubbles:
            k = (ph + t * 0.7 * sp) % 1.0
            r = 1 + k * 3
            y = self.bottom - 1 - k * 5 + math.sin(t * 3 + x) * 0.8
            c = mix(self.foam, self.light, k)
            pygame.draw.circle(s, c, (int(x), int(y)), int(r), 1 if k > 0.5 else 0)


class River:
    """Flowing water: glints and ripple dashes sliding across a band, bigger up close."""

    def __init__(self, rng, edge_top, edge_bot, x_range, n, light, foam, speed=14):
        self.top, self.bot = edge_top, edge_bot  # callables: x -> y
        self.xr = x_range
        self.items = [(rng.random(), rng.random(), rng.uniform(0.7, 1.3)) for _ in range(n)]
        self.light, self.foam, self.speed = light, foam, speed

    def draw(self, s, t):
        x0, x1 = self.xr
        w = x1 - x0
        for fx, fy, sp in self.items:
            near = fy  # 0 far bank, 1 near bank
            x = x0 + (fx * w + t * self.speed * sp * (0.4 + near * 1.2)) % w
            y = self.top(x) + (self.bot(x) - self.top(x)) * fy
            ln = int(2 + near * 7)
            c = self.foam if int(fx * 97) % 5 == 0 else self.light
            ph = math.sin(t * 2 + fx * 40)
            if ph > -0.3:
                pygame.draw.line(s, c, (x, y), (x + ln, y))


class Lantern:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color

    def draw(self, s, t):
        f = 0.75 + 0.15 * math.sin(t * 7.3) + 0.1 * math.sin(t * 13.1)
        glow(s, self.x, self.y, int(16 * f), self.color, int(70 * f))
        glow(s, self.x, self.y, 4, (255, 255, 230), 120)


class Critter:
    """A small cream-coloured creature with a long soft tail that wanders the ground.

    Its body is a chain of points: the head walks and each segment trails the one
    before it, which gives the floppy, physical movement Rain World's animals have.
    Click it and it hops.
    """

    SEG = 2.2

    def __init__(self, rng, ground, x_range, body=(255, 246, 238), belly=(236, 214, 236), eye=(46, 36, 84)):
        self.rng, self.ground, self.xr = rng, ground, x_range
        x = rng.uniform(*x_range)
        self.pts = [[x - i * self.SEG, ground(x) - 4] for i in range(9)]
        self.vy, self.air = 0.0, 0.0
        self.target, self.wait = x, 1.0
        self.facing = 1
        self.body, self.belly, self.eye = body, belly, eye
        self.step = 0.0
        self.blink = 0.0

    def hit(self, x, y):
        hx, hy = self.pts[0]
        return abs(x - hx) < 8 and abs(y - hy) < 7

    def hop(self):
        if self.air <= 0:
            self.vy = -55
            self.air = 0.01

    def update(self, dt):
        hx, hy = self.pts[0]
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                lo, hi = self.xr
                self.target = self.rng.uniform(lo, hi)
        else:
            d = self.target - hx
            if abs(d) < 2:
                self.wait = self.rng.uniform(1.5, 6.0)
                if self.rng.random() < 0.25:
                    self.hop()
            else:
                self.facing = 1 if d > 0 else -1
                hx += self.facing * 16 * dt
                self.step += dt * 10
        gy = self.ground(hx) - 4
        if self.air > 0:
            self.vy += 160 * dt
            hy += self.vy * dt
            if hy >= gy:
                hy, self.vy, self.air = gy, 0.0, 0.0
        else:
            hy = gy - (abs(math.sin(self.step)) * 1.2 if self.wait <= 0 else 0)
        self.pts[0] = [hx, hy]
        for i in range(1, len(self.pts)):
            px, py = self.pts[i - 1]
            x, y = self.pts[i]
            y += 18 * dt * (i / len(self.pts))  # tail droops toward the ground
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy) or 1
            x, y = px + dx / d * self.SEG, py + dy / d * self.SEG
            y = min(y, self.ground(x) - 1.5)
            self.pts[i] = [x, y]
        self.blink -= dt
        if self.blink < -3.5:
            self.blink = 0.15

    def draw(self, s, t):
        radii = [3.4, 3.6, 3.2, 2.6, 2.1, 1.7, 1.3, 1.0, 0.8]
        for (x, y), r in reversed(list(zip(self.pts, radii))):
            pygame.draw.circle(s, self.belly, (round(x), round(y + 1)), r)
        for (x, y), r in reversed(list(zip(self.pts, radii))):
            pygame.draw.circle(s, self.body, (round(x), round(y)), r)
        hx, hy = self.pts[0]
        # little legs while walking
        for i, k in ((0, 0.0), (2, math.pi)):
            x, y = self.pts[i]
            lift = max(0, math.sin(self.step + k)) * 1.5 if self.wait <= 0 else 0
            s.set_at((round(x), round(y + 3 - lift)), self.belly)
            s.set_at((round(x), round(y + 4 - lift)), self.belly)
        # ears
        s.set_at((round(hx - self.facing), round(hy - 4)), self.body)
        s.set_at((round(hx + self.facing * 0), round(hy - 5)), self.body)
        ex = round(hx + self.facing * 1.6)
        if self.blink <= 0:
            s.set_at((ex, round(hy - 1)), self.eye)
            s.set_at((ex - self.facing * 2, round(hy - 1)), self.eye)
        else:
            s.set_at((ex, round(hy)), self.eye)
        s.set_at((round(hx + self.facing * 2.6), round(hy + 1)), (255, 170, 200))  # cheek


def make_rng(seed):
    return random.Random(seed)
