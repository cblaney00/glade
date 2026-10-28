"""The places in the glade, at night.

Each `build_<place>()` paints one scene back to front and returns a Scene: the
static picture (cached as a few surfaces), the moving things slotted between them,
its light map, and the clickable spots — paths to other places, and objects that
open apps. The moon is up but dim; most of the light comes from things that glow:
moss, mushrooms, crystals, lanterns, fireflies and the little sky-squid.
"""

import math
import random

import pygame

import art
from art import GLOW, H, W, at_depth, glow, mix
from beasts import FLIERS, Flier, Walker
from orchard import Nibbler, Orchard
from storm import newcomer
from squids import Colony
from pond import Shoal, Water
from life import (Aurora, Blades, Critter, Fireflies, GlowThreads, Lantern, Millipede, Motes, Petals, Pulses, River,
                  Shafts, Slug, Snow, Squid, Stars, Steam, Track, Vines, Waterfall, make_rng)


# Where every place lies, on a grid: x grows to the right, y downwards. The Glade is in
# the middle; a path always points the way its place really lies (left only ever goes
# left), and the minimap is this drawn small. The far places lie one step further out,
# reached through the place next to them (LINKS: the paths that join places).
MAP = {
    "glade": (0, 0),
    "waterfall": (0, -1),
    "rocks": (0, 1),
    "forest": (-1, 0),
    "river": (1, 0),
    "ridge": (-2, 0),
    "springs": (2, 0),
    "tower": (0, 2),
    "caverns": (0, -2),
    "meadow": (1, -1),
    "hollow": (-1, 1),
    "bog": (1, 1),
    "ruins": (-1, -1),
    "bridge": (0, -3),
    "shore": (3, 0),
    # fifteen more (2026-10-27, his picks; kit.py, faraway2-4.py)
    "falls": (-2, -1), "peak": (-3, 0), "gully": (-2, 1), "orchard": (-1, 2), "temple": (1, 2),
    "dunes": (2, 1), "lava": (2, -1), "grotto": (4, 0), "kelp": (3, 1), "lighthouse": (3, -1),
    "comet": (1, -2), "garden": (-1, -2), "isles": (0, -4), "storm": (1, -3), "thorn": (-3, 1),
}
LINKS = [("glade", "waterfall"), ("glade", "rocks"), ("glade", "forest"), ("glade", "river"),
         ("forest", "ridge"), ("river", "springs"), ("rocks", "tower"),
         ("waterfall", "caverns"), ("waterfall", "meadow"),
         ("forest", "hollow"), ("river", "bog"), ("forest", "ruins"), ("caverns", "bridge"), ("springs", "shore"),
         ("ridge", "falls"), ("ridge", "peak"), ("hollow", "gully"), ("hollow", "orchard"), ("bog", "temple"),
         ("bog", "dunes"), ("springs", "lava"), ("shore", "grotto"), ("shore", "kelp"), ("shore", "lighthouse"),
         ("meadow", "comet"), ("ruins", "garden"), ("bridge", "isles"), ("bridge", "storm"), ("gully", "thorn")]


def heading(here, there):
    """Which way you walk from one place to another, as (dx, dy) — one of the four arrows."""
    (x0, y0), (x1, y1) = MAP[here], MAP[there]
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)


class Spot:
    """Somewhere you can click: `go` to another place, or `app` to open a program.
    `sign` is where its name board hangs (centre); it is clickable too."""

    def __init__(self, kind, rect, label, target, mark=None, direction=None, sign=None):
        self.kind, self.rect, self.label, self.target = kind, pygame.Rect(rect), label, target
        self.mark = mark or self.rect.center
        self.direction = direction  # which way a path sign points; paths get it from MAP
        self.sign = sign or (self.mark[0], self.mark[1] - 40)
        self.hits = [self.rect]

    def hit(self, p):
        return any(r.collidepoint(p) for r in self.hits)


class Scene(art.Lighting):
    def __init__(self, key, title, pal, rng):
        self.key, self.title, self.pal, self.rng = key, title, pal, rng
        self.parts = []
        self.lives = []
        self.spots = []
        self.critter = None
        self.bugs = []
        self.creatures = []
        art.forget_paths()
        self.cur = art.solid()
        art.gradient(self.cur, (0, 0, W, H), pal["sky"], steps=10)
        self.init_light(pal)

    # building -----------------------------------------------------------------
    def col(self, name, d):
        return at_depth(self.pal, self.pal[name], d)

    def add(self, lay, d, veil=0.0, low=0.0, texture=1.0):
        art.finish(lay, self.pal, d, self.rng, texture)
        self.cur.blit(lay, (0, 0))
        if veil or low:
            self.cur.blit(art.mist_veil(self.pal, veil, low), (0, 0))

    def raw(self, lay):
        self.cur.blit(lay, (0, 0))

    def live(self, thing):
        if hasattr(thing, "draw"):
            self.parts.append(("still", self.cur))
            self.parts.append(("live", thing))
            self.cur = art.plane()
        self.lives.append(thing)
        if hasattr(thing, "poke"):
            self.creatures.append(thing)
        return thing

    def done(self):
        from storm import crowd
        crowd(self, random.Random(sum(map(ord, self.key))))  # twice as many out as there used to be
        roam = getattr(self, "roam", None) or [MEADOW]
        for o in self.lives:  # slugs on the ground wander all over it (not the ones up a tree)
            if type(o).__name__ == "Slug" and o.track.up is None:
                o.roam = roam
        for sp in self.spots:  # every path points the way its place lies on the map
            if sp.kind == "go":
                sp.direction = heading(self.key, sp.target)
        self.parts.append(("still", self.cur))
        self.cur = None
        from spacing import gather
        gather(self)
        parts = []
        for kind, p in self.parts:
            if kind == "still":
                if p.get_flags() & pygame.SRCALPHA:
                    p = art.trimmed(p)
                    if p is None:
                        continue
                else:
                    p = (p, (0, 0))
            parts.append((kind, p))
        self.parts = parts
        return self

    # running ----------------------------------------------------------------------
    def draw(self, s, t):
        for kind, p in self.parts:
            if kind == "still":
                s.blit(*p)
            elif not getattr(p, "gone", False):  # eaten by the apex, for now
                p.draw(s, t)
        self.lit(s, self.lives, t)

    def update(self, dt):
        if self.critter and not getattr(self.critter, "gone", False):
            self.critter.update(dt)


FLY = ("bat", "moth", "drake", "wisp")
MEADOW = (lambda x: 512 + 3 * math.sin(x / 45), (60, 900))  # the near grass, in every place
WALK = ("toad", "mole", "sporeling", "newt", "beetle")


def persp(y):
    """How big something standing at y looks on the upper screen: 1 at the front of the
    meadow (y 512), smaller further back toward the hills."""
    return max(0.6, min(1.05, 0.35 + 0.65 * (y - 200) / 312))  # (the far river bank was a tad small at 0.42)


def second_wave(sc, rng, sky, grounds, fliers=FLY, walkers=WALK, out=(), new=(), far=()):
    """One of every animal of the second wave (beasts.py) lives in every place: the fliers
    in its sky, the walkers on its stretches of ground. They start out sheltering, and a
    thunderstorm (storm.py) brings out a random mix of everyone who lives here. The far
    places have their own animals instead, and the kinds in `out` start out in sight.
    `new`: the place's own kinds from the third wave (2026-10-27), on their own dice so the
    rest of the place is painted just as before; one of each starts out in sight.
    `far`: stretches of ground further back (2026-10-27, his ask: more room for animals),
    each with two walkers of their own that wander only there, drawn smaller (`persp`), and a
    flier or two in the distance above them."""
    for kind in fliers:
        f = sc.live(Flier(rng, sky, kind, 1.1))
        if kind not in out:
            newcomer(f)
    roam = list(grounds) + [MEADOW]  # they wander all over the ground of their place
    sc.roam = roam
    for i, kind in enumerate(walkers):
        ground, x_range = grounds[i % len(grounds)]
        w = sc.live(Walker(rng, ground, x_range, kind, 1.1, roam=roam, persp=persp))
        if kind not in out:
            newcomer(w)
    from wave5 import HOMES, LEGENDS
    new = tuple(new) + HOMES.get(sc.key, ())  # pages four to six of the Forest Dex (wave5.py)
    own = random.Random(sum(map(ord, sc.key)) + 2)
    legend = LEGENDS.get(sc.key)
    if legend:  # a legendary lives here, out only rarely (storm.py), and big
        o = (Flier(own, sky, legend, 2.6) if legend in FLIERS else
             Walker(own, grounds[0][0], grounds[0][1], legend, 2.6, roam=list(grounds) + [MEADOW], persp=persp))
        o.legendary = True
        sc.live(newcomer(o))
    for i, kind in enumerate(new):
        if kind in FLIERS:
            sc.live(Flier(own, sky, kind, 1.1))
            sc.live(newcomer(Flier(own, sky, kind, 1.1)))
        else:
            ground, x_range = grounds[i % len(grounds)]
            sc.live(Walker(own, ground, x_range, kind, 1.1, roam=roam, persp=persp))
            ground, x_range = grounds[(i + 1) % len(grounds)]
            sc.live(newcomer(Walker(own, ground, x_range, kind, 1.1, roam=roam, persp=persp)))
    if far:
        back = random.Random(sum(map(ord, sc.key)) + 3)
        kinds = list(walkers) + [k for k in new if k not in FLIERS]
        flying = list(fliers) + [k for k in new if k in FLIERS]
        far = list(far)
        for i, (ground, x_range) in enumerate(far):
            for j in range(2):
                w = Walker(back, ground, x_range, kinds[(i * 2 + j) % len(kinds)], 1.1, roam=far, persp=persp)
                sc.live(w if j == 0 else newcomer(w))
            mid = (x_range[0] + x_range[1]) / 2
            gy = ground(mid)
            f = Flier(back, (x_range[0], gy - 70, x_range[1] - x_range[0], 40), flying[i % len(flying)], 1.1 * persp(gy))
            sc.live(f if i == 0 else newcomer(f))
    # a second of each, waiting to come out (his ask: twice as many animals about). Their own
    # dice, so the rest of the place is painted just as before.
    more = random.Random(sum(map(ord, sc.key)) + 1)
    for kind in fliers:
        sc.live(newcomer(Flier(more, sky, kind, 1.1)))
    for i, kind in enumerate(walkers):
        ground, x_range = grounds[(i + 1) % len(grounds)]
        sc.live(newcomer(Walker(more, ground, x_range, kind, 1.1, roam=roam, persp=persp)))


# --- shared palette pieces ------------------------------------------------------------

BASE = dict(
    leaf=(78, 178, 172), leaf2=(106, 202, 168), leaf3=(56, 126, 158), lav=(124, 114, 206),
    pink=(246, 158, 216), pink2=(255, 202, 236), stone=(138, 134, 208), moss=(100, 216, 164),
    earth=(204, 188, 226), earth_edge=(136, 114, 178), water=(78, 138, 228), wood=(158, 106, 148),
    wood2=(198, 148, 178), flowers=[(255, 150, 214), (255, 236, 140), (196, 160, 255), (240, 240, 255),
                                     (140, 230, 255), (255, 186, 150)],
    rim=(178, 198, 255), moon_side=-1,
)


def pal(**kw):
    p = dict(BASE)
    p.update(kw)
    p["light"] = p["rim"]
    return p


def leaf_row(lay, rng, x0, x1, y, rx, ry, color, p, jitter=10, step=None):
    """A row of foliage masses — a canopy edge or a hedge."""
    x = x0
    while x < x1:
        art.foliage(lay, rng, x, y + rng.randint(-jitter, jitter), rx * rng.uniform(0.8, 1.2), ry, color, p)
        x += step or int(rx * 1.1)


def moon(scene, x, y, r=20):
    """A small, pale moon with a soft halo. It is not the main light."""
    s = scene.cur
    art.glow(s, x, y, r * 5, (110, 120, 200), 50)
    art.glow(s, x, y, r * 2, (200, 210, 255), 50)
    face, dark = (236, 236, 255), (196, 196, 236)
    pygame.draw.circle(s, face, (x, y), r)
    for dx, dy, cr in ((-6, -4, 5), (7, 5, 4), (-2, 9, 3), (8, -8, 2), (-10, 6, 2)):
        pygame.draw.circle(s, dark, (x + dx, y + dy), cr)
    pygame.draw.circle(s, (255, 255, 255), (x - r // 3, y - r // 3), r // 4)
    scene.lamp(x, y, r * 6, (90, 100, 150), 40)
    scene.moon = (x, y, r)  # clicking it starts listening for a word (apex.py)


def glowmoss(sc, lay, x, y, w, h, color=None, strength=80, specks=1.0):
    art.glowmoss(sc, lay, x, y, w, h, color, strength, specks)


def moss_glow(sc, pts, color=None, strength=60, every=3):
    """Light the glowing moss cap that art.rock() reported."""
    color = color or GLOW["moss"]
    for i, (x, y) in enumerate(pts):
        if 0 <= x < W and 0 <= y < H:
            sc.emit.set_at((int(x), int(y)), art.scale(color, 0.6))
            if sc.rng.random() < 0.5:
                sc.emit.set_at((int(x) + 1, int(y) + 1), art.scale(color, 0.4))
        if i % every == 0:
            sc.lamp(x, y + 4, 34, color, strength)


def mushroom(lay, x, y, size, cap, sc=None, glow_list=None):
    """A mushroom with a glowing cap; registers its light."""
    stem = (236, 226, 236)
    pygame.draw.rect(lay, stem, (x - 1, y - size, 2 + size // 3, size))
    pygame.draw.ellipse(lay, mix(cap, (30, 20, 60), 0.35), (x - size, y - size - size // 2 + 1, size * 2 + 1, size + 1))
    pygame.draw.ellipse(lay, cap, (x - size, y - size - size // 2, size * 2 + 1, size))
    pygame.draw.line(lay, mix(cap, (255, 255, 255), 0.5), (x - size // 2, y - size - size // 3),
                     (x + size // 3, y - size - size // 3))
    for k in range(-size + 2, size - 1, 3):  # gills
        lay.set_at((x + k, y - size - size // 2 + size), mix(cap, (30, 20, 60), 0.5))
    if sc is not None:
        cx, cy = x, y - size - size // 4
        for dx in (-1, 0, 1):  # the cap glows from its crown
            if 0 <= x + dx < W and 0 <= cy - 1 < H:
                sc.emit.set_at((x + dx, cy - 1), art.scale(cap, 0.35))
        if glow_list is not None:
            glow_list.append((cx, cy, 30 + size * 4, cap, 90, cx * 0.1))


def front_frame(scene, rng, left=True, right=True, top=True, vines=True):
    """Close-up foliage framing the corners — darkest, nearest, like Rain World's foreground."""
    lay = art.plane()
    c, c2 = scene.col("leaf3", 0.02), scene.col("leaf", 0.05)
    p = scene.pal
    if left:
        art.foliage(lay, rng, 20, 532, 88, 48, c, p)
        art.foliage(lay, rng, 60, 504, 52, 32, c2, p)
    if right:
        art.foliage(lay, rng, 940, 536, 92, 40, c, p)
        art.foliage(lay, rng, 904, 524, 40, 24, c2, p)
    if top:
        pygame.draw.rect(lay, c, (0, 0, 280, 10))
        leaf_row(lay, rng, -12, 300, 12, 32, 20, c, p, jitter=6)
        pygame.draw.rect(lay, c, (740, 0, 220, 6))
        leaf_row(lay, rng, 732, 980, 6, 26, 16, c, p, jitter=4)
    scene.add(lay, 0.02, texture=1.2)
    if top and vines:
        tops = lambda x: 28 if x < 300 else 18  # noqa: E731
        xs = list(range(12, 292, 14)) + list(range(732, 956, 20))
        scene.live(Vines(rng, xs, tops, (20, 88), scene.col("leaf3", 0.03), scene.col("leaf2", 0.05),
                         flower=scene.pal["pink"], glow_tip=GLOW["cyan"]))


def squids(sc, rng, region, colors, size=1.5):
    for c in colors:
        sc.live(Squid(rng, region, c, size=size * rng.uniform(0.85, 1.15)))


# --- The Glade (home) ---------------------------------------------------------------------

def build_glade():
    rng = make_rng(11)
    p = pal(sky=[(10, 12, 42), (24, 24, 74), (50, 42, 110), (92, 68, 146)],
            mist=(80, 70, 140), shade=(14, 12, 42), ambient=((230, 232, 255), (80, 80, 142)))
    sc = Scene("glade", "The Glade", p, rng)
    sc.live(Stars(rng, 220, 300, avoid=lambda x, y: x > 600 and y > 80))
    moon(sc, 420, 74, 20)

    # far: violet hills and a little cliff with the waterfall far away
    lay = art.plane()
    art.mountains(lay, rng, 300, 68, sc.col("lav", 0.9), scales=(180, 62, 22), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    art.crag(lay, [(392, 344), (408, 248), (440, 228), (472, 236), (524, 224), (568, 240), (596, 272), (612, 344)],
             sc.col("stone", 0.78), 78, side=p["moon_side"], strata=(6, 12))
    art.canopy(lay, rng, 0, 460, 320, sc.col("leaf3", 0.78), r=(10, 20))
    art.canopy(lay, rng, 560, 980, 316, sc.col("leaf3", 0.78), r=(10, 20))
    for x in (68, 140, 300, 660, 820, 904):  # tall distant trees, Rain World-ish verticals
        art.trunk(lay, rng, x, 192, 330, 6, sc.col("leaf3", 0.8), branches=1)
        art.foliage(lay, rng, x, 208, 18, 44, sc.col("leaf3", 0.8), p)
    sc.add(lay, 0.78, veil=0.04)
    lay = art.plane()
    art.falls(lay, (494, 510, 228), (493, 511, 340), sc.col("water", 0.6), (200, 220, 255), 79)
    sc.raw(lay)
    sc.live(Waterfall(rng, 494, 510, 228, 336, None, sc.col("water", 0.35), (230, 240, 255)))

    lay = art.plane()
    art.ridge(lay, rng, 356, 20, sc.col("leaf", 0.62), scales=(120, 38, 14))
    sc.add(lay, 0.62, veil=0.04, low=0.14)
    for x in (130, 330, 610, 800):  # faraway moss, glowing through the mist
        sc.lamp(x, 350, 60, GLOW["moss"], 30)

    # mid: forest edges framing left and right
    lay = art.plane()
    leans = {}
    for x, w in ((28, 20), (96, 16), (172, 14), (236, 24)):
        leans[x] = art.trunk(lay, rng, x, 40, 392, w, sc.col("wood", 0.5), branches=2, pal=p)
    # a hollow in the nearest of them
    hollow = (round(236 + (392 - 300) * leans[236]), 300)
    pygame.draw.ellipse(lay, mix(sc.col("wood", 0.5), p["shade"], 0.55), (hollow[0] - 13, hollow[1] - 18, 26, 36))
    pygame.draw.ellipse(lay, sc.col("shade", 0.1), (hollow[0] - 10, hollow[1] - 15, 20, 31))
    pygame.draw.rect(lay, sc.col("leaf3", 0.5), (0, 0, 280, 40))
    leaf_row(lay, rng, -20, 292, 52, 44, 32, sc.col("leaf3", 0.5), p, jitter=16)
    for x in (860, 932):
        leans[x] = art.trunk(lay, rng, x, 60, 392, 16, sc.col("wood", 0.5), pal=p)
    # one more tree at the right forest edge, with its own random numbers so the rest of the
    # glade still looks the same. (The bare one left of the signpost is gone: he asked; it is
    # still drawn, out of sight, so the right one comes out unchanged.)
    more = random.Random(117)
    art.trunk(art.plane(), more, 306, 70, 392, 14, sc.col("wood", 0.5), branches=1, pal=p)
    leans[676] = art.trunk(lay, more, 676, 110, 392, 14, sc.col("wood", 0.5), branches=1, pal=p)
    # its crown (he noticed it had none): leafy masses up top, most of it behind the blossom tree
    crown = random.Random(118)
    top = 676 + (392 - 110) * leans[676]
    for dx, dy, rx, ry in ((0, 96, 34, 26), (-22, 116, 24, 18), (20, 112, 26, 18), (2, 74, 22, 18)):
        art.foliage(lay, crown, top + dx, dy, rx, ry, sc.col("leaf3", 0.5), p)
    pygame.draw.rect(lay, sc.col("leaf3", 0.5), (808, 0, 160, 60))
    leaf_row(lay, rng, 808, 980, 72, 40, 32, sc.col("leaf3", 0.5), p, jitter=16)
    art.canopy(lay, rng, -20, 300, 388, sc.col("leaf", 0.5), r=(12, 24))
    art.canopy(lay, rng, 820, 980, 392, sc.col("leaf", 0.5), r=(12, 24))
    leaf_row(lay, rng, -20, 300, 376, 24, 16, sc.col("leaf", 0.5), p)
    leaf_row(lay, rng, 820, 980, 380, 24, 16, sc.col("leaf", 0.5), p)
    sc.add(lay, 0.5, veil=0.04, low=0.1)
    for x in (40, 110, 190, 880, 930):
        sc.lamp(x, 392, 50, GLOW["moss"], 40)

    # near: the meadow, the paths, the signpost
    lay = art.plane()
    art.ridge(lay, rng, 400, 10, sc.col("leaf2", 0.3), scales=(160, 60, 24))
    art.grass_bed(lay, rng, (0, 392, W, 148), sc.col("leaf", 0.25), 2400, 6)
    art.flowers(lay, rng, (0, 408, W, 132), p["flowers"], 160)
    sc.add(lay, 0.3, texture=0.6)
    lay = art.plane()
    earth, edge = sc.col("earth", 0.25), sc.col("earth_edge", 0.25)
    art.path(lay, [(480, 428), (492, 404), (500, 380), (504, 360)], [52, 30, 16, 8], earth, edge, rng=rng)
    art.path(lay, [(480, 428), (340, 422), (200, 412), (60, 404), (-24, 402)], [52, 42, 34, 28, 26], earth, edge, rng=rng)
    art.path(lay, [(480, 428), (640, 434), (800, 426), (984, 430)], [52, 44, 40, 36], earth, edge, rng=rng)
    art.path(lay, [(480, 428), (408, 468), (320, 512), (260, 556)], [52, 68, 84, 100], earth, edge, rng=rng)
    pygame.draw.ellipse(lay, edge, (416, 412, 132, 40))
    pygame.draw.ellipse(lay, earth, (418, 410, 128, 36))
    # mossy rocks by the path down to the Mossy Rocks, their moss glowing
    rock_moss = []
    for x, y, w, h in ((192, 476, 60, 26), (140, 492, 40, 18), (380, 524, 48, 20), (120, 456, 28, 12)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.2), moss=sc.col("moss", 0.18), mossiness=0.7,
                 glow_pts=rock_moss)
        sc.shadow(x, y + 4, w * 0.7, h * 0.4, 0.35)
    moss_glow(sc, rock_moss, strength=55)
    # signpost
    wood, wood2 = sc.col("wood", 0.22), sc.col("wood2", 0.22)
    pygame.draw.rect(lay, wood, (476, 364, 8, 64))
    for y, dx, w in ((368, -1, 44), (384, 1, 40), (400, -1, 36)):
        x = 480 if dx > 0 else 480 - w
        pygame.draw.rect(lay, wood2, (x, y, w, 10))
        tip = x + w if dx > 0 else x
        pygame.draw.polygon(lay, wood2, [(tip, y), (tip + dx * 6, y + 5), (tip, y + 9)])
        pygame.draw.line(lay, wood, (x + 4, y + 4), (x + w - 6, y + 4))
        pygame.draw.line(lay, mix(wood2, p["rim"], 0.3), (x, y), (x + w - 1, y))
    # stump with a lantern on it
    pygame.draw.ellipse(lay, wood, (320, 424, 40, 24))
    pygame.draw.rect(lay, wood, (322, 412, 36, 22))
    pygame.draw.ellipse(lay, wood2, (320, 404, 40, 16))
    for r in (5, 10, 15):
        pygame.draw.ellipse(lay, mix(wood2, wood, 0.5), (340 - r, 412 - r // 2.6, r * 2, r * 0.75), 1)
    pygame.draw.rect(lay, sc.col("wood", 0.1), (334, 392, 12, 14))
    pygame.draw.rect(lay, (255, 240, 180), (336, 394, 8, 10))
    pygame.draw.line(lay, sc.col("wood", 0.1), (340, 386), (340, 392))
    sc.add(lay, 0.22, texture=0.4)
    glowmoss(sc, lay, 300, 444, 30, 10)
    glowmoss(sc, lay, 560, 452, 40, 12, GLOW["lime"])
    glowmoss(sc, lay, 640, 504, 54, 14)
    glowmoss(sc, lay, 60, 470, 46, 12, GLOW["cyan"])
    glowmoss(sc, lay, 860, 470, 60, 16)
    sc.raw(lay)
    sc.shadow(340, 440, 40, 10, 0.4)
    sc.shadow(480, 430, 20, 6, 0.4)
    sc.live(Lantern(340, 398, (255, 196, 120), reach=150))

    # the big blossom tree, its blossoms faintly glowing
    lay = art.plane()
    art.trunk(lay, rng, 744, 192, 412, 26, sc.col("wood", 0.28), branches=3, pal=p)
    pygame.draw.ellipse(lay, sc.col("shade", 0.1), (732, 320, 22, 32))  # the hollow
    sc.add(lay, 0.28, texture=0.8)
    glowmoss(sc, lay, 728, 412, 50, 12)
    glowmoss(sc, lay, 774, 408, 30, 10, GLOW["cyan"])
    sc.raw(lay)
    sc.shadow(744, 420, 90, 18, 0.45)
    sc.lamp(743, 336, 26, GLOW["amber"], 50)  # something lives in the hollow
    sc.shine(743, 338, 8, GLOW["amber"], 60)
    lay = art.plane()
    crown = ((744, 200, 112, 60), (680, 168, 60, 40), (808, 172, 60, 40), (744, 140, 76, 44),
             (644, 216, 40, 24), (848, 216, 40, 24))
    for cx, cy, rx, ry in crown:
        art.foliage(lay, rng, cx, cy, rx, ry, sc.col("pink", 0.32), p, leaf=(4, 8))
    mask = pygame.mask.from_surface(lay)
    art.blossoms(lay, rng, (600, 80, 300, 200), [(255, 255, 255), (255, 220, 240), (255, 130, 196)], 700, mask)
    sc.add(lay, 0.3)
    for _ in range(90):
        x, y = rng.randint(620, 870), rng.randint(110, 260)
        if mask.get_at((x, y)):
            sc.emit.set_at((x, y), (120, 50, 100))
    sc.lamp(744, 200, 150, GLOW["pink"], 34)
    sc.live(Petals(rng, (620, 140, 260, 80), 460, 60, [(255, 200, 230), (255, 255, 255), (255, 150, 200)]))
    # fruit in its canopy: what he used lately, and his new downloads up top (orchard.py)
    sc.orchard = sc.live(Orchard(sc, Spot, canopy=crown))
    sc.live(Nibbler(rng, sc.orchard, (600, 80, 300, 200), GLOW["pink"]))

    sc.live(Shafts([(400, 40, 300, 130, 0.0), (450, 30, 590, 100, 2.4)], (150, 170, 255), alpha=18))
    sc.live(Blades(rng, (0, 412, W, 128), 520, [sc.col("leaf", 0.15), sc.col("leaf2", 0.12), sc.col("leaf3", 0.12)], 6, 18))
    # invertebrates: a slug on the meadow, a glowing one on the mossy rock, a snail up the tree
    # the big violet slug keeps to the middle strip of grass: the corner is the battle field
    sc.live(Slug(rng, Track([(404, 514), (464, 518), (524, 511), (584, 516)]), (214, 170, 222), size=1.5))
    rock_track = sorted((pt for pt in rock_moss if 166 < pt[0] < 220), key=lambda pt: pt[0])
    if len(rock_track) > 2:
        sc.live(Slug(rng, Track([(x, y - 1) for x, y in rock_track]), (120, 150, 230), size=1.2, speed=3,
                     spots=GLOW["cyan"]))
    sc.live(Slug(rng, Track([(758, 404), (757, 360), (756, 300)], up=(1, 0)), (220, 196, 180), size=1.1, speed=2.5,
                 shell=(232, 178, 140)))
    # his desktop icons: a squid on the tree trunks for every app and Desktop item (squids.py)
    trunk = lambda x, w, lo, hi, bottom=392, lean=None: dict(  # noqa: E731
        x=x, w=w, lo=lo, hi=hi, bottom=bottom, lean=leans[x] if lean is None else lean)
    sc.colony = sc.live(Colony(sc, Spot, [
        trunk(28, 18, 96, 290), trunk(96, 14, 96, 290), trunk(172, 13, 96, 330), trunk(236, 22, 96, 330)]))
    # four trees of four: his sixteen; the seed sign under them grows more (squids.GROW_AT)
    sc.critter = Critter(rng, lambda x: 460 + 6 * math.sin(x / 80), (360, 640))
    sc.live(sc.critter)
    additions(sc, rng, [("ring", 650, 488), ("cairn", 120, 506)])
    second_wave(sc, rng, (80, 60, 760, 170), [(lambda x: 500 + 4 * math.sin(x / 50), (420, 600)), (lambda x: 488 + 3 * math.sin(x / 40), (250, 300))],
                far=[(lambda x: 402 + 2 * math.sin(x / 40), (540, 690)), (lambda x: 446 + 2 * math.sin(x / 50), (600, 820))])
    bugs = sc.live(Fireflies(rng, (0, 200, W, 300), 34))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 440), 40, GLOW["cyan"]))
    front_frame(sc, rng)  # no squid in the air here: the glade's squid are on its left trees

    sc.spots = [
        Spot("go", (0, 352, 92, 92), "The Forest", "forest", (28, 400), sign=(78, 352)),
        Spot("go", (872, 376, 88, 88), "The River", "river", (932, 424), sign=(884, 380)),
        Spot("go", (452, 300, 100, 84), "The Waterfall", "waterfall", (504, 352), sign=(510, 300)),
        Spot("go", (200, 476, 168, 64), "The Mossy Rocks", "rocks", (292, 516), sign=(262, 512)),
    ]
    sc.lower = dict(ground=0.3, pond=(540, 256, 224, 132), paths=[dict(
        pts=[(202, -4), (180, 16), (160, 60), (156, 120), (172, 190), (204, 260), (220, 340), (208, 460)],
        widths=[94, 98, 104, 112, 120, 128, 136, 148],
        sign=(320, 392), spot=((120, 300, 240, 150), "The Mossy Rocks", "rocks", (212, 412)))])
    return sc.done()


# --- The Waterfall ----------------------------------------------------------------------

def build_waterfall():
    rng = make_rng(22)
    p = pal(sky=[(10, 14, 46), (22, 30, 82), (40, 52, 116), (70, 84, 150)],
            mist=(64, 80, 146), shade=(12, 14, 44), ambient=((226, 236, 255), (78, 86, 146)), moon_side=1)
    sc = Scene("waterfall", "The Waterfall", p, rng)
    sc.live(Stars(rng, 200, 260, avoid=lambda x, y: 380 < x < 580 and y > 70))
    moon(sc, 800, 70, 18)

    lay = art.plane()
    art.mountains(lay, rng, 240, 80, sc.col("lav", 0.9), scales=(140, 50, 18), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    art.ridge(lay, rng, 300, 60, sc.col("leaf3", 0.72), scales=(100, 34, 12))
    sc.add(lay, 0.72, veil=0.05, low=0.1)

    # the cliff: a ragged outline, stone strata clipped to it, glowing moss on the ledges
    stone = mix(sc.col("stone", 0.42), p["shade"], 0.2)
    outline = [(80, 400)]
    for x, y in ((120, 340), (156, 300), (168, 240), (200, 208), (216, 140), (248, 112), (300, 100), (360, 88), (424, 80)):
        outline.append((x + rng.randint(-6, 6), y + rng.randint(-6, 6)))
    for x, y in ((536, 80), (600, 84), (660, 96), (712, 108), (744, 152), (760, 200), (796, 232), (808, 292),
                 (840, 332), (880, 400)):
        outline.append((x + rng.randint(-6, 6), y + rng.randint(-6, 6)))
    lay = art.plane()
    pygame.draw.polygon(lay, stone, outline)
    ledges = []
    y = 104
    while y < 392:
        h = rng.randint(18, 36)
        band = mix(stone, sc.col("lav", 0.3), rng.uniform(0, 0.55))
        edge = [(x, y + int(4 * math.sin(x / 22 + y) + 2 * math.sin(x / 8.6))) for x in range(60, 903, 6)]
        pygame.draw.polygon(lay, band, edge + [(900, y + h), (60, y + h)])
        pygame.draw.lines(lay, sc.col("stone", 0.24), False, [(x, yy + h) for x, yy in edge])
        x = 60 + rng.randint(0, 40)
        while x < 900:  # moss strips along the ledge, with drips
            ln = rng.randint(12, 44)
            if not (400 < x + ln and x < 560):
                for xx in range(x, x + ln):
                    yy = y + h - 1 + int(4 * math.sin(xx / 22 + y) + 2 * math.sin(xx / 8.6))
                    lay.set_at((xx, yy), sc.col("moss", 0.3))
                    lay.set_at((xx, yy - 1), mix(sc.col("moss", 0.3), (220, 255, 230), 0.4))
                    if rng.random() < 0.15:
                        pygame.draw.line(lay, sc.col("moss", 0.34), (xx, yy), (xx, yy + rng.randint(2, 8)))
                ledges.append((x + ln // 2, y + h, ln))
            x += ln + rng.randint(20, 68)
        y += h
    for x0, x1 in ((404, 428), (532, 556)):  # wet, darker rock beside the falling water, streaked
        wet = mix(stone, p["shade"], 0.3)
        pygame.draw.rect(lay, wet, (x0, 80, x1 - x0, 320))
        for x in range(x0, x1, 2):
            y = 80 + rng.randint(0, 40)
            while y < 400:
                ln = rng.randint(6, 30)
                pygame.draw.line(lay, mix(wet, (230, 240, 255), 0.12) if x % 4 else mix(wet, p["shade"], 0.4), (x, y), (x, y + ln))
                y += ln + rng.randint(4, 20)
    art.crag(lay, outline, stone, 23, side=p["moon_side"], strata=None, fill=False)
    clip = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(clip, (255, 255, 255, 255), outline)
    lay.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    for (x, y) in [pt for pt in outline[1:-1] if not 400 < pt[0] < 560]:
        art.foliage(lay, rng, x, y + 4, 24, 12, sc.col("leaf", 0.4), p)
    sc.add(lay, 0.42, veil=0.02)
    # the cliff's flanks curve away into shadow; its foot is lit by the glowing pool
    sc.shadow(170, 250, 170, 230, 0.5)
    sc.shadow(790, 250, 170, 230, 0.5)
    sc.shadow(480, 60, 300, 80, 0.3)
    for x, y, ln in ledges:
        if rng.random() < 0.7:
            sc.lamp(x, y, ln + 20, GLOW["moss"], 45)
            sc.shine(x, y, ln // 2 + 4, GLOW["moss"], 20)
    # glow-worm curtains under the overhangs either side of the falls
    sc.live(GlowThreads(rng, list(range(236, 396, 5)), lambda x: 104 + abs(x - 316) // 6, (12, 64), GLOW["cyan"]))
    sc.live(GlowThreads(rng, list(range(566, 700, 6)), lambda x: 92 + abs(x - 630) // 6, (12, 56), GLOW["cyan"]))
    lay = art.plane()
    art.falls(lay, (428, 532, 88), (420, 540, 388), sc.col("water", 0.3), (220, 236, 255), 24)
    pygame.draw.ellipse(lay, sc.col("water", 0.2), (200, 372, 560, 88))
    pygame.draw.ellipse(lay, mix(sc.col("water", 0.2), GLOW["cyan"], 0.3), (240, 380, 480, 60))
    for i, k in enumerate((0.92, 0.78, 0.64, 0.5)):  # rings spreading out from the falls, broken up
        rw, rh = int(560 * k), int(88 * k)
        ring = mix(sc.col("water", 0.2), (230, 244, 255), 0.25 + 0.1 * i)
        for a in range(0, 180, 9):
            if (a // 9 + i) % 3:
                pygame.draw.arc(lay, ring, (480 - rw // 2, 416 - rh // 2, rw, rh), math.radians(180 + a),
                                math.radians(180 + a + 6))
    sc.raw(lay)
    sc.lamp(480, 410, 260, GLOW["cyan"], 70)  # the pool glows
    cliff_top = lambda x: 96 if 220 < x < 740 else 220  # noqa: E731
    sc.live(Vines(rng, list(range(232, 408, 12)) + list(range(568, 740, 12)) + [140, 156, 176, 784, 800, 820], cliff_top,
                  (20, 100), sc.col("leaf3", 0.3), sc.col("leaf2", 0.3), flower=p["pink"], glow_tip=GLOW["moss"]))
    sc.live(Waterfall(rng, 428, 536, 88, 392, None, sc.col("water", 0.05), (236, 248, 255)))
    sc.live(River(rng, lambda x: 392, lambda x: 444, (248, 712), 110, mix(sc.col("water", 0.1), (255, 255, 255), 0.5),
                  (255, 255, 255), speed=10))
    sc.pond = sc.live(Shoal(rng, [(Water(350, 420, 100, 22), 2), (Water(620, 420, 100, 22), 2)],
                            sc.col("water", 0.2), size=0.75))
    sc.live(Motes(rng, (380, 300, 200, 120), 50, GLOW["cyan"], rise=-16))

    # banks, mossy rocks, the path down
    lay = art.plane()
    art.ridge(lay, rng, 464, 12, sc.col("leaf2", 0.22), scales=(100, 34, 12))
    pygame.draw.polygon(lay, sc.col("leaf2", 0.22), [(0, 540), (0, 400), (180, 392), (220, 460), (0, 540)])
    pygame.draw.polygon(lay, sc.col("leaf2", 0.22), [(960, 540), (960, 392), (780, 392), (740, 460), (960, 540)])
    art.grass_bed(lay, rng, (0, 392, W, 148), sc.col("leaf", 0.2), 1600, 6)
    art.flowers(lay, rng, (0, 460, W, 80), p["flowers"], 70)
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(480, 456), (472, 492), (464, 556)], [60, 80, 108], earth, edge, rng=rng)
    sc.add(lay, 0.2, texture=0.6)
    lay = art.plane()
    moss_pts = []
    for x, y, w, h, mo in ((280, 424, 112, 48, 0.5), (208, 436, 68, 32, 0.5), (688, 428, 124, 56, 0.5),
                           (600, 444, 52, 24, 0.8)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.22), moss=sc.col("moss", 0.2), mossiness=mo, glow_pts=moss_pts)
    sc.add(lay, 0.2)
    moss_glow(sc, moss_pts, strength=50)
    lay = art.plane()
    glowmoss(sc, lay, 120, 480, 60, 16)
    glowmoss(sc, lay, 860, 474, 50, 14, GLOW["lime"])
    sc.raw(lay)
    sc.live(Blades(rng, (0, 392, 220, 140), 160, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 12, 32, stiff=1.4))
    sc.live(Blades(rng, (740, 392, 220, 140), 160, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 12, 32, stiff=1.4))
    top_pts = sorted((pt for pt in moss_pts if 640 < pt[0] < 740), key=lambda pt: pt[0])
    if len(top_pts) > 2:
        sc.live(Slug(rng, Track([(x, y - 1) for x, y in top_pts]), (210, 190, 176), size=1.3, speed=2.5,
                     shell=(196, 160, 236)))
    sc.live(Slug(rng, Track([(40, 512), (120, 506), (200, 514), (300, 510)]), (150, 120, 210), size=1.5,
                 spots=GLOW["violet"]))
    second_wave(sc, rng, (120, 140, 720, 160), [(lambda x: 500 + 3 * math.sin(x / 45), (200, 360)), (lambda x: 505 + 3 * math.sin(x / 50), (620, 780))],
                new=("spark", "rune"),
                far=[(lambda x: 434 + 2 * math.sin(x / 40), (30, 200)), (lambda x: 434 + 2 * math.sin(x / 45), (770, 930))])
    bugs = sc.live(Fireflies(rng, (0, 260, W, 220), 16, color=GLOW["cyan"], reach=26))
    sc.bugs.append(bugs)
    squids(sc, rng, (80, 120, 800, 220), [GLOW["violet"], GLOW["cyan"]])
    front_frame(sc, rng, top=False)

    lay = art.plane()  # the way up into the Crystal Caverns, and the path out to the Starfall Meadow
    pygame.draw.ellipse(lay, (20, 12, 36), (150, 318, 56, 52))
    pygame.draw.rect(lay, (20, 12, 36), (150, 344, 56, 30))
    for j, c in enumerate(CAVE_CRYSTAL):
        crystal(lay, 160 + j * 16, 372, 14 + j * 4, 4, c)
    for j in range(4):  # steps of stone up to it
        pygame.draw.rect(lay, sc.col("stone", 0.25), (140 + j * 4, 374 + j * 7, 76 - j * 8, 7))
        pygame.draw.line(lay, mix(sc.col("stone", 0.25), (255, 255, 255), 0.2), (140 + j * 4, 374 + j * 7), (216 - j * 4, 374 + j * 7))
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(780, 470), (860, 460), (920, 452), (984, 446)], [24, 32, 40, 48], earth, edge, rng=rng)
    sc.raw(lay)
    sc.lamp(178, 350, 90, CAVE_CRYSTAL[0], 80)
    sc.spots = [
        Spot("go", (392, 480, 168, 60), "Back to the Glade", "glade", (468, 516), sign=(470, 506)),
        Spot("go", (140, 316, 80, 90), "The Crystal Caverns", "caverns", (178, 350), sign=(178, 302)),
        Spot("go", (872, 420, 88, 70), "The Starfall Meadow", "meadow", (920, 454), sign=(850, 412)),
    ]
    sc.lower = dict(ground=0.2, props=["rocks"], fly=GLOW["cyan"], walkers=WALK + ("rune",), fliers=FLY + ("spark",),
                    out=("rune", "spark"), paths=[dict(
        pts=[(386, -4), (382, 60), (374, 160), (364, 280), (354, 460)], widths=[110, 118, 128, 140, 156],
        sign=(480, 344), spot=((260, 220, 240, 230), "Back to the Glade", "glade", (360, 408)))])
    return sc.done()


# --- The River ------------------------------------------------------------------------------

def build_river():
    rng = make_rng(33)
    p = pal(sky=[(10, 12, 44), (26, 26, 80), (56, 44, 116), (98, 70, 148)],
            mist=(84, 72, 142), shade=(12, 14, 42), ambient=((230, 232, 255), (80, 82, 142)), moon_side=1)
    sc = Scene("river", "The River", p, rng)
    sc.live(Stars(rng, 220, 260))
    moon(sc, 760, 96, 22)

    lay = art.plane()
    art.mountains(lay, rng, 256, 60, sc.col("lav", 0.9), scales=(180, 60, 20), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()
    art.canopy(lay, rng, -20, 980, 280, sc.col("leaf3", 0.72), r=(12, 24))
    sc.add(lay, 0.72, veil=0.05, low=0.08)

    # far bank, with a willow
    lay = art.plane()
    art.ridge(lay, rng, 316, 8, sc.col("leaf2", 0.5), scales=(120, 40, 16))
    art.trunk(lay, rng, 600, 184, 312, 14, sc.col("wood", 0.5), branches=2, pal=p)
    art.foliage(lay, rng, 600, 192, 72, 32, sc.col("leaf", 0.5), p)
    for x in (140, 240, 820):
        art.foliage(lay, rng, x, 284, 32, 24, sc.col("leaf", 0.55), p)
    sc.add(lay, 0.5, veil=0.03)
    for x in (140, 240, 820, 600):
        sc.lamp(x, 312, 44, GLOW["moss"], 34)
    sc.live(Vines(rng, range(544, 660, 6), lambda x: 192 + abs(x - 600) // 3, (48, 104),
                  sc.col("leaf", 0.45), sc.col("leaf2", 0.45), glow_tip=GLOW["cyan"]))

    # the water, with the moon in it
    top = lambda x: 320 + 4 * math.sin(x / 100)  # noqa: E731
    bot = lambda x: 412 + 6 * math.sin(x / 140 + 1)  # noqa: E731
    lay = art.plane()
    pygame.draw.polygon(lay, sc.col("water", 0.35), [(0, top(0))] + [(x, top(x)) for x in range(0, W + 1, 8)]
                        + [(x, bot(x)) for x in range(W, -1, -8)])
    for y in range(316, 420):  # sky reflected in bands
        if y % 14 < 3:
            pygame.draw.line(lay, mix(sc.col("water", 0.35), p["sky"][2], 0.4), (0, y), (W, y))
    for i in range(12):  # the moon's broken reflection
        y = 330 + i * 7
        w_ = 36 - i * 2 + rng.randint(-4, 4)
        pygame.draw.line(lay, (200, 210, 250), (760 - w_ // 2 + rng.randint(-4, 4), y), (760 + w_ // 2, y))
    sc.raw(lay)
    lay = art.plane()  # lily pads with glowing flowers, and stepping stones
    lilies = []
    for _ in range(18):
        x, y = rng.randint(60, 400), rng.randint(352, 404)
        r = 4 + (y - 340) // 9
        pygame.draw.ellipse(lay, mix(sc.col("leaf2", 0.25), (14, 12, 40), 0.3), (x, y + 1, r * 2 + 4, r))
        pygame.draw.ellipse(lay, sc.col("leaf2", 0.25), (x, y, r * 2 + 4, r))
        if rng.random() < 0.45:
            c = rng.choice([GLOW["pink"], GLOW["violet"], (255, 255, 255)])
            for dx, dy in ((r, -1), (r + 1, -1), (r + 2, -1), (r + 1, -2), (r, 0), (r + 2, 0)):
                lay.set_at((x + dx, y + dy), c)
            lilies.append((x + r + 1, y - 1, 24, c, 70, x * 0.1))
    stones_moss = []
    for x, y, w in ((300, 352, 24), (360, 372, 32), (428, 392, 40)):
        art.rock(lay, rng, x, y, w, w // 3, sc.col("stone", 0.3), moss=sc.col("moss", 0.3), mossiness=0.6,
                 glow_pts=stones_moss)
    sc.add(lay, 0.28, texture=0.5)
    moss_glow(sc, stones_moss, strength=40)
    sc.live(Pulses(lilies, speed=0.9))
    sc.live(River(rng, top, bot, (0, W), 220, mix(sc.col("water", 0.3), (255, 255, 255), 0.4), (255, 255, 255)))
    sc.pond = sc.live(Shoal(rng, [(Water(170, 368, 150, 24), 2), (Water(450, 362, 130, 22), 2), (Water(860, 370, 90, 20), 1)],
                            sc.col("water", 0.35), size=0.7))
    lay = art.plane()  # the little boat, tied up at the bank, with a lantern on its bow
    wood, wood2 = sc.col("wood", 0.12), sc.col("wood2", 0.12)
    pygame.draw.ellipse(lay, mix(sc.col("water", 0.3), p["shade"], 0.3), (624, 398, 152, 16))  # its reflection
    pygame.draw.polygon(lay, wood, [(628, 380), (768, 380), (748, 404), (648, 404)])
    pygame.draw.line(lay, wood2, (628, 380), (768, 380), 3)
    pygame.draw.line(lay, mix(wood, wood2, 0.5), (640, 392), (756, 392))
    for x in range(652, 750, 16):
        pygame.draw.line(lay, mix(wood, (20, 10, 40), 0.3), (x, 383), (x + 2, 402))
    pygame.draw.rect(lay, wood2, (688, 374, 20, 6))
    pygame.draw.line(lay, wood, (760, 380), (760, 356), 2)  # lantern pole
    pygame.draw.rect(lay, sc.col("wood", 0.05), (754, 356, 12, 12))
    pygame.draw.rect(lay, (255, 236, 176), (756, 358, 8, 8))
    sc.add(lay, 0.12, texture=0.3)
    sc.live(Lantern(760, 362, (255, 200, 130), reach=120))

    # near bank, path
    lay = art.plane()
    pts = [(x, int(bot(x)) + 4 + int(4 * math.sin(x / 26))) for x in range(0, W + 1, 4)]
    pygame.draw.polygon(lay, sc.col("leaf2", 0.18), [(0, H)] + pts + [(W, H)])
    art.grass_bed(lay, rng, (0, 412, W, 128), sc.col("leaf", 0.15), 1600, 6)
    art.flowers(lay, rng, (0, 436, W, 104), p["flowers"], 80)
    earth, edge = sc.col("earth", 0.15), sc.col("earth_edge", 0.15)
    art.path(lay, [(-24, 476), (160, 484), (400, 480), (580, 456), (636, 440)], [40, 44, 44, 36, 28], earth, edge, rng=rng)
    art.path(lay, [(600, 452), (700, 446), (800, 440), (900, 436), (984, 434)], [30, 30, 32, 34, 34], earth, edge,
             rng=random.Random(34))  # on to the Hot Springs
    sc.add(lay, 0.15, texture=0.6)
    lay = art.plane()  # the post the boat is tied to
    pygame.draw.line(lay, sc.col("earth_edge", 0.1), (632, 386), (608, 428))
    pygame.draw.rect(lay, sc.col("wood", 0.1), (604, 412, 8, 32))
    glowmoss(sc, lay, 500, 500, 70, 16)
    glowmoss(sc, lay, 860, 482, 60, 14, GLOW["cyan"])
    glowmoss(sc, lay, 260, 520, 50, 12, GLOW["lime"])
    sc.add(lay, 0.1, texture=0.3)
    for x0, x1 in ((0, 120), (240, 400), (800, 960)):  # reeds in clumps along the bank
        sc.live(Blades(rng, (x0, 404, x1 - x0, 16), (x1 - x0) // 2, [sc.col("leaf", 0.12), sc.col("leaf3", 0.12)],
                       16, 40, stiff=1.3))
    sc.live(Slug(rng, Track([(320, 506), (420, 512), (520, 508), (640, 514), (760, 506)]), (230, 200, 120), size=1.6,
                 speed=4))
    additions(sc, rng, [("lotus", 230, 362), ("lotus", 300, 384), ("lotus", 540, 372), ("lotus", 470, 392), ("log", 420, 470), ("cairn", 880, 486)])
    second_wave(sc, rng, (100, 60, 760, 220), [(lambda x: 505 + 4 * math.sin(x / 55), (420, 600)), (lambda x: 510 + 3 * math.sin(x / 50), (120, 300))],
                new=("murk", "glint"),
                far=[(lambda x: 312 + 2 * math.sin(x / 50), (60, 520)), (lambda x: 432 + 2 * math.sin(x / 40), (200, 600))])
    bugs = sc.live(Fireflies(rng, (0, 220, W, 220), 30))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 400), 30, GLOW["cyan"]))
    squids(sc, rng, (100, 120, 760, 200), [GLOW["pink"], GLOW["cyan"], GLOW["lime"]])
    front_frame(sc, rng, top=True, right=False)

    sc.spots = [
        Spot("go", (0, 428, 88, 92), "Back to the Glade", "glade", (28, 476), sign=(104, 444)),
        Spot("go", (872, 396, 88, 76), "The Hot Springs", "springs", (930, 434), sign=(852, 392)),
    ]
    sc.lower = dict(ground=0.18, props=["rocks"], fly=GLOW["firefly"], walkers=WALK + ("murk", "glint"),
                    out=("murk", "glint"), paths=[dict(
                        pts=[(312, -4), (316, 80), (322, 200), (326, 320), (330, 460)], widths=[96, 104, 116, 128, 140],
                        sign=(460, 240), spot=((240, 150, 170, 220), "The Misty Bog", "bog", (322, 300)))])
    return sc.done()


# --- The Forest --------------------------------------------------------------------------------

def build_forest():
    rng = make_rng(44)
    p = pal(sky=[(8, 18, 34), (16, 36, 60), (34, 60, 88), (58, 92, 116)],
            mist=(48, 84, 110), shade=(8, 16, 36), ambient=((210, 230, 240), (66, 80, 120)),
            leaf3=(56, 140, 150), wood=(130, 104, 140))
    sc = Scene("forest", "The Forest", p, rng)
    sc.live(Stars(rng, 60, 60))

    # rank after rank of trunks fading into the mist
    for d, n, (wmin, wmax), y in ((0.9, 14, (4, 8), 372), (0.76, 11, (8, 12), 384),
                                  (0.6, 8, (12, 18), 396), (0.42, 5, (20, 28), 412)):
        lay = art.plane()
        xs = sorted(rng.sample(range(0, W, 16), n))
        for x in xs:
            art.trunk(lay, rng, x + rng.randint(-6, 6), -10, y + 8, rng.randint(wmin, wmax), sc.col("wood", d),
                      branches=rng.randint(0, 2), pal=p if d < 0.7 else None)
        art.canopy(lay, rng, -20, 980, int(40 * (1 - d)) + 8, sc.col("leaf3", d), r=(16, 32), jitter=12, down=False)
        art.ridge(lay, rng, y, 8, sc.col("leaf", d), scales=(80, 30, 12))
        sc.add(lay, d, veil=0.04, low=0.12)
        for x in xs[::2]:
            sc.lamp(x, y, int(50 * (1.2 - d)), GLOW["moss"], int(50 * (1.1 - d)))
    lay = art.plane()
    art.trunk(lay, rng, 52, -10, 524, 48, sc.col("wood", 0.08), branches=1, pal=p)
    art.trunk(lay, rng, 808, -10, 476, 36, sc.col("wood", 0.12), branches=1, pal=p)
    leaf_row(lay, rng, -20, 980, 8, 40, 24, sc.col("leaf3", 0.1), p, jitter=8)
    sc.add(lay, 0.1, texture=1.0)
    lay = art.plane()
    for x, y, w, h, c in ((60, 470, 40, 60, GLOW["moss"]), (808, 450, 30, 50, GLOW["lime"])):  # moss up the trunks
        glowmoss(sc, lay, x, y, w, h, c, strength=60, specks=0.6)
    sc.raw(lay)
    sc.live(Shafts([(440, 60, 240, 160, 0.0), (600, 48, 480, 128, 1.7), (320, 32, 120, 100, 3.4)],
                   (140, 200, 220), alpha=24))

    lay = art.plane()
    art.ridge(lay, rng, 428, 8, sc.col("leaf2", 0.22), scales=(100, 36, 14))
    art.grass_bed(lay, rng, (0, 420, W, 120), sc.col("leaf", 0.18), 1800, 6)
    art.flowers(lay, rng, (0, 440, W, 100), [(255, 255, 255), (196, 150, 255), (130, 226, 255)], 60)
    earth, edge = sc.col("earth", 0.2), sc.col("earth_edge", 0.2)
    art.path(lay, [(984, 488), (800, 476), (600, 448), (500, 428), (460, 412)], [48, 44, 36, 20, 10], earth, edge, rng=rng)
    art.path(lay, [(486, 424), (380, 430), (240, 434), (100, 440), (-24, 444)], [16, 24, 28, 32, 34], earth, edge,
             rng=random.Random(45))  # on to the Snowy Ridge
    art.path(lay, [(486, 426), (480, 406), (474, 388), (472, 376)], [16, 11, 7, 4], earth, edge,
             rng=random.Random(46))  # up through the trees to the Old Ruins
    sc.add(lay, 0.2, texture=0.6)

    # a ring of glowing mushrooms, and more scattered about
    lay = art.plane()
    glowmoss(sc, lay, 300, 476, 80, 18, GLOW["moss"], strength=50, specks=0.5)  # inside the ring, behind it
    glowmoss(sc, lay, 640, 470, 50, 12, GLOW["lime"])
    caps = [(130, 140, 255), (255, 150, 220), (140, 236, 255), (200, 160, 255)]
    ring = []
    for i in range(11):
        a = i / 11 * math.tau
        x, y = int(300 + math.cos(a) * 52), int(472 + math.sin(a) * 15)
        size = rng.randint(6, 11) + (4 if y > 472 else 0)
        mushroom(lay, x, y, size, caps[i % len(caps)], sc, ring)
    for x, y in ((120, 500), (520, 480), (700, 500), (880, 470), (440, 520)):
        for _ in range(rng.randint(2, 3)):
            mushroom(lay, x + rng.randint(-14, 14), y + rng.randint(-4, 4), rng.randint(4, 8), rng.choice(caps), sc, ring)
    sc.add(lay, 0.12, texture=0)
    sc.live(Pulses(ring, speed=1.0))
    sc.live(Blades(rng, (0, 424, W, 116), 400, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1), sc.col("leaf2", 0.1)], 8, 24))
    sc.live(Millipede(rng, Track([(760, 486), (720, 470), (700, 440), (690, 380)], up=(1, -0.3)), (90, 60, 110),
                      GLOW["cyan"]))
    sc.live(Slug(rng, Track([(140, 512), (240, 518), (360, 512), (480, 520)]), (250, 220, 130), size=1.6, speed=4))
    sc.live(Slug(rng, Track([(66, 500), (64, 440), (62, 380)], up=(1, 0)), (140, 120, 220), size=1.3, speed=2,
                 spots=GLOW["pink"]))
    additions(sc, rng, [("log", 600, 500), ("ring", 820, 500)])
    second_wave(sc, rng, (100, 120, 700, 200), [(lambda x: 478 + 3 * math.sin(x / 40), (140, 280)), (lambda x: 512 + 3 * math.sin(x / 50), (420, 600))],
                new=("thistle", "bramble"),
                far=[(lambda x: 436 + 3 * math.sin(x / 60), (150, 760)), (lambda x: 394 + 2 * math.sin(x / 40), (220, 680))])
    bugs = sc.live(Fireflies(rng, (0, 140, W, 360), 56, color=GLOW["lime"]))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 460), 70, GLOW["moss"]))
    squids(sc, rng, (120, 100, 700, 240), [GLOW["cyan"], GLOW["pink"]])
    front_frame(sc, rng)

    sc.spots = [
        Spot("go", (872, 428, 88, 92), "Back to the Glade", "glade", (932, 480), sign=(864, 424)),
        Spot("go", (0, 400, 96, 76), "The Snowy Ridge", "ridge", (30, 442), sign=(112, 396)),
        Spot("go", (424, 330, 100, 76), "The Old Ruins", "ruins", (474, 380), sign=(474, 340)),
    ]
    sc.lower = dict(ground=0.2, props=["mushrooms"], fly=GLOW["lime"], walkers=WALK + ("bramble",),
                    fliers=FLY + ("thistle",), out=("bramble", "thistle"), paths=[dict(
                        pts=[(232, -4), (230, 80), (226, 200), (220, 320), (214, 460)], widths=[96, 104, 116, 128, 140],
                        sign=(370, 240), spot=((150, 150, 160, 220), "The Mushroom Hollow", "hollow", (224, 300)))])
    return sc.done()


# --- The Mossy Rocks --------------------------------------------------------------------------------

def build_rocks():
    rng = make_rng(55)
    p = pal(sky=[(14, 10, 44), (34, 24, 84), (64, 40, 118), (106, 64, 148)],
            mist=(90, 66, 142), shade=(16, 10, 42), ambient=((232, 226, 255), (78, 74, 140)))
    sc = Scene("rocks", "The Mossy Rocks", p, rng)
    sc.live(Stars(rng, 220, 280))
    moon(sc, 180, 110, 18)

    lay = art.plane()
    art.mountains(lay, rng, 280, 72, sc.col("lav", 0.9), scales=(160, 54, 18), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()  # distant stone spires, moss glowing on their tops
    for x, top, w in ((120, 140, 36), (220, 192, 24), (744, 120, 44), (840, 180, 28), (908, 220, 20)):
        art.crag(lay, [(x - w // 2, 360), (x - w // 3, top + 12), (x, top), (x + w // 3, top + 16), (x + w // 2, 360)],
                 sc.col("stone", 0.72), x, side=p["moon_side"], strata=(8, 18))
        art.clump(lay, rng, x, top, w // 2 + 6, sc.col("moss", 0.72), n=5)
        sc.lamp(x, top, w + 20, GLOW["moss"], 34)
    art.canopy(lay, rng, -20, 980, 336, sc.col("leaf3", 0.72), r=(10, 20))
    sc.add(lay, 0.72, veil=0.05, low=0.1)
    lay = art.plane()
    art.ridge(lay, rng, 392, 12, sc.col("leaf2", 0.45), scales=(120, 40, 16))
    sc.add(lay, 0.45, veil=0.03)

    # the pile of mossy boulders, with a crystal cave at its foot
    lay = art.plane()
    stone, moss = sc.col("stone", 0.3), sc.col("moss", 0.25)
    moss_pts = []
    pygame.draw.polygon(lay, mix(stone, p["shade"], 0.25), [(340, 444), (392, 300), (480, 264), (600, 300), (640, 444)])
    art.rock(lay, rng, 488, 300, 100, 56, stone, moss=moss, mossiness=0.6, glow_pts=moss_pts)
    art.rock(lay, rng, 420, 344, 160, 80, stone, moss=moss, glow_pts=moss_pts)
    art.rock(lay, rng, 564, 356, 152, 84, stone, moss=moss, glow_pts=moss_pts)
    art.rock(lay, rng, 352, 444, 192, 100, stone, moss=moss, mossiness=0.4, glow_pts=moss_pts)
    art.rock(lay, rng, 608, 452, 208, 108, stone, moss=moss, mossiness=0.4, glow_pts=moss_pts)
    pygame.draw.ellipse(lay, sc.col("shade", 0.0), (444, 392, 80, 68))  # cave mouth
    pygame.draw.rect(lay, sc.col("shade", 0.0), (444, 426, 80, 28))
    sc.add(lay, 0.28, texture=1.0)
    moss_glow(sc, moss_pts, strength=60, every=2)
    lay = art.plane()
    crystals = [(464, 440, GLOW["violet"]), (478, 430, GLOW["cyan"]), (490, 436, GLOW["pink"]), (504, 444, GLOW["cyan"]),
                (456, 448, GLOW["pink"])]
    for x, y, c in crystals:
        h = rng.randint(10, 18)
        pygame.draw.polygon(lay, c, [(x - 4, y + 10), (x - 1, y - h + 10), (x + 1, y - h + 8), (x + 4, y + 10)])
        pygame.draw.line(lay, mix(c, (255, 255, 255), 0.7), (x - 1, y - h + 12), (x - 1, y + 8))
        pygame.draw.line(lay, mix(c, (20, 10, 50), 0.3), (x + 2, y - h + 12), (x + 2, y + 9))
    sc.raw(lay)
    sc.live(Pulses([(x, y, 70, c, 120, i * 2.0) for i, (x, y, c) in enumerate(crystals)], speed=1.2))
    sc.live(GlowThreads(rng, list(range(452, 520, 4)), lambda x: 400 + abs(x - 484) // 3, (6, 20), GLOW["cyan"]))

    lay = art.plane()  # standing stone with a carved rune
    pygame.draw.polygon(lay, sc.col("stone", 0.22), [(152, 452), (156, 324), (176, 300), (200, 316), (204, 452)])
    rune_moss = []
    art.rock(lay, rng, 178, 324, 52, 24, sc.col("stone", 0.22), moss=sc.col("moss", 0.2), mossiness=0.9,
             glow_pts=rune_moss)
    rune = (150, 230, 255)
    for a, b in (((172, 352), (184, 352)), ((178, 344), (178, 388)), ((170, 368), (186, 380)), ((186, 368), (170, 380))):
        pygame.draw.line(lay, rune, a, b, 2)
    sc.add(lay, 0.22, texture=0.6)
    moss_glow(sc, rune_moss, strength=50)
    sc.shadow(178, 456, 40, 8, 0.4)
    sc.live(Pulses([(178, 366, 60, (150, 220, 255), 110, 0.0)], speed=0.8))
    for a, b in (((172, 352), (184, 352)), ((178, 344), (178, 388)), ((170, 368), (186, 380)), ((186, 368), (170, 380))):
        pygame.draw.line(sc.emit, (70, 110, 130), a, b, 2)

    lay = art.plane()
    art.ridge(lay, rng, 460, 8, sc.col("leaf2", 0.15), scales=(100, 36, 14))
    art.grass_bed(lay, rng, (0, 452, W, 88), sc.col("leaf", 0.12), 1200, 6)
    art.flowers(lay, rng, (0, 464, W, 76), p["flowers"], 60)
    earth, edge = sc.col("earth", 0.12), sc.col("earth_edge", 0.12)
    # the way back up to the Glade, climbing away into the distance
    art.path(lay, [(600, 556), (640, 504), (696, 470), (744, 450), (768, 438)], [112, 76, 46, 22, 10], earth, edge, rng=rng)
    # and the way down to the Battle Tower, on down the lower screen
    art.path(lay, [(320, 466), (316, 500), (312, 530), (312, 556)], [16, 52, 80, 96], earth, edge, rng=random.Random(82))
    near_moss = []
    for x in (240, 860, 900, 420):  # clear of the paths
        art.rock(lay, rng, x, 480 + rng.randint(0, 40), rng.randint(28, 52), rng.randint(12, 20),
                 sc.col("stone", 0.1), moss=sc.col("moss", 0.1), glow_pts=near_moss)
    sc.add(lay, 0.12, texture=0.6)
    moss_glow(sc, near_moss, strength=50)
    lay = art.plane()
    glowmoss(sc, lay, 80, 500, 70, 16)
    glowmoss(sc, lay, 900, 500, 60, 16, GLOW["cyan"])
    glowmoss(sc, lay, 460, 516, 50, 12, GLOW["lime"])
    sc.raw(lay)
    sc.live(Blades(rng, (0, 452, W, 88), 400, [sc.col("leaf", 0.08), sc.col("leaf2", 0.08)], 8, 24))
    # the slug capital of the glade: two on the boulders, a snail, one on the ground
    def crest(lo, hi):
        # the gently sloping top of a boulder's moss cap: slugs do not hang off cliffs
        pts = sorted((pt for pt in moss_pts if lo < pt[0] < hi), key=lambda pt: pt[0])
        if not pts:
            return []
        top = min(y for _, y in pts)
        return [pt for pt in pts if pt[1] < top + 16]

    for lo, hi, body, spots, shell, sz in ((380, 470, (130, 120, 220), GLOW["cyan"], None, 1.4),
                                          (528, 606, (236, 190, 120), None, None, 1.5),  # its own boulder only
                                          (300, 400, (210, 190, 200), None, (180, 150, 230), 1.3)):
        pts = crest(lo, hi)
        if len(pts) > 3:
            sc.live(Slug(rng, Track([(x, y - 1) for x, y in pts]), body, size=sz, speed=2.5, spots=spots, shell=shell))
    sc.live(Slug(rng, Track([(600, 524), (700, 520), (800, 528), (900, 522)]), (200, 120, 200), size=1.6, speed=4,
                 spots=GLOW["violet"]))
    additions(sc, rng, [("cairn", 90, 486), ("cairn", 880, 470), ("ring", 330, 500)])
    second_wave(sc, rng, (100, 40, 760, 160), [(lambda x: 506 + 3 * math.sin(x / 50), (300, 520)), (lambda x: 505 + 2 * math.sin(x / 40), (40, 110))],
                far=[(lambda x: 424 + 2 * math.sin(x / 40), (20, 200)), (lambda x: 434 + 2 * math.sin(x / 45), (700, 930))])
    bugs = sc.live(Fireflies(rng, (0, 180, W, 300), 26, color=GLOW["pink"]))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 460), 50, GLOW["moss"]))
    squids(sc, rng, (100, 80, 760, 220), [GLOW["violet"], GLOW["cyan"], GLOW["pink"]])
    front_frame(sc, rng, left=False)

    sc.spots = [
        Spot("go", (700, 420, 120, 64), "Back to the Glade", "glade", (756, 446), sign=(780, 404)),
    ]
    sc.lower = dict(ground=0.14, props=["rocks"], fly=GLOW["pink"], paths=[dict(
        pts=[(232, -4), (230, 80), (226, 200), (220, 320), (214, 460)], widths=[96, 104, 116, 128, 140],
        sign=(370, 240), spot=((150, 150, 160, 220), "The Battle Tower", "tower", (224, 300)))])
    return sc.done()


# --- The Snowy Ridge (beyond the Forest) ----------------------------------------------------------

SNOW = (236, 244, 255)


def snowcaps(lay, tops, color, line, rng):
    """Snow on far peaks: thick on the summits, thinning to streaks down the gullies."""
    for x in range(len(tops) - 1):
        depth = max(0, line - tops[x])
        if depth <= 0:
            continue
        ln = int(depth * (0.5 + 0.3 * math.sin(x / 7.0) + 0.2 * math.sin(x / 2.3)))
        pygame.draw.line(lay, color, (x, tops[x]), (x, tops[x] + ln))
        if rng.random() < 0.3:
            pygame.draw.line(lay, color, (x, tops[x] + ln), (x, tops[x] + ln + rng.randint(2, 10)))


def ice_crystals(sc, lay, x, y, n, color, glows):
    """A cluster of glowing ice crystals growing out of the snow."""
    rng = sc.rng
    for i in range(n):
        h = rng.randint(6, 18)
        w = max(2, h // 4)
        cx = x + rng.randint(-10, 10)
        lean = rng.uniform(-0.4, 0.4)
        tip = (cx + lean * h, y - h)
        body = mix(color, (255, 255, 255), 0.35)
        pygame.draw.polygon(lay, mix(color, (40, 50, 120), 0.35), [(cx - w, y), (cx + w, y), tip])
        pygame.draw.polygon(lay, body, [(cx - w + 1, y), (cx, y), tip])
        if 0 <= int(tip[0]) < W and 0 <= int(tip[1]) < H:
            sc.emit.set_at((int(tip[0]), int(tip[1])), art.scale(color, 0.8))
    glows.append((x, y - 8, 60, color, 90, x * 0.1))


def build_ridge():
    rng = make_rng(55)
    p = pal(sky=[(6, 10, 34), (14, 24, 66), (32, 50, 110), (70, 92, 160)],
            mist=(84, 104, 170), shade=(10, 16, 48), ambient=((230, 240, 255), (92, 104, 166)),
            leaf=(196, 222, 246), leaf2=(222, 236, 252), leaf3=(58, 112, 140), lav=(150, 162, 228),
            stone=(150, 156, 214), earth=(206, 206, 240), earth_edge=(140, 140, 196), wood=(120, 96, 128),
            rim=(206, 226, 255), flowers=[(200, 240, 255), (240, 240, 255), (196, 170, 255), (160, 255, 220)])
    sc = Scene("ridge", "The Snowy Ridge", p, rng)
    sc.live(Stars(rng, 260, 250))
    sc.live(Aurora(rng, 0, 160, [((120, 255, 190), (110, 210, 255)), ((190, 140, 255), (255, 150, 220))]))
    moon(sc, 170, 70, 16)

    # far: high snowy peaks
    lay = art.plane()
    tops = art.mountains(lay, rng, 250, 120, sc.col("lav", 0.88), scales=(150, 52, 17), side=p["moon_side"])
    snowcaps(lay, tops, mix(sc.col("leaf2", 0.85), SNOW, 0.6), 220, rng)
    sc.add(lay, 0.88, veil=0.05)
    # a long ridge of small pines
    lay = art.plane()
    tops = art.ridge(lay, rng, 318, 26, sc.col("leaf2", 0.72), scales=(130, 44, 14))
    for x in range(-4, W + 8, 9):
        if rng.random() < 0.75:
            art.pine(lay, rng, x, tops[max(0, min(W, x))] + 4, rng.randint(18, 34), sc.col("leaf3", 0.72),
                     snow=sc.col("leaf2", 0.7), side=p["moon_side"])
    sc.add(lay, 0.72, veil=0.05, low=0.1)
    # nearer: a frozen lake, and taller pines on the slopes either side of it
    lay = art.plane()
    tops = art.ridge(lay, rng, 372, 18, sc.col("leaf2", 0.5), scales=(160, 50, 16))
    for x in list(range(10, 330, 22)) + list(range(640, 960, 22)):
        art.pine(lay, rng, x + rng.randint(-6, 6), tops[max(0, min(W, x))] + 6, rng.randint(48, 84),
                 sc.col("leaf3", 0.5), snow=sc.col("leaf2", 0.45), trunk=sc.col("wood", 0.5), side=p["moon_side"])
    sc.add(lay, 0.5, veil=0.03, low=0.08)
    lay = art.plane()
    ice = sc.col("water", 0.4)
    pygame.draw.ellipse(lay, mix(ice, SNOW, 0.35), (300, 384, 360, 52))
    pygame.draw.ellipse(lay, mix(ice, SNOW, 0.15), (316, 390, 328, 40))
    for i in range(10):  # the aurora and the moon, faint in the ice
        y = 394 + i * 3
        c = mix(mix(ice, SNOW, 0.15), (150, 255, 210) if i % 2 else (200, 160, 255), 0.25)
        pygame.draw.line(lay, c, (380 + rng.randint(-20, 20), y), (580 + rng.randint(-20, 20), y))
    for _ in range(9):  # cracks in the ice
        x, y = rng.randint(340, 620), rng.randint(394, 424)
        for _ in range(rng.randint(6, 16)):
            lay.set_at((x, y), mix(ice, (20, 30, 80), 0.3))
            x += rng.choice((-1, 1, 1))
            y += rng.choice((-1, 0, 0, 1))
    sc.raw(lay)
    sc.lamp(480, 410, 180, GLOW["cyan"], 40)  # something glows under the ice

    # near: deep snow, the path in from the Forest, crystals, and two big snowy firs framing it all
    lay = art.plane()
    art.ridge(lay, rng, 440, 10, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    for _ in range(1400):  # sparkle in the snow
        x, y = rng.randrange(W), rng.randint(436, H - 1)
        lay.set_at((x, y), SNOW if rng.random() < 0.3 else sc.col("leaf", 0.2))
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(984, 486), (840, 480), (700, 466), (580, 452), (500, 446)], [44, 42, 36, 26, 14], earth, edge, rng=rng)
    from kit import exit_spot, trail
    trail(sc, lay, "left", 446)
    trail(sc, lay, "up", 446, 220)
    sc.add(lay, 0.2, texture=0.5)
    lay = art.plane()
    glows = []
    for x, y, n, c in ((180, 476, 6, GLOW["cyan"]), (360, 508, 4, GLOW["violet"]), (650, 520, 5, GLOW["moss"]),
                       (800, 452, 3, GLOW["cyan"]), (90, 452, 3, GLOW["violet"])):
        ice_crystals(sc, lay, x, y, n, c, glows)
    glowmoss(sc, lay, 260, 520, 60, 12, GLOW["cyan"])
    sc.raw(lay)
    sc.live(Pulses(glows, speed=0.8))
    lay = art.plane()
    for x, base, h in ((36, 560, 400), (930, 560, 380)):
        art.pine(lay, rng, x, base, h, sc.col("leaf3", 0.08), snow=sc.col("leaf2", 0.06), trunk=sc.col("wood", 0.08),
                 side=p["moon_side"])
    sc.add(lay, 0.08, texture=0.8)

    # who lives here: the new animals of the snow, out from the start, and a few old friends
    grounds = [(lambda x: 470 + 3 * math.sin(x / 50), (120, 300)), (lambda x: 506 + 3 * math.sin(x / 40), (400, 620)),
               (lambda x: 490 + 2 * math.sin(x / 60), (640, 820))]
    additions(sc, rng, [("cairn", 580, 486), ])
    second_wave(sc, rng, (120, 80, 700, 200), grounds, fliers=("finch", "wisp"), walkers=("fox", "goat", "newt"),
                out=("fox", "goat", "finch"),
                far=[(lambda x: 372 + 3 * math.sin(x / 50), (120, 300)), (lambda x: 378 + 3 * math.sin(x / 45), (660, 860)), (lambda x: 440 + 2 * math.sin(x / 40), (300, 640))])
    sc.live(Slug(rng, Track([(420, 524), (520, 528), (620, 524)]), (200, 210, 250), size=1.4, speed=3,
                 spots=GLOW["cyan"]))
    bugs = sc.live(Fireflies(rng, (0, 200, W, 260), 14, color=GLOW["cyan"], reach=22))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 100, 700, 200), [GLOW["cyan"], GLOW["violet"]])
    sc.live(Snow(rng, (0, 0, W, H), 180))

    sc.spots = [
        Spot("go", (872, 440, 88, 80), "Back to the Forest", "forest", (930, 482), sign=(852, 436)),
        exit_spot("left", "Aurora Peak", "peak", 446), exit_spot("up", "The Frozen Falls", "falls", 446, 220),
    ]
    sc.lower = dict(ground=0.2, props=["pines", "crystals"], fly=GLOW["cyan"], bushes=False,
                    walkers=("fox", "goat", "newt"), fliers=("finch", "wisp"), out=("fox", "finch"))
    return sc.done()


# --- The Hot Springs (beyond the River) ----------------------------------------------------------

EMBER = (255, 150, 80)
SPRING = (110, 236, 226)


def terrace(lay, sc, cx, y, w, rim, water, glows, steam):
    """A pool on a stepped terrace of mineral rock: a pale rim, turquoise water glowing from
    below, ripples, and the lip spilling over the front."""
    face = mix(rim, (60, 30, 70), 0.3)  # the terrace's face below the pool, streaked by mineral drips
    pygame.draw.rect(lay, face, (cx - w // 2 + 2, y + 4, w - 4, 26), border_radius=6)
    for k in range(-w // 2 + 5, w // 2 - 5, 3):
        ln = 8 + (k * 17) % 16
        pygame.draw.line(lay, mix(face, (255, 255, 255), 0.18 if k % 2 else 0.0), (cx + k, y + 8), (cx + k, y + 8 + ln))
    pygame.draw.ellipse(lay, mix(rim, (40, 20, 60), 0.35), (cx - w // 2 - 3, y - 5, w + 6, 22))
    pygame.draw.ellipse(lay, rim, (cx - w // 2 - 3, y - 7, w + 6, 20))
    pygame.draw.ellipse(lay, water, (cx - w // 2 + 2, y - 4, w - 4, 12))
    pygame.draw.ellipse(lay, mix(water, (255, 255, 255), 0.35), (cx - w // 4, y - 2, w // 2, 4), 1)
    for k in range(-w // 2 + 6, w // 2 - 6, 5):  # drips over the lip
        if (k * 7) % 3:
            ln = (k * 13) % 7 + 3
            pygame.draw.line(lay, mix(rim, (255, 255, 255), 0.25), (cx + k, y + 12), (cx + k, y + 12 + ln))
    glows.append((cx, y + 2, w, SPRING, 70, cx * 0.05))
    steam.append((cx, y, w * 0.6))


def build_springs():
    rng = make_rng(66)
    p = pal(sky=[(14, 8, 36), (40, 18, 66), (88, 38, 96), (150, 72, 112)],
            mist=(122, 66, 116), shade=(20, 10, 36), ambient=((255, 224, 236), (112, 72, 124)),
            leaf=(136, 168, 140), leaf2=(150, 116, 146), leaf3=(86, 70, 116), lav=(150, 96, 156),
            stone=(128, 100, 140), earth=(206, 170, 182), earth_edge=(136, 94, 124), water=(80, 210, 210),
            wood=(140, 96, 118), rim=(255, 206, 196), moon_side=1,
            flowers=[(255, 186, 150), (255, 150, 214), (255, 236, 140), (255, 255, 255)])
    sc = Scene("springs", "The Hot Springs", p, rng)
    sc.live(Stars(rng, 160, 220, avoid=lambda x, y: 520 < x < 860))
    moon(sc, 120, 64, 15)

    # far: a sleeping volcano, its crater glowing, a ribbon of lava down its flank
    lay = art.plane()
    art.mountains(lay, rng, 268, 60, sc.col("lav", 0.9), scales=(170, 56, 18), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()
    cone = [(470, 330), (560, 196), (610, 150), (650, 146), (700, 152), (744, 196), (850, 330)]
    art.crag(lay, cone, sc.col("stone", 0.78), 66, side=p["moon_side"], strata=(9, 16))
    pygame.draw.ellipse(lay, mix(EMBER, (60, 20, 40), 0.3), (614, 144, 82, 12))
    pygame.draw.ellipse(lay, (255, 196, 120), (626, 146, 58, 6))
    x, y = 640.0, 156
    while y < 300:  # the lava ribbon
        lay.set_at((int(x), y), (255, 170, 90))
        lay.set_at((int(x) + 1, y), (220, 110, 70))
        if 0 <= int(x) < W:
            sc.emit.set_at((int(x), y), (140, 70, 30))
        x += math.sin(y / 9) * 0.9 - 0.25
        y += 1
    sc.add(lay, 0.78, veil=0.04)
    sc.lamp(655, 150, 140, EMBER, 80)
    sc.lamp(620, 230, 80, EMBER, 40)
    sc.live(Steam(rng, [(655, 140, 40)], n_each=8, color=(200, 170, 200), height=130))
    lay = art.plane()
    art.ridge(lay, rng, 330, 22, sc.col("leaf3", 0.66), scales=(110, 36, 12))
    sc.add(lay, 0.66, veil=0.05, low=0.12)

    # middle: stepped mineral terraces with steaming turquoise pools
    lay = art.plane()
    rim = sc.col("pink2", 0.4)
    glows, steam = [], []
    hill = [(120, 440), (200, 360), (300, 336), (420, 326), (560, 330), (680, 344), (780, 380), (860, 440)]
    art.crag(lay, hill, mix(rim, (60, 30, 70), 0.45), 67, side=p["moon_side"], strata=(5, 9))  # the mineral hill the terraces step down
    for cx, y, w in ((300, 356, 120), (560, 350, 150), (420, 382, 170), (700, 384, 130), (230, 400, 140),
                     (560, 414, 190)):
        terrace(lay, sc, cx, y, w, mix(rim, (255, 255, 255), 0.1 if y < 380 else 0.0), sc.col("water", 0.3), glows,
                steam)
    sc.add(lay, 0.36, texture=0.3)
    sc.live(Pulses(glows, speed=0.6))
    sc.pond = sc.live(Shoal(rng, [(Water(420, 384, 80, 6), 1), (Water(560, 416, 90, 6), 1)], sc.col("water", 0.3), size=0.45))
    for x, y, r, c, st, ph in glows:
        sc.lamp(x, y, r, c, 40)

    # near: warm ash ground, the path from the River, rocks glowing with heat through their cracks
    lay = art.plane()
    art.ridge(lay, rng, 452, 10, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    art.grass_bed(lay, rng, (0, 452, W, 88), sc.col("leaf", 0.2), 900, 5)
    art.flowers(lay, rng, (0, 470, W, 70), p["flowers"], 40)
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(-24, 486), (120, 480), (280, 470), (400, 462), (460, 458)], [44, 42, 36, 26, 14], earth, edge, rng=rng)
    from kit import exit_spot, trail
    trail(sc, lay, "up", 452, 200)  # up to the Lava Lake
    sc.add(lay, 0.2, texture=0.6)
    lay = art.plane()
    hot = []
    art.path(sc.cur, [(984, 470), (900, 466), (820, 460), (790, 458)], [44, 36, 22, 12], earth, edge,
             rng=random.Random(67))  # on to the Glow Shore
    for x, y, w, h in ((690, 506, 90, 40), (900, 526, 70, 32), (600, 512, 50, 22), (90, 520, 60, 24)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.16))
        for _ in range(3):  # cracks with heat glowing through
            cx_, cy_ = x + rng.randint(-w // 3, w // 3), y - rng.randint(4, h - 6)
            for i in range(rng.randint(5, 10)):
                lay.set_at((cx_, cy_), (255, 170, 90))
                if 0 <= cx_ < W and 0 <= cy_ < H:
                    sc.emit.set_at((cx_, cy_), (150, 70, 30))
                cx_ += rng.choice((-1, 0, 1))
                cy_ += 1
        hot.append((x, y - h // 2, w, EMBER, 50, x * 0.1))
    glowmoss(sc, lay, 380, 520, 60, 14, GLOW["amber"])
    sc.add(lay, 0.16, texture=0.6)
    sc.live(Pulses(hot, speed=0.7))
    sc.live(Steam(rng, steam, n_each=4))
    sc.live(Motes(rng, (0, 120, W, 420), 40, EMBER, rise=-18))  # embers drifting up

    pool = (lambda x: 418 + 0 * x, (500, 620))  # the big lower pool: the steambara bathes in it
    grounds = [pool, (lambda x: 500 + 3 * math.sin(x / 40), (480, 700)), (lambda x: 512 + 2 * math.sin(x / 50), (160, 340))]
    additions(sc, rng, [("cairn", 860, 500)])
    second_wave(sc, rng, (120, 80, 700, 180), grounds, fliers=("jelly", "moth"), walkers=("capy", "gecko", "beetle"),
                out=("capy", "gecko", "jelly"),
                far=[(lambda x: 404 + 2 * math.sin(x / 40), (20, 140)), (lambda x: 452 + 2 * math.sin(x / 50), (300, 700))])
    sc.live(Slug(rng, Track([(200, 520), (300, 526), (420, 522)]), (255, 190, 170), size=1.4, speed=3, spots=EMBER))
    bugs = sc.live(Fireflies(rng, (0, 220, W, 260), 16, color=GLOW["amber"], reach=24))
    sc.bugs.append(bugs)
    squids(sc, rng, (120, 100, 600, 200), [GLOW["pink"], GLOW["amber"]])
    front_frame(sc, rng, top=False)

    sc.spots = [
        Spot("go", (0, 440, 88, 80), "Back to the River", "river", (30, 484), sign=(110, 436)),
        Spot("go", (872, 420, 88, 80), "The Glow Shore", "shore", (930, 462), sign=(850, 420)),
        exit_spot("up", "The Lava Lake", "lava", 452, 200),
    ]
    sc.lower = dict(ground=0.18, props=["rocks", "vents"], fly=GLOW["amber"],
                    walkers=("capy", "gecko", "beetle"), fliers=("jelly", "moth"), out=("gecko", "jelly"))
    return sc.done()


# --- The Battle Tower (below the Mossy Rocks) ------------------------------------------------------

def build_tower():
    rng = make_rng(77)
    p = pal(sky=[(10, 8, 40), (28, 20, 78), (60, 40, 120), (110, 70, 160)],
            mist=(96, 74, 150), shade=(14, 10, 44), ambient=((236, 230, 255), (92, 80, 150)))
    sc = Scene("tower", "The Battle Tower", p, rng)
    sc.live(Stars(rng, 240, 260, avoid=lambda x, y: 420 < x < 560))
    moon(sc, 790, 84, 18)

    lay = art.plane()
    art.mountains(lay, rng, 300, 70, sc.col("lav", 0.9), scales=(170, 58, 20), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    art.ridge(lay, rng, 350, 24, sc.col("leaf3", 0.7), scales=(120, 40, 14))
    for x in (60, 150, 260, 700, 820, 910):
        art.trunk(lay, rng, x, 240, 350, 6, sc.col("leaf3", 0.72), branches=1)
        art.foliage(lay, rng, x, 250, 22, 40, sc.col("leaf3", 0.72), p)
    sc.add(lay, 0.7, veil=0.05, low=0.1)

    # the tower: an old stone spire, round windows glowing in pastels, a beacon crystal on top
    lay = art.plane()
    spire = [(424, 440), (432, 300), (444, 170), (456, 96), (472, 64), (488, 64), (504, 96), (516, 170), (528, 300),
             (536, 440)]
    art.crag(lay, spire, sc.col("stone", 0.38), 77, side=p["moon_side"], strata=(10, 18))
    for y in (130, 210, 290, 370):  # a carved band at every floor
        half = 16 + (y - 64) * 0.13
        pygame.draw.line(lay, mix(sc.col("stone", 0.38), (255, 255, 255), 0.18), (480 - half, y), (480 + half, y))
        pygame.draw.line(lay, mix(sc.col("stone", 0.38), (12, 10, 40), 0.35), (480 - half, y + 1), (480 + half, y + 1))
    windows = []
    for i, (wx, wy) in enumerate(((480, 112), (468, 176), (492, 238), (466, 262), (480, 330), (500, 352))):
        c = (GLOW["pink"], GLOW["cyan"], GLOW["violet"], GLOW["amber"], GLOW["moss"], GLOW["pink"])[i]
        pygame.draw.circle(lay, (24, 14, 40), (wx, wy), 6)
        pygame.draw.circle(lay, c, (wx, wy), 4)
        pygame.draw.line(lay, (24, 14, 40), (wx - 4, wy), (wx + 4, wy))
        pygame.draw.line(lay, (24, 14, 40), (wx, wy - 4), (wx, wy + 4))
        windows.append((wx, wy, 40, c, 70, i * 1.3))
        sc.emit.set_at((wx - 2, wy - 2), art.scale(c, 0.8))
    # the door: a tall arch, glowing from within
    pygame.draw.ellipse(lay, (24, 14, 40), (458, 386, 44, 40))
    pygame.draw.rect(lay, (24, 14, 40), (458, 404, 44, 38))
    pygame.draw.ellipse(lay, (255, 210, 236), (464, 392, 32, 30))
    pygame.draw.rect(lay, (255, 210, 236), (464, 406, 32, 36))
    for x in range(466, 496, 4):  # light pouring out across the threshold
        pygame.draw.line(lay, (255, 236, 246), (x, 410), (x, 440))
    # banners either side of the door, in your colours and the challengers'
    for bx, c in ((440, (110, 255, 180)), (520, (255, 150, 214))):
        pygame.draw.line(lay, sc.col("wood", 0.3), (bx, 330), (bx, 440), 2)
        pygame.draw.polygon(lay, c, [(bx, 334), (bx + (12 if bx > 480 else -12), 338), (bx + (10 if bx > 480 else -10), 368),
                                     (bx, 362)])
    sc.add(lay, 0.38, veil=0.02)
    sc.live(Pulses(windows, speed=0.7))
    sc.lamp(480, 420, 120, (255, 190, 230), 90)
    sc.live(Lantern(480, 52, (200, 170, 255), reach=160))  # the beacon crystal
    lay = art.plane()
    pygame.draw.polygon(lay, (220, 200, 255), [(480, 30), (488, 50), (480, 62), (472, 50)])
    pygame.draw.polygon(lay, (255, 255, 255), [(480, 32), (484, 48), (480, 56)])
    sc.raw(lay)
    sc.live(Vines(rng, list(range(440, 524, 9)), lambda x: 170 + abs(x - 480) // 2, (14, 60), sc.col("leaf3", 0.3),
                  sc.col("leaf2", 0.3), flower=p["pink"], glow_tip=GLOW["cyan"]))

    # the plaza: a ring of flagstones before the door, a storage shrine, the path back up
    lay = art.plane()
    art.ridge(lay, rng, 440, 8, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    art.grass_bed(lay, rng, (0, 440, W, 100), sc.col("leaf", 0.18), 1300, 6)
    art.flowers(lay, rng, (0, 470, W, 70), p["flowers"], 50)
    stone = sc.col("stone", 0.2)
    pygame.draw.ellipse(lay, mix(stone, (12, 10, 40), 0.3), (300, 432, 360, 84))
    pygame.draw.ellipse(lay, stone, (306, 434, 348, 76))
    for ring, n in ((0.35, 8), (0.65, 14), (0.95, 22)):  # the joints between the flags
        pygame.draw.ellipse(lay, mix(stone, (12, 10, 40), 0.25), (480 - 174 * ring, 472 - 38 * ring, 348 * ring, 76 * ring), 1)
        for i in range(n):
            a = i / n * math.tau + ring
            x0, y0 = 480 + math.cos(a) * 174 * (ring - 0.3), 472 + math.sin(a) * 38 * (ring - 0.3)
            x1, y1 = 480 + math.cos(a) * 174 * ring, 472 + math.sin(a) * 38 * ring
            pygame.draw.line(lay, mix(stone, (12, 10, 40), 0.25), (x0, y0), (x1, y1))
    earth, edge = sc.col("earth", 0.15), sc.col("earth_edge", 0.15)
    art.path(lay, [(150, 556), (170, 510), (200, 476), (240, 452), (270, 440)], [100, 72, 48, 30, 18], earth, edge, rng=rng)
    sc.add(lay, 0.18, texture=0.5)
    lay = art.plane()  # the shrine: a little stone house of drawers, glowing amber
    sx, sy = 760, 470
    pygame.draw.rect(lay, sc.col("stone", 0.12), (sx - 30, sy - 46, 60, 46))
    pygame.draw.polygon(lay, sc.col("wood", 0.12), [(sx - 38, sy - 46), (sx, sy - 66), (sx + 38, sy - 46)])
    for row in range(2):
        for col in range(3):
            d = pygame.Rect(sx - 26 + col * 18, sy - 40 + row * 18, 16, 16)
            pygame.draw.rect(lay, (255, 214, 140), d, border_radius=2)
            pygame.draw.rect(lay, mix((255, 214, 140), (60, 30, 40), 0.5), d, 1, border_radius=2)
            sc.emit.set_at(d.center, (120, 90, 40))
    sc.add(lay, 0.12, texture=0.4)
    sc.lamp(sx, sy - 24, 90, GLOW["amber"], 80)
    glowmoss(sc, art.plane(), 100, 500, 60, 14)

    additions(sc, rng, [("ring", 860, 500)])
    second_wave(sc, rng, (100, 80, 760, 180), [(lambda x: 500 + 3 * math.sin(x / 50), (300, 640)),
                                              (lambda x: 516 + 2 * math.sin(x / 40), (700, 900))],
                far=[(lambda x: 412 + 2 * math.sin(x / 40), (40, 360)), (lambda x: 414 + 2 * math.sin(x / 45), (820, 940))])
    sc.live(Slug(rng, Track([(580, 520), (680, 524), (800, 520)]), (220, 190, 240), size=1.5, speed=3, spots=GLOW["pink"]))
    bugs = sc.live(Fireflies(rng, (0, 200, W, 280), 24, color=GLOW["pink"]))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 460), 30, GLOW["violet"]))
    squids(sc, rng, (100, 100, 760, 200), [GLOW["violet"], GLOW["pink"]])
    front_frame(sc, rng, top=False)

    door = Spot("tower", (452, 380, 56, 64), "Battle Tower", "tower", (480, 414), sign=(480, 372))
    shrine = Spot("boxes", (726, 404, 68, 70), "Your creatures", "boxes", (760, 440), sign=(760, 392))
    sc.spots = [
        Spot("go", (150, 430, 120, 90), "Back to the Mossy Rocks", "rocks", (210, 470), sign=(250, 424)),
        door, shrine,
    ]
    sc.lower = dict(ground=0.16, props=["rocks"], fly=GLOW["pink"])
    return sc.done()


# --- small additions to the older places (2026-10-27, his ask: more in the existing areas) ------

LANTERN_COLORS = [(255, 190, 120), (255, 150, 200), (190, 170, 255), (150, 240, 220)]


def additions(sc, rng, things):
    """Little things that make a place feel lived in: ("lanterns", x0, y0, x1, y1) a string of paper
    lanterns, ("ring", x, y) a fairy ring of glowing mushrooms, ("cairn", x, y) a stack of stones
    with a glowing rune, ("log", x, y) a hollow mossy log, ("lotus", x, y) a glowing lotus on the
    water. Anything that would sit on a path is left out."""
    lay = art.plane()
    glows = []
    for kind, *a in things:
        if kind != "lanterns" and art.on_path(a[0], a[1]):
            continue
        if kind == "lanterns":
            x0, y0, x1, y1 = a
            n = max(3, int(math.hypot(x1 - x0, y1 - y0) // 28))
            pts = []
            for i in range(n + 1):
                f = i / n
                pts.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f + math.sin(f * math.pi) * 18))
            pygame.draw.lines(lay, (60, 44, 70), False, pts)
            for i, (x, y) in enumerate(pts[1:-1]):
                c = LANTERN_COLORS[i % len(LANTERN_COLORS)]
                pygame.draw.line(lay, (60, 44, 70), (x, y), (x, y + 4))
                pygame.draw.ellipse(lay, mix(c, (40, 20, 50), 0.3), (x - 4, y + 4, 9, 11))
                pygame.draw.ellipse(lay, c, (x - 4, y + 4, 8, 10))
                pygame.draw.line(lay, (60, 44, 70), (x - 2, y + 4), (x + 2, y + 4))
                sc.emit.set_at((round(x), round(y + 9)), art.scale(c, 0.6))
                glows.append((x, y + 9, 40, c, 70, i * 1.1))
        elif kind == "ring":
            x, y = a
            for i in range(7):
                ang = i / 7 * math.tau
                mushroom(lay, round(x + math.cos(ang) * 26), round(y + math.sin(ang) * 7), 3 + i % 2,
                         (200, 150, 255) if i % 2 else (150, 240, 220), sc, glows)
        elif kind == "cairn":
            x, y = a
            stone = sc.col("stone", 0.2)
            for j, (w, h) in enumerate(((22, 9), (17, 8), (13, 7), (8, 6))):
                cy = y - sum(hh for _, hh in ((22, 9), (17, 8), (13, 7), (8, 6))[:j]) - h // 2
                pygame.draw.ellipse(lay, mix(stone, (20, 10, 40), 0.35), (x - w // 2, cy - h // 2 + 1, w, h))
                pygame.draw.ellipse(lay, mix(stone, (255, 255, 255), 0.06 * j), (x - w // 2, cy - h // 2, w, h))
            c = GLOW["cyan"]
            for dy in (-14, -12, -10):
                lay.set_at((x, y + dy), c)
            lay.set_at((x - 1, y - 13), c)
            lay.set_at((x + 1, y - 11), c)
            glows.append((x, y - 12, 50, c, 60, x * 0.03))
        elif kind == "log":
            x, y = a
            bark = sc.col("wood", 0.2)
            pygame.draw.ellipse(lay, mix(bark, (20, 10, 40), 0.4), (x - 40, y - 15, 80, 18))
            pygame.draw.rect(lay, bark, (x - 38, y - 16, 76, 14), border_radius=6)
            for k in range(-34, 34, 6):
                pygame.draw.line(lay, mix(bark, (20, 10, 40), 0.25), (x + k, y - 14), (x + k + 3, y - 4))
            pygame.draw.ellipse(lay, mix(bark, (255, 230, 220), 0.25), (x + 32, y - 17, 10, 16))
            pygame.draw.ellipse(lay, (24, 14, 34), (x + 34, y - 14, 6, 10))
            pygame.draw.ellipse(lay, sc.col("moss", 0.2), (x - 30, y - 19, 44, 6))
            for k, cap in ((-24, GLOW["pink"]), (-10, GLOW["violet"]), (6, GLOW["cyan"])):
                mushroom(lay, x + k, y - 15, 3, cap, sc, glows)
        elif kind == "lotus":
            x, y = a
            pygame.draw.ellipse(lay, (60, 120, 100), (x - 9, y - 2, 18, 6))
            for j in range(6):
                ang = math.pi + j / 5 * math.pi
                tip = (x + math.cos(ang) * 6, y - 2 + math.sin(ang) * 6)
                pygame.draw.polygon(lay, (255, 196, 230) if j % 2 else (255, 224, 240), [(x - 2, y), (x + 2, y), tip])
            pygame.draw.circle(lay, (255, 236, 160), (x, y - 2), 2)
            glows.append((x, y - 3, 44, (255, 180, 220), 70, x * 0.05))
    sc.raw(lay)
    if glows:
        sc.live(Pulses(glows, speed=0.7))


class FallingStars:
    """Now and then a star streaks down the sky (the Starfall Meadow)."""

    def __init__(self, rng):
        self.rng, self.next, self.star = rng, 3.0, None

    def shine(self, s, t):
        if self.star is None and t > self.next:
            self.star = (t, self.rng.uniform(100, 860), self.rng.uniform(30, 160), self.rng.choice((-1, 1)))
            self.next = t + self.rng.uniform(4, 12)
        if self.star is None:
            return
        t0, x, y, d = self.star
        a = (t - t0) / 0.9
        if a > 1:
            self.star = None
            return
        hx, hy = x + d * a * 220, y + a * 110
        for i in range(14):
            f = i / 14
            s.set_at((round(hx - d * f * 50), round(hy - f * 25)), mix((255, 250, 220), (40, 30, 90), f))
        glow(s, hx, hy, 8, (255, 240, 200), 120)


# --- The Crystal Caverns (up from the Waterfall) and the Starfall Meadow (right of it) -------
# (2026-10-27, his picks: two new places for the Forest Dex's page three)

CAVE_CRYSTAL = [(190, 140, 255), (130, 230, 255), (255, 150, 220)]


def crystal(lay, x, y, h, w, color, lean=0.0):
    """One big crystal, faceted: a lit face and a shaded one, a bright edge."""
    tip = (x + lean * h, y - h)
    left, right = (x - w, y), (x + w, y)
    mid = (x + lean * h * 0.3, y - h * 0.15)
    pygame.draw.polygon(lay, mix(color, (30, 20, 60), 0.45), [left, mid, tip])
    pygame.draw.polygon(lay, mix(color, (30, 20, 60), 0.15), [mid, right, tip])
    pygame.draw.line(lay, mix(color, (255, 255, 255), 0.6), mid, tip)


def build_caverns():
    rng = make_rng(91)
    p = pal(sky=[(8, 6, 22), (14, 10, 34), (20, 14, 44), (26, 18, 54)],
            mist=(60, 40, 110), shade=(10, 6, 26), ambient=((200, 190, 255), (60, 44, 110)),
            leaf=(120, 100, 190), leaf2=(150, 130, 210), leaf3=(70, 56, 130), stone=(110, 96, 170),
            earth=(150, 130, 200), earth_edge=(96, 80, 150), water=(70, 110, 220), moss=(130, 230, 220))
    sc = Scene("caverns", "The Crystal Caverns", p, rng)
    rock, rock2 = sc.col("stone", 0.7), sc.col("stone", 0.45)
    # the far wall of the cavern, and its ceiling hung with stalactites
    lay = art.plane()
    pygame.draw.rect(lay, mix(rock, p["shade"], 0.5), (0, 0, W, H))
    art.ridge(lay, rng, 200, 50, rock, scales=(160, 50, 16))
    for _ in range(40):
        x, ln = rng.randint(0, W), rng.randint(20, 90)
        w = rng.randint(6, 18)
        pygame.draw.polygon(lay, mix(rock, p["shade"], 0.3), [(x - w, 0), (x + w, 0), (x + rng.randint(-3, 3), ln)])
    sc.add(lay, 0.8, veil=0.06)
    glows = []
    lay = art.plane()  # far crystals, glowing out of the wall
    for _ in range(14):
        x, y = rng.randint(30, W - 30), rng.randint(230, 330)
        c = rng.choice(CAVE_CRYSTAL)
        crystal(lay, x, y, rng.randint(20, 46), rng.randint(5, 10), mix(c, rock, 0.35), rng.uniform(-0.3, 0.3))
        glows.append((x, y - 20, 60, c, 40, rng.random() * 6))
    sc.add(lay, 0.6, veil=0.03)
    # the middle: rock shelves either side, an underground pool lit from below
    lay = art.plane()
    pygame.draw.polygon(lay, rock2, [(0, 300), (140, 320), (260, 360), (300, 420), (0, 430)])
    pygame.draw.polygon(lay, rock2, [(W, 290), (800, 316), (690, 360), (650, 420), (W, 430)])
    art.ridge(lay, rng, 410, 10, sc.col("stone", 0.3), scales=(120, 40, 14))
    pool = sc.col("water", 0.3)
    pygame.draw.ellipse(lay, mix(pool, (20, 30, 80), 0.3), (300, 400, 360, 60))
    pygame.draw.ellipse(lay, mix(pool, CAVE_CRYSTAL[1], 0.3), (320, 408, 320, 44))
    for i in range(8):
        pygame.draw.arc(lay, mix(pool, (230, 244, 255), 0.3), (360 + i * 14, 414 + (i % 3) * 8, 120, 14), 0.2, 2.8)
    sc.add(lay, 0.4, veil=0.02, texture=0.6)
    sc.lamp(480, 430, 220, CAVE_CRYSTAL[1], 70)
    lay = art.plane()
    up = random.Random(92)
    crack = [(846, 110), (872, 96), (900, 120), (906, 200), (880, 260), (852, 240), (842, 170)]
    pygame.draw.polygon(lay, (24, 22, 70), crack)
    pygame.draw.polygon(lay, (60, 56, 130), crack, 2)
    for _ in range(18):
        sx, sy = up.randint(852, 898), up.randint(110, 236)
        lay.set_at((sx, sy), (240, 240, 255))
    for i in range(9):  # steps cut into the shelf, climbing to it
        x, y = 760 + i * 13, 352 - i * 12
        pygame.draw.rect(lay, mix(rock, (255, 255, 255), 0.12 + 0.04 * (i % 2)), (x - 14, y, 30, 6))
        pygame.draw.rect(lay, mix(rock, p["shade"], 0.4), (x - 14, y + 6, 30, 4))
    sc.raw(lay)
    sc.lamp(876, 180, 120, (200, 200, 255), 60)
    sc.pond = sc.live(Shoal(rng, [(Water(480, 430, 150, 18), 3)], pool, size=0.7))
    # near: the cave floor, a path down to the Waterfall, and great crystal clusters
    lay = art.plane()
    art.ridge(lay, rng, 450, 8, sc.col("stone", 0.2), scales=(120, 40, 14))
    for _ in range(900):
        x, y = rng.randrange(W), rng.randint(450, H - 1)
        lay.set_at((x, y), mix(sc.col("stone", 0.2), (255, 255, 255), rng.uniform(0, 0.2)))
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(470, 470), (474, 510), (480, 560)], [40, 70, 110], earth, edge, rng=rng)
    sc.add(lay, 0.2, texture=0.5)
    lay = art.plane()
    for cx, cy, n, c in ((110, 470, 5, 0), (230, 440, 3, 1), (720, 440, 4, 2), (850, 476, 6, 1), (640, 500, 3, 0)):
        for j in range(n):
            h = rng.randint(24, 70)
            crystal(lay, cx + (j - n / 2) * 12 + rng.randint(-4, 4), cy, h, rng.randint(6, 12), CAVE_CRYSTAL[c],
                    rng.uniform(-0.35, 0.35))
        glows.append((cx, cy - 30, 90, CAVE_CRYSTAL[c], 70, rng.random() * 6))
    sc.raw(lay)
    sc.live(Pulses(glows, speed=0.6))
    for x0, x1 in ((40, 260), (680, 920)):
        sc.live(GlowThreads(rng, list(range(x0, x1, 7)), lambda x: 30 + (x * 7) % 40, (10, 70), CAVE_CRYSTAL[1]))
    sc.live(Motes(rng, (0, 100, W, 380), 60, CAVE_CRYSTAL[0], rise=-6))

    grounds = [(lambda x: 470 + 2 * math.sin(x / 40), (120, 330)), (lambda x: 506 + 3 * math.sin(x / 50), (560, 820)),
               (lambda x: 496 + 2 * math.sin(x / 60), (300, 420))]
    second_wave(sc, rng, (120, 120, 720, 200), grounds, fliers=("hum", "umbra"),
                walkers=("geode", "drip", "lumi", "ferro", "shard", "pebble"), out=("geode", "lumi", "shard", "hum"),
                far=[(lambda x: 318 + 2 * math.sin(x / 40), (40, 230)), (lambda x: 316 + 2 * math.sin(x / 45), (730, 930))])
    sc.live(Slug(rng, Track([(560, 520), (660, 524), (780, 518)]), (170, 150, 230), size=1.4, speed=3, spots=CAVE_CRYSTAL[1]))
    bugs = sc.live(Fireflies(rng, (0, 200, W, 260), 18, color=CAVE_CRYSTAL[1], reach=22))
    sc.bugs.append(bugs)

    sc.spots = [Spot("go", (392, 480, 168, 60), "Back to the Waterfall", "waterfall", (476, 516), sign=(476, 504)),
                Spot("go", (820, 150, 110, 200), "The Cloud Bridge", "bridge", (876, 200), sign=(800, 150))]
    sc.lower = dict(ground=0.12, props=["rocks", "crystals"], fly=CAVE_CRYSTAL[1], bushes=False,
                    walkers=("geode", "drip", "lumi", "ferro", "shard", "pebble"), fliers=("hum", "umbra"),
                    out=("geode", "shard", "hum"))
    return sc.done()


METEOR = (255, 190, 130)


def build_meadow():
    rng = make_rng(64)
    p = pal(sky=[(6, 6, 30), (20, 18, 70), (50, 40, 120), (100, 80, 170)],
            mist=(90, 80, 160), shade=(12, 10, 40), ambient=((240, 236, 255), (90, 84, 160)),
            leaf=(110, 190, 150), leaf2=(150, 214, 160), leaf3=(60, 120, 120),
            flowers=[(255, 236, 160), (255, 200, 230), (200, 180, 255), (255, 255, 255), (160, 240, 255)])
    sc = Scene("meadow", "The Starfall Meadow", p, rng)
    sc.live(Stars(rng, 420, 330))  # the sky is closest here: more stars than anywhere
    sc.live(FallingStars(rng))
    moon(sc, 150, 64, 22)
    lay = art.plane()  # the milky way, a soft band across the sky
    for i in range(1600):
        f = rng.random()
        x = int(f * W)
        y = int(40 + f * 140 + rng.gauss(0, 18))
        if 0 <= y < H:
            lay.set_at((x, y), mix((200, 190, 255), (255, 255, 255), rng.random()))
    sc.raw(lay)
    lay = art.plane()
    art.mountains(lay, rng, 330, 50, sc.col("lav", 0.9), scales=(180, 60, 20), side=p["moon_side"])
    sc.add(lay, 0.9, veil=0.05)
    # rolling hills of tall grass
    for d, y0, amp in ((0.6, 360, 26), (0.4, 400, 20)):
        lay = art.plane()
        art.ridge(lay, rng, y0, amp, sc.col("leaf2", d), scales=(200, 60, 20))
        art.grass_bed(lay, rng, (0, y0 - 10, W, 60), sc.col("leaf", d), 900, 5)
        sc.add(lay, d, veil=0.04, low=0.08)
    # fallen-star stones: dark rocks with a glow in their cracks, a crater ring round the big one
    glows = []
    lay = art.plane()
    for x, y, w, h in ((700, 420, 70, 40), (250, 410, 40, 26), (560, 440, 30, 20)):
        pygame.draw.ellipse(lay, sc.col("earth_edge", 0.3), (x - w, y + h // 2 - 6, w * 2, 14))
        art.rock(lay, rng, x, y, w, h, (90, 70, 100))
        for j in range(4):
            a = rng.random() * math.tau
            pygame.draw.line(lay, METEOR, (x, y), (x + math.cos(a) * w * 0.4, y + math.sin(a) * h * 0.4))
        glows.append((x, y, w * 2, METEOR, 70, rng.random() * 6))
    sc.add(lay, 0.3)
    sc.live(Pulses(glows, speed=0.9))
    # near: the meadow itself, flowers everywhere, the path back to the Waterfall
    lay = art.plane()
    art.ridge(lay, rng, 446, 8, sc.col("leaf2", 0.2), scales=(120, 40, 14))
    art.grass_bed(lay, rng, (0, 446, W, 100), sc.col("leaf", 0.18), 1800, 7)
    art.flowers(lay, rng, (0, 450, W, 90), p["flowers"], 160)
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(-24, 486), (120, 480), (260, 470), (380, 462)], [48, 44, 36, 22], earth, edge, rng=rng)
    from kit import exit_spot, trail
    trail(sc, lay, "up", 446, 600)  # up to the Comet Crater
    sc.add(lay, 0.2, texture=0.5)
    sc.live(Blades(rng, (0, 420, W, 120), 380, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 14, 40, stiff=1.2))
    sc.live(Fireflies(rng, (0, 300, W, 200), 40, color=(255, 236, 160), reach=24))
    sc.live(Motes(rng, (0, 0, W, 480), 50, (255, 240, 200), rise=-8))

    grounds = [(lambda x: 490 + 3 * math.sin(x / 50), (120, 360)), (lambda x: 506 + 3 * math.sin(x / 45), (460, 700)),
               (lambda x: 480 + 2 * math.sin(x / 60), (720, 900))]
    additions(sc, rng, [("ring", 830, 500), ("cairn", 600, 470)])
    second_wave(sc, rng, (100, 60, 760, 220), grounds, fliers=("meteor", "zap", "dream", "wish"),
                walkers=("twinkle", "tuft", "kick", "dust"), out=("twinkle", "tuft", "wish", "dream"),
                far=[(lambda x: 404 + 2 * math.sin(x / 40), (60, 400)), (lambda x: 364 + 2 * math.sin(x / 50), (520, 900))])
    squids(sc, rng, (120, 80, 700, 200), [GLOW["violet"], (255, 236, 160)])
    front_frame(sc, rng, top=False)

    sc.spots = [Spot("go", (0, 430, 96, 90), "Back to the Waterfall", "waterfall", (30, 476), sign=(116, 430)),
                exit_spot("up", "The Comet Crater", "comet", 446, 600)]
    sc.lower = dict(ground=0.2, props=["mushrooms"], fly=(255, 236, 160),
                    walkers=("twinkle", "tuft", "kick", "dust"), fliers=("meteor", "zap", "dream", "wish"),
                    out=("twinkle", "wish"))
    return sc.done()


BUILDERS = {
    "glade": build_glade,
    "waterfall": build_waterfall,
    "river": build_river,
    "forest": build_forest,
    "rocks": build_rocks,
    "ridge": build_ridge,
    "springs": build_springs,
    "tower": build_tower,
    "caverns": build_caverns,
    "meadow": build_meadow,
}

# five more places (2026-10-27, his picks), painted in faraway.py
from faraway import BUILD as _FARAWAY  # noqa: E402
from faraway2 import BUILD as _ROUND1  # noqa: E402
BUILDERS.update(_FARAWAY)
BUILDERS.update(_ROUND1)
from faraway3 import BUILD as _ROUND2  # noqa: E402
BUILDERS.update(_ROUND2)
from faraway4 import BUILD as _ROUND3  # noqa: E402
BUILDERS.update(_ROUND3)
