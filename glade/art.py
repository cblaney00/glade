"""Pixel-art drawing helpers, in the spirit of Rain World — but idyllic.

How the look is made:
- Everything is drawn on a small canvas (W x H) and scaled up with no smoothing.
- A scene is a stack of *depth planes* drawn back to front. Every colour is mixed
  toward the scene's mist colour by how far away its plane is, and a veil of mist is
  laid between planes, so distant shapes dissolve into pastel haze. That layered fog
  is where Rain World's depth comes from.
- No outlines. Shapes read by value against the mist, plus a thin sunlit rim on their
  top edges and a speckle of texture inside.
"""

import math

import pygame

W, H = 480, 270

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


# --- colour ---------------------------------------------------------------------

def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def at_depth(pal, color, d):
    """A material colour as seen from depth d (0 = right here, 1 = lost in the mist)."""
    near = mix(color, pal["shade"], 0.52 * (1 - d) ** 2.2)
    return mix(near, pal["mist"], d ** 1.35 * 0.9)


# --- surfaces ---------------------------------------------------------------------

def solid(size=(W, H)):
    """An opaque surface. Never use a bare pygame.Surface(size): under a compositor the
    screen has an alpha channel, plain surfaces inherit it and start fully transparent,
    and everything drawn through them comes out black."""
    return pygame.Surface(size, 0, 24)


def plane():
    return pygame.Surface((W, H), pygame.SRCALPHA)


def gradient(surf, rect, stops, steps=6):
    """Vertical gradient over rect in solid bands joined by an ordered-dither seam."""
    x0, y0, w, h = rect
    n = len(stops) - 1
    for yy in range(max(0, y0), min(surf.get_height(), y0 + h)):
        t = (yy - y0) / max(1, h - 1) * n
        i = min(int(t), n - 1)
        f = (t - i) * steps
        a, b = stops[i], stops[i + 1]
        lo, hi = mix(a, b, math.floor(f) / steps), mix(a, b, math.ceil(f) / steps)
        frac = f - math.floor(f)
        surf.fill(lo, (x0, yy, w, 1))
        row = BAYER[yy % 4]
        for x in range(x0, x0 + w):
            if frac * 16 > row[x % 4] + 0.5:
                surf.set_at((x, yy), hi)


def sky(pal):
    surf = solid()
    gradient(surf, (0, 0, W, H), pal["sky"])
    return surf


def mist_veil(pal, strength, low=0.0):
    """A sheet of mist to lay over everything drawn so far. `low` thickens it near
    the ground, like haze pooling in a valley."""
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(H):
        a = strength + low * max(0.0, (y - H * 0.35) / (H * 0.65)) ** 1.5
        s.fill((*pal["mist"], int(255 * min(1.0, a))), (0, y, W, 1))
    return s


def finish(lay, pal, d, rng, texture=1.0):
    """Sunlit rim along the top edges of everything on this plane, plus speckle."""
    mask = pygame.mask.from_surface(lay)
    count = mask.count()
    if count == 0:
        return lay
    glow_k = (1 - d) * 0.55 + 0.15
    for off, k in (((0, 1), 1.0), ((0, 2), 0.45)):
        top = mask.copy()
        top.erase(mask, off)
        lay.blit(top.to_surface(setcolor=(*pal["light"], int(255 * glow_k * k)), unsetcolor=(0, 0, 0, 0)), (0, 0))
    left = mask.copy()
    left.erase(mask, (1, 0))
    lay.blit(left.to_surface(setcolor=(*pal["light"], int(150 * glow_k)), unsetcolor=(0, 0, 0, 0)), (0, 0))
    # texture: a sprinkle of darker and lighter pixels inside the shapes
    for _ in range(int(count * 0.025 * texture)):
        x, y = rng.randrange(W), rng.randrange(H)
        if mask.get_at((x, y)):
            c = lay.get_at((x, y))
            k = 0.86 if rng.random() < 0.85 else 1.06
            lay.set_at((x, y), (min(255, int(c.r * k)), min(255, int(c.g * k)), min(255, int(c.b * k)), c.a))
    return lay


# --- shapes ---------------------------------------------------------------------------

def wave(x, phase, scales):
    return sum(math.sin(x / s + phase * (i + 1)) / (i + 1) for i, s in enumerate(scales))


def ridge(s, rng, y, amp, color, scales=(70, 23, 9), bottom=H):
    """A rolling silhouette edge to edge, filled down to `bottom`. Returns its height per x."""
    phase = rng.random() * 10
    tops = [int(y - amp * (0.5 + 0.35 * wave(x, phase, scales))) for x in range(W + 1)]
    pygame.draw.polygon(s, color, [(0, bottom)] + [(x, tops[x]) for x in range(0, W + 1, 2)] + [(W, bottom)])
    return tops


def canopy(s, rng, x0, x1, y, color, r=(7, 14), jitter=6, down=True):
    """A lumpy mass of foliage along a line, filled toward the bottom (or the top)."""
    x = x0
    while x < x1:
        rr = rng.randint(*r)
        cy = y + rng.randint(-jitter, jitter)
        pygame.draw.circle(s, color, (x, cy), rr)
        if down:
            pygame.draw.rect(s, color, (x - rr, cy, rr * 2, H - cy))
        else:
            pygame.draw.rect(s, color, (x - rr, 0, rr * 2, cy))
        x += rng.randint(rr // 2 + 2, rr + 2)


def clump(s, rng, cx, cy, r, color, n=9, squash=0.7):
    """A rounded cloud of leaves (tree crowns, bushes)."""
    for _ in range(n):
        a = rng.random() * math.tau
        dd = rng.random() * r * 0.6
        rr = int(r * (0.4 + rng.random() * 0.25))
        pygame.draw.circle(s, color, (int(cx + math.cos(a) * dd), int(cy + math.sin(a) * dd * squash)), rr)


def foliage(s, rng, cx, cy, rx, ry, color, pal, density=1.0, leaf=(2, 4)):
    """A mass of leaves with ragged, leafy edges: many little discs, a shaded
    underside, and a sunlit upper-left."""
    dark = mix(color, pal["shade"], 0.32)
    light = mix(color, pal["light"], 0.38)
    pts = []
    for _ in range(int(rx * ry / 5 * density) + 3):
        a = rng.random() * math.tau
        r = math.sqrt(rng.random())
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, rng.randint(*leaf)))
    for x, y, r in pts:
        pygame.draw.circle(s, dark, (int(x + 1), int(y + 2)), r)
    for x, y, r in pts:
        if (y - cy) / ry < 0.55:
            pygame.draw.circle(s, color, (int(x), int(y)), r)
    for x, y, r in pts:
        if (x - cx) / rx * 0.5 + (y - cy) / ry < -0.35:
            pygame.draw.circle(s, light, (int(x - 1), int(y - 1)), max(1, r - 1))


def trunk(s, rng, x, top, bottom, w, color, branches=2):
    """A tall, slightly leaning trunk that flares into roots."""
    lean = rng.uniform(-0.04, 0.04)
    pts_l, pts_r = [], []
    for y in list(range(top, bottom, 3)) + [bottom]:
        f = (y - top) / max(1, bottom - top)
        ww = w * (0.8 + 0.2 * f) + (w * 2.2 * ((f - 0.88) / 0.12) ** 2 if f > 0.88 else 0)
        cx = x + (bottom - y) * lean
        pts_l.append((cx - ww / 2, y))
        pts_r.append((cx + ww / 2, y))
    pygame.draw.polygon(s, color, pts_l + pts_r[::-1])
    for _ in range(branches):
        by = rng.randint(top, top + (bottom - top) // 2)
        side = rng.choice((-1, 1))
        ln = rng.randint(w * 2, w * 4)
        cx = x + (bottom - by) * lean
        pygame.draw.line(s, color, (cx, by), (cx + side * ln, by - ln // 2), max(1, w // 3))


def rock(s, rng, cx, cy, w, h, color, moss=None, mossiness=0.5):
    """A jagged boulder sitting on y=cy; with `moss`, a soft cap of moss over its top."""
    n = 11
    pts = []
    for i in range(n):
        a = math.pi + i / (n - 1) * math.pi  # top half, left to right
        rr = rng.uniform(0.82, 1.0)
        pts.append((cx + math.cos(a) * w / 2 * rr, cy + math.sin(a) * h * rr))
    base_r, base_l = (cx + w / 2 * 0.95, cy + h * 0.12), (cx - w / 2 * 0.95, cy + h * 0.12)
    tmp = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, color, pts + [base_r, base_l])
    # facets: the right-hand side is in shadow
    dark = mix(color, (20, 10, 40), 0.22)
    for i in range(n // 2 + 1, n - 1):
        pygame.draw.polygon(tmp, dark, [(cx + w * 0.08, cy + h * 0.12), pts[i], pts[i + 1]])
    pygame.draw.polygon(tmp, dark, [(cx + w * 0.08, cy + h * 0.12), pts[n - 1], base_r])
    if moss:
        mask = pygame.mask.from_surface(tmp)
        hi = mix(moss, (255, 255, 220), 0.3)
        for x in range(max(0, int(cx - w / 2)), min(W, int(cx + w / 2) + 1)):
            for y in range(max(0, int(cy - h - 2)), min(H, int(cy + h))):
                if not mask.get_at((x, y)):
                    continue
                depth = int(h * mossiness * (0.65 + 0.35 * math.sin(x * 0.37 + cx))) + rng.randint(0, 2)
                for yy in range(y, min(H, y + depth)):
                    if mask.get_at((x, yy)):
                        k = (yy - y) / max(1, depth)
                        if k < 0.7 or BAYER[yy % 4][x % 4] > (k - 0.7) * 50:
                            tmp.set_at((x, yy), hi if yy - y < 1 else moss)
                if rng.random() < 0.1:  # moss drips
                    for yy in range(y + depth, min(H, y + depth + rng.randint(2, 7))):
                        if mask.get_at((x, yy)):
                            tmp.set_at((x, yy), moss)
                break
    s.blit(tmp, (0, 0))


def grass_bed(s, rng, rect, color, n, hmax=4):
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        pygame.draw.line(s, color, (x, y), (x + rng.choice((-1, 0, 1)), y - rng.randint(1, hmax)))


def blossoms(s, rng, rect, colors, n, mask=None):
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        if mask is not None and not (0 <= x < W and 0 <= y < H and mask.get_at((x, y))):
            continue
        c = rng.choice(colors)
        s.set_at((x, y), c)
        if rng.random() < 0.5:
            s.set_at((x + 1, y), c)
            s.set_at((x, y + 1), mix(c, (40, 20, 60), 0.2))


def flowers(s, rng, rect, colors, n, centre=(255, 236, 140)):
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        c = rng.choice(colors)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s.set_at((x + dx, y + dy), c)
        s.set_at((x, y), centre)


def path(s, pts, widths, color, edge):
    """A trodden path along a polyline whose width changes (wide = near)."""
    left, right = [], []
    for i, (p, w) in enumerate(zip(pts, widths)):
        q = pts[min(i + 1, len(pts) - 1)]
        o = pts[max(i - 1, 0)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        left.append((p[0] + nx * w / 2, p[1] + ny * w / 2 * 0.6))
        right.append((p[0] - nx * w / 2, p[1] - ny * w / 2 * 0.6))
    poly = left + right[::-1]
    pygame.draw.polygon(s, edge, [(x, y + 1) for x, y in poly])
    pygame.draw.polygon(s, color, poly)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        steps = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2)
        for k in range(steps):
            f = k / max(1, steps)
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            w = widths[i] + (widths[i + 1] - widths[i]) * f
            if (k * 7 + i) % 4 == 0:
                s.set_at((int(x + math.sin(k * 2.3 + i) * w * 0.3), int(y + math.cos(k * 1.7) * 1.5)), edge)


def glow(s, x, y, r, color, strength=60):
    """Soft additive glow: concentric discs."""
    r = max(1, int(r))
    key = (r, color, strength)
    g = _GLOWS.get(key)
    if g is None:
        g = solid((r * 2 + 1, r * 2 + 1))
        for i in range(r, 0, -1):
            k = strength / 255 * (1 - i / (r + 1)) ** 1.6
            pygame.draw.circle(g, tuple(int(c * k) for c in color), (r, r), i)
        _GLOWS[key] = g
    s.blit(g, (int(x) - r, int(y) - r), special_flags=pygame.BLEND_RGB_ADD)


_GLOWS = {}


def sprite(rows, colors):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set_at((x, y), colors[ch])
    return s
