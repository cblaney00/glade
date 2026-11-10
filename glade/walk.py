"""Walking anywhere the ground allows (2026-11-10, his ask: "the creatures should be able to walk
everywhere that they physically can and they should get smaller based on perspective").

Walkers used to keep to a few lines across each place. Now each place (and each lower screen) has
its ground drawn out here: `AREAS[key]`, one polygon per piece of ground you could walk on without
swimming or flying (the River's far bank is its own piece), less `HOLES` (pools, lakes, a house).
A walker belongs to the piece it was put on, picks anywhere in it, back or front, and walks there in
a straight line (beasts.Walker._retarget), growing and shrinking with how near it is (`persp`).
A builder can set `sc.field` itself (the aerial home does, aerial.py). A place not listed keeps the
old stretches of ground (`from_stretches`). Ground was traced from each place's picture: when a
place's art changes, check its areas still fit (tools: draw `Field.spots` over the picture).
"""

import pygame

import art
from art import H, W

STEP = 4  # how finely the ground is sampled for picking a spot
FRONT = H - 8  # the front edge of every upper screen's ground


def below(*pts):
    """The ground from a line across the screen (its far edge) down to the front."""
    return [(-4, pts[0][1])] + list(pts) + [(W + 4, pts[-1][1]), (W + 4, FRONT), (-4, FRONT)]


def oval(cx, cy, rx, ry):
    return ("oval", cx, cy, rx, ry)


AREAS = {
    "glade": [below((0, 402), (960, 402))],
    "waterfall": [below((0, 428), (960, 428))],
    "river": [below((0, 382), (960, 382))],
    "forest": [below((0, 452), (960, 452))],
    "rocks": [below((0, 424), (270, 430), (290, 470), (680, 470), (700, 432), (960, 424))],
    "ridge": [below((0, 374), (960, 374))],
    "springs": [below((0, 432), (960, 432))],
    "tower": [below((0, 416), (960, 416))],
    "caverns": [below((0, 440), (300, 462), (720, 462), (960, 440))],
    "meadow": [below((0, 372), (960, 352))],
    "hollow": [below((0, 392), (960, 392))],
    "bog": [below((0, 466), (960, 466))],
    "ruins": [below((0, 372), (960, 372))],
    "bridge": [[(180, 336), (780, 336), (780, 470), (964, 470), (964, FRONT), (-4, FRONT), (-4, 470), (180, 470)]],
    "shore": [below((0, 444), (960, 444))],
    "falls": [below((0, 424), (960, 424))],
    "peak": [below((0, 384), (960, 384))],
    "gully": [below((0, 470), (200, 454), (760, 454), (960, 470))],
    "orchard": [below((0, 388), (960, 388))],
    "temple": [below((0, 456), (960, 456)), [(290, 356), (680, 356), (680, 380), (290, 380)]],
    "dunes": [below((0, 350), (480, 340), (960, 340))],
    "lava": [below((0, 416), (960, 416))],
    "grotto": [below((0, 432), (960, 432))],
    "kelp": [below((0, 452), (960, 452))],
    "lighthouse": [below((0, 452), (960, 452)), [(330, 334), (964, 318), (964, 352), (330, 358)]],
    "comet": [below((0, 336), (960, 336))],
    "garden": [below((0, 376), (960, 376))],
    "isles": [below((0, 452), (960, 452))],
    "storm": [below((0, 412), (960, 412))],
    "thorn": [below((0, 384), (960, 384))],
    "hall": [below((0, 448), (960, 448))],
}
HOLES = {
    "waterfall": [oval(410, 418, 215, 40)],
    "ridge": [oval(480, 415, 165, 28)],
    "tower": [(726, 404, 80, 60)],
    "falls": [oval(480, 414, 152, 22)],
    "comet": [oval(480, 372, 40, 18)],
    "garden": [oval(480, 424, 110, 26)],
}


class Field:
    """Ground an animal may stand on: a mask, and the spots in it to pick from."""

    def __init__(self, mask, offset=(0, 0)):
        self.mask, self.offset = mask, offset
        w, h = mask.get_size()
        self.spots = []
        for x in range(0, w, STEP):
            self.spots += [(x + offset[0], y + offset[1]) for y in range(0, h, STEP) if mask.get_at((x, y))]
            if x % 96 == 0:
                art.breathe()  # (built while wandering, between frames: loading.py)

    def __bool__(self):
        return bool(self.spots)

    def inside(self, x, y):
        x, y = int(x) - self.offset[0], int(y) - self.offset[1]
        w, h = self.mask.get_size()
        return 0 <= x < w and 0 <= y < h and bool(self.mask.get_at((x, y)))

    def pick(self, rng):
        x, y = rng.choice(self.spots)
        return x + rng.uniform(0, STEP - 1), y + rng.uniform(0, STEP - 1)

    def clear_way(self, x0, y0, x1, y1, avoid=None):
        """Can it walk straight from one spot to the other without leaving the ground?"""
        n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) / 5))
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            if not self.inside(x, y) or (avoid and avoid(x, y)):
                return False
        return True


def drawn(polys, holes=(), size=(W, H)):
    """A Field from polygons of ground, less holes (rects, or ovals from `oval`)."""
    s = pygame.Surface(size, pygame.SRCALPHA)
    for poly in polys:
        pygame.draw.polygon(s, (255, 255, 255, 255), poly)
    for h in holes:
        if h[0] == "oval":
            _, cx, cy, rx, ry = h
            pygame.draw.ellipse(s, (0, 0, 0, 0), (cx - rx, cy - ry, rx * 2, ry * 2))
        else:
            s.fill((0, 0, 0, 0), h)
    art.breathe()
    return Field(pygame.mask.from_surface(s))


def from_stretches(stretches, holes=(), up=8, down=6):
    """A band round the old lines of ground [(ground, (x0, x1))] (a place not in AREAS)."""
    polys = []
    for ground, (a, b) in stretches:
        xs = [a + (b - a) * k / 16 for k in range(17)]
        polys.append([(x, ground(x) - up) for x in xs] + [(x, ground(x) + down) for x in reversed(xs)])
    return drawn(polys, holes)


def for_scene(sc):
    """Give every walker of an upper screen the piece of ground it stands on."""
    fields = [sc.field] if getattr(sc, "field", None) is not None else \
        [drawn([poly], HOLES.get(sc.key, ())) for poly in AREAS.get(sc.key, ())]
    sc.field = fields[0] if fields else None
    walkers = [o for o in sc.lives if type(o).__name__ == "Walker"]
    for o in walkers:
        mid = (o.xr[0] + o.xr[1]) / 2
        y = o.ground(mid)
        home = next((f for f in fields if f.inside(mid, y) or f.inside(mid, y + 6)), None)
        if home is None and fields:  # (its old line was off the ground: the nearest piece)
            home = min(fields, key=lambda f: min(abs(sx - mid) + 3 * abs(sy - y) for sx, sy in f.spots[::8]))
        if home is None and o.roam:  # nowhere drawn: the old stretches it walked
            home = from_stretches(o.roam, HOLES.get(sc.key, ()))
        o.field = home or None
        if o.field is not None:
            o.lane = o.lane_to = 0.0
        if o.field is not None and not o.field.inside(o.x, o.y):  # start somewhere in it
            o.x, o.y = o.field.pick(o.rng)
            o.ground = flat(o.y)
            o.xr = (o.x - 1, o.x + 1)
            if o.persp:
                o.depth = o.persp(o.y)


def flat(y):
    return lambda x: y


def line(x0, y0, x1, y1):
    """Ground that runs straight from one spot to another (and stays level beyond them)."""
    if abs(x1 - x0) < 1e-6:
        return flat(y1)
    lo, hi = min(x0, x1), max(x0, x1)

    def ground(x):
        x = lo if x < lo else hi if x > hi else x
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ground


def for_lower(walkers, w, h, pond=None, signs=()):
    """A lower screen's ground: all of it, but the pond (and a little room round the path signs,
    so they stay easy to click)."""
    holes = []
    if pond:
        cx, cy, rx, ry = pond
        holes.append(oval(cx, cy, rx + 18, ry + 18))
    holes += [oval(sx, sy, 56, 30) for sx, sy in signs]
    field = drawn([[(40, 80), (w - 40, 80), (w - 40, h - 22), (40, h - 22)]], holes, (w, h))
    for o in walkers:
        o.field = field or None
        o.lane = o.lane_to = 0.0
    return field
