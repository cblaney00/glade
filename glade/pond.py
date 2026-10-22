"""The lily pond in the foreground of the Glade (on the lower monitor).

Koi with floppy chain bodies wander under the lily pads; click the water and it
ripples, the fish come to see what fell in, and the glowing plankton in the water
lights up where it was disturbed. The water is an ellipse; everything here stays
inside it.
"""

import math

import pygame

from art import GLOW, glow, mix, scale

KOI = [
    [(255, 250, 244), (255, 166, 120), (255, 250, 244), (255, 166, 120)],
    [(255, 150, 190), (255, 250, 244), (255, 150, 190), (255, 210, 230)],
    [(255, 226, 120), (255, 250, 244), (255, 226, 120), (255, 196, 110)],
    [(255, 250, 244), (190, 160, 255), (255, 250, 244), (255, 250, 244)],
    [(255, 176, 130), (255, 176, 130), (255, 250, 244), (255, 130, 110)],
]


class Water:
    """An elliptical body of water: knows what is inside it."""

    def __init__(self, cx, cy, rx, ry):
        self.cx, self.cy, self.rx, self.ry = cx, cy, rx, ry

    def inside(self, x, y, margin=1.0):
        return ((x - self.cx) / self.rx) ** 2 + ((y - self.cy) / self.ry) ** 2 < margin

    def pick(self, rng, margin=0.6):
        while True:
            x = rng.uniform(self.cx - self.rx, self.cx + self.rx)
            y = rng.uniform(self.cy - self.ry, self.cy + self.ry)
            if self.inside(x, y, margin):
                return x, y


class Fish:
    SEG = 6.6
    RADII = (4.8, 6, 5.4, 4.4, 3.2, 2.2, 1.6)

    def __init__(self, rng, water, colors, tint):
        self.rng, self.water = rng, water
        # seen through water: colours pulled a little toward the water
        self.colors = [mix(c, tint, 0.22) for c in colors]
        self.lit = [mix(c, (255, 255, 255), 0.35) for c in self.colors]
        x, y = water.pick(rng)
        self.heading = rng.random() * math.tau
        self.pts = [[x, y] for _ in range(7)]
        self.target = water.pick(rng)
        self.speed = rng.uniform(14, 22)
        self.wig = rng.random() * 10
        self.size = rng.uniform(0.9, 1.15)

    def lure(self, x, y):
        if math.hypot(x - self.pts[0][0], y - self.pts[0][1]) < 320:
            self.target = (x + self.rng.uniform(-16, 16), y + self.rng.uniform(-10, 10))
            self.speed = self.rng.uniform(36, 52)

    def update(self, dt):
        hx, hy = self.pts[0]
        tx, ty = self.target
        want = math.atan2(ty - hy, tx - hx)
        turn = (want - self.heading + math.pi) % math.tau - math.pi
        self.heading += max(-2.0 * dt, min(2.0 * dt, turn))
        self.wig += dt * self.speed * 0.3
        nx_, ny_ = hx + math.cos(self.heading) * self.speed * dt, hy + math.sin(self.heading) * self.speed * dt
        if self.water.inside(nx_, ny_, 0.75):
            hx, hy = nx_, ny_
        else:  # nose at the bank: turn back toward the middle
            self.target = self.water.pick(self.rng, 0.3)
        if math.hypot(tx - hx, ty - hy) < 12:
            self.target = self.water.pick(self.rng)
            self.speed = self.rng.uniform(12, 22)
        self.pts[0] = [hx, hy]
        nx, ny = -math.sin(self.heading), math.cos(self.heading)
        seg = 4.4 * self.size
        for i in range(1, len(self.pts)):
            px, py = self.pts[i - 1]
            x, y = self.pts[i]
            sw = math.sin(self.wig - i * 0.9) * 0.7 * i / len(self.pts)  # a swish travelling down the body
            x, y = x + nx * sw, y + ny * sw
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy) or 1
            self.pts[i] = [px + dx / d * seg, py + dy / d * seg]

    def draw_shadow(self, s, color):
        for (x, y), r in zip(self.pts, self.RADII):
            pygame.draw.circle(s, color, (round(x + 6), round(y + 8)), r * self.size)

    def draw(self, s, t):
        sz = self.size
        nx, ny = -math.sin(self.heading), math.cos(self.heading)
        for i in range(len(self.pts) - 1, -1, -1):
            x, y = self.pts[i]
            c = self.colors[min(i, len(self.colors) - 1)]
            pygame.draw.circle(s, c, (round(x), round(y)), self.RADII[i] * sz)
        for i in range(len(self.pts) - 2):  # a lit stripe down the back
            x, y = self.pts[i]
            pygame.draw.circle(s, self.lit[min(i, len(self.lit) - 1)], (round(x - nx), round(y - ny)),
                               max(1, self.RADII[i] * sz * 0.4))
        (ax, ay), (bx, by) = self.pts[-2], self.pts[-1]
        ang = math.atan2(by - ay, bx - ax) + math.sin(self.wig * 1.3) * 0.5
        for spread in (-0.6, 0.6):  # tail fin
            for k in (6, 8):
                pygame.draw.line(s, mix(self.colors[-1], (255, 255, 255), 0.3), (bx, by),
                                 (bx + math.cos(ang + spread * k / 7) * k * sz * 1.2,
                                  by + math.sin(ang + spread * k / 7) * k * sz * 1.2))
        hx, hy = self.pts[1]
        flap = 6 * sz + math.sin(self.wig * 2) * 1.6
        for k in (-1, 1):  # side fins
            pygame.draw.line(s, mix(self.colors[0], (255, 255, 255), 0.5), (hx + nx * 3 * k, hy + ny * 3 * k),
                             (hx + nx * flap * k - math.cos(self.heading) * 3, hy + ny * flap * k - math.sin(self.heading) * 3), 2)
        ex, ey = self.pts[0]
        for k in (-1, 1):  # eyes
            s.set_at((round(ex + nx * 2.4 * sz * k + math.cos(self.heading) * 2),
                      round(ey + ny * 2.4 * sz * k + math.sin(self.heading) * 2)), (46, 36, 84))


class Pond:
    """The moving parts of the pond: koi, lily pads, petals, ripples, caustics and
    glowing plankton."""

    def __init__(self, rng, water, deep, light, pad):
        self.rng, self.water, self.deep, self.light_c, self.pad = rng, water, deep, light, pad
        self.fish = [Fish(rng, water, KOI[i % len(KOI)], deep) for i in range(6)]
        self.pads = []
        for _ in range(16):
            x, y = water.pick(rng, 0.8)
            self.pads.append((x, y, rng.randint(10, 18), rng.random() * math.tau, rng.random() < 0.35))
        self.petals = [(*water.pick(rng, 0.85), rng.uniform(-1.5, 1.5), rng.choice(
            [(255, 200, 230), (255, 255, 255), (255, 150, 200)])) for _ in range(30)]
        self.caustics = [(*water.pick(rng, 0.85), rng.random() * math.tau) for _ in range(120)]
        self.plankton = [(*water.pick(rng, 0.9), rng.random() * math.tau, rng.uniform(0.5, 1.5)) for _ in range(90)]
        self.ripples = []
        self.next_plop = 3.0

    def poke(self, x, y, t):
        if not self.water.inside(x, y):
            return False
        self.ripples.append((x, y, t))
        for f in self.fish:
            f.lure(x, y)
        return True

    def update(self, dt, t):
        for f in self.fish:
            f.update(dt)
        if t > self.next_plop:  # now and then a fish kisses the surface
            f = self.rng.choice(self.fish)
            self.ripples.append((f.pts[0][0], f.pts[0][1], t))
            self.next_plop = t + self.rng.uniform(4, 10)
        self.ripples = [r for r in self.ripples if t - r[2] < 2.4]

    def draw(self, s, t):
        w = self.water
        for x, y, ph in self.caustics:
            k = math.sin(t * 1.3 + ph)
            if k > 0.2:
                xx = x + math.sin(t * 0.4 + ph) * 6
                pygame.draw.line(s, mix(self.deep, self.light_c, 0.3 * k), (xx, y), (xx + 6 + k * 4, y + math.sin(ph) * 3))
        shadow = mix(self.deep, (20, 30, 70), 0.35)
        for f in self.fish:
            f.draw_shadow(s, shadow)
        for f in self.fish:
            f.draw(s, t)
        dark, light = mix(self.pad, (20, 30, 70), 0.4), mix(self.pad, self.light_c, 0.3)
        vein = mix(self.pad, (20, 30, 70), 0.2)
        for x, y, r, ph, bloom in self.pads:
            bob = math.sin(t * 0.8 + ph) * 1.2
            pygame.draw.ellipse(s, dark, (x - r + 2, y - r // 2 + 4 + bob, r * 2, r))
            pygame.draw.ellipse(s, self.pad, (x - r, y - r // 2 + bob, r * 2, r))
            pygame.draw.ellipse(s, light, (x - r + 4, y - r // 2 + bob, r, r // 2))
            for a in (ph + 1.6, ph + 2.6, ph + 3.6, ph + 4.6):
                pygame.draw.line(s, vein, (x, y + bob), (x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.4 + bob))
            pygame.draw.polygon(s, self.deep, [  # the notch every lily pad has
                (x, y + bob), (x + math.cos(ph) * r, y + math.sin(ph) * r / 2 + bob),
                (x + math.cos(ph + 0.5) * r, y + math.sin(ph + 0.5) * r / 2 + bob)])
        for i, (x, y, sp, c) in enumerate(self.petals):
            xx = x + math.sin(t * 0.07 * sp + i) * 40
            yy = y + math.sin(t * 0.5 + i) * 4
            if w.inside(xx, yy, 0.9):
                s.set_at((int(xx), int(yy)), c)
                s.set_at((int(xx) + 1, int(yy)), c)
                s.set_at((int(xx), int(yy) + 1), mix(c, (120, 90, 150), 0.2))
        for x, y, t0 in self.ripples:
            age = t - t0
            for k in (0, 0.4):
                a = age - k
                if a <= 0:
                    continue
                r = a * 28
                pygame.draw.ellipse(s, mix((255, 255, 255), self.deep, a / 2.4), (x - r, y - r * 0.5, r * 2, r), 1)

    def light(self, lm, t):
        for x, y, t0 in self.ripples:
            k = 1 - (t - t0) / 2.4
            glow(lm, x, y, 60, GLOW["cyan"], int(120 * k) // 12 * 12)

    def shine(self, s, t):
        for x, y, r, ph, bloom in self.pads:  # water lilies that glow
            if bloom:
                bob = math.sin(t * 0.8 + ph) * 1.2
                fx, fy = x - 2, y - 4 + bob
                glow(s, fx, fy, 10, GLOW["pink"], 70)
                for dx, dy in ((0, 0), (-2, 2), (2, 2), (0, -2), (-4, 0), (4, 0), (-1, 1), (1, 1)):
                    s.set_at((int(fx + dx), int(fy + dy)), (255, 170, 220))
                s.set_at((int(fx), int(fy)), (255, 240, 170))
        for x, y, ph, sp in self.plankton:
            k = math.sin(t * sp + ph)
            near = 0.0
            for rx_, ry_, t0 in self.ripples:  # stirred-up plankton flares
                d = math.hypot(x - rx_, (y - ry_) * 2) - (t - t0) * 28
                if abs(d) < 14:
                    near = max(near, 1 - (t - t0) / 2.4)
            k = max(k, near * 2 - 1)
            if k > 0.5:
                xx, yy = x + math.sin(t * 0.3 + ph) * 4, y
                s.set_at((int(xx), int(yy)), scale(GLOW["cyan"], 0.4 + 0.6 * k))
                if k > 0.8:
                    glow(s, xx, yy, 3, GLOW["cyan"], 60)
