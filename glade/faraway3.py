"""The far places, round two (2026-10-27, his picks): the Moon Dunes right of the Misty Bog, the
Lava Lake above the Hot Springs, and three off the Glow Shore: the Coral Grotto to its right,
the Kelp Deep below it (under the sea) and Lighthouse Point up on the headland.
"""

import math

import pygame

import art
from art import GLOW, H, W, glow, mix
from kit import blob_row, lit, make, tint
from life import Shafts, Steam
from pond import Shoal, Water

SAND = (230, 200, 190)
CACTUS = (140, 255, 200)
LAVA = (255, 140, 70)
CORAL = [(255, 140, 170), (255, 190, 120), (200, 150, 255), (120, 240, 220)]
DEEP = (90, 220, 230)
BEAM = (255, 240, 190)


# --- The Moon Dunes (right of the Misty Bog) ------------------------------------------------

def cactus(lay, sc, x, base, h, glows):
    """A tall cactus, ribbed, its arms raised, glowing at the tips."""
    c = sc.col("leaf", 0.35)
    pygame.draw.rect(lay, tint(c, -0.2), (x - 5, base - h, 10, h), border_radius=5)
    pygame.draw.rect(lay, c, (x - 5, base - h, 7, h), border_radius=5)
    for side, at, up in ((-1, 0.45, 0.25), (1, 0.6, 0.2)):
        ax, ay = x + side * 5, base - h * at
        pygame.draw.line(lay, c, (ax, ay), (ax + side * 10, ay), 6)
        pygame.draw.line(lay, c, (ax + side * 10, ay + 2), (ax + side * 10, ay - h * up), 6)
        glows.append(lit(sc, ax + side * 10, int(ay - h * up), 30, CACTUS, 60, core=2))
    glows.append(lit(sc, x, base - h, 40, CACTUS, 70, core=3))


def dunes_mid(sc, rng):
    glows = []
    for d, y0, amp, k in ((0.85, 330, 30, 0.3), (0.6, 370, 24, 0.15), (0.4, 410, 20, 0.05)):
        lay = art.plane()
        top = [(x, y0 + amp * math.sin(x / (120 + 40 * d) + d * 5) + 8 * math.sin(x / 37)) for x in range(0, W + 9, 8)]
        pygame.draw.polygon(lay, sc.col("leaf2", d), top + [(W, H), (0, H)])
        for x, y in top[::2]:  # the moonlit crest of each dune
            pygame.draw.line(lay, tint(sc.col("leaf2", d), 0.25 + k), (x, y), (x + 8, y), 2)
        sc.add(lay, d, veil=0.03, texture=0.3)
    lay = art.plane()
    for x, b, h in ((150, 420, 60), (330, 400, 40), (690, 410, 70), (850, 430, 50)):
        cactus(lay, sc, x, b, h, glows)
    art.rock(lay, rng, 560, 420, 40, 20, (220, 210, 220))  # an old pale stone, half buried
    sc.add(lay, 0.35, texture=0.4)
    return glows


def dunes_near(sc, lay, rng):
    pygame.draw.rect(lay, sc.col("leaf2", 0.2), (0, 452, W, H - 452))
    for _ in range(1600):
        x, y = rng.randrange(W), rng.randint(452, H - 1)
        lay.set_at((x, y), tint(sc.col("leaf2", 0.2), rng.uniform(-0.1, 0.2)))
    for y in range(470, H, 18):  # wind ripples
        pts = [(x, y + 3 * math.sin(x / 20 + y)) for x in range(0, W + 1, 10)]
        pygame.draw.lines(lay, tint(sc.col("leaf2", 0.2), 0.12), False, pts)


def build_dunes():
    return make("dunes", "The Moon Dunes", 86,
                dict(sky=[(10, 8, 34), (30, 20, 70), (70, 46, 110), (130, 90, 140)], mist=(150, 110, 150),
                     shade=(16, 10, 34), ambient=((255, 240, 236), (120, 96, 140)), leaf=(110, 190, 150),
                     leaf2=SAND, leaf3=(120, 90, 130), earth=(240, 214, 200), earth_edge=(170, 130, 150),
                     flowers=[(140, 255, 200), (255, 220, 160)]),
                exits=[("left", "Back to the Misty Bog", "bog")], gy=452, stars=300, star_floor=300,
                moon_at=(700, 90, 34), mid=dunes_mid, near=dunes_near, grassy=False, fly=CACTUS,
                squid=[CACTUS, GLOW["amber"]], motes=((255, 230, 200), -1), slug=((240, 200, 180), CACTUS),
                fliers=("zap", "meteor", "moth", "wish"), walkers=("gecko", "dust", "silt", "ash", "pebble"),
                out=("gecko", "zap", "dust"), far_grounds=[(408, (100, 440)), (372, (500, 900))],
                lower_props=("rocks",), lower=dict(bushes=False))


# --- The Lava Lake (above the Hot Springs) ------------------------------------------------------

def lava_mid(sc, rng):
    glows = []
    lay = art.plane()  # the crater's far wall
    art.crag(lay, [(0, 200), (200, 150), (420, 170), (600, 140), (800, 170), (W, 150), (W, 380), (0, 380)],
             sc.col("stone", 0.7), 87, side=1, strata=(8, 14))
    sc.add(lay, 0.7, veil=0.03)
    lay = art.plane()  # the lake itself: molten, crusted with dark plates that glow at the seams
    art.gradient(lay, (0, 330, W, 80), [(255, 210, 120), LAVA, (200, 70, 50)], steps=6)
    for _ in range(40):
        x, y, w = rng.randint(0, W), rng.randint(336, 400), rng.randint(20, 60)
        pygame.draw.ellipse(lay, (70, 36, 50), (x - w // 2, y - 3, w, 7))
    for x in range(0, W, 3):
        sc.emit.set_at((x, 330 + (x * 7) % 70), (160, 80, 30))
    sc.add(lay, 0.45, texture=0)
    for x in range(60, W, 120):
        glows.append(lit(sc, x, 370, 160, LAVA, 90))
    sc.live(Steam(rng, [(x, 340, 60) for x in range(100, W, 200)], n_each=4, color=(230, 170, 170), height=140))
    lay = art.plane()  # the near rim, black rock with heat in its cracks
    art.crag(lay, [(0, 400), (180, 420), (400, 410), (620, 424), (800, 404), (W, 412), (W, H), (0, H)],
             sc.col("stone", 0.25), 88, side=1, strata=(5, 9))
    for _ in range(12):
        cx, cy = rng.randint(20, W - 20), rng.randint(420, 450)
        for i in range(rng.randint(6, 12)):
            lay.set_at((cx, cy), (255, 170, 90))
            sc.emit.set_at((cx, cy), (150, 70, 30))
            cx += rng.choice((-1, 0, 1))
            cy += 1
    sc.add(lay, 0.25, texture=0.5)
    return glows


def build_lava():
    return make("lava", "The Lava Lake", 87,
                dict(sky=[(18, 6, 26), (44, 14, 40), (90, 30, 50), (150, 60, 60)], mist=(140, 60, 70),
                     shade=(20, 6, 20), ambient=((255, 220, 200), (130, 60, 70)), leaf=(130, 110, 110),
                     leaf2=(110, 80, 96), leaf3=(70, 40, 60), stone=(90, 70, 100), earth=(170, 120, 120),
                     earth_edge=(100, 60, 80), flowers=[(255, 170, 90), (255, 220, 140)], moon_side=1),
                exits=[("down", "Back to the Hot Springs", "springs")], gy=456, stars=120, star_floor=140,
                mid=lava_mid, fly=GLOW["amber"], squid=[LAVA, GLOW["amber"]], motes=(LAVA, -20),
                slug=((255, 180, 150), LAVA), fliers=("lava", "jelly", "moth", "meteor"),
                walkers=("gecko", "ash", "obsid", "sulf", "capy"), out=("gecko", "lava", "obsid"),
                far_grounds=[(416, (60, 400)), (418, (560, 900))], lower_props=("rocks", "vents"), lower=dict(bushes=False))


# --- The Coral Grotto (right of the Glow Shore) -----------------------------------------------

def coral(lay, rng, x, base, h, color, glows, sc):
    """A branching coral, each tip a bead of light."""
    def branch(px, py, a, ln, depth):
        nx, ny = px + math.cos(a) * ln, py + math.sin(a) * ln
        pygame.draw.line(lay, color, (px, py), (nx, ny), max(1, depth))
        if depth > 1:
            for da in (-0.5, 0.45):
                branch(nx, ny, a + da + rng.uniform(-0.2, 0.2), ln * 0.72, depth - 1)
        else:
            pygame.draw.circle(lay, tint(color, 0.5), (round(nx), round(ny)), 1)
    branch(x, base, -math.pi / 2, h * 0.4, 4)
    glows.append(lit(sc, x, base - h // 2, h + 30, color, 60))


def grotto_mid(sc, rng):
    glows = []
    lay = art.plane()  # inside the sea cave: the back wall, an opening onto the night sea
    rock = sc.col("stone", 0.6)
    art.crag(lay, [(0, 0), (W, 0), (W, H), (0, H)], rock, 89, strata=(7, 13))
    hole = [(560 + 130 + math.cos(i / 14 * math.tau) * (120 + 18 * math.sin(i * 2.3)),
             200 + math.sin(i / 14 * math.tau) * (100 + 14 * math.cos(i * 1.7))) for i in range(14)]
    pygame.draw.polygon(lay, (0, 0, 0, 0), hole)  # the cave mouth onto the night sea
    pygame.draw.polygon(lay, tint(rock, 0.2), hole, 2)
    for _ in range(30):
        x, ln = rng.randint(0, W), rng.randint(20, 70)
        pygame.draw.polygon(lay, tint(rock, -0.15), [(x - 8, 0), (x + 8, 0), (x, ln)])
    sc.add(lay, 0.6, veil=0.02)
    lay = art.plane()  # the pool, glowing from below
    water = mix(DEEP, (20, 40, 80), 0.5)
    pygame.draw.ellipse(lay, water, (160, 340, 640, 90))
    pygame.draw.ellipse(lay, mix(DEEP, (255, 255, 255), 0.2), (220, 356, 520, 58), 1)
    sc.add(lay, 0.4, texture=0)
    glows.append(lit(sc, 480, 386, 260, DEEP, 70))
    lay = art.plane()
    for x, b, h in ((120, 440, 60), (240, 430, 40), (380, 446, 34), (620, 440, 50), (760, 432, 64), (880, 446, 44)):
        coral(lay, rng, x, b, int(h * 1.6), rng.choice(CORAL), glows, sc)
    for x, y in ((300, 452), (700, 456), (520, 448)):  # anemones
        for j in range(9):
            a = math.pi + j * math.pi / 8
            pygame.draw.line(lay, (255, 170, 210), (x, y), (x + math.cos(a) * 8, y + math.sin(a) * 9))
        glows.append(lit(sc, x, y - 4, 40, (255, 170, 210), 60, core=2))
    sc.add(lay, 0.3, texture=0.3)
    return glows


def build_grotto():
    return make("grotto", "The Coral Grotto", 88,
                dict(sky=[(6, 12, 34), (12, 26, 66), (20, 40, 96), (36, 60, 120)], mist=(60, 90, 140),
                     shade=(6, 10, 30), ambient=((220, 240, 255), (60, 80, 130)), leaf=(110, 170, 160),
                     leaf2=(200, 190, 210), leaf3=(60, 90, 120), stone=(70, 80, 130), earth=(214, 200, 214),
                     earth_edge=(140, 120, 160), flowers=[(255, 150, 200), (120, 240, 220)]),
                exits=[("left", "Back to the Glow Shore", "shore")], gy=456, stars=60, star_floor=280,
                moon_at=(700, 170, 16), mid=grotto_mid, grassy=False, fly=DEEP, squid=[DEEP, CORAL[0]],
                motes=(DEEP, -3), slug=((255, 190, 210), DEEP), fliers=("bubbl", "foam", "jelly", "hum"),
                walkers=("glint", "murk", "ripple", "splash", "geode"), out=("glint", "bubbl", "splash"),
                pond=lambda sc, rng: Shoal(rng, [(Water(480, 386, 240, 24), 3)], DEEP, size=0.6),
                far_grounds=[(430, (40, 200)), (432, (760, 930))], lower_props=("rocks", "crystals"),
                lower=dict(bushes=False))


# --- The Kelp Deep (under the sea, below the Glow Shore) -----------------------------------------

def kelp_far(sc, rng):
    sc.live(Shafts([(300, 80, 200, 200, 0.0), (620, 60, 700, 180, 2.0), (480, 40, 440, 120, 4.0)], (120, 220, 230), alpha=30))
    lay = art.plane()
    blob_row(lay, rng, 360, 20, (30, 70), sc.col("leaf3", 0.8))  # far reef
    sc.add(lay, 0.8, veil=0.06)
    return []


def kelp_mid(sc, rng):
    glows = []
    for d, n, (h0, h1) in ((0.6, 14, (140, 260)), (0.35, 9, (220, 380))):
        lay = art.plane()
        for _ in range(n):
            x, base = rng.randint(0, W), 420 + int((0.6 - d) * 60)
            h = rng.randint(h0, h1)
            c = sc.col("leaf", d)
            pts = [(x + math.sin(i / 18 + x) * 6, base - i) for i in range(0, h, 4)]
            pygame.draw.lines(lay, c, False, pts, 3 if d > 0.5 else 4)
            for i, (px, py) in enumerate(pts[3::3]):  # blades, and a glowing float now and then
                side = 1 if i % 2 else -1
                pygame.draw.ellipse(lay, tint(c, 0.1), (px + (side > 0) * 2 - (side < 0) * 12, py - 3, 12, 6))
                if i % 5 == 2:
                    pygame.draw.circle(lay, DEEP, (round(px), round(py)), 2)
                    glows.append((round(px), round(py), 20, DEEP, 50, px * 0.1))
        sc.add(lay, d, veil=0.05)
    return glows


def kelp_near(sc, lay, rng):
    pygame.draw.rect(lay, sc.col("leaf2", 0.2), (0, 450, W, H - 450))  # the sandy floor
    for _ in range(1400):
        x, y = rng.randrange(W), rng.randint(450, H - 1)
        lay.set_at((x, y), tint(sc.col("leaf2", 0.2), rng.uniform(-0.15, 0.15)))
    for x, y in ((140, 500), (820, 490), (600, 520)):
        art.rock(lay, rng, x, y, 30, 18, sc.col("stone", 0.2), moss=sc.col("leaf", 0.15))
    return [(380, 480, 50, (255, 170, 210), 50, 0.0), (700, 470, 40, DEEP, 50, 2.0)]


def build_kelp():
    return make("kelp", "The Kelp Deep", 89,
                dict(sky=[(4, 20, 40), (8, 44, 70), (14, 70, 100), (24, 100, 120)], mist=(30, 110, 130),
                     shade=(4, 16, 30), ambient=((200, 240, 255), (40, 100, 130)), leaf=(70, 170, 120),
                     leaf2=(170, 180, 170), leaf3=(30, 80, 100), stone=(60, 90, 110), earth=(190, 200, 190),
                     earth_edge=(110, 130, 130), flowers=[(120, 240, 220)]),
                exits=[("up", "Back to the Glow Shore", "shore", 480)], gy=450, stars=0, far=kelp_far, mid=kelp_mid,
                near=kelp_near, grassy=False, fly=DEEP, squid=[DEEP, (255, 170, 210)], motes=((200, 255, 255), -12),
                slug=((200, 230, 220), DEEP), fliers=("jelly", "bubbl", "foam", "mire"),
                walkers=("murk", "glint", "ripple", "silt", "reed"), out=("jelly", "murk", "glint"),
                pond=lambda sc, rng: Shoal(rng, [(Water(480, 260, 300, 60), 4), (Water(200, 330, 120, 30), 2)], DEEP, size=0.8),
                far_grounds=[(420, (40, 400)), (424, (560, 920))], lower_props=("rocks",), lower=dict(bushes=False))


# --- Lighthouse Point (up on the headland above the Glow Shore) ------------------------------------

class Beam:
    """The lighthouse's light, sweeping slowly round: a pale wedge that swings out to one side,
    narrows as it turns toward you, and swings out to the other."""

    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.band = art.solid((W, 140))

    def light(self, lm, t):
        glow(lm, self.x, self.y, 120, self.color, 90)

    def shine(self, s, t):
        k = math.sin(t * 0.5)
        self.band.fill((0, 0, 0))
        reach = 700 * abs(k)
        end = self.x + reach * (1 if k > 0 else -1)
        spread = 10 + 50 * abs(k)
        cy = self.y - (self.y - 70)
        c = tuple(int(v * 0.18) for v in self.color)
        pygame.draw.polygon(self.band, c, [(self.x, cy), (end, cy - spread), (end, cy + spread)])
        s.blit(self.band, (0, self.y - 70), special_flags=pygame.BLEND_RGB_ADD)
        glow(s, self.x, self.y, 14, self.color, 200)


def lighthouse_mid(sc, rng):
    glows = []
    lay = art.plane()  # the sea far below, the moon's path on it
    sea = sc.col("water", 0.7)
    art.gradient(lay, (0, 300, W, 240), [tint(sea, 0.1), sea, tint(sea, -0.3)], steps=5)
    for i in range(30):
        y = 304 + int(i ** 1.5)
        pygame.draw.line(lay, mix(sea, (230, 236, 255), 0.4), (200 - 6 - i * 2, y), (200 + i, y))
    sc.add(lay, 0.7, texture=0.2)
    lay = art.plane()  # the headland, and the lighthouse on it
    art.crag(lay, [(260, 540), (330, 380), (420, 330), (W, 320), (W, 540)], sc.col("stone", 0.4), 90, side=1)
    pygame.draw.polygon(lay, sc.col("leaf", 0.4), [(330, 380), (420, 326), (W, 316), (W, 330), (420, 340)])
    x, base, top = 640, 336, 140
    for y in range(top, base):
        w = 18 + (y - top) * 0.06
        band = ((y - top) // 28) % 2
        c = (236, 226, 240) if band else (240, 160, 190)
        pygame.draw.line(lay, tint(c, -0.25), (x - w, y), (x + w, y))
        pygame.draw.line(lay, c, (x - w, y), (x + w * 0.4, y))
    pygame.draw.rect(lay, (60, 50, 70), (x - 20, top - 8, 40, 8))
    pygame.draw.rect(lay, (255, 236, 180), (x - 12, top - 30, 24, 22))
    pygame.draw.polygon(lay, (90, 70, 100), [(x - 18, top - 30), (x, top - 48), (x + 18, top - 30)])
    pygame.draw.rect(lay, (90, 70, 100), (x - 6, base - 22, 12, 22), border_radius=4)  # its door
    pygame.draw.rect(lay, (255, 210, 150), (x - 3, top + 60, 6, 10))
    glows.append(lit(sc, x, top + 64, 40, GLOW["amber"], 60))
    sc.add(lay, 0.4, texture=0.4)
    sc.live(Beam(x, top - 19, BEAM))
    glows.append(lit(sc, x, top - 19, 160, BEAM, 60))
    return glows


def build_lighthouse():
    return make("lighthouse", "Lighthouse Point", 90,
                dict(sky=[(6, 10, 32), (14, 22, 66), (30, 40, 100), (60, 66, 140)], mist=(80, 90, 150),
                     shade=(8, 10, 34), ambient=((236, 240, 255), (80, 90, 150)), leaf=(110, 180, 150),
                     leaf2=(140, 200, 160), leaf3=(60, 110, 130), water=(40, 80, 150), stone=(110, 110, 160),
                     flowers=[(255, 255, 255), (255, 200, 230), (200, 220, 255)], moon_side=1),
                exits=[("down", "Back to the Glow Shore", "shore")], gy=452, stars=260, star_floor=280,
                moon_at=(200, 70, 18), mid=lighthouse_mid, fly=BEAM, squid=[BEAM, GLOW["cyan"]],
                motes=((240, 240, 255), -4), slug=((230, 220, 250), BEAM),
                fliers=("finch", "breeze", "foam", "drake"), walkers=("goat", "tuft", "quill", "rubble", "splash"),
                out=("goat", "finch", "tuft"), far_grounds=[(338, (440, 600)), (330, (700, 920))],
                lower_props=("rocks",), adds=[("cairn", 140, 500)])


BUILD = dict(dunes=build_dunes, lava=build_lava, grotto=build_grotto, kelp=build_kelp, lighthouse=build_lighthouse)
