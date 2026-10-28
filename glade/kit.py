"""A kit for the far places (2026-10-27, his ask: fifteen more places in three rounds). Each new
place is a short spec plus a painter for what makes it itself (`mid`, and sometimes `far`,
`near`, `props`); `make` does the rest the same way every place in scenes.py does: sky, the
near ground with its paths out, moving grass and lights, the animals, the name boards.

`trail` and `exit_spot` are also used to add the paths out of the places they branch off from.
"""

import math
import random

import pygame

import art
from art import GLOW, H, W, glow, mix
from life import Blades, Fireflies, Motes, Pulses, Slug, Stars, Track, make_rng
from scenes import Scene, Spot, additions, front_frame, moon, pal, second_wave, squids

LOWER_PATH = dict(pts=[(232, -4), (230, 80), (226, 200), (220, 320), (214, 460)], widths=[96, 104, 116, 128, 140],
                  sign=(370, 240))


def trail(sc, lay, side, gy, x=480, seed=0, depth=0.2):
    """Draw a path leaving the picture: off the left or right edge at the front, `up` into the
    back of the picture at x, or `down` off the bottom (the way back to a place below)."""
    earth, edge = sc.col("earth", depth), sc.col("earth_edge", depth)
    rng = random.Random(seed or sum(map(ord, sc.key)) + len(side))
    if side == "left":
        art.path(lay, [(-24, gy + 36), (80, gy + 32), (170, gy + 26), (230, gy + 22)], [44, 40, 28, 14], earth, edge, rng=rng)
    elif side == "right":
        art.path(lay, [(W + 24, gy + 36), (W - 80, gy + 32), (W - 170, gy + 26), (W - 230, gy + 22)], [44, 40, 28, 14],
                 earth, edge, rng=rng)
    elif side == "up":
        art.path(lay, [(x, gy + 60), (x + 4, gy + 20), (x, gy - 14), (x - 2, gy - 40)], [36, 20, 10, 4], earth, edge, rng=rng)
    elif side == "down":
        art.path(lay, [(476, gy + 20), (478, 510), (480, 560)], [40, 70, 110], earth, edge, rng=rng)


def exit_spot(side, label, target, gy, x=480):
    """The clickable spot and name board for a path drawn by `trail`."""
    if side == "left":
        return Spot("go", (0, gy - 4, 96, 80), label, target, (30, gy + 36), sign=(116, gy - 4))
    if side == "right":
        return Spot("go", (W - 96, gy - 4, 96, 80), label, target, (W - 30, gy + 36), sign=(W - 116, gy - 4))
    if side == "up":
        return Spot("go", (x - 50, gy - 70, 100, 80), label, target, (x, gy - 30), sign=(x, gy - 66))
    return Spot("go", (392, 480, 168, 60), label, target, (476, 516), sign=(476, 504))


def lower_path(label, target, x=232):
    """A path down the lower screen to the place below (`sc.lower`'s paths)."""
    dx = x - 232
    return dict(pts=[(px + dx, py) for px, py in LOWER_PATH["pts"]], widths=LOWER_PATH["widths"],
                sign=(370 + dx, 240), spot=((150 + dx, 150, 160, 220), label, target, (224 + dx, 300)))


def wobble(y, amp=3, period=45):
    return lambda x: y + amp * math.sin(x / period)


def make(key, title, seed, palette, *, exits, fliers, walkers, out, gy=450, stars=200, star_floor=260,
         moon_at=None, far=None, mid=None, near=None, props=None, grassy=True, fly=GLOW["firefly"], squid=None,
         motes=None, slug=None, far_grounds=(), sky=(100, 80, 760, 180), lower_props=("rocks",), adds=(),
         frame=None, lower=None, pond=None):
    """Build one place. Painters each take (sc, rng) — `near` also gets the near layer to draw
    on — and may return a list of glows ((x, y, r, colour, strength, phase)) for Pulses."""
    rng = make_rng(seed)
    p = pal(**palette)
    sc = Scene(key, title, p, rng)
    if stars:
        sc.live(Stars(rng, stars, star_floor))
    if moon_at:
        moon(sc, *moon_at)
    glows = []
    for painter in (far, mid):
        if painter:
            glows += painter(sc, rng) or []
    # near: the ground in front, and the paths out
    lay = art.plane()
    art.ridge(lay, rng, gy, 8, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    if near:
        glows += near(sc, lay, rng) or []
    else:
        art.grass_bed(lay, rng, (0, gy, W, H - gy), sc.col("leaf", 0.18), 1400, 6)
        art.flowers(lay, rng, (0, gy + 10, W, H - gy - 10), p["flowers"], 70)
    for side, label, target, *x in exits:
        if side != "lower":
            trail(sc, lay, side, gy, *x)
    sc.add(lay, 0.2, texture=0.6)
    if props:
        glows += props(sc, rng) or []
    if glows:
        sc.live(Pulses(glows, speed=0.8))
    if grassy:
        sc.live(Blades(rng, (0, gy - 4, W, H - gy + 4), 300, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1)], 8, 24))
    if motes:
        sc.live(Motes(rng, (0, 80, W, gy - 40), 60, motes[0], rise=motes[1]))
    if pond is not None:
        sc.pond = sc.live(pond(sc, rng))
    if slug:
        y = min(526, gy + 70)
        sc.live(Slug(rng, Track([(560, y), (660, y + 4), (760, y)]), slug[0], size=1.4, speed=3, spots=slug[1]))
    if adds:
        additions(sc, rng, list(adds))
    grounds = [(wobble(gy + 40, 3, 40), (120, 360)), (wobble(gy + 66, 3, 50), (540, 860)), (wobble(gy + 30, 2, 60), (360, 560))]
    second_wave(sc, rng, sky, grounds, fliers=fliers, walkers=walkers, out=out,
                far=[(wobble(y, 2, 40 + 10 * i), xr) for i, (y, xr) in enumerate(far_grounds)])
    bugs = sc.live(Fireflies(rng, (0, 200, W, gy - 140), 30, color=fly, reach=24))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 70, 700, 180), squid or [GLOW["cyan"], GLOW["pink"]])
    front_frame(sc, rng, **(frame or dict(top=False)))
    sc.spots = [exit_spot(side, label, target, gy, *x) for side, label, target, *x in exits if side != "lower"]
    sc.lower = dict(ground=0.18, props=list(lower_props), fly=fly, walkers=tuple(walkers)[:4], fliers=tuple(fliers)[:2],
                    out=(walkers[0], fliers[0]), **(lower or {}))
    downs = [lower_path(label, target, *x) for side, label, target, *x in exits if side == "lower"]
    if downs:
        sc.lower["paths"] = downs
    return sc.done()


# --- painting helpers shared by the far places -----------------------------------------------

def blob_row(lay, rng, y, n, r, color, x0=-40, x1=W + 40, jitter=10):
    """A bank of round lumps (clouds, bushes, dunes) along y, filled down to the bottom."""
    for _ in range(n):
        pygame.draw.circle(lay, color, (rng.randint(x0, x1), y + rng.randint(-jitter, jitter)), rng.randint(*r))
    pygame.draw.rect(lay, color, (0, y, W, H - y))


def lit(sc, x, y, r, color, strength=60, core=None):
    """A light at (x, y): its pool on the light map, a bright pixel or two, and a glow for Pulses."""
    sc.lamp(x, y, r, color, strength)
    if core and 0 <= x < W and 0 <= y < H:
        glow(sc.emit, x, y, core, color, 200)
    return (x, y, r // 2, color, strength, x * 0.05)


def tint(c, k):
    return mix(c, (255, 255, 255), k) if k > 0 else mix(c, (0, 0, 0), -k)
