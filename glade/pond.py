"""The lily pond on the lower monitor: the water at the foot of the Glade.

Koi with floppy chain bodies wander under the lily pads; click the water and it
ripples, and the fish come to see what fell in.
"""

import math
import random

import pygame

import art
from art import mix
from life import Blades, Bugs

PAL = dict(mist=(255, 220, 232), light=(255, 248, 220), shade=(40, 70, 120))
WATER_TOP = (176, 214, 250)
WATER_DEEP = (84, 162, 206)
KOI = [
    [(255, 250, 244), (255, 166, 120), (255, 250, 244), (255, 166, 120)],
    [(255, 150, 190), (255, 250, 244), (255, 150, 190), (255, 210, 230)],
    [(255, 226, 120), (255, 250, 244), (255, 226, 120), (255, 196, 110)],
    [(255, 250, 244), (190, 160, 255), (255, 250, 244), (255, 250, 244)],
    [(255, 176, 130), (255, 176, 130), (255, 250, 244), (255, 130, 110)],
]


class Fish:
    SEG = 3.3

    def __init__(self, rng, w, h, colors):
        self.rng, self.w, self.h, self.colors = rng, w, h, colors
        x, y = rng.uniform(40, w - 40), rng.uniform(40, h - 30)
        self.heading = rng.random() * math.tau
        self.pts = [[x - i * self.SEG, y] for i in range(7)]
        self.target = self.pick()
        self.speed = rng.uniform(7, 11)
        self.wig = rng.random() * 10
        self.size = rng.uniform(1.4, 1.8)

    def pick(self):
        return self.rng.uniform(30, self.w - 30), self.rng.uniform(34, self.h - 20)

    def lure(self, x, y):
        if math.hypot(x - self.pts[0][0], y - self.pts[0][1]) < 160:
            self.target = (x + self.rng.uniform(-8, 8), y + self.rng.uniform(-5, 5))
            self.speed = self.rng.uniform(18, 26)

    def update(self, dt):
        hx, hy = self.pts[0]
        tx, ty = self.target
        want = math.atan2(ty - hy, tx - hx)
        turn = (want - self.heading + math.pi) % math.tau - math.pi
        self.heading += max(-2.0 * dt, min(2.0 * dt, turn))
        self.wig += dt * self.speed * 0.6
        hx += math.cos(self.heading) * self.speed * dt
        hy += math.sin(self.heading) * self.speed * dt
        if math.hypot(tx - hx, ty - hy) < 6:
            self.target = self.pick()
            self.speed = self.rng.uniform(6, 11)
        self.pts[0] = [hx, hy]
        for i in range(1, len(self.pts)):
            px, py = self.pts[i - 1]
            x, y = self.pts[i]
            # a sideways swish travelling down the body
            nx, ny = -math.sin(self.heading), math.cos(self.heading)
            sw = math.sin(self.wig - i * 0.9) * 0.35 * i / len(self.pts)
            x += nx * sw
            y += ny * sw
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy) or 1
            self.pts[i] = [px + dx / d * self.SEG, py + dy / d * self.SEG]

    def draw_shadow(self, s):
        for (x, y), r in zip(self.pts, (2.4, 3, 2.7, 2.2, 1.6, 1.1, 0.8)):
            pygame.draw.circle(s, (60, 120, 170), (round(x + 3), round(y + 4)), r * self.size)

    def draw(self, s, t):
        radii = (2.4, 3, 2.7, 2.2, 1.6, 1.1, 0.8)
        for i in range(len(self.pts) - 1, -1, -1):
            x, y = self.pts[i]
            c = self.colors[min(i, len(self.colors) - 1)] if i < 4 else self.colors[-1]
            pygame.draw.circle(s, c, (round(x), round(y)), radii[i] * self.size)
        # tail fin: a little fan off the last segment
        (ax, ay), (bx, by) = self.pts[-2], self.pts[-1]
        ang = math.atan2(by - ay, bx - ax) + math.sin(self.wig * 1.3) * 0.5
        for spread in (-0.6, 0.6):
            ex = bx + math.cos(ang + spread) * 4 * self.size
            ey = by + math.sin(ang + spread) * 4 * self.size
            pygame.draw.line(s, mix(self.colors[-1], (255, 255, 255), 0.3), (bx, by), (ex, ey))
        # side fins and eyes
        hx, hy = self.pts[1]
        nx, ny = -math.sin(self.heading), math.cos(self.heading)
        flap = 2.5 + math.sin(self.wig * 2) * 0.8
        for k in (-1, 1):
            s.set_at((round(hx + nx * flap * k), round(hy + ny * flap * k)), mix(self.colors[0], (255, 255, 255), 0.5))
        ex, ey = self.pts[0]
        for k in (-1, 1):
            s.set_at((round(ex + nx * 1.2 * k + math.cos(self.heading)), round(ey + ny * 1.2 * k + math.sin(self.heading))),
                     (46, 36, 84))


class Pond:
    def __init__(self, w, h, seed=77):
        self.w, self.h = w, h
        rng = self.rng = random.Random(seed)
        self.bg = art.solid((w, h))
        bg = self.bg
        # water: bright where it reflects the sky near the bank, deeper further out
        for y in range(h):
            f = (y / h) ** 0.8
            lo = mix(WATER_TOP, WATER_DEEP, math.floor(f * 8) / 8)
            hi = mix(WATER_TOP, WATER_DEEP, math.ceil(f * 8) / 8)
            frac = f * 8 - math.floor(f * 8)
            bg.fill(lo, (0, y, w, 1))
            for x in range(w):
                if frac * 16 > art.BAYER[y % 4][x % 4] + 0.5:
                    bg.set_at((x, y), hi)
        # pebbles seen through the water
        for _ in range(int(w * h / 90)):
            x, y = rng.randrange(w), rng.randrange(h // 3, h)
            f = y / h
            c = mix(mix((200, 180, 220), WATER_DEEP, 0.45 + 0.2 * f), (40, 80, 130), rng.random() * 0.2)
            rx = rng.randint(2, 5)
            pygame.draw.ellipse(bg, c, (x, y, rx * 2, rx))
            bg.set_at((x + 1, y), mix(c, (255, 255, 255), 0.25))
        # the blossom tree's reflection, soft and pink
        refl = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(40):
            x = int(w * 0.72) + rng.randint(-40, 40)
            y = 30 + rng.randint(0, 50)
            pygame.draw.ellipse(refl, (255, 170, 214, 70), (x, y, rng.randint(14, 30), rng.randint(5, 9)))
        pygame.draw.rect(refl, (170, 110, 150, 60), (int(w * 0.72) + 8, 14, 10, 30))
        bg.blit(refl, (0, 0))
        # the bank along the top, continuing the meadow from the screen above
        bank = art.plane()
        leaf, leaf2 = (92, 196, 170), (132, 220, 152)
        pygame.draw.rect(bank, mix(leaf2, PAL["shade"], 0.2), (0, 0, w, 8))
        x = -4
        while x < w + 8:
            art.foliage(bank, rng, x, 8 + rng.randint(-2, 3), rng.randint(8, 14), 4, mix(leaf, PAL["shade"], 0.15), PAL,
                        leaf=(1, 3))
            x += rng.randint(8, 14)
        art.flowers(bank, rng, (0, 1, w, 8), [(255, 140, 200), (255, 232, 110), (196, 150, 255), (255, 255, 255)], w // 6)
        bg.blit(bank, (0, 0))
        # lily pads
        self.pads = []
        for _ in range(int(w / 22)):
            x, y = rng.randint(10, w - 20), rng.randint(20, h - 14)
            r = rng.randint(5, 9)
            self.pads.append((x, y, r, rng.random() * math.tau, rng.random() < 0.35))
        self.fish = [Fish(rng, w, h, KOI[i % len(KOI)]) for i in range(6)]
        self.ripples = []
        self.petals = [(rng.random() * w, rng.uniform(16, h - 6), rng.uniform(1, 3), rng.choice(
            [(255, 200, 230), (255, 255, 255), (255, 150, 200)])) for _ in range(26)]
        self.caustics = [(rng.random() * w, rng.uniform(h * 0.3, h), rng.random() * math.tau) for _ in range(int(w * h / 600))]
        self.reeds = [Blades(rng, (0, 10, 22, h - 10), 40, [(70, 160, 170), (92, 196, 170)], 8, 22, stiff=1.2),
                      Blades(rng, (w - 22, 10, 22, h - 10), 40, [(70, 160, 170), (92, 196, 170)], 8, 22, stiff=1.2)]
        self.bugs = Bugs(rng, [(rng.randint(30, w - 30), rng.randint(20, h - 40)) for _ in range(4)], (150, 255, 236),
                         wing=(220, 255, 255))
        self.next_plop = 3.0

    def click(self, x, y, t):
        self.ripples.append((x, y, t))
        for f in self.fish:
            f.lure(x, y)

    def update(self, dt, t):
        for f in self.fish:
            f.update(dt)
        if t > self.next_plop:  # now and then a fish kisses the surface
            f = self.rng.choice(self.fish)
            self.ripples.append((f.pts[0][0], f.pts[0][1], t))
            self.next_plop = t + self.rng.uniform(4, 10)
        self.ripples = [r for r in self.ripples if t - r[2] < 2.2]

    def draw(self, s, t):
        s.blit(self.bg, (0, 0))
        light = (214, 240, 255)
        for x, y, ph in self.caustics:
            k = math.sin(t * 1.3 + ph)
            if k > 0.2:
                xx = x + math.sin(t * 0.4 + ph) * 3
                pygame.draw.line(s, mix(WATER_DEEP, light, 0.35 * k), (xx, y), (xx + 3 + k * 2, y + math.sin(ph) * 1.5))
        for f in self.fish:
            f.draw_shadow(s)
        for f in self.fish:
            f.draw(s, t)
        for x, y, r, ph, bloom in self.pads:
            bob = math.sin(t * 0.8 + ph) * 0.6
            pad = (110, 206, 140)
            pygame.draw.ellipse(s, mix(pad, PAL["shade"], 0.35), (x - r + 1, y - r // 2 + 2 + bob, r * 2, r))
            pygame.draw.ellipse(s, pad, (x - r, y - r // 2 + bob, r * 2, r))
            pygame.draw.ellipse(s, mix(pad, PAL["light"], 0.35), (x - r + 2, y - r // 2 + bob, r, r // 2))
            a = ph
            pygame.draw.polygon(s, mix(WATER_TOP, WATER_DEEP, y / self.h), [
                (x, y + bob), (x + math.cos(a) * r, y + math.sin(a) * r / 2 + bob),
                (x + math.cos(a + 0.5) * r, y + math.sin(a + 0.5) * r / 2 + bob)])
            if bloom:
                fx, fy = x - 1, y - 2 + bob
                for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, -1), (-2, 0), (2, 0)):
                    s.set_at((int(fx + dx), int(fy + dy)), (255, 160, 210))
                s.set_at((int(fx), int(fy)), (255, 240, 160))
        for i, (x, y, sp, c) in enumerate(self.petals):
            xx = (x + t * sp) % self.w
            yy = y + math.sin(t * 0.5 + i) * 2
            s.set_at((int(xx), int(yy)), c)
            s.set_at((int(xx) + 1, int(yy)), mix(c, (120, 90, 150), 0.2))
        for x, y, t0 in self.ripples:
            age = t - t0
            for k in (0, 0.4):
                a = age - k
                if a <= 0:
                    continue
                r = a * 14
                c = mix((255, 255, 255), WATER_DEEP, a / 2.2)
                pygame.draw.ellipse(s, c, (x - r, y - r * 0.5, r * 2, r), 1)
        for b in self.reeds:
            b.draw(s, t)
        self.bugs.draw(s, t)
