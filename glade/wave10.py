"""Drawings for the twelve legendaries of legends2.py (2026-11-03, his ask). Same rules as the
other legendaries in wave5.py: never evolve (always drawn as they are), no humanoids, each its
own body. `draw_<kind>` paints the body and notes where its lights go; `glow_<kind>` lights them.
They live one to a place (wave5.LEGENDS), out only rarely (storm.rare).
"""

import math

import pygame

from art import glow
from beasts import FLIERS, LIT, WALKERS, Flier, Walker
from legends2 import LEGENDS2
from life import q
from wave5 import LEGENDS, TAU, WHITE, dark, eyes, lite, moving, poly

for _kind, _name, _home, *_r, _flies, _body, _glow, _speed, _lore in LEGENDS2:
    _spec = dict(species=_name, body=_body, color=_glow, speed=_speed)
    if _flies:
        FLIERS[_kind] = dict(_spec, turn=2.5)
    else:
        WALKERS[_kind] = _spec
    LIT.add(_kind)
    LEGENDS[_home] = _kind


def R(v):
    return round(v)


def circ(s, c, x, y, r):
    pygame.draw.circle(s, c, (R(x), R(y)), max(1, R(r)))


def bob(o, t, k=1.0):
    return math.sin(t * 1.1 + o.phase) * k * o.size


def lights(o, s, t, k, scale=1.0):
    for i, (x, y, r) in enumerate(getattr(o, "_lights", ())):
        glow(s, x, y, max(2, int(r * scale)), o.color, q(40 + 25 * math.sin(t * 1.7 + i + o.phase) + 60 * k))


def draw_veilf(o, s, t):
    """Veilfall: a veil of falling water that never reaches the ground, round a mossy stone heart."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    w, h = 9 * z, 16 * z
    for i in range(14):  # the veil: strands of water falling and fading
        sx = x - w + i * (2 * w / 13)
        top = y - h * 0.55 + math.sin(i * 1.7) * z
        for j in range(5):
            f = (t * 0.9 + j / 5 + i * 0.13) % 1
            yy = top + f * h
            c = lite(o.body, 0.25 + 0.4 * (1 - f))
            pygame.draw.line(s, c, (sx, yy), (sx, yy + 2 * z))
    pygame.draw.ellipse(s, lite(o.body, 0.5), (x - w * 1.05, y - h * 0.62, w * 2.1, 3 * z))  # where it pours from
    sr = 4.2 * z
    circ(s, dark((120, 116, 130), 0.2), x, y + 0.6 * z, sr)
    circ(s, (120, 116, 130), x, y, sr)
    for a in range(5):  # moss on the stone
        ang = a * 1.3 + 0.4
        circ(s, (110, 190, 120), x + math.cos(ang) * sr * 0.7, y - abs(math.sin(ang)) * sr * 0.7, 1.2 * z)
    eyes(s, x, y + 0.5 * z, 2.6 * z, z, t, o.phase)
    o._lights = [(x, y, sr * 1.6), (x, y - h * 0.55, w)]


def glow_veilf(o, s, t, st, k):
    lights(o, s, t, k)


def draw_rimeh(o, s, t):
    """Rimeheart: a great snowflake turning slowly, an aurora trailing off it."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    for i in range(18):  # the aurora ribbon behind it
        f = i / 17
        ax = x - o.facing * f * 22 * z
        ay = y - 6 * z + math.sin(t * 1.4 + f * 6 + o.phase) * 3 * z
        c = (int(140 + 80 * f), 255 - int(90 * f), int(200 + 40 * f))
        pygame.draw.line(s, c, (ax, ay), (ax, ay + (6 - 4 * f) * z))
    turn = t * 0.2 + o.phase
    arm = 10 * z
    for j in range(6):
        a = turn + j * TAU / 6
        ex, ey = x + math.cos(a) * arm, y + math.sin(a) * arm
        pygame.draw.line(s, o.body, (x, y), (ex, ey), max(1, R(1.3 * z)))
        for b in (0.45, 0.7):  # the branches on each arm
            bx, by = x + math.cos(a) * arm * b, y + math.sin(a) * arm * b
            for side in (-1, 1):
                aa = a + side * 0.7
                pygame.draw.line(s, lite(o.body, 0.3), (bx, by), (bx + math.cos(aa) * arm * 0.25, by + math.sin(aa) * arm * 0.25))
        circ(s, WHITE, ex, ey, 0.9 * z)
    poly(s, lite(o.body, 0.4), [(x + math.cos(turn + j * TAU / 6) * 3 * z, y + math.sin(turn + j * TAU / 6) * 3 * z) for j in range(6)])
    eyes(s, x, y, 2 * z, z, t, o.phase)
    o._lights = [(x, y, 8 * z)]


def glow_rimeh(o, s, t, st, k):
    lights(o, s, t, k)


def draw_calde(o, s, t):
    """Calderon: a little walking volcano, lava glowing through its cracks, smoke above."""
    z, x, y, f = o.size, o.x, o.y, o.facing
    step = math.sin(o.x * 0.3) * z if moving(o) else 0
    for side in (-1, 1):  # four stumpy rock feet
        for k in (0.35, 0.8):
            fx = x + side * k * 7 * z
            pygame.draw.ellipse(s, dark(o.body, 0.3), (fx - 1.6 * z, y - 1.6 * z + side * step * 0.5, 3.2 * z, 2.4 * z))
    base, top = 9 * z, 3 * z
    h = 11 * z
    cone = [(x - base, y - z), (x + base, y - z), (x + top, y - h), (x - top, y - h)]
    poly(s, o.body, cone)
    poly(s, lite(o.body, 0.12), [(x - base, y - z), (x - base * 0.2, y - z), (x - top * 0.4, y - h), (x - top, y - h)])
    o._lights = []
    for i, (cx, cy) in enumerate(((-0.4, 0.3), (0.3, 0.55), (0.05, 0.8))):  # lava cracks
        px, py = x + cx * base * 0.7, y - h * cy
        pts = [(px, py), (px + z, py + 2 * z), (px - 0.5 * z, py + 3.5 * z)]
        pygame.draw.lines(s, (255, 150, 70), False, pts, max(1, R(z * 0.8)))
        o._lights.append((px, py + 2 * z, 3 * z))
    pygame.draw.ellipse(s, (255, 170, 80), (x - top, y - h - z, 2 * top, 2 * z))  # the crater's lava
    for i in range(4):  # smoke
        sf = (t * 0.3 + i / 4) % 1
        circ(s, (110, 100, 120), x + math.sin(sf * 5 + i) * 2 * z, y - h - 2 * z - sf * 10 * z, (0.8 + sf * 2) * z)
    eyes(s, x + f * 2 * z, y - h * 0.55, 3 * z, z, t, o.phase)
    o._lights.append((x, y - h, 5 * z))


def glow_calde(o, s, t, st, k):
    lights(o, s, t, k)


def draw_prism(o, s, t):
    """Prismcore: a floating geode that opens and shuts, crackling crystals inside."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    r = 7 * z
    gap = (0.5 + 0.5 * math.sin(t * 0.6 + o.phase)) * 3 * z  # how far open it is
    o._lights = []
    for i in range(7):  # the crystals, seen between the halves
        a = math.pi * (0.15 + 0.7 * i / 6)
        cx, cy = x + math.cos(a) * r * 0.5 - r * 0.25, y
        c = [(200, 180, 255), (170, 230, 255), (255, 210, 250)][i % 3]
        poly(s, c, [(cx, cy - (2 + i % 3) * z), (cx + 1.2 * z, cy), (cx, cy + (2 + i % 2) * z), (cx - 1.2 * z, cy)])
    for side in (-1, 1):  # two rough rock halves
        hx = x + side * gap
        pts = [(hx, y - r)] + [(hx + side * math.sin(a / 8 * math.pi) * r * (1 + 0.08 * ((a * 7) % 3)),
                                 y - r + a / 8 * 2 * r) for a in range(9)] + [(hx, y + r)]
        poly(s, o.body if side < 0 else lite(o.body, 0.1), pts)
        pygame.draw.line(s, lite(o.color, 0.3), (hx, y - r), (hx, y + r), max(1, R(z * 0.7)))
    if gap > 1.5 * z:  # sparks jump between the crystals
        for i in range(3):
            sx = x + math.sin(t * 13 + i * 2) * gap * 0.8
            pygame.draw.line(s, (255, 255, 200), (sx, y - (i + 1) * 2 * z), (sx + z, y - i * 2 * z))
    eyes(s, x, y - r * 0.15, 2.4 * z, z, t, o.phase, shut=gap < z)
    o._lights.append((x, y, (4 + gap / z) * z))


def glow_prism(o, s, t, st, k):
    lights(o, s, t, k)


def draw_wispm(o, s, t):
    """Wispmire: a marsh-light lantern on tall stilts of tangled root, swinging as it walks."""
    z, x, y = o.size, o.x, o.y
    h = 15 * z
    step = math.sin(o.x * 0.25) * 2 * z if moving(o) else 0
    for j, side in enumerate((-1, -0.3, 0.4, 1)):  # the stilts of root
        foot = x + side * 5 * z + (step if j % 2 else -step)
        pts = [(foot, y)]
        for k in range(1, 5):
            pts.append((x + side * 5 * z * (1 - k / 4) + math.sin(k * 2 + j) * z, y - h * k / 4))
        pygame.draw.lines(s, lite(o.body, 0.45 - 0.08 * j), False, pts, max(1, R(z)))
    swing = math.sin(t * 1.5 + o.phase) * 0.3
    hx, hy = x, y - h
    lx, ly = hx + math.sin(swing) * 4 * z, hy + math.cos(swing) * 4 * z
    pygame.draw.line(s, dark(o.body, 0.2), (hx, hy), (lx, ly))
    pygame.draw.rect(s, (60, 54, 70), (lx - 3 * z, ly, 6 * z, 7 * z), border_radius=max(1, R(z)))
    pygame.draw.rect(s, lite(o.color, 0.2), (lx - 2 * z, ly + z, 4 * z, 5 * z))
    poly(s, (60, 54, 70), [(lx - 3.5 * z, ly), (lx + 3.5 * z, ly), (lx, ly - 2.5 * z)])
    for i in range(3):  # a drip of poison mist
        mf = (t * 0.5 + i / 3) % 1
        circ(s, (150, 210, 110), lx + (i - 1) * z, ly + 7 * z + mf * 6 * z, (1 - mf) * z)
    eyes(s, lx, ly + 3.5 * z, 1.8 * z, z, t, o.phase)
    o._lights = [(lx, ly + 3.5 * z, 7 * z)]


def glow_wispm(o, s, t, st, k):
    lights(o, s, t, k, 1.3)


def draw_runet(o, s, t):
    """Runetome: a stone book bound in bronze, its pages fanning, runes circling it."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    w, h = 6 * z, 8 * z
    open_ = 0.5 + 0.5 * math.sin(t * 0.5 + o.phase)
    for side in (-1, 1):  # the two covers, opening like wings
        tip = x + side * w * (0.6 + 0.6 * open_)
        poly(s, o.body, [(x, y - h * 0.5), (tip, y - h * 0.5 - open_ * 2 * z), (tip, y + h * 0.5 - open_ * 2 * z), (x, y + h * 0.5)])
        pygame.draw.line(s, (230, 190, 110), (tip, y - h * 0.5 - open_ * 2 * z), (tip, y + h * 0.5 - open_ * 2 * z), max(1, R(z)))
    for i in range(5):  # pages of stone, fanning
        f = (i + 1) / 6
        px = x + (f - 0.5) * 2 * w * 0.9 * open_
        pygame.draw.line(s, lite((180, 176, 190), 0.1 * i), (x, y + h * 0.5), (px, y - h * 0.45), max(1, R(z * 0.8)))
    pygame.draw.line(s, (230, 190, 110), (x, y - h * 0.5), (x, y + h * 0.5), max(1, R(z * 1.2)))  # the spine
    o._lights = []
    for j in range(6):  # runes circling it
        a = t * 0.5 + j * TAU / 6
        rx, ry = x + math.cos(a) * 12 * z, y + math.sin(a) * 4 * z
        pygame.draw.lines(s, o.color, False, [(rx - z, ry - z), (rx + z, ry - z), (rx - z, ry + z), (rx + z, ry + z)])
        o._lights.append((rx, ry, 2 * z))
    eyes(s, x, y - h * 0.1, 2 * z, z, t, o.phase)
    o._lights.append((x, y, 6 * z))


def glow_runet(o, s, t, st, k):
    lights(o, s, t, k)


def draw_cloom(o, s, t):
    """Cloudloom: a floating loom of pale wood, weaving long threads of cloud."""
    z, x, y, f = o.size, o.x, o.y + bob(o, t), o.facing
    w, h = 9 * z, 8 * z
    wood = (196, 170, 140)
    for side in (-1, 1):
        pygame.draw.line(s, wood, (x + side * w, y - h), (x + side * w, y + h * 0.4), max(1, R(1.3 * z)))
    pygame.draw.line(s, lite(wood, 0.2), (x - w - z, y - h), (x + w + z, y - h), max(1, R(1.3 * z)))
    pygame.draw.line(s, wood, (x - w, y + h * 0.4), (x + w, y + h * 0.4), max(1, R(1.3 * z)))
    for i in range(7):  # the warp threads
        tx = x - w + (i + 1) * w * 2 / 8
        pygame.draw.line(s, (230, 234, 250), (tx, y - h), (tx, y + h * 0.4))
    sh = math.sin(t * 2 + o.phase) * w * 0.8  # the shuttle, darting back and forth
    pygame.draw.ellipse(s, dark(wood, 0.2), (x + sh - 2 * z, y - 0.8 * z, 4 * z, 1.6 * z))
    for i in range(6):  # woven cloud streaming off behind it
        cf = (t * 0.4 + i / 6) % 1
        circ(s, lite(o.body, 0.1), x - f * (w + cf * 18 * z), y + h * 0.1 + math.sin(cf * 6 + i) * 2 * z, (2.5 - cf * 1.5) * z)
    poly(s, o.body, [(x - w * 0.8, y - h * 0.6), (x + w * 0.8, y - h * 0.6), (x + w * 0.8, y), (x - w * 0.8, y)])
    eyes(s, x, y - h * 0.3, 3 * z, z, t, o.phase)
    o._lights = [(x, y - h * 0.3, 7 * z)]


def glow_cloom(o, s, t, st, k):
    lights(o, s, t, k)


def draw_tides(o, s, t):
    """Tidespindle: a spinning whirl of tide water, full of glowing plankton, sparks in its eye."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    o._lights = []
    spin = t * 1.6 + o.phase
    for ring in range(5):  # the whirl, narrower towards the bottom
        ry = y - 8 * z + ring * 3.5 * z
        rw = (10 - ring * 1.6) * z
        pts = [(x + math.cos(spin + a / 16 * TAU + ring) * rw, ry + math.sin(spin + a / 16 * TAU + ring) * rw * 0.3) for a in range(17)]
        pygame.draw.lines(s, lite(o.body, 0.12 * ring), False, pts, max(1, R(1.2 * z)))
    for i in range(10):  # plankton riding round it
        a = spin * 1.3 + i * 0.63
        ring = i % 5
        px, py = x + math.cos(a) * (10 - ring * 1.6) * z, y - 8 * z + ring * 3.5 * z + math.sin(a) * z
        circ(s, o.color, px, py, 0.6 * z)
        o._lights.append((px, py, 1.6 * z))
    for i in range(2):  # sparks in its eye
        a = t * 9 + i * 3
        pygame.draw.line(s, (255, 255, 180), (x, y - 3 * z), (x + math.cos(a) * 3 * z, y - 3 * z + math.sin(a) * 2 * z))
    eyes(s, x, y - 5 * z, 2.4 * z, z, t, o.phase)
    o._lights.append((x, y - 3 * z, 6 * z))


def glow_tides(o, s, t, st, k):
    lights(o, s, t, k)


def draw_harve(o, s, t):
    """Harvestglow: a great hanging fruit-lantern, a fire inside, glowing seeds dropping."""
    z, x, y = o.size, o.x, o.y + bob(o, t, 0.6)
    swing = math.sin(t * 0.9 + o.phase) * 0.15
    pygame.draw.line(s, (90, 130, 80), (x, y - 16 * z), (x + math.sin(swing) * 5 * z, y - 7 * z), max(1, R(z)))  # its stalk
    for side in (-1, 1):  # two leaves
        poly(s, (110, 170, 90), [(x, y - 13 * z), (x + side * 5 * z, y - 15 * z), (x + side * 2 * z, y - 11 * z)])
    cx = x + math.sin(swing) * 5 * z
    r = 6.5 * z
    for i, dx in enumerate((-0.55, 0.55, 0)):  # the ribbed fruit
        pygame.draw.ellipse(s, o.body if i < 2 else lite(o.body, 0.1), (cx + dx * r - r * 0.6, y - 7 * z, r * 1.2, r * 1.8))
    for i in range(4):  # windows of light between the ribs
        wy = y - 5.5 * z + i * 2.2 * z
        pygame.draw.line(s, (255, 220, 130), (cx - r * 0.25, wy), (cx + r * 0.25, wy))
    o._lights = [(cx, y - 2 * z, 8 * z)]
    for i in range(3):  # seeds of light dropping
        sf = (t * 0.35 + i / 3) % 1
        sx, sy = cx + (i - 1) * 2 * z, y + 5 * z + sf * 12 * z
        circ(s, (255, 230, 150), sx, sy, (1 - sf * 0.5) * z)
        o._lights.append((sx, sy, 2 * z))
    eyes(s, cx, y - 2.5 * z, 2.4 * z, z, t, o.phase)


def glow_harve(o, s, t, st, k):
    lights(o, s, t, k)


def draw_hourd(o, s, t):
    """Hourdune: a giant hourglass of moon-sand, turning itself over now and then."""
    z, x, y = o.size, o.x, o.y + bob(o, t)
    cycle = (t * 0.08 + o.phase) % 1
    flip = max(0.0, (cycle - 0.9) / 0.1)  # the last tenth of each cycle it turns over
    a = flip * math.pi
    h, w = 10 * z, 6 * z
    fill = cycle / 0.9 if flip == 0 else 1.0

    def rot(px, py):
        return x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)

    frame = (150, 120, 90)
    for py in (-h, h):
        pygame.draw.line(s, frame, rot(-w - z, py), rot(w + z, py), max(1, R(1.5 * z)))
    for px in (-w - z, w + z):
        pygame.draw.line(s, dark(frame, 0.2), rot(px, -h), rot(px, h), max(1, R(z)))
    glass = (190, 200, 230)
    pygame.draw.lines(s, glass, True, [rot(-w, -h), rot(w, -h), rot(0.8 * z, 0), rot(w, h), rot(-w, h), rot(-0.8 * z, 0)])
    top = 1 - fill  # sand: draining from the top bulb into the bottom one
    if top > 0.02:
        poly(s, o.body, [rot(-w * top, -h * top), rot(w * top, -h * top), rot(0, 0)])
    if fill > 0.02:
        poly(s, o.body, [rot(-w, h), rot(w, h), rot(w * (1 - fill), h * (1 - fill)), rot(-w * (1 - fill), h * (1 - fill))])
    if flip == 0:
        pygame.draw.line(s, lite(o.body, 0.3), (x, y), (x, y + h * (1 - fill)))
    ex, ey = rot(0, -h * 0.55)
    eyes(s, ex, ey, 2.4 * z, z, t, o.phase)
    o._lights = [(x, y, 7 * z)]


def glow_hourd(o, s, t, st, k):
    lights(o, s, t, k)


def draw_anvil(o, s, t):
    """Anvilstorm: an iron anvil wrapped in a thundercloud; lightning strikes it and it rings."""
    z, x, y, f = o.size, o.x, o.y + bob(o, t), o.facing
    for i, (px, py, pr) in enumerate(((-6, -4, 4), (5, -5, 4.5), (0, -7, 5), (-9, -1, 3), (9, -1, 3))):
        circ(s, (70, 70, 96) if i % 2 else (84, 84, 110), x + px * z, y + py * z, pr * z)
    iron = (110, 116, 136)
    poly(s, iron, [(x - 8 * z, y - z), (x + 6 * z, y - z), (x + 9 * z * f if f > 0 else x + 6 * z, y + 0.5 * z),
                   (x + 3 * z, y + 2 * z), (x + 3 * z, y + 5 * z), (x - 4 * z, y + 5 * z), (x - 4 * z, y + 2 * z), (x - 8 * z, y + z)])
    pygame.draw.line(s, lite(iron, 0.4), (x - 8 * z, y - z), (x + 6 * z, y - z))
    pygame.draw.rect(s, dark(iron, 0.3), (x - 6 * z, y + 5 * z, 12 * z, 2 * z))
    o._lights = []
    strike = (t * 0.7 + o.phase) % 1
    if strike < 0.12:  # lightning strikes, and the anvil rings
        bx = x + math.sin(t * 31) * 3 * z
        pts = [(bx, y - 12 * z), (bx - 2 * z, y - 7 * z), (bx + z, y - 5 * z), (bx - z, y - z)]
        pygame.draw.lines(s, (255, 255, 200), False, pts, max(1, R(z)))
        for r in (8, 12):
            pygame.draw.circle(s, lite(o.color, 0.3), (R(x), R(y + 2 * z)), R(r * z * (0.5 + strike * 4)), 1)
        o._lights.append((x, y, 12 * z))
    eyes(s, x - f * z, y + 2 * z, 2.6 * z, z, t, o.phase)
    o._lights.append((x, y - 5 * z, 6 * z))


def glow_anvil(o, s, t, st, k):
    lights(o, s, t, k)


def draw_thornh(o, s, t):
    """Thornheart: a crown of black thorns, slowly turning, round one glowing red rose."""
    z, x, y = o.size, o.x, o.y + bob(o, t, 0.7)
    turn = t * 0.3 + o.phase
    r = 8 * z
    for ring in range(2):  # two twisted vines make the crown
        pts = [(x + math.cos(a / 24 * TAU + turn) * r, y + math.sin(a / 24 * TAU + turn) * r * 0.4 + math.sin(a / 24 * TAU * 4 + ring * 2) * z)
               for a in range(25)]
        pygame.draw.lines(s, lite(o.body, 0.1 * ring), False, pts, max(1, R(z * 1.2)))
    for j in range(9):  # thorns pointing up and out
        a = turn + j * TAU / 9
        bx, by = x + math.cos(a) * r, y + math.sin(a) * r * 0.4
        poly(s, o.body, [(bx - z * 0.8, by), (bx + z * 0.8, by), (bx + math.cos(a) * 2 * z, by - 4 * z)])
    rose = o.color
    for p in range(6):  # the rose, its petals
        pa = p * TAU / 6 + t * 0.2
        circ(s, dark(rose, 0.2) if p % 2 else rose, x + math.cos(pa) * 1.6 * z, y - 2 * z + math.sin(pa) * 1.2 * z, 1.8 * z)
    circ(s, lite(rose, 0.3), x, y - 2 * z, 1.2 * z)
    pygame.draw.line(s, (60, 110, 70), (x, y), (x, y + 4 * z))
    eyes(s, x, y - 2 * z, 1.6 * z, z, t, o.phase)
    o._lights = [(x, y - 2 * z, 6 * z)]


def glow_thornh(o, s, t, st, k):
    lights(o, s, t, k)


for _kind, *_r in LEGENDS2:
    _cls = Flier if _kind in FLIERS else Walker
    setattr(_cls, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(_cls, "glow_" + _kind, globals()["glow_" + _kind])
