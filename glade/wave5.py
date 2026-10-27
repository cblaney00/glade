"""The Forest Dex's pages four to six (2026-10-27, his ask): 38 new three-stage lines (#145-#258)
living in the ten older places, and the two legendaries, Elderglow (#259, the Glade) and Moonward
(#260, the Starfall Meadow), which come out only rarely (storm.py).

With so many to draw, each creature is a body plan (`quad`, `biped`, `blob`, `serpent` on the
ground; `bird`, `bug`, `float` in the air) dressed in features (horns, crest, mane, petals,
crystals, flames, ...). A feature has the stage it first appears at, so a line grows into its
later stages the way Pokémon do: same body, more of it. `KINDS` holds them all; `HOMES` says where
each lives (scenes.second_wave and lower.py read it).
"""

import math

import pygame

from art import glow, mix
from beasts import FLIERS, INK, LIT, WALKERS, Flier, Walker
from life import q

WHITE = (255, 255, 255)

# kind: (first stage's species, plan, body, glow, accent, [(feature, from stage)], speed)
KINDS = {
    # the Glade
    "petal": ("Petalpip", "quad", (236, 214, 230), (255, 170, 220), (120, 200, 140), [("petals", 1), ("leaves", 2), ("mane", 3)], 14),
    "lulla": ("Lullabud", "biped", (150, 210, 160), (220, 180, 255), (255, 200, 236), [("petals", 1), ("leaves", 2), ("halo", 3)], 8),
    "wick": ("Gleamwick", "float", (240, 226, 200), (255, 180, 100), (120, 90, 110), [("flame", 1), ("tendrils", 2), ("halo", 3)], 14),
    "hush": ("Hushling", "blob", (210, 206, 240), (180, 170, 255), (110, 100, 160), [("mask", 1), ("frills", 2), ("halo", 3)], 6),
    # the Waterfall
    "splash": ("Splashkin", "biped", (110, 180, 240), (160, 230, 255), (230, 245, 255), [("frills", 1), ("tailorb", 2), ("crest", 3)], 16),
    "mistm": ("Mistmote", "bird", (200, 226, 250), (170, 230, 255), (140, 170, 230), [("crest", 1), ("tailorb", 2), ("frills", 3)], 60),
    "slate": ("Slatelet", "quad", (120, 128, 160), (140, 220, 255), (90, 96, 130), [("shell", 1), ("crest", 2), ("spots", 3)], 6),
    "foam": ("Foamlet", "blob", (220, 240, 255), (180, 220, 255), (160, 200, 240), [("frills", 1), ("spots", 2), ("halo", 3)], 7),
    # the River
    "reed": ("Reedlet", "biped", (120, 170, 120), (200, 255, 170), (190, 160, 110), [("reeds", 1), ("leaves", 2), ("mane", 3)], 18),
    "ripple": ("Ripplet", "quad", (110, 150, 170), (120, 220, 255), (150, 130, 110), [("shell", 1), ("spots", 2), ("leaves", 3)], 5),
    "bubbl": ("Bubblo", "float", (170, 220, 255), (255, 245, 140), (120, 170, 230), [("spots", 1), ("tendrils", 1), ("halo", 3)], 12),
    "silt": ("Siltpaw", "quad", (150, 126, 106), (150, 220, 255), (110, 90, 80), [("ears", 1), ("frills", 2), ("armor", 3)], 16),
    # the Forest
    "bark": ("Barkling", "biped", (140, 100, 110), (170, 255, 170), (100, 190, 120), [("armor", 1), ("leaves", 2), ("antlers", 3)], 9),
    "fern": ("Fernflit", "bird", (130, 200, 140), (200, 255, 190), (90, 160, 110), [("leaves", 1), ("crest", 2), ("tailorb", 3)], 70),
    "hollow": ("Hollowink", "biped", (70, 56, 90), (170, 255, 200), (220, 214, 200), [("mask", 1), ("leaves", 2), ("antlers", 3)], 8),
    "sap": ("Sapsip", "bug", (210, 160, 90), (255, 210, 120), (120, 90, 70), [("spots", 1), ("armor", 2), ("leaves", 3)], 30),
    # the Mossy Rocks
    "rubble": ("Rubblet", "quad", (150, 140, 156), (255, 170, 120), (100, 200, 150), [("crest", 1), ("armor", 2), ("crystals", 3)], 7),
    "quill": ("Quillnip", "quad", (130, 110, 150), (200, 140, 255), (230, 220, 240), [("quills", 1), ("spots", 2), ("armor", 3)], 9),
    "echo": ("Echolet", "bird", (200, 186, 220), (190, 170, 255), (150, 130, 200), [("ears", 1), ("crest", 2), ("halo", 3)], 70),
    "sigil": ("Sigilet", "biped", (140, 136, 176), (140, 255, 240), (100, 200, 150), [("runes", 1), ("armor", 2), ("halo", 3)], 5),
    # the Snowy Ridge
    "snowp": ("Snowpuff", "quad", (240, 244, 255), (170, 230, 255), (190, 200, 240), [("mane", 1), ("horns", 2), ("crystals", 3)], 8),
    "shiver": ("Shiverling", "biped", (180, 210, 240), (160, 230, 255), (220, 240, 255), [("crystals", 1), ("armor", 2), ("horns", 3)], 12),
    "glace": ("Glacelet", "bird", (220, 236, 255), (150, 240, 255), (150, 190, 240), [("crest", 1), ("tailorb", 2), ("crystals", 3)], 80),
    "cone": ("Conelet", "quad", (150, 110, 90), (190, 240, 255), (110, 170, 130), [("quills", 1), ("leaves", 2), ("crystals", 3)], 6),
    # the Hot Springs
    "ash": ("Ashpaw", "quad", (110, 96, 104), (255, 150, 80), (60, 50, 60), [("ears", 1), ("flame", 1), ("mane", 2), ("armor", 3)], 20),
    "sulf": ("Sulfling", "blob", (220, 210, 120), (255, 200, 90), (180, 150, 80), [("spots", 1), ("flame", 2), ("frills", 3)], 5),
    "lava": ("Lavalet", "bird", (90, 70, 80), (255, 140, 70), (255, 200, 110), [("flame", 1), ("crest", 2), ("tailorb", 3)], 80),
    "obsid": ("Obsidling", "biped", (50, 40, 60), (255, 120, 70), (130, 110, 150), [("crest", 1), ("armor", 2), ("horns", 3)], 14),
    # the Battle Tower
    "gong": ("Gongling", "biped", (210, 180, 110), (255, 220, 140), (150, 120, 80), [("armor", 1), ("halo", 2), ("crest", 3)], 9),
    "spire": ("Spirelet", "float", (190, 196, 220), (200, 180, 255), (140, 146, 180), [("crystals", 1), ("runes", 2), ("halo", 3)], 10),
    "duel": ("Dueljab", "biped", (170, 120, 140), (255, 120, 150), (60, 50, 70), [("ears", 1), ("mask", 2), ("crest", 3)], 20),
    # the Crystal Caverns
    "myce": ("Mycelet", "quad", (110, 96, 120), (190, 140, 255), (230, 210, 240), [("mushrooms", 1), ("spots", 2), ("antlers", 3)], 6),
    "deep": ("Deepling", "serpent", (50, 60, 100), (140, 255, 220), (90, 110, 160), [("lure", 1), ("frills", 2), ("spots", 3)], 14),
    "quartz": ("Quartzlet", "quad", (170, 170, 196), (220, 200, 255), (120, 120, 150), [("crystals", 1), ("armor", 2), ("horns", 3)], 6),
    "gem": ("Gemmet", "bug", (130, 120, 170), (150, 255, 230), (200, 180, 255), [("crystals", 1), ("spots", 2), ("halo", 3)], 40),
    # the Starfall Meadow
    "starb": ("Starbud", "biped", (130, 190, 150), (255, 240, 160), (255, 220, 120), [("petals", 1), ("leaves", 2), ("halo", 3)], 10),
    "breeze": ("Breezlet", "bird", (230, 226, 210), (220, 240, 255), (170, 160, 200), [("crest", 1), ("tailorb", 2), ("frills", 3)], 100),
    "dew": ("Dewlet", "float", (180, 240, 230), (170, 255, 220), (120, 200, 160), [("leaves", 1), ("spots", 2), ("tendrils", 3)], 10),
    # the two legendaries: a third stage's worth of features from the start
    "elder": ("Elderglow", "quad", (210, 230, 210), (170, 255, 200), (255, 240, 200), [("antlers", 1), ("mane", 1), ("spots", 1), ("halo", 1), ("leaves", 1)], 10),
    "moonw": ("Moonward", "serpentfly", (120, 120, 210), (220, 220, 255), (255, 240, 190), [("crest", 1), ("frills", 1), ("halo", 1), ("tailorb", 1)], 30),
}
HOMES = {
    "glade": ("petal", "lulla", "wick", "hush"), "waterfall": ("splash", "mistm", "slate", "foam"),
    "river": ("reed", "ripple", "bubbl", "silt"), "forest": ("bark", "fern", "hollow", "sap"),
    "rocks": ("rubble", "quill", "echo", "sigil"), "ridge": ("snowp", "shiver", "glace", "cone"),
    "springs": ("ash", "sulf", "lava", "obsid"), "tower": ("gong", "spire", "duel"),
    "caverns": ("myce", "deep", "quartz", "gem"), "meadow": ("starb", "breeze", "dew"),
}
LEGENDS = {"glade": "elder", "meadow": "moonw"}
FLY_PLANS = ("bird", "bug", "float", "serpentfly")

for _kind, (_sp, _plan, _body, _glow, _acc, _feats, _speed) in KINDS.items():
    spec = dict(species=_sp, body=_body, color=_glow, speed=_speed)
    if _plan in FLY_PLANS:
        FLIERS[_kind] = dict(spec, turn=2.0 if _plan in ("float", "serpentfly") else 1.0)
    else:
        WALKERS[_kind] = spec
    LIT.add(_kind)


def stage(o):
    return 3 if o.kind in LEGENDS.values() else getattr(o, "stage", 1)


def shaded(s, color, rect):
    pygame.draw.ellipse(s, mix(color, INK, 0.35), pygame.Rect(rect).move(0, 1))
    pygame.draw.ellipse(s, color, rect)


# --- body plans: each draws the body and returns where features go ----------------------------
# anchors: head (x, y), top (x, y) above the head, back [(x, y)...] along the top of the body,
# tail (x, y), face (x, y) for a mask, r: the body's size

def plan_quad(o, s, t):
    z, x, y, f = o.size, o.x, o.y, o.facing
    moving = o.wait <= 0
    dark = mix(o.body, INK, 0.4)
    for i, lx in enumerate((-5, -2, 3, 6)):
        lift = max(0.0, math.sin(o.step + i * 1.6)) * 1.5 * z if moving else 0
        pygame.draw.line(s, dark, (x + lx * z, y - 4 * z), (x + lx * z, y - lift), max(1, round(z * 1.2)))
    sway = math.sin(t * 2 + o.phase) * z
    tail = (x - f * 11 * z, y - 9 * z + sway)
    pygame.draw.line(s, o.body, (x - f * 7 * z, y - 7 * z), tail, max(1, round(z * 1.4)))
    shaded(s, o.body, (x - 8 * z, y - 12 * z, 16 * z, 9 * z))
    pygame.draw.ellipse(s, mix(o.body, WHITE, 0.25), (x - 5 * z, y - 11.5 * z, 8 * z, 2.5 * z))
    hx, hy = x + f * 8 * z, y - 12 * z
    pygame.draw.circle(s, mix(o.body, INK, 0.3), (round(hx), round(hy + 1)), max(2, round(3.8 * z)))
    pygame.draw.circle(s, o.body, (round(hx), round(hy)), max(2, round(3.8 * z)))
    pygame.draw.circle(s, mix(o.body, WHITE, 0.15), (round(hx + f * 3 * z), round(hy + z)), max(1, round(1.6 * z)))
    o.eyes(s, hx + f * 0.5 * z - 1 * z, hy - 0.8 * z, 2 * z)
    back = [(x + k * z, y - 12 * z + abs(k) * 0.12 * z) for k in (-5, -2.5, 0, 2.5, 5)]
    return dict(head=(hx, hy), top=(hx, hy - 3.5 * z), back=back, tail=tail, face=(hx + f * z, hy), r=8)


def plan_biped(o, s, t):
    z, x, y, f = o.size, o.x, o.y, o.facing
    moving = o.wait <= 0
    dark = mix(o.body, INK, 0.4)
    for i, lx in enumerate((-2.5, 2.5)):
        lift = max(0.0, math.sin(o.step + i * math.pi)) * 2 * z if moving else 0
        pygame.draw.line(s, dark, (x + lx * z, y - 6 * z), (x + lx * z, y - lift), max(1, round(z * 1.5)))
    shaded(s, o.body, (x - 5 * z, y - 17 * z, 10 * z, 12 * z))
    pygame.draw.ellipse(s, mix(o.body, WHITE, 0.3), (x - 3 * z, y - 13 * z, 6 * z, 6 * z))
    swing = math.sin(o.step) * 1.5 * z if moving else math.sin(t * 1.5 + o.phase) * 0.5 * z
    for side in (-1, 1):  # arms
        pygame.draw.line(s, dark, (x + side * 4.5 * z, y - 14 * z), (x + side * 6.5 * z + swing * side, y - 9 * z), max(1, round(z * 1.2)))
    hx, hy = x + f * 0.5 * z, y - 20 * z
    pygame.draw.circle(s, mix(o.body, INK, 0.3), (round(hx), round(hy + 1)), max(2, round(4.2 * z)))
    pygame.draw.circle(s, o.body, (round(hx), round(hy)), max(2, round(4.2 * z)))
    o.eyes(s, hx - 1.5 * z + f * z, hy - 0.5 * z, 3 * z)
    back = [(x - f * 4 * z, y - 15 * z), (x - f * 4.8 * z, y - 11 * z)]
    return dict(head=(hx, hy), top=(hx, hy - 4 * z), back=back, tail=(x - f * 4 * z, y - 7 * z), face=(hx + f * z, hy), r=6)


def plan_blob(o, s, t):
    z, x, y, f = o.size, o.x, o.y, o.facing
    wob = math.sin(t * 2.5 + o.phase) * 0.8 * z + (math.sin(o.step * 1.3) * z if o.wait <= 0 else 0)
    rect = pygame.Rect(0, 0, round((16 * z + wob)), round(11 * z - wob * 0.6))
    rect.midbottom = (round(x), round(y))
    shaded(s, o.body, rect)
    pygame.draw.ellipse(s, mix(o.body, WHITE, 0.35), (rect.x + rect.w * 0.2, rect.y + 2 * z, rect.w * 0.35, 2.5 * z))
    hx, hy = x + f * 2 * z, y - 6 * z
    o.eyes(s, hx - 1.5 * z, hy, 3 * z)
    back = [(x + k * z, rect.y + abs(k) * 0.35 * z) for k in (-5, -2, 1, 4)]
    return dict(head=(hx, hy), top=(x, rect.y), back=back, tail=(x - f * 7 * z, y - 3 * z), face=(hx + 0.5 * z, hy), r=8)


def plan_serpent(o, s, t):
    z, f, pts = o.size, o.facing, o.tail
    dark = mix(o.body, INK, 0.4)
    radii = [3.4, 3.6, 3.4, 3.1, 2.7, 2.3, 1.9, 1.5, 1.2, 0.9]
    for i, (px, py) in reversed(list(enumerate(pts))):
        wave = math.sin(t * 3 - i * 0.7 + o.phase) * z
        pygame.draw.circle(s, dark, (round(px), round(py - 3 * z + wave + 1)), round(max(1, radii[i] * z)))
        pygame.draw.circle(s, o.body if i % 2 else mix(o.body, WHITE, 0.12), (round(px), round(py - 3 * z + wave)), round(max(1, radii[i] * z)))
    hx, hy = pts[0]
    hx += f * 2.5 * z
    hy -= 4 * z
    shaded(s, o.body, (hx - 4 * z, hy - 3 * z, 8 * z, 6 * z))
    pygame.draw.line(s, INK, (hx + f * z, hy + 1.5 * z), (hx + f * 3.5 * z, hy + z))  # a wide mouth
    ex, ey = round(hx + f * 1.5 * z), round(hy - 1.2 * z)
    pygame.draw.rect(s, (230, 240, 255), (ex - 1, ey - 1, 2, 2))
    s.set_at((ex, ey), INK)
    back = [(px, py - 6 * z) for px, py in pts[1:7:2]]
    return dict(head=(hx, hy), top=(hx, hy - 3 * z), back=back, tail=(pts[-1][0], pts[-1][1] - 3 * z), face=(hx, hy), r=6)


def plan_bird(o, s, t):
    z, x, y, f = o.size, o.x, o.y, o.facing
    flap = math.sin(t * 14 + o.phase)
    dark = mix(o.body, INK, 0.35)
    for side, c in ((-1, dark), (1, mix(o.body, WHITE, 0.15))):
        tip = (x - f * 3 * z + side * 0.5 * z, y - 2 * z - (8 * flap if side > 0 else 6 * flap) * z)
        pygame.draw.polygon(s, c, [(x - f * z, y - z), tip, (x - f * 7 * z, y + z)])
    tail = (x - f * 8 * z, y + 0.5 * z)
    pygame.draw.polygon(s, dark, [(x - f * 4 * z, y), (tail[0], tail[1] - 1.5 * z), (tail[0], tail[1] + 1.5 * z)])
    shaded(s, o.body, (x - 4.5 * z, y - 3.5 * z, 9 * z, 7 * z))
    pygame.draw.polygon(s, o.color, [(x + f * 4 * z, y - z), (x + f * 6.5 * z, y), (x + f * 4 * z, y + z)])
    pygame.draw.rect(s, INK, (round(x + f * 2 * z), round(y - 1.8 * z), max(1, round(z)), max(1, round(z))))
    return dict(head=(x + f * 2 * z, y - 1.5 * z), top=(x + f * 2 * z, y - 3.5 * z), back=[(x - f * z, y - 3.5 * z)],
                tail=tail, face=(x + f * 2.5 * z, y - z), r=4)


def plan_bug(o, s, t):
    z, x, y, f = o.size, o.x, o.y, o.facing
    open_ = 0.4 + 0.6 * abs(math.cos(t * 10 + o.phase))
    for p in range(2):
        w, h = (6 - p * 1.5) * z * open_, (5 - p) * z
        for side in (-1, 1):
            rect = (x + (0 if side > 0 else -w), y - h + p * 2.5 * z, w, h)
            pygame.draw.ellipse(s, mix(o.color, WHITE, 0.55), rect)
            pygame.draw.ellipse(s, o.color, rect, 1)
    shaded(s, o.body, (x - 2 * z, y - 4 * z, 4 * z, 9 * z))
    for side in (-1, 1):
        pygame.draw.line(s, mix(o.body, INK, 0.3), (x, y - 4 * z), (x + side * 2.5 * z, y - 8 * z))
    return dict(head=(x, y - 4 * z), top=(x, y - 7 * z), back=[(x, y - 1 * z), (x, y + 2 * z)], tail=(x, y + 5 * z),
                face=(x, y - 3 * z), r=4)


def plan_float(o, s, t):
    z, x, y = o.size, o.x, o.y
    bob = math.sin(t * 1.8 + o.phase) * z
    y += bob
    shaded(s, o.body, (x - 5 * z, y - 5 * z, 10 * z, 10 * z))
    pygame.draw.ellipse(s, mix(o.body, WHITE, 0.4), (x - 3 * z, y - 4 * z, 3 * z, 2 * z))
    o_eyes(s, x, y, z)
    return dict(head=(x, y), top=(x, y - 5 * z), back=[(x - 3 * z, y - 4 * z), (x + 3 * z, y - 4 * z)], tail=(x, y + 5 * z),
                face=(x, y), r=5)


def plan_serpentfly(o, s, t):
    """Moonward: a long sky-dragon, winding through the air in a ribbon of night."""
    z, x, y, f = o.size, o.x, o.y, o.facing
    pts = []
    for i in range(16):
        px = x - f * (3 + i * 2.6) * z
        py = y + math.sin(t * 2.5 - i * 0.4 + o.phase) * (0.6 + i * 0.1) * z
        pts.append((px, py))
    for i, (px, py) in reversed(list(enumerate(pts))):
        r = max(1, (3.2 - i * 0.15) * z)
        pygame.draw.circle(s, mix(o.body, INK, 0.3), (round(px), round(py + 1)), round(r))
        pygame.draw.circle(s, mix(o.body, (40, 40, 110), i / 18), (round(px), round(py)), round(r))
        if i % 3 == 1:
            s.set_at((round(px), round(py - r * 0.4)), (255, 250, 220))
    shaded(s, o.body, (x - 4 * z, y - 3.5 * z, 9 * z, 7 * z))
    for side in (-1, 1):  # swept horns
        pygame.draw.line(s, (255, 240, 200), (x - f * z, y - 2.5 * z), (x - f * 6 * z, y - (5 + side) * z), max(1, round(z * 0.8)))
    ex, ey = round(x + f * 2 * z), round(y - z)
    pygame.draw.rect(s, (200, 220, 255), (ex - 1, ey - 1, 2, 2))
    o._ribbon = pts
    return dict(head=(x, y), top=(x, y - 4 * z), back=pts[2:12:3], tail=pts[-1], face=(x + f * 2 * z, y), r=6)


def o_eyes(s, x, y, z):
    for side in (-1, 1):
        s.set_at((round(x + side * 1.6 * z), round(y - 0.5 * z)), INK)
        s.set_at((round(x + side * 1.6 * z), round(y + 0.5 * z)), INK)


PLANS = dict(quad=plan_quad, biped=plan_biped, blob=plan_blob, serpent=plan_serpent, bird=plan_bird, bug=plan_bug,
             float=plan_float, serpentfly=plan_serpentfly)


# --- features: drawn over the body; `n` is how far into the line it is (1-3) ---------------------

def f_petals(o, s, t, a, n, c):
    x, y = a["top"]
    z = o.size
    k = 4 + n
    for j in range(k):
        ang = j / k * math.tau + t * 0.2
        pygame.draw.circle(s, c if j % 2 else mix(c, WHITE, 0.4), (round(x + math.cos(ang) * (1.5 + n * 0.6) * z),
                                                                   round(y - 1.5 * z + math.sin(ang) * (1.2 + n * 0.4) * z)),
                           max(1, round((1.2 + 0.3 * n) * z)))
    pygame.draw.circle(s, (255, 236, 140), (round(x), round(y - 1.5 * z)), max(1, round(0.9 * z)))


def f_leaves(o, s, t, a, n, c):
    z = o.size
    for j, (bx, by) in enumerate(a["back"][: 1 + n]):
        sway = math.sin(t * 2 + j) * 0.3
        ang = -math.pi / 2 + (j - n / 2) * 0.5 + sway
        ex, ey = bx + math.cos(ang) * 4 * z, by + math.sin(ang) * 4 * z
        pygame.draw.polygon(s, c, [(bx, by), (bx + math.cos(ang + 0.6) * 2.5 * z, by + math.sin(ang + 0.6) * 2.5 * z), (ex, ey),
                                   (bx + math.cos(ang - 0.6) * 2.5 * z, by + math.sin(ang - 0.6) * 2.5 * z)])


def f_mane(o, s, t, a, n, c):
    x, y = a["head"]
    z = o.size
    f = getattr(o, "facing", 1)
    for j in range(5 + 2 * n):
        ang = math.pi * 0.6 + j / (4 + 2 * n) * math.pi * 1.2
        r = (3 + n) * z
        pygame.draw.circle(s, mix(c, WHITE, 0.2 * (j % 2)), (round(x - f * 2 * z + math.cos(ang) * r * 0.6), round(y + math.sin(ang) * r * 0.5)),
                           max(1, round((1.4 + 0.3 * n) * z)))


def f_horns(o, s, t, a, n, c):
    x, y = a["top"]
    z = o.size
    for side in (-1, 1):
        pygame.draw.line(s, c, (x + side * 1.5 * z, y + z), (x + side * (2 + n) * z, y - (1.5 + 1.5 * n) * z), max(1, round(z * 0.9)))


def f_antlers(o, s, t, a, n, c):
    x, y = a["top"]
    z = o.size
    for side in (-1, 1):
        bx, by = x + side * 1.5 * z, y + z
        tx, ty = bx + side * (2 + n) * z, by - (3 + 2 * n) * z
        pygame.draw.line(s, c, (bx, by), (tx, ty), max(1, round(z * 0.8)))
        for k in range(n):
            mx, my = bx + (tx - bx) * (0.4 + 0.25 * k), by + (ty - by) * (0.4 + 0.25 * k)
            pygame.draw.line(s, c, (mx, my), (mx + side * 2 * z, my - 1.5 * z))
            o._tips.append((mx + side * 2 * z, my - 1.5 * z))
        o._tips.append((tx, ty))


def f_crest(o, s, t, a, n, c):
    z = o.size
    for bx, by in a["back"]:
        h = (1.5 + n) * z
        pygame.draw.polygon(s, c, [(bx - z, by + 0.5 * z), (bx + z, by + 0.5 * z), (bx, by - h)])


def f_quills(o, s, t, a, n, c):
    z = o.size
    f = getattr(o, "facing", 1)
    for j, (bx, by) in enumerate(a["back"]):
        for k in range(n + 1):
            ang = -math.pi / 2 - f * (0.5 + k * 0.25)
            ln = (3 + n + (j + k) % 2) * z
            pygame.draw.line(s, c, (bx, by), (bx + math.cos(ang) * ln, by + math.sin(ang) * ln))


def f_shell(o, s, t, a, n, c):
    bx, by = a["back"][len(a["back"]) // 2]
    z = o.size
    w, h = (7 + n) * z, (3 + n) * z
    rect = pygame.Rect(0, 0, round(2 * w), round(2 * h))
    rect.center = (round(bx), round(by + h * 0.6))
    was = s.get_clip()
    s.set_clip(pygame.Rect(rect.x - 1, rect.y - 1, rect.w + 2, rect.h // 2 + 2).clip(was))
    pygame.draw.ellipse(s, mix(c, INK, 0.3), rect.move(0, 1))
    pygame.draw.ellipse(s, c, rect)
    for j in range(-2, 3):
        pygame.draw.line(s, mix(c, INK, 0.3), (rect.centerx + j * w * 0.35, rect.centery), (rect.centerx + j * w * 0.25, rect.y + 1))
    s.set_clip(was)


def f_crystals(o, s, t, a, n, c):
    z = o.size
    for j, (bx, by) in enumerate(a["back"][: 1 + n]):
        h = (3 + n + (j % 2)) * z
        pygame.draw.polygon(s, mix(c, INK, 0.15), [(bx - 1.3 * z, by), (bx + 1.3 * z, by), (bx + 0.3 * z, by - h)])
        pygame.draw.line(s, mix(c, WHITE, 0.6), (bx, by), (bx + 0.3 * z, by - h))
        o._tips.append((bx + 0.3 * z, by - h * 0.6))


def f_armor(o, s, t, a, n, c):
    z = o.size
    for bx, by in a["back"]:
        pygame.draw.rect(s, c, (bx - 1.6 * z, by - 0.5 * z, 3.2 * z, (1.6 + 0.3 * n) * z), border_radius=max(1, round(z * 0.5)))
        pygame.draw.line(s, mix(c, WHITE, 0.35), (bx - 1.4 * z, by - 0.4 * z), (bx + 1.4 * z, by - 0.4 * z))


def f_frills(o, s, t, a, n, c):
    x, y = a["head"]
    z = o.size
    f = getattr(o, "facing", 1)
    for side in (-1, 1):
        for k in range(1 + n):
            ang = math.pi / 2 - f * math.pi / 2 + side * (0.6 + k * 0.35) + math.sin(t * 2 + k) * 0.1
            ang = -math.pi / 2 + side * (0.9 + k * 0.35) - f * 0.6
            ln = (3 + n - k * 0.5) * z
            pygame.draw.line(s, c, (x - f * z, y), (x - f * z + math.cos(ang) * ln, y + math.sin(ang) * ln), max(1, round(z * 0.8)))


def f_ears(o, s, t, a, n, c):
    x, y = a["top"]
    z = o.size
    for side in (-1, 1):
        pygame.draw.polygon(s, o.body, [(x + side * 0.5 * z, y + z), (x + side * 2.5 * z, y + z), (x + side * 2 * z, y - (3 + n) * z)])
        pygame.draw.line(s, c, (x + side * 1.6 * z, y), (x + side * 1.9 * z, y - (2 + n * 0.8) * z))


def f_mask(o, s, t, a, n, c):
    x, y = a["face"]
    z = o.size
    rect = pygame.Rect(0, 0, round((5 + n) * z), round((3.5 + 0.5 * n) * z))
    rect.center = (round(x), round(y))
    pygame.draw.ellipse(s, c, rect)
    for side in (-1, 1):
        pygame.draw.circle(s, INK, (round(x + side * 1.3 * z), round(y)), max(1, round(0.8 * z)))
    o._tips.append((x - 1.3 * z, y))
    o._tips.append((x + 1.3 * z, y))


def f_reeds(o, s, t, a, n, c):
    z = o.size
    for j, (bx, by) in enumerate(a["back"] * 2):
        sway = math.sin(t * 1.7 + j) * 1.2 * z
        h = (5 + n * 2 + j % 3) * z
        pygame.draw.line(s, c, (bx + j * 0.6 * z, by), (bx + j * 0.6 * z + sway, by - h))
        pygame.draw.ellipse(s, mix(c, (90, 60, 50), 0.5), (bx + j * 0.6 * z + sway - 0.6 * z, by - h - 1.6 * z, 1.4 * z, 2.4 * z))


def f_mushrooms(o, s, t, a, n, c):
    z = o.size
    for j, (bx, by) in enumerate(a["back"][: 1 + n]):
        pygame.draw.line(s, (230, 220, 230), (bx, by), (bx, by - 2 * z))
        pygame.draw.ellipse(s, c, (bx - 1.8 * z, by - 3.4 * z, 3.6 * z, 2 * z))
        o._tips.append((bx, by - 2.6 * z))


def f_lure(o, s, t, a, n, c):
    x, y = a["head"]
    z = o.size
    f = getattr(o, "facing", 1)
    end = (x + f * (3 + n) * z, y - (5 + n) * z + math.sin(t * 2) * z)
    pygame.draw.lines(s, mix(o.body, INK, 0.2), False, [(x, y - 2 * z), (x + f * z, y - (5 + n) * z), end])
    o._tips.append(end)


def f_tendrils(o, s, t, a, n, c):
    x, y = a["tail"]
    z = o.size
    for j in range(2 + n):
        tx = x + (j - (1 + n) / 2) * 2 * z
        pts = [(tx + math.sin(t * 2.4 + j + k * 0.8) * z, y + k * 2.5 * z) for k in range(3 + n)]
        pygame.draw.lines(s, c, False, pts)


SHAPES = dict(petals=f_petals, leaves=f_leaves, mane=f_mane, horns=f_horns, antlers=f_antlers, crest=f_crest,
              quills=f_quills, shell=f_shell, crystals=f_crystals, armor=f_armor, frills=f_frills, ears=f_ears,
              mask=f_mask, reeds=f_reeds, mushrooms=f_mushrooms, lure=f_lure, tendrils=f_tendrils)
# features that are all light: drawn by glow_
LIGHTS = ("spots", "tailorb", "halo", "flame", "runes")


def draw_any(self, s, t):
    _, plan, _, _, acc, feats, _ = KINDS[self.kind]
    n = stage(self)
    self._tips = []
    a = PLANS[plan](self, s, t)
    self._anch = a
    for name, first in feats:
        if n >= first and name in SHAPES:
            SHAPES[name](self, s, t, a, n, acc if name not in ("crystals", "mushrooms") else self.color)


def glow_any(self, s, t, st, k):
    a = getattr(self, "_anch", None)
    if a is None:
        return
    _, plan, _, _, acc, feats, _ = KINDS[self.kind]
    n = stage(self)
    z, c = self.size, self.color
    b = 0.6 + 0.4 * math.sin(t * 2 + self.phase)
    glow(s, a["head"][0], a["head"][1], int((5 + 3 * n) * z), c, q(25 + 15 * n + 60 * k))
    for tx, ty in self._tips:
        glow(s, tx, ty, int(3 * z), c, q(70 * b))
        s.set_at((round(tx), round(ty)), mix(c, WHITE, 0.5))
    for name, first in feats:
        if n < first or name not in LIGHTS:
            continue
        if name == "spots":
            for j, (bx, by) in enumerate(a["back"]):
                bb = 0.5 + 0.5 * math.sin(t * 1.8 + j * 1.3 + self.phase)
                glow(s, bx, by + z, int(3 * z), c, q(60 * bb + 30 * n))
                s.set_at((round(bx), round(by + z)), mix(c, WHITE, 0.5))
        elif name == "tailorb":
            tx, ty = a["tail"]
            glow(s, tx, ty, int((4 + 2 * n) * z), c, q(90 * b + 40 * k))
            pygame.draw.circle(s, mix(c, WHITE, 0.5), (round(tx), round(ty)), max(1, round((1 + 0.4 * n) * z)))
        elif name == "halo":
            x, y = a["top"]
            hy = y - (1.5 + 0.5 * n) * z
            pygame.draw.ellipse(s, mix(c, WHITE, 0.5), (x - (3 + n) * z, hy - 1.2 * z, (6 + 2 * n) * z, 2.4 * z), 1)
            glow(s, x, hy, int((5 + n) * z), c, q(60 * b))
        elif name == "flame":
            pts = a["back"] if plan not in ("float",) else [a["top"]]
            for j, (bx, by) in enumerate(pts):
                h = (2 + n + abs(math.sin(t * 8 + j * 1.7)) * 2) * z
                pygame.draw.polygon(s, (255, 170, 90), [(bx - 1.2 * z, by), (bx + 1.2 * z, by), (bx + math.sin(t * 6 + j) * z, by - h)])
                pygame.draw.line(s, (255, 236, 160), (bx, by), (bx, by - h * 0.5))
                glow(s, bx, by - h * 0.5, int(4 * z), c, q(90))
        elif name == "runes":
            x, y = a["head"][0], (a["head"][1] + a["tail"][1]) / 2
            for j in range(n + 1):
                rx, ry = x + (j - n / 2) * 2.5 * z, y + (j % 2) * 2 * z
                pygame.draw.line(s, c, (rx, ry - 1.2 * z), (rx, ry + 1.2 * z))
                pygame.draw.line(s, c, (rx, ry), (rx + 0.8 * z, ry - 0.8 * z))
            glow(s, x, y, int(6 * z), c, q(50 * b + 30 * n))
    if plan == "serpentfly":  # Moonward: a crescent moon held over its brow
        x, y = a["top"]
        glow(s, x, y - 4 * z, int(10 * z), (255, 240, 190), q(90 + 50 * k))
        pygame.draw.circle(s, (255, 240, 190), (round(x), round(y - 4 * z)), max(2, round(3 * z)))
        pygame.draw.circle(s, (60, 60, 140), (round(x + 1.2 * z), round(y - 4.8 * z)), max(2, round(2.6 * z)))


for _kind, (_sp, _plan, *_rest) in KINDS.items():
    cls = Flier if _plan in FLY_PLANS else Walker
    setattr(cls, "draw_" + _kind, draw_any)
    setattr(cls, "glow_" + _kind, glow_any)
