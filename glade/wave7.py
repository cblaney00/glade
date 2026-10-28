"""Two new lines for the five new places (2026-10-27, his ask; places in faraway.py): Tanglet
(#289-#291, Fighting/Flying) lives on the Cloud Bridge, Tumblet (#292-#294, Rock/Water) on the
Glow Shore. Everyone else in those places moved in from elsewhere.

Same rules as wave5.py and wave6.py: no humanoids, a body of its own, `draw_<kind>` for all three
stages and `glow_<kind>` for its lights. They join wave5's HOMES.
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, LIT, WALKERS, Flier, Walker
from life import q
from wave5 import HOMES, KINDS as _OLD, TAU, WHITE, dark, eyes, hop, lite, moving, stage

# kind: (first stage's species, flies?, body, glow, speed)
KINDS = {
    "tangle": ("Tanglet", False, (206, 172, 140), (255, 214, 160), 14),
    "tumble": ("Tumblet", False, (110, 210, 190), (120, 255, 230), 6),
}
NEW_HOMES = {"bridge": ("tangle",), "shore": ("tumble",)}

for _kind, (_sp, _flies, _body, _glow, _speed) in KINDS.items():
    spec = dict(species=_sp, body=_body, color=_glow, speed=_speed)
    if _flies:
        FLIERS[_kind] = dict(spec, turn=2.5)
    else:
        WALKERS[_kind] = spec
    LIT.add(_kind)
_OLD.update(KINDS)
for _place, _kinds in NEW_HOMES.items():
    HOMES[_place] = tuple(HOMES.get(_place, ())) + _kinds


def rope(s, color, pts, w):
    """A twisted rope: a dark under-strand, the strand, and a light twist every few pixels."""
    w = max(1, round(w))
    pygame.draw.lines(s, dark(color, 0.4), False, [(x, y + 1) for x, y in pts], w)
    pygame.draw.lines(s, color, False, pts, w)
    for i in range(0, len(pts) - 1, 2):
        s.set_at((round(pts[i][0]), round(pts[i][1])), lite(color, 0.4))


def loop(cx, cy, rx, ry, a0=0.0, a1=TAU, n=18):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx, cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


# ===================================== the Cloud Bridge ==========================================

def draw_tangle(o, s, t):
    """Tanglet: a loop of glowing rope knotted at the top, hopping on its two frayed ends.
    Tanglash: a figure-eight of rope, one end cracking out like a whip. Tanglehold: a big
    ball of tangled rope with three lassos swinging round it, their ends lit."""
    z, x, n = o.size, o.x, stage(o)
    w = (0.9 + 0.3 * n) * z
    b = hop(o, t, 2.5 if n == 1 else 1.2)
    if n == 1:
        r = 3.6 * z
        cy = o.y - r - 2 * z - b
        rope(s, o.body, loop(x, cy, r, r * 1.1), w)
        for side in (-1, 1):  # frayed ends as feet
            fx = x + side * 1.4 * z
            rope(s, o.body, [(fx, cy + r), (fx + side * 0.6 * z, o.y - b * 0.3)], w)
        knot = (x, cy - r)
    elif n == 2:
        r = 3.6 * z
        cy = o.y - r - 1.5 * z - b
        rope(s, o.body, loop(x - r * 0.9, cy, r, r), w)
        rope(s, o.body, loop(x + r * 0.9, cy, r, r), w)
        lash = [(x + o.facing * (r * 1.8 + i * 1.6 * z), cy - r * 0.4 + math.sin(t * 7 - i * 0.8 + o.phase) * i * 0.5 * z)
                for i in range(8)]
        rope(s, o.body, lash, w * 0.8)
        knot = (x, cy)
    else:
        r = 6.5 * z
        cy = o.y - r - b
        for j in range(5):  # strands wound every which way
            a = j * 1.3 + 0.2
            rope(s, mix(o.body, dark(o.body), 0.15 * (j % 2)), loop(x, cy, r * (1 - 0.06 * j), r * (0.55 + 0.1 * j), a, a + 5.6), w)
        o._tips = []
        for j in range(3):  # three lassos
            a = t * 1.4 + j * TAU / 3 + o.phase
            ex, ey = x + math.cos(a) * r * 2.1, cy + math.sin(a) * r * 0.9 - 2 * z
            mid = (x + math.cos(a - 0.4) * r * 1.4, cy + math.sin(a - 0.4) * r * 0.6 - 4 * z)
            rope(s, o.body, [(x + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.5), mid, (ex, ey)], w * 0.8)
            rope(s, o.body, loop(ex, ey, 1.8 * z, 1.2 * z), w * 0.6)
            o._tips.append((ex, ey))
        knot = (x, cy - r * 0.5)
    kx, ky = knot
    pygame.draw.circle(s, lite(o.body, 0.15), (round(kx), round(ky)), round((1.6 + 0.4 * n) * z))
    eyes(s, kx + o.facing * 0.5 * z, ky, 2.4 * z, z, t, o.phase)
    o._heart = (kx, ky)


def glow_tangle(o, s, t, st, k):
    x, y = getattr(o, "_heart", (o.x, o.y))
    z, n = o.size, stage(o)
    glow(s, x, y, int((4 + 2 * n) * z), o.color, q(30 + 15 * n + 60 * k))
    for ex, ey in getattr(o, "_tips", []) if n == 3 else ():
        glow(s, ex, ey, int(3 * z), o.color, q(60 + 30 * math.sin(t * 3 + ex)))


# ===================================== the Glow Shore ============================================

GLASS = [(110, 210, 190), (150, 230, 140), (120, 170, 240), (240, 200, 120), (230, 160, 210)]


def gem(s, color, cx, cy, r, turn):
    """A rounded piece of sea glass: frosted, with a bright edge where the light comes through."""
    pts = [(cx + math.cos(turn + j * TAU / 6) * r * (1 - 0.15 * (j % 2)), cy + math.sin(turn + j * TAU / 6) * r * 0.8)
           for j in range(6)]
    pygame.draw.polygon(s, dark(color, 0.3), [(px, py + 1) for px, py in pts])
    pygame.draw.polygon(s, color, pts)
    pygame.draw.polygon(s, mix(color, WHITE, 0.25), [pts[0], pts[1], (cx, cy)])
    s.set_at((round(cx - r * 0.3), round(cy - r * 0.3)), WHITE)


def draw_tumble(o, s, t):
    """Tumblet: a pebble of sea glass that tumbles along the sand, lit from inside. Tumbleglass:
    three pieces stuck together on a pale shell, clinking as it goes. Tumblereef: a little reef
    of sea glass of every colour, a lantern of light deep inside, creeping up the beach."""
    z, x, n = o.size, o.x, stage(o)
    roll = o.x * 0.15 * o.facing if moving(o) else 0.0
    o._glints = []
    if n == 1:
        r = 3.4 * z
        cy = o.y - r * 0.8
        gem(s, o.body, x, cy, r, roll)
        eyes(s, x + o.facing * 0.6 * z, cy - 0.3 * z, 2.2 * z, z, t, o.phase)
        o._glints.append((x, cy, r))
    else:
        base = (6 if n == 2 else 9) * z
        pygame.draw.ellipse(s, (226, 214, 222), (x - base, o.y - 2.5 * z, base * 2, 3.5 * z))  # the shell they sit on
        pygame.draw.ellipse(s, (180, 160, 186), (x - base, o.y - 1 * z, base * 2, 2 * z))
        pieces = ([(-2.6, 3, 3.0), (2.8, 3.2, 2.6), (0, 7, 3.2)] if n == 2 else
                  [(-6, 3, 3.2), (-2, 4, 3.6), (3, 3.4, 3.4), (7, 3, 2.6), (-4, 8, 3.0), (1.5, 9, 3.4), (5, 7.5, 2.8),
                   (-1, 13, 3.0), (3, 13.5, 2.4)])
        clink = math.sin(t * 6 + o.phase) * 0.15 if moving(o) else 0.0
        for i, (dx, dy, r) in enumerate(pieces):
            c = GLASS[(i + (n == 3)) % len(GLASS)] if n == 3 else (o.body if i != 1 else GLASS[1])
            px, py = x + dx * z, o.y - dy * z
            gem(s, c, px, py, r * z, 0.3 * i + clink * (1 if i % 2 else -1))
            o._glints.append((px, py, r * z))
        ex, ey = o._glints[-1][0], o._glints[-1][1]
        eyes(s, ex + o.facing * 0.6 * z, ey, 2.4 * z, z, t, o.phase)
    o._heart = (x, o._glints[len(o._glints) // 2][1])


def glow_tumble(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, y = getattr(o, "_heart", (o.x, o.y))
    glow(s, x, y, int((5 + 3 * n) * z), o.color, q(30 + 15 * n + 60 * k))
    for i, (gx, gy, r) in enumerate(getattr(o, "_glints", [])):  # light coming through each piece in turn
        if math.sin(t * 1.5 + i * 1.3 + o.phase) > 0.7:
            glow(s, gx, gy, int(r + 2 * z), GLASS[i % len(GLASS)], 60)


for _kind, (_sp, _flies, *_rest) in KINDS.items():
    cls = Flier if _flies else Walker
    setattr(cls, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(cls, "glow_" + _kind, globals()["glow_" + _kind])


import wave8  # noqa: E402,F401  (fifty more lines, #295-#444: lines8.py)
