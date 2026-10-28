"""The far places, round one (2026-10-27, his picks): the Frozen Falls above the Snowy Ridge,
Aurora Peak left of it, Fern Gully left of the Mushroom Hollow, the Lantern Orchard below the
Hollow and the Sunken Temple below the Misty Bog. Built with kit.make; each painter here is
what makes its place itself.
"""

import math

import pygame

import art
from art import GLOW, W, glow, mix
from kit import blob_row, lit, make, tint
from life import Aurora, River, Snow
from pond import Shoal, Water
from scenes import ice_crystals

ICE = (170, 230, 255)
AURORA = [((120, 255, 190), (110, 210, 255)), ((190, 140, 255), (255, 150, 220))]
FRUIT = [(255, 196, 120), (255, 150, 200), (255, 236, 140)]


# --- The Frozen Falls (above the Snowy Ridge) ---------------------------------------------------

def falls_mid(sc, rng):
    sc.live(Aurora(rng, 0, 130, AURORA))
    glows = []
    lay = art.plane()
    rock = sc.col("stone", 0.6)
    art.crag(lay, [(0, 150), (180, 120), (380, 104), (580, 100), (780, 118), (W, 150), (W, 420), (0, 420)], rock, 81,
             strata=(8, 14))
    for x in range(0, W, 3):  # snow along the cliff top
        y = 104 + abs(x - 480) * 0.1 + math.sin(x / 9) * 2
        pygame.draw.line(lay, (230, 240, 255), (x, y - 2), (x + 3, y - 2), 3)
    # the falls, frozen solid: a pale column, streaked, icicles off the lip
    for x in range(400, 561):
        f = (x - 400) / 160
        c = mix(ICE, (255, 255, 255), 0.3 * math.sin(f * math.pi)) if x % 7 else mix(ICE, (120, 170, 230), 0.4)
        pygame.draw.line(lay, c, (x, 100), (x, 400 + int(6 * math.sin(x / 11))))
    for x in range(380, 580, 6):
        ln = rng.randint(8, 30)
        pygame.draw.polygon(lay, ICE, [(x - 3, 100), (x + 3, 100), (x, 100 + ln)])
    for x in range(410, 560, 20):
        sc.emit.set_at((x, 260), art.scale(ICE, 0.5))
        glows.append(lit(sc, x, 240 + (x % 60), 80, ICE, 50))
    sc.add(lay, 0.55, veil=0.03, texture=0.5)
    lay = art.plane()
    pygame.draw.ellipse(lay, mix(ICE, (60, 90, 160), 0.4), (330, 396, 300, 40))  # the frozen pool at its foot
    pygame.draw.ellipse(lay, mix(ICE, (255, 255, 255), 0.2), (380, 404, 200, 18), 1)
    for x in (120, 210, 760, 860):
        art.pine(lay, rng, x, 440, rng.randint(70, 110), sc.col("leaf3", 0.35), snow=(220, 236, 255))
    ice_crystals(sc, lay, 300, 430, 4, ICE, glows)
    ice_crystals(sc, lay, 660, 426, 5, GLOW["violet"], glows)
    sc.add(lay, 0.35, texture=0.4)
    sc.live(Snow(rng, (0, 0, W, 540), 70))
    return glows


def build_falls():
    return make("falls", "The Frozen Falls", 81,
                dict(sky=[(6, 10, 30), (14, 24, 60), (30, 44, 96), (60, 80, 140)], mist=(110, 130, 190),
                     shade=(10, 14, 40), ambient=((230, 240, 255), (90, 110, 170)), leaf=(160, 190, 220),
                     leaf2=(210, 226, 250), leaf3=(60, 100, 130), stone=(120, 130, 190), earth=(220, 230, 250),
                     earth_edge=(140, 150, 200), flowers=[(200, 230, 255), (255, 255, 255), (190, 160, 255)]),
                exits=[("down", "Back to the Snowy Ridge", "ridge")], gy=444, star_floor=120,
                mid=falls_mid, fly=ICE, squid=[ICE, GLOW["violet"]], motes=(ICE, -2), slug=((200, 210, 255), ICE),
                fliers=("glace", "wisp", "finch", "mistm"), walkers=("snowp", "shiver", "newt", "fox", "splash"),
                out=("snowp", "glace", "shiver"), far_grounds=[(420, (40, 300)), (420, (660, 920))],
                lower_props=("pines", "crystals"), lower=dict(bushes=False))


# --- Aurora Peak (left of the Snowy Ridge) ------------------------------------------------------

def peak_mid(sc, rng):
    sc.live(Aurora(rng, 0, 240, AURORA + [((255, 236, 160), (150, 255, 220))]))
    lay = art.plane()  # the world far below: other peaks poking through a sea of mist
    art.mountains(lay, rng, 380, 40, sc.col("lav", 0.85), scales=(140, 50, 18))
    sc.add(lay, 0.85, veil=0.04)
    lay = art.plane()
    blob_row(lay, rng, 396, 30, (20, 50), mix(sc.pal["mist"], (255, 255, 255), 0.1))
    sc.add(lay, 0.7, veil=0.02, texture=0)
    glows = []
    lay = art.plane()  # the summit, and a ring of standing stones lit with runes
    art.crag(lay, [(0, 470), (160, 400), (360, 360), (600, 356), (800, 390), (W, 450), (W, 540), (0, 540)],
             sc.col("leaf2", 0.35), 82, strata=(6, 12))
    for i in range(9):
        a = i / 9 * math.tau
        x, y = int(480 + math.cos(a) * 200), int(392 + math.sin(a) * 26)
        h = rng.randint(50, 76) + (20 if y > 392 else 0)
        art.rock(lay, rng, x, y, 16 + (y > 392) * 5, h, sc.col("stone", 0.3 if y > 392 else 0.4), moss=sc.col("leaf2", 0.3))
        c = AURORA[i % 2][i % 2]
        for dy in range(0, 8, 2):
            lay.set_at((x, y - h + 10 + dy), c)
        glows.append(lit(sc, x, y - h + 14, 50, c, 60, core=2))
    sc.add(lay, 0.35, texture=0.5)
    sc.live(Snow(rng, (0, 0, W, 540), 40))
    return glows


def build_peak():
    return make("peak", "Aurora Peak", 82,
                dict(sky=[(4, 8, 26), (10, 20, 54), (24, 36, 90), (46, 60, 120)], mist=(120, 120, 200),
                     shade=(8, 10, 34), ambient=((236, 240, 255), (100, 110, 180)), leaf=(170, 190, 230),
                     leaf2=(214, 224, 250), leaf3=(70, 90, 140), stone=(110, 116, 170), lav=(90, 90, 160),
                     earth=(220, 226, 250), earth_edge=(140, 140, 200),
                     flowers=[(190, 255, 220), (255, 255, 255), (200, 180, 255)]),
                exits=[("right", "Back to the Snowy Ridge", "ridge")], gy=448, stars=320, star_floor=300,
                mid=peak_mid, fly=(190, 255, 220), squid=[(120, 255, 190), (255, 150, 220)], motes=((200, 255, 230), -3),
                fliers=("finch", "glace", "breeze", "wish"), walkers=("goat", "fox", "cone", "rune", "rubble"),
                out=("goat", "finch", "rune"), far_grounds=[(404, (300, 660))], lower_props=("rocks", "crystals"),
                lower=dict(bushes=False))


# --- Fern Gully (left of the Mushroom Hollow) ---------------------------------------------------

def frond(lay, x, y, length, angle, color, curl=1.0):
    """A fern frond arching out from (x, y), leaflets either side, the tip curling over."""
    px, py, a = x, y, angle
    for i in range(int(length)):
        f = i / length
        a += 0.012 * curl * (1 + 2 * f)
        nx, ny = px + math.cos(a), py + math.sin(a)
        if i % 4 == 0:
            ln = (1 - f) * length * 0.18 + 2
            for side in (-1, 1):
                b = a + side * 1.2
                pygame.draw.line(lay, mix(color, (255, 255, 255), 0.15 * (side > 0)), (nx, ny),
                                 (nx + math.cos(b) * ln, ny + math.sin(b) * ln), 2)
        pygame.draw.line(lay, mix(color, (0, 0, 0), 0.2), (px, py), (nx, ny), 2)
        px, py = nx, ny


def gully_mid(sc, rng):
    glows = []
    lay = art.plane()  # far: the gully narrowing away, trees along its rim
    art.canopy(lay, rng, -20, 980, 120, sc.col("leaf3", 0.85), r=(12, 24))
    sc.add(lay, 0.85, veil=0.06)
    lay = art.plane()
    art.crag(lay, [(0, 120), (200, 180), (380, 330), (400, 460), (0, 460)], sc.col("stone", 0.45), 83, strata=(6, 12))
    art.crag(lay, [(W, 110), (760, 170), (580, 330), (560, 460), (W, 460)], sc.col("stone", 0.45), 84, strata=(6, 12))
    for x, y, a, c in ((60, 200, 0.2, 0.45), (160, 250, 0.1, 0.4), (260, 330, -0.1, 0.4), (900, 190, math.pi - 0.2, 0.45),
                       (800, 250, math.pi - 0.1, 0.4), (690, 330, math.pi + 0.1, 0.4)):
        for k in range(3):
            frond(lay, x, y + k * 8, rng.randint(90, 140), a + 0.3 - k * 0.3, mix(sc.col("leaf", c * 0.5), (180, 255, 200), 0.15),
                  curl=1 if a < 1 else -1)
    for x, y in ((120, 300), (300, 380), (840, 300), (650, 380)):
        art.glowmoss(sc, lay, x, y, 50, 16, GLOW["moss"], 50, 0.8)
    sc.add(lay, 0.4, veil=0.03)
    lay = art.plane()  # the creek coming down the middle
    water = sc.col("water", 0.3)
    art.path(lay, [(480, 330), (470, 380), (500, 420), (470, 470), (480, 560)], [10, 24, 40, 70, 110],
             water, mix(water, (255, 255, 255), 0.25))
    art.forget_paths()
    sc.add(lay, 0.3, texture=0)
    sc.live(River(sc.rng, lambda x: 440, lambda x: 470, (430, 530), 30, mix(water, (255, 255, 255), 0.5), (255, 255, 255),
                  speed=20))
    for y in (360, 420, 480):
        glows.append(lit(sc, 480, y, 60, GLOW["cyan"], 40))
    return glows


def build_gully():
    return make("gully", "Fern Gully", 83,
                dict(sky=[(6, 14, 26), (12, 30, 46), (26, 52, 70), (44, 80, 96)], mist=(60, 110, 120),
                     shade=(6, 16, 26), ambient=((214, 240, 230), (60, 100, 110)), leaf=(90, 190, 140),
                     leaf2=(110, 200, 150), leaf3=(40, 110, 110), stone=(80, 110, 120), water=(60, 150, 190),
                     flowers=[(180, 255, 200), (255, 255, 255), (140, 220, 255)]),
                exits=[("right", "Back to the Mushroom Hollow", "hollow"), ("left", "Thornwood", "thorn")],
                gy=452, stars=40, star_floor=80, mid=gully_mid, fly=GLOW["lime"], squid=[GLOW["moss"], GLOW["cyan"]],
                motes=(GLOW["moss"], -4), slug=((180, 230, 160), GLOW["moss"]),
                fliers=("fern", "drake", "spark", "thistle"), walkers=("reed", "sap", "bark", "toad", "newt", "ripple"),
                out=("reed", "fern", "toad"), far_grounds=[(456, (300, 420)), (452, (560, 680))],
                lower_props=("mushrooms",), adds=[("log", 300, 520)])


# --- The Lantern Orchard (below the Mushroom Hollow) -------------------------------------------

def orchard_mid(sc, rng):
    glows = []
    lay = art.plane()
    art.ridge(lay, rng, 320, 20, sc.col("leaf3", 0.8), scales=(160, 50, 16))
    sc.add(lay, 0.8, veil=0.05)
    for d, y, xs, h in ((0.6, 360, range(60, W, 110), 70), (0.4, 410, range(10, W, 150), 110)):
        lay = art.plane()
        art.ridge(lay, rng, y, 6, sc.col("leaf2", d), scales=(120, 40, 14))
        for x in xs:
            x += rng.randint(-10, 10)
            art.trunk(lay, rng, x, y - h, y, 6 + int(h / 18), sc.col("wood", d), branches=2)
            art.foliage(lay, rng, x, y - h, int(h * 0.55), int(h * 0.35), sc.col("leaf", d), sc.pal)
            for _ in range(5):  # glowing fruit in the leaves
                fx, fy = x + rng.randint(-int(h * 0.45), int(h * 0.45)), y - h + rng.randint(-int(h * 0.2), int(h * 0.3))
                c = rng.choice(FRUIT)
                pygame.draw.circle(lay, c, (fx, fy), 2 + (d < 0.5))
                if 0 <= fx < W:
                    sc.emit.set_at((fx, fy), art.scale(c, 0.5))
                glows.append((fx, fy, 14, c, 50, fx * 0.1))
            lx, ly = x + rng.choice((-1, 1)) * int(h * 0.3), y - h + int(h * 0.35)  # a lantern hung from a branch
            pygame.draw.line(lay, (60, 40, 60), (lx, ly - 10), (lx, ly - 3))
            pygame.draw.ellipse(lay, (255, 200, 140), (lx - 3, ly - 3, 7, 9))
            glows.append(lit(sc, lx, ly, 70, GLOW["amber"], 70, core=3))
        sc.add(lay, d, veil=0.03)
    return glows


def build_orchard():
    return make("orchard", "The Lantern Orchard", 84,
                dict(sky=[(12, 8, 30), (30, 18, 60), (60, 36, 96), (110, 64, 130)], mist=(110, 80, 140),
                     shade=(14, 8, 30), ambient=((255, 236, 236), (100, 76, 130)), leaf=(120, 180, 140),
                     leaf2=(150, 200, 150), leaf3=(70, 110, 120), wood=(140, 100, 120),
                     flowers=[(255, 200, 230), (255, 236, 160), (255, 255, 255)]),
                exits=[("up", "Back to the Mushroom Hollow", "hollow", 480)], gy=448, stars=120, star_floor=200,
                moon_at=(780, 60, 16), mid=orchard_mid, fly=GLOW["amber"], squid=[GLOW["amber"], GLOW["pink"]],
                motes=((255, 220, 200), -2), slug=((255, 200, 170), GLOW["amber"]),
                fliers=("moth", "lulla", "hush", "zing"), walkers=("petal", "burr", "pom", "sporeling", "wick"),
                out=("petal", "moth", "pom"), far_grounds=[(408, (40, 400)), (410, (560, 920))],
                lower_props=("mushrooms",), adds=[("ring", 160, 510), ("cairn", 820, 500)])


# --- The Sunken Temple (below the Misty Bog) ---------------------------------------------------

JADE = (110, 230, 190)


def temple_mid(sc, rng):
    glows = []
    lay = art.plane()
    art.canopy(lay, rng, -20, 980, 230, sc.col("leaf3", 0.85), r=(12, 26))
    sc.add(lay, 0.85, veil=0.08, low=0.12)
    lay = art.plane()  # the temple, half under the water: stepped tiers and a shrine on top
    stone = sc.col("stone", 0.5)
    for i, (w, h) in enumerate(((420, 34), (330, 30), (240, 28), (150, 26))):
        y = 360 - sum(hh for _, hh in ((420, 34), (330, 30), (240, 28), (150, 26))[:i + 1])
        pygame.draw.rect(lay, tint(stone, 0.06 * (i % 2)), (480 - w // 2, y, w, h))
        pygame.draw.rect(lay, sc.col("moss", 0.45), (480 - w // 2, y, w, 3))
        for k in range(480 - w // 2 + 8, 480 + w // 2 - 8, 22):
            pygame.draw.rect(lay, tint(stone, -0.25), (k, y + 8, 10, h - 12))
    pygame.draw.rect(lay, tint(stone, 0.08), (450, 210, 60, 40))  # the shrine
    pygame.draw.polygon(lay, tint(stone, 0.12), [(440, 212), (480, 190), (520, 212)])
    pygame.draw.rect(lay, JADE, (472, 224, 16, 22))
    glow(sc.emit, 480, 234, 10, JADE, 200)
    glows.append(lit(sc, 480, 234, 140, JADE, 80))
    for x in (300, 660):  # vines down its face
        for k in range(0, 80, 3):
            lay.set_at((x + int(math.sin(k / 6) * 3), 250 + k), sc.col("leaf", 0.4))
    sc.add(lay, 0.5, veil=0.04)
    lay = art.plane()  # the dark water it stands in, with its lights mirrored
    water = sc.col("water", 0.35)
    art.gradient(lay, (0, 360, W, 90), [mix(water, (140, 200, 200), 0.2), water, tint(water, -0.3)], steps=5)
    for k in range(12):
        pygame.draw.line(lay, mix(water, JADE, 0.5 - k * 0.04), (474 + k % 3, 362 + k * 6), (486 - k % 2, 362 + k * 6))
    for x, y in ((180, 400), (360, 420), (620, 410), (800, 430), (520, 438)):
        pygame.draw.ellipse(lay, sc.col("leaf", 0.3), (x - 12, y - 3, 24, 7))
        for j in range(5):  # a lotus, glowing
            a = math.pi + j * math.pi / 4
            pygame.draw.ellipse(lay, (255, 190, 230), (x + math.cos(a) * 5 - 3, y - 6 + math.sin(a) * 4, 6, 8))
        glows.append(lit(sc, x, y - 4, 50, GLOW["pink"], 60, core=3))
    sc.add(lay, 0.3, texture=0.3)
    return glows


def temple_pond(sc, rng):
    return Shoal(rng, [(Water(240, 420, 120, 10), 2), (Water(720, 420, 120, 10), 2)], sc.col("water", 0.35), size=0.6)


def build_temple():
    return make("temple", "The Sunken Temple", 85,
                dict(sky=[(6, 12, 24), (12, 28, 40), (26, 46, 60), (46, 70, 84)], mist=(80, 120, 120),
                     shade=(6, 14, 22), ambient=((214, 240, 230), (60, 90, 96)), leaf=(90, 160, 130),
                     leaf2=(110, 170, 140), leaf3=(50, 100, 100), stone=(110, 130, 130), water=(40, 100, 110),
                     moss=(110, 200, 150), flowers=[(255, 190, 230), (200, 255, 220), (255, 255, 255)]),
                exits=[("up", "Back to the Misty Bog", "bog", 180)], gy=452, stars=80, star_floor=120,
                mid=temple_mid, pond=temple_pond, fly=JADE, squid=[JADE, GLOW["pink"]], motes=(JADE, -2),
                slug=((170, 220, 190), JADE), fliers=("mire", "hollow", "sigil", "umbra"),
                walkers=("murk", "rune", "slate", "glint", "ripple"), out=("rune", "sigil", "murk"),
                far_grounds=[(358, (300, 420)), (358, (540, 660))], lower_props=("rocks",))


BUILD = dict(falls=build_falls, peak=build_peak, gully=build_gully, orchard=build_orchard, temple=build_temple)
