"""The lower monitor: the ground right in front of you, below whichever place you are in.

It is the nearest layer of the scene above it, so it uses that scene's palette and
starts with exactly the colours the upper screen ends on, then gets a little deeper
and bigger toward the bottom (nearer). Paths that leave the bottom of the upper
screen carry on here and lead somewhere you can see — a signpost or the pond. Up
close you can see the small life of the ground best: slugs, a snail, fireflies,
glowing moss and mushrooms.

Built on a full W x H canvas so every brush in art.py works unchanged; only the
top-left `w x h` of it is shown.
"""

import math

import pygame

import art
from art import GLOW, at_depth, mix
from life import Blades, Fireflies, Motes, Pulses, Slug, Squid, Track, make_rng
from pond import Pond, Water


class Lower(art.Lighting):
    def __init__(self, scene, w, h):
        self.w, self.h = w, h
        self.key = scene.key
        spec = getattr(scene, "lower", {})
        p = self.pal = scene.pal
        rng = self.rng = make_rng(sum(map(ord, scene.key)) + 7)
        d0 = spec.get("ground", 0.2)
        col = lambda name, d: at_depth(p, p[name], d)  # noqa: E731
        self.spots, self.bugs, self.creatures, self.pond = [], [], [], None
        self.init_light(p, (w, h), lower=True)

        cur = art.solid()
        # ground: the upper screen's meadow colour, deepening toward you
        top, bottom = col("leaf2", d0), col("leaf2", 0.04)
        art.gradient(cur, (0, 0, art.W, h), [top, mix(top, bottom, 0.5), bottom], steps=8)
        lay = art.plane()
        art.grass_bed(lay, rng, (0, 0, w, h // 2), col("leaf", d0 - 0.05), w * h // 30, 6)
        art.grass_bed(lay, rng, (0, h // 2, w, h // 2), col("leaf", 0.03), w * h // 30, 10)
        art.flowers(lay, rng, (0, 0, w, h // 2), p["flowers"], w // 5)
        big_flowers(lay, rng, (0, h // 2, w, h // 2), p["flowers"], w // 8)
        cur.blit(lay, (0, 0))

        # paths carried on from the screen above, each ending at a signpost
        lay = art.plane()
        earth, edge = col("earth", d0), col("earth_edge", d0)
        for path in spec.get("paths", []):
            art.path(lay, path["pts"], path["widths"], earth, edge, rng=rng)
        cur.blit(lay, (0, 0))

        if spec.get("pond"):
            self.build_pond(cur, rng, col, p, spec["pond"])
        self.ground = cur

        paths = spec.get("paths", [])
        pond = spec.get("pond")

        def clear(x, y, room=20):
            for pp in paths:
                for (px, py), pw in zip(pp["pts"], pp["widths"]):
                    if math.hypot(x - px, (y - py) * 1.4) < pw / 2 + room:
                        return False
                sx, sy = pp["sign"]
                if math.hypot(x - sx, y - sy) < 70:
                    return False
            if pond:
                cx, cy, rx, ry = pond
                if ((x - cx) / (rx + room)) ** 2 + ((y - cy) / (ry + room)) ** 2 < 1.2:
                    return False
            return True

        taken = []

        def spots(n, room):
            out = []
            for _ in range(n * 30):
                x, y = rng.randint(48, w - 48), rng.randint(48, h - 12)
                if clear(x, y, room) and all(math.hypot(x - a, y - b) > room * 2 for a, b in out + taken):
                    out.append((x, y))
                if len(out) == n:
                    break
            taken.extend(out)
            return out

        front = art.plane()
        props = art.plane()
        glows = []
        # glowing moss cushions on the ground
        for i, (x, y) in enumerate(spots(5, 40)):
            c = (GLOW["moss"], GLOW["cyan"], GLOW["lime"])[i % 3]
            self.moss(props, x, y, rng.randint(50, 90), rng.randint(14, 22), c)
        # close-up bushes with blossoms, and clumps of ferns (they sway; see below)
        for x, y in spots(4, 44):
            art.foliage(props, rng, x, y - 16, rng.randint(28, 44), rng.randint(18, 26), col("leaf", 0.08), p)
            m = pygame.mask.from_surface(props)
            art.blossoms(props, rng, (x - 44, y - 44, 88, 52), [(255, 255, 255), p["pink"], p["pink2"]], 90, m)
            self.shadow(x, y + 6, 46, 12, 0.35)
        self.fern_spots = spots(6, 28)
        for kind in spec.get("props", []):
            if kind == "rocks":
                for x, y in spots(5, 32):
                    pts = []
                    w_, h_ = rng.randint(28, 60), rng.randint(12, 24)
                    art.rock(props, rng, x, y, w_, h_, col("stone", 0.08), moss=col("moss", 0.06), mossiness=0.7,
                             glow_pts=pts)
                    self.shadow(x, y + 4, w_ * 0.7, h_ * 0.35, 0.4)
                    for i, (gx, gy) in enumerate(pts):
                        if 0 <= gx < art.W and 0 <= gy < art.H:
                            self.emit.set_at((int(gx), int(gy)), art.scale(GLOW["moss"], 0.6))
                        if i % 3 == 0:
                            self.lamp(gx, gy + 4, 40, GLOW["moss"], 60)
            if kind == "mushrooms":
                for x, y in spots(6, 24):  # in little clusters
                    for _ in range(rng.randint(2, 4)):
                        cap = rng.choice([(255, 150, 220), (140, 236, 255), (200, 160, 255)])
                        mx, my, sz = x + rng.randint(-16, 16), y + rng.randint(-6, 6), rng.randint(6, 14)
                        mushroom(props, mx, my, sz, cap)
                        glows.append((mx, my - sz - sz // 4, 40 + sz * 3, cap, 90, mx * 0.1))
        for path in spec.get("paths", []):
            sx, sy = path["sign"]
            signpost(props, sx, sy, col("wood", 0.06), col("wood2", 0.06), path.get("arrow", (0, 1)), p)
            self.shadow(sx, sy + 2, 20, 6, 0.4)
        art.finish(props, p, 0.06, rng, texture=0.5)
        front.blit(props, (0, 0))

        # the nearest foliage, framing the sides like the corners of the screen above
        lay = art.plane()
        c, c2 = col("leaf3", 0.02), col("leaf", 0.04)
        for y in range(-20, h + 40, 52):
            art.foliage(lay, rng, rng.randint(-28, 4), y, rng.randint(40, 60), rng.randint(28, 40), c, p)
            art.foliage(lay, rng, w + rng.randint(-4, 28), y + 20, rng.randint(40, 60), rng.randint(28, 40), c, p)
        art.foliage(lay, rng, 32, 16, 44, 24, c2, p)
        art.foliage(lay, rng, w - 28, 8, 36, 20, c2, p)
        art.finish(lay, p, 0.02, rng, texture=1.2)
        front.blit(lay, (0, 0))
        self.front = art.trimmed(front)

        far = Blades(rng, (0, 8, w, h - 120), w // 2, [col("leaf", d0 - 0.08), col("leaf3", d0 - 0.08)], 8, 24)
        near = Blades(rng, (0, h - 100, w, 104), w // 2,
                      [col("leaf", 0.02), col("leaf3", 0.02), col("leaf2", 0.03)], 20, 52, stiff=1.2, width=2)
        ferns = Blades(rng, (0, 0, 1, 1), 0, [col("leaf", 0.05)])
        for x, y in self.fern_spots:
            clump = Blades(rng, (x - 14, y - 4, 28, 8), 16, [col("leaf", 0.05), col("leaf2", 0.06), col("leaf3", 0.04)],
                           24, 56, stiff=1.6, width=2)
            ferns.items += clump.items
        ferns.items.sort(key=lambda b: b[1])
        if self.pond:  # no grass growing out of the water, but reeds at its edge
            for blades in (far, near):
                blades.items = [it for it in blades.items if not self.pond.water.inside(it[0], it[1], 1.15)]
            for x, y in self.shore_reeds:
                ferns.items += Blades(rng, (int(x) - 12, int(y) - 4, 24, 8), 14,
                                      [col("leaf3", 0.08), col("leaf", 0.08)], 20, 48, stiff=1.4).items
            ferns.items.sort(key=lambda b: b[1])
        bugs = Fireflies(rng, (30, 20, w - 60, h - 80), 14, color=spec.get("fly", GLOW["firefly"]), reach=46)
        self.bugs.append(bugs)
        # up close: two big slugs and a snail, crawling across the grass
        crawlers = []
        for body, spots_c, shell, sz in (((214, 172, 226), None, None, 2.4), ((126, 132, 236), GLOW["cyan"], None, 2.1),
                                         ((220, 200, 186), None, (226, 170, 140), 1.9)):
            for _ in range(60):
                x0, y0 = rng.randint(40, w - 300), rng.randint(60, h - 30)
                ln = rng.randint(220, 340)
                pts = [(x, y0 + 8 * math.sin(x / 70 + y0)) for x in range(x0, min(w - 40, x0 + ln), 20)]
                if len(pts) > 6 and all(clear(x, y, 10) for x, y in pts) and \
                        all(abs(y0 - c.track.pts[0][1]) > 50 for c in crawlers):
                    crawlers.append(Slug(rng, Track(pts), body, size=sz, speed=7, spots=spots_c, shell=shell))
                    break
        sky = Squid(rng, (60, 20, w - 120, h // 2), rng.choice([GLOW["cyan"], GLOW["pink"], GLOW["violet"]]), size=2.0)
        self.parts = [far, ferns] + crawlers + [near, bugs, sky, Motes(rng, (0, 0, w, h), 26, GLOW["cyan"])]
        if glows:
            self.parts.append(Pulses(glows))
        self.creatures = [c for c in self.parts if hasattr(c, "poke")]
        if self.pond:
            self.creatures.append(self.pond)
        from scenes import Spot  # here, not at the top: scenes is the module that describes us
        for path in spec.get("paths", []):
            rect, label, target, mark = path["spot"]
            sx, sy = path["sign"]
            self.spots.append(Spot("go", rect, label, target, mark, direction=path.get("arrow", (0, 1)),
                                   sign=(sx, sy - 92)))

    def moss(self, lay, x, y, w, h, color):
        art.glowmoss(self, lay, x, y, w, h, color, strength=90)

    def build_pond(self, cur, rng, col, p, where):
        cx, cy, rx, ry = where
        water = Water(cx, cy, rx, ry)
        shore = art.plane()
        pygame.draw.ellipse(shore, col("earth_edge", 0.12), (cx - rx - 10, cy - ry - 6, rx * 2 + 20, ry * 2 + 18))
        pygame.draw.ellipse(shore, col("earth", 0.14), (cx - rx - 6, cy - ry - 6, rx * 2 + 12, ry * 2 + 8))
        cur.blit(shore, (0, 0))
        # water: the night sky reflected on the far side, deeper toward you
        far = mix(col("water", 0.25), p["sky"][2], 0.4)
        near = col("water", 0.1)
        surf = art.solid()
        art.gradient(surf, (0, cy - ry, art.W, ry * 2), [far, mix(far, near, 0.5), near], steps=6)
        mask = pygame.Surface((art.W, art.H), pygame.SRCALPHA)
        pygame.draw.ellipse(mask, (255, 255, 255, 255), (cx - rx, cy - ry, rx * 2, ry * 2))
        pond_s = art.plane()
        pond_s.blit(surf, (0, 0))
        pond_s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # pebbles on the bottom, the blossom tree's reflection
        for _ in range(300):
            x, y = water.pick(rng, 0.9)
            c = mix(mix(col("stone", 0.2), near, 0.55), (30, 60, 120), rng.random() * 0.25)
            r = rng.randint(3, 7)
            pygame.draw.ellipse(pond_s, c, (x, y, r * 2, r))
            pygame.draw.line(pond_s, mix(c, (255, 255, 255), 0.15), (x + 2, y), (x + r, y))
        refl = art.plane()
        for _ in range(40):
            x, y = 664 + rng.randint(-64, 64), cy - ry + 16 + rng.randint(0, 68)
            if water.inside(x, y, 0.9):
                pygame.draw.ellipse(refl, (*p["pink"], 50), (x, y, rng.randint(24, 52), rng.randint(6, 14)))
        for i in range(6):  # stars reflected
            x, y = water.pick(rng, 0.7)
            refl.set_at((int(x), int(y)), (230, 236, 255, 160))
        pond_s.blit(refl, (0, 0))
        cur.blit(pond_s, (0, 0))
        self.lamp(cx, cy, int(rx * 1.1), GLOW["cyan"], 60)
        self.pond = Pond(rng, water, near, p["rim"], col("leaf2", 0.12))
        self.shore_reeds = [(cx + math.cos(a) * rx * 0.97, cy + math.sin(a) * ry * 0.97)
                            for a in (0.15, 0.5, 2.2, 2.75, 1.6)]
        # rocks on the shore and a little dock from the path
        lay = art.plane()
        shore_moss = []
        for a, w_, h_ in ((2.5, 60, 28), (3.4, 40, 18), (0.4, 52, 24), (1.2, 32, 16), (4.6, 36, 16)):
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry + 8
            art.rock(lay, rng, x, y, w_, h_, col("stone", 0.12), moss=col("moss", 0.1), mossiness=0.7,
                     glow_pts=shore_moss)
        for i, (gx, gy) in enumerate(shore_moss):
            if 0 <= gx < art.W and 0 <= gy < art.H:
                self.emit.set_at((int(gx), int(gy)), art.scale(GLOW["moss"], 0.6))
            if i % 3 == 0:
                self.lamp(gx, gy + 4, 36, GLOW["moss"], 50)
        wood, wood2 = col("wood", 0.08), col("wood2", 0.08)
        x0, x1, y0 = cx - rx - 88, cx - rx + 60, cy - 52
        for x in (x1 - 12, x1 - 60):  # posts in the water, under the deck
            pygame.draw.rect(lay, mix(wood, (20, 12, 40), 0.35), (x, y0 + 16, 6, 16))
        pygame.draw.rect(lay, wood2, (x0, y0, x1 - x0, 16))  # deck
        for x in range(x0 + 10, x1, 10):
            pygame.draw.line(lay, wood, (x, y0), (x, y0 + 14))
        pygame.draw.line(lay, mix(wood2, p["rim"], 0.3), (x0, y0), (x1, y0))
        pygame.draw.rect(lay, wood, (x0, y0 + 16, x1 - x0, 4))  # its front edge
        # reeds and leafy clumps breaking up the shoreline
        for i in range(16):
            a_ = math.pi * (1.05 + i / 15 * 0.9)  # along the far side
            art.foliage(lay, rng, cx + math.cos(a_) * (rx + 4), cy + math.sin(a_) * (ry + 2), rng.randint(12, 22), 8,
                        col("leaf", 0.14), p, leaf=(2, 4))
        art.finish(lay, p, 0.1, rng, texture=0.6)
        self.pond_top = art.trimmed(lay)

    def click(self, x, y, t):
        for c in self.creatures:
            if c.poke(x, y, t):
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
            s.blit(*self.pond_top)
        s.blit(*self.front)
        for part in self.parts:
            if hasattr(part, "draw"):
                part.draw(s, t)
        self.lit(s, self.parts + ([self.pond] if self.pond else []), t)


def big_flowers(s, rng, rect, colors, n):
    """Flowers close up: bigger heads with a darker underside, on a stem with a leaf."""
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        c = rng.choice(colors)
        pygame.draw.line(s, (50, 110, 110), (x, y + 3), (x, y + 12))
        s.set_at((x + 1, y + 8), (70, 140, 130))
        s.set_at((x + 2, y + 7), (70, 140, 130))
        for a in range(5):
            ang = a / 5 * math.tau - math.pi / 2
            px, py = x + math.cos(ang) * 3, y + math.sin(ang) * 3
            pygame.draw.circle(s, c if py <= y else mix(c, (50, 24, 80), 0.25), (round(px), round(py)), 2)
        pygame.draw.circle(s, (255, 236, 140), (x, y), 1)


def mushroom(s, x, y, size, cap):
    pygame.draw.rect(s, (236, 226, 236), (x - 1, y - size, 2 + size // 3, size))
    pygame.draw.ellipse(s, mix(cap, (30, 20, 60), 0.35), (x - size, y - size - size // 2 + 1, size * 2 + 1, size + 1))
    pygame.draw.ellipse(s, cap, (x - size, y - size - size // 2, size * 2 + 1, size))
    pygame.draw.line(s, mix(cap, (255, 255, 255), 0.5), (x - size // 2, y - size - size // 3),
                     (x + size // 3, y - size - size // 3))


def signpost(s, x, y, wood, wood2, direction, pal):
    """A post with one board pointing the way, standing with its foot at (x, y)."""
    pygame.draw.rect(s, wood, (x - 4, y - 68, 9, 72))
    pygame.draw.line(s, mix(wood, pal["rim"], 0.25), (x - 4, y - 68), (x - 4, y + 2))
    dx, dy = direction
    if dy > 0 and dx == 0:  # pointing down: a board with a downward chevron
        pygame.draw.rect(s, wood2, (x - 24, y - 64, 50, 18))
        pygame.draw.line(s, mix(wood2, pal["rim"], 0.35), (x - 24, y - 64), (x + 25, y - 64))
        pygame.draw.lines(s, wood, False, [(x - 8, y - 60), (x, y - 52), (x + 8, y - 60)], 3)
    else:
        bx = x if dx > 0 else x - 48
        pygame.draw.rect(s, wood2, (bx, y - 64, 48, 16))
        tip = bx + 48 if dx > 0 else bx
        pygame.draw.polygon(s, wood2, [(tip, y - 64), (tip + dx * 10, y - 56), (tip, y - 48)])
        pygame.draw.line(s, wood, (bx + 6, y - 56), (bx + 40, y - 56), 2)
