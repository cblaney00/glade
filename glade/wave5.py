"""The Forest Dex's pages four to six (2026-10-27, his ask): 38 three-stage lines (#145-#258)
living in the ten older places, and the two legendaries, Elderglow (the Glade) and
Moonward (the Starfall Meadow), the last two numbers in the Dex,, which come out only rarely (storm.py).

Redrawn the same day, his rules: no humanoid creatures at all, and no two lines sharing a body,
so each kind here has its own `draw_<kind>` (all three stages, `stage(o)`) and `glow_<kind>`
(its lights). Most are not animals at all: a rolling bud, a candle stub, a folding paper screen,
a water-wheel, a stack of skipping stones, a gong on a stand, a pair of sparring halves...
`HOMES` says where each lives (scenes.second_wave and lower.py read it).
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, INK, LIT, WALKERS, Flier, Walker
from life import q

WHITE = (255, 255, 255)
TAU = math.tau

# kind: (first stage's species, flies?, body, glow, speed)
KINDS = {
    "petal": ("Petalpip", False, (240, 200, 226), (255, 170, 220), 12),
    "lulla": ("Lullabud", True, (170, 160, 240), (220, 190, 255), 10),
    "wick": ("Gleamwick", False, (240, 228, 206), (255, 176, 96), 8),
    "hush": ("Hushling", True, (230, 222, 206), (180, 170, 255), 12),
    "splash": ("Splashkin", False, (110, 180, 240), (170, 236, 255), 18),
    "mistm": ("Mistmote", True, (214, 232, 252), (170, 230, 255), 50),
    "slate": ("Slatelet", False, (112, 120, 152), (140, 220, 255), 10),
    "foam": ("Foamlet", True, (226, 240, 255), (190, 220, 255), 10),
    "reed": ("Reedlet", False, (176, 150, 100), (200, 255, 170), 9),
    "ripple": ("Ripplet", False, (120, 140, 170), (130, 220, 255), 12),
    "bubbl": ("Bubblo", True, (180, 226, 255), (255, 245, 140), 14),
    "silt": ("Siltpaw", False, (140, 116, 98), (150, 220, 255), 6),
    "bark": ("Barkling", False, (130, 96, 104), (170, 255, 170), 7),
    "fern": ("Fernflit", True, (110, 190, 130), (200, 255, 190), 46),
    "hollow": ("Hollowink", True, (196, 170, 120), (170, 255, 200), 12),
    "sap": ("Sapsip", False, (236, 160, 60), (255, 210, 120), 10),
    "rubble": ("Rubblet", False, (150, 140, 156), (255, 170, 120), 9),
    "quill": ("Quillnip", False, (126, 110, 150), (200, 140, 255), 4),
    "echo": ("Echolet", True, (210, 196, 226), (190, 170, 255), 24),
    "sigil": ("Sigilet", True, (150, 146, 186), (140, 255, 240), 10),
    "snowp": ("Snowpuff", False, (244, 248, 255), (170, 230, 255), 10),
    "shiver": ("Shiverling", False, (190, 220, 248), (160, 230, 255), 20),
    "glace": ("Glacelet", True, (214, 236, 255), (150, 240, 255), 70),
    "cone": ("Conelet", False, (150, 104, 84), (190, 240, 255), 9),
    "ash": ("Ashpaw", False, (78, 66, 74), (255, 150, 80), 12),
    "sulf": ("Sulfling", False, (210, 196, 110), (255, 220, 90), 4),
    "lava": ("Lavalet", True, (90, 60, 66), (255, 140, 70), 70),
    "obsid": ("Obsidling", False, (46, 36, 58), (255, 120, 70), 16),
    "gong": ("Gongling", False, (212, 172, 96), (255, 220, 140), 8),
    "spire": ("Spirelet", True, (196, 200, 224), (200, 180, 255), 16),
    "duel": ("Dueljab", True, (190, 120, 150), (255, 120, 150), 30),
    "myce": ("Mycelet", False, (200, 180, 220), (190, 140, 255), 4),
    "deep": ("Deepling", False, (24, 30, 60), (140, 255, 220), 6),
    "quartz": ("Quartzlet", False, (206, 200, 230), (220, 200, 255), 8),
    "gem": ("Gemmet", True, (150, 240, 220), (150, 255, 230), 40),
    "starb": ("Starbud", False, (120, 180, 130), (255, 240, 160), 5),
    "breeze": ("Breezlet", True, (232, 236, 250), (220, 240, 255), 60),
    "dew": ("Dewlet", True, (190, 244, 236), (170, 255, 220), 14),
    # the legendaries: Elderglow, a great wreath of living roots that drifts over the Glade with a
    # seed of light at its heart; Moonward, a crescent of night-glass with one watching eye in its
    # hollow and small moons, in every phase, wheeling about it
    "elder": ("Elderglow", True, (150, 116, 104), (255, 236, 170), 8),
    "moonw": ("Moonward", True, (60, 64, 130), (220, 220, 255), 14),
}
HOMES = {
    "glade": ("petal", "lulla", "wick", "hush"), "waterfall": ("splash", "mistm", "slate", "foam"),
    "river": ("reed", "ripple", "bubbl", "silt"), "forest": ("bark", "fern", "hollow", "sap"),
    "rocks": ("rubble", "quill", "echo", "sigil"), "ridge": ("snowp", "shiver", "glace", "cone"),
    "springs": ("ash", "sulf", "lava", "obsid"), "tower": ("gong", "spire", "duel"),
    "caverns": ("myce", "deep", "quartz", "gem"), "meadow": ("starb", "breeze", "dew"),
}
LEGENDS = {"glade": "elder", "meadow": "moonw"}

for _kind, (_sp, _flies, _body, _glow, _speed) in KINDS.items():
    spec = dict(species=_sp, body=_body, color=_glow, speed=_speed)
    if _flies:
        FLIERS[_kind] = dict(spec, turn=2.5)
    else:
        WALKERS[_kind] = spec
    LIT.add(_kind)


def stage(o):
    return 3 if o.kind in LEGENDS.values() else getattr(o, "stage", 1)


def dark(c, k=0.35):
    return mix(c, INK, k)


def lite(c, k=0.35):
    return mix(c, WHITE, k)


def shaded(s, color, rect):
    pygame.draw.ellipse(s, dark(color), pygame.Rect(rect).move(0, 1))
    pygame.draw.ellipse(s, color, rect)


def poly(s, color, pts, rim=None):
    pygame.draw.polygon(s, dark(color), [(x, y + 1) for x, y in pts])
    pygame.draw.polygon(s, color, pts)
    if rim:
        pygame.draw.lines(s, rim, True, pts)


def eyes(s, x, y, gap, z, t, phase, shut=False):
    blink = shut or (t * 0.9 + phase * 3) % 5 < 0.13
    for ex in (x - gap / 2, x + gap / 2):
        if blink:
            pygame.draw.line(s, INK, (round(ex - z * 0.6), round(y)), (round(ex + z * 0.6), round(y)))
        else:
            pygame.draw.rect(s, INK, (round(ex) - 1, round(y) - 1, 2, 2))
            s.set_at((round(ex), round(y) - 1), WHITE)


def moving(o):
    return getattr(o, "wait", 0) <= 0


def hop(o, t, h=3.0, speed=1.2):
    z = o.size
    if moving(o):
        return abs(math.sin(o.step * speed)) * h * z
    return abs(math.sin(t * 2 + o.phase)) * 0.5 * z


# ===================================== the Glade ==============================================

def draw_petal(o, s, t):
    """Petalpip: a closed flower bud that rolls along. Petalprim: half open, it tiptoes on the tips
    of its petals. Petalregal: a great open bloom striding on five petal-points, a crown of
    stamens glowing in its heart."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    if n == 1:
        roll = o.x * 0.25 * -o.facing
        shaded(s, o.body, (x - 5 * z, y - 10 * z, 10 * z, 10 * z))
        for j in range(4):  # the folded petals, turning as it rolls
            a = roll + j * TAU / 4
            pygame.draw.line(s, dark(o.body, 0.25), (x, y - 5 * z), (x + math.cos(a) * 5 * z, y - 5 * z + math.sin(a) * 5 * z))
        pygame.draw.ellipse(s, (120, 200, 140), (x - 3 * z, y - 2 * z, 6 * z, 2 * z))
        eyes(s, x, y - 5 * z, 3 * z, z, t, o.phase)
        o._heart = (x, y - 9 * z)
        return
    k = 5
    legs = (5 + 4 * n) * z
    cy = y - legs - hop(o, t, 1.2)
    for j in range(k):  # petals as legs, stepping in turn
        a = math.pi * (0.15 + 0.7 * j / (k - 1))
        lift = max(0.0, math.sin(o.step * 1.3 + j * 1.4)) * 2 * z if moving(o) else 0
        tip = (x + math.cos(a) * (6 + 2 * n) * z * (1 if j % 2 else 0.8), y - lift)
        poly(s, o.body if j % 2 else lite(o.body, 0.15), [(x - 2 * z + j * z * 0.8, cy), tip, (x - z + j * z * 0.8, cy + 2 * z)])
    for j in range(7 if n == 3 else 5):  # the bloom's upper petals
        a = -math.pi / 2 + (j - (3 if n == 3 else 2)) * 0.45
        r = (5 + 2 * n) * z
        poly(s, lite(o.body, 0.1 * (j % 2)), [(x, cy), (x + math.cos(a - 0.2) * r, cy + math.sin(a - 0.2) * r),
                                               (x + math.cos(a) * r * 1.15, cy + math.sin(a) * r * 1.15),
                                               (x + math.cos(a + 0.2) * r, cy + math.sin(a + 0.2) * r)])
    pygame.draw.circle(s, (255, 230, 150), (round(x), round(cy)), max(2, round((2 + n * 0.5) * z)))
    eyes(s, x, cy, 2.6 * z, z, t, o.phase)
    o._heart = (x, cy - (2 + n) * z)


def glow_petal(o, s, t, st, k):
    x, y = getattr(o, "_heart", (o.x, o.y))
    z, n = o.size, stage(o)
    glow(s, x, y, int((4 + 3 * n) * z), o.color, q(40 + 20 * n + 60 * k))
    if n == 3:
        for j in range(5):
            a = -math.pi / 2 + (j - 2) * 0.35
            sx, sy = x + math.cos(a) * 4 * z, y + math.sin(a) * 4 * z
            pygame.draw.line(s, (255, 236, 160), (x, y + 2 * z), (sx, sy))
            s.set_at((round(sx), round(sy)), WHITE)


def draw_lulla(o, s, t):
    """Lullabud: a drooping bell-flower that drifts, ringing softly. Lullabloom: three bells on an
    arching stem. Lullagrove: a drifting canopy of bells, vines trailing, notes floating off."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    bells = [(0, 0)] if n == 1 else [(-6, 2), (0, -1), (6, 2)] if n == 2 else [(-10, 4), (-5, 0), (0, -2), (5, 0), (10, 4)]
    if n > 1:
        pts = [(x + bx * z, y + by * z - 6 * z) for bx, by in bells]
        pygame.draw.lines(s, (110, 170, 120), False, pts, max(1, round(z)))
    if n == 3:
        for j in range(6):  # vines hanging
            vx = x + (j - 2.5) * 4 * z
            pygame.draw.lines(s, (90, 150, 110), False, [(vx + math.sin(t * 1.5 + j + i) * z, y - 4 * z + i * 4 * z) for i in range(5)])
        pygame.draw.ellipse(s, (90, 160, 120), (x - 13 * z, y - 12 * z, 26 * z, 8 * z))
    o._bells = []
    for i, (bx, by) in enumerate(bells):
        cx, cy = x + bx * z, y + by * z
        sway = math.sin(t * 2 + i + o.phase) * 0.15
        pygame.draw.line(s, (110, 170, 120), (cx, cy - 6 * z), (cx, cy - 3 * z))
        w, h = 4 * z, 5 * z
        pts = [(cx - w * 0.5, cy - 3 * z), (cx + w * 0.5, cy - 3 * z), (cx + w + sway * 6 * z, cy + h * 0.5),
               (cx + w * 0.4, cy + h * 0.3), (cx, cy + h * 0.6), (cx - w * 0.4, cy + h * 0.3), (cx - w + sway * 6 * z, cy + h * 0.5)]
        poly(s, o.body if i % 2 == 0 else lite(o.body, 0.2), pts)
        if i == len(bells) // 2:
            eyes(s, cx, cy - z, 2.4 * z, z, t, o.phase, shut=True)
        o._bells.append((cx, cy + h * 0.5))


def glow_lulla(o, s, t, st, k):
    z = o.size
    for i, (cx, cy) in enumerate(getattr(o, "_bells", [])):
        glow(s, cx, cy, int(4 * z), o.color, q(60 + 40 * math.sin(t * 2 + i) + 60 * k))
        s.set_at((round(cx), round(cy)), WHITE)
    for j in range(stage(o)):  # notes drifting off
        kk = (t * 0.25 + j / 3 + o.phase) % 1.0
        nx, ny = o.x + 8 * z + kk * 8 * z, o.y - 6 * z - kk * 12 * z
        c = mix(WHITE, (40, 30, 80), kk)
        pygame.draw.line(s, c, (nx + 1, ny - 3), (nx + 1, ny))
        pygame.draw.circle(s, c, (round(nx), round(ny)), 1)


def draw_wick(o, s, t):
    """Gleamwick: a stub of candle that hops about, its eyes in its flame. Gleamtorch: a tall
    candle that has melted into three wicks. Gleambeacon: a lantern-tower of old wax, ghost-
    flames wheeling round it and wax pooled at its foot."""
    z, x, y, n = o.size, o.x, o.y - hop(o, t, 2), stage(o)
    h = (6 + 5 * n) * z
    w = (4 + n) * z
    pygame.draw.ellipse(s, dark(o.body, 0.15), (x - w * 1.6, o.y - 2 * z, w * 3.2, 3 * z))  # its pool of wax
    rect = pygame.Rect(0, 0, round(2 * w), round(h))
    rect.midbottom = (round(x), round(y))
    pygame.draw.rect(s, dark(o.body, 0.25), rect.move(1, 0), border_radius=round(z * 1.5))
    pygame.draw.rect(s, o.body, rect, border_radius=round(z * 1.5))
    pygame.draw.line(s, lite(o.body, 0.4), (rect.x + z, rect.y + 2 * z), (rect.x + z, rect.bottom - 2 * z))
    for j in range(2 + n):  # drips down its sides
        dx = rect.x + (j + 0.5) * rect.w / (2 + n)
        ln = (2 + (j * 5 + n) % 4) * z
        pygame.draw.line(s, lite(o.body, 0.2), (dx, rect.y), (dx, rect.y + ln), max(1, round(z)))
    if n == 3:  # a lantern's windows
        for wy in (rect.y + h * 0.35, rect.y + h * 0.65):
            pygame.draw.rect(s, (60, 40, 50), (x - w * 0.5, wy, w, 2.5 * z))
    wicks = [x] if n == 1 else [x - w * 0.6, x, x + w * 0.6] if n == 2 else [x]
    o._flames = []
    for wx in wicks:
        pygame.draw.line(s, (60, 40, 50), (wx, rect.y), (wx, rect.y - 1.5 * z))
        o._flames.append((wx, rect.y - (3 + (n == 3)) * z))


def glow_wick(o, s, t, st, k):
    z, n = o.size, stage(o)
    for i, (fx, fy) in enumerate(getattr(o, "_flames", [])):
        fl = (3 + (n == 3) * 2 + abs(math.sin(t * 9 + i * 2)) * 1.2) * z
        poly(s, (255, 180, 90), [(fx - 1.6 * z, fy + 1.5 * z), (fx + 1.6 * z, fy + 1.5 * z), (fx + math.sin(t * 5 + i) * 0.6 * z, fy - fl)])
        pygame.draw.line(s, (255, 240, 180), (fx, fy + z), (fx, fy - fl * 0.4))
        glow(s, fx, fy, int((6 + 2 * n) * z), o.color, q(110 + 60 * k))
        if i == len(o._flames) // 2:
            eyes(s, fx, fy - 0.5 * z, 1.8 * z, z * 0.6, t, o.phase)
    if n == 3:
        cx, cy = o.x, o.y - 12 * z
        for j in range(3):  # ghost-flames wheeling round
            a = t * 0.9 + j * TAU / 3
            gx, gy = cx + math.cos(a) * 12 * z, cy + math.sin(a) * 4 * z
            glow(s, gx, gy, int(4 * z), (170, 200, 255), q(110))
            pygame.draw.circle(s, (210, 225, 255), (round(gx), round(gy)), max(1, round(1.2 * z)))


def draw_hush(o, s, t):
    """Hushling: a little folded paper fan that flutters, one eye painted on it. Hushveil: the fan
    open, layer on layer of paper. Hushwarden: a great folding screen of paper panels, a night
    landscape painted across them, eyes opening in the panels one by one."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    if n < 3:
        k = 5 if n == 1 else 9
        spread = (1.1 if n == 1 else 1.6) + 0.25 * math.sin(t * 3 + o.phase)
        r = (9 if n == 1 else 12) * z
        for j in range(k):
            a = -math.pi / 2 + (j - (k - 1) / 2) * spread / (k - 1)
            a2 = a + spread / (k - 1)
            c = o.body if j % 2 else dark(o.body, 0.12)
            pts = [(x, y + 2 * z), (x + math.cos(a) * r, y + 2 * z + math.sin(a) * r), (x + math.cos(a2) * r, y + 2 * z + math.sin(a2) * r)]
            pygame.draw.polygon(s, c, pts)
        pygame.draw.circle(s, (110, 80, 90), (round(x), round(y + 2 * z)), max(1, round(z)))
        if n == 2:
            for j in range(3):  # a painted moon and two hills
                pygame.draw.circle(s, (240, 220, 160), (round(x - 3 * z), round(y - 5 * z)), max(1, round(1.4 * z)))
        ey = y - r * 0.55
        eyes(s, x, ey, 0.01, z, t, o.phase)
        return
    panels = 4
    pw, ph = 6 * z, 16 * z
    fold = 0.7 + 0.2 * math.sin(t * 1.2 + o.phase)
    o._panels = []
    for j in range(panels):
        px = x + (j - panels / 2) * pw * fold
        skew = (2 * z if j % 2 else -2 * z)
        pts = [(px, y - ph / 2 + skew * 0.2), (px + pw * fold, y - ph / 2 - skew * 0.2),
               (px + pw * fold, y + ph / 2 - skew * 0.2), (px, y + ph / 2 + skew * 0.2)]
        poly(s, o.body if j % 2 else dark(o.body, 0.1), pts)
        pygame.draw.line(s, (60, 50, 80), (px + pw * fold * 0.5 - 2 * z, y + 3 * z), (px + pw * fold * 0.5 + 2 * z, y + 1 * z))
        o._panels.append((px + pw * fold * 0.5, y - 3 * z))
    pygame.draw.circle(s, (240, 220, 160), (round(x + 4 * z), round(y - 6 * z)), max(1, round(1.6 * z)))


def glow_hush(o, s, t, st, k):
    z = o.size
    if stage(o) == 3:
        for j, (px, py) in enumerate(getattr(o, "_panels", [])):
            if (t * 0.3 + j * 0.25 + o.phase) % 1.0 < 0.6:  # the eyes open in turn
                pygame.draw.ellipse(s, o.color, (px - 1.4 * z, py - 0.8 * z, 2.8 * z, 1.6 * z))
                s.set_at((round(px), round(py)), INK)
        glow(s, o.x, o.y, int(14 * z), o.color, q(40 + 60 * k))
    else:
        glow(s, o.x, o.y - 3 * z, int(7 * z), o.color, q(40 + 60 * k))


# ===================================== the Waterfall ==========================================

def draw_splash(o, s, t):
    """Splashkin: a little top of spinning water that skitters about. Splashtide: a whirling
    column with rings of water it lashes out. Cascadon: a roaring water-wheel that rolls and
    slams, buckets of spray flying from its rim."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    spin = t * 8
    if n < 3:
        h = (8 if n == 1 else 15) * z
        for i in range(int(h / z)):
            f = i / (h / z)
            r = (1 + 4 * math.sin(f * math.pi) + (n - 1) * 2 * f) * z
            cy = y - f * h
            c = mix(dark(o.body, 0.2), lite(o.body, 0.4), (math.sin(spin + i * 0.8) + 1) / 2)
            pygame.draw.ellipse(s, c, (x - r, cy - z, 2 * r, 2 * z))
        if n == 2:
            for j in range(2):  # rings flung out
                kk = (t * 0.8 + j * 0.5) % 1.0
                r = (5 + kk * 8) * z
                pygame.draw.ellipse(s, mix(lite(o.body), (30, 30, 80), kk), (x - r, y - h * 0.5 - r * 0.25, 2 * r, r * 0.5), 1)
        eyes(s, x, y - h * 0.6, 2.4 * z, z, t, o.phase)
        o._top = (x, y - h)
        return
    R = 11 * z
    cx, cy = x, y - R
    roll = -o.x / R * o.facing
    pygame.draw.circle(s, dark(o.body, 0.4), (round(cx), round(cy)), round(R), max(2, round(1.6 * z)))
    pygame.draw.circle(s, lite(o.body, 0.2), (round(cx), round(cy)), round(R - 1.6 * z), max(1, round(z)))
    for j in range(8):  # spokes of water and its buckets
        a = roll + j * TAU / 8
        bx, by = cx + math.cos(a) * R, cy + math.sin(a) * R
        pygame.draw.line(s, lite(o.body, 0.3), (cx, cy), (bx, by))
        pygame.draw.rect(s, o.body, (bx - 1.5 * z, by - 1.5 * z, 3 * z, 3 * z))
    pygame.draw.circle(s, o.body, (round(cx), round(cy)), max(2, round(4 * z)))
    eyes(s, cx, cy, 2.8 * z, z, t, o.phase)
    o._top = (cx, cy - R)


def glow_splash(o, s, t, st, k):
    z = o.size
    x, y = getattr(o, "_top", (o.x, o.y))
    for j in range(3 * stage(o)):  # spray
        kk = (t * 1.2 + j / (3 * stage(o)) + o.phase) % 1.0
        a = j * 2.4
        s.set_at((round(x + math.cos(a) * kk * 10 * z), round(y - kk * 6 * z + kk * kk * 8 * z)), mix(WHITE, (40, 50, 110), kk))
    glow(s, x, y + 4 * z, int((5 + 3 * stage(o)) * z), o.color, q(40 + 60 * k))


def draw_mistm(o, s, t):
    """Mistmote: a bead of spray on gossamer streamers, flying like a kite. Mistplume: a kite of
    mist, a cross of spray. Mistcrest: a great sail of mist, a crest of spray along its top,
    ribbons trailing far behind."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    for j in range(1 + n):  # streamers
        pts = [(px - f * (2 + j) * z, py + (j - n / 2) * 2 * z + math.sin(t * 4 + i + j) * z) for i, (px, py) in enumerate(o.trail)]
        pygame.draw.lines(s, mix(o.body, (60, 70, 130), 0.3), False, pts)
    if n == 1:
        shaded(s, o.body, (x - 3 * z, y - 3 * z, 6 * z, 6 * z))
        eyes(s, x, y - 0.5 * z, 2 * z, z, t, o.phase)
        return
    w, h = (6 if n == 2 else 10) * z, (9 if n == 2 else 14) * z
    kite = [(x + f * w * 0.3, y - h * 0.6), (x + f * w, y), (x + f * w * 0.3, y + h * 0.4), (x - f * w * 0.6, y)]
    pygame.draw.polygon(s, mix(o.body, (180, 200, 240), 0.2), kite)
    pygame.draw.lines(s, WHITE, True, kite)
    pygame.draw.line(s, lite(o.body, 0.5), kite[0], kite[2])
    pygame.draw.line(s, lite(o.body, 0.5), kite[1], kite[3])
    if n == 3:
        for j in range(5):  # a crest of spray along the top edge
            px = kite[3][0] + (kite[0][0] - kite[3][0]) * j / 4
            py = kite[3][1] + (kite[0][1] - kite[3][1]) * j / 4
            pygame.draw.line(s, WHITE, (px, py), (px - f * z, py - (2 + j % 2) * z))
    eyes(s, x + f * w * 0.25, y - z, 2 * z, z, t, o.phase)


def glow_mistm(o, s, t, st, k):
    glow(s, o.x, o.y, int((5 + 3 * stage(o)) * o.size), o.color, q(40 + 60 * k))


def draw_slate(o, s, t):
    """Slatelet: one flat skipping-stone that skips along. Slatebound: a stack of three, sliding
    over each other as it goes. Slatecliff: a leaning tower of slabs, a thread of waterfall
    pouring off its top."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    skip = abs(math.sin(o.step * 0.8)) * 4 * z if moving(o) and n == 1 else 0
    k = (1, 3, 6)[n - 1]
    by = y - skip
    o._top = (x, by)
    for j in range(k):
        w = (8 - j * 0.6 + (n - 1)) * z
        lean = math.sin(t * 1.4 + j * 0.8 + o.phase) * (0.6 if n < 3 else 1.0) * z + (j * 0.7 * z if n == 3 else 0)
        rect = (x - w + lean, by - 4 * z, 2 * w, 4 * z)
        pygame.draw.ellipse(s, dark(o.body, 0.3), pygame.Rect(rect).move(0, 1))
        pygame.draw.ellipse(s, lite(o.body, 0.06 * (j % 3)), rect)
        pygame.draw.line(s, lite(o.body, 0.3), (x - w * 0.6 + lean, by - 2.6 * z), (x + w * 0.3 + lean, by - 2.6 * z))
        by -= 2.6 * z
        o._top = (x + lean, by)
    tx, ty = o._top
    eyes(s, tx, ty + 1.2 * z + (2.6 * z if k > 1 else 0) - 2.6 * z * (k > 1), 3 * z, z, t, o.phase)
    if n == 3:  # a thread of water off the top, down its side
        for i in range(int((y - ty) / z)):
            wy = ty + i * z
            s.set_at((round(tx + 6 * z + math.sin(t * 6 + i) * 0.4), round(wy)), lite(o.color, 0.3) if (i + int(t * 10)) % 3 else WHITE)


def glow_slate(o, s, t, st, k):
    z = o.size
    tx, ty = getattr(o, "_top", (o.x, o.y))
    if stage(o) > 1:
        glow(s, tx, ty, int(6 * z), o.color, q(50 + 60 * k))
    if stage(o) == 3:
        glow(s, tx + 6 * z, o.y, int(8 * z), o.color, q(70))


def draw_foam(o, s, t):
    """Foamlet: three soap-light bubbles stuck together, one with an eye. Foamcurl: a curl of
    foam, rainbow sheen sliding over it. Foamcrest: a great dome of froth, an eye in every
    third bubble."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    count = (3, 8, 16)[n - 1]
    o._eyes = []
    for j in range(count):
        a = j * 2.4 + (0 if n < 3 else t * 0.1)
        d = (0 if j == 0 else (1.5 + math.sqrt(j) * 2.2)) * z
        r = (3.6 - min(2.0, j * 0.15)) * z * (1.2 if n == 3 else 1)
        bx, by = x + math.cos(a) * d * (1.2 if n > 1 else 1), y + math.sin(a) * d * 0.7 + math.sin(t * 2 + j) * 0.4 * z
        pygame.draw.circle(s, mix(o.body, (150, 180, 230), 0.25), (round(bx), round(by)), max(1, round(r)))
        pygame.draw.circle(s, WHITE, (round(bx), round(by)), max(1, round(r)), 1)
        sheen = (t * 0.5 + j * 0.2) % 1.0
        c = ((255, 180, 220), (180, 255, 220), (180, 200, 255))[j % 3]
        s.set_at((round(bx - r * 0.4), round(by - r * 0.4)), c if sheen < 0.6 else WHITE)
        if j == 0 or (n == 3 and j % 3 == 0):
            o._eyes.append((bx, by))
    for ex, ey in o._eyes:
        pygame.draw.circle(s, INK, (round(ex), round(ey)), max(1, round(0.9 * z)))


def glow_foam(o, s, t, st, k):
    glow(s, o.x, o.y, int((6 + 3 * stage(o)) * o.size), o.color, q(30 + 60 * k))


# ===================================== the River ==============================================

def draw_reed(o, s, t):
    """Reedlet: a bundle of reeds tied at the waist, bobbing along on its root-tips, a cattail for
    a head. Reedrunner: a long reed raft that skims along. Reedmarsh: a floating island of reeds,
    cattails nodding, a little pool glinting in its middle."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    bob = math.sin(t * 2 + o.phase) * 0.6 * z
    if n == 1:
        for j in range(6):
            rx = x + (j - 2.5) * 0.9 * z
            top = y - (12 + (j % 3) * 2) * z + bob
            sway = math.sin(t * 1.6 + j) * 0.8 * z
            pygame.draw.line(s, o.body if j % 2 else lite(o.body, 0.15), (rx, y), (rx + sway, top))
        pygame.draw.line(s, (120, 90, 70), (x - 3 * z, y - 6 * z + bob), (x + 3 * z, y - 6 * z + bob), max(1, round(z)))
        pygame.draw.ellipse(s, (110, 76, 60), (x - 1.4 * z, y - 18 * z + bob, 2.8 * z, 5 * z))
        eyes(s, x, y - 9 * z + bob, 2.4 * z, z, t, o.phase)
        o._tips = [(x, y - 18 * z + bob)]
        return
    L = (16 if n == 2 else 26) * z
    deck = y - 3 * z + bob
    for j in range(int(L / z / 1.4)):  # the raft's reeds, side by side
        rx = x - L / 2 + j * 1.4 * z
        pygame.draw.line(s, o.body if j % 2 else dark(o.body, 0.15), (rx, deck), (rx + f * z, deck + 3 * z))
    pygame.draw.line(s, lite(o.body, 0.3), (x - L / 2, deck), (x + L / 2, deck))
    o._tips = []
    for j in range(3 if n == 2 else 7):
        cx = x - L * 0.4 + j * L * 0.8 / max(1, (2 if n == 2 else 6))
        h = (8 + (j * 5) % 7) * z
        sway = math.sin(t * 1.5 + j) * z
        pygame.draw.line(s, (110, 170, 110), (cx, deck), (cx + sway, deck - h))
        pygame.draw.ellipse(s, (110, 76, 60), (cx + sway - 1.2 * z, deck - h - 3 * z, 2.4 * z, 4 * z))
        o._tips.append((cx + sway, deck - h - 4 * z))
    if n == 3:
        pygame.draw.ellipse(s, (90, 150, 210), (x - 4 * z, deck - 2 * z, 8 * z, 2.5 * z))
    eyes(s, x + f * L * 0.35, deck - 1.5 * z, 2.4 * z, z, t, o.phase)


def glow_reed(o, s, t, st, k):
    z = o.size
    for i, (tx, ty) in enumerate(getattr(o, "_tips", [])):
        b = 0.5 + 0.5 * math.sin(t * 1.3 + i * 1.7)
        glow(s, tx, ty, int(3 * z), o.color, q(60 * b + 40 * k))
        s.set_at((round(tx), round(ty)), lite(o.color, 0.4))


def draw_ripple(o, s, t):
    """Ripplet: a short ribbon of river that ripples along the ground. Rippleback: longer, humped,
    river stones riding on its humps. Ripplelord: a long rolling wave of river and mud, its crest
    breaking white, a crown of pebbles on its head."""
    z, f, n = o.size, o.facing, stage(o)
    segs = (6, 10, 14)[n - 1]
    x0, y0 = o.x, o.y
    pts = []
    for i in range(segs):
        px = x0 - f * i * 2.4 * z
        amp = (1.5 + n) * z
        py = y0 - 3 * z - abs(math.sin(t * 3 - i * 0.6 + o.phase)) * amp
        pts.append((px, py))
    for i, (px, py) in reversed(list(enumerate(pts))):
        r = max(1, (3 + n * 0.5 - i * 0.12) * z)
        pygame.draw.circle(s, dark(o.body, 0.3), (round(px), round(py + 1)), round(r))
        pygame.draw.circle(s, mix(o.body, (110, 170, 230), 0.4 * ((i + int(t * 6)) % 2)), (round(px), round(py)), round(r))
        if i % 2 == 0:
            pygame.draw.arc(s, lite(o.body, 0.5), (px - r, py - r, 2 * r, 2 * r), 0.6, 2.5)
    if n > 1:
        for i in range(2, segs - 2, 3):  # stones riding on its humps
            px, py = pts[i]
            pygame.draw.ellipse(s, (150, 140, 156), (px - 1.6 * z, py - (3.5 + n * 0.5) * z, 3.2 * z, 2 * z))
    if n == 3:
        hx, hy = pts[0]
        for j in range(5):
            pygame.draw.line(s, WHITE, (hx + f * j * 0.6 * z, hy - 3 * z), (hx + f * (j * 0.6 + 1) * z, hy - (5 + j % 2) * z))
    hx, hy = pts[0]
    eyes(s, hx + f * z, hy - z, 2.4 * z, z, t, o.phase)
    o._pts = pts


def glow_ripple(o, s, t, st, k):
    z = o.size
    for i, (px, py) in enumerate(getattr(o, "_pts", [])[::3]):
        b = 0.5 + 0.5 * math.sin(t * 2 - i)
        glow(s, px, py, int(3 * z), o.color, q(40 * b + 40 * k))


def draw_bubbl(o, s, t):
    """Bubblo: a bubble with a spark caught inside it, bouncing through the air. Bubblosh: a chain
    of bubbles linked by arcs. Bubblorb: a great bubble with a little storm-cloud inside it,
    smaller bubbles wheeling round."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    if n == 2:
        o._links = [(x + (j - 1) * 6 * z, y + math.sin(t * 2 + j) * 2 * z) for j in range(3)]
    else:
        o._links = [(x, y)]
    R = (4, 3.4, 9)[n - 1] * z
    for bx, by in o._links:
        pygame.draw.circle(s, mix(o.body, (40, 60, 120), 0.4), (round(bx), round(by)), round(R))
        pygame.draw.circle(s, WHITE, (round(bx), round(by)), round(R), 1)
        pygame.draw.arc(s, WHITE, (bx - R * 0.7, by - R * 0.7, R * 1.4, R * 1.4), 1.8, 2.8)
    if n == 3:
        for j in range(5):  # a storm-cloud in it
            cx = x + (j - 2) * 2.2 * z
            pygame.draw.circle(s, (180, 186, 220), (round(cx), round(y - 2 * z + (j % 2) * z)), max(1, round(2.4 * z)))
        for j in range(3):
            a = t * 1.2 + j * TAU / 3
            bx, by = x + math.cos(a) * 14 * z, y + math.sin(a) * 5 * z
            pygame.draw.circle(s, WHITE, (round(bx), round(by)), max(1, round(1.8 * z)), 1)
    eyes(s, x, y + (2 * z if n == 3 else 0), 2.4 * z, z, t, o.phase)


def glow_bubbl(o, s, t, st, k):
    z, n = o.size, stage(o)
    links = getattr(o, "_links", [(o.x, o.y)])
    for bx, by in links:
        if math.sin(t * 7 + bx) > 0.2 or k > 0:
            sx, sy = bx + math.sin(t * 13) * z, by - z
            pygame.draw.line(s, o.color, (sx - z, sy - z), (sx + z, sy + z))
            glow(s, bx, by, int(4 * z), o.color, q(110))
    for (ax, ay), (bx, by) in zip(links, links[1:]):
        mx = (ax + bx) / 2
        pygame.draw.lines(s, o.color, False, [(ax, ay), (mx, ay - 2 * z + math.sin(t * 20) * z), (bx, by)])
    if n == 3 and (math.sin(t * 3 + o.phase) > 0.5 or k > 0):
        pygame.draw.lines(s, o.color, False, [(o.x, o.y), (o.x - z, o.y + 3 * z), (o.x + z, o.y + 4 * z), (o.x, o.y + 7 * z)])
        glow(s, o.x, o.y, int(12 * z), o.color, q(100))


def draw_silt(o, s, t):
    """Siltpaw: a slow flowing wedge of river mud that pads along on little toes of mud, leaving
    pawprints. Siltstride: a long low mudflow, pebbles carried along in it. Siltgrand: a great
    delta of mud spreading as it goes, streams of water running down channels in its back."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    L, H = (10 + 6 * n) * z, (5 + 1.5 * n) * z
    flow = math.sin(t * 1.2 + o.phase) * z
    body = [(x + f * L * 0.5, y), (x + f * L * 0.3, y - H * 0.8), (x - f * L * 0.1, y - H + flow), (x - f * L * 0.5, y - H * 0.4),
            (x - f * L * 0.6, y)]
    poly(s, o.body, body)
    pygame.draw.line(s, lite(o.body, 0.25), body[1], body[2])
    for j in range(3):  # toes of mud at its front edge
        tx = x + f * (L * 0.5 - j * 2 * z)
        pygame.draw.circle(s, dark(o.body, 0.15), (round(tx), round(y - z)), max(1, round(1.4 * z)))
    if n > 1:
        for j in range(2 + n):  # pebbles carried in it
            px = x - f * L * 0.4 + f * j * L * 0.8 / (2 + n)
            pygame.draw.circle(s, (170, 160, 176), (round(px), round(y - H * 0.4 - (j % 2) * z)), max(1, round(1.2 * z)))
    if n == 3:
        for j in range(3):  # channels of water down its back
            cx = x - f * L * (0.3 - j * 0.15)
            pygame.draw.line(s, (120, 190, 240), (cx, y - H * 0.85), (cx - f * 3 * z, y - z))
    eyes(s, x + f * L * 0.18, y - H * 0.6, 2.4 * z, z, t, o.phase)


def glow_silt(o, s, t, st, k):
    if stage(o) == 3 or k > 0:
        glow(s, o.x, o.y - 6 * o.size, int(8 * o.size), o.color, q(40 + 60 * k))


# ===================================== the Forest =============================================

def draw_bark(o, s, t):
    """Barkling: a stubby log on four root-feet, a knot for an eye. Barkbrute: a broad stump with a
    great knotty burl on its brow for butting. Barkmonarch: a huge walking stump, roots for legs,
    a crown of young branches in leaf."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    for i, lx in enumerate((-5, -2, 2, 5)):
        lift = max(0.0, math.sin(o.step + i * 1.6)) * 1.5 * z if moving(o) else 0
        pygame.draw.lines(s, dark(o.body, 0.2), False, [(x + lx * z, y - 4 * z), (x + lx * 1.4 * z, y - 1.5 * z - lift), (x + lx * 1.6 * z, y - lift)],
                          max(1, round(z * 1.2)))
    w, h = (12 + 3 * n) * z, (6 + 3 * n) * z
    rect = pygame.Rect(0, 0, round(w), round(h))
    rect.midbottom = (round(x), round(y - 3 * z))
    pygame.draw.rect(s, dark(o.body, 0.3), rect.move(0, 1), border_radius=round(z * 2))
    pygame.draw.rect(s, o.body, rect, border_radius=round(z * 2))
    for j in range(int(w / z / 2.5)):  # bark ridges
        bx = rect.x + (j + 0.5) * 2.5 * z
        pygame.draw.line(s, dark(o.body, 0.2), (bx, rect.y + z), (bx + z * 0.5, rect.bottom - z))
    pygame.draw.ellipse(s, lite(o.body, 0.35), (rect.x + z, rect.y - z, rect.w - 2 * z, 2.4 * z))  # cut top, rings
    pygame.draw.ellipse(s, dark(o.body, 0.1), (rect.centerx - w * 0.2, rect.y - 0.6 * z, w * 0.4, 1.2 * z), 1)
    fx = rect.right - 2 * z if f > 0 else rect.x + 2 * z
    pygame.draw.circle(s, dark(o.body, 0.5), (round(fx), round(rect.centery)), max(1, round(1.8 * z)))  # the knot-eye
    s.set_at((round(fx), round(rect.centery - z)), (230, 220, 180))
    if n >= 2:  # the burl
        pygame.draw.circle(s, dark(o.body, 0.15), (round(fx + f * 2 * z), round(rect.y + 2 * z)), max(2, round((2 + n) * z)))
    if n == 3:
        for j in (-1, 0, 1):
            bx = rect.centerx + j * 4 * z
            pygame.draw.line(s, dark(o.body, 0.2), (bx, rect.y), (bx + j * 2 * z, rect.y - 6 * z), max(1, round(z)))
            pygame.draw.circle(s, (110, 200, 130), (round(bx + j * 2 * z), round(rect.y - 7 * z)), max(2, round(2.6 * z)))
    o._top = (rect.centerx, rect.y)


def glow_bark(o, s, t, st, k):
    if stage(o) == 3:
        tx, ty = o._top
        glow(s, tx, ty - 7 * o.size, int(10 * o.size), o.color, q(50 + 60 * k))


def draw_fern(o, s, t):
    """Fernflit: a curled fiddlehead that flies by unrolling and rolling up again. Fernglide: a
    half-open frond gliding on its leaflets. Fernsong: three great fronds fanned out, seeds
    ringing like bells along their spines."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    unroll = 0.5 + 0.5 * math.sin(t * 5 + o.phase)
    fronds = 1 if n < 3 else 3
    o._seeds = []
    for k in range(fronds):
        base_a = math.pi + (k - (fronds - 1) / 2) * 0.6
        ln = (8 + 4 * n) * z
        curl = (1 - unroll * (0.4 + 0.3 * n)) * 5
        px, py, a = x, y, base_a if f > 0 else -base_a + math.pi
        pts = [(px, py)]
        for i in range(12):
            a += curl * 0.12 * f
            seg = ln / 12
            px, py = px + math.cos(a) * seg, py + math.sin(a) * seg
            pts.append((px, py))
        pygame.draw.lines(s, dark(o.body, 0.2), False, pts, max(1, round(z)))
        for i, (px, py) in enumerate(pts[1:-1]):
            if i % 2 == 0:
                l = (1.5 + 0.2 * n) * z * (1 - i / 14)
                pygame.draw.line(s, o.body, (px, py), (px + l, py - l))
                pygame.draw.line(s, o.body, (px, py), (px - l, py - l))
            if n == 3 and i % 4 == 1:
                o._seeds.append((px, py + z))
    eyes(s, x + f * 1.2 * z, y - z, 2 * z, z, t, o.phase)


def glow_fern(o, s, t, st, k):
    z = o.size
    for i, (sx, sy) in enumerate(getattr(o, "_seeds", [])):
        b = 0.5 + 0.5 * math.sin(t * 3 + i)
        glow(s, sx, sy, int(3 * z), o.color, q(70 * b))
        s.set_at((round(sx), round(sy)), WHITE)
    glow(s, o.x, o.y, int(5 * z), o.color, q(30 + 60 * k))


def draw_hollow(o, s, t):
    """Hollowink: a hollow seed-husk, black as ink inside, two eyes peering out of the dark.
    Hollowmask: the husk split into a pale face-shell, drifting with vines through its holes.
    Hollowking: a great hollow knot of old wood afloat, dead branches for a crown, the dark inside
    full of watching eyes."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    R = (5, 7, 11)[n - 1] * z
    shell = o.body if n < 3 else (120, 90, 90)
    pygame.draw.ellipse(s, dark(shell, 0.3), (x - R, y - R * 1.2 + 1, 2 * R, 2.4 * R))
    pygame.draw.ellipse(s, shell, (x - R, y - R * 1.2, 2 * R, 2.4 * R))
    for j in range(-2, 3):  # husk ribs
        pygame.draw.arc(s, dark(shell, 0.2), (x - R * (0.3 + abs(j) * 0.2), y - R * 1.2, R * (0.6 + abs(j) * 0.4), 2.4 * R), -1.4, 1.4)
    hole = pygame.Rect(0, 0, round(R * 1.1), round(R * 1.2))
    hole.center = (round(x), round(y))
    pygame.draw.ellipse(s, (10, 6, 18), hole)
    if n >= 2:
        for side in (-1, 1):  # vines through its holes
            vx = x + side * R * 0.9
            pygame.draw.lines(s, (90, 160, 110), False, [(vx, y + i * 3 * z) for i in range(4)] if False else
                              [(vx + math.sin(t * 2 + i) * z, y - R * 0.2 + i * 3 * z) for i in range(4 + n)])
    if n == 3:
        for j in range(5):
            a = -math.pi / 2 + (j - 2) * 0.35
            bx, by = x + math.cos(a) * R * 1.1, y + math.sin(a) * R * 1.3
            pygame.draw.line(s, (90, 70, 70), (bx, by), (bx + math.cos(a) * 5 * z, by + math.sin(a) * 6 * z), max(1, round(z)))
    o._hole = hole


def glow_hollow(o, s, t, st, k):
    z, n = o.size, stage(o)
    hole = getattr(o, "_hole", None)
    if hole is None:
        return
    pairs = [(0, 0)] if n < 3 else [(0, 0), (-2.5, 2), (2.5, -1.5), (-1, -3)]
    for i, (dx, dy) in enumerate(pairs):
        if (t * 0.6 + i * 0.37 + o.phase) % 4 < 0.15:
            continue
        cx, cy = hole.centerx + dx * z, hole.centery + dy * z
        for side in (-1, 1):
            s.set_at((round(cx + side * 1.2 * z), round(cy)), o.color)
    glow(s, hole.centerx, hole.centery, int(6 * z), o.color, q(30 + 20 * n + 60 * k))


def draw_sap(o, s, t):
    """Sapsip: a bead of amber sap that walks on six little twig legs, something dark caught
    inside. Sapsurge: its amber cracked open, two leaves for wing-cases. Sapsentinel: a big cut
    block of amber like a lantern, leaf-shields on either side, the glow inside it beating."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    for i in range(3):
        for side in (-1, 1):
            lx = x + (i - 1) * 3 * z
            w = math.sin(o.step * 1.5 + i * 2 + side) * 1.2 * z if moving(o) else 0
            pygame.draw.lines(s, (100, 70, 60), False, [(lx, y - 3 * z), (lx + side * 2 * z + w, y - 2 * z), (lx + side * 2.5 * z + w, y)])
    R = (4, 5.5, 7)[n - 1] * z
    cy = y - 3 * z - R
    if n < 3:
        pygame.draw.circle(s, dark(o.body, 0.3), (round(x), round(cy + 1)), round(R))
        pygame.draw.circle(s, o.body, (round(x), round(cy)), round(R))
    else:
        pts = [(x + math.cos(a / 6 * TAU) * R, cy + math.sin(a / 6 * TAU) * R) for a in range(6)]
        poly(s, o.body, pts, rim=lite(o.body, 0.4))
    pygame.draw.circle(s, lite(o.body, 0.5), (round(x - R * 0.4), round(cy - R * 0.4)), max(1, round(R * 0.25)))
    pygame.draw.circle(s, (70, 40, 30), (round(x + R * 0.1), round(cy + R * 0.15)), max(1, round(R * 0.25)))  # caught inside
    if n >= 2:
        for side in (-1, 1):
            lx = x + side * R * 0.9
            pygame.draw.ellipse(s, (110, 190, 120), (lx - 2 * z, cy - R * 0.8, 4 * z, R * 1.6))
            pygame.draw.line(s, (80, 150, 90), (lx, cy - R * 0.7), (lx, cy + R * 0.7))
    if n == 2:
        pygame.draw.lines(s, dark(o.body, 0.4), False, [(x - R * 0.3, cy - R), (x, cy - R * 0.4), (x + R * 0.2, cy)])
    eyes(s, x + f * R * 0.45, cy - R * 0.2, 2 * z, z, t, o.phase)
    o._core = (x, cy)


def glow_sap(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, y = getattr(o, "_core", (o.x, o.y))
    b = 0.6 + 0.4 * math.sin(t * (1.5 if n < 3 else 3) + o.phase)
    glow(s, x, y, int((5 + 3 * n) * z), o.color, q(40 + 40 * b + 60 * k))


# ===================================== the Mossy Rocks ========================================

def draw_rubble(o, s, t):
    """Rubblet: a loose heap of pebbles that tumbles along, falling apart and gathering again.
    Rubbleback: a heap of stones, a mossy ridge along its top. Rubblequake: a landslide on the
    move, boulders grinding, crystals jutting out, the ground shaking under it."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    count = (7, 12, 18)[n - 1]
    shake = math.sin(t * 30) * 0.5 * z if n == 3 and moving(o) else 0
    for j in range(count):
        a = j * 2.4
        d = math.sqrt(j) * (2.2 + n * 0.4) * z
        tumble = math.sin(o.step * 0.7 + j) * z if moving(o) else 0
        px = x + math.cos(a) * d * 1.4 + shake
        py = y - (2.5 + n) * z - abs(math.sin(a)) * d * 0.6 - (count - j) * 0.15 * z + tumble * 0.3
        r = (2.4 + (j % 3) * 0.6 + (n - 1) * 0.6) * z
        pygame.draw.circle(s, dark(o.body, 0.3), (round(px), round(py + 1)), round(r))
        pygame.draw.circle(s, lite(o.body, 0.08 * (j % 3)), (round(px), round(py)), round(r))
    top = y - (8 + 3 * n) * z
    if n >= 2:
        pygame.draw.ellipse(s, (100, 190, 140), (x - 5 * z, top - z, 10 * z, 2.5 * z))
    if n == 3:
        for j in (-1, 1):
            cx = x + j * 5 * z
            poly(s, (255, 190, 150), [(cx - 1.5 * z, top + 3 * z), (cx + 1.5 * z, top + 3 * z), (cx + j * z, top - 4 * z)])
    eyes(s, x + f * 3 * z, top + 4 * z, 2.4 * z, z, t, o.phase)
    o._top = (x, top)


def glow_rubble(o, s, t, st, k):
    if stage(o) == 3:
        tx, ty = o._top
        for j in (-1, 1):
            glow(s, tx + j * 5 * o.size, ty, int(5 * o.size), o.color, q(70 + 60 * k))


def draw_quill(o, s, t):
    """Quillnip: a nub of violet rock bristling with poison quills, shuffling along. Quillback: a
    tall barbed column, an arm of rock branching off it. Quillfortress: a great spined spire of
    rock, branching, its quills dripping."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    h = (6, 13, 20)[n - 1] * z
    w = (4.5, 4, 5)[n - 1] * z
    rect = pygame.Rect(0, 0, round(2 * w), round(h))
    rect.midbottom = (round(x), round(y))
    pygame.draw.rect(s, dark(o.body, 0.3), rect.move(1, 0), border_radius=round(w))
    pygame.draw.rect(s, o.body, rect, border_radius=round(w))
    branches = [] if n == 1 else [(f, 0.55)] if n == 2 else [(f, 0.45), (-f, 0.7)]
    arms = []
    for side, at in branches:
        by = rect.bottom - h * at
        bx = x + side * w
        ex, ey = bx + side * 4 * z, by
        pygame.draw.line(s, o.body, (bx, by), (ex, ey), max(2, round(2.6 * z)))
        pygame.draw.line(s, o.body, (ex, ey), (ex, ey - 4 * z), max(2, round(2.6 * z)))
        arms.append((ex, ey - 4 * z))
    o._quills = []
    for j in range(int(h / z / 2)):  # quills all over
        qy = rect.bottom - (j + 0.5) * 2 * z
        for side in (-1, 1):
            qx = x + side * w
            ln = (2 + n * 0.6) * z
            pygame.draw.line(s, (236, 226, 246), (qx, qy), (qx + side * ln, qy - ln * 0.6))
            if j % 3 == 1:
                o._quills.append((qx + side * ln, qy - ln * 0.6))
    for ax, ay in arms:
        pygame.draw.line(s, (236, 226, 246), (ax, ay), (ax, ay - 2 * z))
    eyes(s, x, rect.y + min(h * 0.35, 4 * z), 2.4 * z, z, t, o.phase)


def glow_quill(o, s, t, st, k):
    z = o.size
    for i, (qx, qy) in enumerate(getattr(o, "_quills", [])):
        kk = (t * 0.4 + i * 0.3) % 1.0
        if stage(o) >= 2:
            s.set_at((round(qx), round(qy + kk * 4 * z)), o.color)  # a drop of poison
        glow(s, qx, qy, int(2 * z), o.color, q(40 + 60 * k))


def draw_echo(o, s, t):
    """Echolet: a little floating horn, like the bell of a trumpet, that calls and listens.
    Echowing: two horns joined back to back, turning. Echodome: a dome with horn-mouths all
    round it, rings of sound going out of every one."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    horns = [(f,)] if n == 1 else [(1,), (-1,)] if n == 2 else [(math.cos(a / 5 * TAU + t * 0.3),) for a in range(5)]
    o._mouths = []
    if n == 3:
        shaded(s, o.body, (x - 7 * z, y - 7 * z, 14 * z, 11 * z))
    for (d,) in horns:
        L = (8 if n < 3 else 8) * z
        mouth = (x + d * L, y - (0 if n < 3 else 3 * z))
        r = (3 + n * 0.5) * z
        pts = [(x, y - z), (mouth[0], mouth[1] - r), (mouth[0], mouth[1] + r), (x, y + z)]
        poly(s, lite(o.body, 0.1) if d > 0 else o.body, pts)
        pygame.draw.ellipse(s, dark(o.body, 0.5), (mouth[0] - r * 0.4, mouth[1] - r, r * 0.8, 2 * r))
        o._mouths.append((mouth, d))
    eyes(s, x, y - 2 * z, 2.4 * z, z, t, o.phase)


def glow_echo(o, s, t, st, k):
    z = o.size
    for i, ((mx, my), d) in enumerate(getattr(o, "_mouths", [])):
        for j in range(2):
            kk = (t * 0.7 + j * 0.5 + i * 0.2) % 1.0
            r = round((3 + kk * 8) * z)
            pygame.draw.arc(s, mix(o.color, (30, 20, 60), kk), (mx - r + d * kk * 6 * z, my - r, 2 * r, 2 * r),
                            -0.8 if d > 0 else math.pi - 0.8, 0.8 if d > 0 else math.pi + 0.8)
    glow(s, o.x, o.y, int((4 + 3 * stage(o)) * z), o.color, q(30 + 60 * k))


def draw_sigil(o, s, t):
    """Sigilet: a small stone cube that floats and slowly turns, a sigil cut in every face.
    Sigilward: the cube half unfolded, its faces hinged out like shutters. Sigilcolossus: three
    cubes nested one inside the next, each turning its own way."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    cubes = [1.0] if n < 3 else [1.6, 1.0, 0.5]
    o._faces = []
    for i, k in enumerate(cubes):
        a = t * (0.6 if i % 2 == 0 else -0.9) + o.phase
        size = (5 if n < 3 else 6) * z * k
        c, si = math.cos(a), math.sin(a)
        # an isometric-ish cube: three visible faces turning
        top = [(x + (c - si) * size, y - size * 0.8 + (si + c) * size * 0.3), (x + (c + si) * size, y - size * 0.8 + (si - c) * size * 0.3),
               (x - (c - si) * size, y - size * 0.8 - (si + c) * size * 0.3), (x - (c + si) * size, y - size * 0.8 - (si - c) * size * 0.3)]
        front = [top[0], top[1], (top[1][0], top[1][1] + size * 1.4), (top[0][0], top[0][1] + size * 1.4)]
        side = [top[0], top[3], (top[3][0], top[3][1] + size * 1.4), (top[0][0], top[0][1] + size * 1.4)]
        col = mix(o.body, INK, 0.1 * i)
        if i == 0 or n < 3:
            poly(s, dark(col, 0.2), side)
            poly(s, col, front)
            poly(s, lite(col, 0.2), top)
        else:
            pygame.draw.lines(s, lite(col, 0.4), True, top)
            pygame.draw.lines(s, lite(col, 0.3), True, front)
        cx = sum(px for px, _ in front) / 4
        cy = sum(py for _, py in front) / 4
        o._faces.append((cx, cy, size))
        if n == 2 and i == 0:  # shutters hinged out
            for sgn in (-1, 1):
                hx = x + sgn * size * 1.4
                pygame.draw.rect(s, dark(col, 0.1), (hx - size * 0.4, y - size * 0.6, size * 0.8, size * 1.2))
                o._faces.append((hx, y, size * 0.6))
    if n < 3:
        eyes(s, x, y - 0.5 * z, 0.01, z, t, o.phase)


def glow_sigil(o, s, t, st, k):
    z = o.size
    b = 0.6 + 0.4 * math.sin(t * 1.7 + o.phase)
    for cx, cy, size in getattr(o, "_faces", []):
        r = size * 0.35
        pygame.draw.circle(s, o.color, (round(cx), round(cy)), max(1, round(r)), 1)
        pygame.draw.line(s, o.color, (cx - r, cy), (cx + r, cy))
        pygame.draw.line(s, o.color, (cx, cy - r), (cx, cy + r * 0.5))
        glow(s, cx, cy, int(r * 2 + 2), o.color, q(60 * b + 50 * k))


# ===================================== the Snowy Ridge ========================================

def draw_snowp(o, s, t):
    """Snowpuff: a fluffy snowball on two tiny feet, picking up snow as it rolls. Snowcloak: a big
    snowball draped in flaps of crusted ice. Snowmonarch: a great rolling mound of snow, an
    icicle crown, little avalanches puffing off it."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    R = (5, 8, 11)[n - 1] * z
    cy = y - R - (z if n == 1 else 0)
    if n == 1:
        for side in (-1, 1):
            pygame.draw.ellipse(s, (180, 190, 220), (o.x + side * 2 * z - z, y - 1.6 * z, 2.4 * z, 1.6 * z))
    roll = -o.x / R * f
    pygame.draw.circle(s, (180, 196, 230), (round(x), round(cy + 1)), round(R))
    pygame.draw.circle(s, o.body, (round(x), round(cy)), round(R))
    for j in range(8 + 4 * n):  # clumps of snow stuck on, turning as it rolls
        a = roll + j * 2.4
        d = R * (0.4 + 0.5 * ((j * 7) % 5) / 5)
        pygame.draw.circle(s, (220, 230, 250) if j % 2 else WHITE, (round(x + math.cos(a) * d), round(cy + math.sin(a) * d)), max(1, round(1.4 * z)))
    if n >= 2:
        for j in range(5):  # flaps of crusted ice
            a = math.pi * (0.1 + j * 0.2)
            px, py = x + math.cos(a + math.pi) * R, cy + math.sin(a + math.pi) * R * 0.2
            poly(s, (196, 220, 246), [(px - 2 * z, py), (px + 2 * z, py), (px, py + (4 + n) * z)])
    if n == 3:
        for j in range(5):
            cx = x + (j - 2) * 3 * z
            poly(s, (200, 236, 255), [(cx - z, cy - R + 1.5 * z), (cx + z, cy - R + 1.5 * z), (cx, cy - R - (3 + (j == 2) * 3) * z)])
    eyes(s, x + f * R * 0.3, cy - R * 0.1, 3 * z, z, t, o.phase)


def glow_snowp(o, s, t, st, k):
    z, n = o.size, stage(o)
    if n == 3 and moving(o):
        for j in range(4):
            kk = (t * 0.8 + j / 4) % 1.0
            s.set_at((round(o.x - o.facing * (8 + kk * 8) * z), round(o.y - kk * 4 * z)), WHITE)
    glow(s, o.x, o.y - 8 * z, int((5 + 3 * n) * z), o.color, q(25 + 60 * k))


def draw_shiver(o, s, t):
    """Shiverling: a splinter of steel-blue ice that skates along on two blades, trembling.
    Shivershard: a cluster of blades standing on their points like a snowflake, turning as it
    goes. Shiverspire: a great wheel of ice and steel, a snowflake as big as a cartwheel,
    spinning across the snow."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    tremble = math.sin(t * 40) * 0.4 * z
    if n == 1:
        for side in (-1, 1):
            pygame.draw.line(s, (220, 230, 245), (x - 3 * z + side * z, y), (x + 3 * z + side * z, y - 0.5 * z))
        pts = [(x - 2 * z + tremble, y - z), (x + 2 * z + tremble, y - z), (x + 1 * z + tremble, y - 11 * z), (x - 0.5 * z + tremble, y - 13 * z)]
        poly(s, o.body, pts, rim=WHITE)
        eyes(s, x + tremble, y - 6 * z, 2 * z, z, t, o.phase)
        o._hub = (x, y - 6 * z)
        return
    R = (8 if n == 2 else 13) * z
    cx, cy = x, y - R
    spin = -o.x / R * o.facing if moving(o) else t * 0.3
    for j in range(6):
        a = spin + j * TAU / 6
        ex, ey = cx + math.cos(a) * R, cy + math.sin(a) * R
        pygame.draw.line(s, o.body, (cx, cy), (ex, ey), max(2, round(1.6 * z)))
        for b in (0.45, 0.75):  # side-branches of the flake
            bx, by = cx + math.cos(a) * R * b, cy + math.sin(a) * R * b
            for sgn in (-1, 1):
                pygame.draw.line(s, lite(o.body, 0.4), (bx, by), (bx + math.cos(a + sgn * 0.9) * R * 0.2, by + math.sin(a + sgn * 0.9) * R * 0.2))
    if n == 3:
        pygame.draw.circle(s, (150, 160, 190), (round(cx), round(cy)), round(R), 1)  # a steel rim
    pygame.draw.circle(s, lite(o.body, 0.3), (round(cx), round(cy)), max(2, round(3 * z)))
    eyes(s, cx, cy, 2 * z, z, t, o.phase)
    o._hub = (cx, cy)


def glow_shiver(o, s, t, st, k):
    x, y = getattr(o, "_hub", (o.x, o.y))
    glow(s, x, y, int((5 + 4 * stage(o)) * o.size), o.color, q(40 + 60 * k))


def draw_glace(o, s, t):
    """Glacelet: a thin flake of ice folded like a paper dart, gliding. Glaceglide: wider, frost
    trails off its wingtips. Glacewing: a glider of many clear panes of ice, light splitting into
    colours through them."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    L = (8 + 4 * n) * z
    W = (3 + 2.5 * n) * z
    tip = (x + f * L * 0.6, y)
    back = (x - f * L * 0.4, y)
    panes = 1 if n < 3 else 3
    for p in range(panes):
        off = (p - (panes - 1) / 2) * 3 * z
        wing_up = (back[0] + f * p * z, y - W + off * 0.3)
        wing_dn = (back[0] + f * p * z, y + W * 0.5 + off * 0.3)
        pygame.draw.polygon(s, mix(o.body, (150, 190, 240), 0.2 + 0.1 * p), [tip, wing_up, back])
        pygame.draw.polygon(s, mix(o.body, (120, 160, 220), 0.3), [tip, back, wing_dn])
        pygame.draw.lines(s, WHITE, False, [wing_up, tip, wing_dn])
    pygame.draw.line(s, lite(o.body, 0.5), tip, back)
    eyes(s, x + f * L * 0.3, y - 0.8 * z, 1.8 * z, z, t, o.phase)
    o._tips = [(back[0], y - W), (back[0], y + W * 0.5)]


def glow_glace(o, s, t, st, k):
    z, n = o.size, stage(o)
    if n >= 2:
        for i, (px, py) in enumerate(o.trail[1:]):
            for j, (tx, ty) in enumerate(getattr(o, "_tips", [])):
                s.set_at((round(px + tx - o.x), round(py + ty - o.y)), mix(WHITE, (40, 50, 110), i / 8))
    if n == 3:
        from beasts import PRISM
        for j, c in enumerate(PRISM[:4]):
            s.set_at((round(o.x - o.facing * j * z), round(o.y + 2 * z + j * 0.5 * z)), c)
    glow(s, o.x, o.y, int((5 + 2 * n) * z), o.color, q(30 + 60 * k))


def draw_cone(o, s, t):
    """Conelet: a pinecone that rolls along end over end, frost in its scales. Conecrest: the cone
    opened up, standing on its lowest scales and walking on them. Conelord: a towering frost-cone,
    its scales flared like a little snowy tree, seeds of ice in every one."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    h = (8, 13, 20)[n - 1] * z
    w = (4, 5.5, 8)[n - 1] * z
    tilt = math.sin(o.step * 0.6) * 0.3 if moving(o) and n == 1 else 0
    base = y - (2 * z if n > 1 else 0)
    o._seeds = []
    rows = int(h / z / 2)
    for r in range(rows):
        f_ = r / rows
        rw = w * math.sin((1 - f_) * math.pi * 0.85 + 0.25) * (1 + 0.3 * (n == 3) * (1 - f_))
        ry = base - f_ * h
        rx = x + tilt * f_ * h
        for j in range(-2, 3):
            sx = rx + j * rw * 0.4
            flare = (1 + n * 0.5) * z
            poly(s, o.body if (r + j) % 2 else lite(o.body, 0.12), [(sx - rw * 0.25, ry), (sx + rw * 0.25, ry), (sx, ry + flare)])
            if (r + j) % 3 == 0:
                s.set_at((round(sx), round(ry + 0.3 * flare)), (230, 245, 255))
                if n == 3:
                    o._seeds.append((sx, ry + 0.3 * flare))
    if n > 1:
        for j in (-1, 1):  # scale-feet
            pygame.draw.line(s, dark(o.body, 0.3), (x + j * w * 0.5, base), (x + j * w * 0.7, y), max(1, round(z)))
    eyes(s, x + f * w * 0.2, base - h * 0.35, 2.4 * z, z, t, o.phase)


def glow_cone(o, s, t, st, k):
    z = o.size
    for i, (sx, sy) in enumerate(getattr(o, "_seeds", [])):
        if math.sin(t * 2 + i) > 0:
            glow(s, sx, sy, int(2 * z), o.color, q(70))
    if k > 0:
        glow(s, o.x, o.y - 8 * z, int(10 * z), o.color, q(80 * k))


# ===================================== the Hot Springs ========================================

def draw_ash(o, s, t):
    """Ashpaw: a lump of charcoal that pads about on four glowing paw-pads of ember. Ashstride: a
    long brazier of a body on iron legs, coals heaped in it. Ashcolossus: a great walking kiln,
    fire roaring behind the grate in its side."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    if n == 1:
        for i, lx in enumerate((-3, -1, 1.5, 3.5)):
            lift = max(0.0, math.sin(o.step * 1.3 + i * 1.6)) * 1.2 * z if moving(o) else 0
            pygame.draw.ellipse(s, (255, 140, 80), (x + lx * z - z, y - 1.4 * z - lift, 2 * z, 1.4 * z))
        pts = [(x - 5 * z, y - 2 * z), (x - 4 * z, y - 7 * z), (x - z, y - 9 * z), (x + 3 * z, y - 8 * z), (x + 5 * z, y - 4 * z), (x + 4 * z, y - 1.5 * z)]
        poly(s, o.body, pts)
        o._fire = [(x, y - 5 * z)]
        eyes(s, x + f * 2 * z, y - 6 * z, 2.4 * z, z, t, o.phase)
        return
    W, H = (14 if n == 2 else 16) * z, (6 if n == 2 else 14) * z
    legh = (5 if n == 2 else 3) * z
    for lx in (-W * 0.4, -W * 0.15, W * 0.15, W * 0.4) if n == 2 else (-W * 0.35, W * 0.35):
        lift = max(0.0, math.sin(o.step + lx)) * 1.5 * z if moving(o) else 0
        pygame.draw.line(s, (60, 54, 60), (x + lx, y - legh), (x + lx, y - lift), max(1, round(z * 1.3)))
    rect = pygame.Rect(0, 0, round(W), round(H))
    rect.midbottom = (round(x), round(y - legh))
    if n == 2:  # a brazier: a bowl of iron, coals heaped in it
        pygame.draw.polygon(s, (60, 54, 60), [rect.topleft, rect.topright, (rect.right - 2 * z, rect.bottom), (rect.x + 2 * z, rect.bottom)])
        for j in range(6):
            pygame.draw.circle(s, o.body, (round(rect.x + (j + 0.5) * W / 6), round(rect.y - (j % 2) * z)), max(1, round(1.8 * z)))
        o._fire = [(rect.x + (j + 0.5) * W / 3, rect.y - z) for j in range(3)]
        eyes(s, rect.centerx + f * W * 0.3, rect.centery, 2.4 * z, z, t, o.phase)
    else:  # a kiln: a dome of brick, a grate in its side, a chimney
        pygame.draw.rect(s, (110, 70, 66), rect, border_top_left_radius=round(W / 2), border_top_right_radius=round(W / 2))
        for r_ in range(1, 5):
            pygame.draw.line(s, (90, 56, 54), (rect.x, rect.bottom - r_ * 3 * z), (rect.right, rect.bottom - r_ * 3 * z))
        grate = pygame.Rect(0, 0, round(W * 0.45), round(H * 0.4))
        grate.midbottom = (rect.centerx, rect.bottom - z)
        pygame.draw.rect(s, (40, 20, 20), grate)
        o._grate = grate
        pygame.draw.rect(s, (90, 56, 54), (rect.centerx - f * W * 0.25 - z, rect.y - 4 * z, 2.4 * z, 6 * z))
        o._fire = [(rect.centerx - f * W * 0.25, rect.y - 5 * z)]
        eyes(s, rect.centerx, rect.y + H * 0.3, 3 * z, z, t, o.phase)


def glow_ash(o, s, t, st, k):
    z, n = o.size, stage(o)
    for i, (fx, fy) in enumerate(getattr(o, "_fire", [])):
        h = (2 + abs(math.sin(t * 8 + i * 1.7)) * 2) * z
        if n == 3:  # chimney smoke and sparks
            kk = (t * 0.6 + o.phase) % 1.0
            s.set_at((round(fx + math.sin(t + kk * 4) * z), round(fy - kk * 10 * z)), mix((255, 200, 140), (60, 40, 50), kk))
        else:
            poly(s, (255, 160, 80), [(fx - 1.4 * z, fy + z), (fx + 1.4 * z, fy + z), (fx, fy - h)])
        glow(s, fx, fy, int(5 * z), o.color, q(90 + 50 * k))
    g = getattr(o, "_grate", None)
    if n == 3 and g is not None:
        b = 0.6 + 0.4 * math.sin(t * 6) * math.sin(t * 3.3)
        pygame.draw.rect(s, mix((255, 120, 50), (255, 220, 140), b), g.inflate(-2, -2))
        for j in range(1, 4):
            pygame.draw.line(s, (40, 20, 20), (g.x + j * g.w / 4, g.y), (g.x + j * g.w / 4, g.bottom))
        glow(s, g.centerx, g.centery, int(10 * z), o.color, q(120 * b + 40 * k))


def draw_sulf(o, s, t):
    """Sulfling: a little crater of yellow mud, bubbling, that creeps about. Sulfspout: a chimney
    of crusted sulphur, puffing yellow fumes. Sulfgeyser: a terraced vent-cone, its top blowing a
    jet of steam now and then."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    if n == 1:
        pygame.draw.ellipse(s, dark(o.body, 0.3), (x - 6 * z, y - 4 * z, 12 * z, 5 * z))
        pygame.draw.ellipse(s, o.body, (x - 6 * z, y - 5 * z, 12 * z, 5 * z))
        pygame.draw.ellipse(s, (170, 150, 70), (x - 3.5 * z, y - 4 * z, 7 * z, 2.5 * z))
        eyes(s, x, y - 2.5 * z, 2.4 * z, z, t, o.phase)
        o._vent = (x, y - 3 * z)
        return
    tiers = 1 if n == 2 else 3
    top = y
    for i in range(tiers):
        w = (5 - i * 1.2 + (n - 2) * 3) * z
        h = (8 if n == 2 else 5) * z
        pts = [(x - w, top), (x + w, top), (x + w * 0.65, top - h), (x - w * 0.65, top - h)]
        poly(s, lite(o.body, 0.08 * i), pts)
        pygame.draw.line(s, lite(o.body, 0.4), pts[3], pts[2])
        top -= h
    pygame.draw.ellipse(s, (90, 70, 40), (x - 2 * z, top - z, 4 * z, 2 * z))
    eyes(s, x, top + (4 if n == 2 else 3) * z, 2.4 * z, z, t, o.phase)
    o._vent = (x, top)


def glow_sulf(o, s, t, st, k):
    z, n = o.size, stage(o)
    vx, vy = getattr(o, "_vent", (o.x, o.y))
    for j in range(2 + n):  # bubbles / fumes
        kk = (t * 0.5 + j / (2 + n) + o.phase) % 1.0
        c = mix((255, 236, 120), (60, 50, 40), kk)
        pygame.draw.circle(s, c, (round(vx + math.sin(t * 1.3 + j * 2) * (1 + kk * 3) * z), round(vy - kk * (4 + 4 * n) * z)), max(1, round((0.8 + kk * n) * z)), 1)
    if n == 3 and ((t + o.phase) % 7 < 1.0 or k > 0.3):
        h = 16 * z
        pygame.draw.line(s, (240, 240, 220), (vx, vy), (vx, vy - h), max(2, round(1.5 * z)))
        glow(s, vx, vy - h, int(6 * z), o.color, q(100))
    glow(s, vx, vy, int((4 + 2 * n) * z), o.color, q(50 + 60 * k))


def draw_lava(o, s, t):
    """Lavalet: a blob of molten rock that flings itself through the air, streamers of fire
    behind. Lavaglide: a flat disc of glowing lava-stone that glides like a thrown plate.
    Lavacrest: a burning ring with a molten core at its middle, spinning as it flies."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    if n == 1:
        pts = [(x + math.cos(a / 7 * TAU + t * 2) * 3.4 * z * (1 + 0.2 * math.sin(t * 5 + a)), y + math.sin(a / 7 * TAU + t * 2) * 3 * z) for a in range(7)]
        poly(s, o.body, pts)
        eyes(s, x + f * z, y - 0.5 * z, 2 * z, z, t, o.phase)
    elif n == 2:
        pygame.draw.ellipse(s, dark(o.body, 0.3), (x - 8 * z, y - 2 * z, 16 * z, 5 * z))
        pygame.draw.ellipse(s, o.body, (x - 8 * z, y - 3 * z, 16 * z, 5 * z))
        eyes(s, x + f * 3 * z, y - 1 * z, 2 * z, z, t, o.phase)
    else:
        R = 10 * z
        spin = t * 4
        for j in range(16):
            a = spin + j * TAU / 16
            pygame.draw.circle(s, mix(o.body, (255, 140, 70), (j % 2) * 0.5), (round(x + math.cos(a) * R), round(y + math.sin(a) * R * 0.5)), max(1, round(1.8 * z)))
        pygame.draw.circle(s, (255, 170, 90), (round(x), round(y)), max(2, round(3.6 * z)))
        eyes(s, x, y, 2 * z, z, t, o.phase)


def glow_lava(o, s, t, st, k):
    z, n = o.size, stage(o)
    for i, (px, py) in enumerate(o.trail[1:]):
        r = round((n * 1.2 - i * 0.2) * z)
        if r >= 1:
            pygame.draw.circle(s, mix((255, 230, 150), (200, 50, 40), i / 8), (round(px), round(py)), r)
    if n == 2:  # its glowing cracks
        for j in range(4):
            a = j * 1.6 + o.phase
            pygame.draw.line(s, (255, 190, 110), (o.x, o.y - 0.5 * z), (o.x + math.cos(a) * 6 * z, o.y - 0.5 * z + math.sin(a) * 1.8 * z))
    glow(s, o.x, o.y, int((6 + 4 * n) * z), o.color, q(70 + 60 * k))


def draw_obsid(o, s, t):
    """Obsidling: a black glass arrowhead that skitters along on three blade-tips. Obsidblade: a
    crescent of obsidian rocking along its curved edge. Obsidclaw: a tumbling cluster of glass
    claws around a molten heart, rolling like a burr."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    rim = (150, 130, 170)
    if n == 1:
        for i in range(3):
            lift = max(0.0, math.sin(o.step * 1.6 + i * 2)) * 1.5 * z if moving(o) else 0
            lx = x + (i - 1) * 3 * z
            pygame.draw.line(s, rim, (lx, y - 3 * z), (lx - f * z, y - lift))
        pts = [(x + f * 7 * z, y - 5 * z), (x - f * 4 * z, y - 8.5 * z), (x - f * 2 * z, y - 5 * z), (x - f * 4 * z, y - 2 * z)]
        poly(s, o.body, pts, rim=rim)
        eyes(s, x + f * 2 * z, y - 5 * z, 2 * z, z, t, o.phase)
        o._heart = (x, y - 5 * z)
    elif n == 2:
        rock = math.sin(o.step * 0.8) * 0.4 if moving(o) else math.sin(t + o.phase) * 0.1
        R = 9 * z
        cx, cy = x, y - 2 * z
        outer = [(cx + math.cos(math.pi + rock + a / 10 * math.pi) * R, cy + math.sin(math.pi + rock + a / 10 * math.pi) * R) for a in range(11)]
        inner = [(cx + math.cos(math.pi + rock + a / 10 * math.pi) * R * 0.55, cy - 2 * z + math.sin(math.pi + rock + a / 10 * math.pi) * R * 0.45) for a in range(10, -1, -1)]
        poly(s, o.body, outer + inner, rim=rim)
        eyes(s, cx + f * 2 * z, cy - R * 0.7, 2 * z, z, t, o.phase)
        o._heart = (cx, cy - R * 0.5)
    else:
        R = 9 * z
        cx, cy = x, y - R
        roll = -o.x / R * f
        for j in range(7):
            a = roll + j * TAU / 7
            bx, by = cx + math.cos(a) * R * 0.4, cy + math.sin(a) * R * 0.4
            ex, ey = cx + math.cos(a + 0.25) * R, cy + math.sin(a + 0.25) * R
            poly(s, o.body, [(bx - math.sin(a) * 1.5 * z, by + math.cos(a) * 1.5 * z), (ex, ey), (bx + math.sin(a) * 1.5 * z, by - math.cos(a) * 1.5 * z)], rim=rim)
        pygame.draw.circle(s, (120, 40, 40), (round(cx), round(cy)), max(2, round(3.5 * z)))
        eyes(s, cx, cy, 2 * z, z, t, o.phase)
        o._heart = (cx, cy)


def glow_obsid(o, s, t, st, k):
    x, y = getattr(o, "_heart", (o.x, o.y))
    b = 0.6 + 0.4 * math.sin(t * 2.5 + o.phase)
    glow(s, x, y, int((4 + 2 * stage(o)) * o.size), o.color, q(60 * b + 20 * stage(o) + 60 * k))


# ===================================== the Battle Tower =======================================

def draw_gong(o, s, t):
    """Gongling: a small bronze gong hung in a little walking frame, ringing as it steps.
    Gongstrike: a heavier gong, a padded mallet swinging from its frame like a tail. Gongmaster:
    a great temple bell on four sturdy feet, its clapper swinging, rings of sound rolling off."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    wood = (120, 80, 70)
    if n < 3:
        R = (5 if n == 1 else 7) * z
        legh = 13 * z if n == 1 else 17 * z
        for i, side in enumerate((-1, 1)):  # an A-frame stand stepping
            lift = max(0.0, math.sin(o.step + i * math.pi)) * 1.5 * z if moving(o) else 0
            pygame.draw.line(s, wood, (x + side * (R + 2 * z), y - lift), (x + side * 0.5 * z, y - legh - 2 * z), max(1, round(z * 1.2)))
        pygame.draw.line(s, wood, (x - R - z, y - legh - 2 * z), (x + R + z, y - legh - 2 * z), max(1, round(z * 1.4)))
        cx, cy = x, y - legh + R * 0.7
        swing = math.sin(t * 2 + o.phase) * 0.15
        pygame.draw.line(s, wood, (cx, y - legh - 2 * z), (cx + swing * R, cy - R))
        pygame.draw.circle(s, dark(o.body, 0.3), (round(cx + swing * R), round(cy + 1)), round(R))
        pygame.draw.circle(s, o.body, (round(cx + swing * R), round(cy)), round(R))
        pygame.draw.circle(s, lite(o.body, 0.3), (round(cx + swing * R), round(cy)), round(R * 0.6), 1)
        eyes(s, cx + swing * R, cy, 2.4 * z, z, t, o.phase)
        if n == 2:  # the mallet-tail
            mx, my = x - f * (R + 5 * z), y - legh * 0.6 + math.sin(t * 3 + o.phase) * 2 * z
            pygame.draw.line(s, wood, (x - f * (R + z), y - legh), (mx, my))
            pygame.draw.circle(s, (220, 200, 180), (round(mx), round(my)), max(2, round(2 * z)))
        o._ring = (cx, cy, R)
        return
    for i, lx in enumerate((-6, -2, 2, 6)):
        lift = max(0.0, math.sin(o.step + i * 1.6)) * 1.2 * z if moving(o) else 0
        pygame.draw.rect(s, dark(o.body, 0.4), (x + lx * z - z, y - 4 * z - lift, 2 * z, 4 * z))
    bell = [(x - 9 * z, y - 4 * z), (x - 7.5 * z, y - 9 * z), (x - 5 * z, y - 17 * z), (x - 3 * z, y - 19 * z), (x + 3 * z, y - 19 * z),
            (x + 5 * z, y - 17 * z), (x + 7.5 * z, y - 9 * z), (x + 9 * z, y - 4 * z)]
    poly(s, o.body, bell)
    pygame.draw.line(s, lite(o.body, 0.35), (x - 4 * z, y - 17 * z), (x - 6.5 * z, y - 7 * z))
    for yy in (y - 7 * z, y - 15 * z):
        pygame.draw.line(s, dark(o.body, 0.25), (x - 7 * z, yy), (x + 7 * z, yy))
    pygame.draw.rect(s, dark(o.body, 0.3), (x - 1.5 * z, y - 22 * z, 3 * z, 3 * z))
    eyes(s, x, y - 11 * z, 4 * z, z, t, o.phase)
    o._ring = (x, y - 11 * z, 9 * z)


def glow_gong(o, s, t, st, k):
    cx, cy, R = getattr(o, "_ring", (o.x, o.y, 5))
    z = o.size
    rings = 1 + stage(o) if k > 0 or (t + o.phase) % 6 < 2 else 0
    for j in range(rings):
        kk = (t * 0.9 + j / max(1, rings)) % 1.0
        r = round(R + kk * 10 * z)
        pygame.draw.circle(s, mix(o.color, (30, 20, 60), kk), (round(cx), round(cy)), r, 1)
    glow(s, cx, cy, int(R + 4 * z), o.color, q(30 + 60 * k))


def draw_spire(o, s, t):
    """Spirelet: a little steel spinning-top that hovers, humming as it turns. Spireguard: a taller
    top with two rings orbiting it. Spirehalo: a long needle of a spire, three halos turning about
    it at different speeds."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    spin = t * 10
    h = (8, 12, 20)[n - 1] * z
    w = (5, 5.5, 4)[n - 1] * z
    body = [(x, y + h * 0.4), (x - w, y - h * 0.1), (x - w * 0.4, y - h * 0.5), (x, y - h * 0.6), (x + w * 0.4, y - h * 0.5), (x + w, y - h * 0.1)]
    poly(s, o.body, body)
    for j in range(3):  # bands that show it spinning
        bx = x + math.sin(spin + j * 2.1) * w * 0.8
        pygame.draw.line(s, dark(o.body, 0.25), (bx, y - h * 0.35), (bx, y + h * 0.1))
    pygame.draw.line(s, lite(o.body, 0.4), (x, y - h * 0.6), (x, y - h * 0.9))
    eyes(s, x, y - h * 0.15, 2.4 * z, z, t, o.phase)
    o._rings = [] if n == 1 else [(y - h * 0.1, 8 * z, 1.0), (y - h * 0.3, 6 * z, -1.5)][: n] if n == 2 else \
        [(y - h * 0.5, 5 * z, 1.0), (y - h * 0.2, 8 * z, -0.7), (y + h * 0.1, 11 * z, 0.5)]
    o._h = h


def glow_spire(o, s, t, st, k):
    z = o.size
    for i, (ry, R, sp) in enumerate(getattr(o, "_rings", [])):
        tilt = math.sin(t * sp + i) * 0.4
        pygame.draw.ellipse(s, mix(o.color, WHITE, 0.4), (o.x - R, ry - R * (0.2 + abs(tilt) * 0.3), 2 * R, R * (0.4 + abs(tilt) * 0.6)), 1)
        a = t * sp * 2
        glow(s, o.x + math.cos(a) * R, ry, int(3 * z), o.color, q(90))
    glow(s, o.x, o.y - getattr(o, "_h", 8) * 0.9, int(4 * z), o.color, q(70 + 60 * k))


def draw_duel(o, s, t):
    """Dueljab: two little round halves on a cord, forever sparring: one darts in, the other
    bounces off. Dueledge: two crescents circling each other, edges flashing. Duelheart: the two
    crescents locked round a burning heart, spinning together as one."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    spar = math.sin(t * 4 + o.phase)
    if n == 1:
        a = (x - (4 + 2 * max(0.0, spar)) * z, y + math.sin(t * 6) * z)
        b = (x + (4 + 2 * max(0.0, -spar)) * z, y - math.sin(t * 6) * z)
        pygame.draw.line(s, (90, 60, 80), a, b)
        for i, (px, py) in enumerate((a, b)):
            c = o.body if i == 0 else (80, 70, 110)
            shaded(s, c, (px - 3 * z, py - 3 * z, 6 * z, 6 * z))
            eyes(s, px + (1 if i == 0 else -1) * z, py - 0.5 * z, 1.6 * z, z, t, o.phase + i)
        o._mid = (x, y)
        return
    R = (6 if n == 2 else 7) * z
    spin = t * (2 if n == 2 else 4)
    gap = (4 + 2 * spar) * z if n == 2 else 0
    for i in range(2):
        a0 = spin + i * math.pi
        cx, cy = x + math.cos(a0) * gap, y + math.sin(a0) * gap * 0.5
        outer = [(cx + math.cos(a0 + math.pi / 2 + a / 8 * math.pi) * R, cy + math.sin(a0 + math.pi / 2 + a / 8 * math.pi) * R) for a in range(9)]
        inner = [(cx + math.cos(a0 + math.pi / 2 + a / 8 * math.pi) * R * 0.55 + math.cos(a0) * R * 0.25,
                  cy + math.sin(a0 + math.pi / 2 + a / 8 * math.pi) * R * 0.55 + math.sin(a0) * R * 0.25) for a in range(8, -1, -1)]
        poly(s, o.body if i == 0 else (80, 70, 110), outer + inner, rim=lite(o.body, 0.4))
    eyes(s, x, y - R * 0.2, 2 * z, z, t, o.phase)
    o._mid = (x, y)


def glow_duel(o, s, t, st, k):
    x, y = getattr(o, "_mid", (o.x, o.y))
    z, n = o.size, stage(o)
    if n == 3:
        b = 0.7 + 0.3 * math.sin(t * 5)
        pygame.draw.circle(s, (255, 140, 160), (round(x), round(y)), max(2, round(2.4 * z)))
        glow(s, x, y, int(10 * z), o.color, q(110 * b + 40 * k))
    elif abs(math.sin(t * 4 + o.phase)) > 0.95 or k > 0:  # a flash where they clash
        glow(s, x, y, int(6 * z), WHITE, q(130))


# ===================================== the Crystal Caverns ====================================

def draw_myce(o, s, t):
    """Mycelet: a creeping net of pale threads with a few tiny mushroom caps, spreading along.
    Mycespire: a tall spire of mushroom caps stacked on the net. Mycethrone: a mound of shelf-
    fungus in tiers, its net of glowing threads reaching out all round."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    reach = (8, 11, 15)[n - 1] * z
    o._caps = []
    for j in range(5 + 2 * n):  # the net
        a = math.pi * (j / (4 + 2 * n))
        ex = x + math.cos(a) * reach * (1 + 0.2 * math.sin(t * 0.8 + j))
        pygame.draw.lines(s, (200, 186, 220), False, [(x, y - z), ((x + ex) / 2, y - 0.5 * z + (j % 2) * z), (ex, y)])
    if n == 1:
        for j, (cx, h) in enumerate(((-4, 3), (1, 4), (5, 2.5))):
            pygame.draw.line(s, (230, 220, 236), (x + cx * z, y), (x + cx * z, y - h * z))
            pygame.draw.ellipse(s, o.color, (x + cx * z - 1.6 * z, y - h * z - 1.2 * z, 3.2 * z, 1.8 * z))
            o._caps.append((x + cx * z, y - h * z))
        eyes(s, x + f * z, y - 1.5 * z, 2 * z, z, t, o.phase)
        return
    tiers = 4 if n == 2 else 4
    for i in range(tiers):
        w = ((3 - i * 0.4) if n == 2 else (8 - i * 1.4)) * z
        cy = y - (2 + i * (4 if n == 2 else 3.5)) * z
        pygame.draw.ellipse(s, dark(o.body, 0.3), (x - w, cy - 1.5 * z + 1, 2 * w, 3 * z))
        pygame.draw.ellipse(s, mix(o.body, o.color, 0.15 * (i % 2)), (x - w, cy - 1.5 * z, 2 * w, 3 * z))
        o._caps.append((x, cy - z))
    if n == 2:
        pygame.draw.line(s, (230, 220, 236), (x, y), (x, y - 15 * z))
    eyes(s, x, y - (4 if n == 2 else 4) * z, 2.6 * z, z, t, o.phase)


def glow_myce(o, s, t, st, k):
    z = o.size
    for i, (cx, cy) in enumerate(getattr(o, "_caps", [])):
        b = 0.5 + 0.5 * math.sin(t * 1.5 + i * 1.3 + o.phase)
        glow(s, cx, cy, int(4 * z), o.color, q(50 * b + 30 + 40 * k))
    if stage(o) == 3:  # pulses running out along the net
        kk = (t * 0.5) % 1.0
        for j in range(5):
            a = math.pi * j / 4
            s.set_at((round(o.x + math.cos(a) * 15 * z * kk), round(o.y - 0.5 * z)), o.color)


def draw_deep(o, s, t):
    """Deepling: a moving puddle of deep black water, a little lure of light dangling over it and
    two eyes shining up from below. Deepglow: a wider pool, a rim of pointed stones like teeth.
    Deepmaw: a gaping round well of dark water, ringed with stone teeth, the lure swinging high
    above it."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    W = (7, 10, 13)[n - 1] * z
    pygame.draw.ellipse(s, (16, 18, 40), (x - W, y - W * 0.35, 2 * W, W * 0.7))
    pygame.draw.ellipse(s, (40, 60, 110), (x - W, y - W * 0.35, 2 * W, W * 0.7), 1)
    if n >= 2:
        k = 8 if n == 2 else 12
        for j in range(k):
            a = j / k * TAU
            px, py = x + math.cos(a) * W, y + math.sin(a) * W * 0.35
            if math.sin(a) < 0.3:
                poly(s, (130, 126, 150), [(px - 1.2 * z, py), (px + 1.2 * z, py), (px, py - (2 + n) * z)])
    stem = (x - f * W * 0.5, y - W * 0.2)
    lure = (x + f * W * 0.3 + math.sin(t * 1.5 + o.phase) * 2 * z, y - (8 + 5 * n) * z)
    pygame.draw.lines(s, (70, 80, 110), False, [stem, ((stem[0] + lure[0]) / 2, lure[1] - 3 * z), lure])
    o._lure = lure


def glow_deep(o, s, t, st, k):
    z = o.size
    lx, ly = getattr(o, "_lure", (o.x, o.y))
    b = 0.7 + 0.3 * math.sin(t * 2.5 + o.phase)
    glow(s, lx, ly, int((4 + 2 * stage(o)) * z), o.color, q(110 * b + 40 * k))
    pygame.draw.circle(s, lite(o.color, 0.4), (round(lx), round(ly)), max(1, round(1.3 * z)))
    if (t * 0.5 + o.phase) % 5 > 0.2:  # its eyes, down in the dark
        for side in (-1, 1):
            s.set_at((round(o.x + side * 1.8 * z), round(o.y)), o.color)


def draw_quartz(o, s, t):
    """Quartzlet: one hexagonal crystal lying on its side, rolling from face to face. Quartzback: a
    cluster of crossed crystals standing on their points. Quartzcolossus: a great druse, a dome
    of rock lined inside with crystals, walking on stubby crystal feet."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    if n == 1:
        roll = (o.x * 0.25) % (TAU / 6) if moving(o) else 0
        R = 4 * z
        cx, cy = x, y - R
        pts = [(cx + math.cos(roll + a / 6 * TAU) * R * 1.6, cy + math.sin(roll + a / 6 * TAU) * R) for a in range(6)]
        poly(s, o.body, pts, rim=WHITE)
        pygame.draw.line(s, lite(o.body, 0.5), pts[0], pts[3])
        eyes(s, cx, cy, 2.4 * z, z, t, o.phase)
        o._glints = [pts[1]]
        return
    if n == 2:
        o._glints = []
        for j, (lean, h) in enumerate(((-0.4, 12), (0.3, 14), (0.0, 10))):
            bx = x + (j - 1) * 2 * z
            tip = (bx + lean * h * z, y - h * z)
            poly(s, lite(o.body, 0.1 * j), [(bx - 1.5 * z, y), (bx + 1.5 * z, y), (tip[0] + 1.5 * z, tip[1] + 2 * z), tip, (tip[0] - 1.5 * z, tip[1] + 2 * z)], rim=WHITE)
            o._glints.append(tip)
        eyes(s, x, y - 5 * z, 2.4 * z, z, t, o.phase)
        return
    for i, lx in enumerate((-6, -2, 2, 6)):
        lift = max(0.0, math.sin(o.step + i * 1.6)) * 1.2 * z if moving(o) else 0
        poly(s, o.body, [(x + lx * z - z, y - 4 * z - lift), (x + lx * z + z, y - 4 * z - lift), (x + lx * z, y - lift)])
    dome = pygame.Rect(0, 0, round(20 * z), round(16 * z))
    dome.midbottom = (round(x), round(y - 3 * z))
    pygame.draw.ellipse(s, (110, 104, 120), dome)
    inner = dome.inflate(-round(5 * z), -round(5 * z)).move(round(f * 1.5 * z), round(z))
    pygame.draw.ellipse(s, (60, 50, 80), inner)
    o._glints = []
    for j in range(7):
        a = j / 7 * TAU
        px, py = inner.centerx + math.cos(a) * inner.w * 0.3, inner.centery + math.sin(a) * inner.h * 0.3
        poly(s, mix(o.body, o.color, 0.3), [(px - z, py + z), (px + z, py + z), (inner.centerx + math.cos(a) * inner.w * 0.08, inner.centery + math.sin(a) * inner.h * 0.08)])
        o._glints.append((px, py))
    eyes(s, dome.centerx + f * 6 * z, dome.y + 4 * z, 2.4 * z, z, t, o.phase)


def glow_quartz(o, s, t, st, k):
    z = o.size
    for i, (gx, gy) in enumerate(getattr(o, "_glints", [])):
        if math.sin(t * 2 + i * 1.9 + o.phase) > 0.3:
            s.set_at((round(gx), round(gy)), WHITE)
            glow(s, gx, gy, int(3 * z), o.color, q(70))
    glow(s, o.x, o.y - 6 * z, int((4 + 3 * stage(o)) * z), o.color, q(20 + 60 * k))


def draw_gem(o, s, t):
    """Gemmet: a little cut gem that flies on two thin panes of glass. Gemwing: a brilliant-cut
    stone, four panes beating. Gemflare: a great gem burning with light, rays fanning from it
    for wings."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    beat = abs(math.cos(t * 12 + o.phase))
    panes = 1 if n == 1 else 2
    if n < 3:
        for p in range(panes):
            w, h = (5 - p) * z * (0.4 + 0.6 * beat), (6 - p) * z
            for side in (-1, 1):
                rect = (x + (0 if side > 0 else -w), y - h + p * 3 * z, w, h)
                pygame.draw.rect(s, mix(o.color, WHITE, 0.7), rect, 1)
    R = (3, 4.5, 6)[n - 1] * z
    pts = [(x, y - R), (x + R, y - R * 0.3), (x + R * 0.6, y + R * 0.2), (x, y + R), (x - R * 0.6, y + R * 0.2), (x - R, y - R * 0.3)]
    poly(s, o.body, pts, rim=WHITE)
    for p in pts[1:3] + pts[4:6]:
        pygame.draw.line(s, lite(o.body, 0.4), (x, y - R * 0.2), p)
    eyes(s, x, y - R * 0.1, 2 * z, z, t, o.phase)


def glow_gem(o, s, t, st, k):
    z, n = o.size, stage(o)
    if n == 3:
        for j in range(9):
            a = math.pi * (1.05 + j / 8 * 0.9) + math.sin(t * 2) * 0.05
            for side in (-1, 1):
                aa = a if side < 0 else math.pi - a
                ln = (8 + (j % 3) * 3) * z * (0.7 + 0.3 * abs(math.cos(t * 6)))
                pygame.draw.line(s, mix(o.color, WHITE, 0.4), (o.x, o.y), (o.x + math.cos(aa) * ln * -side * -1, o.y + math.sin(aa) * ln))
    glow(s, o.x, o.y, int((4 + 3 * n) * z), o.color, q(60 + 20 * n + 50 * k))


# ===================================== the Starfall Meadow ====================================

def draw_starb(o, s, t):
    """Starbud: a seed with a five-pointed sprout, creeping along on its root-tips. Starbloom: a
    rosette of star-shaped leaves flat on the ground, a bud of light at its heart. Starblossom: a
    tall stalk crowned by a star-flower, pollen like falling stars drifting from it."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    for j in range(4):  # root-tips it creeps on
        pygame.draw.line(s, (150, 110, 90), (x, y - z), (x + (j - 1.5) * 2 * z + math.sin(o.step + j) * 0.5 * z, y + 0.5 * z))

    def star(cx, cy, r1, r2, c, rot=0.0):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5 + rot
            r = r1 if i % 2 == 0 else r2
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        poly(s, c, pts)

    if n == 1:
        shaded(s, (150, 110, 90), (x - 3 * z, y - 5 * z, 6 * z, 5 * z))
        pygame.draw.line(s, o.body, (x, y - 5 * z), (x, y - 8 * z))
        star(x, y - 10 * z, 3 * z, 1.3 * z, o.body, math.sin(t + o.phase) * 0.2)
        eyes(s, x, y - 2.5 * z, 2 * z, z, t, o.phase)
        o._bud = (x, y - 10 * z)
    elif n == 2:
        for j in range(5):
            a = j / 5 * TAU + 0.3
            star(x + math.cos(a) * 5 * z, y - 2 * z + math.sin(a) * 1.6 * z, 3.2 * z, 1.4 * z, o.body if j % 2 else lite(o.body, 0.15), a)
        eyes(s, x, y - 2 * z, 2.4 * z, z, t, o.phase)
        o._bud = (x, y - 4 * z)
    else:
        sway = math.sin(t * 1.2 + o.phase) * 2 * z
        pygame.draw.lines(s, (100, 160, 110), False, [(x, y - z), (x + sway * 0.4, y - 10 * z), (x + sway, y - 20 * z)], max(1, round(z * 1.2)))
        for side, hy in ((-1, 7), (1, 12)):
            star(x + side * 3 * z + sway * hy / 20, y - hy * z, 2.4 * z, 1.1 * z, o.body)
        star(x + sway, y - 23 * z, 6 * z, 2.6 * z, (255, 236, 170), t * 0.2)
        eyes(s, x + sway, y - 23 * z, 2.4 * z, z, t, o.phase)
        o._bud = (x + sway, y - 23 * z)


def glow_starb(o, s, t, st, k):
    z, n = o.size, stage(o)
    bx, by = getattr(o, "_bud", (o.x, o.y))
    glow(s, bx, by, int((4 + 3 * n) * z), o.color, q(50 + 20 * n + 60 * k))
    if n == 3:
        for j in range(4):  # pollen falling like stars
            kk = (t * 0.25 + j / 4 + o.phase) % 1.0
            px, py = bx + (j - 1.5) * 3 * z + kk * 4 * z, by + kk * 22 * z
            s.set_at((round(px), round(py)), mix((255, 250, 220), (40, 30, 80), kk))


def draw_breeze(o, s, t):
    """Breezlet: a little curl of wind carrying a leaf about. Breezeplume: a bigger swirl, streamers
    unrolling behind. Breezemonarch: a great wind-wheel of curls, many leaves riding round it, a
    tuft of cloud for a crest."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    curls = 1 if n < 3 else 3
    o._leaves = []
    for c in range(curls):
        cx = x + (c - (curls - 1) / 2) * 7 * z
        cy = y + (abs(c - 1) * 2 * z if curls > 1 else 0)
        R = (4 if n == 1 else 6) * z
        pts = []
        for i in range(30):
            a = i * 0.32 + t * 3 * (1 if c % 2 == 0 else -1)
            r = R * i / 30
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8))
        pygame.draw.lines(s, o.body, False, pts)
        a = t * 3 + c * 2
        o._leaves.append((cx + math.cos(a) * R, cy + math.sin(a) * R * 0.8, a))
    if n >= 2:
        for j in range(n):
            pygame.draw.lines(s, mix(o.body, (60, 70, 130), 0.4), False,
                              [(px - f * 4 * z, py + (j - 0.5) * 2 * z + math.sin(t * 4 + i) * z) for i, (px, py) in enumerate(o.trail)])
    if n == 3:
        for j in range(4):
            pygame.draw.circle(s, (230, 234, 250), (round(x + (j - 1.5) * 3 * z), round(y - 8 * z - (j % 2) * z)), max(2, round(2.4 * z)))
    for lx, ly, a in o._leaves:
        pygame.draw.polygon(s, (130, 200, 120), [(lx + math.cos(a) * 2 * z, ly + math.sin(a) * z), (lx, ly - z), (lx - math.cos(a) * 2 * z, ly - math.sin(a) * z), (lx, ly + z)])
    eyes(s, x, y, 2 * z, z, t, o.phase)


def glow_breeze(o, s, t, st, k):
    glow(s, o.x, o.y, int((4 + 3 * stage(o)) * o.size), o.color, q(20 + 60 * k))


def draw_dew(o, s, t):
    """Dewlet: a bead of dew riding a leaf through the air like a little boat. Dewglimmer: the bead
    bigger, two leaves for sails. Dewcascade: a ring of dewdrops spilling round and round, a
    fountain with no basin."""
    z, x, y, f, n = o.size, o.x, o.y, o.facing, stage(o)
    if n < 3:
        leaves = 1 if n == 1 else 2
        for j in range(leaves):
            if n == 1:
                pts = [(x - 6 * z, y + 2 * z), (x, y + 4 * z), (x + 6 * z, y + 1 * z), (x, y + 2.4 * z)]
            else:
                side = -1 if j == 0 else 1
                pts = [(x, y + z), (x + side * 7 * z, y - 4 * z + math.sin(t * 3) * z), (x + side * 3 * z, y - 7 * z)]
            pygame.draw.polygon(s, (110, 190, 130), pts)
            pygame.draw.line(s, (80, 150, 100), pts[0], pts[2])
        R = (3 if n == 1 else 4.5) * z
        pygame.draw.circle(s, mix(o.body, (100, 160, 200), 0.3), (round(x), round(y - R * 0.3)), round(R))
        pygame.draw.circle(s, WHITE, (round(x - R * 0.35), round(y - R * 0.7)), max(1, round(R * 0.25)))
        eyes(s, x, y - R * 0.2, 2 * z, z, t, o.phase)
        o._drops = [(x, y - R * 0.3)]
        return
    o._drops = []
    for j in range(10):
        a = j / 10 * TAU + t * 1.4
        px, py = x + math.cos(a) * 9 * z, y + math.sin(a) * 9 * z
        r = (1.6 + (j % 3) * 0.4) * z
        pygame.draw.circle(s, mix(o.body, (100, 160, 200), 0.3), (round(px), round(py)), max(1, round(r)))
        s.set_at((round(px - r * 0.3), round(py - r * 0.3)), WHITE)
        o._drops.append((px, py))
    pygame.draw.circle(s, mix(o.body, (100, 160, 200), 0.2), (round(x), round(y)), max(2, round(4 * z)))
    eyes(s, x, y, 2 * z, z, t, o.phase)


def glow_dew(o, s, t, st, k):
    z = o.size
    for i, (px, py) in enumerate(getattr(o, "_drops", [])):
        glow(s, px, py, int(3 * z), o.color, q(50 + 30 * math.sin(t * 2 + i) + 40 * k))


# ===================================== the legendaries ========================================

def draw_elder(o, s, t):
    """Elderglow: a great wreath of ancient living roots, drifting over the Glade. Blossoms open
    and close around the ring, root-tassels trail beneath it, and a seed of light hangs at its
    heart."""
    z, x, y = o.size, o.x, o.y
    R = 10 * z
    turn = t * 0.15
    for j in range(7):  # tassels of root hanging below
        a = math.pi * (0.2 + 0.6 * j / 6)
        bx, by = x + math.cos(a) * R, y + math.sin(a) * R * 0.5
        pts = [(bx + math.sin(t * 1.3 + j + i * 0.7) * z, by + i * 3 * z) for i in range(3 + j % 3)]
        pygame.draw.lines(s, dark(o.body, 0.2), False, pts)
    for strand in range(3):  # the ring: three roots braided round it
        pts = []
        for i in range(41):
            a = i / 40 * TAU
            off = math.sin(a * 5 + strand * TAU / 3 + turn * 4) * 1.4 * z
            pts.append((x + math.cos(a) * (R + off), y + math.sin(a) * (R + off) * 0.5))
        pygame.draw.lines(s, mix(o.body, WHITE, 0.08 * strand), False, pts, max(1, round(1.4 * z)))
    o._blooms = []
    for j in range(6):
        a = turn + j / 6 * TAU
        bx, by = x + math.cos(a) * R, y + math.sin(a) * R * 0.5
        open_ = 0.5 + 0.5 * math.sin(t * 0.8 + j * 1.1)
        for p in range(5):
            pa = p / 5 * TAU + a
            pygame.draw.circle(s, (255, 196, 226) if j % 2 else (255, 236, 200),
                               (round(bx + math.cos(pa) * open_ * 1.8 * z), round(by + math.sin(pa) * open_ * 1.4 * z)), max(1, round(1.1 * z)))
        o._blooms.append((bx, by))
    pygame.draw.line(s, dark(o.body, 0.2), (x, y - R * 0.5), (x, y - 1.5 * z))  # the seed's stem


def glow_elder(o, s, t, st, k):
    z, x, y = o.size, o.x, o.y
    b = 0.7 + 0.3 * math.sin(t * 1.2 + o.phase)
    glow(s, x, y, int(20 * z), o.color, q(70 * b + 50 * k))
    pygame.draw.ellipse(s, (255, 246, 210), (x - 1.6 * z, y - 2.4 * z, 3.2 * z, 4.4 * z))
    for side in (-1, 1):
        s.set_at((round(x + side * 0.6 * z), round(y - 0.5 * z)), INK)
    for bx, by in getattr(o, "_blooms", []):
        glow(s, bx, by, int(3 * z), (255, 210, 230), q(60))


def draw_moonw(o, s, t):
    """Moonward: a crescent of night-glass, a single great eye watching from its hollow, and seven
    small moons, each in its own phase, wheeling slowly round it."""
    z, x, y, f = o.size, o.x, o.y, o.facing
    R = 10 * z
    tilt = math.sin(t * 0.5 + o.phase) * 0.2
    outer = [(x + math.cos(a / 20 * math.pi * 1.5 + math.pi * 0.25 + tilt) * R * -f, y + math.sin(a / 20 * math.pi * 1.5 + math.pi * 0.25 + tilt) * R)
             for a in range(21)]
    inner = [(x + math.cos(a / 20 * math.pi * 1.5 + math.pi * 0.25 + tilt) * R * 0.6 * -f + f * R * 0.35,
              y + math.sin(a / 20 * math.pi * 1.5 + math.pi * 0.25 + tilt) * R * 0.6) for a in range(20, -1, -1)]
    poly(s, o.body, outer + inner, rim=lite(o.body, 0.5))
    for i in range(0, 21, 3):  # stars caught in the glass
        px, py = outer[i]
        s.set_at((round(px + f * 1.5 * z), round(py * 0.85 + y * 0.15)), (255, 250, 220))
    o._eye = (x + f * R * 0.15, y)
    o._moons = []
    for j in range(7):
        a = t * 0.25 + j / 7 * TAU
        o._moons.append((x + math.cos(a) * R * 1.7, y + math.sin(a) * R * 0.6, j / 7))


def glow_moonw(o, s, t, st, k):
    z = o.size
    ex, ey = getattr(o, "_eye", (o.x, o.y))
    glow(s, ex, ey, int(16 * z), o.color, q(70 + 50 * k))
    pygame.draw.ellipse(s, (240, 240, 255), (ex - 3 * z, ey - 2 * z, 6 * z, 4 * z))
    look = math.sin(t * 0.7 + o.phase) * 1.2 * z
    pygame.draw.circle(s, (90, 80, 200), (round(ex + look), round(ey)), max(1, round(1.6 * z)))
    s.set_at((round(ex + look), round(ey)), INK)
    for mx, my, phase in getattr(o, "_moons", []):  # each little moon in its own phase
        r = max(1, round(1.8 * z))
        pygame.draw.circle(s, (255, 244, 210), (round(mx), round(my)), r)
        shade = (phase - 0.5) * 2 * r * 2
        pygame.draw.circle(s, (30, 30, 70), (round(mx + shade), round(my)), r)
        glow(s, mx, my, int(3 * z), (255, 240, 200), q(50))


for _kind, (_sp, _flies, *_rest) in KINDS.items():
    cls = Flier if _flies else Walker
    setattr(cls, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(cls, "glow_" + _kind, globals()["glow_" + _kind])


import wave6  # noqa: E402,F401  (page six: lines #259-#288)
