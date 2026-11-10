"""The desktop's home, seen from above (2026-11-10, his ask).

"I'd like the main glade screen to be a more zoomed out, slightly angled, aerial view, in high
detail (not more pixels, attention to detail) showing the main glade area in the centre and then
some of the areas around it." So the desktop's top screen is the Glade from high up and a little
behind, looking north: the clearing in the middle with its blossom tree, the Waterfall's cliff right
behind it, the Forest's crowns to the left, the River winding off to the right, the Mossy Rocks at
the front edge; and further out, small in the night mist (his pick), the Crystal Caverns, the Snowy
Ridge, the Old Ruins, the Starfall Meadow and the Hot Springs. Tall trees line both edges, holding
the tree squid and owls. Each place has a name board; clicking it opens a small live look at it
(peek.py), and the mouse wheel zooms (desktop.Camera).

Only the desktop uses this (desktop.Desktop.builder); the game keeps scenes.build_glade. The same
animals live here as there, made in the same order, so carry.py hands them across one for one. The
lower screen is the Glade's as before (the same `sc.lower`).
"""

import math

import pygame

import art
from art import GLOW, H, W, mix
from life import (Aurora, Blades, Critter, Fireflies, Lantern, Motes, Petals, Pulses, River, Shafts, Slug, Stars,
                  Steam, Track, Vines, Waterfall, make_rng)
from orchard import Nibbler, Orchard
from scenes import (CAVE_CRYSTAL, SPRING, FallingStars, Scene, Spot, additions, crystal, leaf_row, moss_glow,
                    mushroom, pal, second_wave, snowcaps)  # noqa: F401
from squids import Colony

CLEAR = (488, 404)  # the middle of the clearing, where the paths meet


def high(y):
    """How big something standing at y looks from up here: small far back, never as big as in the
    old close-up (it is all further away now)."""
    return max(0.42, min(0.86, 0.3 + 0.56 * (y - 300) / 220))


def tops_of(lay, x0, x1):
    """The highest painted pixel of each column (for snow on the peaks)."""
    out = []
    for x in range(0, W):
        y = H
        if x0 <= x < x1:
            for yy in range(0, H):
                if lay.get_at((x, yy))[3]:
                    y = yy
                    break
        out.append(y)
    return out


def eye():
    """The little eye on each place's board: click for a look."""
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (236, 255, 246), (0, 3, 14, 8))
    pygame.draw.ellipse(s, (40, 90, 96), (0, 3, 14, 8), 1)
    pygame.draw.circle(s, (60, 170, 150), (7, 7), 3)
    pygame.draw.circle(s, (20, 40, 60), (7, 7), 1)
    s.set_at((8, 6), (255, 255, 255))
    return s


POND = (214, 420, 34, 11)  # the little lily pond in the grass (cx, cy, rx, ry)
LANTERNS = ((436, 456), (566, 398), (322, 384), (690, 432))


def meadow_life(sc, p, glows):
    """The clearing's grass filled in (2026-11-10, his ask: "the new grass space feels a little
    empty"; his picks: plants and glow, and small places). Its own dice, so the rest of the
    picture and the animals are just as they were."""
    rng = make_rng(12)
    d = 0.22
    lay = art.plane()
    # a little lily pond, with a rim of stones and reeds
    cx, cy, rx, ry = POND
    water = mix(sc.col("water", d), (40, 70, 160), 0.25)
    pygame.draw.ellipse(lay, sc.col("stone", d), (cx - rx - 3, cy - ry - 2, rx * 2 + 6, ry * 2 + 5))
    pygame.draw.ellipse(lay, water, (cx - rx, cy - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(lay, mix(water, (255, 255, 255), 0.35), (cx - rx + 8, cy - ry + 3, rx, ry), 1)
    for a in range(0, 360, 30):  # rim stones
        x = cx + math.cos(math.radians(a)) * (rx + 2)
        y = cy + math.sin(math.radians(a)) * (ry + 1)
        pygame.draw.ellipse(lay, mix(sc.col("stone", d), (236, 228, 255), 0.15 + 0.1 * (a % 60 == 0)),
                            (round(x) - 3, round(y) - 2, 6, 4))
    for x, y in ((cx - 14, cy - 2), (cx + 10, cy + 3), (cx + 20, cy - 4)):  # lily pads and lotuses
        pygame.draw.ellipse(lay, sc.col("leaf", d), (x - 4, y - 1, 9, 4))
        pygame.draw.circle(lay, (255, 200, 238), (x, y - 1), 1)
        glows.append((x, y - 1, 14, GLOW["pink"], 70, x * 0.1))
    for x in (cx - rx - 2, cx - rx + 4, cx + rx - 4, cx + rx + 1):  # reeds
        for k in range(3):
            pygame.draw.line(lay, sc.col("leaf2", d), (x + k * 2, cy + 2), (x + k * 2 + k - 1, cy - 8 - (x + k) % 5))
    sc.add(lay, d, texture=0.3)
    sc.lamp(cx, cy, 60, GLOW["cyan"], 40)
    sc.shine(cx, cy, 5, GLOW["cyan"], 40)
    glows.append((cx, cy, rx, GLOW["cyan"], 50, 1.3))

    lay = art.plane()
    # wildflower patches that glow, all over the grass
    for rect in ((112, 386, 130, 40), (270, 450, 90, 40), (452, 470, 140, 44), (640, 396, 90, 26),
                 (500, 420, 70, 26), (120, 470, 80, 20)):
        art.flowers(lay, rng, rect, p["flowers"], rect[2] * rect[3] // 30)
        for _ in range(rect[2] // 10):
            x, y = rng.randint(rect[0], rect[0] + rect[2]), rng.randint(rect[1], rect[1] + rect[3])
            c = rng.choice((GLOW["pink"], GLOW["cyan"], GLOW["violet"], (255, 246, 200)))
            lay.set_at((x, y), c)
            glows.append((x, y, 12, c, 70, x * 0.13 + y))
    # tall grass tufts
    for _ in range(46):
        x, y = rng.randint(100, 740), rng.randint(380, 528)
        if abs(x - POND[0]) < 44 and abs(y - POND[1]) < 18:
            continue
        for k in range(rng.randint(4, 7)):
            ln = rng.randint(5, 10)
            pygame.draw.line(lay, sc.col(rng.choice(("leaf", "leaf2")), 0.16),
                             (x + k, y), (x + k + rng.randint(-3, 3), y - ln))
    # little round bushes with glowing berries
    for x, y, r in ((150, 404, 9), (286, 418, 8), (700, 452, 9), (530, 512, 8), (380, 466, 7)):
        pygame.draw.ellipse(lay, mix(sc.col("leaf", d), (0, 0, 0), 0.3), (x - r, y - r // 2, r * 2, r))
        art.foliage(lay, rng, x, y - r // 2, r, r * 0.7, sc.col("leaf", d), p, leaf=(2, 3))
        for _ in range(4):
            bx, by = x + rng.randint(-r + 2, r - 2), y - rng.randint(1, r)
            lay.set_at((bx, by), GLOW["violet"])
            glows.append((bx, by, 10, GLOW["violet"], 80, bx * 0.2))
        sc.shadow(x, y + 1, r, 3, 0.35)
    # mossy stepping stones from the pond toward the forest path, and a ring of little standing stones
    for i, (x, y) in enumerate(((250, 412), (266, 404), (282, 398), (296, 390))):
        pygame.draw.ellipse(lay, sc.col("stone", d), (x - 4, y - 2, 8, 4))
        pygame.draw.line(lay, sc.col("moss", d), (x - 2, y - 2), (x + 2, y - 2))
    for k in range(6):
        a = k * math.pi / 3
        x, y = round(640 + math.cos(a) * 18), round(500 + math.sin(a) * 6)
        pygame.draw.rect(lay, sc.col("stone", 0.18), (x - 1, y - 6, 3, 6))
        lay.set_at((x, y - 6), GLOW["cyan"])
        glows.append((x, y - 6, 10, GLOW["cyan"], 60, k))
    # fallen petals under the blossom tree
    for _ in range(90):
        x, y = rng.randint(540, 680), rng.randint(438, 468)
        lay.set_at((x, y), rng.choice(((255, 200, 230), (255, 236, 246), (255, 150, 200))))
    sc.add(lay, 0.18, texture=0.4)
    lay = art.plane()
    # glowing mushroom clusters
    for x, y, size, cap in ((180, 446, 3, GLOW["cyan"]), (186, 450, 2, GLOW["cyan"]), (262, 394, 3, GLOW["amber"]),
                            (520, 456, 3, GLOW["pink"]), (527, 460, 2, GLOW["pink"]), (676, 392, 3, GLOW["lime"]),
                            (470, 518, 3, GLOW["violet"]), (476, 521, 2, GLOW["violet"]), (120, 430, 2, GLOW["lime"]),
                            (306, 506, 3, GLOW["cyan"]), (726, 404, 2, GLOW["pink"])):
        mushroom(lay, x, y, size, cap, sc, glows)
    # lantern posts by the paths
    for x, y in LANTERNS:
        pygame.draw.line(lay, sc.col("wood", 0.16), (x, y), (x, y - 16), 2)
        pygame.draw.line(lay, sc.col("wood", 0.16), (x, y - 16), (x + 4, y - 16))
        pygame.draw.rect(lay, sc.col("wood", 0.1), (x + 2, y - 15, 5, 6))
        pygame.draw.rect(lay, (255, 236, 170), (x + 3, y - 14, 3, 4))
        sc.lamp(x + 4, y - 12, 60, GLOW["amber"], 50)
        sc.shine(x + 4, y - 12, 3, GLOW["amber"], 80)
        glows.append((x + 4, y - 12, 18, GLOW["amber"], 60, x * 0.05))
        sc.shadow(x, y + 1, 4, 2, 0.4)
    # tall glow-bulb plants: a curling stem with a luminous bulb, in little groups
    for gx, gy, c in ((140, 444, GLOW["cyan"]), (346, 410, GLOW["pink"]), (596, 500, GLOW["lime"]),
                      (712, 486, GLOW["violet"]), (254, 500, GLOW["amber"]), (520, 398, GLOW["cyan"])):
        for k in range(3):
            x, y = gx + k * 5 - 5, gy + (k % 2) * 3
            h = 10 + (k * 7) % 6
            lean = (k - 1) * 2
            pygame.draw.line(lay, sc.col("leaf2", 0.16), (x, y), (x + lean, y - h))
            pygame.draw.line(lay, sc.col("leaf", 0.16), (x, y - 3), (x - 3, y - 5))
            pygame.draw.circle(lay, c, (x + lean, y - h - 1), 2)
            lay.set_at((x + lean, y - h - 2), (255, 255, 255))
            glows.append((x + lean, y - h - 1, 18, c, 90, gx * 0.1 + k))
        sc.lamp(gx, gy - 12, 44, c, 40)
    sc.add(lay, 0.16)
    for x, y, w, h, c in ((150, 492, 30, 6, GLOW["cyan"]), (680, 470, 26, 6, None), (250, 476, 24, 5, GLOW["lime"]),
                          (540, 430, 22, 5, None)):
        art.glowmoss(sc, sc.cur, x, y, w, h, c)


def ground(sc):
    """Where its animals may walk (walk.py): the clearing's grass, not the River, the pond, the
    tree, the stones, nor the corner the minimap covers."""
    from walk import drawn, oval
    edge = [(96, 384), (200, 378), (340, 372), (380, 352), (420, 334), (450, 328), (536, 328), (560, 336),
            (600, 340), (700, 352), (748, 362), (748, 532), (96, 532)]
    holes = [oval(*POND[:2], POND[2] + 6, POND[3] + 5), (530, 296, 150, 96), (592, 392, 26, 46),
             oval(400, 412, 16, 10), (726, 444, 22, 16)]
    for x, y, w, h in ((330, 436, 28, 12), (620, 446, 34, 14), (566, 372, 18, 8), (360, 376, 16, 7)):
        holes.append(oval(x, y - h // 3, w // 2 + 3, h // 2 + 3))
    for x, y, w, h in ((218, 520, 70, 30), (160, 532, 50, 22), (286, 534, 44, 18), (452, 530, 50, 20),
                       (110, 500, 30, 14), (512, 536, 38, 14)):
        holes.append(oval(x, y - h // 3, w // 2 + 2, h // 2 + 2))
    holes += [oval(x, y, 6, 4) for x, y in LANTERNS]
    sc.field = drawn([edge], holes)


def build_aerial():
    rng = make_rng(11)
    p = pal(sky=[(8, 10, 38), (20, 20, 66), (42, 36, 100), (78, 60, 134)],
            mist=(80, 70, 140), shade=(14, 12, 42), ambient=((230, 232, 255), (80, 80, 142)))
    sc = Scene("glade", "The Glade", p, rng)
    # (set before the trees' squid are made: where new trees grow, and the seed sign, squids.py)
    sc.grow_at = [(842, 150, 500), (806, 178, 506)]
    sc.seed = (150, 508)
    glows = []
    sc.live(Stars(rng, 260, 120, avoid=lambda x, y: 330 < x < 620 and y > 60))
    sc.live(Aurora(rng, 0, 110, [((120, 255, 190), (110, 210, 255)), ((190, 140, 255), (255, 150, 220))]))
    # the moon, small and high: it is not the light here
    pygame.draw.circle(sc.cur, (226, 228, 255), (700, 30), 9)
    pygame.draw.circle(sc.cur, (200, 204, 246), (697, 28), 9)
    pygame.draw.circle(sc.cur, (236, 238, 255), (703, 31), 7)
    sc.moon = (700, 30, 9)
    sc.lamp(700, 30, 40, (190, 196, 255), 16)

    # --- the furthest ring, in the night mist --------------------------------------------------
    lay = art.plane()
    art.mountains(lay, rng, 112, 26, sc.col("lav", 0.96), scales=(160, 50, 16), side=p["moon_side"])
    sc.add(lay, 0.96, veil=0.06)

    # the Snowy Ridge, far left: white peaks, pines, a frozen lake
    lay = art.plane()
    art.crag(lay, [(-10, 200), (-10, 120), (30, 84), (58, 100), (96, 60), (130, 92), (160, 78), (204, 116),
                   (236, 132), (250, 200)], sc.col("stone", 0.86), 301, side=p["moon_side"], strata=(5, 10))
    tops = tops_of(lay, 0, 250)
    snowcaps(lay, tops, mix(sc.col("stone", 0.86), (240, 246, 255), 0.75), 150, rng)
    for x in range(8, 236, 9):
        base = 176 + int(6 * math.sin(x / 17))
        art.pine(lay, rng, x, base, rng.randint(12, 22), sc.col("leaf3", 0.84), snow=(226, 236, 255))
    pygame.draw.ellipse(lay, (150, 190, 236), (66, 172, 92, 14))
    pygame.draw.ellipse(lay, (196, 222, 255), (80, 175, 40, 5))
    sc.add(lay, 0.84, veil=0.08)
    sc.lamp(110, 178, 50, (170, 220, 255), 22)
    ice = (150, 230, 255)
    for x, y in ((48, 172), (178, 176)):
        for k in range(3):
            pygame.draw.line(sc.cur, ice, (x + k * 3, y), (x + k * 3 + 1, y - 5 - k * 2))
        glows.append((x, y - 4, 26, ice, 70, x * 0.1))

    # the Hot Springs, far right: a sleeping volcano, embers, turquoise terraces and steam
    lay = art.plane()
    art.crag(lay, [(740, 200), (790, 140), (836, 84), (856, 78), (880, 80), (902, 88), (930, 128), (980, 170),
                   (980, 200)], sc.col("stone", 0.86), 302, side=p["moon_side"], strata=(5, 9))
    pygame.draw.ellipse(lay, (255, 150, 110), (846, 76, 40, 8))
    pygame.draw.ellipse(lay, (255, 210, 150), (856, 77, 20, 4))
    for x0, y0, x1, y1 in ((862, 84, 850, 118), (872, 84, 884, 112)):  # cooling lava runs, faint
        pygame.draw.line(lay, (200, 90, 110), (x0, y0), (x1, y1), 2)
    sc.add(lay, 0.86, veil=0.06)
    sc.lamp(864, 80, 60, (255, 140, 110), 40)
    sc.shine(864, 80, 10, (255, 170, 130), 60)
    lay = art.plane()
    steam = []
    for cx, y, w in ((812, 176, 36), (850, 186, 44), (900, 180, 40), (938, 190, 34)):
        rim = (226, 214, 238)
        pygame.draw.ellipse(lay, mix(rim, (60, 30, 70), 0.35), (cx - w // 2 - 2, y - 3, w + 4, 11))
        pygame.draw.ellipse(lay, rim, (cx - w // 2 - 2, y - 4, w + 4, 10))
        pygame.draw.ellipse(lay, SPRING, (cx - w // 2 + 2, y - 2, w - 4, 6))
        pygame.draw.line(lay, mix(SPRING, (255, 255, 255), 0.5), (cx - w // 4, y - 1), (cx + w // 6, y - 1))
        glows.append((cx, y, w, SPRING, 60, cx * 0.05))
        steam.append((cx, y - 2, w * 0.5))
    sc.add(lay, 0.74, veil=0.03)
    sc.live(Steam(rng, steam, n_each=3, color=(220, 210, 246), height=60))

    # the Crystal Caverns, far centre: a great crag with a cave mouth full of glowing crystal
    lay = art.plane()
    art.crag(lay, [(360, 230), (380, 140), (414, 96), (452, 76), (500, 70), (546, 84), (584, 120), (612, 170),
                   (624, 230)], sc.col("stone", 0.8), 303, side=p["moon_side"], strata=(6, 12))
    pygame.draw.ellipse(lay, sc.col("shade", 0.5), (468, 106, 46, 34))
    pygame.draw.ellipse(lay, (24, 16, 52), (472, 110, 38, 28))
    sc.add(lay, 0.8, veil=0.05)
    lay = art.plane()
    for i, (x, h, lean) in enumerate(((478, 14, -0.3), (486, 22, 0.1), (494, 17, 0.2), (502, 12, 0.4),
                                      (420, 10, -0.2), (560, 12, 0.3), (548, 8, -0.1))):
        crystal(lay, x, 138 if i < 4 else 160 + i, h, 3 + h // 7, CAVE_CRYSTAL[i % 3], lean)
    sc.raw(lay)
    for x, y, c in ((490, 126, CAVE_CRYSTAL[0]), (420, 156, CAVE_CRYSTAL[1]), (560, 160, CAVE_CRYSTAL[2])):
        sc.lamp(x, y, 46, c, 54)
        sc.shine(x, y, 5, c, 50)
        glows.append((x, y, 34, c, 80, x * 0.07))

    # the Old Ruins, far left of centre: broken arches of pale stone among the trees
    lay = art.plane()
    art.canopy(lay, rng, 210, 370, 206, sc.col("leaf3", 0.78), r=(8, 14))
    stone = mix(sc.col("stone", 0.76), (236, 228, 255), 0.2)
    for x, h, arch in ((250, 40, True), (300, 34, True), (346, 20, False)):
        pygame.draw.rect(lay, stone, (x, 196 - h, 7, h))
        pygame.draw.rect(lay, stone, (x + 30, 196 - h + 6, 7, h - 6))
        if arch:
            pygame.draw.arc(lay, stone, (x, 196 - h - 14, 37, 30), 0.15, math.pi - 0.1, 5)
        pygame.draw.line(lay, mix(stone, (255, 255, 255), 0.4), (x, 196 - h), (x, 196))
    for x in (258, 316):  # a fallen block, and moss on the stones
        pygame.draw.rect(lay, stone, (x, 192, 14, 6))
    sc.add(lay, 0.76, veil=0.05)
    for x, y in ((268, 172), (318, 178)):
        sc.lamp(x, y, 30, GLOW["moss"], 30)
        glows.append((x, y, 18, GLOW["moss"], 60, x * 0.1))
    sc.lamp(284, 166, 26, (255, 214, 140), 30)  # a rune that still glows
    sc.shine(284, 166, 3, (255, 224, 160), 80)

    # the Starfall Meadow, far right of centre: a pale field under falling stars
    lay = art.plane()
    art.ridge(lay, rng, 196, 8, sc.col("lav", 0.74), scales=(80, 26, 10), bottom=226)
    art.flowers(lay, rng, (620, 186, 150, 30), [(255, 246, 200), (220, 210, 255), (255, 200, 240)], 70)
    sc.add(lay, 0.74, veil=0.03)
    for x in range(630, 770, 22):
        glows.append((x, 196 + (x * 7) % 12, 14, (255, 246, 200), 50, x * 0.13))
    sc.live(FallingStars(rng))

    # --- the land in between --------------------------------------------------------------------
    lay = art.plane()
    art.ridge(lay, rng, 206, 8, sc.col("leaf3", 0.72), scales=(140, 40, 14))
    art.canopy(lay, rng, -10, 980, 212, sc.col("leaf3", 0.72), r=(5, 10))
    for x in (150, 214, 378, 612, 742, 790):  # tall far trees, Rain World-ish verticals
        art.trunk(lay, rng, x, 168, 214, 3, sc.col("leaf3", 0.72), branches=1)
        art.foliage(lay, rng, x, 172, 8, 18, sc.col("leaf3", 0.72), p, leaf=(2, 4))
    sc.add(lay, 0.72, veil=0.06, low=0.1)
    lay = art.plane()
    art.ridge(lay, rng, 238, 10, sc.col("leaf3", 0.62), scales=(120, 36, 12))
    art.canopy(lay, rng, 560, 980, 244, sc.col("leaf", 0.62), r=(6, 12))
    sc.add(lay, 0.62, veil=0.04, low=0.12)
    for x, y in ((130, 226), (330, 222), (640, 236), (820, 240), (720, 252)):  # far moss glowing through the mist
        sc.lamp(x, y, 50, GLOW["moss"], 22)

    # the Waterfall, right behind the clearing: a mossy cliff, the falls, the pool
    lay = art.plane()
    cliff = [(388, 326), (394, 286), (404, 256), (418, 232), (434, 216), (452, 206), (470, 200), (488, 197),
             (508, 196), (526, 200), (542, 208), (558, 222), (572, 242), (582, 268), (590, 298), (596, 326)]
    art.crag(lay, cliff, sc.col("stone", 0.56), 304, side=p["moon_side"], strata=(5, 10))
    for x, y, rx, ry in ((440, 212, 16, 8), (470, 200, 14, 6), (520, 199, 16, 6), (552, 214, 16, 8),
                         (404, 262, 12, 16), (582, 272, 12, 18), (398, 306, 16, 18), (590, 306, 16, 18)):
        art.foliage(lay, rng, x, y, rx, ry, sc.col("leaf", 0.56), p, leaf=(2, 4))
    sc.add(lay, 0.56, veil=0.03)
    lay = art.plane()  # vines down the cliff face, and moss that glows on its ledges
    for x in range(424, 566, 7):
        if 474 <= x <= 506:
            continue
        y0 = 210 + abs(x - 490) // 5
        ln = 8 + (x * 13) % 22
        pygame.draw.line(lay, sc.col("leaf2", 0.5), (x, y0), (x + (x % 3) - 1, y0 + ln))
        if x % 2:
            lay.set_at((x + (x % 3) - 1, y0 + ln), GLOW["cyan"])
    sc.raw(lay)
    for x, y in ((432, 250), (556, 254), (420, 288), (566, 292)):
        art.glowmoss(sc, sc.cur, x - 8, y, 16, 5)
    lay = art.plane()
    art.falls(lay, (480, 500, 202), (474, 506, 300), sc.col("water", 0.42), (214, 230, 255), 305)
    sc.raw(lay)
    sc.live(Waterfall(rng, 480, 500, 202, 298, None, sc.col("water", 0.28), (232, 242, 255)))
    lay = art.plane()
    pool = mix(sc.col("water", 0.42), (40, 60, 150), 0.2)
    pygame.draw.ellipse(lay, sc.col("stone", 0.48), (430, 294, 120, 28))
    pygame.draw.ellipse(lay, pool, (436, 296, 108, 22))
    pygame.draw.ellipse(lay, mix(pool, (255, 255, 255), 0.35), (460, 301, 60, 9), 1)
    pygame.draw.ellipse(lay, mix(pool, (255, 255, 255), 0.6), (478, 298, 24, 5))  # foam at the foot
    rock_moss = []
    for x, y, w, h in ((428, 314, 22, 10), (548, 314, 24, 10), (448, 322, 14, 6), (530, 324, 12, 6)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.48), moss=sc.col("moss", 0.48), mossiness=0.6,
                 glow_pts=rock_moss)
    sc.add(lay, 0.48, texture=0.6)
    moss_glow(sc, rock_moss, strength=40)
    sc.lamp(490, 304, 70, GLOW["cyan"], 50)
    sc.lamp(490, 236, 40, GLOW["cyan"], 26)

    # the Forest, left: crowns seen from above, packed close, glowing mushrooms in the gaps
    lay = art.plane()
    leaf = [sc.col("leaf3", 0.64), sc.col("leaf3", 0.58), sc.col("leaf", 0.54), sc.col("leaf", 0.5),
            sc.col("leaf2", 0.46), sc.col("leaf2", 0.42)]
    floor = mix(leaf[0], p["shade"], 0.55)
    edge_pts = [(0, 226)] + [(x, 224 + int(4 * math.sin(x / 11))) for x in range(0, 392, 12)]
    edge_pts += [(392 - (y - 226) * 0.32 + 6 * math.sin(y / 9), y) for y in range(232, 372, 10)]
    edge_pts += [(x, 372 + int(5 * math.sin(x / 13))) for x in range(340, -1, -14)]
    pygame.draw.polygon(lay, floor, edge_pts)
    x = 0
    while x < 396:  # the back row, rising over the forest's far edge
        r = rng.randint(5, 9)
        art.foliage(lay, rng, x, 220 + rng.randint(-4, 3), r * 1.1, r * 0.9, leaf[0], p, leaf=(2, 4))
        x += int(r * 1.4)
    for i, y in enumerate(range(226, 372, 22)):
        rmin, rmax = 7 + i * 2, 12 + i * 3
        x = -6 + (i % 2) * 10
        end = 394 - (y - 226) * 0.34
        while x < end:
            r = rng.randint(rmin, rmax)
            cy = y + rng.randint(-6, 6)
            pygame.draw.ellipse(lay, mix(floor, (0, 0, 0), 0.25), (x - r, cy - r * 0.3, r * 2.2, r * 1.3))  # its shade
            art.foliage(lay, rng, x, cy, r * 1.1, r * 0.8, leaf[min(i, 5)], p, leaf=(2, 5))
            x += int(r * rng.uniform(1.3, 1.7))
    sc.add(lay, 0.5, veil=0.02, low=0.06)
    lay = art.plane()
    for x, y, size, cap in ((70, 262, 3, GLOW["cyan"]), (132, 286, 3, GLOW["pink"]), (196, 312, 4, GLOW["violet"]),
                            (256, 276, 3, GLOW["lime"]), (318, 300, 3, GLOW["cyan"]), (150, 340, 4, GLOW["amber"]),
                            (36, 300, 2, GLOW["pink"]), (226, 246, 2, GLOW["cyan"]), (286, 344, 3, GLOW["pink"]),
                            (96, 322, 3, GLOW["lime"])):
        mushroom(lay, x, y, size, cap, sc, glows)
    sc.raw(lay)
    for x, y in ((90, 280), (210, 300), (300, 260), (160, 350)):
        sc.lamp(x, y, 50, GLOW["moss"], 26)

    # --- the clearing, in the middle ------------------------------------------------------------
    lay = art.plane()
    art.ridge(lay, rng, 326, 6, sc.col("leaf2", 0.36), scales=(140, 40, 14), texture=False)
    sc.add(lay, 0.36, low=0.04)
    for x in (340, 640, 760):
        sc.lamp(x, 340, 40, GLOW["moss"], 26)
    lay = art.plane()
    art.grass_bed(lay, rng, (0, 336, W, 204), sc.col("leaf", 0.26), 2800, 5)
    lay.blit(art.soft_ellipse(200, 70, sc.col("leaf2", 0.22), 150), (CLEAR[0] - 200, CLEAR[1] - 64))
    art.grass_bed(lay, rng, (320, 356, 340, 104), sc.col("leaf2", 0.2), 900, 3)
    art.flowers(lay, rng, (300, 356, 380, 110), p["flowers"], 120)
    art.flowers(lay, rng, (0, 440, W, 100), p["flowers"], 80)
    sc.add(lay, 0.26, texture=0.6)

    # the River, right: out of the pool, round the clearing, widening toward you as it goes
    course = [(520, 316), (580, 326), (640, 332), (700, 338), (780, 352), (870, 372), (980, 398)]
    widths = [8, 12, 16, 20, 26, 32, 40]
    lay = art.plane()
    water = sc.col("water", 0.36)
    edge = mix(sc.col("earth_edge", 0.36), sc.col("leaf", 0.36), 0.5)
    art.path(lay, course, widths, water, edge)
    sc.add(lay, 0.36, texture=0.3)

    def along(x):
        for (x0, y0), (x1, y1), w0, w1 in zip(course, course[1:], widths, widths[1:]):
            if x <= x1:
                f = max(0.0, (x - x0) / (x1 - x0))
                return y0 + (y1 - y0) * f, w0 + (w1 - w0) * f
        return course[-1][1], widths[-1]

    def top(x):
        y, w = along(x)
        return y - w / 2 + 3

    def bot(x):
        y, w = along(x)
        return y + w / 2 - 3

    sc.live(River(rng, top, bot, (600, W), 110, mix(sc.col("water", 0.3), (255, 255, 255), 0.45), (255, 255, 255),
                  speed=18))
    lay = art.plane()  # reeds and lotuses along the banks, and the boat with its lantern
    for x in range(600, 960, 11):
        y = round(top(x)) - 1 + (x * 7) % 3
        for k in range(3):
            pygame.draw.line(lay, sc.col("leaf2", 0.4), (x + k * 2, y), (x + k * 2 + (k - 1), y - 4 - (x + k) % 4))
        yb = round(bot(x)) + 2
        pygame.draw.line(lay, sc.col("leaf", 0.36), (x + 4, yb), (x + 5, yb - 5))
    for x in (690, 760, 890):
        y = round((top(x) + bot(x)) / 2)
        pygame.draw.ellipse(lay, sc.col("leaf", 0.4), (x - 4, y - 1, 9, 4))
        pygame.draw.circle(lay, (255, 196, 236), (x, y), 2)
        glows.append((x, y, 18, GLOW["pink"], 70, x * 0.1))
    bx = 812
    by = round((top(bx) + bot(bx)) / 2) + 1
    hull, hull2 = sc.col("wood", 0.36), sc.col("wood2", 0.36)
    pygame.draw.polygon(lay, hull, [(bx - 16, by - 3), (bx + 16, by - 4), (bx + 11, by + 3), (bx - 12, by + 3)])
    pygame.draw.line(lay, hull2, (bx - 16, by - 3), (bx + 16, by - 4))
    pygame.draw.line(lay, hull, (bx + 8, by - 4), (bx + 8, by - 14))
    pygame.draw.rect(lay, (255, 236, 170), (bx + 6, by - 17, 4, 4))
    sc.add(lay, 0.36, texture=0.4)
    sc.lamp(bx + 8, by - 14, 50, GLOW["amber"], 60)
    sc.shine(bx + 8, by - 15, 4, GLOW["amber"], 80)

    lay = art.plane()
    earth, edge = mix(sc.col("earth", 0.24), sc.col("leaf", 0.24), 0.45), mix(sc.col("earth_edge", 0.24), sc.col("leaf", 0.24), 0.3)
    cx, cy = CLEAR
    art.path(lay, [(cx, cy), (486, 380), (488, 352), (490, 326)], [16, 12, 8, 5], earth, edge, rng=rng)  # waterfall
    art.path(lay, [(cx, cy), (420, 398), (360, 384), (310, 366), (270, 356)], [16, 12, 10, 8, 6], earth, edge,
             rng=rng)  # forest
    art.path(lay, [(cx, cy), (560, 404), (630, 394), (690, 382), (716, 376)], [16, 12, 10, 8, 7], earth, edge,
             rng=rng)  # river
    art.path(lay, [(cx, cy), (452, 440), (412, 480), (380, 516), (362, 548)], [16, 22, 28, 34, 40], earth, edge,
             rng=rng)  # down to the Mossy Rocks
    pygame.draw.ellipse(lay, edge, (458, 395, 60, 18))
    pygame.draw.ellipse(lay, earth, (460, 394, 56, 16))
    # a stepping-stone footbridge over the river
    for i in range(4):
        x, y = 716 + i * 6, round(top(716 + i * 6)) + 2 + i
        pygame.draw.ellipse(lay, sc.col("stone", 0.3), (x - 3, y, 7, 4))
    # signpost, three arms
    wood, wood2 = sc.col("wood", 0.2), sc.col("wood2", 0.2)
    pygame.draw.rect(lay, wood, (cx - 2, cy - 34, 4, 36))
    for y, dx, w in ((cy - 32, -1, 22), (cy - 24, 1, 20), (cy - 16, -1, 18)):
        x = cx if dx > 0 else cx - w
        pygame.draw.rect(lay, wood2, (x, y, w, 5))
        tip = x + w if dx > 0 else x
        pygame.draw.polygon(lay, wood2, [(tip, y), (tip + dx * 3, y + 2), (tip, y + 4)])
        pygame.draw.line(lay, mix(wood2, p["rim"], 0.3), (x, y), (x + w - 1, y))
    # the stump with its lantern
    sx, sy = 400, 418
    pygame.draw.ellipse(lay, wood, (sx - 12, sy - 2, 24, 12))
    pygame.draw.rect(lay, wood, (sx - 11, sy - 8, 22, 10))
    pygame.draw.ellipse(lay, wood2, (sx - 12, sy - 13, 24, 9))
    for r in (3, 6, 9):
        pygame.draw.ellipse(lay, mix(wood2, wood, 0.5), (sx - r, sy - 9 - r // 3, r * 2, r * 0.7), 1)
    pygame.draw.rect(lay, sc.col("wood", 0.1), (sx - 4, sy - 22, 8, 9))
    pygame.draw.rect(lay, (255, 240, 180), (sx - 3, sy - 21, 6, 7))
    pygame.draw.line(lay, sc.col("wood", 0.1), (sx, sy - 26), (sx, sy - 22))
    # mossy rocks about the clearing
    rocks = []
    for x, y, w, h in ((330, 436, 28, 12), (620, 446, 34, 14), (566, 372, 18, 8), (360, 376, 16, 7)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.22), moss=sc.col("moss", 0.2), mossiness=0.7,
                 glow_pts=rocks)
        sc.shadow(x, y + 3, w * 0.7, h * 0.4, 0.3)
    sc.add(lay, 0.22, texture=0.4)
    moss_glow(sc, rocks, strength=50)
    sc.shadow(sx, sy + 4, 16, 5, 0.4)
    sc.shadow(cx, cy + 2, 10, 3, 0.4)
    sc.live(Lantern(sx, sy - 18, (255, 196, 120), reach=110))
    for x, y, w, h, c in ((340, 456, 30, 8, None), (560, 470, 30, 9, GLOW["lime"]), (420, 362, 24, 6, GLOW["cyan"]),
                          (640, 420, 26, 7, None)):
        art.glowmoss(sc, sc.cur, x, y, w, h, c)

    # the blossom tree, right of the signpost: seen from above, its crown a soft pink dome
    lay = art.plane()
    tx = 604
    art.trunk(lay, rng, tx, 360, 430, 14, sc.col("wood", 0.26), branches=2, pal=p)
    sc.add(lay, 0.26, texture=0.8)
    sc.shadow(tx, 436, 70, 14, 0.5)
    lay = art.plane()
    crown = ((604, 344, 72, 40), (566, 330, 40, 26), (644, 332, 40, 26), (604, 314, 52, 28),
             (546, 356, 26, 16), (664, 356, 26, 16))
    for ccx, ccy, rx, ry in crown:
        art.foliage(lay, rng, ccx, ccy, rx, ry, sc.col("pink", 0.3), p, leaf=(3, 6))
    mask = pygame.mask.from_surface(lay)
    art.blossoms(lay, rng, (520, 280, 170, 110), [(255, 255, 255), (255, 220, 240), (255, 130, 196)], 520, mask)
    sc.add(lay, 0.28)
    for _ in range(70):
        x, y = rng.randint(530, 680), rng.randint(290, 380)
        if mask.get_at((x, y)):
            sc.emit.set_at((x, y), (120, 50, 100))
    sc.lamp(604, 340, 110, GLOW["pink"], 34)
    sc.live(Petals(rng, (540, 300, 140, 50), 470, 40, [(255, 200, 230), (255, 255, 255), (255, 150, 200)]))
    sc.orchard = sc.live(Orchard(sc, Spot, canopy=crown))
    sc.live(Nibbler(rng, sc.orchard, (520, 280, 170, 110), GLOW["pink"]))

    # riverside: a few small trees behind the River, and ferns, mushrooms and a hollow log in front
    lay = art.plane()
    for x, y, r in ((612, 318, 10), (664, 320, 12), (744, 328, 11), (818, 340, 13), (866, 350, 10)):
        art.trunk(lay, rng, x, y - r, y + 4, 3, sc.col("wood", 0.42), branches=0)
        art.foliage(lay, rng, x, y - r - 4, r, r * 0.8, sc.col("leaf", 0.42), p, leaf=(2, 4))
    sc.add(lay, 0.42, texture=0.5)
    for x, y in ((664, 316), (818, 334)):
        sc.lamp(x, y, 34, GLOW["moss"], 26)
    lay = art.plane()
    for x, y, n in ((110, 452, 5), (300, 488, 4), (560, 508, 5), (760, 470, 6), (830, 506, 5), (650, 520, 4),
                    (240, 420, 4), (720, 432, 4)):
        for k in range(n):  # a fern: fronds fanning out of the ground
            a = math.pi * (0.15 + 0.7 * k / max(1, n - 1))
            ln = 8 + (k * 5) % 6
            tip = (x + math.cos(a) * ln * 1.3, y - math.sin(a) * ln)
            pygame.draw.line(lay, sc.col("leaf2", 0.16), (x, y), tip)
            pygame.draw.line(lay, sc.col("leaf", 0.16), (x + 1, y), (tip[0] + 1, tip[1] + 1))
    for x, y, size, cap in ((132, 468, 3, GLOW["pink"]), (140, 472, 2, GLOW["pink"]), (586, 488, 3, GLOW["cyan"]),
                            (776, 486, 4, GLOW["violet"]), (784, 490, 2, GLOW["violet"]), (346, 470, 2, GLOW["lime"]),
                            (700, 412, 2, GLOW["cyan"])):
        mushroom(lay, x, y, size, cap, sc, glows)
    lx, ly = 760, 452  # a hollow mossy log
    pygame.draw.ellipse(lay, sc.col("wood", 0.18), (lx - 30, ly - 7, 60, 14))
    pygame.draw.rect(lay, sc.col("wood", 0.18), (lx - 26, ly - 7, 52, 12))
    pygame.draw.line(lay, sc.col("wood2", 0.18), (lx - 26, ly - 7), (lx + 26, ly - 7))
    pygame.draw.ellipse(lay, sc.col("wood2", 0.18), (lx + 20, ly - 7, 12, 13))
    pygame.draw.ellipse(lay, sc.col("shade", 0.1), (lx + 22, ly - 5, 8, 9))
    pygame.draw.ellipse(lay, sc.col("moss", 0.18), (lx - 22, ly - 10, 30, 6))
    sc.add(lay, 0.16, texture=0.5)
    art.glowmoss(sc, sc.cur, lx - 22, ly - 9, 30, 4)
    sc.shadow(lx, ly + 6, 30, 5, 0.4)

    meadow_life(sc, p, glows)

    # --- the Mossy Rocks, along the front edge ---------------------------------------------------
    lay = art.plane()
    front_moss = []
    for x, y, w, h in ((218, 520, 70, 30), (160, 532, 50, 22), (286, 534, 44, 18), (452, 530, 50, 20),
                       (110, 500, 30, 14), (512, 536, 38, 14)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.14), moss=sc.col("moss", 0.12), mossiness=0.8,
                 glow_pts=front_moss)
        sc.shadow(x, y + 4, w * 0.7, h * 0.4, 0.35)
    sc.add(lay, 0.14, texture=0.4)
    moss_glow(sc, front_moss, strength=55)

    sc.live(Shafts([(470, 0, 520, 170, 0.0), (520, 0, 640, 150, 2.4)], (150, 170, 255), alpha=12))
    sc.live(Blades(rng, (0, 440, W, 100), 380, [sc.col("leaf", 0.15), sc.col("leaf2", 0.12), sc.col("leaf3", 0.12)],
                   5, 14))

    # --- the tall trees along both edges, holding his squid --------------------------------------
    lay = art.plane()
    leans = {}
    for x, w in ((24, 26), (80, 18), (884, 18), (938, 26)):
        leans[x] = art.trunk(lay, rng, x, -10, 540, w, sc.col("wood", 0.1), branches=2, pal=p)
    for x0, x1 in ((-20, 130), (830, 980)):
        leaf_row(lay, rng, x0, x1, 10, 34, 26, sc.col("leaf3", 0.1), p, jitter=10)
        leaf_row(lay, rng, x0 + 10, x1 - 10, 46, 26, 18, sc.col("leaf", 0.1), p, jitter=10)
    sc.add(lay, 0.1, texture=1.0)
    for x in (24, 80, 884, 938):
        art.glowmoss(sc, sc.cur, x - 16, 520, 32, 10)
        sc.lamp(x, 530, 40, GLOW["moss"], 34)
    sc.live(Vines(rng, list(range(140, 300, 18)) + list(range(660, 820, 20)), lambda x: 0, (10, 46),
                  sc.col("leaf3", 0.06), sc.col("leaf2", 0.08), flower=p["pink"], glow_tip=GLOW["cyan"]))

    # --- the animals: the same ones as the old clearing, made in the same order (carry.py) ---------
    sc.live(Slug(rng, Track([(404, 504), (464, 508), (524, 502), (584, 506)]), (214, 170, 222), size=1.2))
    rock_track = sorted((pt for pt in front_moss if 190 < pt[0] < 250), key=lambda pt: pt[0])
    if len(rock_track) < 3:
        rock_track = [(196, 508), (218, 505), (240, 508)]
    sc.live(Slug(rng, Track([(x, y - 1) for x, y in rock_track]), (120, 150, 230), size=1.0, speed=3,
                 spots=GLOW["cyan"]))
    sc.live(Slug(rng, Track([(tx + 4, 426), (tx + 3, 400), (tx + 2, 372)], up=(1, 0)), (220, 196, 180), size=0.9,
                 speed=2.5, shell=(232, 178, 140)))
    trunk = lambda x, w, lo, hi: dict(x=x, w=w, lo=lo, hi=hi, bottom=540, lean=leans[x])  # noqa: E731
    sc.colony = sc.live(Colony(sc, Spot, [trunk(24, 24, 96, 470), trunk(80, 16, 96, 470),
                                          trunk(884, 16, 96, 340), trunk(938, 24, 96, 340)]))
    sc.critter = Critter(rng, lambda x: 436 + 4 * math.sin(x / 60), (380, 600))
    sc.live(sc.critter)
    additions(sc, rng, [("ring", 690, 470), ("cairn", 262, 452)])
    second_wave(sc, rng, (160, 200, 640, 120),
                [(lambda x: 476 + 4 * math.sin(x / 50), (420, 640)), (lambda x: 462 + 3 * math.sin(x / 40), (200, 330))],
                far=[(lambda x: 372 + 2 * math.sin(x / 40), (540, 660)), (lambda x: 384 + 2 * math.sin(x / 50),
                                                                         (330, 420))],
                persp=high)
    bugs = sc.live(Fireflies(rng, (0, 200, W, 300), 40))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 440), 40, GLOW["cyan"]))
    sc.live(Pulses(glows))

    # --- what can be clicked: each place you can see, for a look at it (peek.py) ---------------
    sc.spots = [
        Spot("peek", (400, 190, 190, 130), "The Waterfall", "waterfall", (490, 260), sign=(490, 192)),
        Spot("peek", (110, 230, 250, 130), "The Forest", "forest", (200, 300), sign=(200, 232)),
        Spot("peek", (640, 320, 190, 60), "The River", "river", (740, 350), sign=(760, 304)),
        Spot("peek", (130, 480, 200, 60), "The Mossy Rocks", "rocks", (220, 520), sign=(250, 486)),
        Spot("peek", (410, 66, 200, 100), "The Crystal Caverns", "caverns", (490, 120), sign=(490, 66)),
        Spot("peek", (0, 70, 250, 120), "The Snowy Ridge", "ridge", (110, 150), sign=(120, 70)),
        Spot("peek", (230, 140, 140, 64), "The Old Ruins", "ruins", (290, 180), sign=(300, 144)),
        Spot("peek", (614, 160, 160, 60), "The Starfall Meadow", "meadow", (690, 196), sign=(690, 160)),
        Spot("peek", (770, 70, 190, 130), "The Hot Springs", "springs", (864, 130), sign=(866, 70)),
    ]
    for sp in sc.spots:
        sp.icon = eye()
    # the lower screen: exactly the Glade's (lower.py), the pond and the path down
    sc.lower = dict(ground=0.3, pond=(540, 256, 224, 132), paths=[dict(
        pts=[(202, -4), (180, 16), (160, 60), (156, 120), (172, 190), (204, 260), (220, 340), (208, 460)],
        widths=[94, 98, 104, 112, 120, 128, 136, 148],
        sign=(320, 392), spot=((120, 300, 240, 150), "The Mossy Rocks", "rocks", (212, 412)))])
    ground(sc)  # (before done: walk.py gives the walkers this ground)
    return sc.done()

