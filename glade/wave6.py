"""The Forest Dex's page six (2026-10-27, his ask): the Dex grows to 400 and ten new three-stage
lines (#259-#288) come in, one for each place, mostly of the types there were fewest of
(Electric, Poison, Dark, Fighting). Dragon, Ghost and Steel stay rare, one line each.

Same rules as wave5.py: no humanoids, no two lines sharing a body, each kind its own
`draw_<kind>` (all three stages) and `glow_<kind>` (its lights). They join wave5's HOMES, so
the places (scenes.py, lower.py) pick them up with the rest.
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, LIT, WALKERS, Flier, Walker
from life import q
from wave5 import HOMES, KINDS as _OLD, TAU, WHITE, dark, eyes, hop, lite, moving, poly, shaded, stage

# kind: (first stage's species, flies?, body, glow, speed)
KINDS = {
    "burr": ("Burrlet", False, (70, 56, 74), (190, 120, 255), 8),
    "zing": ("Zingle", True, (200, 190, 110), (255, 250, 140), 60),
    "mire": ("Mirelet", True, (120, 170, 110), (170, 255, 120), 10),
    "smudge": ("Smudgit", False, (34, 30, 52), (150, 140, 255), 7),
    "stump": ("Stumplet", False, (120, 90, 70), (190, 255, 160), 6),
    "fizz": ("Fizzlet", False, (190, 150, 110), (150, 230, 255), 16),
    "fume": ("Fumelet", False, (80, 74, 96), (220, 130, 255), 5),
    "bulb": ("Bulblet", False, (180, 186, 200), (255, 236, 150), 10),
    "delve": ("Delvelet", False, (150, 112, 86), (255, 190, 120), 9),
    "pom": ("Pomlet", False, (240, 186, 210), (255, 210, 240), 14),
}
NEW_HOMES = {
    "glade": ("burr",), "waterfall": ("zing",), "river": ("mire",), "forest": ("smudge",), "rocks": ("stump",),
    "ridge": ("fizz",), "springs": ("fume",), "tower": ("bulb",), "caverns": ("delve",), "meadow": ("pom",),
}

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


def spikes(s, color, cx, cy, r, k, length, turn=0.0):
    for j in range(k):
        a = turn + j * TAU / k
        tip = (cx + math.cos(a) * (r + length), cy + math.sin(a) * (r + length))
        side = 0.35 / max(1, r / 3)
        poly(s, color, [(cx + math.cos(a - side) * r, cy + math.sin(a - side) * r), tip,
                        (cx + math.cos(a + side) * r, cy + math.sin(a + side) * r)])


# ===================================== the Glade ==============================================

def draw_burr(o, s, t):
    """Burrlet: a spiky seed-burr that rolls along on its hooks. Burrclasp: bigger, its hooks
    curling like little hands. Burrthorn: a ball of black bramble, thorns all round, rolling."""
    z, x, n = o.size, o.x, stage(o)
    r = (3 + 1.6 * n) * z
    cy = o.y - r - (n == 1) * hop(o, t, 1.5)
    turn = o.x * 0.12 * o.facing
    spikes(s, dark(o.body, 0.2) if n < 3 else (40, 30, 46), x, cy, r * 0.9, 6 + 3 * n, (2 + n * 0.6) * z, turn)
    pygame.draw.circle(s, o.body, (round(x), round(cy)), round(r))
    if n >= 2:  # the hooks, curled
        for j in range(6 if n == 2 else 9):
            a = turn + 0.3 + j * TAU / (6 if n == 2 else 9)
            hx, hy = x + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.35
            pygame.draw.arc(s, lite(o.body, 0.25), (hx - 1.5 * z, hy - 1.5 * z, 3 * z, 3 * z), a, a + 3.5)
    if n == 3:  # bramble strands wound round it
        for j in range(3):
            a0 = turn + j * 2.1
            pts = [(x + math.cos(a0 + i * 0.5) * r * (0.5 + 0.1 * i), cy + math.sin(a0 + i * 0.5) * r * 0.6) for i in range(6)]
            pygame.draw.lines(s, (96, 70, 104), False, pts, max(1, round(z * 0.8)))
    eyes(s, x + o.facing * z, cy - 0.5 * z, 2.6 * z, z, t, o.phase)
    o._heart = (x, cy)


def glow_burr(o, s, t, st, k):
    x, cy = getattr(o, "_heart", (o.x, o.y))
    z, n = o.size, stage(o)
    glow(s, x, cy, int((4 + 2 * n) * z), o.color, q(30 + 15 * n + 60 * k))
    for j in range(n + 1):  # the tips of its thorns catch the light
        a = t * 0.4 + j * TAU / (n + 1)
        r = (3 + 1.6 * n + 2 + n * 0.6) * z
        s.set_at((round(x + math.cos(a) * r), round(cy + math.sin(a) * r)), lite(o.color, 0.5))


# ===================================== the Waterfall ==========================================

def draw_zing(o, s, t):
    """Zingle: a glowing seed-pod on two blurring wings, zig-zagging. Zingwing: longer, with four
    wings. Zingswarm: a humming cloud of little pods that keep together, one bigger at its heart."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    pods = [(0, 0, 1.0)] if n < 3 else [(0, 0, 1.2)] + [
        (math.cos(t * 1.6 + j * TAU / 6 + o.phase) * 9, math.sin(t * 2.3 + j * 1.7) * 5, 0.6) for j in range(6)]
    o._pods = []
    for i, (px, py, sc) in enumerate(pods):
        cx, cy = x + px * z, y + py * z + math.sin(t * 9 + i) * 0.8 * z
        w, h = (3 + (n == 2) * 2) * z * sc, (2.2 + (n == 2) * 0.6) * z * sc
        flap = abs(math.sin(t * 30 + i))
        for side in ((-1, 1) if n == 1 or sc < 1 else (-1, -0.5, 0.5, 1)):
            wx = cx + side * w * 0.3
            pygame.draw.ellipse(s, mix(o.body, WHITE, 0.6), (wx - 1.5 * z * sc, cy - h - 3 * z * sc * flap, 3 * z * sc, 3 * z * sc * flap + 1))
        shaded(s, o.body, (cx - w, cy - h * 0.5, 2 * w, h))
        pygame.draw.line(s, dark(o.body, 0.3), (cx - w * 0.2, cy - h * 0.4), (cx - w * 0.2, cy + h * 0.4))
        if i == 0:
            eyes(s, cx + o.facing * w * 0.4, cy - 0.2 * z, 1.8 * z, z, t, o.phase)
        o._pods.append((cx - o.facing * w * 0.7, cy))


def glow_zing(o, s, t, st, k):
    z = o.size
    for i, (cx, cy) in enumerate(getattr(o, "_pods", [])):
        glow(s, cx, cy, int(4 * z), o.color, q(70 + 40 * math.sin(t * 7 + i) + 60 * k))
        s.set_at((round(cx), round(cy)), WHITE)
    if stage(o) >= 2 and int(t * 6 + o.phase) % 4 == 0:  # a little spark jumps off it
        a = (t * 13) % TAU
        sx, sy = o.x + math.cos(a) * 7 * z, o.y + math.sin(a) * 5 * z
        pygame.draw.lines(s, (255, 255, 200), False, [(o.x, o.y), ((o.x + sx) / 2 + z, (o.y + sy) / 2 - z), (sx, sy)])


# ===================================== the River ==============================================

def draw_mire(o, s, t):
    """Mirelet: a wisp of glowing marsh gas with two dim eyes. Mirelamp: the wisp holds itself in
    the shape of a hanging lamp. Mirelantern: a tall green flame of gas with wisps curling off it
    and a faint, swinging ring of lights round it."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    h, w = (5 + 3 * n) * z, (3 + 1.2 * n) * z
    pts = []
    for i in range(13):  # its flame-shaped body, wavering
        a = i / 12 * TAU
        r = 1 + 0.12 * math.sin(t * 4 + i * 1.3 + o.phase)
        up = math.cos(a) < 0  # the top half narrows into a point
        px = x + math.sin(a) * w * r * ((1 + math.cos(a)) ** 1.5 if up else 1)
        py = y + (math.cos(a) * h * 0.5 if not up else math.cos(a) * h * (0.9 + 0.1 * math.sin(t * 3)))
        pts.append((px + math.sin(t * 2.5 + o.phase) * z * max(0, -math.cos(a)) * 2, py))
    body = mix(o.body, (20, 30, 30), 0.45)
    pygame.draw.polygon(s, body, pts)
    pygame.draw.lines(s, lite(o.body, 0.2), True, pts)
    if n >= 2:  # a lamp's cap and hoop
        pygame.draw.line(s, (90, 96, 80), (x - w * 0.6, y - h * 0.75), (x + w * 0.6, y - h * 0.75), max(1, round(z)))
        pygame.draw.arc(s, (90, 96, 80), (x - 2 * z, y - h - 2 * z, 4 * z, 4 * z), 0, math.pi)
    for j in range(n):  # trailing wisps
        kk = (t * 0.4 + j / max(1, n) + o.phase) % 1
        pygame.draw.circle(s, mix(o.body, (20, 30, 30), 0.3 + 0.6 * kk), (round(x - o.facing * (w + kk * 8 * z)), round(y + h * 0.3 - kk * 5 * z)),
                           max(1, round((1.6 - kk) * z)))
    eyes(s, x, y, 2.4 * z, z, t, o.phase)
    o._core = (x, y + z)


def glow_mire(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, y = getattr(o, "_core", (o.x, o.y))
    b = 0.7 + 0.3 * math.sin(t * 2.2 + o.phase)
    glow(s, x, y, int((6 + 3 * n) * z), o.color, q(70 * b + 60 * k))
    if n == 3:
        for j in range(5):
            a = t * 0.7 + j * TAU / 5
            gx, gy = x + math.cos(a) * 11 * z, y + math.sin(a) * 3 * z + 2 * z
            glow(s, gx, gy, int(3 * z), o.color, q(70))
            s.set_at((round(gx), round(gy)), (220, 255, 200))


# ===================================== the Forest =============================================

def draw_smudge(o, s, t):
    """Smudgit: a drop of ink with eyes, oozing along and leaving smudges. Smudgeon: a flat
    puddle of ink that rises into a hump to look about. Smudgemire: a pool of ink with a tall
    curling crest, drips falling from it, the smudges behind it slowly fading."""
    z, x, y, n = o.size, o.x, o.y, stage(o)
    trail = getattr(o, "_trail", [])
    if moving(o) and (not trail or abs(trail[-1][0] - x) > 4 * z):
        trail = (trail + [(x, y, t)])[-6:]
    o._trail = trail
    for tx, ty, born in trail:  # the smudges it leaves
        fade = min(1, (t - born) / 3)
        if fade < 1:
            pygame.draw.ellipse(s, mix(o.body, (60, 60, 80), fade * 0.8), (tx - 2 * z, ty - 0.6 * z, 4 * z, 1.4 * z))
    squash = 1 + 0.1 * math.sin(o.step * 2 if moving(o) else t * 1.5)
    w, h = (4 + 2.5 * n) * z * squash, (4 + 2 * n) * z / squash
    pts = [(x + math.cos(a / 16 * math.pi) * w * (1.1 if a in (0, 16) else 1),
            y - math.sin(a / 16 * math.pi) ** 0.8 * h + math.sin(t * 2 + a) * 0.3 * z) for a in range(17)]
    if n == 3:  # its crest curls over
        pts[8] = (x + o.facing * 4 * z, y - h - 5 * z + math.sin(t * 1.4) * z)
    poly(s, o.body, pts, rim=(84, 76, 130))
    pygame.draw.line(s, (90, 86, 140), (x - w * 0.4, y - h * 0.7), (x - w * 0.1, y - h * 0.85))  # a sheen
    if n >= 2:
        for j in range(n):  # drips
            dx = x + (j - (n - 1) / 2) * w * 0.6
            ln = (1 + (t * 1.3 + j * 0.7) % 2.5) * z
            pygame.draw.line(s, o.body, (dx, y - h * 0.4), (dx, y - h * 0.4 + ln))
    eyes(s, x + o.facing * w * 0.25, y - h * 0.6, 2.6 * z, z, t, o.phase)
    o._eye = (x + o.facing * w * 0.25, y - h * 0.6)


def glow_smudge(o, s, t, st, k):
    z = o.size
    ex, ey = getattr(o, "_eye", (o.x, o.y))
    glow(s, ex, ey, int((3 + stage(o)) * z), o.color, q(40 + 60 * k))
    for side in (-1.3, 1.3):  # just its eyes shine, like a cat's in the dark
        s.set_at((round(ex + side * z), round(ey)), lite(o.color, 0.4))


# ===================================== the Mossy Rocks ========================================

def draw_stump(o, s, t):
    """Stumplet: a little tree-stump on root-feet, stomping. Stumpstomp: taller, with two stout
    branch-arms and moss on its top. Stumpquake: a great old stump, rings showing on its top, a
    sapling growing from it, that shakes the ground (dust and moss jump) when it stamps."""
    z, x, n = o.size, o.x, stage(o)
    stomp = abs(math.sin(o.step * 0.9)) if moving(o) else 0
    y = o.y
    w, h = (4 + 1.5 * n) * z, (5 + 3 * n) * z
    lift = stomp * (1.5 + n * 0.5) * z
    for side in (-1, 1):  # root feet, stepping in turn
        up = lift if (side > 0) == (math.sin(o.step * 1.8) > 0) else 0
        pygame.draw.line(s, dark(o.body, 0.2), (x + side * w * 0.5, y - h * 0.2), (x + side * w * 1.1, y - up), max(1, round(1.4 * z)))
    rect = pygame.Rect(0, 0, round(2 * w), round(h))
    rect.midbottom = (round(x), round(y - 1.5 * z))
    pygame.draw.rect(s, dark(o.body, 0.3), rect.move(1, 0), border_radius=round(z))
    pygame.draw.rect(s, o.body, rect, border_radius=round(z))
    for j in range(2 + n):  # bark grooves
        gx = rect.x + (j + 0.5) * rect.w / (2 + n)
        pygame.draw.line(s, dark(o.body, 0.2), (gx, rect.y + 2 * z), (gx + z * 0.5, rect.bottom - z))
    top = pygame.Rect(rect.x, rect.y - 1.5 * z, rect.w, 3 * z)
    pygame.draw.ellipse(s, (200, 170, 120), top)  # the cut top, its rings
    if n == 3:
        for r in (0.6, 0.3):
            pygame.draw.ellipse(s, (160, 126, 90), top.inflate(-top.w * (1 - r), -top.h * (1 - r)), 1)
        pygame.draw.line(s, (100, 170, 90), (x, top.y), (x + z, top.y - 6 * z))  # its sapling
        pygame.draw.circle(s, (120, 200, 110), (round(x + z), round(top.y - 6 * z)), round(1.6 * z))
    if n >= 2:
        pygame.draw.ellipse(s, (90, 150, 80), (top.x - z, top.y - z * 0.5, top.w * 0.6, 2 * z))  # moss
        for side in (-1, 1):  # branch arms
            ay = rect.y + h * 0.35
            pygame.draw.line(s, o.body, (x + side * w, ay), (x + side * (w + 3 * z), ay - 2 * z + stomp * z), max(1, round(1.4 * z)))
    eyes(s, x + o.facing * z, rect.y + h * 0.35, 3 * z, z, t, o.phase)
    o._feet = (x, y, stomp)


def glow_stump(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, y, stomp = getattr(o, "_feet", (o.x, o.y, 0))
    glow(s, x, y - (6 + 3 * n) * z, int((4 + 2 * n) * z), o.color, q(25 + 50 * k))
    if stomp > 0.9:  # dust and moss jump when it stamps
        for j in range(2 + 2 * n):
            dx = (j - (1 + n)) * 2.4 * z
            s.set_at((round(x + dx), round(y - (1 + j % 3) * z)), (170, 220, 140) if j % 2 else (200, 186, 160))


# ===================================== the Snowy Ridge ========================================

def draw_fizz(o, s, t):
    """Fizzlet: a coil of copper wire that boings along on its spring, a spark on its top.
    Fizzcoil: a taller coil with a ball on top that fizzes. Fizzdynamo: a tower of three coils
    stacked on a base, arcs of lightning jumping between their tops."""
    z, x, n = o.size, o.x, stage(o)
    y = o.y - hop(o, t, 2.5 if n == 1 else 1.0, 1.6)
    turns = 3 + 2 * n
    tall = (6 + 4 * n) * z
    stacks = [0] if n < 3 else [-6, 0, 6]
    o._tops = []
    if n == 3:
        pygame.draw.rect(s, (90, 90, 110), (x - 10 * z, o.y - 3 * z, 20 * z, 3 * z), border_radius=round(z))
        y = o.y - 3 * z
    for i, dx in enumerate(stacks):
        cx = x + dx * z
        ht = tall * (1.15 if dx == 0 and n == 3 else 0.8 if n == 3 else 1)
        pts = []
        for j in range(turns * 8 + 1):
            a = j / 8 * TAU + t * 3 * (n == 3)
            pts.append((cx + math.cos(a) * (2 + 0.3 * n) * z, y - j / (turns * 8) * ht + math.sin(a) * 0.6 * z))
        pygame.draw.lines(s, dark(o.body, 0.2), False, [(px + 1, py) for px, py in pts], max(1, round(z * 0.8)))
        pygame.draw.lines(s, o.body, False, pts, max(1, round(z * 0.8)))
        top = (cx, y - ht - 1.5 * z)
        pygame.draw.circle(s, (210, 214, 230), (round(top[0]), round(top[1])), max(1, round((1.2 + 0.5 * n) * z)))
        o._tops.append(top)
    eyes(s, x, y - tall * 0.45, 2.6 * z, z, t, o.phase)


def glow_fizz(o, s, t, st, k):
    z, n = o.size, stage(o)
    tops = getattr(o, "_tops", [])
    for i, (tx, ty) in enumerate(tops):
        glow(s, tx, ty, int((4 + 2 * n) * z), o.color, q(80 + 50 * math.sin(t * 11 + i * 2) + 60 * k))
        s.set_at((round(tx), round(ty)), WHITE)
    if n == 3 and int(t * 5 + o.phase) % 3 != 0:  # lightning jumping between its tops
        for (ax, ay), (bx, by) in zip(tops, tops[1:]):
            mid = ((ax + bx) / 2 + math.sin(t * 40) * z, (ay + by) / 2 - 2 * z + math.cos(t * 37) * 2 * z)
            pygame.draw.lines(s, (220, 245, 255), False, [(ax, ay), mid, (bx, by)])
    elif n < 3 and int(t * 4 + o.phase) % 5 == 0:
        tx, ty = tops[0] if tops else (o.x, o.y)
        pygame.draw.lines(s, (220, 245, 255), False, [(tx, ty), (tx + 2 * z, ty - 2 * z), (tx + z, ty - 4 * z)])


# ===================================== the Hot Springs ========================================

def draw_fume(o, s, t):
    """Fumelet: a tiny iron pot on three stubby legs, bubbling. Fumepot: a round pot that
    waddles, a ladle sticking out of it that stirs by itself. Fumecauldron: a great cauldron,
    simmering over a bed of glowing coals that it carries along beneath it."""
    z, x, n = o.size, o.x, stage(o)
    wad = math.sin(o.step * 1.5) * 0.12 if moving(o) else 0
    w, h = (3.5 + 2 * n) * z, (3 + 2 * n) * z
    leg = (1.5 + 0.5 * n) * z
    y = o.y - leg
    for j in (-1, 0, 1):  # stubby legs
        pygame.draw.line(s, dark(o.body, 0.3), (x + j * w * 0.6, y), (x + j * w * 0.7, o.y), max(1, round(z)))
    if n == 3:
        for j in range(5):  # its coals
            pygame.draw.circle(s, (120, 50, 40), (round(x + (j - 2) * 2 * z), round(o.y - 0.6 * z)), max(1, round(z)))
    rim = y - h
    pts = [(x - w * 0.8, rim), (x + w * 0.8, rim)]
    pts += [(x + math.cos(a / 8 * math.pi) * w, y - h * 0.5 + math.sin(a / 8 * math.pi) * h * 0.55) for a in range(9)]
    pts = [(px + (py - y) * wad, py) for px, py in pts]
    poly(s, o.body, pts, rim=lite(o.body, 0.2))
    pygame.draw.ellipse(s, (60, 40, 70), (x - w * 0.8, rim - 1.2 * z, w * 1.6, 2.4 * z))  # the brew
    pygame.draw.line(s, lite(o.body, 0.35), (x - w, rim - 0.2 * z), (x + w, rim - 0.2 * z), max(1, round(z)))
    if n >= 2:  # the ladle, stirring by itself
        a = t * 1.8 + o.phase
        lx = x + math.cos(a) * w * 0.4
        pygame.draw.line(s, (170, 150, 120), (lx, rim), (lx + 2 * z * math.cos(a), rim - (4 + n) * z), max(1, round(z)))
    eyes(s, x + o.facing * z, y - h * 0.45, 2.8 * z, z, t, o.phase)
    o._brew = (x, rim)


def glow_fume(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, rim = getattr(o, "_brew", (o.x, o.y))
    glow(s, x, rim, int((4 + 2 * n) * z), o.color, q(60 + 60 * k))
    for j in range(2 + n):  # bubbles rising into purple fumes
        kk = (t * 0.5 + j / (2 + n) + o.phase) % 1
        bx = x + math.sin(kk * 6 + j) * (2 + 3 * kk) * z
        by = rim - kk * (8 + 4 * n) * z
        r = max(1, round((0.8 + 2 * kk) * z))
        c = mix((230, 170, 255), (60, 40, 80), kk)
        pygame.draw.circle(s, c, (round(bx), round(by)), r, 1 if kk > 0.3 else 0)
    if n == 3:
        glow(s, x, o.y - z, int(7 * z), (255, 130, 70), q(80 + 30 * math.sin(t * 3)))


# ===================================== the Battle Tower =======================================

def draw_bulb(o, s, t):
    """Bulblet: a little light-bulb that hops on its metal screw. Bulbflare: a bigger bulb with a
    metal cage over it and two short spring-arms that spar. Bulbbeacon: a lighthouse lamp of
    steel and glass, its beam turning slowly round."""
    z, x, n = o.size, o.x, stage(o)
    y = o.y - hop(o, t, 3 if n == 1 else 1.2, 1.4)
    sw, sh = (2 + 0.8 * n) * z, (2.5 + n) * z
    if n == 3:  # a base of riveted steel
        pygame.draw.rect(s, dark(o.body, 0.2), (x - 6 * z, o.y - 5 * z, 12 * z, 5 * z), border_radius=round(z))
        for rx in (-4, 0, 4):
            s.set_at((round(x + rx * z), round(o.y - 2.5 * z)), lite(o.body, 0.5))
        y = o.y - 5 * z
    screw = pygame.Rect(0, 0, round(2 * sw), round(sh))
    screw.midbottom = (round(x), round(y))
    pygame.draw.rect(s, o.body, screw)
    for j in range(1, 3 + n):  # its threads
        ty = screw.bottom - j * sh / (3 + n)
        pygame.draw.line(s, dark(o.body, 0.3), (screw.x, ty + z * 0.4), (screw.right, ty - z * 0.4))
    r = (3 + 1.4 * n) * z
    cy = screw.y - r * 0.9
    pygame.draw.circle(s, (250, 246, 220), (round(x), round(cy)), round(r))
    pygame.draw.circle(s, (190, 186, 160), (round(x), round(cy)), round(r), 1)
    pygame.draw.lines(s, (200, 150, 70), False, [(x - z, screw.y), (x - z * 0.5, cy), (x + z * 0.5, cy), (x + z, screw.y)])  # filament
    if n >= 2:  # a cage of steel bars
        for j in (-0.6, 0, 0.6):
            pygame.draw.line(s, o.body, (x + j * r, screw.y), (x + j * r * 0.5, cy - r))
        pygame.draw.arc(s, o.body, (x - r, cy - r, 2 * r, 2 * r), 0, math.pi, max(1, round(z * 0.8)))
    if n == 2:  # spring-arms that spar
        jab = max(0, math.sin(t * 4 + o.phase)) * 2 * z
        for side in (-1, 1):
            ax = x + side * (sw + 1)
            pts = [(ax + side * (i * 1.2 * z + (jab if side == o.facing else 0) * i / 3), screw.y + (i % 2) * z) for i in range(4)]
            pygame.draw.lines(s, o.body, False, pts)
    eyes(s, x, cy + r * 0.2, 2.6 * z, z, t, o.phase)
    o._lamp = (x, cy, r)


def glow_bulb(o, s, t, st, k):
    z, n = o.size, stage(o)
    x, cy, r = getattr(o, "_lamp", (o.x, o.y, 3 * z))
    flick = 0.85 + 0.15 * math.sin(t * 17 + o.phase) * (1 if n == 1 else 0.3)
    glow(s, x, cy, int(r + (5 + 3 * n) * z), o.color, q((80 + 30 * n) * flick + 60 * k))
    if n == 3:  # its beam, turning
        a = t * 0.8
        for side in (1, -1):
            dx = math.cos(a) * side
            ln = 22 * z * abs(dx)
            for j in range(1, 5):
                glow(s, x + dx / max(abs(dx), 1e-6) * ln * j / 4, cy, int((2 + j) * z), o.color, q(40 * abs(dx)))


# ===================================== the Crystal Caverns ====================================

def draw_delve(o, s, t):
    """Delvelet: a small round dragon on four stubby legs, big shovel claws in front, a blunt
    horn. Delvedrill: bigger, stubby wings folded on its back and a spiralled drill of a horn.
    Delvecrag: a heavy earth dragon crouched low on thick legs, broad rock-caked wings, a row of
    glowing crystal spikes down its back and a club of stone on its tail."""
    z, x, f, n = o.size, o.x, o.facing, stage(o)
    if n == 2:
        return draw_delve2(o, s, t)
    walk = o.step * 1.6 if moving(o) else 0
    bw, bh = (4.5 + 1.6 * n) * z, (4 + 1.8 * n) * z
    leg = (2 + 0.8 * n) * z
    by = o.y - leg - bh * 0.5 + (0 if moving(o) else math.sin(t * 1.5 + o.phase) * 0.3 * z)
    deep, rock = dark(o.body, 0.25), (110, 100, 110)
    # the far legs, then the tail, behind the body
    for j, side in enumerate((-0.55, 0.55)):
        lx = x + side * bw * f
        lift = max(0.0, math.sin(walk + j * math.pi + 0.8)) * 1.5 * z
        pygame.draw.line(s, dark(o.body, 0.45), (lx, by), (lx + f * 0.5 * z, o.y - lift), max(2, round((1.4 + 0.3 * n) * z)))
    tail = [(x - f * bw * (0.7 + i * 0.28), by + bh * 0.15 - i * 0.6 * z + math.sin(t * 2 + i + o.phase) * 0.3 * z * i) for i in range(4)]
    pygame.draw.lines(s, o.body, False, tail, max(2, round((1.8 + 0.4 * n) * z)))
    if n == 3:  # its stone tail-club
        tx, ty = tail[-1]
        pygame.draw.circle(s, rock, (round(tx), round(ty)), round(2.4 * z))
        pygame.draw.circle(s, lite(rock, 0.2), (round(tx - 0.6 * z), round(ty - 0.6 * z)), round(1 * z))
    if n >= 2:  # wings: folded stubs, then broad and caked with rock
        span = (5.5 if n == 2 else 9) * z
        flex = math.sin(t * 1.2 + o.phase) * 0.6 * z
        root = (x + f * bw * 0.15, by - bh * 0.4)
        tip = (root[0] - f * span * 0.35, root[1] - span - flex)
        back = (root[0] - f * span * 1.05, root[1] - span * 0.15)
        mid = (root[0] - f * span * 0.75, root[1] - span * 0.45)  # a scallop between its two fingers
        poly(s, mix(o.body, rock, 0.5) if n == 3 else lite(o.body, 0.1), [root, tip, mid, back], rim=deep)
        if n == 3:
            for i in (0.35, 0.65):
                pygame.draw.line(s, deep, root, (tip[0] + (back[0] - tip[0]) * i, tip[1] + (back[1] - tip[1]) * i))
    shaded(s, o.body, (x - bw, by - bh * 0.5, 2 * bw, bh))
    pygame.draw.ellipse(s, (214, 190, 150), (x - bw * 0.6 + f * bw * 0.15, by, bw * 1.2, bh * 0.45))  # its belly plates
    o._crest = []
    if n == 3:  # crystal spikes down its back
        for i in range(4):
            sx = x + f * bw * (0.45 - i * 0.32)
            sy = by - bh * (0.45 - abs(i - 1.2) * 0.04)
            ln = (3.4 - abs(i - 1) * 0.5) * z
            poly(s, (170, 220, 250), [(sx - z, sy), (sx - f * 0.6 * z, sy - ln), (sx + z, sy)])
            o._crest.append((sx - f * 0.4 * z, sy - ln * 0.6))
    # the near legs, the front pair with shovel claws
    for j, side in enumerate((-0.45, 0.65)):
        lx = x + side * bw * f
        lift = max(0.0, math.sin(walk + j * math.pi)) * 1.6 * z
        fx, fy = lx + f * 0.6 * z, o.y - lift
        pygame.draw.line(s, o.body, (lx, by + bh * 0.2), (fx, fy), max(2, round((1.6 + 0.4 * n) * z)))
        if side > 0:  # the shovel
            poly(s, (226, 214, 190), [(fx - f * 0.6 * z, fy - 1.4 * z), (fx + f * (2.4 + 0.5 * n) * z, fy - 0.2 * z), (fx + f * 0.2 * z, fy + 0.5 * z)])
    # neck and head
    hx, hy = x + f * (bw * 0.95 + 0.8 * n * z), by - bh * 0.55
    pygame.draw.line(s, o.body, (x + f * bw * 0.6, by - bh * 0.1), (hx, hy), max(2, round((2 + 0.5 * n) * z)))
    hr = (2.6 + 0.6 * n) * z
    shaded(s, o.body, (hx - hr, hy - hr * 0.8, 2 * hr, 1.6 * hr))
    pygame.draw.ellipse(s, o.body, (hx + f * hr * 0.3 - hr * 0.6, hy - hr * 0.3, 1.8 * hr, hr))  # its snout
    horn = [(hx + f * hr * 0.2, hy - hr * 0.7), (hx + f * hr * (0.55 + 0.15 * n), hy - hr * (0.95 + 0.25 * n)), (hx + f * hr * 0.8, hy - hr * 0.5)]
    poly(s, (232, 222, 200), horn)
    if n >= 2:  # a drill: spiral grooves
        for i in (0.35, 0.6):
            a, b = horn[0], horn[2]
            px, py = a[0] + (horn[1][0] - a[0]) * i, a[1] + (horn[1][1] - a[1]) * i
            pygame.draw.line(s, (170, 160, 140), (px - z * 0.6, py + z * 0.4), (px + f * z * 0.6, py - z * 0.2))
    if n == 3:  # little back-swept horns too
        pygame.draw.line(s, (232, 222, 200), (hx - f * hr * 0.5, hy - hr * 0.5), (hx - f * hr * 1.4, hy - hr * 1.0), max(1, round(z)))
    eyes(s, hx + f * hr * 0.15, hy - hr * 0.15, 1.2 * z, z, t, o.phase)
    o._crest.append((hx + f * hr * 0.15, hy - hr * 0.15))


def draw_delve2(o, s, t):
    """Delvedrill (redrawn, his ask): crouched low and leaning forward, ready to dig. A wedge of a
    head held low with one smooth horn swept back from its brow, a row of rounded rock plates
    down its back instead of wings, great three-clawed front hands, and a tail ending in a spade."""
    z, x, f, y = o.size, o.x, o.facing, o.y
    walk = o.step * 1.6 if moving(o) else 0
    breathe = 0 if moving(o) else math.sin(t * 1.5 + o.phase) * 0.3 * z
    deep, rock, belly = dark(o.body, 0.3), (122, 108, 112), (214, 190, 150)
    hip = (x - f * 3 * z, y - 7 * z + breathe)
    chest = (x + f * 2.5 * z, y - 6 * z + breathe)

    def leg(px, py, j, near, front):
        lift = max(0.0, math.sin(walk + j * math.pi)) * 1.4 * z
        fx, fy = px + f * (1.2 if front else -0.4) * z, y - lift
        pygame.draw.line(s, o.body if near else dark(o.body, 0.4), (px, py), (fx, fy), max(2, round(2.2 * z)))
        if front and near:  # three big digging claws
            for c in (-1, 0, 1):
                pygame.draw.line(s, (232, 222, 200), (fx, fy), (fx + f * (1.6 + 0.3 * (1 - abs(c))) * z, fy + c * 0.7 * z), max(1, round(0.8 * z)))
        else:
            pygame.draw.line(s, dark(o.body, 0.2), (fx - 0.8 * z, fy), (fx + f * 1.2 * z, fy), max(1, round(z)))

    leg(hip[0] + f * z, hip[1], 1, False, False)  # the far legs
    leg(chest[0] - f * 0.5 * z, chest[1], 0, False, True)
    # its tail, thick at the root and tapering to a spade
    tail = []
    for i in range(6):
        k = i / 5
        tail.append((hip[0] - f * (3 + 9 * k) * z, hip[1] - 0.5 * z + k * k * 5 * z + math.sin(t * 1.8 + o.phase + k * 3) * k * 0.8 * z))
    for i in range(5):
        pygame.draw.line(s, o.body, tail[i], tail[i + 1], max(1, round((3.2 - i * 0.55) * z)))
    tx, ty = tail[-1]
    poly(s, rock, [(tx + f * 0.5 * z, ty - 1.2 * z), (tx - f * 2.6 * z, ty), (tx + f * 0.5 * z, ty + 1.2 * z)], rim=dark(rock, 0.3))
    # body: haunch and chest
    shaded(s, o.body, (hip[0] - 4.5 * z, hip[1] - 3.5 * z, 9 * z, 7 * z))
    shaded(s, o.body, (chest[0] - 4.5 * z, chest[1] - 3.2 * z, 9 * z, 6.4 * z))
    pygame.draw.ellipse(s, belly, (x - 5 * z, y - 5.6 * z + breathe, 10 * z, 2.6 * z))
    # rounded rock plates down its back
    for i in range(4):
        k = i / 3
        px = hip[0] - f * 2 * z + f * k * 8.5 * z
        py = hip[1] - 3.6 * z - math.sin(k * math.pi) * 0.5 * z + k * 0.6 * z
        r = (0.9 + math.sin(k * math.pi) * 0.5) * z
        pygame.draw.circle(s, dark(rock, 0.25), (round(px), round(py + 0.5 * z)), round(r))
        pygame.draw.circle(s, rock, (round(px), round(py)), round(r))
        pygame.draw.arc(s, lite(rock, 0.35), (px - r, py - r, 2 * r, 2 * r), 0.6, 2.5)
    leg(hip[0] - f * 0.5 * z, hip[1] + 1.5 * z, 0, True, False)  # the near legs
    leg(chest[0] + f * 1 * z, chest[1] + 1.5 * z, 1, True, True)
    # head: a low wedge, snout forward
    hx, hy = chest[0] + f * 5 * z, chest[1] - 0.5 * z
    head = [(hx - f * 2.6 * z, hy - 2.2 * z), (hx + f * 1 * z, hy - 2 * z), (hx + f * 3.6 * z, hy - 0.2 * z),
            (hx + f * 3.4 * z, hy + 1 * z), (hx - f * 0.5 * z, hy + 1.8 * z), (hx - f * 2.8 * z, hy + 1 * z)]
    poly(s, o.body, head, rim=deep)
    pygame.draw.line(s, deep, (hx + f * 3.2 * z, hy + 0.5 * z), (hx + f * 0.6 * z, hy + 0.9 * z))  # its mouth
    s.set_at((round(hx + f * 3 * z), round(hy - 0.4 * z)), deep)  # a nostril
    # one smooth horn, swept back from its brow
    horn = [(hx - f * 0.2 * z, hy - 2 * z), (hx - f * 1.5 * z, hy - 5 * z), (hx - f * 3.8 * z, hy - 6 * z),
            (hx - f * 2.2 * z, hy - 4.2 * z), (hx - f * 1.6 * z, hy - 2.1 * z)]
    poly(s, (232, 222, 200), horn, rim=(180, 168, 146))
    eyes(s, hx + f * 0.6 * z, hy - 0.8 * z, 0.1, z, t, o.phase)
    pygame.draw.line(s, deep, (hx - f * 0.4 * z, hy - 2 * z), (hx + f * 1.6 * z, hy - 1.6 * z))  # a heavy brow
    o._crest = [(hx + f * 0.6 * z, hy - 0.8 * z)]


def glow_delve(o, s, t, st, k):
    z, n = o.size, stage(o)
    crest = getattr(o, "_crest", [])
    for i, (cx, cy) in enumerate(crest[:-1]):  # its crystals
        glow(s, cx, cy, int(4 * z), (170, 230, 255), q(70 + 30 * math.sin(t * 2 + i) + 50 * k))
        s.set_at((round(cx), round(cy - z)), WHITE)
    if crest:  # a warm glow about its eyes
        ex, ey = crest[-1]
        glow(s, ex, ey, int((3 + n) * z), o.color, q(35 + 50 * k))


# ===================================== the Starfall Meadow ====================================

def draw_pom(o, s, t):
    """Pomlet: a fluffy pom-pom that bounces everywhere. Pompom: two of them, bouncing in turn.
    Pomparade: a stack of three that bounces along like a little marching column, a ribbon
    streaming from the top one."""
    z, x, n = o.size, o.x, stage(o)
    count = (1, 2, 3)[n - 1]
    colors = (o.body, (200, 220, 255), (255, 236, 170), (200, 255, 210))
    o._poms = []
    base = o.y
    for i in range(count):
        r = (4.5 - 0.4 * i + (n - 1) * 0.6) * z
        b = abs(math.sin(o.step * 1.4 + i * (math.pi / 2 if n == 2 else 0.6))) * (3 if moving(o) else 0.6) * z
        cx = x + (i - (count - 1) / 2) * 6 * z if n == 2 else x + math.sin(t * 2 + i) * 0.6 * z
        cy = (base if n != 3 else base - sum((4.5 - 0.4 * j + 1.2) * 1.5 * z for j in range(i))) - r - b
        c = colors[i % len(colors)]
        for j in range(10):  # its fluff
            a = j * TAU / 10 + i
            pygame.draw.circle(s, dark(c, 0.1), (round(cx + math.cos(a) * r * 0.8), round(cy + math.sin(a) * r * 0.8 + 1)), round(r * 0.4))
        pygame.draw.circle(s, c, (round(cx), round(cy)), round(r * 0.9))
        for j in range(6):
            a = j * TAU / 6 + i + 0.3
            s.set_at((round(cx + math.cos(a) * r * 0.6), round(cy + math.sin(a) * r * 0.6)), lite(c, 0.5))
        if i == 0 or n == 2:
            eyes(s, cx + o.facing * z, cy, 2.6 * z, z, t, o.phase + i)
        o._poms.append((cx, cy, r))
    if n == 3:  # a ribbon from the top one
        tx, ty, r = o._poms[-1]
        pts = [(tx - o.facing * i * 2.5 * z, ty - r + math.sin(t * 6 - i) * z) for i in range(6)]
        pygame.draw.lines(s, (255, 150, 190), False, pts, max(1, round(z)))


def glow_pom(o, s, t, st, k):
    z = o.size
    for i, (cx, cy, r) in enumerate(getattr(o, "_poms", [])):
        glow(s, cx, cy, int(r + 2 * z), o.color, q(30 + 20 * math.sin(t * 2 + i) + 50 * k))


for _kind, (_sp, _flies, *_rest) in KINDS.items():
    cls = Flier if _flies else Walker
    setattr(cls, "draw_" + _kind, globals()["draw_" + _kind])
    setattr(cls, "glow_" + _kind, globals()["glow_" + _kind])
