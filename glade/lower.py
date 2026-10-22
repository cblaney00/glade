"""The lower monitor: the ground right in front of you, below whichever place you are in.

It is the nearest layer of the scene above it, so it uses that scene's palette and
starts with exactly the colours the upper screen ends on, then gets a little deeper
and bigger toward the bottom (nearer). Paths that leave the bottom of the upper
screen carry on here and lead somewhere you can see — a signpost or the pond.

Built on a full W x H canvas so every brush in art.py works unchanged; only the
top-left `w x h` of it is shown.
"""

import math

import pygame

import art
from art import at_depth, mix
from life import Blades, Bugs, Motes, make_rng
from pond import Pond, Water


class Lower:
    def __init__(self, scene, w, h):
        self.w, self.h = w, h
        self.key = scene.key
        spec = getattr(scene, "lower", {})
        p = self.pal = scene.pal
        rng = make_rng(hash(scene.key) % 1000 + 7)
        d0 = spec.get("ground", 0.2)
        col = lambda name, d: at_depth(p, p[name], d)  # noqa: E731
        self.spots, self.bugs, self.parts, self.pond = [], [], [], None

        cur = art.solid()
        # ground: the upper screen's meadow colour, deepening toward you
        top, bottom = col("leaf2", d0), col("leaf2", 0.04)
        art.gradient(cur, (0, 0, art.W, h), [top, mix(top, bottom, 0.5), bottom], steps=8)
        lay = art.plane()
        art.grass_bed(lay, rng, (0, 0, w, h // 2), col("leaf", d0 - 0.05), w * h // 14, 3)
        art.grass_bed(lay, rng, (0, h // 2, w, h // 2), col("leaf", 0.03), w * h // 14, 5)
        art.flowers(lay, rng, (0, 0, w, h // 2), p["flowers"], w // 3)
        big_flowers(lay, rng, (0, h // 2, w, h // 2), p["flowers"], w // 5)
        cur.blit(lay, (0, 0))

        # paths carried on from the screen above, each ending at a signpost
        lay = art.plane()
        earth, edge = col("earth", d0), col("earth_edge", d0)
        for path in spec.get("paths", []):
            art.path(lay, path["pts"], path["widths"], earth, edge)
        cur.blit(lay, (0, 0))

        if spec.get("pond"):
            self.build_pond(cur, rng, col, p, spec["pond"])
        self.ground = cur

        paths = spec.get("paths", [])
        pond = spec.get("pond")

        def clear(x, y, room=10):
            for pp in paths:
                for (px, py), pw in zip(pp["pts"], pp["widths"]):
                    if math.hypot(x - px, (y - py) * 1.4) < pw / 2 + room:
                        return False
            if pond:
                cx, cy, rx, ry = pond
                if ((x - cx) / (rx + room)) ** 2 + ((y - cy) / (ry + room)) ** 2 < 1.2:
                    return False
            return True

        def spots(n, room):
            out = []
            for _ in range(n * 20):
                x, y = rng.randint(24, w - 24), rng.randint(24, h - 6)
                if clear(x, y, room) and all(math.hypot(x - a, y - b) > room * 2 for a, b in out):
                    out.append((x, y))
                if len(out) == n:
                    break
            return out

        front = art.plane()
        props = art.plane()
        # close-up bushes with blossoms, and clumps of ferns (they sway; see below)
        for x, y in spots(4, 22):
            art.foliage(props, rng, x, y - 8, rng.randint(14, 22), rng.randint(9, 13), col("leaf", 0.08), p)
            m = pygame.mask.from_surface(props)
            art.blossoms(props, rng, (x - 22, y - 22, 44, 26), [(255, 255, 255), p["pink"], p["pink2"]], 40, m)
        self.fern_spots = spots(6, 14)
        for kind in spec.get("props", []):
            if kind == "rocks":
                for x, y in spots(5, 16):
                    art.rock(props, rng, x, y, rng.randint(14, 30), rng.randint(6, 12), col("stone", 0.08),
                             moss=col("moss", 0.06), mossiness=0.7)
            if kind == "mushrooms":
                for x, y in spots(6, 12):  # in little clusters
                    for _ in range(rng.randint(2, 4)):
                        mushroom(props, x + rng.randint(-8, 8), y + rng.randint(-3, 3), rng.randint(3, 7),
                                 rng.choice([(255, 150, 220), (140, 236, 255), (200, 160, 255)]))
        for path in spec.get("paths", []):
            sx, sy = path["sign"]
            signpost(props, sx, sy, col("wood", 0.06), col("wood2", 0.06), path.get("arrow", (0, 1)))
        art.finish(props, p, 0.06, rng, texture=0.5)
        front.blit(props, (0, 0))

        # the nearest foliage, framing the sides like the corners of the screen above
        lay = art.plane()
        c, c2 = col("leaf3", 0.02), col("leaf", 0.04)
        for y in range(-10, h + 20, 26):
            art.foliage(lay, rng, rng.randint(-14, 2), y, rng.randint(20, 30), rng.randint(14, 20), c, p)
            art.foliage(lay, rng, w + rng.randint(-2, 14), y + 10, rng.randint(20, 30), rng.randint(14, 20), c, p)
        art.foliage(lay, rng, 16, 8, 22, 12, c2, p)
        art.foliage(lay, rng, w - 14, 4, 18, 10, c2, p)
        art.finish(lay, p, 0.02, rng, texture=1.4)
        front.blit(lay, (0, 0))
        self.front = front

        far = Blades(rng, (0, 4, w, h - 60), w // 2, [col("leaf", d0 - 0.08), col("leaf3", d0 - 0.08)], 4, 12)
        near = Blades(rng, (0, h - 50, w, 52), w // 2,
                      [col("leaf", 0.02), col("leaf3", 0.02), col("leaf2", 0.03)], 10, 26, stiff=1.2)
        ferns = Blades(rng, (0, 0, 1, 1), 0, [col("leaf", 0.05)])
        for x, y in self.fern_spots:
            clump = Blades(rng, (x - 7, y - 2, 14, 4), 14, [col("leaf", 0.05), col("leaf2", 0.06), col("leaf3", 0.04)],
                           12, 28, stiff=1.6)
            ferns.items += clump.items
        ferns.items.sort(key=lambda b: b[1])
        if self.pond:  # no grass growing out of the water, but reeds at its edge
            for blades in (far, near):
                blades.items = [it for it in blades.items if not self.pond.water.inside(it[0], it[1], 1.15)]
            for x, y in self.shore_reeds:
                ferns.items += Blades(rng, (int(x) - 6, int(y) - 2, 12, 4), 12,
                                      [col("leaf3", 0.08), col("leaf", 0.08)], 10, 24, stiff=1.4).items
            ferns.items.sort(key=lambda b: b[1])
        bugs = Bugs(rng, [(rng.randint(30, w - 30), rng.randint(20, h - 40)) for _ in range(5)],
                    spec.get("bug", (255, 236, 150)))
        self.bugs.append(bugs)
        self.parts = [far, ferns, near, bugs, Motes(rng, (0, 0, w, h), 30, (255, 252, 230))]
        from scenes import Spot  # here, not at the top: scenes is the module that describes us
        for path in spec.get("paths", []):
            rect, label, target, mark = path["spot"]
            self.spots.append(Spot("go", rect, label, target, mark, direction=path.get("arrow", (0, 1))))

    def build_pond(self, cur, rng, col, p, where):
        cx, cy, rx, ry = where
        water = Water(cx, cy, rx, ry)
        shore = art.plane()
        pygame.draw.ellipse(shore, col("earth_edge", 0.12), (cx - rx - 5, cy - ry - 3, rx * 2 + 10, ry * 2 + 9))
        pygame.draw.ellipse(shore, col("earth", 0.14), (cx - rx - 3, cy - ry - 3, rx * 2 + 6, ry * 2 + 4))
        cur.blit(shore, (0, 0))
        # water: the sky reflected on the far side, deeper toward you
        far = mix(col("water", 0.25), p["sky"][1], 0.35)
        near = col("water", 0.1)
        surf = art.solid()
        art.gradient(surf, (0, cy - ry, art.W, ry * 2), [far, mix(far, near, 0.5), near], steps=6)
        mask = pygame.Surface((art.W, art.H), pygame.SRCALPHA)
        pygame.draw.ellipse(mask, (255, 255, 255, 255), (cx - rx, cy - ry, rx * 2, ry * 2))
        pond_s = art.plane()
        pond_s.blit(surf, (0, 0))
        pond_s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # pebbles on the bottom, the blossom tree's reflection
        for _ in range(170):
            x, y = water.pick(rng, 0.9)
            c = mix(mix(col("stone", 0.2), near, 0.55), (40, 80, 130), rng.random() * 0.2)
            r = rng.randint(2, 4)
            pygame.draw.ellipse(pond_s, c, (x, y, r * 2, r))
        refl = art.plane()
        for _ in range(26):
            x, y = 332 + rng.randint(-32, 32), cy - ry + 8 + rng.randint(0, 34)
            if water.inside(x, y, 0.9):
                pygame.draw.ellipse(refl, (*p["pink"], 60), (x, y, rng.randint(12, 26), rng.randint(4, 8)))
        pond_s.blit(refl, (0, 0))
        cur.blit(pond_s, (0, 0))
        self.pond = Pond(rng, water, near, p["light"], col("leaf2", 0.12))
        self.shore_reeds = [(cx + math.cos(a) * rx * 0.97, cy + math.sin(a) * ry * 0.97)
                            for a in (0.15, 0.5, 2.2, 2.75, 1.6)]
        # rocks on the shore and a little dock from the path
        lay = art.plane()
        for a, w_, h_ in ((2.5, 30, 14), (3.4, 20, 9), (0.4, 26, 12), (1.2, 16, 8), (4.6, 18, 8)):
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry + 4
            art.rock(lay, rng, x, y, w_, h_, col("stone", 0.12), moss=col("moss", 0.1), mossiness=0.7)
        wood, wood2 = col("wood", 0.08), col("wood2", 0.08)
        x0, x1, y0 = cx - rx - 44, cx - rx + 30, cy - 26
        for x in (x1 - 6, x1 - 30):  # posts in the water, under the deck
            pygame.draw.rect(lay, mix(wood, (30, 20, 50), 0.35), (x, y0 + 8, 3, 8))
        pygame.draw.rect(lay, wood2, (x0, y0, x1 - x0, 8))  # deck
        for x in range(x0 + 5, x1, 5):
            pygame.draw.line(lay, wood, (x, y0), (x, y0 + 7))
        pygame.draw.rect(lay, wood, (x0, y0 + 8, x1 - x0, 2))  # its front edge
        # reeds and leafy clumps breaking up the shoreline
        for i in range(14):
            a_ = math.pi * (1.05 + i / 13 * 0.9)  # along the far side
            art.foliage(lay, rng, cx + math.cos(a_) * (rx + 2), cy + math.sin(a_) * (ry + 1), rng.randint(6, 11), 4,
                        col("leaf", 0.14), p, leaf=(1, 3))
        art.finish(lay, p, 0.1, rng, texture=0.6)
        self.pond_top = lay

    def click(self, x, y, t):
        if self.pond and self.pond.click(x, y, t):
            return
        for b in self.bugs:
            b.scatter(x, y, t)

    def update(self, dt, t):
        if self.pond:
            self.pond.update(dt, t)

    def draw(self, s, t):
        s.blit(self.ground, (0, 0))
        if self.pond:
            self.pond.draw(s, t)
            s.blit(self.pond_top, (0, 0))
        s.blit(self.front, (0, 0))
        for part in self.parts:
            part.draw(s, t)


def big_flowers(s, rng, rect, colors, n):
    """Flowers close up: bigger heads with a darker underside."""
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        c = rng.choice(colors)
        pygame.draw.line(s, (60, 130, 120), (x, y + 2), (x, y + 6))
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            s.set_at((x + dx, y + dy), c if dy <= 0 else mix(c, (60, 30, 90), 0.2))
        s.set_at((x, y), (255, 236, 140))


def mushroom(s, x, y, size, cap):
    pygame.draw.rect(s, (250, 240, 236), (x - 1, y - size, 2 + size // 4, size))
    pygame.draw.ellipse(s, cap, (x - size, y - size - size // 2, size * 2 + 1, size + 1))
    s.set_at((x - size // 2, y - size - size // 4), (255, 255, 255))


def signpost(s, x, y, wood, wood2, direction):
    """A post with one board pointing the way, standing with its foot at (x, y)."""
    pygame.draw.rect(s, wood, (x - 2, y - 34, 5, 36))
    dx, dy = direction
    if dy > 0 and dx == 0:  # pointing down: a board with a downward chevron
        pygame.draw.rect(s, wood2, (x - 12, y - 32, 25, 9))
        pygame.draw.lines(s, wood, False, [(x - 4, y - 30), (x, y - 26), (x + 4, y - 30)], 2)
    else:
        bx = x if dx > 0 else x - 24
        pygame.draw.rect(s, wood2, (bx, y - 32, 24, 8))
        tip = bx + 24 if dx > 0 else bx
        pygame.draw.polygon(s, wood2, [(tip, y - 32), (tip + dx * 5, y - 28), (tip, y - 24)])
        pygame.draw.line(s, wood, (bx + 3, y - 28), (bx + 20, y - 28))
