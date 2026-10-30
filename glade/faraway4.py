"""The far places, round three (2026-10-27, his picks): the Comet Crater above the Starfall
Meadow, the Moonpetal Garden above the Old Ruins, the Floating Isles above the Cloud Bridge, the
Storm Peaks right of it, and Thornwood left of Fern Gully.
"""

import math
import random

import pygame

import art
from art import GLOW, H, W, glow, mix
from kit import blob_row, lit, make, tint
from life import Motes, Steam
from scenes import crystal

COMET = (180, 220, 255)
MOONFLOWER = (240, 236, 255)
BOLT = (230, 230, 255)
BERRY = [(255, 80, 140), (190, 110, 255), (255, 120, 90)]
CLOUD = (196, 186, 255)


# --- The Comet Crater (above the Starfall Meadow) ----------------------------------------------

def comet_mid(sc, rng):
    glows = []
    lay = art.plane()  # the comet's track, still glowing across the sky
    for i in range(240):
        f = i / 240
        x, y = int(80 + f * 380), int(40 + f * 210)
        glow(lay, x, y, int(2 + f * 6), COMET, int(30 + 90 * f))
    sc.raw(lay)
    lay = art.plane()  # the crater: a wide bowl, its rim thrown up
    art.ridge(lay, rng, 330, 16, sc.col("leaf3", 0.7), scales=(140, 40, 14))
    sc.add(lay, 0.7, veil=0.04)
    lay = art.plane()
    rim = sc.col("stone", 0.45)
    pygame.draw.ellipse(lay, rim, (90, 330, 780, 120))
    pygame.draw.ellipse(lay, tint(rim, -0.35), (130, 344, 700, 92))
    pygame.draw.ellipse(lay, tint(rim, -0.2), (170, 360, 620, 70))
    # the comet itself, sunk in the middle, cracked and shining
    art.rock(lay, rng, 480, 404, 60, 50, (120, 130, 180))
    for j in range(7):
        a = -math.pi * (0.1 + 0.8 * j / 6)
        pygame.draw.line(lay, COMET, (480, 386), (480 + math.cos(a) * 46, 386 + math.sin(a) * 34))
    glow(sc.emit, 480, 380, 18, COMET, 220)
    glows.append(lit(sc, 480, 380, 260, COMET, 90))
    for x, y, c in ((280, 400, GLOW["violet"]), (660, 396, COMET), (380, 420, GLOW["cyan"]), (590, 424, GLOW["violet"])):
        for k in range(4):
            crystal(lay, x + (k - 2) * 9, y, rng.randint(14, 34), rng.randint(4, 7), c, rng.uniform(-0.4, 0.4))
        glows.append(lit(sc, x, y - 16, 70, c, 60))
    sc.add(lay, 0.45, texture=0.4)
    sc.live(Motes(rng, (200, 260, 560, 160), 60, COMET, rise=-10))
    return glows


def build_comet():
    return make("comet", "The Comet Crater", 91,
                dict(sky=[(6, 6, 30), (16, 16, 64), (36, 34, 110), (70, 60, 150)], mist=(100, 100, 180),
                     shade=(8, 8, 36), ambient=((236, 236, 255), (90, 90, 160)), leaf=(110, 180, 170),
                     leaf2=(150, 200, 190), leaf3=(70, 100, 150), stone=(120, 120, 180),
                     flowers=[(200, 220, 255), (255, 255, 255), (230, 200, 255)]),
                exits=[("down", "Back to the Starfall Meadow", "meadow")], gy=452, stars=380, star_floor=320,
                mid=comet_mid, fly=COMET, squid=[COMET, GLOW["violet"]], slug=((200, 210, 255), COMET),
                fliers=("meteor", "dream", "gem", "wish"), walkers=("twinkle", "quartz", "shard", "geode", "kick"),
                out=("twinkle", "meteor", "quartz"), far_grounds=[(338, (60, 300)), (338, (660, 900))],
                lower_props=("rocks", "crystals"))


# --- The Moonpetal Garden (above the Old Ruins) ---------------------------------------------------

def garden_mid(sc, rng):
    glows = []
    lay = art.plane()
    art.canopy(lay, rng, -20, 980, 250, sc.col("leaf3", 0.8), r=(12, 26))
    sc.add(lay, 0.8, veil=0.05)
    lay = art.plane()  # the old garden wall, an archway in it, moonflowers climbing everywhere
    stone = sc.col("stone", 0.5)
    pygame.draw.rect(lay, stone, (0, 300, W, 60))
    for y in range(306, 360, 10):
        for x in range((y // 10 % 2) * 14, W, 28):
            pygame.draw.rect(lay, tint(stone, -0.18), (x, y, 26, 8), 1)
    pygame.draw.rect(lay, (0, 0, 0, 0), (440, 300, 80, 60))
    pygame.draw.ellipse(lay, (0, 0, 0, 0), (440, 276, 80, 50))
    pygame.draw.arc(lay, tint(stone, 0.15), (436, 272, 88, 58), 0, math.pi, 4)
    for _ in range(26):
        x, y = rng.randint(0, W), rng.randint(290, 350)
        art.clump(lay, rng, x, y, rng.randint(10, 18), sc.col("leaf", 0.5))
        for k in range(rng.randint(2, 5)):
            fx, fy = x + rng.randint(-12, 12), y + rng.randint(-8, 6)
            pygame.draw.circle(lay, MOONFLOWER, (fx, fy), 2)
            if k == 0:
                glows.append((fx, fy, 24, MOONFLOWER, 50, fx * 0.1))
    sc.add(lay, 0.5, veil=0.03)
    lay = art.plane()  # the fountain in the middle of the lawn
    stone = sc.col("stone", 0.32)
    pygame.draw.ellipse(lay, tint(stone, -0.3), (370, 404, 220, 40))
    pygame.draw.ellipse(lay, stone, (370, 400, 220, 36))
    pygame.draw.ellipse(lay, sc.col("water", 0.3), (384, 404, 192, 26))
    pygame.draw.rect(lay, stone, (470, 350, 20, 56))
    pygame.draw.ellipse(lay, stone, (440, 344, 80, 16))
    pygame.draw.ellipse(lay, sc.col("water", 0.3), (448, 346, 64, 10))
    for side in (-1, 1):  # the water falling from the top bowl
        for k in range(14):
            pygame.draw.circle(lay, (190, 230, 255), (480 + side * (32 + k * 0.6), 352 + k * 4), 1)
    sc.add(lay, 0.32, texture=0.4)
    glows.append(lit(sc, 480, 410, 160, (150, 220, 255), 60))
    sc.live(Steam(rng, [(480, 346, 20)], n_each=4, color=(200, 230, 255), height=40))
    return glows


def build_garden():
    return make("garden", "The Moonpetal Garden", 92,
                dict(sky=[(8, 8, 30), (20, 20, 64), (40, 40, 100), (76, 70, 140)], mist=(110, 100, 170),
                     shade=(10, 10, 34), ambient=((240, 240, 255), (96, 96, 160)), leaf=(100, 180, 150),
                     leaf2=(130, 200, 160), leaf3=(60, 110, 130), stone=(170, 166, 200), water=(90, 150, 220),
                     flowers=[MOONFLOWER, (255, 210, 240), (200, 200, 255), (255, 255, 255)]),
                exits=[("down", "Back to the Old Ruins", "ruins")], gy=448, stars=220, star_floor=260,
                moon_at=(160, 70, 26), mid=garden_mid, fly=MOONFLOWER, squid=[MOONFLOWER, GLOW["pink"]],
                motes=((255, 240, 255), -3), slug=((230, 220, 255), MOONFLOWER),
                fliers=("lulla", "hush", "dew", "moth"), walkers=("petal", "wick", "pom", "sap", "glint"),
                out=("petal", "lulla", "wick"), far_grounds=[(366, (40, 400)), (366, (560, 920))],
                adds=[("ring", 160, 500), ("ring", 800, 500)], lower_props=("mushrooms",))


# --- The Floating Isles (above the Cloud Bridge) ---------------------------------------------------

def isle(lay, sc, rng, x, y, w, d, glows, falls=True):
    """A floating island: grass on top, a root-hung rock underneath, a thread of water off its edge."""
    rock = sc.col("stone", d)
    pts = [(x - w, y), (x + w, y), (x + w * 0.6, y + w * 0.4), (x + w * 0.1, y + w * 0.9), (x - w * 0.5, y + w * 0.5)]
    art.crag(lay, pts, rock, x + y, strata=(5, 9))
    pygame.draw.ellipse(lay, sc.col("leaf2", d), (x - w - 2, y - 7, w * 2 + 4, 14))
    for k in range(int(w // 12)):
        tx = x - w + 10 + k * 24 + rng.randint(-4, 4)
        art.foliage(lay, rng, tx, y - 10, 9, 8, sc.col("leaf", d), sc.pal)
    for k in range(5):  # hanging roots
        rx = x - w * 0.4 + k * w * 0.2
        pygame.draw.line(lay, tint(rock, -0.2), (rx, y + w * 0.3), (rx + rng.randint(-3, 3), y + w * 0.3 + rng.randint(10, 30)))
    if falls:
        fx = x + w * 0.8
        for k in range(120):
            fy = y + k * 2
            if fy > 470:
                break
            c = mix((200, 230, 255), sc.pal["sky"][1], k / 140)
            pygame.draw.line(lay, c, (fx - 2, fy), (fx + 2, fy))
    glows.append(lit(sc, x, y - 4, w * 2, GLOW["moss"], 40))


def isles_mid(sc, rng):
    glows = []
    for d, y0, c in ((0.85, 380, 0.75), (0.6, 430, 0.55)):
        lay = art.plane()
        blob_row(lay, rng, y0, 24, (30, 70), mix(CLOUD, sc.pal["sky"][1], c))
        sc.add(lay, d, veil=0.02)
    lay = art.plane()
    for x, y, w in ((150, 200, 50), (420, 130, 36), (700, 220, 70), (880, 120, 30), (300, 300, 40)):
        isle(lay, sc, rng, x, y, w, 0.55, glows)
    sc.add(lay, 0.55, veil=0.02)
    return glows


def isles_near(sc, lay, rng):
    """We stand on an island too: its grass ends in a broken edge with cloud below."""
    art.grass_bed(lay, rng, (0, 452, W, 88), sc.col("leaf", 0.18), 1200, 6)
    art.flowers(lay, rng, (0, 460, W, 80), sc.pal["flowers"], 60)
    from hall import stair
    stair(sc, lay)  # up to the Moonlit Hall


def build_isles():
    return make("isles", "The Floating Isles", 93,
                dict(sky=[(8, 10, 40), (24, 26, 80), (50, 50, 130), (100, 96, 180)], mist=(140, 140, 210),
                     shade=(12, 12, 40), ambient=((240, 240, 255), (110, 110, 180)), leaf=(110, 190, 160),
                     leaf2=(150, 210, 170), leaf3=(70, 120, 140), stone=(140, 120, 180),
                     flowers=[(255, 255, 255), (200, 220, 255), (255, 220, 240)]),
                exits=[("down", "Back to the Cloud Bridge", "bridge"), ("up", "The Moonlit Hall", "hall", 700)], gy=452, stars=300, star_floor=360,
                moon_at=(560, 60, 20), mid=isles_mid, near=isles_near, fly=(255, 240, 220),
                squid=[GLOW["violet"], GLOW["white"]], motes=((230, 230, 255), -2), slug=((220, 230, 255), GLOW["moss"]),
                fliers=("breeze", "wish", "drake", "finch", "dream"), walkers=("tuft", "goat", "kick", "starb"),
                out=("tuft", "breeze", "goat"), far_grounds=[(214, (650, 760)), (194, (110, 190))],
                lower_props=("rocks",))


# --- The Storm Peaks (right of the Cloud Bridge) ----------------------------------------------------

class Lightning:
    """Now and then a bolt forks down behind the peaks and the whole sky flickers."""

    def __init__(self, seed):
        rng = random.Random(seed)
        self.bolts = []
        for _ in range(4):
            x, y, pts = rng.randint(150, 810), 30, []
            while y < 300:
                pts.append((x, y))
                x += rng.randint(-18, 18)
                y += rng.randint(10, 24)
            self.bolts.append(pts)
        self.band = art.solid((W, 320))

    def strike(self, t):
        k = t % 7.0
        return None if k > 0.35 else (int(t // 7) % 4, 1 - k / 0.35)

    def light(self, lm, t):
        hit = self.strike(t)
        if hit:
            glow(lm, self.bolts[hit[0]][-1][0], 200, 400, BOLT, int(80 * hit[1]))

    def shine(self, s, t):
        hit = self.strike(t)
        if not hit:
            return
        i, k = hit
        self.band.fill(tuple(int(v * 0.12 * k) for v in BOLT))
        pygame.draw.lines(self.band, tuple(int(v * k) for v in BOLT), False, self.bolts[i], 2)
        s.blit(self.band, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def storm_mid(sc, rng):
    glows = []
    lay = art.plane()  # the thunderheads
    for _ in range(40):
        x, y, r = rng.randint(-40, W + 40), rng.randint(20, 160), rng.randint(30, 70)
        pygame.draw.circle(lay, mix((70, 70, 110), sc.pal["sky"][1], rng.random() * 0.5), (x, y), r)
    sc.add(lay, 0.9, texture=0)
    sc.live(Lightning(94))
    lay = art.plane()  # jagged peaks, iron-dark, lit along their edges
    for d, y0, amp in ((0.7, 300, 80), (0.45, 360, 60)):
        tops = []
        x = -20
        while x < W + 40:
            tops.append((x, y0 - rng.randint(0, amp)))
            x += rng.randint(30, 70)
        art.crag(lay, tops + [(W + 40, H), (-20, H)], sc.col("stone", d), int(y0), strata=(6, 12))
        for (x0, y0_), (x1, y1) in zip(tops, tops[1:]):
            pygame.draw.line(lay, tint(BOLT, -0.4), (x0, y0_), (x1, y1))
    sc.add(lay, 0.45, veil=0.03)
    for x in (200, 520, 780):  # crystals on the peaks humming with charge
        glows.append(lit(sc, x, 330, 60, (250, 250, 140), 60, core=3))
    return glows


def build_storm():
    return make("storm", "The Storm Peaks", 94,
                dict(sky=[(10, 10, 24), (24, 24, 50), (44, 44, 80), (70, 70, 110)], mist=(90, 90, 130),
                     shade=(10, 10, 26), ambient=((230, 230, 255), (80, 80, 120)), leaf=(110, 140, 150),
                     leaf2=(130, 150, 160), leaf3=(60, 80, 110), stone=(90, 90, 130),
                     flowers=[(250, 250, 140), (200, 220, 255)]),
                exits=[("left", "Back to the Cloud Bridge", "bridge")], gy=452, stars=40, star_floor=80,
                mid=storm_mid, fly=(250, 250, 140), squid=[(250, 250, 140), GLOW["cyan"]],
                motes=((250, 250, 160), -6), slug=((200, 200, 230), (250, 250, 140)),
                fliers=("spark", "zap", "zing", "umbra"), walkers=("fizz", "goat", "rubble", "pebble", "bulb"),
                out=("fizz", "spark", "pebble"), far_grounds=[(424, (60, 400)), (426, (560, 900))],
                lower_props=("rocks",))


# --- Thornwood (left of Fern Gully) -----------------------------------------------------------------

def bramble(lay, rng, x, y, r, color, glows, sc):
    """A knot of black thorny stems, berries glowing in it."""
    for _ in range(int(r * 0.8)):
        a, ln = rng.uniform(0, math.tau), rng.uniform(r * 0.3, r)
        pts, px, py = [], x, y
        for i in range(6):
            px += math.cos(a + i * 0.4) * ln / 6
            py += math.sin(a + i * 0.4) * ln / 6 * 0.7
            pts.append((px, py))
        pygame.draw.lines(lay, color, False, [(x, y)] + pts, 2)
        tx, ty = pts[-1]
        pygame.draw.line(lay, color, (tx, ty), (tx + 3, ty - 2))
    for _ in range(int(r // 6)):
        bx, by = x + rng.randint(-int(r * 0.7), int(r * 0.7)), y + rng.randint(-int(r * 0.4), int(r * 0.4))
        c = rng.choice(BERRY)
        pygame.draw.circle(lay, c, (bx, by), 2)
        if 0 <= bx < W and 0 <= by < H:
            sc.emit.set_at((bx, by), art.scale(c, 0.6))
        glows.append((bx, by, 18, c, 60, bx * 0.1))


def thorn_mid(sc, rng):
    glows = []
    for d, n, y in ((0.75, 10, 380), (0.5, 6, 410)):
        lay = art.plane()
        art.ridge(lay, rng, y, 6, sc.col("leaf3", d), scales=(120, 40, 14))
        for _ in range(n):  # twisted black trees
            x = rng.randint(0, W)
            art.trunk(lay, rng, x, 40 + rng.randint(0, 80), y + 6, rng.randint(6, 14), sc.col("wood", d), branches=3)
        for _ in range(n + 4):
            bramble(lay, rng, rng.randint(0, W), y - rng.randint(0, 30), rng.randint(20, 40), sc.col("wood", d * 0.8), glows, sc)
        sc.add(lay, d, veil=0.05, low=0.12)
    return glows


def thorn_props(sc, rng):
    glows = []
    lay = art.plane()
    for x, y, r in ((90, 500, 50), (300, 520, 36), (700, 510, 44), (880, 470, 50)):
        bramble(lay, rng, x, y, r, (40, 26, 44), glows, sc)
    sc.add(lay, 0.12, texture=0.4)
    return glows


def build_thorn():
    return make("thorn", "Thornwood", 95,
                dict(sky=[(10, 6, 20), (24, 12, 40), (40, 20, 60), (64, 32, 80)], mist=(90, 50, 100),
                     shade=(12, 6, 22), ambient=((240, 220, 240), (80, 50, 96)), leaf=(90, 120, 110),
                     leaf2=(100, 110, 120), leaf3=(50, 50, 80), wood=(70, 50, 76),
                     flowers=[(255, 80, 140), (190, 110, 255)]),
                exits=[("right", "Back to Fern Gully", "gully")], gy=452, stars=60, star_floor=100,
                moon_at=(820, 70, 14), mid=thorn_mid, props=thorn_props, fly=BERRY[1], squid=[BERRY[0], BERRY[1]],
                motes=((255, 120, 180), -3), slug=((160, 120, 170), BERRY[0]),
                fliers=("umbra", "bat", "hollow", "mire"), walkers=("bramble", "smudge", "burr", "murk", "bark"),
                out=("bramble", "umbra", "smudge"), far_grounds=[(410, (60, 400)), (412, (560, 900))],
                lower_props=("mushrooms",))


BUILD = dict(comet=build_comet, garden=build_garden, isles=build_isles, storm=build_storm, thorn=build_thorn)
