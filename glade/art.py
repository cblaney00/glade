"""Pixel-art drawing helpers.

Everything is drawn on a small canvas (W x H) and scaled up with no smoothing,
so plain non-antialiased pygame shapes come out as chunky pixels.
"""

import math

import pygame

W, H = 480, 270

# --- Palette: bright pastels with a deep indigo outline -----------------------
OUT = (46, 36, 84)

SKY = [(146, 196, 255), (190, 186, 255), (255, 200, 236), (255, 232, 214)]
CLOUD = ((255, 255, 255), (255, 226, 246), (214, 200, 255))

HILL_FAR = (196, 170, 240)
HILL_MID = (150, 210, 220)

GRASS = ((52, 150, 130), (88, 202, 150), (140, 236, 168), (206, 255, 178))
LEAF = ((44, 120, 128), (72, 178, 146), (122, 222, 160), (196, 255, 184))
LEAF_PINK = ((176, 96, 168), (232, 132, 196), (255, 178, 222), (255, 222, 240))
LEAF_LAV = ((106, 92, 180), (150, 132, 230), (196, 178, 255), (232, 222, 255))

PATH = ((214, 150, 122), (255, 206, 160), (255, 232, 196))
WOOD = ((128, 78, 96), (196, 126, 110), (236, 176, 140))
ROCK = ((96, 92, 156), (146, 140, 210), (192, 186, 240), (226, 222, 255))
MOSS = ((60, 168, 110), (122, 220, 120), (190, 250, 140))
WATER = ((70, 150, 230), (90, 200, 240), (150, 236, 255), (232, 255, 255))

PINK = (255, 132, 196)
YELLOW = (255, 228, 104)
PURPLE = (190, 140, 255)
PEACH = (255, 164, 128)
WHITE = (255, 255, 255)
CREAM = (255, 244, 222)
RED = (255, 98, 128)

FLOWER_COLORS = [PINK, YELLOW, PURPLE, PEACH, WHITE, (120, 220, 255)]

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def gradient(surf, rect, stops):
    """Vertical gradient in solid bands joined by an ordered-dither seam."""
    x0, y0, w, h = rect
    n = len(stops) - 1
    px = pygame.PixelArray(surf)
    try:
        for y in range(h):
            t = y / max(1, h - 1) * n
            i = min(int(t), n - 1)
            f = (t - i - 0.3) / 0.4
            f = max(0.0, min(1.0, f))
            a = surf.map_rgb(stops[i])
            b = surf.map_rgb(stops[i + 1])
            row = BAYER[(y0 + y) % 4]
            for x in range(w):
                px[x0 + x, y0 + y] = b if f * 16 > row[(x0 + x) % 4] + 0.5 else a
    finally:
        del px


def dither_rect(surf, rect, color, density):
    """Sprinkle `color` over rect in an ordered pattern (0..1 density)."""
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if density * 16 > BAYER[y % 4][x % 4] + 0.5:
                surf.set_at((x, y), color)


def layer():
    return pygame.Surface((W, H), pygame.SRCALPHA)


def stamp(base, lay, outline=OUT):
    """Blit a layer onto base with a 1px cartoon outline around its shape."""
    if outline is not None:
        sil = pygame.mask.from_surface(lay).to_surface(
            setcolor=outline, unsetcolor=(0, 0, 0, 0)
        )
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            base.blit(sil, (dx, dy))
    base.blit(lay, (0, 0))


def blob(s, cx, cy, r, pal, rng, speck=True):
    """One leafy/fluffy clump: dark rim, body, light top, sparkle specks."""
    dark, base, light, hi = pal
    pygame.draw.circle(s, dark, (cx, cy), r)
    pygame.draw.circle(s, base, (cx - 1, cy - 2), max(1, r - 2))
    pygame.draw.circle(s, light, (cx - r // 3, cy - r // 2), max(1, r // 2))
    if speck:
        for _ in range(r):
            a = rng.random() * math.tau
            d = rng.random() * (r - 2)
            x, y = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)
            s.set_at((x, y), hi if y < cy else dark)


def crown(s, cx, cy, r, pal, rng, n=7):
    """A tree crown built from several clumps, shaded bottom-up."""
    pts = []
    for _ in range(n):
        a = rng.random() * math.tau
        d = rng.random() * r * 0.6
        pts.append((int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.7)))
    pts.sort(key=lambda p: -p[1])
    for x, y in pts:
        blob(s, x, y, int(r * (0.45 + rng.random() * 0.2)), pal, rng)


def trunk(s, x, top, bottom, w, pal=WOOD):
    dark, base, light = pal
    pygame.draw.rect(s, base, (x - w // 2, top, w, bottom - top))
    pygame.draw.rect(s, dark, (x + w // 2 - max(2, w // 3), top, max(2, w // 3), bottom - top))
    pygame.draw.rect(s, light, (x - w // 2 + 1, top, max(1, w // 5), bottom - top))
    # roots
    pygame.draw.polygon(s, base, [(x - w // 2, bottom - 4), (x - w, bottom), (x + w, bottom), (x + w // 2, bottom - 4)])
    pygame.draw.line(s, dark, (x + w // 2, bottom - 4), (x + w, bottom))


def tree(s, x, ground, height, rng, pal=LEAF, w=None):
    w = w or max(4, height // 8)
    trunk(s, x, ground - height + height // 3, ground, w)
    crown(s, x, ground - height + height // 4, height // 3, pal, rng)


def rock(s, cx, cy, w, h, rng, moss=True, pal=ROCK):
    dark, base, light, hi = pal
    pygame.draw.ellipse(s, dark, (cx - w // 2, cy - h // 2, w, h))
    pygame.draw.ellipse(s, base, (cx - w // 2 + 1, cy - h // 2, w - 4, h - 3))
    pygame.draw.ellipse(s, light, (cx - w // 2 + w // 6, cy - h // 2 + 2, w // 2, h // 3))
    s.set_at((cx - w // 4, cy - h // 3), hi)
    if moss:
        mdark, mbase, mlight = MOSS
        for i in range(max(3, w // 5)):
            a = math.pi + (i + rng.random()) / max(3, w // 5) * math.pi
            mx = int(cx + math.cos(a) * w * 0.38)
            my = int(cy + math.sin(a) * h * 0.38)
            r = 2 + rng.randrange(max(1, w // 10))
            pygame.draw.circle(s, mdark, (mx, my + 1), r)
            pygame.draw.circle(s, mbase, (mx, my), r)
            pygame.draw.circle(s, mlight, (mx - 1, my - 1), max(1, r // 2))
        # a few drips of moss hanging down the sides
        for _ in range(w // 8):
            dx = rng.randint(-w // 3, w // 3)
            top = cy - h // 3
            pygame.draw.line(s, mbase, (cx + dx, top), (cx + dx, top + rng.randint(2, h // 3)))


def mushroom(s, x, y, size, cap=RED):
    sw = max(2, size // 2)
    pygame.draw.rect(s, CREAM, (x - sw // 2, y - size, sw, size))
    pygame.draw.ellipse(s, cap, (x - size, y - size - size // 2 - 1, size * 2, size + 2))
    pygame.draw.rect(s, cap, (x - size, y - size - 1, size * 2, 1))
    s.set_at((x - size // 2, y - size - size // 3), WHITE)
    s.set_at((x + size // 3, y - size - size // 2 + 1), WHITE)
    if size > 3:
        s.set_at((x, y - size - size // 4), WHITE)


def flower(s, x, y, color, rng):
    stem = rng.randint(2, 5)
    pygame.draw.line(s, GRASS[0], (x, y), (x, y - stem))
    y -= stem
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set_at((x + dx, y + dy), color)
    s.set_at((x, y), YELLOW if color != YELLOW else WHITE)


def tuft(s, x, y, rng, pal=GRASS):
    for dx in (-1, 0, 1):
        h = rng.randint(2, 5)
        pygame.draw.line(s, pal[0], (x + dx * 2, y), (x + dx * 2 + dx, y - h))
        s.set_at((x + dx * 2 + dx, y - h), pal[3])


def scatter(s, rect, n, rng, fn):
    x0, y0, w, h = rect
    for _ in range(n):
        fn(s, x0 + rng.randrange(w), y0 + rng.randrange(h))


def meadow_detail(s, rect, rng, flowers=40, tufts=40, colors=FLOWER_COLORS):
    scatter(s, rect, tufts, rng, lambda s, x, y: tuft(s, x, y, rng))
    scatter(s, rect, flowers, rng, lambda s, x, y: flower(s, x, y, rng.choice(colors), rng))


def cloud(s, x, y, size, rng):
    white, pink, shade = CLOUD
    parts = [(x + rng.randint(-size, size), y + rng.randint(-size // 3, size // 4), rng.randint(size // 2, size)) for _ in range(5)]
    for px, py, r in parts:
        pygame.draw.circle(s, shade, (px, py + 2), r)
    for px, py, r in parts:
        pygame.draw.circle(s, pink, (px, py), r)
    for px, py, r in parts:
        pygame.draw.circle(s, white, (px - 1, py - 2), max(1, r - 2))


def hills(s, y, amp, color, rng, step=40, light=None):
    """A rolling silhouette from the left edge to the right edge, filled down to H."""
    pts = [(0, H)]
    phase = rng.random() * 10
    for x in range(0, W + step, 4):
        yy = y - amp * (0.5 + 0.5 * math.sin(x / step + phase)) - amp * 0.4 * math.sin(x / (step * 0.37) + phase * 2)
        pts.append((x, int(yy)))
    pts.append((W, H))
    pygame.draw.polygon(s, color, pts)
    if light:
        for (x1, y1), (x2, y2) in zip(pts[1:-2], pts[2:-1]):
            pygame.draw.line(s, light, (x1, y1), (x2, y2))


def treeline(s, y, rng, pal=LEAF, spacing=14, r=12, jitter=8):
    x = -r
    while x < W + r:
        blob(s, x, y + rng.randint(-jitter, jitter // 2), r + rng.randint(-3, 3), pal, rng)
        x += spacing + rng.randint(-3, 3)


def path(s, pts, widths, rng, pebbles=True):
    """A sandy path along a polyline that changes width (for perspective)."""
    dark, base, light = PATH
    left, right = [], []
    for i, (p, w) in enumerate(zip(pts, widths)):
        q = pts[min(i + 1, len(pts) - 1)] if i < len(pts) - 1 else p
        o = pts[i - 1] if i > 0 else p
        dx, dy = q[0] - o[0], q[1] - o[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        left.append((p[0] + nx * w / 2, p[1] + ny * w / 2))
        right.append((p[0] - nx * w / 2, p[1] - ny * w / 2))
    poly = left + right[::-1]
    pygame.draw.polygon(s, dark, [(x, y + 2) for x, y in poly])
    pygame.draw.polygon(s, base, poly)
    inner = []
    for (lx, ly), (rx, ry) in zip(left, right):
        inner.append((lx * 0.7 + rx * 0.3, ly * 0.7 + ry * 0.3))
    for (lx, ly), (rx, ry) in zip(reversed(left), reversed(right)):
        inner.append((lx * 0.35 + rx * 0.65, ly * 0.35 + ry * 0.65))
    pygame.draw.polygon(s, light, inner)
    if pebbles:
        for i in range(len(pts) - 1):
            for _ in range(int(widths[i] / 3)):
                f = rng.random()
                x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
                y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
                w = widths[i] * 0.8
                s.set_at((int(x + rng.uniform(-w / 2, w / 2)), int(y + rng.uniform(-2, 2))), dark)


def sign(s, x, y, w, h, color):
    pygame.draw.rect(s, color, (x, y, w, h))
    pygame.draw.rect(s, tuple(min(255, c + 40) for c in color), (x, y, w, 1))
    pygame.draw.rect(s, tuple(max(0, c - 60) for c in color), (x, y + h - 1, w, 1))


# --- Sprites for the custom cursor --------------------------------------------

def sprite(rows, colors):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set_at((x, y), colors[ch])
    return s
