"""The places in the glade, at night.

Each `build_<place>()` paints one scene back to front and returns a Scene: the
static picture (cached as a few surfaces), the moving things slotted between them,
its light map, and the clickable spots — paths to other places, and objects that
open apps. The moon is up but dim; most of the light comes from things that glow:
moss, mushrooms, crystals, lanterns, fireflies and the little sky-squid.
"""

import math

import pygame

import art
from art import GLOW, H, W, at_depth, mix
from life import (Blades, Critter, Fireflies, GlowThreads, Lantern, Millipede, Motes, Petals, Pulses, River,
                  Shafts, Slug, Squid, Stars, Track, Vines, Waterfall, make_rng)


class Spot:
    """Somewhere you can click: `go` to another place, or `app` to open a program.
    `sign` is where its name board hangs (centre); it is clickable too."""

    def __init__(self, kind, rect, label, target, mark=None, direction=None, sign=None):
        self.kind, self.rect, self.label, self.target = kind, pygame.Rect(rect), label, target
        self.mark = mark or self.rect.center
        self.direction = direction  # which way a path sign points; guessed from position if None
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
        self.parts.append(("still", self.cur))
        self.cur = None
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
            else:
                p.draw(s, t)
        self.lit(s, self.lives, t)

    def update(self, dt):
        if self.critter:
            self.critter.update(dt)


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
        for dx in range(-size + 1, size):
            if 0 <= x + dx < W and 0 <= cy < H:
                sc.emit.set_at((x + dx, cy), art.scale(cap, 0.45))
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
    art.ridge(lay, rng, 300, 68, sc.col("lav", 0.9), scales=(180, 62, 22))
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    pygame.draw.polygon(lay, sc.col("stone", 0.78), [(392, 344), (408, 248), (440, 228), (472, 236), (524, 224),
                                                       (568, 240), (596, 272), (612, 344)])
    art.canopy(lay, rng, 0, 460, 320, sc.col("leaf3", 0.78), r=(10, 20))
    art.canopy(lay, rng, 560, 980, 316, sc.col("leaf3", 0.78), r=(10, 20))
    for x in (68, 140, 300, 660, 820, 904):  # tall distant trees, Rain World-ish verticals
        art.trunk(lay, rng, x, 192, 330, 6, sc.col("leaf3", 0.8), branches=1)
        art.foliage(lay, rng, x, 208, 18, 44, sc.col("leaf3", 0.8), p)
    sc.add(lay, 0.78, veil=0.04)
    lay = art.plane()
    pygame.draw.rect(lay, sc.col("water", 0.6), (494, 228, 16, 112))
    sc.raw(lay)
    sc.live(Waterfall(rng, 494, 510, 228, 336, None, sc.col("water", 0.35), (230, 240, 255)))

    lay = art.plane()
    art.ridge(lay, rng, 356, 20, sc.col("leaf", 0.62), scales=(120, 38, 14))
    sc.add(lay, 0.62, veil=0.04, low=0.14)
    for x in (130, 330, 610, 800):  # faraway moss, glowing through the mist
        sc.lamp(x, 350, 60, GLOW["moss"], 30)

    # mid: forest edges framing left and right
    lay = art.plane()
    for x, w in ((28, 20), (96, 16), (172, 14), (236, 12)):
        art.trunk(lay, rng, x, 40, 392, w, sc.col("wood", 0.5), branches=2, pal=p)
    pygame.draw.rect(lay, sc.col("leaf3", 0.5), (0, 0, 280, 40))
    leaf_row(lay, rng, -20, 292, 52, 44, 32, sc.col("leaf3", 0.5), p, jitter=16)
    for x in (860, 932):
        art.trunk(lay, rng, x, 60, 392, 16, sc.col("wood", 0.5), pal=p)
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
    for cx, cy, rx, ry in ((744, 200, 112, 60), (680, 168, 60, 40), (808, 172, 60, 40), (744, 140, 76, 44),
                           (644, 216, 40, 24), (848, 216, 40, 24)):
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

    sc.live(Shafts([(400, 40, 300, 130, 0.0), (450, 30, 590, 100, 2.4)], (150, 170, 255), alpha=18))
    sc.live(Blades(rng, (0, 412, W, 128), 520, [sc.col("leaf", 0.15), sc.col("leaf2", 0.12), sc.col("leaf3", 0.12)], 6, 18))
    # invertebrates: a slug on the meadow, a glowing one on the mossy rock, a snail up the tree
    sc.live(Slug(rng, Track([(520, 474), (600, 478), (680, 472), (760, 476), (840, 470)]), (214, 170, 222), size=1.5))
    rock_track = sorted((pt for pt in rock_moss if 166 < pt[0] < 220), key=lambda pt: pt[0])
    if len(rock_track) > 2:
        sc.live(Slug(rng, Track([(x, y - 1) for x, y in rock_track]), (120, 150, 230), size=1.2, speed=3,
                     spots=GLOW["cyan"]))
    sc.live(Slug(rng, Track([(758, 404), (757, 360), (756, 300)], up=(1, 0)), (220, 196, 180), size=1.1, speed=2.5,
                 shell=(232, 178, 140)))
    sc.critter = Critter(rng, lambda x: 460 + 6 * math.sin(x / 80), (360, 640))
    sc.live(sc.critter)
    bugs = sc.live(Fireflies(rng, (0, 200, W, 300), 34))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 440), 40, GLOW["cyan"]))
    squids(sc, rng, (120, 60, 720, 260), [GLOW["cyan"], GLOW["pink"], GLOW["violet"]])
    front_frame(sc, rng)

    sc.spots = [
        Spot("go", (0, 352, 92, 92), "The Forest", "forest", (28, 400), sign=(78, 352)),
        Spot("go", (872, 376, 88, 88), "The River", "river", (932, 424), sign=(884, 380)),
        Spot("go", (452, 300, 100, 84), "The Waterfall", "waterfall", (504, 352), direction=(0, -1), sign=(510, 300)),
        Spot("go", (200, 476, 168, 64), "The Mossy Rocks", "rocks", (292, 516), direction=(0, 1), sign=(262, 512)),
        Spot("app", (720, 308, 48, 56), "Files", "files", (742, 336), sign=(744, 290)),
        Spot("app", (312, 380, 56, 68), "Terminal", "terminal", (340, 398), sign=(340, 356)),
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
    art.ridge(lay, rng, 240, 80, sc.col("lav", 0.9), scales=(140, 50, 18))
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
    for x0, x1 in ((404, 428), (532, 556)):  # wet, darker rock beside the falling water
        pygame.draw.rect(lay, mix(stone, p["shade"], 0.3), (x0, 80, x1 - x0, 320))
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
    pygame.draw.polygon(lay, sc.col("water", 0.3), [(428, 88), (532, 88), (540, 388), (420, 388)])
    pygame.draw.ellipse(lay, sc.col("water", 0.2), (200, 372, 560, 88))
    pygame.draw.ellipse(lay, mix(sc.col("water", 0.2), GLOW["cyan"], 0.3), (240, 380, 480, 60))
    sc.raw(lay)
    sc.lamp(480, 410, 260, GLOW["cyan"], 70)  # the pool glows
    cliff_top = lambda x: 96 if 220 < x < 740 else 220  # noqa: E731
    sc.live(Vines(rng, list(range(232, 408, 12)) + list(range(568, 740, 12)) + [140, 156, 176, 784, 800, 820], cliff_top,
                  (20, 100), sc.col("leaf3", 0.3), sc.col("leaf2", 0.3), flower=p["pink"], glow_tip=GLOW["moss"]))
    sc.live(Waterfall(rng, 428, 536, 88, 392, None, sc.col("water", 0.05), (236, 248, 255)))
    sc.live(River(rng, lambda x: 392, lambda x: 444, (248, 712), 110, mix(sc.col("water", 0.1), (255, 255, 255), 0.5),
                  (255, 255, 255), speed=10))
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
    art.path(lay, [(720, 428), (840, 432), (984, 428)], [24, 32, 36], earth, edge, rng=rng)
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
    bugs = sc.live(Fireflies(rng, (0, 260, W, 220), 16, color=GLOW["cyan"], reach=26))
    sc.bugs.append(bugs)
    squids(sc, rng, (80, 120, 800, 220), [GLOW["violet"], GLOW["cyan"]])
    front_frame(sc, rng, top=False)

    sc.spots = [
        Spot("app", (340, 380, 280, 64), "Music", "music", (480, 412), sign=(480, 360)),
        Spot("go", (392, 480, 168, 60), "Back to the Glade", "glade", (468, 516), direction=(0, 1), sign=(470, 506)),
        Spot("go", (864, 388, 96, 80), "The River", "river", (924, 428), sign=(866, 392)),
    ]
    sc.lower = dict(ground=0.2, props=["rocks"], fly=GLOW["cyan"], paths=[dict(
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
    art.ridge(lay, rng, 256, 60, sc.col("lav", 0.9), scales=(180, 60, 20))
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
    art.path(lay, [(192, 472), (120, 428), (80, 408)], [20, 12, 6], earth, edge, rng=rng)
    sc.add(lay, 0.15, texture=0.6)
    lay = art.plane()  # the post the boat is tied to
    pygame.draw.line(lay, sc.col("earth_edge", 0.1), (632, 386), (608, 428))
    pygame.draw.rect(lay, sc.col("wood", 0.1), (604, 412, 8, 32))
    glowmoss(sc, lay, 500, 500, 70, 16)
    glowmoss(sc, lay, 860, 470, 60, 14, GLOW["cyan"])
    glowmoss(sc, lay, 260, 520, 50, 12, GLOW["lime"])
    sc.add(lay, 0.1, texture=0.3)
    for x0, x1 in ((0, 120), (240, 400), (800, 960)):  # reeds in clumps along the bank
        sc.live(Blades(rng, (x0, 404, x1 - x0, 16), (x1 - x0) // 2, [sc.col("leaf", 0.12), sc.col("leaf3", 0.12)],
                       16, 40, stiff=1.3))
    sc.live(Slug(rng, Track([(320, 506), (420, 512), (520, 508), (640, 514), (760, 506)]), (230, 200, 120), size=1.6,
                 speed=4))
    bugs = sc.live(Fireflies(rng, (0, 220, W, 220), 30))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 400), 30, GLOW["cyan"]))
    squids(sc, rng, (100, 120, 760, 200), [GLOW["pink"], GLOW["cyan"], GLOW["lime"]])
    front_frame(sc, rng, top=True, right=False)

    sc.spots = [
        Spot("go", (0, 428, 88, 92), "Back to the Glade", "glade", (28, 476), sign=(104, 444)),
        Spot("go", (44, 384, 92, 44), "The Waterfall", "waterfall", (84, 408), direction=(-1, 0), sign=(104, 384)),
        Spot("app", (620, 350, 156, 60), "Games", "games", (700, 388), sign=(700, 330)),
    ]
    sc.lower = dict(ground=0.18, props=["rocks"], fly=GLOW["firefly"])
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
    art.path(lay, [(600, 448), (400, 452), (180, 444), (-24, 440)], [36, 36, 32, 28], earth, edge, rng=rng)
    sc.add(lay, 0.2, texture=0.6)

    # a ring of glowing mushrooms, and more scattered about
    lay = art.plane()
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
    glowmoss(sc, lay, 300, 476, 80, 18, GLOW["moss"], strength=50, specks=0.5)
    glowmoss(sc, lay, 640, 470, 50, 12, GLOW["lime"])
    sc.add(lay, 0.12, texture=0)
    sc.live(Pulses(ring, speed=1.0))
    sc.live(Blades(rng, (0, 424, W, 116), 400, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1), sc.col("leaf2", 0.1)], 8, 24))
    sc.live(Millipede(rng, Track([(760, 486), (720, 470), (700, 440), (690, 380)], up=(1, -0.3)), (90, 60, 110),
                      GLOW["cyan"]))
    sc.live(Slug(rng, Track([(140, 512), (240, 518), (360, 512), (480, 520)]), (250, 220, 130), size=1.6, speed=4))
    sc.live(Slug(rng, Track([(66, 500), (64, 440), (62, 380)], up=(1, 0)), (140, 120, 220), size=1.3, speed=2,
                 spots=GLOW["pink"]))
    bugs = sc.live(Fireflies(rng, (0, 140, W, 360), 56, color=GLOW["lime"]))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 460), 70, GLOW["moss"]))
    squids(sc, rng, (120, 100, 700, 240), [GLOW["cyan"], GLOW["pink"]])
    front_frame(sc, rng)

    sc.spots = [
        Spot("go", (872, 428, 88, 92), "Back to the Glade", "glade", (932, 480), sign=(864, 424)),
        Spot("go", (0, 396, 88, 84), "The Mossy Rocks", "rocks", (28, 440), sign=(96, 404)),
        Spot("app", (232, 428, 140, 60), "Web Browser", "browser", (300, 460), sign=(300, 404)),
    ]
    sc.lower = dict(ground=0.2, props=["mushrooms"], fly=GLOW["lime"])
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
    art.ridge(lay, rng, 280, 72, sc.col("lav", 0.9), scales=(160, 54, 18))
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()  # distant stone spires, moss glowing on their tops
    for x, top, w in ((120, 140, 36), (220, 192, 24), (744, 120, 44), (840, 180, 28), (908, 220, 20)):
        pygame.draw.polygon(lay, sc.col("stone", 0.72), [(x - w // 2, 360), (x - w // 3, top + 12), (x, top),
                                                           (x + w // 3, top + 16), (x + w // 2, 360)])
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
    art.path(lay, [(484, 556), (500, 500), (620, 476), (760, 456), (848, 444)], [92, 68, 44, 24, 12], earth, edge, rng=rng)
    art.path(lay, [(500, 500), (300, 492), (120, 484), (-24, 480)], [60, 44, 36, 32], earth, edge, rng=rng)
    near_moss = []
    for x in (260, 720, 800, 320):
        art.rock(lay, rng, x, 480 + rng.randint(0, 40), rng.randint(28, 52), rng.randint(12, 20),
                 sc.col("stone", 0.1), moss=sc.col("moss", 0.1), glow_pts=near_moss)
    sc.add(lay, 0.12, texture=0.6)
    moss_glow(sc, near_moss, strength=50)
    lay = art.plane()
    glowmoss(sc, lay, 80, 500, 70, 16)
    glowmoss(sc, lay, 900, 500, 60, 16, GLOW["cyan"])
    glowmoss(sc, lay, 640, 520, 50, 12, GLOW["lime"])
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
                                          (520, 620, (236, 190, 120), None, None, 1.5),
                                          (300, 400, (210, 190, 200), None, (180, 150, 230), 1.3)):
        pts = crest(lo, hi)
        if len(pts) > 3:
            sc.live(Slug(rng, Track([(x, y - 1) for x, y in pts]), body, size=sz, speed=2.5, spots=spots, shell=shell))
    sc.live(Slug(rng, Track([(600, 524), (700, 520), (800, 528), (900, 522)]), (200, 120, 200), size=1.6, speed=4,
                 spots=GLOW["violet"]))
    bugs = sc.live(Fireflies(rng, (0, 180, W, 300), 26, color=GLOW["pink"]))
    sc.bugs.append(bugs)
    sc.live(Motes(rng, (0, 0, W, 460), 50, GLOW["moss"]))
    squids(sc, rng, (100, 80, 760, 220), [GLOW["violet"], GLOW["cyan"], GLOW["pink"]])
    front_frame(sc, rng, left=False)

    sc.spots = [
        Spot("go", (768, 412, 128, 64), "Back to the Glade", "glade", (840, 440), sign=(840, 404)),
        Spot("go", (0, 436, 88, 84), "The Forest", "forest", (28, 480), sign=(96, 436)),
        Spot("app", (436, 384, 96, 76), "Discord", "discord", (484, 428), sign=(484, 372)),
        Spot("app", (140, 292, 76, 164), "Code Editor", "code", (178, 366), sign=(178, 270)),
    ]
    sc.lower = dict(ground=0.14, props=["rocks"], fly=GLOW["pink"], paths=[dict(
        pts=[(408, -4), (406, 60), (396, 180), (386, 300), (380, 460)], widths=[86, 96, 112, 128, 144],
        sign=(504, 344), spot=((280, 220, 220, 230), "Back to the Glade", "glade", (384, 408)))])
    return sc.done()


BUILDERS = {
    "glade": build_glade,
    "waterfall": build_waterfall,
    "river": build_river,
    "forest": build_forest,
    "rocks": build_rocks,
}
