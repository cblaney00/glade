"""Drawings for the 50 lines in lines8.py, part two: the twenty spread over every place by theme
(2026-10-27, his ask). Same helpers and rules as wave8.py, which imports this file and hooks
every drawing onto Walker/Flier.
"""

import math

import pygame

from wave5 import TAU, WHITE, dark, eyes, hop, lite, moving, poly  # noqa: F401
from wave8 import INK, R, ball, begin, circ, shine_at, wiggle


def draw_clove(o, s, t):
    """Clovelet: a four-leaf clover that cartwheels along on its leaves. Clovebrawl: bigger, its
    leaves curled tight like mitts. Clovechamp: a great clover with a golden fifth leaf, spinning so
    fast it hums."""
    z, x, y, n = begin(o)
    r = (2.4, 3.2, 4.2)[n - 1] * z
    cy = y - r * 1.4
    spin = (o.x * 0.25 * o.facing if moving(o) else 0) * (1 + 0.5 * (n == 3))
    leaves = 4 if n < 3 else 5
    for j in range(leaves):
        a = spin + j * TAU / leaves
        lx, ly = x + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8
        c = (255, 220, 110) if (n == 3 and j == 4) else o.body
        for side in (-0.35, 0.35):
            circ(s, c if side < 0 else lite(c, 0.12), lx + math.cos(a + side * 4) * r * 0.25, ly + math.sin(a + side * 4) * r * 0.25, r * (0.42 if n == 1 else 0.5))
        if n == 2:
            circ(s, dark(o.body, 0.25), lx, ly, r * 0.2)
    circ(s, lite(o.body, 0.3), x, cy, r * 0.35)
    eyes(s, x + o.facing * 0.3 * z, cy, 1.4 * z, z, t, o.phase)
    shine_at(o, x, cy, r)


def draw_glaze(o, s, t):
    """Glazelet: a pebble glazed in frozen spray, knuckled with ice, that charges head-first.
    Glazebash: a block of ice with a cracked, battered brow. Glazebreaker: a hulking floe of blue
    ice on stubby legs, a ram of icicles at its front."""
    z, x, y, n = begin(o)
    lean = wiggle(o, t, 0.8, 6) * z
    if n == 1:
        r = 3 * z
        ball(s, o.body, x + lean, y - r, r)
        for k in range(3):
            circ(s, (230, 245, 255), x + o.facing * r * 0.7 + lean, y - r * (1.4 - k * 0.4), 0.7 * z)
        ex, ey = x + o.facing * r * 0.2 + lean, y - r * 1.1
    else:
        w, h = (5, 8)[n - 2] * z, (6, 8)[n - 2] * z
        base = y - (2 * z if n == 3 else 0)
        if n == 3:
            for j in range(4):
                lx = x + (j - 1.5) * 3.5 * z
                pygame.draw.rect(s, dark(o.body, 0.3), (lx - z, base - z + wiggle(o, t, 0.5, 8) * (1 if j % 2 else -1), 2 * z, 3 * z))
        pts = [(x - w, base), (x + w, base), (x + w * 0.9 + lean, base - h), (x - w * 0.8 + lean, base - h * 1.1)]
        poly(s, o.body, pts)
        pygame.draw.line(s, (230, 245, 255), pts[3], pts[2], max(1, R(z * 0.6)))
        for k in range(2):  # cracks
            cx = x + (k - 0.5) * w * 0.8
            pygame.draw.lines(s, dark(o.body, 0.3), False, [(cx, base - h), (cx + z, base - h * 0.7), (cx - z * 0.5, base - h * 0.4)])
        if n == 3:
            for k in range(4):
                fy = base - h * (0.2 + k * 0.2)
                poly(s, (230, 245, 255), [(x + o.facing * w, fy - z), (x + o.facing * (w + 3 * z), fy), (x + o.facing * w, fy + z)])
        ex, ey = x + o.facing * w * 0.4 + lean, base - h * 0.75
    eyes(s, ex, ey, 1.8 * z, z, t, o.phase)
    shine_at(o, ex, ey, (3 + n) * z)


def draw_dart(o, s, t):
    """Dartlet: a needle of ember with four glassy wings, darting. Dartwing: longer, its wings
    edged in flame. Dartblaze: a streak of fire with six blazing wings and a smoking trail."""
    z, x, y, n = begin(o)
    ln = (6, 9, 12)[n - 1] * z
    for i in range(int(ln / z)):
        f = i / (ln / z)
        circ(s, dark(o.body, 0.4 * f) if i % 2 else o.body, x - o.facing * i * z, y + math.sin(f * 3 + t * 10) * 0.2 * z, (1.2 - 0.6 * f) * z)
    pairs = 2 if n < 3 else 3
    for j in range(pairs):
        wx = x - o.facing * (1 + j * 1.8) * z
        flap = abs(math.sin(t * 40 + j))
        for side in (-1, 1):
            rect = (wx - 2.5 * z, y + side * (0.5 + 2 * flap) * z - 1.2 * z, 5 * z, 2.4 * z)
            pygame.draw.ellipse(s, (240, 230, 240) if n == 1 else (255, 200, 140), rect)
            if n >= 2:
                pygame.draw.ellipse(s, o.color, rect, 1)
    if n == 3:
        for i in range(8):
            circ(s, (120, 100, 110), x - o.facing * (ln + i * 1.6 * z), y + math.sin(t * 6 + i) * z, (0.5 + i * 0.15) * z)
    eyes(s, x + o.facing * 0.4 * z, y - 0.3 * z, 1.2 * z, z, t, o.phase)
    shine_at(o, x, y, (2 + n) * z)


def draw_whisp(o, s, t):
    """Whisplet: a knot-hole of glowing wood that floats, two leaves for ears. Whispbark: a curl of
    bark around the knot, moss trailing from it. Whispelder: a hollow stump floating free, its face a
    ring of knot-holes, roots drifting like a beard."""
    z, x, y, n = begin(o)
    bark = o.body
    if n == 1:
        pygame.draw.ellipse(s, bark, (x - 3 * z, y - 2.5 * z, 6 * z, 5 * z))
        pygame.draw.ellipse(s, INK, (x - 1.6 * z, y - 1.2 * z, 3.2 * z, 2.6 * z))
        for side in (-1, 1):
            poly(s, (110, 190, 130), [(x + side * 2 * z, y - 2 * z), (x + side * 4.5 * z, y - 4.5 * z + math.sin(t * 3 + side) * z), (x + side * 1 * z, y - 2.5 * z)])
        eyes(s, x, y, 1.4 * z, z, t, o.phase)
        shine_at(o, x, y, 3 * z)
        return
    w, h = (4, 6)[n - 2] * z, (6, 9)[n - 2] * z
    pygame.draw.rect(s, dark(bark, 0.25), (x - w, y - h / 2, 2 * w, h), border_radius=R(w * 0.6))
    pygame.draw.rect(s, bark, (x - w, y - h / 2, w * 1.3, h), border_radius=R(w * 0.6))
    for k in range(-2, 3):
        pygame.draw.line(s, dark(bark, 0.35), (x + k * w * 0.4, y - h / 2 + z), (x + k * w * 0.4, y + h / 2 - z))
    holes = [(0, -0.1)] if n == 2 else [(-0.4, -0.2), (0.4, -0.2), (0, 0.2)]
    for hx, hy in holes:
        pygame.draw.ellipse(s, INK, (x + hx * w - 1.2 * z, y + hy * h - z, 2.4 * z, 2 * z))
        circ(s, o.color, x + hx * w, y + hy * h, 0.5 * z)
        shine_at(o, x + hx * w, y + hy * h, 2.5 * z)
    for k in range(4 + 2 * n):  # moss or roots trailing below
        rx = x - w + k * 2 * w / (3 + 2 * n)
        pygame.draw.line(s, (90, 150, 110) if n == 2 else dark(bark, 0.2), (rx, y + h / 2), (rx + math.sin(t * 2 + k) * z, y + h / 2 + (3 + n) * z))


def draw_flint(o, s, t):
    """Flintlet: a nodule of flint that knocks itself against things, striking sparks. Flintknock:
    two nodules, one held up to knock the other. Flintcolossus: a craggy heap of flint blocks that
    shuffles along, sparks jumping between its seams."""
    z, x, y, n = begin(o)
    knock = max(0, math.sin(t * 4 + o.phase))
    if n < 3:
        r = 3 * z
        poly(s, o.body, [(x - r, y), (x + r, y), (x + r * 0.8, y - r * 1.3), (x, y - r * 1.8), (x - r * 0.9, y - r * 1.1)])
        pygame.draw.line(s, lite(o.body, 0.3), (x - r * 0.9, y - r * 1.1), (x, y - r * 1.8))
        if n == 2:
            kx, ky = x + o.facing * 4 * z, y - (5 + knock * 2) * z
            poly(s, o.body, [(kx - 1.6 * z, ky + 1.6 * z), (kx + 1.6 * z, ky + 1.6 * z), (kx + z, ky - 1.6 * z), (kx - z, ky - 1.6 * z)])
            if knock < 0.15:
                for j in range(5):
                    a = j * TAU / 5
                    s.set_at((R(kx + math.cos(a) * 2.5 * z), R(ky + 2 * z + math.sin(a) * 2 * z)), o.color)
                shine_at(o, kx, ky + 2 * z, 5 * z)
        eyes(s, x + o.facing * 0.5 * z, y - 1.6 * r * 0.6, 1.8 * z, z, t, o.phase)
        shine_at(o, x, y - r, 2 * z)
        return
    blocks = [(-4, 0, 4, 5), (3, 0, 4.5, 6), (-1, -6, 4, 4.5), (4, -7, 3, 3.5)]
    for bx, by, w, h in blocks:
        cx, cy = x + bx * z, y + by * z
        poly(s, o.body, [(cx - w * z, cy), (cx + w * z, cy), (cx + w * 0.7 * z, cy - h * z), (cx - w * 0.8 * z, cy - h * 1.1 * z)])
        pygame.draw.line(s, lite(o.body, 0.25), (cx - w * 0.8 * z, cy - h * 1.1 * z), (cx + w * 0.7 * z, cy - h * z))
    for j in range(3):
        if (t * 5 + j * 1.7 + o.phase) % 3 < 0.4:
            sx, sy = x + (j - 1) * 3 * z, y - (4 + j * 2) * z
            pygame.draw.line(s, o.color, (sx, sy), (sx + z, sy - z))
            shine_at(o, sx, sy, 3 * z)
    eyes(s, x + o.facing * 0.5 * z, y - 9 * z, 2 * z, z, t, o.phase)
    shine_at(o, x, y - 9 * z, 2 * z)


def draw_slush(o, s, t):
    """Slushlet: a wet heap of slush with a snow cap, that slumps along. Slushmound: a bigger heap
    with icicle drips down its front. Slushavalanche: a rolling wave of snow and slush, boulders of
    ice tumbling in its front."""
    z, x, y, n = begin(o)
    w, h = (4, 6.5, 10)[n - 1] * z, (3.4, 5, 6.5)[n - 1] * z
    slump = wiggle(o, t, 0.15, 4)
    pts = [(x + (i / 14 - 0.5) * 2 * w, y - math.sin(i / 14 * math.pi) * h * (1 + slump * (i / 14 - 0.5))) for i in range(15)]
    poly(s, o.body, pts + [(x + w, y), (x - w, y)])
    cap = [(px, py) for px, py in pts[3:12]]
    pygame.draw.lines(s, (245, 250, 255), False, cap, max(2, R(z * 1.3)))
    if n >= 2:
        for k in range(3):
            ix = x + (k - 1) * w * 0.4
            poly(s, (220, 240, 255), [(ix - 0.6 * z, y - h * 0.4), (ix + 0.6 * z, y - h * 0.4), (ix, y - h * 0.4 + 2 * z)])
    if n == 3:
        for k in range(3):
            bx = x + o.facing * (w * 0.7 + k * 1.5 * z)
            ball(s, (200, 230, 250), bx, y - (1.5 + k % 2) * z, (1.2 + k * 0.3) * z)
    eyes(s, x + o.facing * w * 0.25, y - h * 0.55, 2 * z, z, t, o.phase)
    shine_at(o, x, y - h * 0.5, w * 0.6)


def draw_kiln(o, s, t):
    """Kilnlet: a little clay pot with a fire in it, an eye looking out of the flame. Kilnbake: a
    round kiln on three feet, its door glowing. Kilnoracle: a tall kiln-tower, smoke curling from its
    chimney into shapes, a great flame-eye in its open door."""
    z, x, y, n = begin(o)
    clay = o.body
    if n == 1:
        b = hop(o, t, 1.4)
        pygame.draw.polygon(s, dark(clay, 0.25), [(x - 3 * z, y - b), (x + 3 * z, y - b), (x + 2.2 * z, y - 5 * z - b), (x - 2.2 * z, y - 5 * z - b)])
        pygame.draw.polygon(s, clay, [(x - 3 * z, y - b), (x + 1 * z, y - b), (x + 0.6 * z, y - 5 * z - b), (x - 2.2 * z, y - 5 * z - b)])
        fy = y - 5 * z - b
        fl = 1 + 0.3 * math.sin(t * 10 + o.phase)
        poly(s, o.color, [(x - 1.8 * z, fy), (x + 1.8 * z, fy), (x, fy - 4 * z * fl)])
        circ(s, WHITE, x, fy - 1.2 * z, 0.8 * z)
        s.set_at((R(x), R(fy - 1.2 * z)), INK)
        shine_at(o, x, fy - z, 5 * z)
        return
    w, h = (4.5, 5)[n - 2] * z, (6, 12)[n - 2] * z
    base = y - 2 * z
    for k in (-1, 0, 1) if n == 2 else (-1, 1):
        pygame.draw.rect(s, dark(clay, 0.3), (x + k * w * 0.6 - 0.6 * z, base, 1.2 * z, 2 * z))
    if n == 2:
        pygame.draw.ellipse(s, dark(clay, 0.25), (x - w, base - h, 2 * w, h))
        pygame.draw.ellipse(s, clay, (x - w, base - h, w * 1.5, h))
    else:
        pygame.draw.rect(s, dark(clay, 0.25), (x - w, base - h, 2 * w, h), border_radius=R(z * 2))
        pygame.draw.rect(s, clay, (x - w, base - h, w * 1.4, h), border_radius=R(z * 2))
        pygame.draw.rect(s, dark(clay, 0.2), (x + w * 0.3, base - h - 3 * z, 1.6 * z, 3 * z))
        for i in range(5):  # smoke curling into a spiral
            a = t * 1.5 + i * 0.9
            circ(s, (170, 160, 170), x + w * 0.4 + math.cos(a) * i * 0.6 * z, base - h - 4 * z - i * 1.6 * z, (0.6 + i * 0.25) * z)
    dy = base - h * (0.45 if n == 2 else 0.35)
    pygame.draw.ellipse(s, INK, (x - 1.6 * z, dy - 1.6 * z, 3.2 * z, 3.2 * z))
    circ(s, o.color, x, dy, 1.3 * z)
    circ(s, WHITE, x, dy, 0.6 * z)
    s.set_at((R(x + 0.2 * z * (1 if o.facing > 0 else -1)), R(dy)), INK)
    shine_at(o, x, dy, 5 * z)


def draw_thump(o, s, t):
    """Thumplet: a stuffed sack, stitched up the middle, that bounces and bumps into things.
    Thumpbag: a long bag hung from its own little post, swinging. Thumpchampion: a great patched
    bag with a belt round its middle, bouncing on a coiled spring."""
    z, x, y, n = begin(o)
    if n == 1:
        b = hop(o, t, 2.4)
        w, h = 3 * z, 5 * z
        pygame.draw.ellipse(s, dark(o.body, 0.25), (x - w, y - h - b, 2 * w, h))
        pygame.draw.ellipse(s, o.body, (x - w, y - h - b, w * 1.5, h))
        top = y - h - b
    elif n == 2:
        sw = math.sin(t * 2.5 + o.phase) * 0.25
        pygame.draw.line(s, (110, 80, 70), (x - 3 * z, y), (x - 3 * z, y - 13 * z), max(1, R(z)))
        pygame.draw.line(s, (110, 80, 70), (x - 3 * z, y - 13 * z), (x + 2 * z, y - 13 * z), max(1, R(z)))
        cx = x + 2 * z + math.sin(sw) * 6 * z
        pygame.draw.line(s, (90, 80, 80), (x + 2 * z, y - 13 * z), (cx, y - 10 * z))
        pygame.draw.rect(s, dark(o.body, 0.2), (cx - 2.4 * z, y - 10 * z, 4.8 * z, 8 * z), border_radius=R(z * 2))
        pygame.draw.rect(s, o.body, (cx - 2.4 * z, y - 10 * z, 3.4 * z, 8 * z), border_radius=R(z * 2))
        x, top = cx, y - 10 * z
        h = 8 * z
    else:
        k = abs(math.sin(t * 4 + o.phase))
        sh = (2 + 2 * k) * z
        for i in range(5):
            pygame.draw.ellipse(s, (170, 170, 190), (x - 2 * z, y - i * sh / 5 - z, 4 * z, 1.4 * z), 1)
        w, h = 5 * z, 9 * z
        base = y - sh
        pygame.draw.rect(s, dark(o.body, 0.2), (x - w, base - h, 2 * w, h), border_radius=R(w))
        pygame.draw.rect(s, o.body, (x - w, base - h, w * 1.4, h), border_radius=R(w))
        pygame.draw.rect(s, (200, 60, 80), (x - w, base - h * 0.45, 2 * w, 1.6 * z))
        circ(s, (255, 220, 120), x, base - h * 0.45 + 0.8 * z, 1 * z)
        pygame.draw.rect(s, (120, 150, 200), (x - w * 0.8, base - h * 0.85, 2 * z, 2 * z))  # a patch
        top = base - h
        shine_at(o, x, base - h * 0.4, 4 * z)
    for k in range(4):  # stitches up its front
        sy = top + (1.2 + k * 1.1) * z
        pygame.draw.line(s, (240, 230, 210), (x - 0.5 * z, sy), (x + 0.5 * z, sy + 0.4 * z))
    eyes(s, x + o.facing * z, top + 1.6 * z, 1.8 * z, z, t, o.phase)
    shine_at(o, x, top + 2 * z, 2.5 * z)


def draw_ooz(o, s, t):
    """Oozite: a lump of cave rock with a seam of glowing green ooze dripping from it. Oozestone: the
    ooze has split it, and bubbles. Oozemonolith: a tall dark pillar running with ooze, a pool
    of it round its foot that it slides upon."""
    z, x, y, n = begin(o)
    w, h = (3.2, 4.6, 4.6)[n - 1] * z, (3.6, 6, 13)[n - 1] * z
    if n == 3:
        pygame.draw.ellipse(s, o.color, (x - 6 * z, y - 1.2 * z, 12 * z, 2.4 * z))
        shine_at(o, x, y, 6 * z)
    poly(s, o.body, [(x - w, y), (x + w, y), (x + w * 0.8, y - h), (x - w * 0.5, y - h - z)])
    pygame.draw.line(s, lite(o.body, 0.2), (x - w * 0.5, y - h - z), (x - w, y))
    seams = 1 if n == 1 else 2
    for k in range(seams):
        sx = x + (k - (seams - 1) / 2) * w * 0.7
        pygame.draw.line(s, o.color, (sx, y - h), (sx + z, y - h * 0.3), max(1, R(z * 0.8)))
        dl = ((t * 3 + k) % 1.0) * 3 * z
        circ(s, o.color, sx + z, y - h * 0.3 + dl, 0.6 * z)
        shine_at(o, sx, y - h * 0.6, 3 * z)
    if n >= 2:
        for k in range(3):
            by = y - h * 0.5 - ((t * 2 + k * 0.33) % 1.0) * 3 * z
            pygame.draw.circle(s, o.color, (R(x + (k - 1) * z), R(by)), max(1, R(0.5 * z)), 1)
    eyes(s, x + o.facing * w * 0.2, y - h * 0.75, 1.8 * z, z, t, o.phase)


def draw_dande(o, s, t):
    """Dandelet: a dandelion clock, round and soft, drifting, its seeds stirring. Dandeplume: a
    clock trailing a stream of seeds that it steers. Dandedream: a huge clock whose seeds float
    loose around it in a slow ring, each one faintly lit."""
    z, x, y, n = begin(o)
    r = (2.6, 3.2, 4.2)[n - 1] * z
    for j in range(16):
        a = j * TAU / 16 + math.sin(t + j) * 0.05
        ex, ey = x + math.cos(a) * r, y + math.sin(a) * r
        pygame.draw.line(s, (220, 220, 210), (x, y), (ex, ey))
        circ(s, o.body, ex, ey, 0.6 * z)
    circ(s, (200, 190, 150), x, y, 0.9 * z)
    loose = 0 if n == 1 else (6 if n == 2 else 12)
    for j in range(loose):
        if n == 2:
            f = (t * 0.3 + j / loose) % 1.0
            sx, sy = x - o.facing * (r + f * 14 * z), y + math.sin(f * 6 + j) * 2 * z
        else:
            a = t * 0.4 + j * TAU / loose
            sx, sy = x + math.cos(a) * r * 2.2, y + math.sin(a) * r * 1.4
        pygame.draw.line(s, (230, 230, 220), (sx, sy), (sx, sy + 1.4 * z))
        for k in (-1, 0, 1):
            s.set_at((R(sx + k * 0.8 * z), R(sy - 0.4 * z)), WHITE)
        if j % 3 == 0:
            shine_at(o, sx, sy, 2 * z)
    pygame.draw.line(s, (120, 170, 120), (x, y + r * 0.2), (x - o.facing * z, y + r * 1.8))
    eyes(s, x + o.facing * 0.4 * z, y - 0.2 * z, 1.4 * z, z, t, o.phase)
    shine_at(o, x, y, r)


def draw_cap(o, s, t):
    """Caplet: a spotted toadstool cap scuttling on six little legs. Capcluster: three caps joined at
    the stalk, scuttling as one. Capcolony: a whole clump of caps on a mossy log-shell, dozens of
    legs going at once, spores puffing up."""
    z, x, y, n = begin(o)
    caps = [(0, 0, 1.0)] if n == 1 else ([(-2.5, 0.5, 0.8), (0, -1, 1.0), (2.5, 0.5, 0.8)] if n == 2 else
                                          [(-5, 1, 0.8), (-2, -1.5, 1.0), (1.5, -2, 1.1), (4.5, 0, 0.9), (0, 1, 0.8)])
    base = y - 2 * z
    legs = (6, 8, 12)[n - 1]
    for j in range(legs):  # scuttling legs
        lx = x + (j - legs / 2 + 0.5) * 1.1 * z
        k = math.sin(t * 22 + j * 1.7) * 0.8 * z if moving(o) else 0
        pygame.draw.line(s, (90, 60, 80), (lx, base), (lx + k, y))
    if n == 3:
        pygame.draw.rect(s, (110, 90, 80), (x - 7 * z, base - 2 * z, 14 * z, 2.6 * z), border_radius=R(z))
        pygame.draw.rect(s, (90, 150, 110), (x - 7 * z, base - 2.4 * z, 14 * z, 1 * z))
    for cx, cy, k in caps:
        px, py = x + cx * z, base - (2 + cy) * z - (2 * z if n == 3 else 0)
        rr = 2.8 * z * k
        pygame.draw.rect(s, (230, 220, 210), (px - 0.6 * z, py, 1.2 * z, 2 * z))
        pygame.draw.ellipse(s, dark(o.body, 0.25), (px - rr, py - rr * 0.7 + 1, 2 * rr, rr))
        pygame.draw.ellipse(s, o.body, (px - rr, py - rr * 0.7, 2 * rr, rr))
        for d in (-0.5, 0.1, 0.5):
            circ(s, (255, 240, 240), px + d * rr, py - rr * 0.35 + abs(d) * z * 0.6, 0.45 * z)
        shine_at(o, px, py, rr)
    if n == 3:
        for i in range(4):
            f = (t * 0.5 + i / 4) % 1
            circ(s, (255, 200, 240), x + (i - 1.5) * 2 * z, base - 8 * z - f * 6 * z, 0.4 * z)
    eyes(s, x + o.facing * 0.5 * z, base - 1.2 * z, 1.6 * z, z, t, o.phase)


def draw_slough(o, s, t):
    """Sloughlet: a low bog dragon, flat and muddy, a fin of glowing weed down its back.
    Sloughcrawl: longer, dripping, its fin taller. Sloughmonarch: a broad, slow dragon wearing the
    bog itself, reeds growing from its back and a crown of luminous weed."""
    z, x, y, n = begin(o)
    length = (7, 11, 15)[n - 1] * z
    hgt = (2.4, 3.2, 5)[n - 1] * z
    for j in range(4):
        lx = x + (j - 1.5) * length / 4.5
        k = wiggle(o, t, 1, 5) * (1 if j % 2 else -1)
        pygame.draw.line(s, dark(o.body, 0.3), (lx, y - hgt * 0.3), (lx + k + (j - 1.5) * 0.4 * z, y), max(1, R(z)))
    pygame.draw.ellipse(s, dark(o.body, 0.25), (x - length / 2, y - hgt * 1.5 + 1, length, hgt * 1.4))
    pygame.draw.ellipse(s, o.body, (x - length / 2, y - hgt * 1.5, length, hgt * 1.2))
    tail = [(x - o.facing * (length / 2 + i * 1.4 * z), y - hgt * 0.6 + math.sin(t * 3 + i) * 0.5 * z) for i in range(5)]
    pygame.draw.lines(s, o.body, False, tail, max(1, R(z)))
    for i in range(5 + n * 2):  # the glowing fin of weed
        f = i / (5 + n * 2)
        fx = x + (f - 0.5) * length * 0.8
        fh = (1 + n) * z * math.sin(f * math.pi) + math.sin(t * 2 + i) * 0.3 * z
        pygame.draw.line(s, o.color, (fx, y - hgt * 1.4), (fx, y - hgt * 1.4 - fh))
        if i % 3 == 0:
            shine_at(o, fx, y - hgt * 1.4 - fh, 2.5 * z)
    if n == 3:
        for k in range(4):
            rx = x + (k - 1.5) * 2.6 * z
            pygame.draw.line(s, (120, 150, 90), (rx, y - hgt * 1.4), (rx + z, y - hgt * 1.4 - 5 * z))
    hx = x + o.facing * length / 2
    pygame.draw.ellipse(s, o.body, (hx - 2.6 * z + o.facing * z, y - hgt * 1.3, 5.2 * z, hgt))
    for i in range(3):
        circ(s, (120, 150, 110), hx + o.facing * (i - 1) * z, y - hgt * 0.3 + ((t * 2 + i * 0.3) % 1) * 2 * z, 0.4 * z)
    eyes(s, hx + o.facing * 1.4 * z, y - hgt * 1.0, 1.4 * z, z, t, o.phase)


def draw_gear(o, s, t):
    """Gearlet: an old bronze cog drifting and turning, one eye in its hub. Gearwork: two cogs that
    mesh as they float. Gearcolossus: a slow wheel of cogs within cogs, a ghost-light shining out
    through every gap."""
    z, x, y, n = begin(o)
    def cog(cx, cy, r, teeth, turn):
        for j in range(teeth):
            a = turn + j * TAU / teeth
            pygame.draw.line(s, dark(o.body, 0.2), (cx + math.cos(a) * r, cy + math.sin(a) * r),
                             (cx + math.cos(a) * (r + 1.2 * z), cy + math.sin(a) * (r + 1.2 * z)), max(1, R(z)))
        circ(s, o.body, cx, cy, r)
        circ(s, (40, 30, 50), cx, cy, r * 0.55)
        for j in range(4):
            a = turn + j * TAU / 4
            pygame.draw.line(s, o.body, (cx, cy), (cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6), max(1, R(z * 0.7)))
        shine_at(o, cx, cy, r * 0.6)
    turn = t * 0.8 + o.phase
    if n == 1:
        cog(x, y, 3 * z, 8, turn)
        circ(s, o.color, x, y, 0.9 * z)
    elif n == 2:
        cog(x - 2.4 * z, y, 3 * z, 8, turn)
        cog(x + 3.2 * z, y - 1 * z, 2.4 * z, 6, -turn * 1.3)
        circ(s, o.color, x - 2.4 * z, y, 0.9 * z)
    else:
        cog(x, y, 6 * z, 14, turn * 0.5)
        for j in range(3):
            a = -turn * 0.7 + j * TAU / 3
            cog(x + math.cos(a) * 3.2 * z, y + math.sin(a) * 3.2 * z, 1.8 * z, 6, turn * 2)
        circ(s, o.color, x, y, 1.2 * z)
    s.set_at((R(x - (2.4 * z if n == 2 else 0)), R(y)), (20, 20, 30))


def draw_lurk(o, s, t):
    """Lurklet: two eyes peering out of a hollow bit of driftwood, which shuffles along the sand.
    Lurklog: a whole hollow log, more eyes inside. Lurkhulk: a great tangle of driftwood and
    weed, a dark mouth of a hollow in its middle, lit eyes everywhere in it."""
    z, x, y, n = begin(o)
    w, h = (4, 7, 9)[n - 1] * z, (2.6, 3.4, 7)[n - 1] * z
    sh = wiggle(o, t, 0.4, 5) * z
    if n < 3:
        pygame.draw.rect(s, dark(o.body, 0.25), (x - w + sh, y - h * 2, 2 * w, h * 2), border_radius=R(h))
        pygame.draw.rect(s, o.body, (x - w + sh, y - h * 2, 2 * w, h * 1.3), border_radius=R(h))
        for k in range(3):
            pygame.draw.line(s, (200, 190, 180), (x - w * 0.6 + k * w * 0.5 + sh, y - h * 1.7), (x - w * 0.4 + k * w * 0.5 + sh, y - h * 1.6))
        mx = x + o.facing * (w - h * 0.6) + sh
        pygame.draw.ellipse(s, (20, 14, 24), (mx - h * 0.6, y - h * 1.6, h * 1.2, h * 1.2))
        pairs = [(mx, y - h)] if n == 1 else [(mx, y - h), (mx - o.facing * 3 * z, y - h * 1.1)]
    else:
        for k in range(6):
            a = k * 0.55
            pygame.draw.line(s, o.body if k % 2 else dark(o.body, 0.2), (x - w * math.cos(a), y - h * 0.5 - k * z), (x + w * math.cos(a * 0.7), y - h * 1.6 + k * 0.6 * z), max(2, R(1.6 * z)))
        pygame.draw.ellipse(s, (20, 14, 24), (x - 3 * z, y - h * 1.3, 6 * z, 5 * z))
        for k in range(5):
            pygame.draw.line(s, (90, 150, 110), (x - w * 0.8 + k * w * 0.4, y - h * 1.5), (x - w * 0.8 + k * w * 0.4 + math.sin(t + k) * z, y - h * 1.5 + 4 * z))
        pairs = [(x, y - h * 0.9), (x - 1.8 * z, y - h * 0.7), (x + 1.8 * z, y - h * 0.7)]
    for ex, ey in pairs:
        for side in (-0.5, 0.5):
            circ(s, o.color, ex + side * 1.2 * z, ey, 0.5 * z)
        shine_at(o, ex, ey, 2.5 * z)


def draw_mud(o, s, t):
    """Mudlet: a mud-pie with two pebble eyes and a twig stuck in it, plopping along. Mudmound: a
    heap of mud with twigs and a leaf roof. Mudcastle: a little mud tower with windows, built round
    itself, plodding on two stumps, glow-worms living in its windows."""
    z, x, y, n = begin(o)
    if n < 3:
        w, h = (3.6, 5.5)[n - 1] * z, (2.8, 4.5)[n - 1] * z
        b = hop(o, t, 1.2) * (n == 1)
        pygame.draw.ellipse(s, dark(o.body, 0.25), (x - w, y - h * 1.8 - b + 1, 2 * w, h * 1.8))
        pygame.draw.ellipse(s, o.body, (x - w, y - h * 1.8 - b, 2 * w, h * 1.6))
        for k in range(1 if n == 1 else 3):
            tx = x + (k - 1) * w * 0.5
            pygame.draw.line(s, (150, 120, 90), (tx, y - h * 1.5 - b), (tx + z, y - h * 2.4 - b))
        if n == 2:
            poly(s, (110, 170, 110), [(x - w * 0.7, y - h * 1.6), (x, y - h * 2.3), (x + w * 0.7, y - h * 1.6)])
        for side in (-1, 1):
            circ(s, (200, 190, 200), x + o.facing * w * 0.3 + side * 1 * z, y - h - b, 0.8 * z)
            s.set_at((R(x + o.facing * w * 0.3 + side * z), R(y - h - b)), (30, 20, 30))
        shine_at(o, x, y - h - b, 2 * z)
        return
    w, h = 4.5 * z, 12 * z
    base = y - 2 * z
    for side in (-1, 1):
        k = wiggle(o, t, 1, 6) * side
        pygame.draw.rect(s, dark(o.body, 0.3), (x + side * 2.5 * z - z, base + k * 0.2, 2 * z, 2 * z))
    pygame.draw.rect(s, dark(o.body, 0.2), (x - w, base - h, 2 * w, h))
    pygame.draw.rect(s, o.body, (x - w, base - h, w * 1.4, h))
    for k in range(-1, 2):
        pygame.draw.rect(s, o.body, (x + k * 3 * z - z, base - h - 2 * z, 2 * z, 2 * z))
    for wx, wy in ((-2, -9), (1.5, -6), (-1, -3.5)):
        pygame.draw.rect(s, (30, 20, 30), (x + wx * z, base + wy * z, 1.6 * z, 1.8 * z))
        circ(s, o.color, x + wx * z + 0.8 * z, base + wy * z + 0.9 * z, 0.4 * z)
        shine_at(o, x + wx * z + 0.8 * z, base + wy * z + z, 2 * z)
    eyes(s, x + o.facing * z, base - h + 2 * z, 2 * z, z, t, o.phase)


def draw_zest(o, s, t):
    """Zestlet: a little citrus fruit, its peel coming away in a spiral that sparks. Zestbolt: the
    peel is a crackling coil it springs along on. Zestdynamo: a fruit cut open, glowing segments
    spinning like a wheel, peel-coils arcing with current round it."""
    z, x, y, n = begin(o)
    r = (2.8, 3.4, 4.6)[n - 1] * z
    spring = (n == 2) * (2 + 1.5 * abs(math.sin(t * 6 + o.phase))) * z
    cy = y - r - spring - hop(o, t, 1.4) * (n == 1)
    if n == 2:
        pts = [(x + math.cos(i * 0.9) * r * 0.6, y - i * spring / 14) for i in range(15)]
        pygame.draw.lines(s, lite(o.body, 0.1), False, pts, max(1, R(z * 0.8)))
    if n < 3:
        ball(s, o.body, x, cy, r)
        pts = [(x + math.cos(a) * r * (1 + i * 0.03), cy + math.sin(a) * r * 0.4 - r * 0.3 + i * 0.15 * z)
               for i, a in enumerate([t * 2 + k * 0.5 for k in range(12)])]
        pygame.draw.lines(s, (255, 236, 150), False, pts)
    else:
        circ(s, (240, 240, 220), x, cy, r)
        for j in range(8):
            a = t * 2 + j * TAU / 8
            poly(s, o.body if j % 2 else (255, 200, 90), [(x, cy), (x + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9),
                                                       (x + math.cos(a + TAU / 8) * r * 0.9, cy + math.sin(a + TAU / 8) * r * 0.9)])
        for j in range(2):
            a0 = t * 3 + j * math.pi
            pts = [(x + math.cos(a0 + k * 0.3) * r * 1.5, cy + math.sin(a0 + k * 0.3) * r * 1.5 + math.sin(t * 30 + k) * 0.4 * z) for k in range(8)]
            pygame.draw.lines(s, o.color, False, pts)
    if (t * 4 + o.phase) % 2 < 0.3:
        s.set_at((R(x + r), R(cy - r)), WHITE)
    eyes(s, x + o.facing * r * 0.3, cy - r * 0.2, 1.6 * z, z, t, o.phase)
    shine_at(o, x, cy, r * 1.3)


def draw_wail(o, s, t):
    """Waillet: a hollow icicle that floats, the wind moaning through the holes along it. Wailfrost:
    two icicle pipes bound with frost, their song colder. Wailglacier: a whole organ of icicle pipes
    drifting in a mist of its own breath."""
    z, x, y, n = begin(o)
    pipes = [(0, 7)] if n == 1 else ([(-1.4, 7), (1.4, 9)] if n == 2 else [(-4, 7), (-2, 10), (0, 13), (2, 10), (4, 7)])
    for px, ln in pipes:
        cx = x + px * z
        top = y - ln * z * 0.5
        poly(s, o.body, [(cx - 1.1 * z, top), (cx + 1.1 * z, top), (cx, top + ln * z)])
        pygame.draw.line(s, (240, 250, 255), (cx - 0.6 * z, top), (cx - 0.2 * z, top + ln * z * 0.7))
        for k in range(2):
            circ(s, (60, 80, 120), cx, top + (1.5 + k * 2) * z, 0.4 * z)
    if n >= 2:
        pygame.draw.line(s, (230, 245, 255), (x - (n * 2) * z, y - 2 * z), (x + (n * 2) * z, y - 2 * z), max(1, R(z * 0.7)))
    for i in range(3 * n):  # its breath, drifting off
        f = (t * 0.4 + i / (3 * n)) % 1
        circ(s, (200, 220, 240), x - o.facing * f * 10 * z, y - (n * 3) * z * 0.5 - f * 2 * z, (0.3 + f) * z)
    pygame.draw.ellipse(s, (30, 30, 60), (x - 1 * z, y - 1.6 * z, 2 * z, 3 * z))  # its wailing mouth
    eyes(s, x, y - 3.4 * z, 1.6 * z, z, t, o.phase)
    shine_at(o, x, y - z, (3 + n) * z)


def draw_grit(o, s, t):
    """Gritlet: a crest of sand-coloured plates that swims through the dunes, only its back showing.
    Gritcrest: a longer row of plates with a horned head that comes up to look. Gritsovereign: a great
    sand dragon risen out of the ground, plated, horned, sand pouring off it."""
    z, x, y, n = begin(o)
    plates = (4, 7, 9)[n - 1]
    rise = (0, 2, 6)[n - 1] * z
    for i in range(plates):
        f = i / plates
        px = x - o.facing * (i - 1) * 2.4 * z
        py = y - rise * math.sin(f * math.pi + 0.3) - math.sin(t * 4 + i) * 0.3 * z
        h = (2.5 + n * 0.8) * z * (1 - f * 0.5)
        poly(s, o.body if i % 2 else dark(o.body, 0.15), [(px - 1.4 * z, py), (px + 1.4 * z, py), (px, py - h)])
    if n == 3:
        pygame.draw.ellipse(s, o.body, (x - 8 * z, y - rise - z, 16 * z, rise + z))
        for i in range(6):  # sand pouring off it
            circ(s, (230, 210, 180), x + (i - 2.5) * 2.5 * z, y - ((t * 4 + i * 0.4) % 1) * rise, 0.4 * z)
    pygame.draw.ellipse(s, (200, 170, 140), (x - plates * 1.4 * z, y - 1 * z, plates * 2.8 * z, 2 * z))  # disturbed sand
    if n >= 2:
        hx, hy = x + o.facing * 3.5 * z, y - rise - 2 * z
        pygame.draw.ellipse(s, o.body, (hx - 2.4 * z, hy - 1.6 * z, 4.8 * z, 3.2 * z))
        for k in (-1, 1):
            pygame.draw.line(s, (240, 230, 210), (hx - o.facing * z, hy - z), (hx - o.facing * 3 * z, hy - (2.5 + k * 0.6) * z), max(1, R(z * 0.6)))
        eyes(s, hx + o.facing * z, hy - 0.3 * z, 1.4 * z, z, t, o.phase)
        shine_at(o, hx, hy, 3 * z)
    else:
        eyes(s, x + o.facing * 3 * z, y - 0.8 * z, 1.4 * z, z, t, o.phase)
        shine_at(o, x, y - 2 * z, 3 * z)


def draw_astral(o, s, t):
    """Astralet: a few bright stars joined by faint lines, a little constellation that flies.
    Astralcoil: a longer one, curling like a dragon. Astralsovereign: a great dragon drawn in stars,
    its lines pulsing with current from star to star."""
    z, x, y, n = begin(o)
    k = (4, 8, 13)[n - 1]
    pts = []
    for i in range(k):
        a = t * 1.2 - i * 0.55 + o.phase
        pts.append((x - o.facing * i * 2.6 * z, y + math.sin(a) * (1 + i * 0.25) * z * (1 + n * 0.3)))
    pygame.draw.lines(s, (90, 100, 170), False, pts)
    if n == 3:
        f = int(t * 8) % k
        pygame.draw.line(s, o.color, pts[f], pts[min(k - 1, f + 1)], 2)
        for i in (3, 7):  # wings, drawn in stars too
            px, py = pts[i]
            for side in (-1, 1):
                wing = [(px, py), (px - o.facing * 2 * z, py + side * 4 * z), (px - o.facing * 5 * z, py + side * 5 * z)]
                pygame.draw.lines(s, (90, 100, 170), False, wing)
                for wx, wy in wing[1:]:
                    circ(s, WHITE, wx, wy, 0.5 * z)
    for i, (px, py) in enumerate(pts):
        r = (1.0 if i == 0 else 0.6) * z * (1 + 0.3 * math.sin(t * 3 + i))
        circ(s, WHITE if i else o.color, px, py, r)
        if i % 2 == 0:
            shine_at(o, px, py, 2.4 * z)
    hx, hy = pts[0]
    if n >= 2:
        pygame.draw.lines(s, (90, 100, 170), False, [(hx, hy), (hx + o.facing * 2 * z, hy - 2 * z), (hx + o.facing * 3.5 * z, hy)])
    eyes(s, hx + o.facing * 0.6 * z, hy - 1.2 * z, 1.2 * z, z, t, o.phase)


def draw_buoy(o, s, t):
    """Buoylet: a round bell-buoy bobbing on the sand as if on waves, its clapper swinging. Buoyjolt:
    taller, a spark crackling in its cage of a top. Buoybeacon: a big striped buoy with a lamp flashing
    on top and its bell clanging, rocking hard enough to knock things over."""
    z, x, y, n = begin(o)
    rock = math.sin(t * 2 + o.phase) * (0.12 + 0.06 * n)
    w, h = (3, 4, 5.5)[n - 1] * z, (4, 6, 9)[n - 1] * z
    def at(dx, dy):
        return (x + dx * math.cos(rock) - dy * math.sin(rock), y - 1 * z + dx * math.sin(rock) + dy * math.cos(rock))
    body = [at(-w, 0), at(w, 0), at(w * 0.8, -h * 0.6), at(-w * 0.8, -h * 0.6)]
    poly(s, o.body, body)
    stripe = [at(-w * 0.9, -h * 0.25), at(w * 0.9, -h * 0.25), at(w * 0.85, -h * 0.4), at(-w * 0.85, -h * 0.4)]
    poly(s, (240, 236, 230), stripe)
    for dx in (-0.6, 0, 0.6):  # its cage of a top
        pygame.draw.line(s, (90, 90, 110), at(dx * w, -h * 0.6), at(dx * w * 0.4, -h), max(1, R(z * 0.6)))
    top = at(0, -h)
    bell = at(0, -h * 0.78)
    circ(s, (230, 200, 120), *bell, 1.3 * z)
    clap = math.sin(t * 5 + o.phase) * 1.2 * z
    circ(s, (90, 80, 70), bell[0] + clap, bell[1] + 1.2 * z, 0.4 * z)
    if n >= 2:
        if (t * 4 + o.phase) % 2 < 0.4 or n == 3:
            circ(s, o.color, *top, (1 + 0.6 * (n == 3)) * z)
            shine_at(o, *top, (4 + 2 * n) * z)
    ex, ey = at(w * 0.3 * o.facing, -h * 0.45)
    eyes(s, ex, ey, 1.6 * z, z, t, o.phase)
    shine_at(o, *bell, 2.5 * z)
