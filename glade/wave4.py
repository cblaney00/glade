"""The Forest Dex's page three (2026-10-27, his ask): sixteen new lines of three, from the two
new places. The Crystal Caverns (above the Waterfall): Geodling, Humlet, Dripling, Lumicrawl,
Umbrit, Ferrodig, Shardling, Pebblefist. The Starfall Meadow (beside the Waterfall): Twinklet,
Tufflet, Meteorlet, Kickbud, Zaplet, Dreamote, Dustlet, Wishlet.

Each kind's `draw_<kind>` draws all three of its stages (`self.stage`), and `glow_<kind>` its
lights; both are set on beasts.Walker / beasts.Flier at the bottom of this file.
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, INK, LIT, PRISM, WALKERS, Flier, Walker
from life import q

WHITE = (255, 255, 255)
CAVE_WALK = ("geode", "drip", "lumi", "ferro", "shard", "pebble")
CAVE_FLY = ("hum", "umbra")
MEADOW_WALK = ("twinkle", "tuft", "kick", "dust")
MEADOW_FLY = ("meteor", "zap", "dream", "wish")

WALKERS.update(
    geode=dict(species="Geodling", body=(126, 116, 150), color=(200, 140, 255), speed=6),
    drip=dict(species="Dripling", body=(120, 190, 240), color=(170, 230, 255), speed=8),
    lumi=dict(species="Lumicrawl", body=(110, 96, 130), color=(140, 255, 220), speed=9),
    ferro=dict(species="Ferrodig", body=(150, 156, 176), color=(255, 180, 110), speed=10),
    shard=dict(species="Shardling", body=(170, 210, 240), color=(150, 220, 255), speed=14),
    pebble=dict(species="Pebblefist", body=(160, 146, 160), color=(255, 160, 120), speed=12),
    twinkle=dict(species="Twinklet", body=(255, 240, 200), color=(255, 236, 140), speed=16),
    tuft=dict(species="Tufflet", body=(150, 210, 140), color=(220, 255, 170), speed=10),
    kick=dict(species="Kickbud", body=(120, 190, 120), color=(255, 150, 190), speed=18),
    dust=dict(species="Dustlet", body=(214, 196, 176), color=(255, 230, 190), speed=20),
)
FLIERS.update(
    hum=dict(species="Humlet", body=(200, 210, 236), color=(170, 160, 255), speed=14, turn=3.0),
    umbra=dict(species="Umbrit", body=(40, 30, 64), color=(200, 120, 255), speed=40, turn=1.4),
    meteor=dict(species="Meteorlet", body=(150, 110, 110), color=(255, 160, 80), speed=90, turn=1.1),
    zap=dict(species="Zaplet", body=(250, 236, 140), color=(255, 250, 150), speed=110, turn=0.6),
    dream=dict(species="Dreamote", body=(230, 200, 255), color=(220, 170, 255), speed=26, turn=2.2),
    wish=dict(species="Wishlet", body=(220, 236, 255), color=(255, 240, 180), speed=12, turn=3.6),
)
LIT.update(CAVE_WALK + CAVE_FLY + MEADOW_WALK + MEADOW_FLY)


def st_of(o):
    return getattr(o, "stage", 1)


def shaded(s, color, rect, ellipse=True):
    dark = mix(color, INK, 0.35)
    fn = pygame.draw.ellipse if ellipse else pygame.draw.rect
    fn(s, dark, pygame.Rect(rect).move(0, 1))
    fn(s, color, rect)


def legs(self, s, xs, top, n_lift=1.5):
    z, y = self.size, self.y
    moving = self.wait <= 0
    for i, lx in enumerate(xs):
        lift = max(0.0, math.sin(self.step + i * math.pi)) * n_lift * z if moving else 0
        pygame.draw.line(s, mix(self.body, INK, 0.4), (lx, y - top * z), (lx, y - lift), max(1, round(z)))


# --- the Crystal Caverns -------------------------------------------------------------------

def draw_geode(self, s, t):
    """Geodling: a round grey stone that waddles; a crack shows amethyst inside. Geodcrest: split
    open along the top, a crest of crystals. Geodsage: a cloak of stone, crystals all round its open
    crown, a crystal eye on its brow."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    legs(self, s, (x - 3 * z, x + 3 * z), 3)
    shaded(s, self.body, (x - 7 * z, y - 13 * z, 14 * z, 11 * z))
    pygame.draw.ellipse(s, mix(self.body, WHITE, 0.2), (x - 4 * z, y - 12 * z, 6 * z, 3 * z))
    if st == 1:
        pygame.draw.lines(s, (90, 60, 120), False, [(x - 3 * z, y - 12 * z), (x - z, y - 9 * z), (x + 2 * z, y - 11 * z)])
    else:
        n = 3 if st == 2 else 6
        for j in range(n):
            cx = x + (j - (n - 1) / 2) * 2.2 * z
            h = (4 + (j % 2) * 2 + (st - 2) * 2) * z
            pygame.draw.polygon(s, (170, 110, 230), [(cx - 1.4 * z, y - 11 * z), (cx + 1.4 * z, y - 11 * z), (cx, y - 11 * z - h)])
            pygame.draw.line(s, (230, 200, 255), (cx, y - 11 * z), (cx - 0.5 * z, y - 11 * z - h * 0.7))
    if st > 2:
        cloak = [(x - 8 * z, y - 9 * z), (x + 8 * z, y - 9 * z), (x + 9 * z, y - 2 * z), (x - 9 * z, y - 2 * z)]
        pygame.draw.polygon(s, mix(self.body, INK, 0.25), cloak)
    self.eyes(s, x + f * z - 1.5 * z, y - 7 * z, 3 * z)


def glow_geode(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    b = 0.6 + 0.4 * math.sin(t * 1.5 + self.phase)
    glow(s, x, y - (10 if st == 1 else 14) * z, int((5 + 3 * st) * z), self.color, q(30 + 30 * st * b + 60 * k))
    if st > 2:
        ex, ey = x + self.facing * z, y - 10 * z
        pygame.draw.polygon(s, (220, 190, 255), [(ex, ey - 1.5 * z), (ex + z, ey), (ex, ey + 1.5 * z), (ex - z, ey)])


def draw_drip(self, s, t):
    """Dripling: a drop of cave water wearing a little stalactite as a hat. Dripspire: taller, a
    stalagmite growing up its back. Stalagdeep: a pillar of flowstone, two stalagmites."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    wob = math.sin(t * 3 + self.phase) * 0.6 * z
    w, h = 6 + st * 1.5, 8 + st * 3
    body = [(x - w * z - wob, y - z), (x + w * z + wob, y - z), (x + w * 0.4 * z, y - h * 0.7 * z), (x, y - h * z),
            (x - w * 0.4 * z, y - h * 0.7 * z)]
    pygame.draw.polygon(s, mix(self.body, INK, 0.3), [(a, b + 1) for a, b in body])
    pygame.draw.polygon(s, self.body, body)
    pygame.draw.ellipse(s, mix(self.body, INK, 0.2), (x - w * z, y - 3 * z, 2 * w * z, 3 * z))
    pygame.draw.line(s, WHITE, (x - w * 0.4 * z, y - h * 0.5 * z), (x - w * 0.2 * z, y - h * 0.7 * z))
    stone = (150, 140, 170)
    pygame.draw.polygon(s, stone, [(x - 3 * z, y - h * z + z), (x + 3 * z, y - h * z + z), (x, y - h * z - (5 + st) * z)])
    if st > 1:
        for j, (ox, hh) in enumerate(((-4, 8), (-6.5, 5))[:st - 1]):
            bx = x + f * ox * z
            pygame.draw.polygon(s, mix(stone, WHITE, 0.1 * j), [(bx - 2 * z, y - 2 * z), (bx + 2 * z, y - 2 * z), (bx, y - (hh + st * 2) * z)])
    self.eyes(s, x + f * z - 1.5 * z, y - 4 * z - st * z, 3 * z)


def glow_drip(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    kk = (t * 0.6 + self.phase) % 1.0  # a drop falls from its hat now and then
    h = 8 + st * 3
    if kk < 0.5:
        s.set_at((round(x), round(y - (h + 3 + st) * z + kk * 10 * z)), self.color)
    glow(s, x, y - h * 0.5 * z, int((6 + 2 * st) * z), self.color, q(40 + 60 * k))


def draw_lumi(self, s, t):
    """Lumicrawl: a stubby cave bug carrying a glowing crystal on its back. Lumitrek: longer, three
    crystals. Lumicaravan: a long shelled thing with a whole lit outcrop riding on it."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    segs = 2 + st
    moving = self.wait <= 0
    for i in range(segs):
        sx = x - f * i * 5 * z
        for side in (-1, 1):
            w = math.sin(self.step * 1.5 + i + side) * 1.2 * z if moving else 0
            pygame.draw.line(s, mix(self.body, INK, 0.4), (sx, y - 3 * z), (sx + w + side * z, y), 1)
        shaded(s, self.body, (sx - 3.5 * z, y - 8 * z, 7 * z, 6 * z))
        pygame.draw.line(s, mix(self.body, WHITE, 0.2), (sx - 2 * z, y - 7.5 * z), (sx + 1.5 * z, y - 7.5 * z))
    for i in range(1 if st == 1 else 3 if st == 2 else segs):
        cx = x - f * (i + (0.5 if st > 1 else 0.8)) * 5 * z
        h = (5 + (i % 2) * 2 + (st - 1)) * z
        pygame.draw.polygon(s, mix(self.color, INK, 0.2), [(cx - 1.8 * z, y - 8 * z), (cx + 1.8 * z, y - 8 * z), (cx, y - 8 * z - h)])
    self.eyes(s, x + f * 2 * z, y - 6 * z, 0.1)


def glow_lumi(self, s, t, st, k):
    z, x, y, f = self.size, self.x, self.y, self.facing
    for i in range(1 if st == 1 else 3 if st == 2 else 2 + st):
        cx = x - f * (i + (0.5 if st > 1 else 0.8)) * 5 * z
        b = 0.5 + 0.5 * math.sin(t * 1.4 + i + self.phase)
        glow(s, cx, y - 11 * z, int(6 * z), self.color, q(50 + 60 * b + 40 * k))
        s.set_at((round(cx), round(y - 11 * z)), mix(self.color, WHITE, 0.6))


def draw_ferro(self, s, t):
    """Ferrodig: a stout iron-grey digger with a spade of a nose. Ferrodrill: the nose has become a
    spiralled drill. Ferrocore: armoured in plates, a glowing molten core in its chest."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    legs(self, s, (x - 4 * z, x - 1 * z, x + 2 * z, x + 5 * z), 3)
    shaded(s, self.body, (x - 7 * z, y - 11 * z, 14 * z, 9 * z))
    nx = x + f * 7 * z
    if st == 1:
        pygame.draw.polygon(s, (200, 200, 214), [(nx - f * z, y - 9 * z), (nx + f * 4 * z, y - 7 * z), (nx - f * z, y - 4 * z)])
    else:
        ln = (6 + st * 1.5) * z
        pygame.draw.polygon(s, (210, 210, 224), [(nx - f * z, y - 10 * z), (nx + f * ln, y - 7 * z), (nx - f * z, y - 4 * z)])
        turn = (t * 8) % 1.0
        for j in range(4):  # the spiral, turning
            fx = nx + f * (j + turn) * ln / 4.5
            pygame.draw.line(s, (120, 120, 140), (fx, y - 9.5 * z + j * 0.6 * z), (fx + f * z, y - 4.5 * z - j * 0.5 * z))
    if st > 2:
        for j in range(-2, 3):
            px = x + j * 3 * z
            pygame.draw.polygon(s, mix(self.body, WHITE, 0.15), [(px - 2 * z, y - 10 * z), (px + 2 * z, y - 10 * z), (px, y - 14 * z)])
    self.eyes(s, x + f * 3 * z, y - 8.5 * z, 0.1)


def glow_ferro(self, s, t, st, k):
    if st < 3 and k <= 0:
        return
    z, x, y = self.size, self.x, self.y
    b = 0.7 + 0.3 * math.sin(t * 2.5 + self.phase)
    glow(s, x, y - 6 * z, int(7 * z), self.color, q(90 * b + 60 * k))
    pygame.draw.circle(s, mix(self.color, WHITE, 0.4), (round(x), round(y - 6 * z)), max(1, round(1.6 * z)))


def draw_shard(self, s, t):
    """Shardling: a small pale dragon, crystal ridges down its back. Shardfang: horned, little
    crystal wings. Shardsovereign: a tall crystal dragon with great faceted wings."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    legs(self, s, (x - 4 * z, x + 3 * z), 4, 2)
    dark = mix(self.body, INK, 0.35)
    tail = [(x - f * (6 + i * 3) * z, y - 5 * z + i * 0.8 * z + math.sin(t * 2 + i) * 0.5 * z) for i in range(2 + st)]
    for i, (px, py) in enumerate(tail):
        pygame.draw.circle(s, dark if i % 2 else self.body, (round(px), round(py)), max(1, round((3 - i * 0.5) * z)))
    if st > 1:  # faceted wings
        span = (8 if st == 2 else 13) * z
        flap = math.sin(t * 2 + self.phase) * 2 * z
        wing = [(x - f * 2 * z, y - 10 * z), (x - f * span * 0.6, y - 10 * z - span * 0.8 - flap), (x - f * span, y - 9 * z - flap),
                (x - f * span * 0.4, y - 7 * z)]
        pygame.draw.polygon(s, mix(self.color, WHITE, 0.35), wing)
        pygame.draw.lines(s, self.color, True, wing)
    shaded(s, self.body, (x - 6 * z, y - 11 * z, 12 * z, 8 * z))
    hx, hy = x + f * 6 * z, y - 12 * z
    shaded(s, self.body, (hx - 3.5 * z, hy - 3 * z, 7 * z, 5.5 * z))
    for j in range(3 + st):  # crystal ridges down its back
        cx = x - f * (j * 2.2 - 3) * z
        h = (2.5 + (j == 1) * 1.5 + (st - 1)) * z
        pygame.draw.polygon(s, (190, 230, 255), [(cx - z, y - 10.5 * z), (cx + z, y - 10.5 * z), (cx, y - 10.5 * z - h)])
    if st > 1:
        for side in (-1, 1):
            pygame.draw.line(s, (230, 245, 255), (hx - f * z + side * z, hy - 2.5 * z), (hx - f * 3 * z + side * z, hy - (6 + st) * z))
    ex, ey = round(hx + f * 1.5 * z), round(hy - z)
    pygame.draw.rect(s, (150, 220, 255), (ex - 1, ey - 1, 2, 2))
    s.set_at((ex, ey), INK)


def glow_shard(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    b = 0.5 + 0.5 * math.sin(t * 1.8 + self.phase)
    glow(s, x, y - 13 * z, int((5 + 3 * st) * z), self.color, q(30 + 20 * st * b + 60 * k))
    if k > 0:  # poked: a puff of frost breath
        glow(s, x + self.facing * 9 * z, y - 12 * z, int(8 * z), WHITE, q(120 * k))


def draw_pebble(self, s, t):
    """Pebblefist: a little stone fellow with big round fists. Cobblefist: broad shoulders, fists of
    cobbles. Quarryfist: a hulking stone brawler, a mossy brow and fists like boulders."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    legs(self, s, (x - 2.5 * z, x + 2.5 * z), 4, 2)
    w = 5 + st
    shaded(s, self.body, (x - w * z, y - 13 * z, 2 * w * z, 10 * z), ellipse=False)
    pygame.draw.line(s, mix(self.body, WHITE, 0.25), (x - w * z + 1, y - 13 * z), (x + w * z - 1, y - 13 * z))
    for j in range(2):
        pygame.draw.line(s, mix(self.body, INK, 0.25), (x - w * z + 2 * z, y - (10 - j * 3) * z), (x + w * z - 2 * z, y - (9 - j * 3) * z))
    jab = max(0.0, math.sin(t * 2 + self.phase)) ** 8 * 3 * z
    r = (2.4 + st * 0.8) * z
    for side, reach in ((-1, 0), (1, jab)):
        fx = x + f * ((w + 2) * z + reach) if side > 0 else x - f * (w + 1.5) * z
        pygame.draw.circle(s, mix(self.body, INK, 0.3), (round(fx), round(y - 8 * z + 1)), round(r))
        pygame.draw.circle(s, mix(self.body, WHITE, 0.1), (round(fx), round(y - 8 * z)), round(r))
    if st > 2:
        pygame.draw.line(s, (100, 200, 150), (x - w * z, y - 13.5 * z), (x + w * z, y - 13.5 * z), max(2, round(1.5 * z)))
    self.eyes(s, x + f * 1.5 * z - 1.5 * z, y - 10.5 * z, 3 * z)


def glow_pebble(self, s, t, st, k):
    if k > 0:
        z = self.size
        glow(s, self.x + self.facing * (7 + st) * z, self.y - 8 * z, int(9 * z), self.color, q(110 * k))


def draw_hum(self, s, t):
    """Humlet: a floating crystal tuning fork, humming. Humchime: three prongs and two chimes.
    Resonarch: a tall cathedral of chime-crystals, rings of sound pulsing out of it."""
    z, x, y, st = self.size, self.x, self.y, st_of(self)
    shake = math.sin(t * 40) * 0.4 * z
    prongs = (-1, 1) if st == 1 else (-1, 0, 1) if st == 2 else (-2, -1, 0, 1, 2)
    for j in prongs:
        h = (9 + (2 - abs(j)) * 2 + st) * z
        px = x + j * 2.6 * z + shake * (1 if j % 2 else -1)
        pygame.draw.line(s, mix(self.body, INK, 0.2), (px, y - 2 * z), (px, y - h), max(2, round(1.4 * z)))
        pygame.draw.line(s, WHITE, (px - 0.5 * z, y - 3 * z), (px - 0.5 * z, y - h + z))
    pygame.draw.ellipse(s, self.body, (x - (3 + st) * z, y - 3 * z, (6 + 2 * st) * z, 5 * z))
    pygame.draw.line(s, mix(self.body, INK, 0.3), (x, y + 2 * z), (x, y + (5 + st) * z), max(1, round(z)))
    if st > 1:
        for j in (-1, 1):
            pygame.draw.circle(s, mix(self.color, WHITE, 0.4), (round(x + j * (6 + st) * z), round(y + 2 * z)), max(1, round(1.5 * z)))
    s.set_at((round(x - z), round(y - 0.5 * z)), INK)
    s.set_at((round(x + z), round(y - 0.5 * z)), INK)


def glow_hum(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    glow(s, x, y - 6 * z, int((8 + 3 * st) * z), self.color, q(40 + 60 * k))
    for j in range(st):  # rings of sound
        kk = (t * 0.8 + j / st + self.phase) % 1.0
        r = round((4 + kk * (8 + 5 * st)) * z)
        if r > 1:
            pygame.draw.circle(s, mix(self.color, (30, 20, 60), kk), (round(x), round(y - 6 * z)), r, 1)


def draw_umbra(self, s, t):
    """Umbrit: a scrap of the cave's shadow with two eyes. Umbrage: ragged, with clawed wisps.
    Umbravast: a great sweeping shadow, four eyes, a grin of stars."""
    z, x, y, st = self.size, self.x, self.y, st_of(self)
    n = 7 + 3 * st
    r0 = (5 + 2.5 * st) * z
    pts = []
    for i in range(n):
        a = i / n * math.tau
        r = r0 * (1 + 0.25 * math.sin(t * 3 + i * 1.7 + self.phase)) * (1.5 if 0.15 * math.pi < a < 0.85 * math.pi and i % 2 else 1)
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.75))
    pygame.draw.polygon(s, self.body, pts)
    pygame.draw.polygon(s, mix(self.body, self.color, 0.3), pts, 1)
    if st > 1:
        for side in (-1, 1):  # clawed wisps
            ax = x + side * r0
            pygame.draw.lines(s, self.body, False, [(ax, y), (ax + side * 4 * z, y + 3 * z + math.sin(t * 2 + side) * z),
                                                    (ax + side * 6 * z, y + 2 * z)], max(1, round(z)))


def glow_umbra(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    eyes = [(-2, -1), (2, -1)] + ([(-5, 1), (5, 1)] if st > 2 else [])
    for i, (ex, ey) in enumerate(eyes):
        if (t * 0.7 + i * 0.3 + self.phase) % 5 >= 0.15:
            pygame.draw.circle(s, self.color, (round(x + ex * z), round(y + ey * z)), max(1, round(1.1 * z)))
            s.set_at((round(x + ex * z), round(y + ey * z)), WHITE)
    if st > 2:  # a grin of stars
        for j in range(-3, 4):
            s.set_at((round(x + j * 1.4 * z), round(y + (3 - abs(j) * 0.3) * z)), (255, 240, 200))
    glow(s, x, y, int((6 + 3 * st) * z), self.color, q(30 + 60 * k))


# --- the Starfall Meadow -------------------------------------------------------------------

def draw_twinkle(self, s, t):
    """Twinklet: a little five-pointed star bouncing along. Twinkstride: up on legs, a ring of light
    round it. Celestide: a tall star-being robed in night sky, a constellation on its robe."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    moving = self.wait <= 0
    hop = abs(math.sin(self.step * 1.2)) * 3 * z if moving else abs(math.sin(t * 2 + self.phase)) * 0.8 * z
    if st == 1:
        cy = y - 6 * z - hop
    else:
        cy = y - (9 + 4 * (st - 2)) * z - hop * 0.4
        legs(self, s, (x - 2 * z, x + 2 * z), (y - cy - 3 * z) / z, 1.5)
    if st > 2:  # a robe of night sky
        pygame.draw.polygon(s, (50, 50, 110), [(x - 3 * z, cy), (x + 3 * z, cy), (x + 6 * z, y - z), (x - 6 * z, y - z)])
        for px, py in ((-2, 4), (1, 7), (3, 9), (-3, 10)):
            s.set_at((round(x + px * z), round(cy + py * z)), (255, 250, 220))
    r1, r2 = (6 + (st - 1) * 1.5) * z, (2.6 + (st - 1) * 0.6) * z
    rot = math.sin(t * 1.5 + self.phase) * 0.15
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5 + rot
        r = r1 if i % 2 == 0 else r2
        pts.append((x + math.cos(a) * r, cy + math.sin(a) * r))
    pygame.draw.polygon(s, mix(self.body, INK, 0.3), [(a, b + 1) for a, b in pts])
    pygame.draw.polygon(s, self.body, pts)
    self.eyes(s, x - 1.5 * z + f * 0.5 * z, cy, 3 * z)
    self._star = (x, cy)


def glow_twinkle(self, s, t, st, k):
    z = self.size
    x, cy = getattr(self, "_star", (self.x, self.y - 6 * z))
    b = 0.6 + 0.4 * math.sin(t * 2.5 + self.phase)
    glow(s, x, cy, int((8 + 3 * st) * z), self.color, q(50 + 40 * b + 60 * k))
    if st > 1:
        pygame.draw.ellipse(s, mix(self.color, WHITE, 0.5), (x - 9 * z, cy - 1.5 * z, 18 * z, 3 * z), 1)


def draw_tuft(self, s, t):
    """Tufflet: a round tuft of meadow grass on four little feet. Tuftrot: a shaggy grazer with
    flowers in its coat. Meadowmane: a tall, gentle beast with a mane of long grass and wildflowers."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    legs(self, s, (x - 4 * z, x - 1.5 * z, x + 1.5 * z, x + 4 * z), 3 + (st - 1) * 2, 1.2)
    by = y - (3 + (st - 1) * 2) * z
    w = 7 + st
    shaded(s, mix(self.body, (110, 90, 80), 0.3), (x - w * z, by - 8 * z, 2 * w * z, 9 * z))
    n = 10 + 6 * st
    for i in range(n):  # blades of grass all over it
        gx = x - w * z + (i + 0.5) * 2 * w * z / n
        sway = math.sin(t * 1.8 + i * 0.7 + self.phase) * 1.2 * z
        h = (3 + (i * 7) % 4 + st) * z
        pygame.draw.line(s, self.body if i % 2 else mix(self.body, WHITE, 0.2), (gx, by - 4 * z), (gx + sway, by - 4 * z - h))
    if st > 1:
        for i, fx in enumerate((-4, 0, 3, 6)[:2 + st]):
            c = ((255, 200, 230), (255, 236, 140), (200, 170, 255), (255, 255, 255))[i % 4]
            pygame.draw.circle(s, c, (round(x + fx * z), round(by - 7 * z)), max(1, round(1.2 * z)))
    hx, hy = x + f * (w + 1) * z, by - 3 * z
    shaded(s, (150, 120, 110), (hx - 3 * z, hy - 3 * z, 6 * z, 5 * z))
    self.eyes(s, hx - 1.5 * z + f * z, hy - 1.5 * z, 2 * z)


def glow_tuft(self, s, t, st, k):
    if st > 2 or k > 0:
        z = self.size
        glow(s, self.x, self.y - 14 * z, int(9 * z), self.color, q(40 + 70 * k))


def draw_kick(self, s, t):
    """Kickbud: a sprout up on two springy legs, a bud for a head, kicking now and then. Kickbloom:
    the bud open into a flower. Kickgrove: a lean bark-armoured tree-fighter with a canopy crown."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    kick = max(0.0, math.sin(t * 1.5 + self.phase)) ** 10
    hip = y - (6 + 2 * st) * z
    stem = mix(self.body, INK, 0.2) if st < 3 else (150, 104, 120)
    pygame.draw.line(s, stem, (x - z, hip), (x - 2 * z, y), max(1, round(z * 1.2)))
    pygame.draw.line(s, stem, (x + z, hip), (x + f * (2 + 8 * kick) * z, y - kick * 6 * z), max(1, round(z * 1.2)))
    top = hip - (6 + 2 * st) * z
    pygame.draw.line(s, stem, (x, hip), (x, top), max(2, round(z * (1.5 + st * 0.4))))
    for side in (-1, 1):  # leaf arms
        pygame.draw.ellipse(s, self.body, (x + side * 3 * z - 2 * z, top + 3 * z - side * f * z, 4 * z, 2.4 * z))
    if st == 1:
        shaded(s, self.body, (x - 3 * z, top - 5 * z, 6 * z, 6 * z))
        pygame.draw.polygon(s, self.color, [(x - 1.5 * z, top - 4 * z), (x + 1.5 * z, top - 4 * z), (x, top - 7 * z)])
        self.eyes(s, x - 1.5 * z + f * 0.5 * z, top - 2 * z, 3 * z)
    elif st == 2:
        for j in range(5):
            a = j / 5 * math.tau + t * 0.3
            pygame.draw.circle(s, self.color, (round(x + math.cos(a) * 3 * z), round(top - 3 * z + math.sin(a) * 3 * z)), max(1, round(2 * z)))
        pygame.draw.circle(s, (255, 236, 140), (round(x), round(top - 3 * z)), max(1, round(1.6 * z)))
    else:
        for j in range(7):
            a = math.pi + j / 6 * math.pi
            pygame.draw.circle(s, (90, 170, 120) if j % 2 else (120, 200, 140), (round(x + math.cos(a) * 6 * z), round(top - 3 * z + math.sin(a) * 4 * z)), max(2, round(3 * z)))
        pygame.draw.circle(s, (130, 210, 150), (round(x), round(top - 6 * z)), max(2, round(3.5 * z)))
        for j in range(3):
            pygame.draw.circle(s, self.color, (round(x + (j - 1) * 4 * z), round(top - (4 + j % 2 * 3) * z)), max(1, round(z)))
        self.eyes(s, x - 1.5 * z + f * 0.5 * z, top + 1.5 * z, 3 * z)


def glow_kick(self, s, t, st, k):
    kick = max(0.0, math.sin(t * 1.5 + self.phase)) ** 10
    if kick > 0.4 or k > 0:
        z = self.size
        glow(s, self.x + self.facing * 10 * z, self.y - 5 * z, int(7 * z), self.color, q(90 * max(kick, k)))


def draw_dust(self, s, t):
    """Dustlet: a fluffy puff of dust that rolls along the path. Dustwhirl: a little dust devil,
    spinning. Dustcyclone: a tall whirlwind of dust and leaves, lit from inside."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    if st == 1:
        for j in range(6):
            a = j / 6 * math.tau + self.x * 0.2 * -f
            pygame.draw.circle(s, mix(self.body, WHITE, 0.15 * (j % 2)), (round(x + math.cos(a) * 3 * z), round(y - 5 * z + math.sin(a) * 3 * z)), max(2, round(3 * z)))
        self.eyes(s, x - 1.5 * z + f * z, y - 5.5 * z, 3 * z)
        return
    h = (14 if st == 2 else 24) * z
    n = int(h / z / 2)
    for i in range(n):
        g = i / n
        r = (2 + g * (6 if st == 2 else 10)) * z
        cy = y - g * h
        pygame.draw.ellipse(s, mix(self.body, INK, 0.25 * (1 - g)), (x - r + math.sin(t * 2 + g * 3) * 2 * z, cy - z, 2 * r, 2 * z))
        s.set_at((round(x + math.cos(t * 6 + i * 0.7) * r), round(cy)), mix(self.body, WHITE, 0.4))
    if st > 2:
        for j in range(4):  # leaves caught in it
            a = t * 4 + j * 1.6
            pygame.draw.ellipse(s, (130, 200, 120), (x + math.cos(a) * 8 * z, y - (0.3 + j * 0.17) * h, 2.4 * z, 1.4 * z))
    self.eyes(s, x + math.cos(t * 3) * 2 * z - 1.5 * z, y - h * 0.65, 3 * z)


def glow_dust(self, s, t, st, k):
    if st > 2:
        z = self.size
        glow(s, self.x, self.y - 12 * z, int(10 * z), self.color, q(40 + 60 * k))


def draw_meteor(self, s, t):
    """Meteorlet: a pebble of fallen star with a tail of sparks. Meteorblaze: wrapped in flame.
    Starforge: a great molten rock with a dark band like an anvil's, and a fiery mane."""
    z, x, y, st = self.size, self.x, self.y, st_of(self)
    r = (3 + st * 1.6) * z
    pts = [(x + math.cos(a / 7 * math.tau) * r * (0.85 + 0.15 * ((a * 3) % 2)), y + math.sin(a / 7 * math.tau) * r) for a in range(7)]
    pygame.draw.polygon(s, mix(self.body, INK, 0.3), [(a, b + 1) for a, b in pts])
    pygame.draw.polygon(s, self.body, pts)
    for j in range(2 + st):  # glowing cracks
        a = j * 2.1 + self.phase
        pygame.draw.line(s, (255, 190, 110), (x, y), (x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8))
    if st > 2:
        pygame.draw.rect(s, mix(self.body, INK, 0.4), (x - r * 0.5, y - r * 0.15, r, r * 0.35))
    s.set_at((round(x - z), round(y - z)), INK)
    s.set_at((round(x + z), round(y - z)), INK)


def glow_meteor(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    for i, (px, py) in enumerate(self.trail[1:]):  # its tail of fire
        rr = round((st * 1.4 - i * 0.25) * z)
        if rr >= 1:
            pygame.draw.circle(s, mix((255, 236, 160), (200, 60, 60), i / 8), (round(px), round(py)), rr)
    glow(s, x, y, int((7 + 4 * st) * z), self.color, q(70 + 20 * st + 60 * k))
    if st > 1:  # flames round it
        r = (3 + st * 1.6) * z
        for j in range(6 + 2 * st):
            a = j / (6 + 2 * st) * math.tau + t * 2
            fl = (2 + abs(math.sin(t * 7 + j)) * 2) * z
            pygame.draw.line(s, (255, 170, 90), (x + math.cos(a) * r, y + math.sin(a) * r),
                             (x + math.cos(a) * (r + fl), y + math.sin(a) * (r + fl) - fl * 0.5))


def draw_zap(self, s, t):
    """Zaplet: a little yellow streak of a bird. Zapstreak: zig-zag tail feathers. Zaptempest: a
    storm-bird with pale cloud wings, lightning beneath it."""
    z, x, y, f, st = self.size, self.x, self.y, self.facing, st_of(self)
    flap = math.sin(t * 20 + self.phase)
    span = (5 + 3 * st) * z
    for side in (1, -1):
        wing = [(x, y - z), (x - f * 2 * z, y - span * (0.6 + 0.4 * flap) * (1 if side > 0 else 0.6)), (x - f * span * 0.6, y)]
        pygame.draw.polygon(s, (230, 230, 250) if st > 2 else mix(self.body, WHITE, 0.3 if side > 0 else 0.0), wing)
    pygame.draw.ellipse(s, self.body, (x - 3 * z, y - 2 * z, 6 * z, 4 * z))
    pygame.draw.polygon(s, (255, 170, 80), [(x + f * 3 * z, y - z), (x + f * 5.5 * z, y), (x + f * 3 * z, y + z)])
    s.set_at((round(x + f * 1.5 * z), round(y - z)), INK)
    if st > 1:
        for j in range(st):  # zig-zag tail feathers
            tx = x - f * 3 * z
            pygame.draw.lines(s, self.body, False, [(tx, y), (tx - f * 3 * z, y - (1 + j) * z), (tx - f * 5 * z, y + (1 + j) * z),
                                                    (tx - f * (8 + j * 2) * z, y - j * z)])


def glow_zap(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    glow(s, x, y, int((5 + 3 * st) * z), self.color, q(60 + 70 * k))
    if st > 2 and (math.sin(t * 6 + self.phase) > 0.6 or k > 0):
        px, py = x, y + 2 * z
        for j in range(4):
            nx, ny = px + (2 if j % 2 else -2) * z, py + 4 * z
            pygame.draw.line(s, self.color, (px, py), (nx, ny))
            px, py = nx, ny


def draw_dream(self, s, t):
    """Dreamote: a fluffy pastel bug on gauzy wings, sleepy-eyed. Dreamwing: two pairs of wings
    patterned like a night sky. Dreamloom: a great soft weaver of dreams, trailing light."""
    z, x, y, st = self.size, self.x, self.y, st_of(self)
    open_ = 0.4 + 0.6 * abs(math.cos(t * 4 + self.phase))
    for p in range(1 if st == 1 else 2):
        w = (5 + 3 * st - p * 2) * z * open_
        h = (5 + 2 * st - p) * z
        for side in (-1, 1):
            rect = (x + (0 if side > 0 else -w), y - h + p * 3 * z, w, h)
            pygame.draw.ellipse(s, mix((200, 180, 255), (60, 50, 120), 0.2 + 0.3 * p) if st > 1 else (240, 220, 255), rect)
            pygame.draw.ellipse(s, WHITE, rect, 1)
            if st > 1:
                s.set_at((round(x + side * w * 0.5), round(y - h * 0.5 + p * 3 * z)), (255, 250, 200))
    pygame.draw.circle(s, self.body, (round(x), round(y)), max(2, round((2.2 + st * 0.6) * z)))
    for side in (-1, 1):  # sleepy eyes
        pygame.draw.line(s, INK, (x + side * z - 0.5 * z, y - 0.5 * z), (x + side * z + 0.5 * z, y - 0.5 * z))


def glow_dream(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    glow(s, x, y, int((6 + 3 * st) * z), self.color, q(40 + 60 * k))
    if st > 2:
        for i, (px, py) in enumerate(self.trail[1::2]):
            s.set_at((round(px), round(py + 3 * z)), mix(PRISM[(i + int(t * 2)) % len(PRISM)], (40, 30, 80), i / 5))
    for j in range(st):  # little "z"s floating up: it is always half asleep
        kk = (t * 0.3 + j / st + self.phase) % 1.0
        zx, zy = x + 4 * z + kk * 5 * z, y - 5 * z - kk * 9 * z
        pygame.draw.lines(s, mix(WHITE, (40, 30, 80), kk), False, [(zx, zy), (zx + 2, zy), (zx, zy + 2), (zx + 2, zy + 2)])


def draw_wish(self, s, t):
    """Wishlet: a tiny paper-lantern spirit with a flame for a heart. Wishlantern: taller, a ribbon
    of written wishes trailing. Wishhaven: a little roofed shrine of a lantern, lanterns circling."""
    z, x, y, st = self.size, self.x, self.y, st_of(self)
    w, h = (5 + 1.5 * st) * z, (7 + 3 * st) * z
    paper = (255, 230, 200) if st < 3 else (240, 220, 255)
    body = pygame.Rect(0, 0, round(w * 2), round(h))
    body.center = (round(x), round(y))
    pygame.draw.ellipse(s, mix(paper, (200, 120, 90), 0.3), body.move(0, 1))
    pygame.draw.ellipse(s, paper, body)
    for j in range(1, 3 + st):  # ribs of the lantern
        yy = body.y + j * body.h / (3 + st)
        pygame.draw.line(s, mix(paper, (200, 120, 90), 0.4), (body.x + 2 * z, yy), (body.right - 2 * z, yy))
    pygame.draw.rect(s, (150, 90, 110), (x - w * 0.5, body.y - 1.5 * z, w, 1.5 * z))
    pygame.draw.rect(s, (150, 90, 110), (x - w * 0.5, body.bottom, w, 1.5 * z))
    if st > 1:  # a ribbon of wishes
        for i, (px, py) in enumerate(self.trail[1:]):
            s.set_at((round(px), round(py + h * 0.5 + i)), (255, 120, 140) if i % 3 else WHITE)
    if st > 2:  # a little roof
        pygame.draw.polygon(s, (150, 90, 110), [(x - w * 0.9, body.y - z), (x + w * 0.9, body.y - z), (x, body.y - 6 * z)])
    for side in (-1, 1):
        s.set_at((round(x + side * 1.5 * z), round(y - z)), INK)


def glow_wish(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    b = 0.7 + 0.3 * math.sin(t * 5 + self.phase) * math.sin(t * 3.1)
    glow(s, x, y, int((9 + 4 * st) * z), self.color, q(70 * b + 20 * st + 60 * k))
    pygame.draw.circle(s, (255, 236, 160), (round(x), round(y + 1.5 * z)), max(1, round(1.4 * z)))
    if st > 2:  # small lanterns circling it
        for j in range(3):
            a = t * 0.8 + j / 3 * math.tau
            lx, ly = x + math.cos(a) * 14 * z, y + math.sin(a) * 5 * z
            glow(s, lx, ly, int(4 * z), self.color, q(80))
            pygame.draw.circle(s, (255, 230, 200), (round(lx), round(ly)), max(1, round(1.4 * z)))


for _kind in CAVE_WALK + MEADOW_WALK:
    setattr(Walker, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(Walker, "glow_" + _kind, globals()["glow_" + _kind])
for _kind in CAVE_FLY + MEADOW_FLY:
    setattr(Flier, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(Flier, "glow_" + _kind, globals()["glow_" + _kind])
