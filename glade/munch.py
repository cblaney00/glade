"""The Munchling (2026-11-03, his design): the glade's predator, Forest Dex #448.

A noodle of a dragon: a long, near-black body on four stubby legs, a ragged purple mane
down its back, a glowing violet tuft at the tip of its tail, glowing slit-pupilled eyes and
one fang that always pokes out. Black and purple, fierce first and only a little cute (his
words) — the pet you would want if you had a pest problem.

In the game, its board sits beside Predator vision (lower screen, top left). Click it and a
Munchling zips in from the edge and, in under five seconds, eats every animal in the place
and on the ground below it: it springs from one to the next, nearest first, and each one it
snaps up stays glowing in its belly, which swells as it goes. Then it does one little happy
thing (a burp, a spin, a wag, a belly bounce — a different one each time) and wiggles off the
edge, full. As it goes, the same number of *new* animals come out (fresh IVs, like after a
Thunderstorm), so he can call it again and again to look for strong ones.

It also lives wild in the Forest, as rare as a legendary of its strength (legends2.py,
storm.rare); `draw_wyrm` draws it both ways.

Everything here is in the shared coordinates of apex.py: the top screen as it is, the lower
screen below it shifted by OFFSET.
"""

import math
import random

import pygame

import corner
import storm
from apex import OFFSET, ease, find_prey
from art import glow, mix
from battle import TEXT, cloth
from life import q

# black and purple, not too cute (his words, 2026-11-03)
BODY = (42, 30, 56)          # near black
BELLY = (88, 52, 124)        # a dark purple underside
MANE = (160, 80, 235)        # a ragged purple mane
MANE_HI = (200, 150, 255)
TUFT = (190, 110, 255)       # the glowing violet tip of its tail
INK = (8, 4, 12)
EYE = (210, 140, 255)        # glowing violet eyes, slit pupils
FANG = (240, 232, 250)

LENGTH = 40.0                # its body, head to tail, at size 1
EAT_FOR = 3.4                # all the eating fits in this (his rule: under 5 s with the dash in)
TRICKS = ("burp", "spin", "wag", "bounce", "wink")


# --- drawing ------------------------------------------------------------------------------

def spine_of(trail, length):
    """Points every 2 px along `trail` (head first) for `length` px."""
    pts, need = [trail[0]], 2.0
    left = length
    for (x0, y0), (x1, y1) in zip(trail, trail[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        d = 0.0
        while seg > 0 and d + need <= seg and left > 0:
            d += need
            k = d / seg
            pts.append((x0 + (x1 - x0) * k, y0 + (y1 - y0) * k))
            left -= 2.0
            need = 2.0
        need -= seg - d
        if left <= 0:
            break
    while left > 0 and len(pts) > 1:  # not enough trail yet: carry straight on behind
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        d = math.hypot(bx - ax, by - ay) or 1.0
        pts.append((bx + (bx - ax) / d * 2, by + (by - ay) / d * 2))
        left -= 2.0
    return pts


def draw_wyrm(s, spine, z, t, phase=0.0, mouth=0.0, fat=1.0, lumps=(), squint=False, wink=False,
              walking=True, tuft=1.0):
    """The Munchling along `spine` (canvas points, head first, 2 px apart at size 1)."""
    n = len(spine)
    if n < 3:
        return
    lights = []
    hx, hy = spine[0]
    fx, fy = hx - spine[2][0], hy - spine[2][1]
    d = math.hypot(fx, fy) or 1.0
    fx, fy = fx / d, fy / d
    face = 1 if fx >= 0 else -1
    ux, uy = fy * face, -fx * face  # "up" for the head, whichever way it points

    def radius(u):
        base = 1.0 + 2.8 * (1 - u) ** 0.6 - 1.3 * math.exp(-((u - 0.09) / 0.05) ** 2)  # a thin neck
        belly = 3.4 * (fat - 1) * math.exp(-((u - 0.5) / 0.2) ** 2)
        return (base + belly) * z

    # legs: four stubby feet under the body, stepping as it goes
    for i, u in enumerate((0.28, 0.33, 0.62, 0.67)):
        x, y = spine[min(n - 1, round(u * (n - 1)))]
        r = radius(u)
        step = math.sin(t * 14 + i * 2.1 + phase) * 1.2 * z if walking else 0
        c = mix(BELLY, INK, 0.55 if i % 2 == 0 else 0.3)
        pygame.draw.line(s, c, (round(x), round(y + r * 0.3)), (round(x + step), round(y + r + 2.2 * z)), max(1, round(1.6 * z)))
        pygame.draw.line(s, mix(MANE_HI, INK, 0.3), (round(x + step), round(y + r + 2.2 * z)),
                         (round(x + step + 1.4 * z), round(y + r + 2.4 * z)))  # little claws
    # the body, tail first, so the head is on top
    for i in range(n - 1, 0, -1):
        u = i / (n - 1)
        x, y = spine[i]
        r = radius(u)
        pygame.draw.circle(s, mix(BODY, INK, 0.45), (round(x), round(y + 0.8 * z)), max(1, round(r)))
        pygame.draw.circle(s, BODY, (round(x), round(y)), max(1, round(r)))
        if r > 1.5:  # a purple sheen along its top
            pygame.draw.circle(s, mix(BODY, MANE, 0.35), (round(x), round(y - r * 0.45)), max(1, round(r * 0.45)))
        if r > 2:
            pygame.draw.circle(s, BELLY if fat > 1.25 and 0.3 < u < 0.7 else mix(BODY, BELLY, 0.35),
                               (round(x), round(y + r * 0.45)), max(1, round(r * 0.5)))
        if i % 5 == 0 and r > 2:  # soft darker bands down its back
            pygame.draw.circle(s, mix(BODY, INK, 0.2), (round(x), round(y - r * 0.4)), max(1, round(r * 0.45)))
    # what it has eaten, glowing through its skin
    for k, (color, u) in enumerate(lumps):
        x, y = spine[min(n - 1, max(3, round(u * (n - 1))))]
        r = radius(u)
        pygame.draw.circle(s, mix(BELLY, color, 0.8), (round(x + math.sin(k * 2.3) * r * 0.35), round(y + r * 0.2)), max(1, round(1.4 * z)))
        lights.append((x, y + r * 0.2, 4 * z, color, 28))
    # the mane: ragged purple spikes down the top of its back, bristling
    for i in range(3, int(n * 0.8)):
        if i % 2:
            continue
        u = i / (n - 1)
        x, y = spine[i]
        r = radius(u)
        a, b = spine[i - 1], spine[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        dd = math.hypot(tx, ty) or 1.0
        nx, ny = ty / dd, -tx / dd
        if ny > 0:
            nx, ny = -nx, -ny
        ruff = 0.8 + 0.3 * math.sin(t * 5 + i * 0.9 + phase)
        h = (3.4 - 2.4 * u) * z * ruff
        bx, by = x + nx * r * 0.7, y + ny * r * 0.7
        lean = -face * 1.2 * z  # the spikes sweep back
        tip = (bx + nx * h + lean, by + ny * h)
        pygame.draw.polygon(s, MANE, [(bx - tx / dd * 1.6 * z, by - ty / dd * 1.6 * z), (bx + tx / dd * 1.6 * z, by + ty / dd * 1.6 * z), tip])
        s.set_at((round(tip[0]), round(tip[1])), MANE_HI)
    # the tail's glowing tuft, flicking
    tx, ty = spine[-1]
    wag = math.sin(t * 6 + phase) * 1.5 * z
    for j in range(3):
        pygame.draw.circle(s, mix(TUFT, (255, 255, 255), 0.3 * j), (round(tx + wag - j * 0.6 * z), round(ty - j * 0.8 * z)),
                           max(1, round((2.4 - 0.6 * j) * z)))
    lights.append((tx + wag, ty, 7 * z, TUFT, q(50 + 30 * tuft)))
    # the head: a round skull, long jaws, two swept-back horns, the mane behind
    hr = 4.6 * z
    pygame.draw.circle(s, mix(BODY, INK, 0.45), (round(hx), round(hy + 0.8 * z)), round(hr))
    pygame.draw.circle(s, BODY, (round(hx), round(hy)), round(hr))
    pygame.draw.circle(s, mix(BODY, MANE, 0.3), (round(hx - fx * hr * 0.2 + ux * hr * 0.35), round(hy - fy * hr * 0.2 + uy * hr * 0.35)), max(1, round(hr * 0.45)))
    for k in (-0.6, -0.15):  # horns, swept back
        bx, by = hx + fx * hr * k + ux * hr * 0.8, hy + fy * hr * k + uy * hr * 0.8
        pygame.draw.line(s, (150, 130, 170), (round(bx), round(by)), (round(bx + ux * 2 * z - fx * 2.6 * z), round(by + uy * 2 * z - fy * 2.6 * z)), max(1, round(z)))
    for k in range(3):  # its mane starts right behind the head
        a = -0.9 - k * 0.35
        pygame.draw.circle(s, MANE, (round(hx + fx * hr * a + ux * hr * (0.7 - 0.15 * k)), round(hy + fy * hr * a + uy * hr * (0.7 - 0.15 * k))), max(1, round((2.2 - 0.3 * k) * z)))
    # the jaws: shut, one fang pokes out over the lip; open, they gape wide
    gape = 0.1 + 0.5 * mouth
    bx, by = hx + fx * hr * 0.45, hy + fy * hr * 0.45
    jaw = hr * 1.7
    up = (fx * math.cos(gape) + ux * math.sin(gape), fy * math.cos(gape) + uy * math.sin(gape))
    dn = (fx * math.cos(gape) - ux * math.sin(gape), fy * math.cos(gape) - uy * math.sin(gape))
    tu = (bx + up[0] * jaw, by + up[1] * jaw)
    tl = (bx + dn[0] * jaw * 0.85, by + dn[1] * jaw * 0.85)
    if mouth > 0.1:
        pygame.draw.polygon(s, INK, [(bx, by), tu, tl])
        pygame.draw.circle(s, (150, 40, 90), (round((bx + tu[0] + tl[0]) / 3), round((by + tu[1] + tl[1]) / 3)), max(1, round(z)))
    top = (bx + ux * hr * 0.6, by + uy * hr * 0.6)
    pygame.draw.polygon(s, mix(BODY, MANE, 0.18), [top, (bx - ux * hr * 0.05, by - uy * hr * 0.05), tu])
    pygame.draw.line(s, mix(BODY, MANE, 0.55), (round(top[0]), round(top[1])), (round(tu[0]), round(tu[1])))  # a sheen along the snout
    pygame.draw.polygon(s, mix(BODY, MANE, 0.08), [(bx - ux * hr * 0.1, by - uy * hr * 0.1), (bx - ux * hr * 0.55, by - uy * hr * 0.55), tl])
    s.set_at((round(tu[0] - up[0] * z + ux * z), round(tu[1] - up[1] * z + uy * z)), INK)  # nostril
    for tip, d, n in ((tu, up, -1), (tl, dn, 1)):  # fangs, pointing across the gap
        if n > 0 and mouth <= 0.1:
            continue
        fx0, fy0 = tip[0] - d[0] * 1.5 * z, tip[1] - d[1] * 1.5 * z
        pygame.draw.line(s, FANG, (round(fx0), round(fy0)), (round(fx0 + n * ux * 2 * z), round(fy0 + n * uy * 2 * z)))
    # the eye: big, round and shiny (or happy ^ when content)
    ex, ey = hx + fx * hr * 0.25 + ux * hr * 0.3, hy + fy * hr * 0.25 + uy * hr * 0.3
    er = max(1, round(2.2 * z))
    blink = (t * 0.9 + phase * 3) % 4.3 < 0.12
    if squint or wink or blink:
        pygame.draw.lines(s, EYE, False, [(round(ex - er), round(ey)), (round(ex), round(ey - er)), (round(ex + er), round(ey))], 1)
    else:  # a glowing eye under a heavy brow, with a slit pupil
        pygame.draw.circle(s, EYE, (round(ex), round(ey)), er)
        pygame.draw.line(s, INK, (round(ex + fx * 0.4 * z), round(ey - er + 1)), (round(ex + fx * 0.4 * z), round(ey + er - 1)))
        s.set_at((round(ex - 0.5 * z), round(ey - 0.6 * z)), (250, 235, 255))
        pygame.draw.line(s, INK, (round(ex - fx * er - ux * er * 0.2), round(ey - fy * er - uy * er * 1.3)),
                         (round(ex + fx * er + ux * er * 0.9), round(ey + fy * er - uy * er * 0.5)), max(1, round(z)))  # the brow
    lights.append((ex, ey, 5 * z, EYE, 60))
    for x, y, r, c, a in lights:
        glow(s, x, y, max(2, round(r)), c, a)


def draw_munch(o, s, t):
    """A wild Munchling (a Walker of kind "munch"): its body trails behind its head and
    ripples as it trots."""
    z, x, y, f = o.size * 0.85, o.x, o.y, o.facing
    walking = getattr(o, "wait", 0) <= 0
    ph = (o.step if walking else t * 0.8) + o.phase
    spine = []
    n = int(LENGTH / 2)
    for i in range(n):
        u = i / (n - 1)
        wave = math.sin(u * 6 - ph * (2.2 if walking else 1)) * (2.2 if walking else 1.0) * z * u
        spine.append((x + f * (12 - u * LENGTH) * z, y - 5.5 * z + wave + u * 1.5 * z - (1 - u) ** 6 * 2 * z))
    draw_wyrm(s, spine, z, t, o.phase, walking=walking)


def glow_munch(o, s, t, st, k):
    pass  # (draw_wyrm lights its own tail)


# --- the button -----------------------------------------------------------------------------

def button_rect(view):
    """Beside Predator vision (his pick)."""
    r = corner.rect("vision")
    return pygame.Rect(r.right + corner.GAP, r.y, 104, r.h)


def draw_button(s, view, font, on):
    r = button_rect(view)
    m = view.mouse()
    hot = on or (bool(m) and r.collidepoint(m))
    cloth(s, r, (110, 60, 160), hot=hot, alpha=230)
    spine = [(r.x + 17 - i * 1.4, r.centery + math.sin(i * 0.6) * 1.2) for i in range(10)]
    draw_wyrm(s, spine, 0.55, pygame.time.get_ticks() / 1000, walking=False, mouth=0.6 if hot else 0.0)
    img = font.render("Munchling", False, (255, 255, 255) if hot else TEXT)
    s.blit(img, (r.x + 24, r.centery - img.get_height() // 2))


# --- the hunt -------------------------------------------------------------------------------

class Bit:
    """A crumb flung off as it chomps, or a burp bubble."""

    def __init__(self, x, y, color, vx, vy, life, bubble=0):
        self.x, self.y, self.color, self.vx, self.vy, self.life, self.age = x, y, color, vx, vy, life, 0.0
        self.bubble = bubble

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.bubble:
            self.vy -= 10 * dt
        else:
            self.vy += 260 * dt
        return self.age < self.life

    def draw(self, s, ox, oy):
        x, y = self.x - ox, self.y - oy
        k = 1 - self.age / self.life
        if self.bubble:
            r = round(self.bubble * (0.6 + 0.6 * self.age / self.life))
            pygame.draw.circle(s, mix(MANE_HI, (255, 255, 255), 0.4), (round(x), round(y)), max(1, r), 1)
            s.set_at((round(x - r * 0.4), round(y - r * 0.4)), (255, 255, 255))
        else:
            s.set_at((round(x), round(y)), mix(self.color, (255, 255, 255), 0.3))
            glow(s, x, y, 3, self.color, q(50 * k))


class Munch:
    """One visit: a little script (a generator, a frame at a time) plus the new animals coming
    out after it. Started from the game (game.py) like a Thunderstorm, for the place on screen."""

    def __init__(self, glade, t, seed=None):
        self.rng = random.Random(seed)
        self.scene = glade.here
        self.lower = glade.lower() if glade.bottom else None
        self.low_w, self.low_h = (glade.bottom.w, glade.bottom.h) if glade.bottom else (0, 0)
        glade.lifespans.settle()
        self.keep = glade.lifespans.keep(glade)
        prey, self.swarms = find_prey(self.scene, self.lower)
        self.prey = [p for p in prey if not any(p.obj is k for k in self.keep)]
        self.t0 = self.t = t
        self.dt = 0.0
        self.z = 1.4
        self.head = (-30.0, 470.0)
        self.trail = [self.head]
        self.mouth, self.fat, self.lumps = 0.0, 1.0, []
        self.squint = self.wink = False
        self.tuft = 0.0
        self.bits, self.moves, self.slurp = [], [], None
        self.out_since = {}            # firefly (swarm, i) -> when it was eaten
        self.back_at = {}              # ... -> when it starts glowing again
        self.came_out = False
        self.gone = False              # it has left
        self.done = False
        self.script = self.run()

    # moving the head; the body follows its trail ---------------------------------------------
    def move(self, x, y):
        self.head = (x, y)
        if math.dist(self.trail[0], self.head) >= 1.0:
            self.trail.insert(0, self.head)
            total, keep = 0.0, 1
            for a, b in zip(self.trail, self.trail[1:]):
                total += math.dist(a, b)
                keep += 1
                if total > LENGTH * self.z + 4:
                    break
            del self.trail[keep:]

    def wait(self, secs, each=None):
        end = self.t + secs
        while self.t < end:
            if each:
                each(1 - (end - self.t) / secs)
            yield

    def ground(self, x, y):
        """A place on the ground near (x, y) on the screen it is on."""
        if y < OFFSET[1] or self.lower is None:
            return max(10.0, min(950.0, x)), 470.0 if y < OFFSET[1] else y
        return x, max(OFFSET[1] + 20.0, min(OFFSET[1] + self.low_h - 20.0, y))

    # the visit --------------------------------------------------------------------------------
    def run(self):
        prey = list(self.prey)
        meals = len(prey) + (1 if self.swarms else 0)
        each = max(0.1, min(0.42, EAT_FOR / max(1, meals)))
        # in it zips, from whichever side is nearer the first meal
        first = min(prey, key=lambda p: p.pos()[0], default=None)
        side = self.rng.choice((-1, 1)) if first is None else (-1 if first.pos()[0] < 480 else 1)
        sx, sy = first.pos() if first is not None else (480.0, 470.0)
        gx, gy = self.ground(sx, sy)
        x0 = (OFFSET[0] - 40 if gy >= OFFSET[1] else -40) if side < 0 else (OFFSET[0] + self.low_w + 40 if gy >= OFFSET[1] else 1000)
        self.trail = [(x0 - side * i, gy) for i in range(0, 60, 2)]
        self.head = self.trail[0]
        x1 = x0 - side * 70
        yield from self.wait(0.3, lambda k: self.move(x0 + (x1 - x0) * ease(k), gy - abs(math.sin(k * 6)) * 3))
        # nearest first, springing from one to the next
        while prey:
            p = min(prey, key=lambda p: math.dist(self.head, p.pos()))
            prey.remove(p)
            if p.obj.__dict__.get("gone"):
                continue  # gone already (it slipped away)
            yield from self.catch(p, each)
        if self.swarms:
            yield from self.fireflies(each)
        yield from self.trick()
        yield from self.leave()
        while any(not m.done for m in self.moves) or self.bits:
            yield
        self.finish()

    def catch(self, p, secs):
        hx, hy = self.head
        hop = min(70.0, 10 + math.dist(self.head, p.pos()) * 0.18)

        def spring(k):
            tx, ty = p.pos()
            e = ease(k)
            self.move(hx + (tx - hx) * e, hy + (ty - hy) * e - math.sin(k * math.pi) * hop)
            self.mouth = min(1.0, k * 1.6)
        yield from self.wait(secs * 0.72, spring)
        p.hide()  # CHOMP
        self.mouth = 0.0
        x, y = self.head
        for _ in range(4):
            self.bits.append(Bit(x, y, p.color, self.rng.uniform(-70, 70), self.rng.uniform(-110, -30), 0.45))
        self.lumps.append((p.color, self.rng.uniform(0.32, 0.7)))
        self.fat = min(2.3, self.fat + 0.07)
        yield from self.wait(secs * 0.28, lambda k: setattr(self, "squint", True))
        self.squint = False

    def fireflies(self, secs):
        """Last, one long slurp: every firefly streams into its open mouth."""
        streams = []
        for si, (swarm, low) in enumerate(self.swarms):
            for i in range(len(swarm.items)):
                if i < len(swarm.now) and swarm.now[i][0] > -50:
                    x, y = swarm.now[i][:2]
                    streams.append(((x + OFFSET[0], y + OFFSET[1]) if low else (x, y), swarm.color, (si, i)))
        self.slurp = (self.t, streams, max(0.35, secs))
        for _, _, key in streams:
            self.out_since[key] = self.t
        yield from self.wait(max(0.35, secs), lambda k: setattr(self, "mouth", 1.0))
        self.slurp = None
        self.mouth = 0.0
        color = self.swarms[0][0].color
        self.lumps += [(color, self.rng.uniform(0.35, 0.65)) for _ in range(3)]
        self.fat = min(2.3, self.fat + 0.1)

    def trick(self):
        """One happy little thing before it goes, a different one each time."""
        kind = self.rng.choice(TRICKS)
        x, y = self.head
        if kind == "burp":
            yield from self.wait(0.25, lambda k: setattr(self, "mouth", ease(k)))
            self.bits.append(Bit(x + 4, y - 4, MANE_HI, self.rng.uniform(-6, 6), -30, 1.2, bubble=4))
            yield from self.wait(0.4, lambda k: setattr(self, "squint", True))
            self.mouth, self.squint = 0.0, False
        elif kind == "spin":  # a happy loop-the-loop
            yield from self.wait(0.7, lambda k: self.move(x + math.sin(k * math.tau) * 12, y - (1 - math.cos(k * math.tau)) * 12))
        elif kind == "wag":
            yield from self.wait(0.7, lambda k: (setattr(self, "squint", True), setattr(self, "tuft", abs(math.sin(k * 12)))))
            self.squint, self.tuft = False, 0.0
        elif kind == "bounce":  # bounces its full belly
            yield from self.wait(0.6, lambda k: self.move(x, y - abs(math.sin(k * math.pi * 3)) * 5))
        else:
            yield from self.wait(0.6, lambda k: setattr(self, "wink", 0.2 < k < 0.8))
            self.wink = False

    def leave(self):
        """It wiggles off the nearer edge of the screen it is on, full; the new animals come out."""
        x, y = self.head
        gx, gy = self.ground(x, y)
        if abs(gy - y) > 2 or abs(gx - x) > 2:  # back down to the ground first
            yield from self.wait(0.25, lambda k: self.move(x + (gx - x) * ease(k), y + (gy - y) * ease(k)))
        low = gy >= OFFSET[1]
        left, right = (OFFSET[0] - 60, OFFSET[0] + self.low_w + 60) if low else (-60, 1020)
        end = left if gx - left < right - gx else right
        self.come_out()
        secs = min(2.4, max(1.2, abs(end - gx) / 260))
        yield from self.wait(secs, lambda k: self.move(gx + (end - gx) * k, gy + math.sin(k * secs * 9) * 4))
        self.gone = True

    def come_out(self):
        """As many new animals as it ate, a mix of everyone who lives here (storm.choose), coming
        out one after another; the koi it ate come back, new ones too, and the fireflies glow again."""
        if self.came_out:
            return
        self.came_out = True
        eaten = {id(p.obj) for p in self.prey if p.eaten}
        n = 0
        for content, low in ((self.scene, False), (self.lower, True)):
            if content is None:
                continue
            animals = [o for o in storm.roster(content) if not any(o is k for k in self.keep)]
            ate = sum(1 for o in storm.roster(content, any_family=True) if id(o) in eaten)
            waiting = [o for o in animals if getattr(o, "gone", False)]
            for o in storm.choose(waiting, self.rng, ate):
                storm.fresh(o)
                self.moves.append(storm.Shelter(o, low, False, self.t + 0.3 + n * 0.12, self.rng))
                n += 1
            pond = getattr(content, "pond", None)
            for f in getattr(pond, "fish", []) if pond is not None else []:
                if id(f) in eaten:
                    f.ivs = f.nature = None  # a new one
                    self.moves.append(storm.Shelter(f, low, False, self.t + 0.5 + self.rng.uniform(0, 1.0), self.rng))
        for key in self.out_since:
            self.back_at[key] = self.t + self.rng.uniform(0.5, 2.5)

    # every frame ------------------------------------------------------------------------------
    def update(self, dt, t):
        self.dt, self.t = dt, t
        if not self.done and t - self.t0 > 30:  # whatever happened, never let it linger
            self.finish()
        if not self.done:
            try:
                next(self.script)
            except StopIteration:
                self.finish()
        self.bits = [b for b in self.bits if b.update(dt)]
        for m in self.moves:
            m.update(t)
        for (si, i), out in self.out_since.items():
            swarm = self.swarms[si][0]
            back = self.back_at.get((si, i))
            swarm.mult[i] = ease((t - back) / 1.5) if back is not None and t > back else 1 - ease((t - out) / 0.3)

    def finish(self):
        """Over (or he walked off): everything settled as it would have ended."""
        if self.done:
            return
        self.come_out()
        for m in self.moves:
            m.begun = m.done = True
            m.obj.gone = m.out
        for swarm, _ in self.swarms:
            swarm.mult.clear()
        self.gone = self.done = True

    def draw(self, s, low, t, scratch):
        ox, oy = OFFSET if low else (0, 0)
        for m in self.moves:
            m.draw(s, low, t, scratch)
        for b in self.bits:
            b.draw(s, ox, oy)
        if self.slurp is not None:  # fireflies streaming into its mouth
            t0, streams, secs = self.slurp
            k = ease((t - t0) / secs)
            hx, hy = self.head
            for (x, y), c, key in streams:
                e = min(1.0, k * (1.2 + (hash(key) % 7) * 0.08))
                px, py = x + (hx - x) * e - ox, y + (hy - y) * e - oy - math.sin(e * math.pi) * 10
                s.set_at((round(px), round(py)), c) if s.get_rect().collidepoint(px, py) else None
                glow(s, px, py, 4, c, 40)
        if self.gone:
            return
        spine = [(x - ox, y - oy) for x, y in spine_of(self.trail, LENGTH * self.z)]
        if not any(-60 < x < s.get_width() + 60 and -60 < y < s.get_height() + 60 for x, y in spine[::4]):
            return
        draw_wyrm(s, spine, self.z, t, mouth=self.mouth, fat=self.fat, lumps=self.lumps,
                  squint=self.squint, wink=self.wink, tuft=self.tuft)
