"""The Moonlit Hall (2026-10-30, his pick): where the Elite 4 and the champion wait (elite.py).

A tall hall of pale stone and glass at the very top of the map, above the Floating Isles, up a
stair of moonlight. Its banners are the four line-ups' colours; its great door glows gold, and
opens only once every gym badge is won.
"""

import pygame

import art
from art import GLOW, H, W, glow, mix
from kit import blob_row, lit, make, tint

PALE = (226, 222, 246)     # the hall's stone
GLASS = (190, 214, 255)    # its windows, lit from inside
GOLD = (255, 214, 140)     # the great door
BANNERS = [(170, 130, 255), (110, 200, 255), (255, 140, 90), (150, 225, 110)]  # elite.LINEUPS' colours
DOOR = (480, 446)          # the foot of the great door (the clickable spot in elite.py)


def arch(lay, color, x, y, w, h):
    """A round-topped window or door: a rectangle under a half circle."""
    pygame.draw.rect(lay, color, (x, y + w // 2, w, h - w // 2))
    pygame.draw.ellipse(lay, color, (x, y, w, w))


def hall_mid(sc, rng):
    glows = []
    for d, y0, c in ((0.85, 400, 0.75), (0.6, 440, 0.55)):  # cloud banks below and behind
        lay = art.plane()
        blob_row(lay, rng, y0, 26, (30, 70), mix((196, 186, 255), sc.pal["sky"][1], c))
        sc.add(lay, d, veil=0.02)

    lay = art.plane()
    stone, dark = tint(PALE, -0.18), tint(PALE, -0.45)
    # the wings, lower and set back
    for x0, x1 in ((180, 300), (660, 780)):
        pygame.draw.rect(lay, dark, (x0, 270, x1 - x0, 180))
        pygame.draw.polygon(lay, tint(PALE, -0.3), [(x0 - 8, 272), ((x0 + x1) // 2, 236), (x1 + 8, 272)])
        for wx in range(x0 + 16, x1 - 20, 30):
            arch(lay, tint(GLASS, -0.35), wx, 300, 14, 50)
            arch(sc.emit, tint(GLASS, -0.55), wx + 2, 302, 10, 46)
    # the towers at either end of the main front
    for tx in (300, 640):
        pygame.draw.rect(lay, stone, (tx, 150, 20, 300))
        pygame.draw.polygon(lay, tint(PALE, -0.05), [(tx - 4, 152), (tx + 10, 92), (tx + 24, 152)])
        sc.emit.set_at((tx + 10, 94), GLASS)
        glows.append(lit(sc, tx + 10, 92, 40, GLASS, 50, core=3))
    # the main front: pale stone, a dome with a rose window, tall glass between the columns
    pygame.draw.rect(lay, stone, (320, 200, 320, 250))
    pygame.draw.ellipse(lay, tint(PALE, -0.08), (370, 110, 220, 190))
    pygame.draw.rect(lay, tint(PALE, -0.08), (370, 205, 220, 10))
    pygame.draw.rect(lay, tint(PALE, 0.1), (470, 70, 20, 50))           # the spire on the dome
    pygame.draw.polygon(lay, tint(PALE, 0.15), [(466, 72), (480, 36), (494, 72)])
    pygame.draw.circle(lay, tint(GLASS, -0.25), (480, 165), 30)        # the rose window
    pygame.draw.circle(sc.emit, tint(GLASS, -0.4), (480, 165), 27)
    for k in range(8):
        v = pygame.math.Vector2(0, 26).rotate(k * 45)
        pygame.draw.line(lay, stone, (480, 165), (480 + v.x, 165 + v.y), 2)
        pygame.draw.line(sc.emit, (0, 0, 0), (480, 165), (480 + v.x, 165 + v.y), 2)
    pygame.draw.circle(sc.emit, GLASS, (480, 165), 5)
    glows.append(lit(sc, 480, 165, 140, GLASS, 70))
    pygame.draw.rect(lay, tint(PALE, 0.12), (316, 196, 328, 8))         # the cornice
    for i, cx in enumerate(range(334, 640, 51)):                       # columns, with glass between
        pygame.draw.rect(lay, tint(PALE, 0.08), (cx, 210, 12, 230))
        pygame.draw.rect(lay, tint(PALE, -0.12), (cx + 9, 210, 3, 230))
        if cx + 51 < 640 and not 430 < cx + 25 < 530:
            arch(lay, tint(GLASS, -0.3), cx + 18, 230, 20, 120)
            arch(sc.emit, tint(GLASS, -0.5), cx + 20, 232, 16, 116)
    # the four banners, one in each line-up's colour, hanging from the cornice
    for (bx, by), c in zip(((344, 214), (395, 214), (556, 214), (607, 214)), BANNERS):
        bx += 10
        pygame.draw.polygon(lay, c, [(bx, by), (bx + 22, by), (bx + 22, by + 90), (bx + 11, by + 80), (bx, by + 90)])
        pygame.draw.polygon(lay, tint(c, -0.3), [(bx + 15, by), (bx + 22, by), (bx + 22, by + 90), (bx + 15, by + 84)])
        pygame.draw.circle(lay, (255, 250, 230), (bx + 11, by + 30), 5, 1)
        pygame.draw.circle(sc.emit, tint(c, -0.4), (bx + 11, by + 30), 4)
        glows.append(lit(sc, bx + 11, by + 30, 50, c, 45))
    # the great door: gold light behind tall leaves, steps below
    arch(lay, tint(PALE, 0.15), 436, 330, 88, 120)
    arch(lay, tint(GOLD, -0.2), 444, 338, 72, 112)
    arch(sc.emit, tint(GOLD, -0.35), 446, 340, 68, 110)
    pygame.draw.line(lay, tint(GOLD, -0.55), (480, 352), (480, 450), 2)
    pygame.draw.line(sc.emit, (0, 0, 0), (480, 352), (480, 450), 2)
    glows.append(lit(sc, 480, 400, 160, GOLD, 90))
    for i in range(3):
        pygame.draw.rect(lay, tint(PALE, 0.05 - 0.07 * i), (400 - i * 16, 444 + i * 5, 160 + i * 32, 6))
    sc.add(lay, 0.4, veil=0.01)
    return glows


def hall_near(sc, lay, rng):
    """We stand on the hall's own island: grass with a pale stone walk up to the door."""
    art.grass_bed(lay, rng, (0, 452, W, H - 452), sc.col("leaf", 0.18), 1200, 6)
    art.flowers(lay, rng, (0, 462, W, H - 462), sc.pal["flowers"], 50)
    for i in range(9):  # flagstones up to the steps
        y = 462 + i * 9
        w = 60 + i * 10
        pygame.draw.rect(lay, mix(tint(PALE, -0.25 - 0.02 * i), sc.pal["shade"], 0.2), (480 - w // 2, y, w, 7))


def hall_props(sc, rng):
    """Lamps on posts either side of the walk."""
    lay = art.plane()
    glows = []
    for x in (330, 630, 200, 760):
        y = 470 if x in (330, 630) else 486
        pygame.draw.rect(lay, tint(PALE, -0.4), (x - 2, y - 40, 4, 40))
        pygame.draw.rect(lay, tint(PALE, -0.2), (x - 5, y - 48, 10, 9))
        glow(sc.emit, x, y - 44, 3, GOLD, 220)
        glows.append(lit(sc, x, y - 44, 70, GOLD, 60, core=2))
    sc.add(lay, 0.16, texture=0.3)
    return glows


def build_hall():
    sc = make("hall", "The Moonlit Hall", 97,
              dict(sky=[(6, 8, 34), (18, 20, 70), (40, 40, 120), (90, 86, 170)], mist=(140, 140, 210),
                   shade=(12, 12, 40), ambient=((240, 240, 255), (110, 110, 180)), leaf=(110, 190, 160),
                   leaf2=(150, 210, 170), leaf3=(70, 120, 140), stone=(170, 160, 210),
                   flowers=[(255, 255, 255), (220, 210, 255), (255, 230, 200)]),
              exits=[("down", "Back to the Floating Isles", "isles")], gy=452, stars=320, star_floor=330,
              moon_at=(800, 70, 24), mid=hall_mid, near=hall_near, props=hall_props, fly=(255, 236, 200),
              squid=[GLOW["violet"], GLOW["white"]], motes=((230, 230, 255), -2), slug=((220, 230, 255), GLOW["moss"]),
              fliers=("breeze", "wish", "dream"), walkers=("tuft", "goat", "starb"),
              out=("tuft", "breeze", "goat"), far_grounds=[], sky=(60, 40, 260, 140), lower_props=("rocks",))
    from elite import place
    place(sc)
    return sc


def stair(sc, lay):
    """In the Floating Isles: a stair of moonlight going up out of the picture, to the hall."""
    for i in range(10):
        x, y, w = 708 + i * 15, 404 - i * 28, 36 - i * 2
        c = mix(GLASS, sc.pal["sky"][2], 0.05 + i * 0.06)
        pygame.draw.rect(lay, tint(c, -0.35), (x - w // 2, y + 3, w, 5))   # its glassy edge
        pygame.draw.rect(lay, c, (x - w // 2, y, w, 4))
        pygame.draw.rect(sc.emit, tint(c, -0.3), (x - w // 2 + 2, y, w - 4, 2))
        sc.lamp(x, y, 40, GLASS, 30)


BUILD = dict(hall=build_hall)
