"""Five more places (2026-10-27, his picks): the Mushroom Hollow below the Forest, the Misty
Bog below the River, the Old Ruins above the Forest, the Cloud Bridge above the Crystal
Caverns, and the Glow Shore past the Hot Springs. Painted the same way as scenes.py (back to
front, always night, lit by what glows); their animals are ones that already live elsewhere,
plus two new lines of their own (wave7.py: Tanglet on the Bridge, Tumblet on the Shore).
scenes.py adds these builders to BUILDERS at its very end.
"""

import math
import random

import pygame

import art
from art import GLOW, H, W, glow, mix
from life import Blades, Fireflies, Motes, Pulses, River, Slug, Stars, Steam, Track, Vines, make_rng
from pond import Shoal, Water
from scenes import (Scene, Spot, additions, front_frame, glowmoss, moon, mushroom, pal, second_wave, squids)

SPORE = (200, 255, 170)
WISP = (190, 255, 210)
RUNE = (150, 230, 255)
CLOUD = (196, 186, 255)
SEA = (90, 240, 230)


def giant_mushroom(sc, lay, x, base, h, r, cap, glows, lean=0.0):
    """A toadstool taller than a tree: a pale bending stalk, a broad cap glowing from its
    gills, and freckles of light on top."""
    stem, shade = (226, 214, 232), (150, 130, 170)
    top = (x + lean * h, base - h)
    for i in range(h):  # the stalk, thicker at the foot
        f = i / h
        cx = x + lean * h * f * f
        w = r * (0.32 - 0.12 * f) + 2
        pygame.draw.line(lay, mix(stem, shade, 0.55 - 0.25 * f), (cx - w, base - i), (cx + w, base - i))
        pygame.draw.line(lay, stem, (cx - w * 0.2, base - i), (cx + w * 0.6, base - i))
    tx, ty = top
    pygame.draw.ellipse(lay, mix(cap, (255, 255, 255), 0.4), (tx - r, ty - 3, r * 2, r * 0.5))  # the glowing gills
    for k in range(-r + 4, r - 3, 4):
        pygame.draw.line(lay, mix(cap, (40, 20, 60), 0.4), (tx + k * 0.3, ty + 2), (tx + k, ty + r * 0.18))
    pygame.draw.ellipse(lay, mix(cap, (40, 20, 70), 0.35), (tx - r, ty - r * 0.62, r * 2, r * 0.75))
    pygame.draw.ellipse(lay, cap, (tx - r + 2, ty - r * 0.66, r * 2 - 4, r * 0.66))
    pygame.draw.ellipse(lay, mix(cap, (255, 255, 255), 0.35), (tx - r * 0.55, ty - r * 0.6, r * 0.8, r * 0.2))
    rng = random.Random(x)
    for _ in range(r // 4):  # freckles
        fx, fy = tx + rng.uniform(-0.7, 0.7) * r, ty - r * rng.uniform(0.2, 0.5)
        pygame.draw.circle(lay, mix(cap, (255, 255, 255), 0.7), (round(fx), round(fy)), rng.choice((1, 2)))
    for dx in range(-r // 2, r // 2, 3):
        if 0 <= tx + dx < W and 0 <= ty + 2 < H:
            sc.emit.set_at((int(tx + dx), int(ty + 2)), art.scale(cap, 0.5))
    glows.append((tx, ty + 6, r * 3, cap, 80, x * 0.05))
    sc.lamp(tx, ty + 30, r * 3, cap, 60)


def back_path(sc, lay, rng, x, y_front, y_back):
    """A path running away up the picture to somewhere further up the map."""
    earth, edge = sc.col("earth", 0.22), sc.col("earth_edge", 0.22)
    art.path(lay, [(x, y_front), (x + 6, (y_front + y_back) // 2), (x + 2, y_back)], [40, 22, 8], earth, edge, rng=rng)


# --- The Mushroom Hollow (below the Forest) ---------------------------------------------------

def build_hollow():
    rng = make_rng(71)
    p = pal(sky=[(8, 10, 26), (16, 22, 46), (30, 34, 70), (52, 50, 96)],
            mist=(70, 70, 130), shade=(10, 10, 30), ambient=((220, 236, 240), (70, 76, 120)),
            leaf=(90, 170, 150), leaf2=(120, 190, 160), leaf3=(50, 110, 120), wood=(120, 96, 130),
            flowers=[(200, 255, 170), (255, 170, 230), (170, 220, 255), (255, 255, 255)])
    sc = Scene("hollow", "The Mushroom Hollow", p, rng)
    sc.live(Stars(rng, 50, 80))
    # far: the steep sides of the hollow, trees along its rim
    lay = art.plane()
    art.ridge(lay, rng, 150, 40, sc.col("leaf3", 0.9), scales=(160, 50, 16))
    art.canopy(lay, rng, -20, 980, 150, sc.col("leaf3", 0.85), r=(12, 24))
    sc.add(lay, 0.9, veil=0.05)
    glows = []
    for d, y0, items in ((0.66, 330, ((120, 150, 30, (170, 140, 255), -0.05), (380, 170, 34, (255, 160, 220), 0.04),
                                      (700, 160, 36, (140, 230, 255), -0.02), (880, 120, 26, SPORE, 0.06))),
                         (0.42, 390, ((240, 230, 52, (255, 180, 120), 0.05), (600, 250, 60, (190, 150, 255), -0.04)))):
        lay = art.plane()
        art.ridge(lay, rng, y0, 14, sc.col("leaf2", d), scales=(120, 40, 14))
        for x, h, r, c, lean in items:
            giant_mushroom(sc, lay, x, y0 + 6, h, r, mix(c, sc.col("leaf3", d), d * 0.3), glows, lean)
        sc.add(lay, d, veil=0.04, low=0.1)
    # near: a mossy floor, the path back up to the Forest, clumps of little glowing caps
    lay = art.plane()
    art.ridge(lay, rng, 440, 8, sc.col("leaf2", 0.2), scales=(100, 36, 14))
    art.grass_bed(lay, rng, (0, 440, W, 100), sc.col("leaf", 0.18), 1500, 6)
    art.flowers(lay, rng, (0, 450, W, 90), p["flowers"], 70)
    back_path(sc, lay, rng, 470, 560, 400)
    sc.add(lay, 0.2, texture=0.6)
    lay = art.plane()
    caps = [(130, 140, 255), (255, 150, 220), (140, 236, 255), (200, 255, 150)]
    ring = []
    for x, y in ((100, 490), (250, 512), (650, 500), (820, 486), (900, 520), (360, 470)):
        for _ in range(rng.randint(3, 5)):
            mushroom(lay, x + rng.randint(-18, 18), y + rng.randint(-4, 4), rng.randint(4, 9), rng.choice(caps), sc, ring)
    glowmoss(sc, lay, 180, 470, 80, 14, GLOW["moss"], strength=50)
    glowmoss(sc, lay, 760, 470, 70, 12, GLOW["lime"], strength=50)
    sc.add(lay, 0.12, texture=0)
    sc.live(Pulses(glows + ring, speed=0.7))
    sc.live(Blades(rng, (0, 436, W, 104), 320, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1)], 8, 22))
    sc.live(Motes(rng, (0, 80, W, 420), 90, SPORE, rise=-5))  # spores drifting up from the gills
    sc.live(Slug(rng, Track([(560, 520), (660, 516), (760, 522)]), (230, 200, 255), size=1.5, speed=3, spots=SPORE))
    additions(sc, rng, [("ring", 560, 470), ("log", 120, 520)])
    grounds = [(lambda x: 480 + 3 * math.sin(x / 40), (120, 360)), (lambda x: 510 + 3 * math.sin(x / 50), (560, 860)),
               (lambda x: 496 + 2 * math.sin(x / 60), (300, 640))]
    second_wave(sc, rng, (100, 100, 760, 200), grounds, fliers=("moth", "thistle", "fern", "hum"),
                walkers=("sporeling", "myce", "toad", "bramble", "sap", "mole"), out=("sporeling", "myce", "moth", "fern"),
                far=[(lambda x: 392 + 2 * math.sin(x / 40), (60, 420)), (lambda x: 396 + 2 * math.sin(x / 50), (520, 900))])
    bugs = sc.live(Fireflies(rng, (0, 160, W, 320), 40, color=GLOW["lime"]))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 60, 700, 200), [GLOW["lime"], GLOW["violet"]])
    front_frame(sc, rng)

    sc.spots = [Spot("go", (420, 360, 110, 90), "Back to the Forest", "forest", (474, 404), sign=(474, 360))]
    sc.lower = dict(ground=0.2, props=["mushrooms"], fly=GLOW["lime"],
                    walkers=("sporeling", "myce", "toad", "bramble", "sap"), fliers=("moth", "thistle", "fern"),
                    out=("sporeling", "moth"))
    return sc.done()


# --- The Misty Bog (below the River) ------------------------------------------------------------

def build_bog():
    rng = make_rng(72)
    p = pal(sky=[(8, 14, 24), (16, 30, 44), (30, 50, 64), (52, 76, 86)],
            mist=(84, 120, 130), shade=(8, 16, 24), ambient=((214, 240, 230), (60, 90, 100)),
            leaf=(96, 150, 120), leaf2=(120, 168, 130), leaf3=(56, 96, 100), water=(50, 110, 120),
            earth=(150, 160, 150), earth_edge=(90, 100, 100), wood=(110, 100, 104),
            flowers=[(220, 255, 200), (255, 230, 160), (200, 220, 255)])
    sc = Scene("bog", "The Misty Bog", p, rng)
    sc.live(Stars(rng, 90, 140))
    moon(sc, 820, 70, 14)
    # far: low dark woods, dead trees standing in the water
    lay = art.plane()
    art.canopy(lay, rng, -20, 980, 250, sc.col("leaf3", 0.85), r=(10, 22))
    art.ridge(lay, rng, 280, 10, sc.col("leaf3", 0.85), scales=(160, 50, 16))
    sc.add(lay, 0.85, veil=0.08, low=0.15)
    lay = art.plane()
    for x, top in ((140, 170), (330, 210), (690, 190), (860, 230)):
        art.trunk(lay, rng, x, top, 340, rng.randint(6, 10), sc.col("wood", 0.6), branches=3)
    sc.add(lay, 0.6, veil=0.08, low=0.2)
    # middle: still black water between mossy hummocks, a reflection of every light
    lay = art.plane()
    water = sc.col("water", 0.35)
    art.gradient(lay, (0, 336, W, 120), [mix(water, (150, 200, 200), 0.25), water, mix(water, (0, 0, 0), 0.3)], steps=6)
    for i in range(16):
        y = 340 + i * 7
        pygame.draw.line(lay, mix(water, (200, 240, 230), 0.08 + (i % 3) * 0.03), (rng.randint(0, 300), y), (rng.randint(500, W), y))
    for x, y, w in ((90, 380, 120), (300, 410, 90), (560, 370, 140), (780, 404, 110), (440, 440, 80)):
        pygame.draw.ellipse(lay, sc.col("leaf3", 0.35), (x - w // 2, y - 10, w, 24))
        pygame.draw.ellipse(lay, sc.col("leaf2", 0.35), (x - w // 2 + 6, y - 12, w - 12, 16))
        for k in range(rng.randint(5, 9)):  # reeds
            rx = x + rng.randint(-w // 2 + 8, w // 2 - 8)
            ln = rng.randint(14, 34)
            pygame.draw.line(lay, sc.col("leaf", 0.3), (rx, y - 6), (rx + rng.randint(-3, 3), y - 6 - ln))
            if k % 3 == 0:
                pygame.draw.ellipse(lay, (120, 84, 70), (rx - 1, y - 6 - ln, 3, 7))
    sc.add(lay, 0.35, veil=0.06, low=0.25, texture=0.4)
    shoal = [(Water(200, 440, 90, 8), 2), (Water(660, 430, 110, 8), 2)]
    sc.pond = sc.live(Shoal(rng, shoal, water, size=0.6))
    # will-o'-wisps over the water, and old lanterns sunk to their necks
    wisps = []
    lay = art.plane()
    for x, y in ((120, 316), (380, 290), (520, 330), (700, 300), (880, 326), (260, 352)):
        wisps.append((x, y, 70, WISP, 90, rng.random() * 6))
        glow(lay, x, y, 9, WISP, 150)
        pygame.draw.circle(lay, (240, 255, 245), (x, y), 2)
        glow(sc.emit, x, y, 12, WISP, 255)
        sc.lamp(x, y + 20, 110, WISP, 70)
        for k in range(10):  # its reflection, broken up by the water
            ry = 2 * 360 - y + k * 3 + (y - 290) // 2
            if ry < 450:
                pygame.draw.line(lay, mix(water, WISP, 0.5 - k * 0.04), (x - 4 + k % 3, ry), (x + 3 - k % 2, ry))
    sc.raw(lay)
    sc.live(Pulses(wisps, speed=1.4))
    for x, y, rx in ((200, 350, 220), (640, 380, 260), (400, 430, 300), (860, 420, 160)):  # low mist on the water
        m = art.soft_ellipse(rx, 14, (190, 220, 220), 70)
        sc.cur.blit(m, (x - m.get_width() // 2, y - m.get_height() // 2))
    lay = art.plane()
    for x, y in ((240, 420), (610, 398), (830, 432)):
        pygame.draw.rect(lay, (60, 56, 64), (x - 5, y - 12, 10, 12), border_radius=2)
        pygame.draw.rect(lay, (255, 220, 140), (x - 3, y - 10, 6, 7))
        pygame.draw.line(lay, (60, 56, 64), (x - 4, y - 14), (x + 4, y - 14))
        sc.lamp(x, y - 6, 60, GLOW["amber"], 60)
        pygame.draw.line(lay, mix(water, (255, 220, 140), 0.4), (x - 8, y + 4), (x + 8, y + 4))
    sc.add(lay, 0.3, texture=0)
    # near: a soft mossy bank, a plank walk leading back up to the River
    lay = art.plane()
    art.ridge(lay, rng, 456, 8, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    art.grass_bed(lay, rng, (0, 456, W, 84), sc.col("leaf", 0.18), 1300, 7)
    art.flowers(lay, rng, (0, 470, W, 70), p["flowers"], 50)
    plank = mix(sc.col("wood", 0.15), (255, 230, 220), 0.25)
    for i in range(14):  # boards narrowing as they go out over the water, on posts
        y = 540 - i * 12
        w = 56 - i * 2.6
        x = 480 + i * 2
        c = mix(plank, p["mist"], i * 0.04)
        pygame.draw.rect(lay, mix(c, (0, 0, 0), 0.35), (x - w // 2, y - 6, w, 5))
        pygame.draw.rect(lay, c, (x - w // 2, y - 9, w, 4))
        if i % 3 == 0:
            for sx in (x - w // 2 - 2, x + w // 2 + 1):
                pygame.draw.line(lay, mix(c, (0, 0, 0), 0.4), (sx, y - 16), (sx, y - 2), 2)
    art.forget_paths()
    sc.add(lay, 0.2, texture=0.6)
    lay = art.plane()
    for x, y in ((446, 500), (518, 470)):  # a lantern on a post either side of the boards
        pygame.draw.line(lay, (70, 60, 70), (x, y), (x, y - 30), 3)
        pygame.draw.rect(lay, (255, 220, 150), (x - 3, y - 40, 7, 9))
        glow(sc.emit, x, y - 36, 8, GLOW["amber"], 220)
        sc.lamp(x, y - 30, 120, GLOW["amber"], 80)
    sc.raw(lay)
    glowmoss(sc, sc.cur, 130, 486, 70, 12, GLOW["moss"], strength=50)
    glowmoss(sc, sc.cur, 800, 490, 80, 12, WISP, strength=50)
    sc.live(Blades(rng, (0, 450, W, 90), 260, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1)], 10, 30, stiff=1.2))
    sc.live(Slug(rng, Track([(120, 520), (220, 526), (320, 520)]), (180, 220, 160), size=1.5, speed=3, spots=WISP))
    sc.live(Motes(rng, (0, 260, W, 200), 40, WISP, rise=-2))
    grounds = [(lambda x: 488 + 3 * math.sin(x / 40), (80, 400)), (lambda x: 512 + 3 * math.sin(x / 50), (560, 880)),
               (lambda x: 404 + 0 * x, (740, 820))]
    second_wave(sc, rng, (100, 120, 760, 160), grounds, fliers=("mire", "wisp", "spark", "bubbl"),
                walkers=("murk", "newt", "reed", "silt", "smudge", "toad"), out=("murk", "reed", "mire", "wisp"),
                far=[(lambda x: 372 + 0 * x, (530, 610)), (lambda x: 378 + 0 * x, (50, 130))])
    bugs = sc.live(Fireflies(rng, (0, 220, W, 260), 50, color=GLOW["firefly"]))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 80, 700, 200), [WISP, GLOW["cyan"]])
    front_frame(sc, rng, top=False)

    sc.spots = [Spot("go", (420, 380, 120, 90), "Back to the River", "river", (490, 420), sign=(490, 372))]
    sc.lower = dict(ground=0.18, props=["rocks"], fly=GLOW["firefly"], walkers=("murk", "newt", "reed", "smudge"),
                    fliers=("mire", "wisp"), out=("murk", "mire"))
    return sc.done()


# --- The Old Ruins (above the Forest) ------------------------------------------------------------

def pillar(sc, lay, x, base, h, w, stone, glows, broken=False, rune=RUNE):
    """A standing stone column with a glowing rune carved halfway up, moss on its foot."""
    top = base - h
    pygame.draw.rect(lay, mix(stone, (20, 10, 40), 0.3), (x - w // 2, top, w, h))
    pygame.draw.rect(lay, stone, (x - w // 2, top, w * 2 // 3, h))
    for y in range(top + 10, base, 14):  # the drums it is stacked from
        pygame.draw.line(lay, mix(stone, (20, 10, 40), 0.4), (x - w // 2, y), (x + w // 2, y))
    if broken:
        pygame.draw.polygon(lay, (0, 0, 0, 0),
                            [(x - w // 2, top), (x + w // 2 + 1, top), (x + w // 2 + 1, top + 10), (x, top + 4)])
    else:
        pygame.draw.rect(lay, mix(stone, (255, 255, 255), 0.1), (x - w // 2 - 4, top - 6, w + 8, 7))
    ry = top + h // 2
    for dy in range(-5, 6):  # the rune
        if dy % 3:
            lay.set_at((x + (dy % 4) - 2, ry + dy), rune)
            if 0 <= x < W and 0 <= ry + dy < H:
                sc.emit.set_at((x + (dy % 4) - 2, ry + dy), art.scale(rune, 0.6))
    glows.append((x, ry, 40, rune, 60, x * 0.07))
    pygame.draw.ellipse(lay, sc.col("moss", 0.3), (x - w // 2 - 3, base - 8, w + 6, 10))


def arch(sc, lay, x, base, w, h, stone, glows):
    """A ruined archway: two columns and a lintel of stones."""
    pillar(sc, lay, x - w // 2, base, h, 18, stone, glows)
    pillar(sc, lay, x + w // 2, base, h, 18, stone, glows)
    for i in range(-w // 2 - 8, w // 2 + 8, 14):
        pygame.draw.rect(lay, mix(stone, (255, 255, 255), 0.06 * ((i // 14) % 2)), (x + i, base - h - 18, 13, 12))


def build_ruins():
    rng = make_rng(73)
    p = pal(sky=[(10, 8, 30), (22, 18, 60), (44, 36, 96), (80, 66, 136)],
            mist=(80, 74, 140), shade=(12, 10, 34), ambient=((226, 230, 255), (78, 76, 136)),
            stone=(140, 136, 186), leaf=(80, 170, 150), leaf2=(110, 190, 160), leaf3=(54, 120, 130))
    sc = Scene("ruins", "The Old Ruins", p, rng)
    sc.live(Stars(rng, 200, 240))
    moon(sc, 180, 80, 18)
    lay = art.plane()
    art.mountains(lay, rng, 250, 50, sc.col("lav", 0.9), scales=(180, 60, 20), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    art.canopy(lay, rng, -20, 980, 290, sc.col("leaf3", 0.75), r=(12, 24))
    sc.add(lay, 0.75, veil=0.05, low=0.1)
    glows = []
    # middle: a line of columns, some fallen, the great arch at the back, a broken stair
    lay = art.plane()
    art.ridge(lay, rng, 350, 10, sc.col("leaf2", 0.5), scales=(120, 40, 14))
    stone = sc.col("stone", 0.5)
    for x, h, broken in ((90, 120, False), (180, 70, True), (760, 130, False), (860, 90, True)):
        pillar(sc, lay, x, 352, h, 22, stone, glows, broken)
    arch(sc, lay, 480, 356, 150, 150, sc.col("stone", 0.45), glows)
    for i in range(5):  # steps up to the arch
        pygame.draw.rect(lay, mix(stone, (255, 255, 255), 0.05 * (i % 2)), (400 - i * 8, 356 + i * 8, 160 + i * 16, 8))
    sc.add(lay, 0.5, veil=0.03)
    lay = art.plane()  # vines hanging off the arch
    sc.add(lay, 0.4)
    sc.live(Vines(rng, list(range(396, 566, 9)), lambda x: 198, (10, 70), sc.col("leaf3", 0.3), sc.col("leaf2", 0.3),
                  flower=p["pink"], glow_tip=RUNE))
    # near: a flagstone court in the grass, a fallen column, the path back down to the Forest
    lay = art.plane()
    art.ridge(lay, rng, 430, 8, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    art.grass_bed(lay, rng, (0, 430, W, 110), sc.col("leaf", 0.18), 1500, 6)
    for _ in range(40):  # flagstones peeping through the grass
        x, y = rng.randint(200, 760), rng.randint(440, 530)
        pygame.draw.rect(lay, mix(sc.col("stone", 0.2), (0, 0, 0), rng.uniform(0, 0.2)), (x, y, rng.randint(14, 26), 6))
    art.flowers(lay, rng, (0, 440, W, 100), p["flowers"], 60)
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(480, 400), (478, 460), (470, 520), (466, 560)], [20, 40, 70, 100], earth, edge, rng=rng)
    sc.add(lay, 0.2, texture=0.6)
    lay = art.plane()
    near = []
    pillar(sc, lay, 120, 520, 150, 34, sc.col("stone", 0.12), near)
    pygame.draw.rect(lay, sc.col("stone", 0.14), (640, 490, 170, 26), border_radius=8)  # the fallen one
    for k in range(660, 800, 22):
        pygame.draw.line(lay, mix(sc.col("stone", 0.14), (0, 0, 0), 0.3), (k, 490), (k, 515))
    pygame.draw.ellipse(lay, sc.col("moss", 0.12), (650, 484, 140, 10))
    glowmoss(sc, lay, 720, 486, 80, 8, GLOW["moss"], strength=50)
    sc.add(lay, 0.12, texture=0.8)
    sc.live(Pulses(glows + near, speed=0.5))
    sc.live(Blades(rng, (0, 426, W, 114), 360, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1)], 8, 26))
    sc.live(Motes(rng, (0, 100, W, 400), 50, RUNE, rise=-4))
    sc.live(Slug(rng, Track([(730, 486), (680, 488), (650, 486)]), (180, 170, 230), size=1.3, speed=2, spots=RUNE))
    additions(sc, rng, [("cairn", 300, 500), ("ring", 860, 500)])
    grounds = [(lambda x: 476 + 3 * math.sin(x / 40), (200, 420)), (lambda x: 512 + 3 * math.sin(x / 50), (540, 860)),
               (lambda x: 470 + 2 * math.sin(x / 60), (560, 760))]
    second_wave(sc, rng, (100, 80, 760, 200), grounds, fliers=("sigil", "echo", "umbra", "bat"),
                walkers=("rune", "glint", "rubble", "slate", "quill", "pebble"), out=("rune", "slate", "sigil", "bat"),
                far=[(lambda x: 360 + 0 * x, (40, 360)), (lambda x: 362 + 0 * x, (600, 920))])
    bugs = sc.live(Fireflies(rng, (0, 180, W, 300), 36, color=RUNE, reach=24))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 60, 700, 180), [RUNE, GLOW["pink"]])
    front_frame(sc, rng, top=False)

    sc.spots = [Spot("go", (392, 480, 168, 60), "Back to the Forest", "forest", (470, 516), sign=(470, 504))]
    sc.lower = dict(ground=0.18, props=["rocks"], fly=RUNE, walkers=("rune", "glint", "rubble", "slate"),
                    fliers=("sigil", "bat"), out=("rune", "sigil"))
    return sc.done()


# --- The Cloud Bridge (above the Crystal Caverns) ----------------------------------------------

def bridge_y(x):
    """The deck of the rope bridge: it sags in the middle."""
    return 330 + 34 * math.sin(math.pi * min(1, max(0, (x - 150) / 660)))


def build_bridge():
    rng = make_rng(74)
    p = pal(sky=[(6, 6, 28), (16, 14, 60), (36, 30, 100), (70, 60, 150)],
            mist=(130, 120, 200), shade=(10, 10, 36), ambient=((240, 236, 255), (100, 96, 170)),
            leaf=(110, 180, 170), leaf2=(140, 200, 180), leaf3=(70, 120, 140), stone=(130, 120, 190),
            wood=(150, 110, 130), flowers=[(255, 255, 255), (200, 220, 255), (255, 210, 240)])
    sc = Scene("bridge", "The Cloud Bridge", p, rng)
    sc.live(Stars(rng, 380, 300))
    moon(sc, 800, 70, 24)
    # the sea of cloud, far below, in soft rolling banks
    for d, y0, c in ((0.9, 300, 0.75), (0.7, 360, 0.6), (0.5, 420, 0.45)):
        lay = art.plane()
        col = mix(CLOUD, p["sky"][1], c)
        for _ in range(26):
            x, r = rng.randint(-40, W + 40), rng.randint(30, 70)
            pygame.draw.circle(lay, col, (x, y0 + rng.randint(-10, 10)), r)
        pygame.draw.rect(lay, col, (0, y0, W, H - y0))
        sc.add(lay, d, veil=0.03)
    sc.lamp(800, 300, 240, (200, 200, 255), 40)  # moonlight on the clouds
    # floating rocks with glowing moss and little falls of mist off them
    glows = []
    lay = art.plane()
    for x, y, w in ((140, 150, 60), (620, 200, 44), (880, 230, 36), (360, 120, 30)):
        pts = [(x - w, y), (x + w, y), (x + w * 0.5, y + w * 0.6), (x, y + w * 1.1), (x - w * 0.4, y + w * 0.7)]
        art.crag(lay, pts, sc.col("stone", 0.6), x, side=p["moon_side"], strata=(5, 9))
        pygame.draw.ellipse(lay, sc.col("leaf2", 0.55), (x - w, y - 6, w * 2, 12))
        glows.append((x, y - 4, w * 2, GLOW["moss"], 60, x * 0.03))
    sc.add(lay, 0.6, veil=0.03)
    sc.live(Steam(rng, [(140 + 40, 190, 20), (620, 240, 14)], n_each=3, color=CLOUD, height=50))
    # the cliffs either side and the rope bridge slung between them, its lanterns lit
    lay = art.plane()
    art.crag(lay, [(0, 300), (130, 290), (170, 330), (190, 540), (0, 540)], sc.col("stone", 0.3), 75, side=p["moon_side"])
    art.crag(lay, [(W, 290), (820, 300), (790, 340), (770, 540), (W, 540)], sc.col("stone", 0.3), 76, side=p["moon_side"])
    rope, plank = (140, 110, 120), sc.col("wood", 0.3)
    for x in range(150, 811, 6):
        y = bridge_y(x)
        pygame.draw.rect(lay, plank if (x // 6) % 2 else mix(plank, (0, 0, 0), 0.15), (x, y - 2, 5, 4))
    for off in (-26, -12):
        pts = [(x, bridge_y(x) + off + 6 * math.sin(math.pi * (x - 150) / 660)) for x in range(150, 811, 10)]
        pygame.draw.lines(lay, rope, False, pts)
    for x in range(160, 811, 20):
        pygame.draw.line(lay, rope, (x, bridge_y(x) - 2), (x, bridge_y(x) - 26 + 6 * math.sin(math.pi * (x - 150) / 660)))
    for x in (150, 810):
        pygame.draw.rect(lay, sc.col("wood", 0.25), (x - 4, bridge_y(x) - 40, 8, 44))
        pygame.draw.rect(lay, (255, 220, 150), (x - 4, bridge_y(x) - 52, 8, 10))
        sc.lamp(x, bridge_y(x) - 48, 90, GLOW["amber"], 80)
        glows.append((x, bridge_y(x) - 48, 40, GLOW["amber"], 60, x))
    for x in (320, 480, 640):  # paper lanterns hung under the hand-rope
        y = bridge_y(x) - 22
        pygame.draw.circle(lay, (255, 190, 220), (x, y + 6), 4)
        sc.lamp(x, y + 6, 50, (255, 170, 210), 50)
        glows.append((x, y + 6, 26, (255, 170, 210), 70, x))
    sc.add(lay, 0.3, texture=0.5)
    sc.live(Pulses(glows, speed=0.8))
    # near: the cliff-top ledge we stand on, grass and flowers, steps back down to the Caverns
    lay = art.plane()
    art.ridge(lay, rng, 456, 10, sc.col("leaf2", 0.18), scales=(140, 40, 14))
    art.grass_bed(lay, rng, (0, 456, W, 84), sc.col("leaf", 0.16), 1100, 6)
    art.flowers(lay, rng, (0, 470, W, 70), p["flowers"], 60)
    stone = sc.col("stone", 0.16)
    for i in range(5):  # stone steps going down out of the picture
        pygame.draw.rect(lay, mix(stone, (255, 255, 255), 0.06 * (i % 2)), (420 - i * 6, 480 + i * 12, 120 + i * 12, 10))
    art.forget_paths()
    sc.add(lay, 0.18, texture=0.6)
    sc.live(Blades(rng, (0, 452, W, 88), 260, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 10, 28, stiff=1.4))
    sc.live(Motes(rng, (0, 260, W, 200), 50, (230, 230, 255), rise=-3))
    grounds = [(bridge_y, (190, 770)), (lambda x: 500 + 3 * math.sin(x / 50), (80, 380)),
               (lambda x: 506 + 3 * math.sin(x / 40), (580, 880))]
    second_wave(sc, rng, (100, 60, 760, 200), grounds, fliers=("breeze", "wish", "dream", "drake", "finch", "mistm"),
                walkers=("tuft", "pom", "kick", "goat"), out=("tuft", "goat", "breeze", "wish"),
                far=[(lambda x: 304 + 0 * x, (20, 120)), (lambda x: 304 + 0 * x, (840, 940))])
    bugs = sc.live(Fireflies(rng, (0, 200, W, 260), 30, color=(255, 236, 200), reach=22))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 60, 700, 200), [GLOW["violet"], GLOW["white"]])
    front_frame(sc, rng, top=False)

    sc.spots = [Spot("go", (392, 480, 168, 60), "Back to the Caverns", "caverns", (476, 516), sign=(476, 504))]
    sc.lower = dict(ground=0.18, props=["rocks"], fly=(255, 236, 200), walkers=("tuft", "pom", "goat"),
                    fliers=("breeze", "wish"), out=("tuft", "breeze"))
    return sc.done()


# --- The Glow Shore (past the Hot Springs) --------------------------------------------------------

def build_shore():
    rng = make_rng(75)
    p = pal(sky=[(6, 10, 30), (14, 24, 60), (30, 44, 96), (60, 70, 130)],
            mist=(70, 90, 150), shade=(8, 12, 34), ambient=((226, 240, 255), (70, 90, 140)),
            leaf=(110, 170, 150), leaf2=(214, 196, 200), leaf3=(60, 110, 130), water=(40, 90, 150),
            earth=(220, 200, 210), earth_edge=(150, 124, 150), stone=(110, 110, 160), moon_side=1,
            flowers=[(255, 236, 200), (200, 255, 240), (255, 200, 230)])
    sc = Scene("shore", "The Glow Shore", p, rng)
    sc.live(Stars(rng, 260, 250))
    moon(sc, 620, 90, 20)
    # the sea, out to the horizon, with the moon's path across it
    sea = sc.col("water", 0.6)
    lay = art.plane()
    art.gradient(lay, (0, 260, W, 200), [mix(sea, p["sky"][3], 0.4), sea, sc.col("water", 0.35)], steps=6)
    for i in range(40):
        y = 264 + int(i ** 1.4)
        if y > 440:
            break
        w = 6 + i * 2
        pygame.draw.line(lay, mix(sea, (230, 236, 255), 0.4), (620 - w + rng.randint(-4, 4), y), (620 + w // 2, y))
    art.crag(lay, [(780, 262), (830, 230), (870, 236), (900, 262)], sc.col("stone", 0.8), 77, side=1)  # a far sea-stack
    sc.add(lay, 0.6, veil=0.02, texture=0.3)
    sc.live(River(rng, lambda x: 300, lambda x: 420, (0, W), 120, mix(sea, (255, 255, 255), 0.35), (220, 255, 250),
                  speed=6, sparks=SEA))
    # the surf line: waves breaking blue-green with light (sea sparkle), pulsing
    surf = []
    lay = art.plane()
    for x in range(0, W + 1, 4):
        y = 432 + 6 * math.sin(x / 50) + 3 * math.sin(x / 13)
        pygame.draw.line(lay, mix(SEA, (255, 255, 255), 0.3), (x, y), (x + 4, y + 1), 2)
        if x % 40 == 0:
            surf.append((x, int(y), 60, SEA, 60, x * 0.02))
        sc.emit.set_at((min(W - 1, x), int(y)), art.scale(SEA, 0.5))
    sc.add(lay, 0.3, texture=0)
    sc.live(Pulses(surf, speed=0.9))
    # near: pale sand, rocks with tide pools full of light, the path back to the Springs
    lay = art.plane()
    sand = sc.col("leaf2", 0.2)
    pygame.draw.polygon(lay, sand, [(0, 440)] + [(x, 440 + 6 * math.sin(x / 50) + 3 * math.sin(x / 13)) for x in range(0, W + 1, 8)]
                        + [(W, H), (0, H)])
    for _ in range(1600):
        x, y = rng.randrange(W), rng.randint(446, H - 1)
        lay.set_at((x, y), mix(sand, (255, 255, 255), rng.uniform(-0.1, 0.25)) if rng.random() < 0.7 else mix(sand, (60, 40, 80), 0.2))
    earth, edge = sc.col("earth", 0.16), sc.col("earth_edge", 0.16)
    art.path(lay, [(-24, 490), (120, 486), (260, 478), (340, 472)], [44, 40, 30, 16], earth, edge, rng=rng)
    sc.add(lay, 0.18, texture=0.4)
    lay = art.plane()
    pools = []
    for x, y, w, h in ((640, 500, 110, 40), (860, 480, 80, 50), (420, 520, 70, 26)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.16), moss=sc.col("leaf", 0.12), mossiness=0.4)
    for x, y, w in ((560, 520, 60), (760, 506, 50), (300, 520, 40)):
        pygame.draw.ellipse(lay, mix(SEA, (20, 40, 70), 0.55), (x - w // 2, y - 6, w, 14))
        pygame.draw.ellipse(lay, mix(SEA, (255, 255, 255), 0.2), (x - w // 3, y - 3, w * 2 // 3, 6), 1)
        pools.append((x, y, w + 30, SEA, 80, x * 0.1))
        for _ in range(4):
            sx, sy = x + rng.randint(-w // 3, w // 3), y + rng.randint(-2, 3)
            pygame.draw.circle(lay, rng.choice([(255, 150, 200), (255, 220, 140), (180, 160, 255)]), (sx, sy), 1)
    sc.add(lay, 0.14, texture=0.6)
    sc.live(Pulses(pools, speed=0.5))
    sc.pond = sc.live(Shoal(rng, [(Water(620, 380, 220, 20), 3), (Water(560, 520, 26, 4), 1)], sea, size=0.6))
    sc.live(Motes(rng, (0, 300, W, 200), 50, SEA, rise=-3))
    sc.live(Slug(rng, Track([(80, 520), (180, 524), (260, 520)]), (255, 200, 220), size=1.4, speed=3, spots=SEA))
    additions(sc, rng, [("lotus", 300, 400), ("cairn", 860, 520)])
    grounds = [(lambda x: 488 + 3 * math.sin(x / 40), (60, 300)), (lambda x: 512 + 2 * math.sin(x / 50), (380, 860)),
               (lambda x: 470 + 2 * math.sin(x / 60), (420, 760))]
    second_wave(sc, rng, (100, 80, 760, 180), grounds, fliers=("jelly", "foam", "dew", "bubbl"),
                walkers=("glint", "ripple", "splash", "murk", "capy"), out=("glint", "ripple", "jelly", "foam"),
                far=[(lambda x: 452 + 2 * math.sin(x / 40), (40, 420)), (lambda x: 454 + 2 * math.sin(x / 50), (500, 920))])
    bugs = sc.live(Fireflies(rng, (0, 260, W, 200), 20, color=SEA, reach=22))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 80, 700, 180), [SEA, GLOW["pink"]])
    front_frame(sc, rng, top=False, left=False)

    sc.spots = [Spot("go", (0, 440, 88, 80), "Back to the Hot Springs", "springs", (30, 484), sign=(122, 436))]
    sc.lower = dict(ground=0.16, props=["rocks"], fly=SEA, bushes=False,
                    walkers=("glint", "ripple", "splash", "murk"), fliers=("jelly", "foam"), out=("glint", "jelly"))
    return sc.done()


BUILD = dict(hollow=build_hollow, bog=build_bog, ruins=build_ruins, bridge=build_bridge, shore=build_shore)
