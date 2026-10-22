"""Everything in the glade that moves.

Each class takes its layout once, then paints itself every frame. A frame happens in
three passes (see art.Lighting.lit):
- `draw(canvas, t)`: things in their true colours, before the lighting is applied;
- `light(lightmap, t)`: moving lights add themselves to that frame's light map;
- `shine(canvas, t)`: things that glow by themselves, painted after the lighting.
Any of them may be missing. Creatures you can click have `poke(x, y, t)`.

Rain World's world feels alive because almost everything sways, drifts or breathes a
little; these are the pieces that do that here.
"""

import math
import random

import pygame

from art import GLOW, H, W, glow, mix, scale, solid


def wind(t):
    """Gusts: a slow swell plus a little flutter."""
    return 0.65 + 0.35 * math.sin(t * 0.37) + 0.12 * math.sin(t * 1.9)


def q(v, step=12):
    """Round a glow strength, so the glow cache stays small."""
    return max(0, int(v) // step * step)


class Clock:
    """Gives a part its own dt from the frame time it is drawn at."""

    def tick(self, t):
        last = getattr(self, "_t", None)
        self._t = t
        return 0.0 if last is None else max(0.0, min(0.1, t - last))


# --- plants ----------------------------------------------------------------------------

class Blades:
    """Swaying grass blades / reeds / fern fronds, with a pale tip."""

    def __init__(self, rng, rect, n, colors, hmin=8, hmax=24, stiff=1.0, width=1):
        x0, y0, w, h = rect
        self.items = []
        for _ in range(n):
            y = y0 + rng.randrange(max(1, h))
            c = rng.choice(colors)
            self.items.append((x0 + rng.randrange(w), y, rng.randint(hmin, hmax), c,
                               rng.random() * math.tau, mix(c, (220, 236, 255), 0.25)))
        self.items.sort(key=lambda b: b[1])
        self.stiff, self.width = stiff, width

    def draw(self, s, t):
        wk = wind(t) / self.stiff
        wd = self.width
        for x, y, h, c, ph, tip in self.items:
            sway = math.sin(t * 1.4 + ph + x * 0.018) * h * 0.26 * wk + h * 0.12 * wk
            mx, my = x + sway * 0.35, y - h * 0.55
            ex, ey = x + sway, y - h
            pygame.draw.line(s, c, (x, y), (mx, my), wd)
            pygame.draw.line(s, c, (mx, my), (ex, ey))
            s.set_at((int(ex), int(ey)), tip)


class Vines:
    """Vines hanging from above, swinging more toward their tips, with leaves in pairs."""

    def __init__(self, rng, xs, top, lengths, color, leaf, flower=None, glow_tip=None):
        self.items = []
        for x in xs:
            top_y = top(x) if callable(top) else top
            self.items.append((x, top_y, rng.randint(*lengths), rng.random() * math.tau,
                               flower if flower and rng.random() < 0.4 else None,
                               glow_tip if glow_tip and rng.random() < 0.35 else None))
        self.color, self.leaf = color, leaf
        self.leaf2 = mix(leaf, (14, 10, 40), 0.3)
        self.tips = []

    def draw(self, s, t):
        wk = wind(t)
        self.tips = []
        for x, top, ln, ph, fl, gt in self.items:
            px, py = x, top
            for i in range(2, ln + 1, 2):
                f = i / ln
                off = math.sin(t * 0.9 + ph + i * 0.03) * f ** 1.5 * 8 * wk + f * f * 4 * wk
                nx, ny = x + off, top + i
                pygame.draw.line(s, self.color, (px, py), (nx, ny))
                if i % 10 == 4:
                    side = 1 if (i // 10) % 2 else -1
                    ix, iy = int(nx), int(ny)
                    for dx, dy, c in ((1, 0, self.leaf), (2, -1, self.leaf), (3, -1, self.leaf2), (2, 0, self.leaf2)):
                        s.set_at((ix + side * dx, iy + dy), c)
                px, py = nx, ny
            if fl:
                ix, iy = int(px), int(py)
                for dx, dy in ((0, 2), (-1, 1), (1, 1), (0, 1), (-2, 2), (2, 2), (0, 3)):
                    s.set_at((ix + dx, iy + dy), fl)
            if gt:
                self.tips.append((px, py + 2, gt))

    def light(self, lm, t):
        for x, y, c in self.tips:
            glow(lm, x, y, 18, c, 60)

    def shine(self, s, t):
        for i, (x, y, c) in enumerate(self.tips):
            k = 0.7 + 0.3 * math.sin(t * 1.3 + i)
            glow(s, x, y, 5, c, q(140 * k))
            s.set_at((int(x), int(y)), mix(c, (255, 255, 255), 0.6))


class Petals:
    """Petals drifting down from a crown to the ground, twirling; some faintly glow."""

    def __init__(self, rng, rect, floor, n, colors):
        self.rect, self.floor = rect, floor
        self.items = [(rng.random(), rng.random(), rng.random() * math.tau, rng.choice(colors), rng.uniform(0.6, 1.3),
                       rng.random() < 0.25) for _ in range(n)]

    def draw(self, s, t):
        self.lit = []
        x0, y0, w, h = self.rect
        fall = self.floor - y0
        for fx, fy, ph, c, sp, bright in self.items:
            k = (fy + t * 0.05 * sp) % 1.0
            y = y0 + k * fall
            x = x0 + fx * w + math.sin(t * 1.1 * sp + ph) * 16 + k * 60 * wind(t)
            if x >= W:
                x -= W
            if bright:
                self.lit.append((x, y, c))
                continue
            s.set_at((int(x), int(y)), c)
            if int(t * 4 + ph) % 2:
                s.set_at((int(x) + 1, int(y)), mix(c, (60, 30, 80), 0.25))
            else:
                s.set_at((int(x), int(y) + 1), mix(c, (60, 30, 80), 0.25))

    def shine(self, s, t):
        for x, y, c in self.lit:
            glow(s, x, y, 3, c, 70)
            s.set_at((int(x), int(y)), c)
            s.set_at((int(x) + 1, int(y)), c)


# --- light in the air --------------------------------------------------------------------

class Stars:
    """Stars twinkling in the sky, and now and then a shooting star."""

    def __init__(self, rng, n, sky_bottom, avoid=None):
        self.items = []
        while len(self.items) < n:
            x, y = rng.randrange(W), int(rng.random() ** 1.6 * sky_bottom)
            if avoid and avoid(x, y):
                continue
            self.items.append((x, y, rng.random() * math.tau, rng.uniform(0.5, 2.5),
                               rng.choice([(255, 255, 255), (220, 230, 255), (255, 230, 250), (200, 255, 250)]),
                               rng.random() < 0.12))
        self.sky_bottom = sky_bottom
        self.rng = random.Random(rng.random())
        self.shoot = None
        self.next_shoot = self.rng.uniform(6, 20)

    def draw(self, s, t):
        for x, y, ph, sp, c, big in self.items:
            k = 0.55 + 0.45 * math.sin(t * sp + ph)
            if k < 0.2:
                continue
            col = scale(c, 0.35 + 0.65 * k)
            s.set_at((x, y), col)
            if big and k > 0.6:
                d = scale(c, 0.4 * k)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    s.set_at((x + dx, y + dy), d)
        if self.shoot is None and t > self.next_shoot:
            r = self.rng
            self.shoot = (r.uniform(100, W - 100), r.uniform(20, self.sky_bottom * 0.5), r.choice((-1, 1)), t)
        if self.shoot:
            x0, y0, dx, t0 = self.shoot
            a = (t - t0) / 0.9
            if a > 1:
                self.shoot = None
                self.next_shoot = t + self.rng.uniform(15, 40)
                return
            hx, hy = x0 + dx * a * 220, y0 + a * 90
            for i in range(26):
                k = 1 - i / 26
                s.set_at((int(hx - dx * i * 2.2), int(hy - i * 0.9)), scale((230, 240, 255), k * (1 - a * 0.6)))


class Motes:
    """Glowing spores drifting up through the dark."""

    def __init__(self, rng, rect, n, color, rise=-4.0, glowing=True):
        self.rect = rect
        self.items = [(rng.random(), rng.random(), rng.random() * math.tau, rng.uniform(0.5, 1.5)) for _ in range(n)]
        self.color, self.rise, self.glowing = color, rise, glowing

    def shine(self, s, t):
        x0, y0, w, h = self.rect
        for fx, fy, ph, sp in self.items:
            x = x0 + (fx * w + t * 5 * sp + math.sin(t * 0.7 * sp + ph) * 12) % w
            y = y0 + (fy * h + t * self.rise * sp + math.cos(t * 0.5 + ph) * 8) % h
            tw = 0.5 + 0.5 * math.sin(t * 2.3 * sp + ph)
            if self.glowing and tw > 0.4:
                glow(s, x, y, 4, self.color, q(70 * tw, 14))
            if tw > 0.25:
                s.set_at((int(x), int(y)), scale(self.color, 0.5 + 0.5 * tw))


class Fireflies:
    """Fireflies drifting about, each blinking on its own rhythm. They light up
    whatever they pass; click near them and they scatter."""

    def __init__(self, rng, region, n, color=GLOW["firefly"], reach=34, homes=None):
        x0, y0, w, h = region
        pts = homes or [(x0 + rng.random() * w, y0 + rng.random() * h) for _ in range(n)]
        self.items = [(x, y, rng.random() * 100, rng.uniform(14, 46), rng.uniform(2.6, 6.5), rng.uniform(0.6, 1.2))
                      for x, y in pts]
        self.color, self.reach = color, reach
        self.body = mix(color, (255, 255, 255), 0.6)
        self.scatter_until, self.scatter_from = 0.0, (0, 0)
        self.now = []

    def scatter(self, x, y, t):
        self.scatter_from = (x, y)
        self.scatter_until = t + 1.8

    def pos(self, item, t):
        x, y, ph, rad, _, sp = item
        px = x + math.sin(t * 0.3 * sp + ph) * rad + math.sin(t * 0.9 * sp + ph * 2) * rad * 0.3
        py = y + math.sin(t * 0.4 * sp + ph * 1.3) * rad * 0.5 + math.cos(t * 1.3 + ph) * 3
        if t < self.scatter_until:
            k = (self.scatter_until - t) / 1.8
            dx, dy = px - self.scatter_from[0], py - self.scatter_from[1]
            d = math.hypot(dx, dy) or 1
            px += dx / d * 60 * k
            py += dy / d * 60 * k - 20 * k
        return px, py

    def draw(self, s, t):
        self.now = []
        for item in self.items:
            period = item[4]
            k = ((t + item[2]) % period) / period
            b = math.sin(k / 0.28 * math.pi) if k < 0.28 else 0.0  # a slow swell on, then dark
            if t < self.scatter_until:
                b = max(b, 0.8)
            self.now.append((*self.pos(item, t), b))

    def light(self, lm, t):
        for x, y, b in self.now:
            if b > 0.15:
                glow(lm, x, y, self.reach, self.color, q(110 * b))

    def shine(self, s, t):
        for x, y, b in self.now:
            if b > 0.1:
                glow(s, x, y, 7, self.color, q(170 * b))
                ix, iy = int(x), int(y)
                s.set_at((ix, iy), self.body)
                s.set_at((ix + 1, iy), self.body)
            else:
                s.set_at((int(x), int(y)), (60, 50, 70))


class Pulses:
    """Fixed things that glow and slowly breathe: mushroom caps, crystals, a rune."""

    def __init__(self, items, speed=1.2):
        self.items = items  # (x, y, reach, color, strength, phase)
        self.speed = speed

    def light(self, lm, t):
        for x, y, r, c, st, ph in self.items:
            k = 0.75 + 0.25 * math.sin(t * self.speed + ph)
            glow(lm, x, y, r, c, q(st * k))

    def shine(self, s, t):
        for x, y, r, c, st, ph in self.items:
            k = 0.7 + 0.3 * math.sin(t * self.speed + ph)
            glow(s, x, y, max(4, r // 4), c, q(st * 1.2 * k))


class Shafts:
    """Moonbeams: faint, cool, slanted, slowly breathing."""

    def __init__(self, beams, color, alpha=26):
        self.layers = []
        for (x_top, w_top, x_bot, w_bot, ph) in beams:
            levels = []
            for lvl in (0.5, 0.75, 1.0):
                surf = solid()
                surf.fill((0, 0, 0))
                for i in range(8):  # soft edges: several nested beams
                    k = i / 8
                    ww_t, ww_b = w_top * (1 - k), w_bot * (1 - k)
                    c = tuple(int(v * alpha / 255 / 8 * (0.6 + k) * 8 * lvl / 3) for v in color)
                    beam = solid()
                    beam.fill((0, 0, 0))
                    pygame.draw.polygon(beam, c, [(x_top - ww_t / 2, 0), (x_top + ww_t / 2, 0),
                                                  (x_bot + ww_b / 2, H), (x_bot - ww_b / 2, H)])
                    surf.blit(beam, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                levels.append(surf)
            self.layers.append((levels, ph))

    def shine(self, s, t):
        for levels, ph in self.layers:
            k = 0.5 + 0.5 * math.sin(t * 0.25 + ph)
            s.blit(levels[min(2, int(k * 3))], (0, 0), special_flags=pygame.BLEND_RGB_ADD)


class Lantern:
    def __init__(self, x, y, color, reach=70):
        self.x, self.y, self.color, self.reach = x, y, color, reach

    def flicker(self, t):
        return 0.8 + 0.12 * math.sin(t * 7.3) + 0.08 * math.sin(t * 13.1)

    def light(self, lm, t):
        f = self.flicker(t)
        glow(lm, self.x, self.y, int(self.reach * f), self.color, q(150 * f))

    def shine(self, s, t):
        f = self.flicker(t)
        glow(s, self.x, self.y, int(16 * f), self.color, q(110 * f))
        glow(s, self.x, self.y, 5, (255, 255, 230), 140)


class GlowThreads:
    """Glow-worm silk: curtains of fine threads hanging from a ledge, beaded with
    droplets of light (like the glow-worm caves in New Zealand)."""

    def __init__(self, rng, xs, top, lengths, color):
        self.items = []
        for x in xs:
            ln = rng.randint(*lengths)
            beads = sorted(rng.sample(range(4, ln), min(ln - 5, rng.randint(2, 5))))
            self.items.append((x, top(x) if callable(top) else top, ln, beads, rng.random() * math.tau))
        self.color = color
        self.thread = mix(color, (40, 40, 80), 0.6)

    def at(self, x, top, i, ph, t):
        return x + math.sin(t * 0.6 + ph + i * 0.05) * i * 0.04, top + i

    def draw(self, s, t):
        for x, top, ln, beads, ph in self.items:
            bx, by = self.at(x, top, ln, ph, t)
            pygame.draw.line(s, self.thread, (x, top), (bx, by))

    def light(self, lm, t):
        for x, top, ln, beads, ph in self.items:
            bx, by = self.at(x, top, ln // 2, ph, t)
            glow(lm, bx, by, 16, self.color, 40)

    def shine(self, s, t):
        for x, top, ln, beads, ph in self.items:
            for j, i in enumerate(beads):
                bx, by = self.at(x, top, i, ph, t)
                k = 0.6 + 0.4 * math.sin(t * 0.8 + ph + j)
                glow(s, bx, by, 3, self.color, q(120 * k))
                s.set_at((int(bx), int(by)), mix(self.color, (255, 255, 255), 0.5 * k))


# --- water ----------------------------------------------------------------------------------

class Waterfall:
    """Falling water: streaks racing down a column; glowing plankton churned up in the
    foam at its foot."""

    def __init__(self, rng, x0, x1, top, bottom, body, light, foam, glow_c=GLOW["cyan"]):
        self.x0, self.x1, self.top, self.bottom = x0, x1, top, bottom
        self.body, self.light_c, self.foam, self.glow_c = body, light, foam, glow_c
        self.streaks = [(rng.uniform(x0, x1), rng.random(), rng.randint(8, 28), rng.uniform(140, 220),
                         rng.random() < 0.35) for _ in range(int((x1 - x0) * 1.6))]
        self.bubbles = [(rng.uniform(x0 - 28, x1 + 28), rng.random(), rng.uniform(0.6, 1.4)) for _ in range(70)]

    def draw(self, s, t):
        span = self.bottom - self.top
        for x, off, ln, sp, white in self.streaks:
            y = self.top + (off * span + t * sp) % span
            wob = math.sin(y * 0.05 + x) * 1.2
            pygame.draw.line(s, self.foam if white else self.light_c, (x + wob, y), (x + wob, min(self.bottom, y + ln)))

    def light(self, lm, t):
        glow(lm, (self.x0 + self.x1) / 2, self.bottom, int((self.x1 - self.x0) * 1.4), self.glow_c,
             q(70 + 15 * math.sin(t * 1.7)))

    def shine(self, s, t):
        for x, ph, sp in self.bubbles:
            k = (ph + t * 0.7 * sp) % 1.0
            r = 1 + k * 5
            y = self.bottom - 2 - k * 10 + math.sin(t * 3 + x) * 1.5
            c = scale(mix(self.glow_c, (255, 255, 255), 0.5 * (1 - k)), 0.9 - 0.6 * k)
            pygame.draw.circle(s, c, (int(x), int(y)), int(r), 1 if k > 0.4 else 0)


class River:
    """Flowing water: ripple dashes sliding across a band (bigger up close), with
    glinting sparks of light in it."""

    def __init__(self, rng, edge_top, edge_bot, x_range, n, light, foam, speed=28, sparks=GLOW["cyan"]):
        self.top, self.bot = edge_top, edge_bot  # callables: x -> y
        self.xr = x_range
        self.items = [(rng.random(), rng.random(), rng.uniform(0.7, 1.3)) for _ in range(n)]
        self.light_c, self.foam, self.speed, self.sparks = light, foam, speed, sparks

    def place(self, fx, fy, sp, t):
        x0, x1 = self.xr
        w = x1 - x0
        x = x0 + (fx * w + t * self.speed * sp * (0.4 + fy * 1.2)) % w
        y = self.top(x) + (self.bot(x) - self.top(x)) * fy
        return x, y

    def draw(self, s, t):
        for fx, fy, sp in self.items:
            x, y = self.place(fx, fy, sp, t)
            ln = int(4 + fy * 14)
            c = self.foam if int(fx * 97) % 5 == 0 else self.light_c
            if math.sin(t * 2 + fx * 40) > -0.3:
                pygame.draw.line(s, c, (x, y), (x + ln, y))

    def shine(self, s, t):
        for i, (fx, fy, sp) in enumerate(self.items[::3]):
            k = math.sin(t * 1.7 + fx * 60)
            if k > 0.6:
                x, y = self.place(fx, fy, sp, t)
                glow(s, x, y + 1, 4, self.sparks, q(120 * (k - 0.6) / 0.4))
                s.set_at((int(x), int(y) + 1), mix(self.sparks, (255, 255, 255), 0.5))


# --- creatures ------------------------------------------------------------------------------

class Critter(Clock):
    """A small cream-coloured creature with a long soft tail that wanders the ground,
    a little glowing bead at the end of its tail.

    Its body is a chain of points: the head walks and each segment trails the one
    before it, which gives the floppy, physical movement Rain World's animals have.
    Click it and it hops.
    """

    SEG = 4.2

    def __init__(self, rng, ground, x_range, body=(255, 246, 238), belly=(226, 204, 232), eye=(46, 36, 84),
                 tail_glow=GLOW["amber"]):
        self.rng, self.ground, self.xr = rng, ground, x_range
        x = rng.uniform(*x_range)
        self.pts = [[x - i * self.SEG, ground(x) - 8] for i in range(11)]
        self.vy, self.air = 0.0, 0.0
        self.target, self.wait = x, 1.0
        self.facing = 1
        self.body, self.belly, self.eye, self.tail_glow = body, belly, eye, tail_glow
        self.fur = mix(body, (255, 255, 255), 0.5)
        self.step = 0.0
        self.blink = 0.0

    def poke(self, x, y, t):
        hx, hy = self.pts[0]
        if abs(x - hx) < 14 and abs(y - hy) < 12:
            self.hop()
            return True
        return False

    def hop(self):
        if self.air <= 0:
            self.vy = -110
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
            if abs(d) < 3:
                self.wait = self.rng.uniform(1.5, 6.0)
                if self.rng.random() < 0.25:
                    self.hop()
            else:
                self.facing = 1 if d > 0 else -1
                hx += self.facing * 32 * dt
                self.step += dt * 10
        gy = self.ground(hx) - 8
        if self.air > 0:
            self.vy += 320 * dt
            hy += self.vy * dt
            if hy >= gy:
                hy, self.vy, self.air = gy, 0.0, 0.0
        else:
            hy = gy - (abs(math.sin(self.step)) * 2.4 if self.wait <= 0 else 0)
        self.pts[0] = [hx, hy]
        for i in range(1, len(self.pts)):
            px, py = self.pts[i - 1]
            x, y = self.pts[i]
            y += 36 * dt * (i / len(self.pts))  # tail droops toward the ground
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy) or 1
            x, y = px + dx / d * self.SEG, py + dy / d * self.SEG
            y = min(y, self.ground(x) - 3)
            self.pts[i] = [x, y]
        self.blink -= dt
        if self.blink < -3.5:
            self.blink = 0.15

    def draw(self, s, t):
        radii = [6.6, 7.2, 6.4, 5.0, 4.0, 3.2, 2.6, 2.1, 1.7, 1.4, 1.2]
        for (x, y), r in reversed(list(zip(self.pts, radii))):
            pygame.draw.circle(s, self.belly, (round(x), round(y + 2)), r)
        for (x, y), r in reversed(list(zip(self.pts, radii))):
            pygame.draw.circle(s, self.body, (round(x), round(y)), r)
        for (x, y), r in list(zip(self.pts, radii))[:4]:  # fluffy lit back
            pygame.draw.circle(s, self.fur, (round(x - 1), round(y - r * 0.5)), max(1, r * 0.45))
        hx, hy = self.pts[0]
        f = self.facing
        for i, k in ((0, 0.0), (2, math.pi)):  # little legs while walking
            x, y = self.pts[i]
            lift = max(0, math.sin(self.step + k)) * 3 if self.wait <= 0 else 0
            pygame.draw.line(s, self.belly, (round(x - 1), round(y + 5 - lift)), (round(x - 1), round(y + 8 - lift)), 2)
        # ears: two soft points
        for ex_, h_ in ((-2, 9), (2, 10)):
            pygame.draw.polygon(s, self.body, [(hx + ex_ * f - 2, hy - 4), (hx + ex_ * f + 2, hy - 4),
                                               (hx + ex_ * f + f, hy - h_)])
            s.set_at((round(hx + ex_ * f), round(hy - 6)), (255, 190, 214))
        ex = round(hx + f * 3)
        if self.blink <= 0:
            for dx in (0, -f * 4):
                pygame.draw.rect(s, self.eye, (ex + dx, round(hy - 2), 2, 2))
                s.set_at((ex + dx, round(hy - 2)), (255, 255, 255))
        else:
            pygame.draw.line(s, self.eye, (ex - f * 4, round(hy - 1)), (ex + 1, round(hy - 1)))
        pygame.draw.rect(s, (255, 170, 200), (round(hx + f * 5) - 1, round(hy + 1), 2, 2))  # cheek

    def light(self, lm, t):
        x, y = self.pts[-1]
        glow(lm, x, y, 26, self.tail_glow, q(80 + 20 * math.sin(t * 2)))

    def shine(self, s, t):
        x, y = self.pts[-1]
        glow(s, x, y, 6, self.tail_glow, 150)
        pygame.draw.circle(s, mix(self.tail_glow, (255, 255, 255), 0.5), (round(x), round(y)), 2)


class Squid(Clock):
    """A little glowing squid that, for reasons nobody knows, swims through the air.

    It pulses: the mantle squeezes, it shoots forward mantle-first, then glides and
    slows while its tentacles trail behind on springy chains. Spots along its back
    blink. Click one and it darts away with a flash."""

    def __init__(self, rng, region, color, size=1.0, spots=None):
        self.rng, self.region = rng, region
        x0, y0, w, h = region
        self.x, self.y = x0 + rng.random() * w, y0 + rng.random() * h
        self.vx, self.vy = 0.0, 0.0
        self.heading = -math.pi / 2 + rng.uniform(-1, 1)
        self.target = self.pick()
        self.phase = rng.random()
        self.period = rng.uniform(1.8, 2.8)
        self.size = size
        self.color = color
        self.body = mix(color, (255, 255, 255), 0.35)
        self.dark = mix(color, (30, 20, 70), 0.45)
        self.spots = spots or mix(color, (255, 255, 255), 0.75)
        self.flash = -10.0
        n = 6
        self.arms = [[[self.x, self.y] for _ in range(n + (3 if i in (1, 4) else 0))] for i in range(6)]

    def pick(self):
        x0, y0, w, h = self.region
        return x0 + self.rng.random() * w, y0 + self.rng.random() * h

    def poke(self, x, y, t):
        if math.hypot(x - self.x, y - self.y) > 22 * self.size:
            return False
        dx, dy = self.x - x, self.y - y
        d = math.hypot(dx, dy) or 1
        self.vx += dx / d * 120
        self.vy += dy / d * 120 - 40
        self.heading = math.atan2(self.vy, self.vx)
        self.target = self.pick()
        self.flash = t
        return True

    def draw(self, s, t):
        dt = self.tick(t)
        if dt == 0:
            return
        tx, ty = self.target
        # squid swim mantle-first and mostly upward, sinking back between pulses, so
        # they steer toward the target but always lean toward "up"
        want = math.atan2(min(ty - self.y, 0) - 90, (tx - self.x) * 0.6)
        turn = (want - self.heading + math.pi) % math.tau - math.pi
        self.heading += max(-1.2 * dt, min(1.2 * dt, turn))
        k = ((t / self.period) + self.phase) % 1.0
        self.squeeze = math.sin(k / 0.25 * math.pi) if k < 0.25 else 0.0
        if k < 0.25:
            thrust = 120
            self.vx += math.cos(self.heading) * thrust * dt
            self.vy += math.sin(self.heading) * thrust * dt
        damp = math.exp(-1.6 * dt)
        self.vx *= damp
        self.vy = self.vy * damp + 16 * dt  # a slow sink between pulses
        self.x += self.vx * dt
        self.y += self.vy * dt
        x0, y0, w, h = self.region
        if math.hypot(tx - self.x, ty - self.y) < 30 or not (x0 - 40 < self.x < x0 + w + 40 and y0 - 40 < self.y < y0 + h + 40):
            self.target = self.pick()
        # tentacles: rope chains hanging off the head, pulled out behind
        ux, uy = math.cos(self.heading), math.sin(self.heading)
        px_, py_ = -uy, ux
        hx, hy = self.x, self.y
        seg = 2.2 * self.size
        for j, arm in enumerate(self.arms):
            off = (j - 2.5) * 0.8 * self.size
            arm[0] = [hx + px_ * off, hy + py_ * off]
            for i in range(1, len(arm)):
                ax, ay = arm[i - 1]
                bx, by = arm[i]
                curl = math.sin(t * 2.4 + j * 1.1 + i * 0.7) * 0.45  # tentacles curl and wave
                bx -= ux * seg * 0.35 + px_ * (curl + (j - 2.5) * 0.03)
                by -= uy * seg * 0.35 + py_ * (curl + (j - 2.5) * 0.03) - 0.1
                dx, dy = bx - ax, by - ay
                d = math.hypot(dx, dy) or 1
                arm[i] = [ax + dx / d * seg, ay + dy / d * seg]

    def light(self, lm, t):
        st = 70 + 40 * getattr(self, "squeeze", 0)
        if t - self.flash < 0.6:
            st += 120 * (1 - (t - self.flash) / 0.6)
        glow(lm, self.x, self.y, int(48 * self.size), self.color, q(st))

    def shine(self, s, t):
        sz = self.size
        ux, uy = math.cos(self.heading), math.sin(self.heading)
        px_, py_ = -uy, ux
        glow(s, self.x + ux * 6 * sz, self.y + uy * 6 * sz, int(13 * sz), self.color, 70)
        arm_c = mix(self.color, (40, 30, 90), 0.25)
        for arm in self.arms:
            pts = [(round(x), round(y)) for x, y in arm]
            pygame.draw.lines(s, arm_c, False, pts)
            for x, y in pts[2::3]:
                s.set_at((x, y), self.spots)
        pygame.draw.circle(s, self.body, (round(self.x + ux * 1.5), round(self.y + uy * 1.5)), max(2, round(3 * sz)))
        sq = getattr(self, "squeeze", 0)
        ln, wd = 14 * sz, 9.0 * sz * (1 - 0.3 * sq)
        # mantle: a teardrop from the head out to a pointed tip, darker underneath
        for i in range(int(ln) + 1):
            f = i / ln
            r = wd / 2 * (math.sin(min(1.0, f * 1.25 + 0.1) * math.pi * 0.5) * (1 - f ** 2.5))
            cx, cy = self.x + ux * (i + 2), self.y + uy * (i + 2)
            pygame.draw.circle(s, self.dark, (round(cx - px_ * 0.8), round(cy - py_ * 0.8 + 0.6)), max(1, r))
        for i in range(int(ln) + 1):
            f = i / ln
            r = wd / 2 * (math.sin(min(1.0, f * 1.25 + 0.1) * math.pi * 0.5) * (1 - f ** 2.5))
            cx, cy = self.x + ux * (i + 2), self.y + uy * (i + 2)
            pygame.draw.circle(s, self.body, (round(cx), round(cy)), max(1, r - 0.6))
        # fins near the tip, flapping
        tipx, tipy = self.x + ux * (ln + 2), self.y + uy * (ln + 2)
        flap = 5 * sz * (1 + 0.3 * math.sin(t * 5 + self.phase * 9))
        fin = mix(self.color, (255, 255, 255), 0.15)
        for k in (-1, 1):  # two wide diamond fins at the top of the mantle
            pygame.draw.polygon(s, fin, [(tipx - ux * 7 * sz, tipy - uy * 7 * sz),
                                         (tipx - ux * 3 * sz + px_ * flap * k, tipy - uy * 3 * sz + py_ * flap * k),
                                         (tipx, tipy)])
        pygame.draw.line(s, mix(self.body, (255, 255, 255), 0.5), (round(self.x + ux * 4 - px_), round(self.y + uy * 4 - py_)),
                         (round(self.x + ux * ln * 0.8 - px_), round(self.y + uy * ln * 0.8 - py_)))
        # blinking spots down the back, and eyes on the head
        for j in range(4):
            if math.sin(t * 2.5 + j * 1.3 + self.phase * 9) > -0.2:
                f = 0.25 + j * 0.17
                s.set_at((round(self.x + ux * (2 + ln * f)), round(self.y + uy * (2 + ln * f))), self.spots)
        for k in (-1, 1):  # big dark eyes with a glint
            ex, ey = self.x + ux * 1.5 + px_ * 2.6 * sz * k, self.y + uy * 1.5 + py_ * 2.6 * sz * k
            pygame.draw.circle(s, (24, 16, 50), (round(ex), round(ey)), max(1, round(1.2 * sz)))
            s.set_at((round(ex - 0.5), round(ey - 0.5)), (255, 255, 255))
        if t - self.flash < 0.6:
            glow(s, self.x, self.y, int(30 * sz), (255, 255, 255), q(160 * (1 - (t - self.flash) / 0.6)))


class Track:
    """A polyline something crawls along, measured by distance."""

    def __init__(self, pts, up=None):
        self.pts = pts
        self.lens = [0.0]
        for a, b in zip(pts, pts[1:]):
            self.lens.append(self.lens[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.length = self.lens[-1]
        self.up = up  # which way is "up" off the surface; None: away from the ground, i.e. -y

    def at(self, d):
        d = max(0.0, min(self.length, d))
        i = 1
        while i < len(self.lens) - 1 and self.lens[i] < d:
            i += 1
        a, b = self.pts[i - 1], self.pts[i]
        seg = self.lens[i] - self.lens[i - 1] or 1
        f = (d - self.lens[i - 1]) / seg
        tx, ty = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        nx, ny = ty, -tx
        if self.up:
            if nx * self.up[0] + ny * self.up[1] < 0:
                nx, ny = -nx, -ny
        elif ny > 0:
            nx, ny = -nx, -ny
        return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, tx, ty, nx, ny


SLUG_PROFILE = [2.0, 2.6, 3.0, 3.5, 3.9, 4.0, 3.8, 3.5, 3.1, 2.7, 2.2, 1.7, 1.2, 0.8]


class Slug(Clock):
    """A slug gliding slowly along a track, leaving a glistening trail. Its eye stalks
    wave about; poke it and they pull in for a moment. Some slugs are luminous
    (glowing spots down the back); with `shell`, it is a snail."""

    def __init__(self, rng, track, body, size=1.0, speed=5.0, spots=None, shell=None, foot=None):
        self.rng, self.track, self.size = rng, track, size
        self.body = body
        self.dark = mix(body, (20, 12, 40), 0.35)
        self.sheen = mix(body, (235, 240, 255), 0.55)
        self.foot = foot or mix(body, (240, 230, 220), 0.4)
        self.spots, self.shell = spots, shell
        self.speed = speed
        self.d = rng.uniform(track.length * 0.2, track.length * 0.8)
        self.dir = rng.choice((-1, 1))
        self.wait = 0.0
        self.trail = []
        self.shy = -10.0
        self.ph = rng.random() * 10
        self.seg = 2.0 * size
        self.n = len(SLUG_PROFILE)
        # its own pattern: dark mottles at fixed places along and across the body
        self.mottle = [(rng.randrange(1, self.n - 1), rng.uniform(0.6, 1.6), rng.uniform(-0.6, 0.6))
                       for _ in range(int(10 * size))]
        self.mantle = mix(body, (255, 255, 255), 0.12)

    def poke(self, x, y, t):
        hx, hy = self.head
        if math.hypot(x - hx, y - hy) < 16 * self.size:
            self.shy = t
            self.wait = 2.5
            return True
        return False

    def draw(self, s, t):
        dt = self.tick(t)
        L = self.track.length
        body_len = self.seg * self.n
        if self.wait > 0:
            self.wait -= dt
            moving = 0.0
        else:
            moving = 1.0
            self.d += self.dir * self.speed * dt * (0.6 + 0.4 * math.sin(t * 2.2 + self.ph))
            if self.d > L - 2 or self.d < body_len + 2:
                if self.d < body_len + 2 and self.dir < 0 or self.d > L - 2 and self.dir > 0:
                    self.dir = -self.dir
                    self.d = max(body_len + 2, min(L - 2, self.d))
            if self.rng.random() < dt * 0.05:
                self.wait = self.rng.uniform(2, 7)
            if self.rng.random() < dt * 0.02:
                self.dir = -self.dir
        self.d = max(0.0, min(L, self.d))
        pts = []
        for i in range(self.n):
            stretch = 1 + 0.1 * math.sin(t * 2.2 + self.ph - i * 0.6) * moving
            x, y, tx, ty, nx, ny = self.track.at(self.d - self.dir * i * self.seg * stretch)
            pts.append((x, y, nx, ny, tx * self.dir, ty * self.dir))
        self.pts = pts
        hx, hy = pts[0][0], pts[0][1]
        self.head = (hx, hy)
        if not self.trail or math.hypot(self.trail[-1][0] - hx, self.trail[-1][1] - hy) > 3:
            self.trail.append((hx, hy, t))
            if len(self.trail) > 90:
                self.trail.pop(0)
        sz = self.size
        # the foot (pale), then the body: dark underside, colour, wet highlight on top
        for (x, y, nx, ny, _, _), r in zip(pts, SLUG_PROFILE):
            pygame.draw.circle(s, self.foot, (round(x + nx * 0.8), round(y + ny * 0.8)), max(1, r * sz * 0.55))
        for (x, y, nx, ny, _, _), r in zip(pts, SLUG_PROFILE):
            r *= sz
            pygame.draw.circle(s, self.dark, (round(x + nx * r * 0.9), round(y + ny * r * 0.9)), max(1, r))
        for (x, y, nx, ny, _, _), r in zip(pts, SLUG_PROFILE):
            r *= sz
            pygame.draw.circle(s, self.body, (round(x + nx * r * 1.15), round(y + ny * r * 1.15)), max(1, r * 0.85))
        for i, k, side in self.mottle:  # mottled skin
            x, y, nx, ny, tx, ty = pts[i]
            r = SLUG_PROFILE[i] * sz
            mx, my = x + nx * r * k + tx * side * r, y + ny * r * k + ty * side * r
            s.set_at((round(mx), round(my)), self.dark)
            if sz > 1.4:
                s.set_at((round(mx) + 1, round(my)), self.dark)
        for i in range(2, 6):  # the mantle: a smoother, paler saddle behind the head, with ridges
            x, y, nx, ny, _, _ = pts[i]
            r = SLUG_PROFILE[i] * sz
            pygame.draw.circle(s, self.mantle, (round(x + nx * r * 1.35), round(y + ny * r * 1.35)), max(1, r * 0.75))
        for k in (0.9, 1.5):
            for i in range(2, 6):
                x, y, nx, ny, tx, ty = pts[i]
                r = SLUG_PROFILE[i] * sz
                s.set_at((round(x + nx * r * (1.35 + 0.3 * k - 0.4)), round(y + ny * r * (1.35 + 0.3 * k - 0.4))),
                         mix(self.mantle, self.dark, 0.4))
        x, y, nx, ny, _, _ = pts[4]  # breathing pore, on the mantle's edge
        r = SLUG_PROFILE[4] * sz
        pygame.draw.circle(s, self.dark, (round(x + nx * r * 0.9), round(y + ny * r * 0.9)), max(1, sz * 0.7))
        for i in range(0, self.n - 1):  # the frilled edge of the foot
            x, y, nx, ny, tx, ty = pts[i]
            if (i + int(t * 3)) % 2 == 0:
                s.set_at((round(x + nx * 0.5), round(y + ny * 0.5)), mix(self.foot, (255, 255, 255), 0.3))
        if self.shell:
            x, y, nx, ny, tx, ty = pts[5]
            cx, cy = x + nx * 7 * sz, y + ny * 7 * sz
            r = 7 * sz
            sh_dark = mix(self.shell, (20, 12, 40), 0.4)
            pygame.draw.circle(s, sh_dark, (round(cx), round(cy + 1)), round(r))
            pygame.draw.circle(s, self.shell, (round(cx), round(cy)), round(r - 1))
            for k in range(26):  # the spiral
                a = k * 0.42
                rr = (r - 1.5) * (1 - k / 30)
                s.set_at((round(cx + math.cos(a) * rr * -self.dir), round(cy + math.sin(a) * rr)), sh_dark)
            s.set_at((round(cx - 2), round(cy - r + 2)), mix(self.shell, (255, 255, 255), 0.6))
        # eye stalks and feelers
        out = 1.0 if t - self.shy > 2.2 else min(1.0, max(0.15, (t - self.shy - 1.2) / 1.0))
        x, y, nx, ny, tx, ty = pts[0]
        r = SLUG_PROFILE[0] * sz
        bx, by = x + nx * r * 1.2, y + ny * r * 1.2
        for k, ln in ((-1, 7.0), (1, 7.5)):
            sway = math.sin(t * 1.7 + k + self.ph) * 0.35
            ax = tx * (0.55 + sway * 0.4) + nx * (0.8 - sway * 0.2)
            ay = ty * (0.55 + sway * 0.4) + ny * (0.8 - sway * 0.2)
            L_ = ln * sz * out
            ex, ey = bx + ax * L_ + tx * k * 0.8, by + ay * L_ + ty * k * 0.8
            pygame.draw.line(s, self.body, (round(bx + tx * k * 0.8), round(by + ty * k * 0.8)), (round(ex), round(ey)))
            s.set_at((round(ex), round(ey)), (34, 24, 56))
            s.set_at((round(ex + nx), round(ey + ny)), self.dark)
        for k in (-1, 1):
            s.set_at((round(x + tx * 3 * sz + nx * k), round(y + ty * 3 * sz + ny * (1 + k))), self.body)

    def shine(self, s, t):
        if getattr(self, "pts", None):  # wet glints along the back catch the light
            for i in range(1, self.n - 2, 2):
                x, y, nx, ny, tx, ty = self.pts[i]
                r = SLUG_PROFILE[i] * self.size
                if math.sin(t * 1.3 + i * 1.7 + self.ph) > -0.4:
                    s.set_at((round(x + nx * r * 1.9 - tx), round(y + ny * r * 1.9 - ty)), (150, 160, 190))
        for i, (x, y, t0) in enumerate(self.trail):
            age = t - t0
            if age > 40:
                continue
            if (i + int(t * 2)) % 3 == 0:
                k = (1 - age / 40) * 0.7
                s.set_at((round(x), round(y)), scale((200, 220, 255), k))
        if self.spots and getattr(self, "pts", None):
            for i in range(2, self.n - 2, 3):
                x, y, nx, ny, _, _ = self.pts[i]
                r = SLUG_PROFILE[i] * self.size
                k = 0.6 + 0.4 * math.sin(t * 1.5 + i)
                px, py = x + nx * r * 1.4, y + ny * r * 1.4
                glow(s, px, py, 5, self.spots, q(130 * k))
                s.set_at((round(px), round(py)), mix(self.spots, (255, 255, 255), 0.5))

    def light(self, lm, t):
        if self.spots and getattr(self, "head", None):
            glow(lm, *self.head, int(28 * self.size), self.spots, 70)


class Millipede(Clock):
    """A glowing millipede (they are real) rippling along a track on dozens of legs."""

    def __init__(self, rng, track, body, glow_c, n=18, speed=9.0):
        self.rng, self.track, self.body, self.glow_c, self.n = rng, track, body, glow_c, n
        self.speed = speed
        self.dark = mix(body, (14, 8, 30), 0.4)
        self.d = rng.uniform(track.length * 0.3, track.length * 0.7)
        self.dir = rng.choice((-1, 1))
        self.wait = 0.0
        self.shy = -10.0

    def poke(self, x, y, t):
        x0, y0 = self.pts[0][:2] if getattr(self, "pts", None) else (-99, -99)
        if math.hypot(x - x0, y - y0) < 18:
            self.shy, self.wait = t, 3.0
            return True
        return False

    def draw(self, s, t):
        dt = self.tick(t)
        L = self.track.length
        body_len = self.n * 2.6
        if self.wait > 0:
            self.wait -= dt
        else:
            self.d += self.dir * self.speed * dt
            if (self.d > L - 2 and self.dir > 0) or (self.d < body_len + 2 and self.dir < 0):
                self.dir = -self.dir
            if self.rng.random() < dt * 0.04:
                self.wait = self.rng.uniform(1, 4)
        self.d = max(body_len, min(L, self.d))
        curl = min(1.0, max(0.0, 1 - (t - self.shy) / 3.0))
        self.pts = []
        for i in range(self.n):
            x, y, tx, ty, nx, ny = self.track.at(self.d - self.dir * i * 2.6 * (1 - curl * 0.5))
            self.pts.append((x + nx * 2.4, y + ny * 2.4, nx, ny))
        moving = self.wait <= 0
        for i, (x, y, nx, ny) in enumerate(self.pts):
            lift = math.sin(t * 14 - i * 0.9) if moving else 0
            for k in (-1, 1):
                lx = x - nx * 3 + k * 0.8 * ny + lift * 0.6 * k
                ly = y - ny * 3 - k * 0.8 * nx
                s.set_at((round(lx), round(ly)), self.dark)
        for i, (x, y, nx, ny) in enumerate(reversed(self.pts)):
            pygame.draw.circle(s, self.dark, (round(x), round(y + 0.5)), 2)
            pygame.draw.circle(s, self.body, (round(x), round(y - 0.5)), 2 if i < self.n - 1 else 3)

    def light(self, lm, t):
        if getattr(self, "pts", None):
            x, y = self.pts[self.n // 2][:2]
            glow(lm, x, y, 30, self.glow_c, 60)

    def shine(self, s, t):
        for i, (x, y, nx, ny) in enumerate(getattr(self, "pts", [])):
            if i % 2 == 0:
                k = 0.6 + 0.4 * math.sin(t * 2 - i * 0.4)
                s.set_at((round(x), round(y - 1)), scale(self.glow_c, 0.5 + 0.5 * k))


def make_rng(seed):
    return random.Random(seed)
