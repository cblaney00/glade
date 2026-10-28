"""Drawings for the 50 lines in lines8.py (2026-10-27, his ask), part one: the thirty that live
in the fifteen far places. Part two (the twenty spread over every place) is wave9.py.

His rules, as in wave5-7: no humanoids, no two lines sharing a body, every stage drawn. Each
`draw_<kind>` records its lights in `o._lights` as (x, y, r); one shared `glow_lines8` lights
them all, so a drawing only has to say where it shines.
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, LIT, WALKERS, Flier, Walker
from life import q
from lines8 import LINES
from wave5 import HOMES, KINDS as _OLD, TAU, WHITE, dark, eyes, hop, lite, moving, poly, stage

INK = (30, 20, 40)

for _kind, _names, _types, _shape, _h, _flies, _body, _glow, _speed, _home in LINES:
    spec = dict(species=_names[0], body=_body, color=_glow, speed=_speed)
    if _flies:
        FLIERS[_kind] = dict(spec, turn=2.0)
    else:
        WALKERS[_kind] = spec
    LIT.add(_kind)
    _OLD[_kind] = (_names[0], _flies, _body, _glow, _speed)
    HOMES[_home] = tuple(HOMES.get(_home, ())) + (_kind,)


def R(v):
    return round(v)


def circ(s, c, x, y, r):
    pygame.draw.circle(s, c, (R(x), R(y)), max(1, R(r)))


def ball(s, c, x, y, r):
    """A shaded ball: darker underneath, a highlight up top."""
    circ(s, dark(c, 0.3), x, y + max(1, r * 0.15), r)
    circ(s, c, x, y, r)
    circ(s, lite(c, 0.35), x - r * 0.35, y - r * 0.35, r * 0.3)


def shine_at(o, x, y, r):
    o._lights.append((x, y, r))


def begin(o):
    o._lights = []
    return o.size, o.x, o.y, stage(o)


def glow_lines8(o, s, t, st, k):
    for i, (x, y, r) in enumerate(getattr(o, "_lights", ())):
        glow(s, x, y, max(2, int(r)), o.color, q(30 + 20 * math.sin(t * 2 + i + o.phase) + 60 * k))


def wiggle(o, t, amount=1.0, speed=6):
    return math.sin(t * speed + o.phase) * amount if moving(o) else math.sin(t * 1.5 + o.phase) * amount * 0.3


# ================================== The Frozen Falls =========================================

def draw_hoar(o, s, t):
    """Hoarlet: a ribbon of frozen spray that slides along, frost frills down its back. Hoarcoil:
    longer, coiling up off the ground. Hoarcascade: a long ice ribbon rearing up like a frozen
    waterfall, its frills a row of icicles."""
    z, x, y, n = begin(o)
    segs, ln = (6, 10, 14)[n - 1], (1.8, 2.0, 2.2)[n - 1] * z
    pts = []
    for i in range(segs):
        f = i / segs
        lift = (0, 3 * f, 6 * f * f)[n - 1] * z * 2.4
        px = x - o.facing * i * ln * (1 - 0.3 * (n == 3) * f)
        py = y - 2 * z - lift + math.sin(t * 4 + i * 0.7 + o.phase) * z * (0.6 if moving(o) else 0.2)
        pts.append((px, py))
    for i in range(segs - 1, -1, -1):
        px, py = pts[i]
        w = (1.6 + 0.4 * n) * z * (1 - i / segs * 0.6)
        circ(s, mix(o.body, WHITE, 0.15 * (i % 2)), px, py, w)
        if i % 2 == 0 and i:
            poly(s, lite(o.color, 0.3), [(px - z * 0.6, py - w), (px + z * 0.6, py - w), (px, py - w - (1.5 + n) * z)])
    hx, hy = pts[0]
    poly(s, lite(o.body, 0.2), [(hx + o.facing * 3 * z, hy), (hx, hy - 2 * z), (hx, hy + 1.5 * z)])
    eyes(s, hx + o.facing * z, hy - 0.5 * z, 1.6 * z, z, t, o.phase)
    shine_at(o, hx, hy, 5 * z)
    if n == 3:
        shine_at(o, *pts[segs // 2], 6 * z)


def draw_chill(o, s, t):
    """Chillbell: one bell of ice, ringing as it floats, an icicle for a clapper. Chillchime: three
    bells hung from a frozen bar. Chillcarillon: a ring of bells round a crown of ice, chiming in turn."""
    z, x, y, n = begin(o)
    bells = [(0, 0, 1.0)] if n == 1 else ([(-4, 1, 0.8), (0, -1, 1.0), (4, 1, 0.8)] if n == 2 else
                                          [(math.cos(a) * 7, math.sin(a) * 3, 0.9) for a in [t * 0.6 + j * TAU / 6 for j in range(6)]])
    if n == 2:
        pygame.draw.line(s, lite(o.body, 0.3), (x - 6 * z, y - 4 * z), (x + 6 * z, y - 4 * z), max(1, R(z)))
    if n == 3:
        poly(s, lite(o.body, 0.2), [(x - 4 * z, y - 2 * z), (x - 2 * z, y - 8 * z), (x, y - 4 * z), (x + 2 * z, y - 9 * z),
                                    (x + 4 * z, y - 2 * z)])
    for j, (bx, by, k) in enumerate(sorted(bells, key=lambda b: b[1])):
        cx, cy = x + bx * z, y + by * z
        sw = math.sin(t * 5 + j + o.phase) * 0.25
        w, h = 2.6 * z * k, 3.4 * z * k
        poly(s, o.body, [(cx - w * 0.4 + sw * z, cy - h), (cx + w * 0.4 + sw * z, cy - h), (cx + w, cy + h * 0.6), (cx - w, cy + h * 0.6)])
        pygame.draw.line(s, lite(o.body, 0.5), (cx - w * 0.2, cy - h * 0.7), (cx - w * 0.6, cy + h * 0.4))
        circ(s, o.color, cx + sw * 2 * z, cy + h * 0.8, 0.8 * z * k)
        shine_at(o, cx, cy + h * 0.6, 3 * z * k)
    eyes(s, x + o.facing * 0.5 * z, y - (0 if n < 3 else 4) * z, 1.6 * z, z, t, o.phase)


# ==================================== Aurora Peak ============================================

def draw_veil(o, s, t):
    """Veilet: a little drape of aurora light that ripples as it drifts, two dark eyes in its fold.
    Veilshimmer: three drapes in different colours. Veilcrown: a great curtain of light, hung from a
    crown of pale stars."""
    z, x, y, n = begin(o)
    cols = [o.color, (190, 140, 255), (255, 150, 220)][:n]
    w = (4, 7, 11)[n - 1] * z
    for j, c in enumerate(cols):
        off = (j - (len(cols) - 1) / 2) * 2.5 * z
        for i in range(R(w * 2)):
            f = i / (w * 2)
            px = x - w + i + off
            top = y - 4 * z - math.sin(f * math.pi) * 2 * z
            ln = (5 + 3 * n) * z * (0.6 + 0.4 * math.sin(t * 3 + f * 6 + j + o.phase))
            pygame.draw.line(s, mix(c, (30, 20, 60), 0.35 + 0.4 * f), (px, top), (px, top + ln))
            pygame.draw.line(s, lite(c, 0.4), (px, top), (px, top + ln * 0.25))
    if n == 3:
        for j in range(5):
            circ(s, WHITE, x - w + j * w / 2, y - 5 * z, 0.8 * z)
            shine_at(o, x - w + j * w / 2, y - 5 * z, 3 * z)
    eyes(s, x + o.facing * z, y - 1 * z, 2 * z, z, t, o.phase)
    shine_at(o, x, y, w * 0.9)


def draw_bast(o, s, t):
    """Bastlet: a squat standing stone bound in an iron band, that rocks forward to move and to hit.
    Bastwall: two stones bound together, a rivet-studded band round both. Bastionhold: a little
    round tower of banded stones with a glowing slit for its eyes."""
    z, x, y, n = begin(o)
    rock = wiggle(o, t, 0.12, 5)
    stone, iron = o.body, (90, 96, 120)
    if n < 3:
        stones = [(0, 1.0)] if n == 1 else [(-2.4, 0.9), (2.4, 1.0)]
        for dx, k in stones:
            w, h = 3.4 * z * k, 7 * z * k
            cx = x + dx * z
            pts = [(cx - w, y), (cx + w, y), (cx + w * 0.8 + rock * h, y - h), (cx - w * 0.6 + rock * h, y - h - 1.5 * z)]
            poly(s, stone, pts)
            pygame.draw.line(s, lite(stone, 0.2), pts[3], pts[0])
        by = y - 3.5 * z
        pygame.draw.rect(s, iron, (x - (4 if n == 1 else 6.5) * z + rock * 3 * z, by - z, (8 if n == 1 else 13) * z, 2 * z))
        for k in range(3 if n == 1 else 5):
            circ(s, lite(iron, 0.4), x - (3 if n == 1 else 5.5) * z + k * 2.6 * z + rock * 3 * z, by, 0.5 * z)
        ex, ey = x + rock * 6 * z, y - 6 * z
    else:
        w, h = 6 * z, 13 * z
        pygame.draw.rect(s, dark(stone, 0.25), (x - w, y - h, 2 * w, h))
        pygame.draw.rect(s, stone, (x - w, y - h, w * 1.3, h))
        for k in range(3):
            pygame.draw.rect(s, iron, (x - w, y - h + 2 * z + k * 4 * z, 2 * w, 1.2 * z))
        for k in range(-1, 2):  # battlements
            pygame.draw.rect(s, stone, (x + k * 4 * z - 1.2 * z, y - h - 2 * z, 2.4 * z, 2 * z))
        pygame.draw.rect(s, o.color, (x - 3 * z, y - h + 5 * z, 6 * z, 1.2 * z))
        shine_at(o, x, y - h + 5.6 * z, 5 * z)
        ex, ey = x, y - h + 5.6 * z
    if n < 3:
        eyes(s, ex, ey, 2 * z, z, t, o.phase)
        shine_at(o, ex, ey, 3 * z)


# ===================================== Fern Gully =============================================

def draw_fiddle(o, s, t):
    """Fiddlet: a fern's fiddlehead, curled tight, hopping on its stalk. Fiddlecoil: two curls, one
    starting to unroll into a frond. Fiddlegrove: a clump of half-open fronds walking on its roots,
    a glowing curl at the heart of it."""
    z, x, y, n = begin(o)
    b = hop(o, t, 2) if n == 1 else 0
    def curl(cx, cy, r, open_, c):
        pts = []
        for i in range(30):
            a = i / 30 * TAU * (1.6 - open_)
            rr = r * (1 - i / 36)
            pts.append((cx + math.cos(a) * rr * o.facing, cy + math.sin(a) * rr))
        pygame.draw.lines(s, c, False, pts, max(1, R(z * 0.9)))
        return pts[-1]
    if n == 1:
        pygame.draw.line(s, dark(o.body, 0.2), (x, y - b), (x, y - 5 * z - b), max(1, R(z)))
        circ(s, o.body, x, y - 7 * z - b, 2.6 * z)
        curl(x, y - 7 * z - b, 2.6 * z, 0, lite(o.body, 0.3))
        eyes(s, x + o.facing * 0.6 * z, y - 7.4 * z - b, 1.6 * z, z, t, o.phase)
        shine_at(o, x, y - 7 * z - b, 4 * z)
        return
    stems = [(-2, 0.9, 0.2), (2, 1.0, 0.0)] if n == 2 else [(-5, 1.1, 0.8), (-2, 1.3, 0.5), (2, 1.3, 0.3), (5, 1.1, 0.7), (0, 1.5, 0.0)]
    for dx, k, op in stems:
        sx, top = x + dx * z, y - 10 * z * k
        sway = wiggle(o, t, 1.0, 3) * z
        pygame.draw.line(s, dark(o.body, 0.15), (sx, y), (sx + sway, top), max(1, R(z)))
        if op > 0:
            for j in range(5):  # leaflets where it has unrolled
                ly = top + j * 1.6 * z
                pygame.draw.line(s, o.body, (sx + sway, ly), (sx + sway - 2.5 * z * (1 - j / 6), ly - z))
                pygame.draw.line(s, o.body, (sx + sway, ly), (sx + sway + 2.5 * z * (1 - j / 6), ly - z))
        curl(sx + sway, top - 1.5 * z, 2 * z * k, op, lite(o.body, 0.2))
    eyes(s, x + o.facing * z, y - (8 if n == 2 else 12) * z, 2 * z, z, t, o.phase)
    shine_at(o, x, y - 12 * z, 5 * z)


def draw_glid(o, s, t):
    """Glidlet: a flat disc that skates over the ground on six legs of thread, sparking where they
    touch. Glidrill: longer, two discs one behind the other. Glidrapid: a sleek blade of a thing,
    legs flickering like lightning."""
    z, x, y, n = begin(o)
    bodies = [(0, 1.0)] if n == 1 else ([(0, 1.0), (-4, 0.8)] if n == 2 else [(0, 1.2), (-4, 1.0), (-7.5, 0.7)])
    top = y - 3 * z
    for j in range(3 if n < 3 else 4):  # legs, splayed wide
        for side in (-1, 1):
            lx = x + o.facing * (-j * 2.4 + 2) * z
            k = math.sin(t * 20 + j + side) if moving(o) else 0
            fx = lx + side * (3 + k) * z
            pygame.draw.line(s, lite(o.body, 0.3), (lx, top), (fx, y), 1)
            if moving(o) and (j + int(t * 10)) % 3 == 0:
                s.set_at((R(fx), R(y)), o.color)
    for dx, k in bodies:
        cx = x + o.facing * dx * z
        w = (3.2 + (n == 3) * 1.2) * z * k
        pygame.draw.ellipse(s, dark(o.body, 0.3), (cx - w, top - 1.2 * z * k + 1, 2 * w, 2.4 * z * k))
        pygame.draw.ellipse(s, o.body, (cx - w, top - 1.2 * z * k, 2 * w, 2.4 * z * k))
        pygame.draw.line(s, o.color, (cx - w * 0.6, top), (cx + w * 0.6, top))
    eyes(s, x + o.facing * 2 * z, top - 0.6 * z, 1.6 * z, z, t, o.phase)
    shine_at(o, x, top, 4 * z)


# ===================================== The Lantern Orchard ====================================

def draw_lamp(o, s, t):
    """Lampip: a round glowing fruit with a little wick for a stalk, alight. Lampfruit: bigger, its
    skin thin as paper, the flame inside showing. Lampbough: a short branch walking on its leaves,
    three lamp-fruits hanging off it."""
    z, x, y, n = begin(o)
    b = hop(o, t, 2) if n < 3 else 0
    def fruit(cx, cy, r):
        ball(s, o.body, cx, cy, r)
        if n >= 2:
            for k in (-0.5, 0, 0.5):
                pygame.draw.arc(s, dark(o.body, 0.2), (cx - r * abs(k) - 1, cy - r, 2 * r * abs(k) + 2, 2 * r), -1.6, 1.6)
        fl = 1 + 0.3 * math.sin(t * 12 + cx)
        poly(s, (255, 236, 160), [(cx - 0.6 * z, cy - r), (cx + 0.6 * z, cy - r), (cx, cy - r - 2 * z * fl)])
        shine_at(o, cx, cy, r * 1.6)
    if n < 3:
        r = (3, 4.5)[n - 1] * z
        fruit(x, y - r - b, r)
        eyes(s, x + o.facing * r * 0.3, y - r - b, r * 0.6, z, t, o.phase)
        return
    pygame.draw.line(s, (120, 80, 70), (x - 7 * z, y - 12 * z), (x + 7 * z, y - 13 * z), max(1, R(1.6 * z)))
    for side in (-1, 1):  # it walks on two bunches of leaves
        lx = x + side * 6 * z
        k = wiggle(o, t, 1.5, 8) * side
        pygame.draw.line(s, (120, 80, 70), (lx, y - 12 * z), (lx + k, y - 3 * z), max(1, R(z)))
        poly(s, (110, 180, 120), [(lx + k - 2 * z, y), (lx + k + 2 * z, y), (lx + k, y - 4 * z)])
    for j, dx in enumerate((-4, 0, 4)):
        sw = math.sin(t * 2 + j) * z
        pygame.draw.line(s, (90, 60, 60), (x + dx * z, y - 12.5 * z), (x + dx * z + sw, y - 9.5 * z))
        fruit(x + dx * z + sw, y - 7.5 * z, 2.3 * z)
    eyes(s, x + o.facing * 2 * z, y - 13.5 * z, 2 * z, z, t, o.phase)


def draw_rind(o, s, t):
    """Rindle: a hard-skinned fruit that rolls rather than walks. Rindshell: its rind has grown into
    plates, edged with metal. Rindfort: a great armoured gourd on four stumpy feet, its plates
    riveted, the soft glowing middle showing through a crack."""
    z, x, y, n = begin(o)
    if n < 3:
        r = (3.4, 5)[n - 1] * z
        cy = y - r
        roll = o.x * 0.2 * o.facing if moving(o) else 0
        ball(s, o.body, x, cy, r)
        for j in range(4 if n == 1 else 6):  # the segments of its rind, turning as it rolls
            a = roll + j * TAU / (4 if n == 1 else 6)
            pygame.draw.line(s, dark(o.body, 0.3) if n == 1 else (150, 150, 170),
                             (x + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2), (x + math.cos(a) * r, cy + math.sin(a) * r),
                             1 if n == 1 else max(1, R(z * 0.7)))
        eyes(s, x + o.facing * r * 0.3, cy - r * 0.2, r * 0.6, z, t, o.phase)
        shine_at(o, x, cy, r)
        return
    w, h = 8 * z, 6 * z
    for dx in (-5, -2, 2, 5):
        k = wiggle(o, t, 0.8, 8) * (1 if dx > 0 else -1)
        pygame.draw.rect(s, dark(o.body, 0.35), (x + dx * z - z, y - 2.5 * z + k * 0.3, 2 * z, 2.5 * z))
    pygame.draw.ellipse(s, dark(o.body, 0.3), (x - w, y - 2 * h - 1.5 * z, 2 * w, 2 * h))
    pygame.draw.ellipse(s, o.body, (x - w, y - 2 * h - 2 * z, 2 * w, 2 * h))
    for k in range(-3, 4):
        px = x + k * 2.2 * z
        pygame.draw.line(s, (150, 150, 170), (px, y - 2 * h - 1.4 * z + abs(k) * 0.7 * z), (px, y - 2.4 * z - abs(k) * 0.5 * z))
        circ(s, (200, 200, 220), px, y - h - 2 * z, 0.4 * z)
    pygame.draw.line(s, o.color, (x + 2 * z, y - 2 * h - z), (x + 3.5 * z, y - h - 2 * z), max(1, R(z * 0.6)))
    shine_at(o, x + 3 * z, y - h - 3 * z, 5 * z)
    eyes(s, x + o.facing * 4 * z, y - h - 3 * z, 2.4 * z, z, t, o.phase)


# ===================================== The Sunken Temple ======================================

def draw_mask(o, s, t):
    """Masklet: a little stone mask floating face-forward, water trailing from under it like a veil.
    Maskdrift: a bigger mask with a jade brow, two water veils. Maskoracle: three masks turning slowly
    round a light, each with a different face."""
    z, x, y, n = begin(o)
    def face(cx, cy, r, mood):
        pygame.draw.ellipse(s, dark(o.body, 0.3), (cx - r, cy - r * 1.2 + 1, 2 * r, 2.4 * r))
        pygame.draw.ellipse(s, o.body, (cx - r, cy - r * 1.2, 2 * r, 2.4 * r))
        for side in (-1, 1):
            pygame.draw.ellipse(s, INK, (cx + side * r * 0.4 - r * 0.22, cy - r * 0.35, r * 0.44, r * 0.3))
            s.set_at((R(cx + side * r * 0.4), R(cy - r * 0.2)), o.color)
        if mood == 0:
            pygame.draw.arc(s, INK, (cx - r * 0.4, cy + r * 0.1, r * 0.8, r * 0.5), math.pi, TAU)
        else:
            pygame.draw.line(s, INK, (cx - r * 0.3, cy + r * 0.5), (cx + r * 0.3, cy + r * 0.5 * mood))
        for i in range(6):  # its veil of falling water
            vx = cx - r * 0.7 + i * r * 0.28
            ln = r * (1.4 + 0.4 * math.sin(t * 4 + i + o.phase))
            pygame.draw.line(s, mix(o.color, (60, 120, 160), 0.4), (vx, cy + r * 1.1), (vx, cy + r * 1.1 + ln))
        shine_at(o, cx, cy, r * 1.4)
    if n < 3:
        r = (2.8, 4)[n - 1] * z
        face(x, y, r, 0)
        if n == 2:
            pygame.draw.rect(s, o.color, (x - r * 0.8, y - r * 0.9, r * 1.6, r * 0.2))
        return
    for j in range(3):
        a = t * 0.5 + j * TAU / 3 + o.phase
        face(x + math.cos(a) * 6 * z, y + math.sin(a) * 2 * z, 2.8 * z, (0, 1, -1)[j])
    circ(s, lite(o.color, 0.4), x, y, 1.6 * z)
    shine_at(o, x, y, 7 * z)


def draw_wyrm(o, s, t):
    """Wyrmlet: a little jade dragon curled into a ring, tail in its mouth, rolling along. Wyrmcoil:
    two rings, linked. Wyrmshrine: a tall coil of jade standing on its tail, head raised over its
    loops, a glowing pearl held in its jaw."""
    z, x, y, n = begin(o)
    jade = o.body
    def ring(cx, cy, r, turn):
        for i in range(24):
            a = turn + i / 24 * TAU
            circ(s, mix(jade, lite(jade, 0.4), 0.5 + 0.5 * math.sin(a * 3)), cx + math.cos(a) * r, cy + math.sin(a) * r, z * 1.1)
        hx, hy = cx + math.cos(turn) * r, cy + math.sin(turn) * r
        circ(s, lite(jade, 0.2), hx, hy, z * 1.6)
        return hx, hy
    roll = o.x * 0.15 * o.facing if moving(o) else 0
    if n == 1:
        hx, hy = ring(x, y - 4 * z, 3.4 * z, roll - 1.2)
        eyes(s, hx, hy, 1.2 * z, z, t, o.phase)
        shine_at(o, x, y - 4 * z, 4 * z)
    elif n == 2:
        ring(x - 2.5 * z, y - 4.5 * z, 3.4 * z, roll)
        hx, hy = ring(x + 2.5 * z, y - 4.5 * z, 3.4 * z, -roll - 1.2)
        eyes(s, hx, hy, 1.2 * z, z, t, o.phase)
        shine_at(o, x, y - 4.5 * z, 5 * z)
    else:
        for k in range(3):
            pygame.draw.ellipse(s, dark(jade, 0.15 * k), (x - (5 - k) * z, y - (3 + k * 4) * z, (10 - 2 * k) * z, 4 * z), max(1, R(1.6 * z)))
        neck = [(x + math.sin(i / 3 + t) * 0.5 * z, y - 12 * z - i * 1.2 * z) for i in range(8)]
        for px, py in neck:
            circ(s, jade, px, py, 1.4 * z)
        hx, hy = neck[-1]
        poly(s, lite(jade, 0.2), [(hx, hy - 1.5 * z), (hx + o.facing * 4 * z, hy), (hx, hy + 1.5 * z)])
        for side in (-1, 1):  # whiskers
            pygame.draw.line(s, lite(jade, 0.4), (hx + o.facing * 3 * z, hy), (hx + o.facing * 6 * z, hy + side * 2 * z))
        circ(s, (240, 255, 240), hx + o.facing * 4.5 * z, hy + 0.5 * z, 1.1 * z)
        eyes(s, hx + o.facing * z, hy - 0.6 * z, 1.2 * z, z, t, o.phase)
        shine_at(o, hx + o.facing * 4.5 * z, hy, 5 * z)


# ===================================== The Moon Dunes =========================================

def draw_dune(o, s, t):
    """Dunelet: a little heap of sand with two eyes that slides along, leaving a ghostly trail.
    Dunedrift: a longer drift, a wisp of light streaming off its crest. Dunewraith: a dune with a
    hollow, glowing face that rises and sinks as it goes."""
    z, x, y, n = begin(o)
    w, h = (4, 7, 10)[n - 1] * z, (2.5, 3.6, 6)[n - 1] * z
    rise = math.sin(t * 1.4 + o.phase) * z * (n == 3)
    pts = [(x + (i / 16 - 0.5) * 2 * w, y - math.sin(i / 16 * math.pi) ** 1.5 * (h + rise)) for i in range(17)]
    poly(s, o.body, pts + [(x + w, y), (x - w, y)])
    pygame.draw.lines(s, lite(o.body, 0.25), False, pts[3:10])
    for i in range(6 * n):  # the trail of ghost-light off its crest
        f = i / (6 * n)
        tx = x - o.facing * (w * 0.2 + f * w * 1.3)
        ty = y - h - rise + f * h * 0.4 + math.sin(t * 3 + f * 6) * z
        s.set_at((R(tx), R(ty)), mix(o.color, (40, 30, 80), f))
    if n == 3:
        pygame.draw.ellipse(s, INK, (x - 3 * z, y - h * 0.8 - rise, 6 * z, 4 * z))
        for side in (-1, 1):
            circ(s, o.color, x + side * 1.2 * z, y - h * 0.65 - rise, 0.8 * z)
        shine_at(o, x, y - h * 0.6, 6 * z)
    else:
        eyes(s, x + o.facing * w * 0.2, y - h * 0.55, 1.8 * z, z, t, o.phase)
        shine_at(o, x, y - h, 3 * z * n)


def draw_prickle(o, s, t):
    """Pricklet: a round cactus that rolls about, spines all over, a pink bud on top. Pricklejab: two
    flat pads, one held up ready to flick its spines. Prickleking: a tall barrel cactus crowned with
    glowing flowers, a ring of long spines it can shoot."""
    z, x, y, n = begin(o)
    def spines(cx, cy, rx, ry, k, ln):
        for j in range(k):
            a = j * TAU / k + 0.2
            px, py = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            pygame.draw.line(s, (240, 240, 220), (px, py), (px + math.cos(a) * ln, py + math.sin(a) * ln))
    if n == 1:
        r = 3.2 * z
        cy = y - r - hop(o, t, 1.5)
        ball(s, o.body, x, cy, r)
        spines(x, cy, r, r, 12, 1.2 * z)
        circ(s, (255, 150, 200), x, cy - r, 1 * z)
        eyes(s, x + o.facing * z, cy, 1.8 * z, z, t, o.phase)
        shine_at(o, x, cy - r, 3 * z)
    elif n == 2:
        jab = max(0, math.sin(t * 3 + o.phase)) * 2 * z
        for dx, dy, w, h in ((0, 0, 4, 5), (o.facing * (5 + jab / z), -4, 3, 3.5)):
            cx, cy = x + dx * z, y - (5 + h) * z + dy * z + (h - 5) * z
            pygame.draw.ellipse(s, dark(o.body, 0.25), (cx - w * z, cy - h * z + 1, 2 * w * z, 2 * h * z))
            pygame.draw.ellipse(s, o.body, (cx - w * z, cy - h * z, 2 * w * z, 2 * h * z))
            spines(cx, cy, w * z, h * z, 10, z)
        eyes(s, x + o.facing * z, y - 6 * z, 2 * z, z, t, o.phase)
        shine_at(o, x, y - 6 * z, 4 * z)
    else:
        w, h = 5 * z, 12 * z
        pygame.draw.rect(s, dark(o.body, 0.25), (x - w, y - h, 2 * w, h), border_radius=R(w))
        pygame.draw.rect(s, o.body, (x - w, y - h, 1.5 * w, h), border_radius=R(w))
        for k in range(-2, 3):
            pygame.draw.line(s, dark(o.body, 0.35), (x + k * 2 * z, y - h + 2 * z), (x + k * 2 * z, y - 1 * z))
        spines(x, y - h * 0.5, w, h * 0.5, 16, 2.4 * z)
        for j in range(5):
            fx = x + (j - 2) * 2 * z
            circ(s, (255, 150, 200) if j % 2 else o.color, fx, y - h - 0.5 * z, 1.1 * z)
            shine_at(o, fx, y - h, 2.5 * z)
        eyes(s, x + o.facing * 1.5 * z, y - h * 0.6, 2.4 * z, z, t, o.phase)


# ===================================== The Lava Lake ===========================================

def draw_cinder(o, s, t):
    """Cinderlet: a crawling lump of cooling lava, crust on top, glowing underneath, a little snout.
    Cindercrawl: longer, a ridge of crust plates down its back like a dragon's. Cindermaw: a great
    magma beast on four stumpy legs, its jaw a crack of fire."""
    z, x, y, n = begin(o)
    crust, hot = o.body, o.color
    length = (6, 11, 14)[n - 1] * z
    hgt = (3, 4, 7)[n - 1] * z
    legs = 0 if n < 3 else 4
    base = y - (2.5 * z if legs else 0)
    for j in range(legs):
        lx = x + (j - 1.5) * 3.5 * z
        k = wiggle(o, t, 1, 7) * (1 if j % 2 else -1)
        pygame.draw.rect(s, crust, (lx - z, base - z + k * 0.3, 2.2 * z, 3.5 * z))
    pts = [(x - length / 2 + i / 12 * length, base - math.sin(i / 12 * math.pi) * hgt) for i in range(13)]
    poly(s, hot, pts + [(x + length / 2, base), (x - length / 2, base)])
    for px, py in pts[1:-1:2]:  # crust plates, the glow between them
        poly(s, crust, [(px - 1.5 * z, py + 1), (px + 1.5 * z, py + 1), (px, py - (1 + n) * z)])
    hx = x + o.facing * length / 2
    poly(s, crust, [(hx, base - hgt * 0.7), (hx + o.facing * 3 * z, base - hgt * 0.3), (hx, base)])
    if n == 3:
        pygame.draw.line(s, (255, 230, 150), (hx, base - hgt * 0.35), (hx + o.facing * 3 * z, base - hgt * 0.32), max(1, R(z * 0.8)))
    eyes(s, hx - o.facing * z, base - hgt * 0.6, 1.4 * z, z, t, o.phase)
    shine_at(o, x, base - hgt * 0.4, length * 0.5)


def draw_slag(o, s, t):
    """Slaglet: a dull grey blob of slag, molten orange showing through its cracks. Slagshell: a
    heavy dome of slag on a glowing foot. Slagbastion: a slow, square heap of iron slag with three
    chimneys smoking off its back."""
    z, x, y, n = begin(o)
    w, h = (3.4, 5.5, 8)[n - 1] * z, (3, 4.5, 8)[n - 1] * z
    if n < 3:
        pygame.draw.ellipse(s, o.color, (x - w, y - 1.5 * z, 2 * w, 2 * z))
        pygame.draw.ellipse(s, dark(o.body, 0.3), (x - w, y - h * 2 + 1, 2 * w, h * 2))
        pygame.draw.ellipse(s, o.body, (x - w, y - h * 2, 2 * w, h * 2 - z))
    else:
        pygame.draw.rect(s, dark(o.body, 0.3), (x - w, y - h, 2 * w, h))
        pygame.draw.rect(s, o.body, (x - w, y - h, w * 1.4, h))
        for k in (-1, 0, 1):
            cx = x + k * 4 * z
            pygame.draw.rect(s, dark(o.body, 0.15), (cx - z, y - h - 3 * z, 2 * z, 3 * z))
            for i in range(4):  # smoke
                sy = y - h - 3 * z - i * 2 * z - (t * 6 + k * 3) % 2 * z
                circ(s, mix((180, 170, 180), (60, 50, 70), i / 4), cx + math.sin(t + i + k) * z, sy, (0.6 + i * 0.3) * z)
    for j in range(2 + n):  # cracks of fire
        a = j * 1.9 + 0.4
        cx, cy = x + math.cos(a) * w * 0.5, y - h * (0.5 if n == 3 else 1) + math.sin(a) * h * 0.4
        pygame.draw.line(s, o.color, (cx, cy), (cx + z * 1.5, cy + z))
        shine_at(o, cx, cy, 2 * z)
    eyes(s, x + o.facing * w * 0.3, y - h * (0.6 if n == 3 else 1.1), 2 * z, z, t, o.phase)


# ===================================== The Coral Grotto ========================================

def draw_coral(o, s, t):
    """Coralet: a little knot of coral that walks on its tube feet. Coralbloom: a fan of coral,
    stinging tips glowing. Coralspire: a tall branching coral, all its tips lit, creeping slowly."""
    z, x, y, n = begin(o)
    feet = (4, 6, 8)[n - 1]
    for j in range(feet):  # tube feet
        fx = x + (j - feet / 2 + 0.5) * 1.2 * z
        k = wiggle(o, t, 0.6, 9) * (1 if j % 2 else -1)
        pygame.draw.line(s, lite(o.body, 0.3), (fx, y - 1.5 * z), (fx + k, y))
    def branch(px, py, a, ln, depth):
        nx, ny = px + math.cos(a) * ln, py + math.sin(a) * ln
        pygame.draw.line(s, o.body, (px, py), (nx, ny), max(1, R(z * depth * 0.5)))
        if depth > 1:
            for da in (-0.45, 0.45):
                branch(nx, ny, a + da + math.sin(t + depth) * 0.05, ln * 0.75, depth - 1)
        else:
            circ(s, lite(o.color, 0.4), nx, ny, 0.6 * z)
            shine_at(o, nx, ny, 1.6 * z)
    branch(x, y - 1.5 * z, -math.pi / 2, (2.4, 3.2, 4.2)[n - 1] * z, n + 1)
    eyes(s, x + o.facing * 0.5 * z, y - 2.6 * z, 1.6 * z, z, t, o.phase)


def draw_pearl(o, s, t):
    """Pearlet: a black pearl that rolls about in a little hinged shell, peeping out. Pearlnight: the
    shell wide open, the pearl shining dark violet. Pearlnoir: three shells stacked, the top one
    holding a great black pearl ringed in silver."""
    z, x, y, n = begin(o)
    gape = 0.3 + 0.3 * math.sin(t * 1.3 + o.phase) + (n >= 2) * 0.3
    def shell(cx, cy, r, pearl):
        pygame.draw.ellipse(s, dark(o.body, 0.2), (cx - r, cy - r * 0.4, 2 * r, r * 0.9))
        for k in range(-2, 3):
            pygame.draw.line(s, lite(o.body, 0.3), (cx, cy + r * 0.4), (cx + k * r * 0.4, cy - r * 0.2))
        circ(s, (40, 30, 60), cx, cy - r * 0.4, pearl)
        circ(s, (200, 180, 255), cx - pearl * 0.3, cy - r * 0.4 - pearl * 0.3, pearl * 0.3)
        lid = [(cx - r + i / 10 * 2 * r, cy - r * 0.4 - math.sin(i / 10 * math.pi) * r * 0.6 - gape * r) for i in range(11)]
        poly(s, o.body, lid + [(cx + r, cy - r * 0.4 - gape * r * 0.4), (cx - r, cy - r * 0.4 - gape * r * 0.4)])
        shine_at(o, cx, cy - r * 0.4, pearl * 2)
        return cx, cy - r * 0.4
    if n < 3:
        r = (3, 4.4)[n - 1] * z
        px, py = shell(x, y - r * 0.5, r, r * 0.45)
    else:
        for k in range(2):
            pygame.draw.ellipse(s, dark(o.body, 0.1 * k), (x - (5 - k) * z, y - (3 + 3 * k) * z, (10 - 2 * k) * z, 3.6 * z))
        px, py = shell(x, y - 9 * z, 4.6 * z, 2.4 * z)
        pygame.draw.circle(s, (210, 210, 230), (R(px), R(py)), R(2.8 * z), 1)
    eyes(s, px + o.facing * 0.4 * z, py - 0.2 * z, 1.4 * z, z, t, o.phase)


# ===================================== The Kelp Deep ===========================================

def draw_kelp(o, s, t):
    """Kelplet: a bladder-float of kelp with frond fins, swimming. Kelpcoil: the float has a long
    leafy tail that ripples behind. Kelpleviathan: a long dragon of kelp, frond after frond, a crest
    of glowing floats down its back."""
    z, x, y, n = begin(o)
    segs = (3, 8, 16)[n - 1]
    pts = [(x - o.facing * i * 2 * z, y + math.sin(t * 3 - i * 0.6 + o.phase) * z * (0.5 + i * 0.1)) for i in range(segs)]
    for i in range(segs - 1, 0, -1):
        px, py = pts[i]
        for side in (-1, 1):
            pygame.draw.ellipse(s, mix(o.body, (60, 120, 90), 0.2 * (i % 2)), (px - 1.5 * z, py + side * 1.6 * z - z, 3 * z, 2 * z))
        if n == 3 and i % 3 == 0:
            circ(s, o.color, px, py - 2 * z, 0.9 * z)
            shine_at(o, px, py - 2 * z, 2.5 * z)
    hx, hy = pts[0]
    r = (2.4, 2.8, 3)[n - 1] * z
    ball(s, lite(o.body, 0.15), hx, hy, r)
    if n == 3:
        poly(s, o.body, [(hx, hy - r), (hx + o.facing * r * 2, hy), (hx, hy + r * 0.6)])
        for k in range(3):
            pygame.draw.line(s, o.body, (hx - o.facing * z, hy - r), (hx - o.facing * (2 + k) * z, hy - r - (2 + k) * z))
    eyes(s, hx + o.facing * r * 0.4, hy - r * 0.2, 1.6 * z, z, t, o.phase)
    shine_at(o, hx, hy, r * 1.4)


def draw_lure(o, s, t):
    """Lurelet: a little dark blob of the deep with a stalk on its head, a light on the end of it.
    Lurelamp: bigger, its mouth wide, two lures. Lureabyss: a huge dark round mouth of a thing, a
    crown of lures swaying above, its teeth glowing faintly."""
    z, x, y, n = begin(o)
    r = (3, 4.6, 7)[n - 1] * z
    ball(s, o.body, x, y, r)
    mouth = (0.3, 0.6, 0.9)[n - 1]
    pygame.draw.arc(s, o.color if n == 3 else INK, (x + o.facing * r * 0.1 - r * 0.6, y - r * 0.1, r * 1.2, r * mouth), math.pi, TAU)
    lures = 1 if n == 1 else (2 if n == 2 else 5)
    for j in range(lures):
        a = -math.pi / 2 + (j - (lures - 1) / 2) * 0.5 + math.sin(t * 1.5 + j) * 0.15
        pts = [(x + math.cos(a) * r * (0.8 + i * 0.25) + o.facing * i * 0.6 * z, y + math.sin(a) * r * (0.8 + i * 0.22) + i * i * 0.2 * z)
               for i in range(6)]
        pygame.draw.lines(s, lite(o.body, 0.2), False, pts)
        circ(s, lite(o.color, 0.4), *pts[-1], 0.9 * z)
        shine_at(o, *pts[-1], 3 * z)
    eyes(s, x + o.facing * r * 0.35, y - r * 0.35, 1.6 * z, z, t, o.phase)


# ===================================== Lighthouse Point =========================================

def draw_lens(o, s, t):
    """Lenslet: a round glass lens rolling on its rim, light caught in its middle. Lensflare: two
    lenses, one turning to throw a beam. Lensbeacon: a faceted lantern of ringed glass that turns,
    its beam sweeping round."""
    z, x, y, n = begin(o)
    if n < 3:
        lenses = [(0, 3.2)] if n == 1 else [(-2.6, 3.0), (2.6, 3.6)]
        for j, (dx, r) in enumerate(lenses):
            cx, cy = x + dx * z, y - r * z
            squash = abs(math.cos(t * 0.8 + j + o.phase)) if n == 2 and j == 1 else 1
            rect = (cx - r * z * squash, cy - r * z, 2 * r * z * squash + 1, 2 * r * z)
            pygame.draw.ellipse(s, mix(o.body, (60, 80, 110), 0.3), rect)
            pygame.draw.ellipse(s, lite(o.body, 0.5), rect, 1)
            pygame.draw.ellipse(s, o.color, (cx - z * squash, cy - z, 2 * z * squash + 1, 2 * z))
            shine_at(o, cx, cy, r * z * 1.2)
        eyes(s, x + o.facing * 0.5 * z, y - 4 * z, 1.6 * z, z, t, o.phase)
        if n == 2:  # a short beam
            a = t * 0.8 + o.phase
            ex = x + math.cos(a) * 14 * z
            pygame.draw.line(s, mix(o.color, (0, 0, 0), 0.4), (x + 2.6 * z, y - 3.6 * z), (ex, y - 3.6 * z))
        return
    w, h = 4.5 * z, 11 * z
    for k in range(5):
        yy = y - h + k * 2.2 * z
        pygame.draw.rect(s, mix(o.body, (60, 80, 110), 0.2 + 0.1 * (k % 2)), (x - w + abs(k - 2) * 0.4 * z, yy, 2 * w - abs(k - 2) * 0.8 * z, 2 * z))
        pygame.draw.line(s, lite(o.body, 0.5), (x - w * 0.6, yy), (x + w * 0.6, yy))
    pygame.draw.rect(s, (90, 90, 110), (x - w, y - 1.5 * z, 2 * w, 1.5 * z))
    circ(s, o.color, x, y - h * 0.55, 2 * z)
    a = t * 0.8 + o.phase
    k = math.cos(a)
    pygame.draw.polygon(s, mix(o.color, (0, 0, 0), 0.55), [(x, y - h * 0.55), (x + k * 26 * z, y - h * 0.55 - 4 * z), (x + k * 26 * z, y - h * 0.55 + 4 * z)])
    shine_at(o, x, y - h * 0.55, 8 * z)
    eyes(s, x + o.facing * z, y - h - 1 * z, 1.8 * z, z, t, o.phase)


def draw_gust(o, s, t):
    """Gustlet: a puff of sea wind you can see, a curl at its front and a long streaming tail.
    Gustcurl: two curls rolling round each other. Gustgale: a broad swirl of wind with streamers off
    every side, a gull's-eye of calm in the middle."""
    z, x, y, n = begin(o)
    curls = 1 if n == 1 else (2 if n == 2 else 4)
    for j in range(curls):
        a0 = t * (2 + j * 0.3) + j * TAU / curls + o.phase
        cx = x + (math.cos(a0) * 2.5 * z if n > 1 else 0)
        cy = y + (math.sin(a0) * 1.5 * z if n > 1 else 0)
        pts = []
        for i in range(28):
            a = a0 + i * 0.32
            r = (3.2 + 0.6 * n) * z * (1 - i / 34)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7))
        pygame.draw.lines(s, o.body, False, pts, max(1, R(z * 0.8)))
    for i in range(3 + 2 * n):  # streamers off the back
        f = i / (3 + 2 * n)
        sy = y + (f - 0.5) * 4 * z
        ln = (6 + 4 * n) * z * (1 - abs(f - 0.5))
        pts = [(x - o.facing * (3 * z + k * ln / 5), sy + math.sin(t * 6 - k + i) * z * 0.6) for k in range(6)]
        pygame.draw.lines(s, mix(o.body, (120, 140, 190), 0.4), False, pts)
    eyes(s, x + o.facing * 0.5 * z, y - 0.3 * z, 1.6 * z, z, t, o.phase)
    shine_at(o, x, y, 4 * z)


# ===================================== The Comet Crater =========================================

def draw_crater(o, s, t):
    """Craterlet: a pitted lump of star-iron that tumbles along. Cratermaw: its middle has fallen in,
    a bowl of a mouth. Craterhulk: a great iron boulder on four legs, its back a whole cratered
    landscape with a light in the deepest pit."""
    z, x, y, n = begin(o)
    if n < 3:
        r = (3.2, 5)[n - 1] * z
        cy = y - r
        turn = o.x * 0.1 * o.facing if moving(o) else 0
        ball(s, o.body, x, cy, r)
        for j in range(5):  # pits
            a = turn + j * 1.3
            circ(s, dark(o.body, 0.35), x + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, r * 0.18)
        if n == 2:
            pygame.draw.ellipse(s, INK, (x - r * 0.5 + o.facing * r * 0.2, cy, r, r * 0.5))
            shine_at(o, x + o.facing * r * 0.2, cy + r * 0.25, r)
        eyes(s, x + o.facing * r * 0.3, cy - r * 0.35, r * 0.5, z, t, o.phase)
        shine_at(o, x, cy, r * 0.6)
        return
    w, h = 9 * z, 6 * z
    for j in range(4):
        lx = x + (j - 1.5) * 4.5 * z
        k = wiggle(o, t, 1, 6) * (1 if j % 2 else -1)
        pygame.draw.rect(s, dark(o.body, 0.3), (lx - 1.2 * z, y - 3 * z + k * 0.3, 2.4 * z, 3 * z))
    pygame.draw.ellipse(s, dark(o.body, 0.25), (x - w, y - 2 * h - 2 * z, 2 * w, 2 * h))
    pygame.draw.ellipse(s, o.body, (x - w, y - 2 * h - 3 * z, 2 * w, 2 * h - z))
    for j, (dx, dy, r) in enumerate(((-4, -10, 2), (1, -12, 3), (5, -9, 1.6), (-1, -8, 1.2))):
        pygame.draw.ellipse(s, dark(o.body, 0.4), (x + dx * z - r * z, y + dy * z - r * 0.5 * z, 2 * r * z, r * z))
        pygame.draw.arc(s, lite(o.body, 0.3), (x + dx * z - r * z, y + dy * z - r * 0.5 * z, 2 * r * z, r * z), 0, math.pi)
    circ(s, o.color, x + z, y - 12 * z, 0.9 * z)
    shine_at(o, x + z, y - 12 * z, 4 * z)
    eyes(s, x + o.facing * 6 * z, y - 7 * z, 2 * z, z, t, o.phase)


def draw_nova(o, s, t):
    """Novalet: a nugget of comet-ice with a short crackling tail. Novaflare: its tail forks and
    sparks. Novaburst: a blazing core of ice ringed with frozen shards, three tails whipping round."""
    z, x, y, n = begin(o)
    tails = (1, 2, 3)[n - 1]
    for j in range(tails):
        a = math.pi * (o.facing < 0) + (j - (tails - 1) / 2) * 0.5 + (t * 1.5 if n == 3 else 0) + (j * TAU / 3 if n == 3 else 0)
        prev = (x, y)
        for i in range(1, 7 + 2 * n):
            jit = math.sin(t * 30 + i * 2.1 + j) * z * 0.8
            px = x - math.cos(a) * i * 1.6 * z + math.sin(a) * jit
            py = y - math.sin(a) * i * 1.6 * z + math.cos(a) * jit
            pygame.draw.line(s, mix(o.color, (60, 60, 120), i / (9 + 2 * n)), prev, (px, py))
            prev = (px, py)
    r = (2.2, 3, 4)[n - 1] * z
    poly(s, o.body, [(x + math.cos(a) * r * (1 - 0.3 * (k % 2)), y + math.sin(a) * r * (1 - 0.3 * (k % 2)))
                     for k, a in enumerate([k * TAU / 8 + t * 0.4 for k in range(8)])])
    if n == 3:
        for k in range(6):
            a = k * TAU / 6 - t * 0.6
            poly(s, lite(o.body, 0.2), [(x + math.cos(a) * r * 1.4, y + math.sin(a) * r * 1.4),
                                        (x + math.cos(a + 0.15) * r * 2.1, y + math.sin(a + 0.15) * r * 2.1),
                                        (x + math.cos(a - 0.15) * r * 2.1, y + math.sin(a - 0.15) * r * 2.1)])
    eyes(s, x + o.facing * 0.4 * z, y, 1.6 * z, z, t, o.phase)
    shine_at(o, x, y, r * 2)


# ===================================== The Moonpetal Garden ========================================

def draw_wilt(o, s, t):
    """Wiltlet: a drooping moonflower that drifts with no stem, its petals trailing like a sheet.
    Wiltbloom: three heads on one bent stem, floating. Wiltwraith: a great pale flower hanging face
    down, its petals long and ragged, a faint light inside."""
    z, x, y, n = begin(o)
    heads = [(0, 0, 1.0)] if n != 2 else [(-3, 1, 0.8), (0, -1, 1.0), (3, 1, 0.8)]
    k = 1.0 if n < 3 else 1.7
    if n == 2:
        pygame.draw.lines(s, (130, 170, 140), False, [(x - 3 * z, y - 2 * z), (x, y - 5 * z), (x + 3 * z, y - 2 * z)])
    for hx, hy, sc_ in heads:
        cx, cy = x + hx * z, y + hy * z
        r = 2.6 * z * sc_ * k
        for j in range(7):  # petals hanging down, ragged and swaying
            a = math.pi * (0.1 + 0.8 * j / 6)
            ln = r * (1.6 + 0.5 * math.sin(t * 2 + j + o.phase)) * (1.4 if n == 3 else 1)
            ex, ey = cx + math.cos(a) * r * 0.6, cy + math.sin(a) * ln
            pygame.draw.polygon(s, mix(o.body, (150, 150, 200), j % 2 * 0.2), [(cx - z * 0.8, cy), (cx + z * 0.8, cy), (ex, ey)])
        pygame.draw.ellipse(s, lite(o.body, 0.3), (cx - r, cy - r * 0.5, 2 * r, r))
        shine_at(o, cx, cy + r * 0.6, r * 1.2)
    eyes(s, x + o.facing * 0.5 * z, y - 0.6 * z * k, 1.8 * z, z, t, o.phase)


def draw_spout(o, s, t):
    """Spoutlet: a little stone basin that hops, a jet of water springing from it. Spoutfount: a
    basin on a pedestal, the water arching out both sides. Spoutcascade: three basins stacked,
    water spilling from each into the next."""
    z, x, y, n = begin(o)
    b = hop(o, t, 2) if n == 1 else 0
    tiers = n
    top = y - b
    for k in range(tiers):
        w = (4 - k * 1.1) * z * (1 + 0.2 * (n - 1))
        by = top - (2.5 + k * 4.5) * z
        if k == 0 and n > 1:
            pygame.draw.rect(s, dark(o.body, 0.2), (x - z, by, 2 * z, 2.5 * z))
        pygame.draw.ellipse(s, dark(o.body, 0.3), (x - w, by - 1.5 * z, 2 * w, 3 * z))
        pygame.draw.ellipse(s, o.body, (x - w, by - 2 * z, 2 * w, 2.6 * z))
        pygame.draw.ellipse(s, (110, 170, 230), (x - w * 0.8, by - 1.7 * z, 1.6 * w, 1.4 * z))
        if k < tiers - 1:
            pygame.draw.rect(s, o.body, (x - 0.6 * z, by - 4.5 * z, 1.2 * z, 3 * z))
        for side in (-1, 1):  # water spilling over the lip
            if n > 1:
                for i in range(5):
                    circ(s, (190, 230, 255), x + side * (w + i * 0.4 * z), by - z + i * 1.2 * z + (t * 10 % 1.2) * z, 0.5 * z)
    jy = top - (2.5 + (tiers - 1) * 4.5) * z - 2 * z
    jet = (3 + math.sin(t * 5 + o.phase)) * z
    pygame.draw.line(s, (200, 236, 255), (x, jy), (x, jy - jet), max(1, R(z * 0.8)))
    circ(s, (230, 245, 255), x, jy - jet, 0.8 * z)
    shine_at(o, x, jy - jet, 3 * z)
    eyes(s, x + o.facing * z, top - 3.5 * z, 1.8 * z, z, t, o.phase)


# ===================================== The Floating Isles ===========================================

def draw_clod(o, s, t):
    """Clodlet: a clod of earth floating on its own, roots dangling, a sprout on top. Clodfloat: a
    bigger lump with a little tree and a trickle of water off its edge. Clodcontinent: a whole tiny
    floating island with a pond, three trees and a waterfall."""
    z, x, y, n = begin(o)
    w = (3, 5, 8)[n - 1] * z
    bob = math.sin(t * 1.2 + o.phase) * z
    cy = y + bob
    poly(s, o.body, [(x - w, cy), (x + w, cy), (x + w * 0.5, cy + w * 0.6), (x, cy + w), (x - w * 0.6, cy + w * 0.5)])
    pygame.draw.ellipse(s, (110, 190, 130), (x - w - 1, cy - 2 * z, 2 * w + 2, 3 * z))
    for k in range(3 + n):  # roots
        rx = x - w * 0.5 + k * w / (2 + n)
        pygame.draw.line(s, dark(o.body, 0.3), (rx, cy + w * 0.5), (rx + math.sin(t + k) * z, cy + w * 0.5 + (2 + n) * z))
    if n == 1:
        pygame.draw.line(s, (110, 190, 130), (x, cy - z), (x, cy - 3 * z))
        circ(s, (150, 230, 150), x + z, cy - 3 * z, 0.8 * z)
    trees = 0 if n == 1 else (1 if n == 2 else 3)
    for k in range(trees):
        tx = x + (k - (trees - 1) / 2) * 4 * z
        pygame.draw.line(s, (120, 90, 80), (tx, cy - z), (tx, cy - 4 * z), max(1, R(z * 0.6)))
        circ(s, (110, 190, 130), tx, cy - 5 * z, 1.8 * z)
    if n >= 2:  # water off the edge
        for i in range(8 * n):
            circ(s, (190, 230, 255), x + w * 0.9, cy + i * 0.9 * z, 0.4 * z)
    if n == 3:
        pygame.draw.ellipse(s, (110, 170, 230), (x - 6 * z, cy - 1.5 * z, 4 * z, 1.5 * z))
    eyes(s, x + o.facing * w * 0.2, cy + w * 0.3, 2 * z, z, t, o.phase)
    shine_at(o, x, cy + w * 0.3, w)


def draw_zeph(o, s, t):
    """Zephlet: a little kite of cloud, diamond-shaped, its tail of knots streaming behind.
    Zephwing: the kite has grown wings and a dragon's head. Zephyrion: a long, many-winged dragon of
    cloud and wind, ribbons rippling all down its length."""
    z, x, y, n = begin(o)
    tail = [(x - o.facing * i * 2.2 * z, y + math.sin(t * 5 - i * 0.7 + o.phase) * z * (1 + i * 0.15)) for i in range((5, 9, 14)[n - 1])]
    pygame.draw.lines(s, lite(o.body, 0.2), False, [(x, y)] + tail)
    for i, (px, py) in enumerate(tail[1::2]):
        poly(s, o.color if n < 3 else mix(o.body, o.color, 0.5), [(px, py - z), (px + z, py), (px, py + z), (px - z, py)])
        if n == 3:
            for side in (-1, 1):
                pygame.draw.line(s, o.body, (px, py), (px - o.facing * 2 * z, py + side * 3 * z * (1 - i / 7)))
    r = (3, 3.6, 4)[n - 1] * z
    poly(s, o.body, [(x + o.facing * r, y), (x, y - r * 0.8), (x - o.facing * r * 0.7, y), (x, y + r * 0.8)])
    if n >= 2:
        flap = math.sin(t * 6 + o.phase) * r
        for side in (-1, 1):
            poly(s, lite(o.body, 0.25), [(x, y), (x - o.facing * r * 0.5, y + side * (r * 1.8 + flap * 0.3)), (x - o.facing * r * 1.4, y + side * r * 0.5)])
        hx = x + o.facing * r * 1.2
        poly(s, o.body, [(hx, y - r * 0.4), (hx + o.facing * r * 0.9, y), (hx, y + r * 0.3)])
        pygame.draw.line(s, lite(o.body, 0.4), (hx, y - r * 0.4), (hx - o.facing * r * 0.5, y - r * 0.9))
    eyes(s, x + o.facing * r * (1.3 if n >= 2 else 0.2), y - r * 0.15, 1.4 * z, z, t, o.phase)
    shine_at(o, x, y, r * 1.5)


# ===================================== The Storm Peaks ===============================================

def draw_bolt(o, s, t):
    """Boltlet: a little zig-zag of lightning on two legs, crackling as it hops. Boltcoil: a spring
    of lightning, coiled, that bounds along. Boltstrider: a long, crackling zig-zag dragon striding
    on four thin legs, sparks running off its back."""
    z, x, y, n = begin(o)
    b = hop(o, t, 2.5 if n < 3 else 1)
    jit = lambda i: math.sin(t * 25 + i * 3.1 + o.phase) * 0.6 * z  # noqa: E731
    if n == 1:
        pts = [(x - 2 * z, y - 9 * z), (x + 1.5 * z, y - 6 * z), (x - 1 * z, y - 5 * z), (x + 2 * z, y - 2 * z)]
        for side in (-1, 1):
            pygame.draw.line(s, dark(o.body, 0.2), (x, y - 3 * z - b), (x + side * 1.4 * z, y))
        pts = [(px + jit(i), py - b) for i, (px, py) in enumerate(pts)]
        pygame.draw.lines(s, o.body, False, pts, max(2, R(1.4 * z)))
        hx, hy = pts[0]
    elif n == 2:
        pts = [(x + (2 if i % 2 else -2) * z + jit(i), y - b - i * 1.6 * z * (0.7 + 0.3 * abs(math.sin(t * 6)))) for i in range(7)]
        pygame.draw.lines(s, o.body, False, pts, max(2, R(1.2 * z)))
        hx, hy = pts[-1]
    else:
        pts = [(x - o.facing * (i * 2.4 - 6) * z, y - 7 * z - b + (1.5 if i % 2 else -1.5) * z + jit(i)) for i in range(8)]
        for j in range(4):
            lx = pts[1 + j * 2][0]
            k = wiggle(o, t, 1.4, 8) * (1 if j % 2 else -1)
            pygame.draw.line(s, dark(o.body, 0.2), (lx, pts[1 + j * 2][1]), (lx + k, y))
        pygame.draw.lines(s, o.body, False, pts, max(2, R(1.6 * z)))
        hx, hy = pts[0]
        poly(s, o.body, [(hx, hy - z), (hx + o.facing * 3 * z, hy), (hx, hy + z)])
        for i in range(3):
            px, py = pts[2 + i * 2]
            s.set_at((R(px + jit(i + 9)), R(py - 2 * z)), WHITE)
    for px, py in pts[::2]:
        shine_at(o, px, py, 3 * z)
    eyes(s, hx + o.facing * 0.5 * z, hy, 1.4 * z, z, t, o.phase)


def draw_thrum(o, s, t):
    """Thrumlet: a little dark thundercloud with a grumpy face, rumbling. Thrumcloud: a bigger cloud
    with rain falling and a flicker inside. Thrumtempest: a great dark anvil of cloud, lightning in
    its belly, a skirt of rain under it."""
    z, x, y, n = begin(o)
    puffs = [(0, 0, 2.6), (-2.4, 0.8, 1.8), (2.4, 0.8, 1.9)] if n == 1 else (
        [(0, -1, 3.2), (-3.4, 0.6, 2.4), (3.4, 0.6, 2.6), (-1.5, 1.4, 2), (1.6, 1.4, 2)] if n == 2 else
        [(0, -3, 4), (-5, -2.4, 3), (5, -2.4, 3), (-3, 0.5, 3), (3, 0.5, 3), (-7, -3.5, 2), (7, -3.5, 2)])
    if n >= 2:  # rain
        for i in range(5 * n):
            rx = x + ((i * 37) % (8 * n) - 4 * n) * z * 0.5
            ry = y + (2 + ((t * 18 + i * 7) % (4 * n))) * z
            pygame.draw.line(s, (150, 160, 200), (rx, ry), (rx - 0.5 * z, ry + z))
    flick = (t * 3 + o.phase) % 2.5 < 0.15
    for px, py, r in puffs:
        circ(s, dark(o.body, 0.2), x + px * z, y + py * z + 1, r * z)
    for px, py, r in puffs:
        circ(s, mix(o.body, o.color, 0.25 if flick else 0.0), x + px * z, y + py * z, r * z)
    if n == 3 and flick:
        pygame.draw.lines(s, o.color, False, [(x - z, y + 2 * z), (x + z, y + 4 * z), (x - 0.5 * z, y + 5 * z), (x + 1.5 * z, y + 8 * z)], 2)
    pygame.draw.line(s, INK, (x - 1.8 * z, y - 1 * z), (x - 0.6 * z, y - 0.5 * z))  # the grumpy brows
    pygame.draw.line(s, INK, (x + 1.8 * z, y - 1 * z), (x + 0.6 * z, y - 0.5 * z))
    eyes(s, x + o.facing * 0.3 * z, y, 2.2 * z, z, t, o.phase)
    shine_at(o, x, y + z, (3 + 2 * n) * z * (1.4 if flick else 0.7))


# ===================================== Thornwood =====================================================

def draw_bane(o, s, t):
    """Banelet: a bunch of glowing poison berries on a black stem, bobbing along. Baneberry: two
    bunches and a ring of thorny leaves. Banebramble: a rolling ball of black brambles hung with
    berries, all of them watching."""
    z, x, y, n = begin(o)
    b = hop(o, t, 1.6) if n < 3 else 0
    berries = []
    if n < 3:
        pygame.draw.line(s, o.body, (x, y - b), (x, y - 6 * z - b), max(1, R(z)))
        for k in range(n):
            bx = x + (k - (n - 1) / 2) * 4 * z
            for j in range(5):
                a = j * TAU / 5
                berries.append((bx + math.cos(a) * 1.4 * z, y - 7.5 * z - b + math.sin(a) * 1.4 * z))
            if n == 2:
                pygame.draw.line(s, o.body, (x, y - 6 * z - b), (bx, y - 7.5 * z - b))
        if n == 2:
            for side in (-1, 1):
                poly(s, (50, 70, 60), [(x, y - 3 * z - b), (x + side * 5 * z, y - 5 * z - b), (x + side * 3 * z, y - 2 * z - b)])
    else:
        r = 6 * z
        cy = y - r
        turn = o.x * 0.12 * o.facing if moving(o) else 0
        for j in range(14):
            a = turn + j * 0.9
            pygame.draw.arc(s, o.body, (x - r * (0.4 + j % 3 * 0.25), cy - r * 0.8, r * (0.8 + j % 3 * 0.5), r * 1.6), a, a + 2.4, 2)
        for j in range(9):
            a = turn + j * TAU / 9
            berries.append((x + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75))
    for bx, by in berries:
        circ(s, o.color, bx, by, 1.1 * z)
        s.set_at((R(bx - 0.4 * z), R(by - 0.4 * z)), lite(o.color, 0.6))
    for bx, by in berries[:: max(1, len(berries) // 4)]:
        shine_at(o, bx, by, 2.5 * z)
    ex, ey = berries[0]
    eyes(s, ex, ey, 1.2 * z, z, t, o.phase)


def draw_shroud(o, s, t):
    """Shroudlet: a small shadow carried on eight threads of web, its eyes like dew. Shroudweb: it
    trails a fan of web behind it, the threads glowing violet. Shroudweaver: a big shadow-shape
    hung in a whole wheel of web, which it carries along wherever it goes."""
    z, x, y, n = begin(o)
    r = (2.4, 3.2, 4.4)[n - 1] * z
    cy = y - (4 + n) * z
    if n == 3:  # the wheel of web it carries
        for j in range(10):
            a = j * TAU / 10
            pygame.draw.line(s, mix(o.color, (40, 30, 60), 0.5), (x, cy), (x + math.cos(a) * 12 * z, cy + math.sin(a) * 9 * z))
        for k in range(1, 5):
            pts = [(x + math.cos(j * TAU / 10) * 3 * k * z, cy + math.sin(j * TAU / 10) * 2.2 * k * z) for j in range(11)]
            pygame.draw.lines(s, mix(o.color, (40, 30, 60), 0.4), False, pts)
        shine_at(o, x, cy, 10 * z)
    for j in range(4):  # eight thread legs
        for side in (-1, 1):
            k = math.sin(t * 14 + j * 1.3 + side) * z * 0.8 if moving(o) else 0
            kx = x + side * (2 + j * 1.2) * z
            fx = x + side * (3 + j * 1.6) * z + k
            pygame.draw.lines(s, lite(o.body, 0.3), False, [(x, cy), (kx, cy - (2 + n) * z), (fx, y)])
    if n == 2:
        for j in range(6):
            pygame.draw.line(s, o.color, (x, cy), (x - o.facing * 10 * z, cy - 5 * z + j * 2 * z))
        shine_at(o, x - o.facing * 6 * z, cy, 5 * z)
    pygame.draw.ellipse(s, o.body, (x - r, cy - r * 0.8, 2 * r, 1.6 * r))
    for side in (-1, 1):
        circ(s, lite(o.color, 0.3), x + side * r * 0.3, cy - r * 0.15, 0.6 * z)
    for side in (-1, 1):
        circ(s, lite(o.color, 0.2), x + side * r * 0.6, cy + r * 0.05, 0.4 * z)
    shine_at(o, x, cy, r)


import wave9  # noqa: E402,F401  (the other twenty)

for _kind, *_rest in LINES:
    _draw = globals().get("draw_" + _kind) or getattr(wave9, "draw_" + _kind)
    setattr(Flier if _kind in FLIERS else Walker, "draw_" + _kind, _draw)
    setattr(Flier if _kind in FLIERS else Walker, "glow_" + _kind, glow_lines8)
