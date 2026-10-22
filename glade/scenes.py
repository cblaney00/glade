"""The places in the glade.

Each `build_<place>()` paints one scene back to front and returns a Scene: the
static picture (cached as a few surfaces), the moving things slotted between them,
and the clickable spots — paths to other places, and objects that open apps.
"""

import math

import pygame

import art
from art import H, W, at_depth, mix
from life import (Blades, Bugs, Critter, Lantern, Motes, Petals, River, Shafts, Vines,
                  Waterfall, make_rng)


class Spot:
    """Somewhere you can click: `go` to another place, or `app` to open a program."""

    def __init__(self, kind, rect, label, target, mark=None, direction=None):
        self.kind, self.rect, self.label, self.target = kind, pygame.Rect(rect), label, target
        self.mark = mark or self.rect.center
        self.direction = direction  # which way a path arrow points; guessed from position if None


class Scene:
    def __init__(self, key, title, pal, rng):
        self.key, self.title, self.pal, self.rng = key, title, pal, rng
        self.parts = []
        self.spots = []
        self.critter = None
        self.bugs = []
        self.cur = art.sky(pal)

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
        self.parts.append(("still", self.cur))
        self.parts.append(("live", thing))
        self.cur = art.plane()

    def done(self):
        self.parts.append(("still", self.cur))
        self.cur = None
        return self

    # running ----------------------------------------------------------------------
    def draw(self, s, t):
        for kind, p in self.parts:
            if kind == "still":
                s.blit(p, (0, 0))
            else:
                p.draw(s, t)

    def update(self, dt):
        if self.critter:
            self.critter.update(dt)


# --- shared palette pieces ------------------------------------------------------------

BASE = dict(
    leaf=(92, 196, 170), leaf2=(132, 220, 152), leaf3=(70, 160, 170), lav=(166, 146, 232),
    pink=(255, 158, 210), pink2=(255, 196, 228), stone=(172, 160, 222), moss=(112, 214, 128),
    earth=(255, 214, 178), earth_edge=(222, 156, 150), water=(124, 204, 250), wood=(186, 118, 132),
    wood2=(222, 160, 150), flowers=[(255, 140, 200), (255, 232, 110), (196, 150, 255), (255, 255, 255),
                                     (130, 226, 255), (255, 176, 140)],
)


def pal(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def leaf_row(lay, rng, x0, x1, y, rx, ry, color, p, jitter=5, step=None):
    """A row of foliage masses — a canopy edge or a hedge."""
    x = x0
    while x < x1:
        art.foliage(lay, rng, x, y + rng.randint(-jitter, jitter), rx * rng.uniform(0.8, 1.2), ry, color, p)
        x += step or int(rx * 1.1)


def sun(scene, x, y, r=70):
    s = art.plane()
    art.glow(s, x, y, r, scene.pal["light"], 70)
    art.glow(s, x, y, r // 3, (255, 255, 255), 60)
    scene.cur.blit(s, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def front_frame(scene, rng, left=True, right=True, top=True, vines=True):
    """Close-up foliage framing the corners — darkest, nearest, like Rain World's foreground."""
    lay = art.plane()
    c, c2 = scene.col("leaf3", 0.02), scene.col("leaf", 0.05)
    p = scene.pal
    if left:
        art.foliage(lay, rng, 10, 266, 44, 24, c, p)
        art.foliage(lay, rng, 30, 252, 26, 16, c2, p)
    if right:
        art.foliage(lay, rng, 470, 268, 46, 20, c, p)
        art.foliage(lay, rng, 452, 262, 20, 12, c2, p)
    if top:
        pygame.draw.rect(lay, c, (0, 0, 140, 5))
        leaf_row(lay, rng, -6, 150, 6, 16, 10, c, p, jitter=3)
        pygame.draw.rect(lay, c, (370, 0, 110, 3))
        leaf_row(lay, rng, 366, 490, 3, 13, 8, c, p, jitter=2)
    scene.add(lay, 0.02, texture=1.5)
    if top and vines:
        tops = lambda x: 14 if x < 150 else 9  # noqa: E731
        xs = list(range(6, 146, 9)) + list(range(366, 478, 13))
        scene.live(Vines(rng, xs, tops, (10, 44), scene.col("leaf3", 0.03), scene.col("leaf2", 0.05),
                         flower=scene.pal["pink"]))


# --- The Glade (home) ---------------------------------------------------------------------

def build_glade():
    rng = make_rng(11)
    p = pal(sky=[(146, 184, 255), (194, 188, 255), (255, 204, 232), (255, 232, 214)],
            mist=(255, 220, 232), light=(255, 248, 220), shade=(58, 52, 120))
    sc = Scene("glade", "The Glade", p, rng)
    sun(sc, 318, 62, 90)

    # far: lavender hills and a little cliff with the waterfall far away
    lay = art.plane()
    art.ridge(lay, rng, 150, 34, sc.col("lav", 0.9), scales=(90, 31, 11))
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    pygame.draw.polygon(lay, sc.col("stone", 0.78), [(196, 172), (204, 124), (220, 114), (236, 118), (262, 112),
                                                       (284, 120), (298, 136), (306, 172)])
    art.canopy(lay, rng, 0, 230, 160, sc.col("leaf3", 0.78), r=(5, 10))
    art.canopy(lay, rng, 280, 490, 158, sc.col("leaf3", 0.78), r=(5, 10))
    for x in (34, 70, 150, 330, 410, 452):  # tall distant trees, Rain World-ish verticals
        art.trunk(lay, rng, x, 96, 165, 3, sc.col("leaf3", 0.8), branches=1)
        art.foliage(lay, rng, x, 104, 9, 22, sc.col("leaf3", 0.8), p)
    sc.add(lay, 0.78, veil=0.04)
    lay = art.plane()
    pygame.draw.rect(lay, sc.col("water", 0.6), (247, 114, 8, 56))
    sc.raw(lay)
    sc.live(Waterfall(rng, 247, 255, 114, 168, None, sc.col("water", 0.35), (255, 255, 255)))

    lay = art.plane()
    art.ridge(lay, rng, 178, 10, sc.col("leaf", 0.62), scales=(60, 19, 7))
    sc.add(lay, 0.62, veil=0.04, low=0.14)

    # mid: forest edges framing left and right
    lay = art.plane()
    for x, w in ((14, 10), (48, 8), (86, 7), (118, 6)):
        art.trunk(lay, rng, x, 20, 196, w, sc.col("wood", 0.5), branches=2)
    pygame.draw.rect(lay, sc.col("leaf3", 0.5), (0, 0, 140, 20))
    leaf_row(lay, rng, -10, 146, 26, 22, 16, sc.col("leaf3", 0.5), p, jitter=8)
    for x in (430, 466):
        art.trunk(lay, rng, x, 30, 196, 8, sc.col("wood", 0.5))
    pygame.draw.rect(lay, sc.col("leaf3", 0.5), (404, 0, 80, 30))
    leaf_row(lay, rng, 404, 490, 36, 20, 16, sc.col("leaf3", 0.5), p, jitter=8)
    art.canopy(lay, rng, -10, 150, 194, sc.col("leaf", 0.5), r=(6, 12))
    art.canopy(lay, rng, 410, 490, 196, sc.col("leaf", 0.5), r=(6, 12))
    leaf_row(lay, rng, -10, 150, 188, 12, 8, sc.col("leaf", 0.5), p)
    leaf_row(lay, rng, 410, 490, 190, 12, 8, sc.col("leaf", 0.5), p)
    sc.add(lay, 0.5, veil=0.04, low=0.1)

    # near: the meadow, the paths, the signpost
    lay = art.plane()
    art.ridge(lay, rng, 200, 5, sc.col("leaf2", 0.3), scales=(80, 30, 12))
    art.grass_bed(lay, rng, (0, 196, W, 74), sc.col("leaf", 0.25), 900, 3)
    art.flowers(lay, rng, (0, 204, W, 66), p["flowers"], 130)
    sc.add(lay, 0.3)
    lay = art.plane()
    earth, edge = sc.col("earth", 0.25), sc.col("earth_edge", 0.25)
    art.path(lay, [(240, 214), (246, 202), (250, 190), (252, 180)], [26, 15, 8, 4], earth, edge)
    art.path(lay, [(240, 214), (170, 211), (100, 206), (30, 202), (-12, 201)], [26, 21, 17, 14, 13], earth, edge)
    art.path(lay, [(240, 214), (320, 217), (400, 213), (492, 215)], [26, 22, 20, 18], earth, edge)
    art.path(lay, [(240, 214), (204, 234), (160, 256), (130, 278)], [26, 34, 42, 50], earth, edge)
    pygame.draw.ellipse(lay, edge, (208, 206, 66, 20))
    pygame.draw.ellipse(lay, earth, (209, 205, 64, 18))
    # a few mossy rocks by the path down to the Mossy Rocks
    for x, y, w, h in ((96, 238, 30, 13), (70, 246, 20, 9), (190, 262, 24, 10), (60, 228, 14, 6)):
        art.rock(lay, rng, x, y, w, h, sc.col("stone", 0.2), moss=sc.col("moss", 0.18), mossiness=0.7)
    # signpost
    wood, wood2 = sc.col("wood", 0.22), sc.col("wood2", 0.22)
    pygame.draw.rect(lay, wood, (238, 182, 4, 32))
    for y, dx, w in ((184, -1, 22), (192, 1, 20), (200, -1, 18)):
        x = 240 if dx > 0 else 240 - w
        pygame.draw.rect(lay, wood2, (x, y, w, 5))
        tip = x + w if dx > 0 else x
        pygame.draw.polygon(lay, wood2, [(tip, y), (tip + dx * 3, y + 2), (tip, y + 4)])
        pygame.draw.line(lay, wood, (x + 2, y + 2), (x + w - 3, y + 2))
    # stump with a lantern on it
    pygame.draw.ellipse(lay, wood, (160, 212, 20, 12))
    pygame.draw.rect(lay, wood, (161, 206, 18, 11))
    pygame.draw.ellipse(lay, wood2, (160, 202, 20, 8))
    pygame.draw.rect(lay, sc.col("wood", 0.1), (167, 196, 6, 7))
    pygame.draw.rect(lay, (255, 240, 180), (168, 197, 4, 5))
    pygame.draw.line(lay, sc.col("wood", 0.1), (170, 193), (170, 196))
    sc.add(lay, 0.22, texture=0.4)
    sc.live(Lantern(170, 199, (255, 200, 120)))

    # the big blossom tree
    lay = art.plane()
    art.trunk(lay, rng, 372, 96, 206, 13, sc.col("wood", 0.28), branches=3)
    pygame.draw.ellipse(lay, sc.col("shade", 0.1), (366, 160, 11, 16))  # the hollow
    sc.add(lay, 0.28, texture=0.8)
    lay = art.plane()
    for cx, cy, rx, ry in ((372, 100, 56, 30), (340, 84, 30, 20), (404, 86, 30, 20), (372, 70, 38, 22),
                           (322, 108, 20, 12), (424, 108, 20, 12)):
        art.foliage(lay, rng, cx, cy, rx, ry, sc.col("pink", 0.32), p, leaf=(3, 5))
    mask = pygame.mask.from_surface(lay)
    art.blossoms(lay, rng, (300, 40, 150, 100), [(255, 255, 255), (255, 220, 240), (255, 120, 190)], 260, mask)
    sc.add(lay, 0.3)
    sc.live(Petals(rng, (310, 70, 130, 40), 230, 40, [(255, 200, 230), (255, 255, 255), (255, 150, 200)]))

    sc.live(Shafts([(330, 40, 250, 70, 0.0), (390, 30, 330, 60, 2.0), (280, 20, 170, 50, 4.0)], p["light"]))
    sc.live(Blades(rng, (0, 206, W, 64), 300, [sc.col("leaf", 0.15), sc.col("leaf2", 0.12), sc.col("leaf3", 0.12)], 3, 9))
    sc.critter = Critter(rng, lambda x: 230 + 3 * math.sin(x / 40), (180, 320))
    sc.live(sc.critter)
    bugs = Bugs(rng, [(90, 150), (130, 120), (60, 110), (420, 150), (300, 160), (200, 140)], (255, 236, 150))
    sc.bugs.append(bugs)
    sc.live(bugs)
    sc.live(Motes(rng, (0, 0, W, 220), 70, (255, 252, 230)))
    front_frame(sc, rng)

    sc.spots = [
        Spot("go", (0, 176, 46, 46), "The Forest", "forest", (14, 200)),
        Spot("go", (436, 188, 44, 44), "The River", "river", (466, 212)),
        Spot("go", (226, 150, 50, 42), "The Waterfall", "waterfall", (252, 176)),
        Spot("go", (100, 238, 84, 32), "The Mossy Rocks", "rocks", (146, 258)),
        Spot("app", (360, 154, 24, 28), "Files", "files", (371, 168)),
        Spot("app", (156, 190, 28, 34), "Terminal", "terminal", (170, 199)),
    ]
    sc.lower = dict(ground=0.3, pond=(270, 128, 112, 66), paths=[dict(
        pts=[(101, -2), (90, 8), (80, 30), (78, 60), (86, 95), (102, 130), (110, 170), (104, 230)],
        widths=[47, 49, 52, 56, 60, 64, 68, 74],
        sign=(160, 196), spot=((60, 150, 120, 75), "The Mossy Rocks", "rocks", (106, 206)))])
    return sc.done()


# --- The Waterfall ----------------------------------------------------------------------

def build_waterfall():
    rng = make_rng(22)
    p = pal(sky=[(156, 206, 255), (186, 212, 255), (220, 228, 255), (244, 236, 255)],
            mist=(230, 236, 255), light=(255, 250, 232), shade=(52, 58, 124))
    sc = Scene("waterfall", "The Waterfall", p, rng)
    sun(sc, 120, 40, 80)

    lay = art.plane()
    art.ridge(lay, rng, 120, 40, sc.col("lav", 0.9), scales=(70, 25, 9))
    sc.add(lay, 0.9, veil=0.05)
    lay = art.plane()
    art.ridge(lay, rng, 150, 30, sc.col("leaf3", 0.72), scales=(50, 17, 6))
    sc.add(lay, 0.72, veil=0.05, low=0.1)

    # rainbow in the spray
    lay = art.plane()
    for i, c in enumerate([(255, 140, 170), (255, 200, 140), (255, 246, 150), (150, 240, 170), (140, 200, 255), (190, 160, 255)]):
        pygame.draw.circle(lay, (*c, 46), (240, 250), 170 - i * 3, 3)
    sc.raw(lay)

    # the cliff: a ragged outline, stone strata clipped to it, mossy ledges
    stone = sc.col("stone", 0.42)
    outline = [(40, 200)]
    for i, (x, y) in enumerate(((60, 170), (78, 150), (84, 120), (100, 104), (108, 70), (124, 56), (150, 50),
                                (180, 44), (212, 40))):
        outline.append((x + rng.randint(-3, 3), y + rng.randint(-3, 3)))
    for i, (x, y) in enumerate(((268, 40), (300, 42), (330, 48), (356, 54), (372, 76), (380, 100), (398, 116),
                                (404, 146), (420, 166), (440, 200))):
        outline.append((x + rng.randint(-3, 3), y + rng.randint(-3, 3)))
    lay = art.plane()
    pygame.draw.polygon(lay, stone, outline)
    y = 52
    while y < 196:
        h = rng.randint(9, 18)
        band = mix(stone, sc.col("lav", 0.3), rng.uniform(0, 0.55))
        edge = [(x, y + int(2 * math.sin(x / 11 + y) + math.sin(x / 4.3))) for x in range(30, 451, 4)]
        pygame.draw.polygon(lay, band, edge + [(450, y + h), (30, y + h)])
        pygame.draw.lines(lay, sc.col("stone", 0.24), False, [(x, yy + h) for x, yy in edge])
        # moss along the ledge: strips with little drips
        x = 30 + rng.randint(0, 20)
        while x < 450:
            ln = rng.randint(6, 22)
            if not (200 < x + ln and x < 280):
                for xx in range(x, x + ln):
                    yy = y + h - 1 + int(2 * math.sin(xx / 11 + y) + math.sin(xx / 4.3))
                    lay.set_at((xx, yy), sc.col("moss", 0.3))
                    lay.set_at((xx, yy - 1), mix(sc.col("moss", 0.3), p["light"], 0.4))
                    if rng.random() < 0.2:
                        pygame.draw.line(lay, sc.col("moss", 0.34), (xx, yy), (xx, yy + rng.randint(1, 4)))
            x += ln + rng.randint(10, 34)
        y += h
    for x0, x1 in ((202, 214), (266, 278)):  # wet, darker rock beside the falling water
        pygame.draw.rect(lay, mix(stone, p["shade"], 0.3), (x0, 40, x1 - x0, 160))
    clip = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(clip, (255, 255, 255, 255), outline)
    lay.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    tops = [pt for pt in outline[1:-1] if not 200 < pt[0] < 280]
    for (x, y) in tops:
        art.foliage(lay, rng, x, y + 2, 12, 6, sc.col("leaf", 0.4), p)
    sc.add(lay, 0.42, veil=0.02)
    lay = art.plane()
    pygame.draw.polygon(lay, sc.col("water", 0.3), [(214, 44), (266, 44), (270, 194), (210, 194)])
    pygame.draw.ellipse(lay, sc.col("water", 0.2), (100, 186, 280, 44))
    pygame.draw.ellipse(lay, mix(sc.col("water", 0.2), p["light"], 0.3), (120, 190, 240, 30))
    sc.raw(lay)
    cliff_top = lambda x: 48 if 110 < x < 370 else 110  # noqa: E731
    sc.live(Vines(rng, list(range(116, 204, 7)) + list(range(284, 370, 7)) + [70, 78, 88, 392, 400, 410], cliff_top, (10, 50),
                  sc.col("leaf3", 0.3), sc.col("leaf2", 0.3), flower=p["pink"]))
    sc.live(Waterfall(rng, 214, 268, 44, 196, None, sc.col("water", 0.05), (255, 255, 255)))
    sc.live(River(rng, lambda x: 196, lambda x: 222, (124, 356), 60, mix(sc.col("water", 0.1), (255, 255, 255), 0.6),
                  (255, 255, 255), speed=5))
    sc.live(Motes(rng, (190, 150, 100, 60), 40, (255, 255, 255), rise=-8))

    # banks, mossy rocks, the path down
    lay = art.plane()
    art.ridge(lay, rng, 232, 6, sc.col("leaf2", 0.22), scales=(50, 17, 6))
    pygame.draw.polygon(lay, sc.col("leaf2", 0.22), [(0, 270), (0, 200), (90, 196), (110, 230), (0, 270)])
    pygame.draw.polygon(lay, sc.col("leaf2", 0.22), [(480, 270), (480, 196), (390, 196), (370, 230), (480, 270)])
    art.grass_bed(lay, rng, (0, 196, W, 74), sc.col("leaf", 0.2), 600, 3)
    art.flowers(lay, rng, (0, 230, W, 40), p["flowers"], 60)
    earth, edge = sc.col("earth", 0.18), sc.col("earth_edge", 0.18)
    art.path(lay, [(240, 228), (236, 246), (232, 278)], [30, 40, 54], earth, edge)
    art.path(lay, [(360, 214), (420, 216), (492, 214)], [12, 16, 18], earth, edge)
    sc.add(lay, 0.2)
    lay = art.plane()
    art.rock(lay, rng, 140, 212, 56, 24, sc.col("stone", 0.25), moss=sc.col("moss", 0.2))
    art.rock(lay, rng, 104, 218, 34, 16, sc.col("stone", 0.2), moss=sc.col("moss", 0.18))
    art.rock(lay, rng, 344, 214, 62, 28, sc.col("stone", 0.25), moss=sc.col("moss", 0.2))
    art.rock(lay, rng, 300, 222, 26, 12, sc.col("stone", 0.2), moss=sc.col("moss", 0.18), mossiness=0.8)
    sc.add(lay, 0.2)
    sc.live(Blades(rng, (0, 196, 110, 70), 90, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 6, 16, stiff=1.4))
    sc.live(Blades(rng, (370, 196, 110, 70), 90, [sc.col("leaf", 0.1), sc.col("leaf2", 0.1)], 6, 16, stiff=1.4))
    bugs = Bugs(rng, [(80, 160), (400, 150), (170, 120), (320, 110)], (180, 240, 255))
    sc.bugs.append(bugs)
    sc.live(bugs)
    front_frame(sc, rng, top=False)

    sc.spots = [
        Spot("app", (170, 190, 140, 32), "Music", "music", (240, 206)),
        Spot("go", (196, 240, 84, 30), "Back to the Glade", "glade", (234, 258)),
        Spot("go", (432, 194, 48, 40), "The River", "river", (462, 214)),
    ]
    sc.lower = dict(ground=0.2, props=["rocks"], bug=(180, 240, 255), paths=[dict(
        pts=[(193, -2), (191, 30), (187, 80), (182, 140), (177, 230)], widths=[51, 55, 60, 66, 74],
        sign=(240, 172), spot=((130, 110, 120, 115), "Back to the Glade", "glade", (180, 204)))])
    return sc.done()


# --- The River ------------------------------------------------------------------------------

def build_river():
    rng = make_rng(33)
    p = pal(sky=[(150, 194, 255), (188, 206, 255), (255, 212, 226), (255, 234, 212)],
            mist=(255, 226, 228), light=(255, 246, 214), shade=(50, 60, 114))
    sc = Scene("river", "The River", p, rng)
    sun(sc, 380, 50, 90)

    lay = art.plane()
    art.ridge(lay, rng, 128, 30, sc.col("lav", 0.9), scales=(90, 30, 10))
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()
    art.canopy(lay, rng, -10, 490, 140, sc.col("leaf3", 0.72), r=(6, 12))
    sc.add(lay, 0.72, veil=0.05, low=0.08)

    # far bank, with a willow
    lay = art.plane()
    art.ridge(lay, rng, 158, 4, sc.col("leaf2", 0.5), scales=(60, 20, 8))
    art.trunk(lay, rng, 300, 92, 156, 7, sc.col("wood", 0.5), branches=2)
    art.foliage(lay, rng, 300, 96, 36, 16, sc.col("leaf", 0.5), p)
    for x in (70, 120, 410):
        art.foliage(lay, rng, x, 142, 16, 12, sc.col("leaf", 0.55), p)
    sc.add(lay, 0.5, veil=0.03)
    sc.live(Vines(rng, range(272, 330, 4), lambda x: 96 + abs(x - 300) // 3, (24, 52),
                  sc.col("leaf", 0.45), sc.col("leaf2", 0.45)))

    # the water
    top = lambda x: 160 + 2 * math.sin(x / 50)  # noqa: E731
    bot = lambda x: 206 + 3 * math.sin(x / 70 + 1)  # noqa: E731
    lay = art.plane()
    pygame.draw.polygon(lay, sc.col("water", 0.35), [(0, top(0))] + [(x, top(x)) for x in range(0, W + 1, 8)]
                        + [(x, bot(x)) for x in range(W, -1, -8)])
    # sky reflected in bands
    for y in range(158, 210):
        if y % 7 < 2:
            pygame.draw.line(lay, mix(sc.col("water", 0.35), p["sky"][2], 0.35), (0, y), (W, y))
    sc.raw(lay)
    lay = art.plane()  # lily pads and stepping stones
    for _ in range(14):
        x, y = rng.randint(30, 200), rng.randint(176, 202)
        r = 2 + (y - 170) // 9
        pygame.draw.ellipse(lay, sc.col("leaf2", 0.25), (x, y, r * 2 + 2, r))
        if rng.random() < 0.4:
            lay.set_at((x + r, y), p["pink"])
            lay.set_at((x + r + 1, y), (255, 255, 255))
    for x, y, w in ((150, 176, 12), (180, 186, 16), (214, 196, 20)):
        art.rock(lay, rng, x, y, w, w // 3, sc.col("stone", 0.3), moss=sc.col("moss", 0.3), mossiness=0.6)
    sc.add(lay, 0.28, texture=0.5)
    sc.live(River(rng, top, bot, (0, W), 120, mix(sc.col("water", 0.3), (255, 255, 255), 0.45), (255, 255, 255)))
    lay = art.plane()  # the little boat, tied up at the bank
    wood, wood2 = sc.col("wood", 0.12), sc.col("wood2", 0.12)
    pygame.draw.ellipse(lay, mix(sc.col("water", 0.3), p["shade"], 0.3), (312, 199, 76, 8))  # its reflection
    pygame.draw.polygon(lay, wood, [(314, 190), (384, 190), (374, 202), (324, 202)])
    pygame.draw.line(lay, wood2, (314, 190), (384, 190), 2)
    pygame.draw.line(lay, wood2, (320, 196), (378, 196))
    pygame.draw.rect(lay, wood2, (344, 187, 10, 3))
    sc.add(lay, 0.12, texture=0.3)

    # near bank, path, the boat
    lay = art.plane()
    pts = [(x, int(bot(x)) + 2 + int(2 * math.sin(x / 13))) for x in range(0, W + 1, 4)]
    pygame.draw.polygon(lay, sc.col("leaf2", 0.18), [(0, H)] + pts + [(W, H)])
    art.grass_bed(lay, rng, (0, 206, W, 64), sc.col("leaf", 0.15), 600, 3)
    art.flowers(lay, rng, (0, 218, W, 52), p["flowers"], 70)
    earth, edge = sc.col("earth", 0.15), sc.col("earth_edge", 0.15)
    art.path(lay, [(-12, 238), (80, 242), (200, 240), (290, 228), (318, 220)], [20, 22, 22, 18, 14], earth, edge)
    art.path(lay, [(96, 236), (60, 214), (40, 204)], [10, 6, 3], earth, edge)
    sc.add(lay, 0.15)
    lay = art.plane()  # the post the boat is tied to
    pygame.draw.line(lay, sc.col("earth_edge", 0.1), (316, 193), (304, 214))
    pygame.draw.rect(lay, sc.col("wood", 0.1), (302, 206, 4, 16))
    sc.add(lay, 0.1, texture=0.3)
    for x0, x1 in ((0, 60), (120, 200), (400, 480)):  # reeds in clumps along the bank
        sc.live(Blades(rng, (x0, 202, x1 - x0, 8), (x1 - x0) // 2, [sc.col("leaf", 0.12), sc.col("leaf3", 0.12)],
                       8, 20, stiff=1.3))
    bugs = Bugs(rng, [(110, 170), (250, 180), (420, 172), (180, 150)], (150, 255, 236), wing=(220, 255, 255))
    sc.bugs.append(bugs)
    sc.live(bugs)
    sc.live(Motes(rng, (0, 0, W, 200), 50, (255, 252, 230)))
    front_frame(sc, rng, top=True, right=False)

    sc.spots = [
        Spot("go", (0, 214, 44, 46), "Back to the Glade", "glade", (14, 238)),
        Spot("go", (22, 192, 46, 22), "The Waterfall", "waterfall", (42, 204)),
        Spot("app", (310, 182, 78, 24), "Games", "games", (350, 194)),
    ]
    sc.lower = dict(ground=0.18, props=["rocks"], bug=(150, 255, 236))
    return sc.done()


# --- The Forest --------------------------------------------------------------------------------

def build_forest():
    rng = make_rng(44)
    p = pal(sky=[(176, 232, 222), (206, 238, 228), (240, 240, 222), (255, 234, 228)],
            mist=(226, 242, 234), light=(255, 250, 210), shade=(40, 64, 96),
            leaf3=(64, 150, 156), wood=(150, 118, 150))
    sc = Scene("forest", "The Forest", p, rng)
    sun(sc, 260, 10, 110)

    # rank after rank of trunks fading into the mist
    for d, n, (wmin, wmax), y in ((0.9, 14, (2, 4), 186), (0.76, 11, (4, 6), 192),
                                  (0.6, 8, (6, 9), 198), (0.42, 5, (10, 14), 206)):
        lay = art.plane()
        xs = sorted(rng.sample(range(0, W, 8), n))
        for x in xs:
            art.trunk(lay, rng, x + rng.randint(-3, 3), -5, y + 4, rng.randint(wmin, wmax), sc.col("wood", d),
                      branches=rng.randint(0, 2))
        art.canopy(lay, rng, -10, 490, int(20 * (1 - d)) + 4, sc.col("leaf3", d), r=(8, 16), jitter=6, down=False)
        art.ridge(lay, rng, y, 4, sc.col("leaf", d), scales=(40, 15, 6))
        sc.add(lay, d, veil=0.04, low=0.12)
    lay = art.plane()
    art.trunk(lay, rng, 26, -5, 262, 24, sc.col("wood", 0.08), branches=1)
    art.trunk(lay, rng, 404, -5, 238, 18, sc.col("wood", 0.12), branches=1)
    leaf_row(lay, rng, -10, 490, 4, 20, 12, sc.col("leaf3", 0.1), p, jitter=4)
    sc.add(lay, 0.1, texture=1.2)
    sc.live(Shafts([(220, 30, 120, 80, 0.0), (300, 24, 240, 64, 1.7), (160, 16, 60, 50, 3.4), (380, 20, 350, 50, 5.0)],
                   p["light"], alpha=44))

    lay = art.plane()
    art.ridge(lay, rng, 214, 4, sc.col("leaf2", 0.22), scales=(50, 18, 7))
    art.grass_bed(lay, rng, (0, 210, W, 60), sc.col("leaf", 0.18), 700, 3)
    art.flowers(lay, rng, (0, 220, W, 50), [(255, 255, 255), (196, 150, 255), (130, 226, 255)], 50)
    earth, edge = sc.col("earth", 0.2), sc.col("earth_edge", 0.2)
    art.path(lay, [(492, 244), (400, 238), (300, 224), (250, 214), (230, 206)], [24, 22, 18, 10, 5], earth, edge)
    art.path(lay, [(300, 224), (200, 226), (90, 222), (-12, 220)], [18, 18, 16, 14], earth, edge)
    sc.add(lay, 0.2)

    # a ring of glowing mushrooms
    lay = art.plane()
    caps = [(130, 140, 255), (255, 150, 220), (140, 236, 255), (200, 160, 255)]
    ring = []
    for i in range(9):
        a = i / 9 * math.tau
        x, y = 150 + math.cos(a) * 24, 236 + math.sin(a) * 7
        size = rng.randint(3, 6) + (2 if y > 236 else 0)
        c = caps[i % len(caps)]
        pygame.draw.rect(lay, (250, 240, 236), (x - 1, y - size, 2 + size // 4, size))
        pygame.draw.ellipse(lay, c, (x - size, y - size - size // 2, size * 2 + 1, size + 1))
        lay.set_at((int(x - size // 2), int(y - size - size // 4)), (255, 255, 255))
        ring.append((x, y - size, c))
    sc.add(lay, 0.12, texture=0)

    class Glows:
        def draw(self, s, t):
            for i, (x, y, c) in enumerate(ring):
                art.glow(s, x, y, 8, c, int(40 + 30 * math.sin(t * 1.5 + i)))

    sc.live(Glows())
    sc.live(Blades(rng, (0, 212, W, 58), 220, [sc.col("leaf", 0.1), sc.col("leaf3", 0.1), sc.col("leaf2", 0.1)], 4, 12))
    bugs = Bugs(rng, [(rng.randint(20, 460), rng.randint(80, 210)) for _ in range(16)], (220, 255, 140))
    sc.bugs.append(bugs)
    sc.live(bugs)
    sc.live(Motes(rng, (0, 0, W, 230), 90, (255, 255, 230)))
    front_frame(sc, rng)

    sc.spots = [
        Spot("go", (436, 214, 44, 46), "Back to the Glade", "glade", (466, 240)),
        Spot("go", (0, 198, 44, 42), "The Mossy Rocks", "rocks", (14, 220)),
        Spot("app", (116, 214, 70, 30), "Web Browser", "browser", (150, 230)),
    ]
    sc.lower = dict(ground=0.2, props=["mushrooms"], bug=(220, 255, 140))
    return sc.done()


# --- The Mossy Rocks --------------------------------------------------------------------------------

def build_rocks():
    rng = make_rng(55)
    p = pal(sky=[(172, 166, 255), (212, 182, 255), (255, 198, 226), (255, 226, 214)],
            mist=(242, 214, 242), light=(255, 240, 222), shade=(54, 44, 108))
    sc = Scene("rocks", "The Mossy Rocks", p, rng)
    sun(sc, 90, 60, 80)

    lay = art.plane()
    art.ridge(lay, rng, 140, 36, sc.col("lav", 0.9), scales=(80, 27, 9))
    sc.add(lay, 0.9, veil=0.04)
    lay = art.plane()  # distant stone spires
    for x, top, w in ((60, 70, 18), (110, 96, 12), (372, 60, 22), (420, 90, 14), (454, 110, 10)):
        pygame.draw.polygon(lay, sc.col("stone", 0.72), [(x - w // 2, 180), (x - w // 3, top + 6), (x, top),
                                                           (x + w // 3, top + 8), (x + w // 2, 180)])
        art.clump(lay, rng, x, top, w // 2 + 3, sc.col("moss", 0.72), n=4)
    art.canopy(lay, rng, -10, 490, 168, sc.col("leaf3", 0.72), r=(5, 10))
    sc.add(lay, 0.72, veil=0.05, low=0.1)
    lay = art.plane()
    art.ridge(lay, rng, 196, 6, sc.col("leaf2", 0.45), scales=(60, 20, 8))
    sc.add(lay, 0.45, veil=0.03)

    # the pile of mossy boulders, with a cave at its foot
    lay = art.plane()
    stone, moss = sc.col("stone", 0.3), sc.col("moss", 0.25)
    pygame.draw.polygon(lay, mix(stone, p["shade"], 0.25), [(170, 222), (196, 150), (240, 132), (300, 150), (320, 222)])
    art.rock(lay, rng, 244, 150, 50, 28, stone, moss=moss, mossiness=0.6)
    art.rock(lay, rng, 210, 172, 80, 40, stone, moss=moss)
    art.rock(lay, rng, 282, 178, 76, 42, stone, moss=moss)
    art.rock(lay, rng, 176, 222, 96, 50, stone, moss=moss, mossiness=0.4)
    art.rock(lay, rng, 304, 226, 104, 54, stone, moss=moss, mossiness=0.4)
    pygame.draw.ellipse(lay, sc.col("shade", 0.0), (222, 196, 40, 34))  # cave mouth
    pygame.draw.rect(lay, sc.col("shade", 0.0), (222, 213, 40, 14))
    sc.add(lay, 0.28, texture=1.4)
    lay = art.plane()
    for x, y, c in ((232, 220, (170, 140, 255)), (244, 216, (140, 230, 255)), (254, 222, (255, 160, 230))):
        pygame.draw.polygon(lay, c, [(x - 2, y + 6), (x, y - 3), (x + 2, y + 6)])
        lay.set_at((x, y - 1), (255, 255, 255))
    sc.raw(lay)

    class Crystals:
        def draw(self, s, t):
            for i, (x, y, c) in enumerate(((232, 220, (170, 140, 255)), (244, 216, (140, 230, 255)),
                                           (254, 222, (255, 160, 230)))):
                art.glow(s, x, y, 10, c, int(50 + 25 * math.sin(t * 1.2 + i * 2)))

    sc.live(Crystals())

    lay = art.plane()  # standing stone with a carved rune
    pygame.draw.polygon(lay, sc.col("stone", 0.22), [(76, 226), (78, 162), (88, 150), (100, 158), (102, 226)])
    art.rock(lay, rng, 89, 162, 26, 12, sc.col("stone", 0.22), moss=sc.col("moss", 0.2), mossiness=0.9)
    rune = sc.col("shade", 0.1)
    for a, b in (((86, 176), (92, 176)), ((89, 172), (89, 194)), ((85, 184), (93, 190)), ((93, 184), (85, 190))):
        pygame.draw.line(lay, rune, a, b)
    sc.add(lay, 0.22, texture=0.6)

    class Rune:
        def draw(self, s, t):
            k = 0.5 + 0.5 * math.sin(t * 0.8)
            art.glow(s, 89, 183, 12, (150, 220, 255), int(30 + 40 * k))

    sc.live(Rune())

    lay = art.plane()
    art.ridge(lay, rng, 230, 4, sc.col("leaf2", 0.15), scales=(50, 18, 7))
    art.grass_bed(lay, rng, (0, 226, W, 44), sc.col("leaf", 0.12), 500, 3)
    art.flowers(lay, rng, (0, 232, W, 38), p["flowers"], 60)
    earth, edge = sc.col("earth", 0.12), sc.col("earth_edge", 0.12)
    art.path(lay, [(242, 278), (250, 250), (310, 238), (380, 228), (424, 222)], [46, 34, 22, 12, 6], earth, edge)
    art.path(lay, [(250, 250), (150, 246), (60, 242), (-12, 240)], [30, 22, 18, 16], earth, edge)
    for x in (130, 360, 400, 160):
        art.rock(lay, rng, x, 240 + rng.randint(0, 20), rng.randint(14, 26), rng.randint(6, 10),
                 sc.col("stone", 0.1), moss=sc.col("moss", 0.1))
    sc.add(lay, 0.12)
    sc.live(Blades(rng, (0, 226, W, 44), 220, [sc.col("leaf", 0.08), sc.col("leaf2", 0.08)], 4, 12))
    bugs = Bugs(rng, [(120, 170), (360, 150), (240, 100), (420, 200)], (255, 200, 240))
    sc.bugs.append(bugs)
    sc.live(bugs)
    sc.live(Motes(rng, (0, 0, W, 230), 60, (255, 250, 240)))
    front_frame(sc, rng, left=False)

    sc.spots = [
        Spot("go", (384, 206, 64, 32), "Back to the Glade", "glade", (420, 220)),
        Spot("go", (0, 218, 44, 42), "The Forest", "forest", (14, 240)),
        Spot("app", (218, 192, 48, 38), "Discord", "discord", (242, 214)),
        Spot("app", (70, 146, 38, 82), "Code Editor", "code", (89, 183)),
    ]
    sc.lower = dict(ground=0.14, props=["rocks"], bug=(255, 200, 240), paths=[dict(
        pts=[(204, -2), (203, 30), (198, 90), (193, 150), (190, 230)], widths=[43, 48, 56, 64, 72],
        sign=(252, 172), spot=((140, 110, 110, 115), "Back to the Glade", "glade", (192, 204)))])
    return sc.done()


BUILDERS = {
    "glade": build_glade,
    "waterfall": build_waterfall,
    "river": build_river,
    "forest": build_forest,
    "rocks": build_rocks,
}
