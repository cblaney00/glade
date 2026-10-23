"""Pixel-art drawing helpers, in the spirit of Rain World — but idyllic, and at night.

How the look is made:
- Everything is drawn on a small canvas (W x H) and scaled up 2x with no smoothing.
- A scene is a stack of *depth planes* drawn back to front. Every colour is mixed
  toward the scene's mist colour by how far away its plane is, and a veil of mist is
  laid between planes, so distant shapes dissolve into violet night haze. That
  layered fog is where Rain World's depth comes from.
- No outlines. Shapes read by value against the mist, plus a thin rim of moonlight on
  the edges facing the moon, a darker underside, and a little texture inside.
- Lighting is real, not painted on: each scene has a *light map* — dim moonlit
  ambient, plus pools of coloured light around everything that glows (moss,
  mushrooms, lanterns, fireflies, squid). The picture is multiplied by it, so only
  what is near a light shows its colour, and then the glowing things themselves are
  added on top (see `Lighting`).
"""

import math
import random

import pygame

W, H = 960, 540
S = 2  # canvas pixels per pixel of the original 480x270 design

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# The colours things glow in.
GLOW = dict(
    moss=(110, 255, 190), lime=(190, 255, 120), cyan=(110, 226, 255), pink=(255, 130, 220),
    violet=(186, 140, 255), amber=(255, 196, 120), firefly=(214, 255, 130), white=(236, 240, 255),
)


# --- colour ---------------------------------------------------------------------

def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def at_depth(pal, color, d):
    """A material colour as seen from depth d (0 = right here, 1 = lost in the mist)."""
    near = mix(color, pal["shade"], 0.5 * (1 - d) ** 2.2)
    return mix(near, pal["mist"], d ** 1.25 * 0.88)


# --- surfaces ---------------------------------------------------------------------

def solid(size=(W, H)):
    """An opaque surface. Never use a bare pygame.Surface(size): under a compositor the
    screen has an alpha channel, plain surfaces inherit it and start fully transparent,
    and everything drawn through them comes out black. 32-bit with no alpha channel,
    not 24-bit: whole-screen copies of 24-bit pixels are several times slower."""
    return pygame.Surface(size, 0, 32, (0xFF0000, 0xFF00, 0xFF, 0))


def plane(size=(W, H)):
    return pygame.Surface(size, pygame.SRCALPHA)


def trimmed(surf):
    """A see-through layer cut down to the part that has anything on it, and where
    that part goes — so drawing it every frame does not blend a whole empty screen.
    None if it is empty."""
    r = surf.get_bounding_rect()
    if r.w == 0 or r.h == 0:
        return None
    return surf.subsurface(r).copy(), r.topleft


def gradient(surf, rect, stops, steps=6):
    """Vertical gradient over rect in solid bands joined by an ordered-dither seam.
    Painted as one 4-pixel-wide strip (the dither repeats every 4 pixels) and tiled."""
    x0, y0, w, h = rect
    n = len(stops) - 1
    strip = solid((4, h))
    for i_y in range(h):
        yy = y0 + i_y
        t = i_y / max(1, h - 1) * n
        i = min(int(t), n - 1)
        f = (t - i) * steps
        a, b = stops[i], stops[i + 1]
        lo, hi = mix(a, b, math.floor(f) / steps), mix(a, b, math.ceil(f) / steps)
        frac = f - math.floor(f)
        row = BAYER[yy % 4]
        for x in range(4):
            strip.set_at((x, i_y), hi if frac * 16 > row[(x0 + x) % 4] + 0.5 else lo)
    for x in range(x0, x0 + w, 4):
        surf.blit(strip, (x, y0), (0, 0, min(4, x0 + w - x), h))


def mist_veil(pal, strength, low=0.0, size=(W, H)):
    """A sheet of mist to lay over everything drawn so far. `low` thickens it near
    the ground, like haze pooling in a valley."""
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        a = strength + low * max(0.0, (y - h * 0.35) / (h * 0.65)) ** 1.5
        s.fill((*pal["mist"], int(255 * min(1.0, a))), (0, y, w, 1))
    return s


def finish(lay, pal, d, rng, texture=1.0):
    """Moonlit rim on the edges facing the moon, a shaded underside, and texture."""
    mask = pygame.mask.from_surface(lay)
    count = mask.count()
    if count == 0:
        return lay
    side = pal.get("moon_side", -1)  # -1: the moon is to the left
    rim = pal["rim"]
    glow_k = (1 - d) * 0.5 + 0.15
    for off, k in (((0, 1), 0.85), ((0, 2), 0.35)):
        top = mask.copy()
        top.erase(mask, off)
        lay.blit(top.to_surface(setcolor=(*rim, int(255 * glow_k * k)), unsetcolor=(0, 0, 0, 0)), (0, 0))
    edge = mask.copy()
    edge.erase(mask, (-side, 0))
    lay.blit(edge.to_surface(setcolor=(*rim, int(170 * glow_k)), unsetcolor=(0, 0, 0, 0)), (0, 0))
    # undersides and the side away from the moon sink into shadow: volume, not flat cut-outs
    for off, a in (((0, -1), 110), ((0, -2), 60), ((side, 0), 70)):
        under = mask.copy()
        under.erase(mask, off)
        lay.blit(under.to_surface(setcolor=(*pal["shade"], int(a * (1 - d * 0.6))), unsetcolor=(0, 0, 0, 0)), (0, 0))
    # texture: a sparse sprinkle of darker pixels, in little vertical pairs
    w, h = lay.get_size()
    for _ in range(int(count * 0.008 * texture)):
        x, y = rng.randrange(w), rng.randrange(h - 1)
        if mask.get_at((x, y)):
            c = lay.get_at((x, y))
            k = 0.84 if rng.random() < 0.8 else 1.08
            cc = (min(255, int(c.r * k)), min(255, int(c.g * k)), min(255, int(c.b * k)), c.a)
            lay.set_at((x, y), cc)
            if mask.get_at((x, y + 1)):
                lay.set_at((x, y + 1), cc)
    return lay


# --- light --------------------------------------------------------------------------

def glow(s, x, y, r, color, strength=60):
    """Soft additive glow: concentric discs, stepped like pixel art."""
    r = max(1, int(r))
    key = (r, color, strength)
    g = _GLOWS.get(key)
    if g is None:
        g = solid((r * 2 + 1, r * 2 + 1))
        for i in range(r, 0, -1):
            k = strength / 255 * (1 - i / (r + 1)) ** 1.8
            pygame.draw.circle(g, tuple(int(c * k) for c in color), (r, r), i)
        if len(_GLOWS) > 4000:
            _GLOWS.clear()
        _GLOWS[key] = g
    s.blit(g, (int(x) - r, int(y) - r), special_flags=pygame.BLEND_RGB_ADD)


_GLOWS = {}


def soft_ellipse(rx, ry, color, alpha):
    """An alpha ellipse that fades out toward its edge (for shadows and haze)."""
    s = pygame.Surface((rx * 2 + 1, ry * 2 + 1), pygame.SRCALPHA)
    n = max(2, min(rx, ry) // 2)
    for i in range(n, 0, -1):
        k = i / n
        a = int(alpha * (1 - k) ** 0.8 / n * 2.2)
        e = pygame.Rect(0, 0, int(rx * 2 * k) + 1, int(ry * 2 * k) + 1)
        e.center = (rx, ry)
        pygame.draw.ellipse(s, (*color, min(255, a)), e)
    return s


class Lighting:
    """The light map of one picture, and how it is applied.

    `light` starts as moonlit ambient (brighter up in the sky, dimmer near the
    ground) and collects pools of coloured light at build time; `emit` collects
    pixels that glow by themselves. Every frame: the picture (drawn in its true,
    fully-lit colours) is multiplied by the light map plus whatever moving lights
    there are, then the glowing pixels are added on top."""

    def init_light(self, pal, size=(W, H), lower=False):
        w, h = size
        top, bottom = pal["ambient"]
        self.light = solid((W, H))
        if lower:  # the ground in front of you: the darkest ambient, a little brighter far away
            gradient(self.light, (0, 0, w, h), [mix(bottom, top, 0.15), scale(bottom, 0.85)], steps=8)
        else:
            # bright only high in the sky; everything standing lower sits in the dark
            # until something glowing lights it
            gradient(self.light, (0, 0, W, H), [top, mix(top, bottom, 0.45), mix(top, bottom, 0.8), bottom], steps=8)
        self.emit = solid((W, H))
        self.emit.fill((0, 0, 0))

    def lamp(self, x, y, r, color, strength=80):
        glow(self.light, x, y, r, color, strength)

    def shine(self, x, y, r, color, strength=60):
        glow(self.emit, x, y, r, color, strength)

    def shadow(self, x, y, rx, ry, k=0.5):
        """Darken the light map softly: contact shadows under things, shade under canopies."""
        e = soft_ellipse(int(rx), int(ry), (255, 255, 255), int(255 * k))
        dark = solid(e.get_size())
        dark.fill((0, 0, 0))
        dark.blit(e, (0, 0))
        self.light.blit(dark, (int(x - rx), int(y - ry)), special_flags=pygame.BLEND_RGB_SUB)

    def lit(self, s, parts, t):
        """Apply the lighting to s, whose picture has been drawn already."""
        lm = self.light.copy()
        parts = [p for p in parts if not getattr(p, "gone", False)]  # eaten (apex.py)
        for p in parts:
            f = getattr(p, "light", None)
            if f:
                f(lm, t)
        s.blit(lm, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        s.blit(self.emit, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        for p in parts:
            f = getattr(p, "shine", None)
            if f:
                f(s, t)


def glowmoss(lit, lay, x, y, w, h, color=None, strength=80, specks=1.0):
    """A cushion of fluorescent moss: a few soft mounds, dark at the base and glowing
    toward the top, sprouting thin stalks with shining spore capsules. It lights up
    the ground around it. `lit` is the picture's Lighting (and has an rng)."""
    rng, color = lit.rng, color or GLOW["moss"]
    mid = mix(color, (20, 52, 60), 0.5)
    tone = dict(shade=(8, 22, 34), rim=mix(color, (255, 255, 255), 0.2), moon_side=-1)
    n = max(2, int(w / 16))
    lumps = []
    for i in range(n):
        lx = x - w / 2 + (i + 0.5) * w / n + rng.uniform(-w / n * 0.3, w / n * 0.3)
        lumps.append((lx, y + rng.uniform(-h * 0.25, h * 0.25), w / n * rng.uniform(0.7, 1.05), h * rng.uniform(0.45, 0.75)))
    lumps.sort(key=lambda l: l[1])
    shadow = mix(tone["shade"], (30, 40, 60), 0.3)
    pygame.draw.ellipse(lay, shadow, (x - w / 2 - 2, y - 1, w + 4, h * 0.6 + 3))
    for lx, ly, rw, rh in lumps:
        foliage(lay, rng, lx, ly, rw, rh, mid, tone, density=2.2, leaf=(1, 3))
    cap = mix(color, (255, 255, 255), 0.45)
    for _ in range(int(w * specks / 5) + 2):
        lx, ly, rw, rh = rng.choice(lumps)
        px, py = int(lx + rng.uniform(-rw * 0.7, rw * 0.7)), int(ly - rh * 0.55 + rng.uniform(-2, 2))
        hgt = rng.randint(3, 8)
        pygame.draw.line(lay, mid, (px, py), (px + rng.choice((-1, 0, 1)), py - hgt))
        lay.set_at((px, py - hgt), cap)
        if 0 <= px < W and 0 <= py - hgt < H:
            lit.emit.set_at((px, py - hgt), scale(color, 0.8))
    lit.lamp(x, y, int(w * 0.9 + 26), color, strength)
    lit.shine(x, y - h * 0.3, int(w * 0.45 + 4), color, 24)


# --- shapes ---------------------------------------------------------------------------

def wave(x, phase, scales):
    return sum(math.sin(x / s + phase * (i + 1)) / (i + 1) for i, s in enumerate(scales))


def ridge(s, rng, y, amp, color, scales=(140, 46, 18), bottom=H):
    """A rolling silhouette edge to edge, filled down to `bottom`. Returns its height per x."""
    phase = rng.random() * 10
    tops = [int(y - amp * (0.5 + 0.35 * wave(x, phase, scales))) for x in range(W + 1)]
    pygame.draw.polygon(s, color, [(0, bottom)] + [(x, tops[x]) for x in range(0, W + 1, 2)] + [(W, bottom)])
    return tops


def mountains(s, rng, y, amp, color, scales=(140, 46, 18), side=-1):
    """Far mountains: a ridge with rocky faces. Slopes facing the moon (`side` -1: it is
    to the left) catch a little light and the others fall into shade; spurs run down
    from every peak, lit on the moon's side and shadowed on the other, and the rock is
    broken by ledges."""
    tops = ridge(s, rng, y, amp, color, scales)
    rng = random.Random(y * 1000 + amp)  # its own dice, so the rest of the scene stays put
    lit, hi = mix(color, (255, 255, 255), 0.16), mix(color, (255, 255, 255), 0.26)
    shade, deep = mix(color, (12, 10, 40), 0.24), mix(color, (12, 10, 40), 0.42)
    depth = max(12, int(amp * 0.9))
    for x in range(1, W):
        slope = (tops[min(W, x + 3)] - tops[max(0, x - 3)]) * -side  # > 0: faces the moon
        band = int(depth * (0.55 + 0.45 * wave(x, 3.1, (37, 13, 5))))
        if slope > 1:
            pygame.draw.line(s, lit, (x, tops[x] + 1), (x, tops[x] + int(band * min(1.0, slope / 4))))
            s.set_at((x, tops[x]), hi)
        elif slope < -1:
            pygame.draw.line(s, shade, (x, tops[x] + 1), (x, tops[x] + band))
    # spurs: ridgelines running down and out from each peak
    peaks = []
    for x in range(24, W - 24, 2):
        if tops[x] == min(tops[x - 24:x + 25]) and (not peaks or x - peaks[-1] > 48):
            peaks.append(x)
    for px in peaks:
        for d in (-1, 1):
            for _ in range(1):
                x, yy = float(px), tops[px] + 1
                run = rng.uniform(0.9, 1.5) * d
                for _ in range(rng.randint(depth // 3, depth * 2 // 3 + 4)):
                    xi = int(x)
                    if not (1 <= xi < W - 1) or yy <= tops[xi]:
                        break
                    s.set_at((xi - side, yy), hi if d == side else lit)  # the moon side of the spur
                    s.set_at((xi, yy), deep)
                    s.set_at((xi + 1 if side < 0 else xi - 1, yy), shade)
                    x += run + rng.uniform(-0.8, 0.8)
                    yy += 1
    # ledges: short slabs of rock, lit on top with a dark lip under them
    for _ in range(int(W * amp / 90)):
        x = rng.randrange(4, W - 14)
        yy = rng.randint(tops[x] + 4, max(tops[x] + 5, tops[x] + depth))
        ln = rng.randint(3, 10)
        if all(yy > tops[min(W, x + i)] + 3 for i in range(ln)):
            pygame.draw.line(s, lit, (x, yy), (x + ln, yy))
            pygame.draw.line(s, deep, (x + 1, yy + 1), (x + ln + 1, yy + 1))
    return tops


def canopy(s, rng, x0, x1, y, color, r=(14, 28), jitter=12, down=True):
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
        x += rng.randint(rr // 2 + 3, rr + 3)


def clump(s, rng, cx, cy, r, color, n=9, squash=0.7):
    """A rounded cloud of leaves (tree crowns, bushes)."""
    for _ in range(n):
        a = rng.random() * math.tau
        dd = rng.random() * r * 0.6
        rr = int(r * (0.4 + rng.random() * 0.25))
        pygame.draw.circle(s, color, (int(cx + math.cos(a) * dd), int(cy + math.sin(a) * dd * squash)), rr)


def foliage(s, rng, cx, cy, rx, ry, color, pal, density=1.0, leaf=(3, 6)):
    """A mass of leaves with ragged, leafy edges: many little discs in four tones, a
    shaded underside and a moonlit side."""
    side = pal.get("moon_side", -1)
    dark = mix(color, pal["shade"], 0.42)
    mid = mix(color, pal["shade"], 0.18)
    light = mix(color, pal["rim"], 0.34)
    pts = []
    for _ in range(int(rx * ry / 14 * density) + 3):
        a = rng.random() * math.tau
        r = math.sqrt(rng.random())
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, rng.randint(*leaf)))
    for x, y, r in pts:
        pygame.draw.circle(s, dark, (int(x - side), int(y + 3)), r)
    for x, y, r in pts:
        if (y - cy) / ry < 0.62:
            pygame.draw.circle(s, mid, (int(x), int(y)), r)
    for x, y, r in pts:
        if (y - cy) / ry < 0.3:
            pygame.draw.circle(s, color, (int(x + side), int(y - 1)), max(1, r - 1))
    for x, y, r in pts:
        if (x - cx) / rx * 0.5 * -side + (y - cy) / ry < -0.45:
            pygame.draw.circle(s, light, (int(x + side * 2), int(y - 2)), max(1, r - 2))


def trunk(s, rng, x, top, bottom, w, color, branches=2, pal=None):
    """A tall, slightly leaning trunk that flares into roots, with bark streaks.
    Returns its lean: at height y its middle is at x + (bottom - y) * lean."""
    lean = rng.uniform(-0.04, 0.04)
    pts_l, pts_r = [], []
    for y in list(range(top, bottom, 4)) + [bottom]:
        f = (y - top) / max(1, bottom - top)
        ww = w * (0.8 + 0.2 * f) + (w * 2.2 * ((f - 0.88) / 0.12) ** 2 if f > 0.88 else 0)
        cx = x + (bottom - y) * lean
        pts_l.append((cx - ww / 2, y))
        pts_r.append((cx + ww / 2, y))
    pygame.draw.polygon(s, color, pts_l + pts_r[::-1])
    if w >= 6:  # bark: long darker streaks, and a lit stripe on the moon side
        dark = mix(color, (14, 10, 36), 0.25)
        side = pal.get("moon_side", -1) if pal else -1
        for _ in range(max(2, w // 3)):
            fx = rng.uniform(-0.35, 0.35)
            y0 = rng.randint(top, bottom - 10)
            y1 = min(bottom, y0 + rng.randint(12, 60))
            for y in range(y0, y1, 2):
                f = (y - top) / max(1, bottom - top)
                cx = x + (bottom - y) * lean
                s.set_at((int(cx + fx * w * (0.8 + 0.2 * f)), y), dark)
        if pal:
            lit = mix(color, pal["rim"], 0.22)
            for (lx, ly), (rx_, ry_) in zip(pts_l, pts_r):
                ex = lx + 1 if side < 0 else rx_ - 2
                pygame.draw.line(s, lit, (ex, ly), (ex, ly + 3))
    for _ in range(branches):
        by = rng.randint(top, top + (bottom - top) // 2)
        side = rng.choice((-1, 1))
        ln = rng.randint(w * 2, w * 4)
        cx = x + (bottom - by) * lean
        pygame.draw.line(s, color, (cx, by), (cx + side * ln, by - ln // 2), max(1, w // 3))
        pygame.draw.line(s, color, (cx + side * ln * 0.6, by - ln * 0.3),
                         (cx + side * ln * 0.9, by - ln * 0.75), max(1, w // 5))
    return lean


def rock(s, rng, cx, cy, w, h, color, moss=None, mossiness=0.5, glow_pts=None):
    """A jagged, faceted boulder sitting on y=cy; with `moss`, a soft cap of moss over
    its top. If `glow_pts` is a list, points along the moss cap are appended to it
    (where the glowing moss should be lit)."""
    n = 13
    pts = []
    for i in range(n):
        a = math.pi + i / (n - 1) * math.pi  # top half, left to right
        rr = rng.uniform(0.84, 1.0)
        pts.append((cx + math.cos(a) * w / 2 * rr, cy + math.sin(a) * h * rr))
    base_r, base_l = (cx + w / 2 * 0.95, cy + h * 0.12), (cx - w / 2 * 0.95, cy + h * 0.12)
    bw, bh = int(w + 8), int(h * 1.3 + 8)
    ox, oy = int(cx - w / 2 - 4), int(cy - h - 4)
    tmp = pygame.Surface((bw, bh), pygame.SRCALPHA)
    loc = lambda p: (p[0] - ox, p[1] - oy)  # noqa: E731
    pygame.draw.polygon(tmp, color, [loc(p) for p in pts + [base_r, base_l]])
    # facets: the right-hand side is in shadow, a lighter face up top-left
    dark = mix(color, (14, 8, 34), 0.3)
    hub = loc((cx + w * 0.08, cy + h * 0.12))
    for i in range(n // 2 + 1, n - 1):
        pygame.draw.polygon(tmp, dark, [hub, loc(pts[i]), loc(pts[i + 1])])
    pygame.draw.polygon(tmp, dark, [hub, loc(pts[n - 1]), loc(base_r)])
    lite = mix(color, (220, 220, 255), 0.12)
    pygame.draw.polygon(tmp, lite, [loc((cx - w * 0.1, cy - h * 0.3)), loc(pts[2]), loc(pts[3]), loc(pts[4])])
    # a few cracks
    for _ in range(max(1, int(w // 40))):
        x0, y0 = cx + rng.uniform(-w * 0.3, w * 0.3), cy - h * rng.uniform(0.2, 0.7)
        pygame.draw.line(tmp, mix(color, (14, 8, 34), 0.45), loc((x0, y0)),
                         loc((x0 + rng.uniform(-6, 6), y0 + rng.uniform(4, 12))))
    if moss:
        mask = pygame.mask.from_surface(tmp)
        hi = mix(moss, (240, 255, 230), 0.35)
        deep = mix(moss, (10, 30, 40), 0.3)
        tones = [moss] * 7 + [deep, deep, hi]  # mottled, not one flat slab
        for x in range(bw):
            for y in range(bh):
                if not mask.get_at((x, y)):
                    continue
                gx = x + ox
                depth = int(h * mossiness * (0.65 + 0.35 * math.sin(gx * 0.19 + cx))) + rng.randint(0, 3)
                for yy in range(y, min(bh, y + depth)):
                    if mask.get_at((x, yy)):
                        k = (yy - y) / max(1, depth)
                        if k < 0.7 or BAYER[yy % 4][x % 4] > (k - 0.7) * 50:
                            tmp.set_at((x, yy), hi if yy - y < 2 else tones[rng.randrange(10)])
                if rng.random() < 0.06:  # moss drips
                    for yy in range(y + depth, min(bh, y + depth + rng.randint(3, 12))):
                        if mask.get_at((x, yy)):
                            tmp.set_at((x, yy), moss)
                if x % 5 == 0 and y > 2:  # little tufts standing up off the top
                    for k in range(rng.randint(1, 3)):
                        tmp.set_at((x + rng.choice((-1, 0, 0, 1)) * (k > 0), y - 1 - k), hi)
                if glow_pts is not None and x % 9 == 0:
                    glow_pts.append((gx, y + oy + 2))
                break
    s.blit(tmp, (ox, oy))


def grass_bed(s, rng, rect, color, n, hmax=6):
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        pygame.draw.line(s, color, (x, y), (x + rng.choice((-1, 0, 1)), y - rng.randint(2, hmax)))


def blossoms(s, rng, rect, colors, n, mask=None):
    x0, y0, w, h = rect
    sw, sh = s.get_size()
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        if mask is not None and not (0 <= x < sw and 0 <= y < sh and mask.get_at((x, y))):
            continue
        c = rng.choice(colors)
        s.set_at((x, y), c)
        s.set_at((x + 1, y), c)
        s.set_at((x, y + 1), mix(c, (40, 20, 60), 0.25))
        if rng.random() < 0.4:
            s.set_at((x + 1, y + 1), mix(c, (40, 20, 60), 0.35))


def flowers(s, rng, rect, colors, n, centre=(255, 236, 140)):
    """Little five-pixel flowers on short stems."""
    x0, y0, w, h = rect
    for _ in range(n):
        x, y = x0 + rng.randrange(w), y0 + rng.randrange(max(1, h))
        c = rng.choice(colors)
        s.set_at((x, y + 2), (50, 110, 110))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s.set_at((x + dx, y + dy), c)
        s.set_at((x, y), centre)


# Every path drawn since the last forget_paths(), so that swaying grass can be kept off
# them: grass that grows out of a trodden path looks wrong.
_TRODDEN = []
_TRODDEN_MASK = [None, 0]


def forget_paths():
    _TRODDEN.clear()


def on_path(x, y):
    if not _TRODDEN:
        return False
    if _TRODDEN_MASK[1] != len(_TRODDEN):
        s = plane()
        for poly in _TRODDEN:
            pygame.draw.polygon(s, (255, 255, 255), poly)
        _TRODDEN_MASK[:] = [pygame.mask.from_surface(s), len(_TRODDEN)]
    x, y = int(x), int(y)
    return 0 <= x < W and 0 <= y < H and _TRODDEN_MASK[0].get_at((x, y))


def path(s, pts, widths, color, edge, pebbles=None, rng=None):
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
    _TRODDEN.append(poly)
    _TRODDEN.append([(x, y + 2) for x, y in poly])
    pygame.draw.polygon(s, edge, [(x, y + 2) for x, y in poly])
    pygame.draw.polygon(s, color, poly)
    # a worn, lighter strip down the middle and scattered pebbles
    centre = mix(color, (255, 255, 255), 0.08)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        steps = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2)
        for k in range(steps):
            f = k / max(1, steps)
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            w = widths[i] + (widths[i + 1] - widths[i]) * f
            if (k * 7 + i) % 3 == 0:
                s.set_at((int(x + math.sin(k * 2.3 + i) * w * 0.32), int(y + math.cos(k * 1.7) * 2)), edge)
            if (k * 5 + i) % 4 == 0:
                s.set_at((int(x + math.sin(k * 0.9) * w * 0.1), int(y)), centre)
            if rng is not None and rng.random() < 0.05 * w / 20:
                px, py = int(x + rng.uniform(-0.4, 0.4) * w), int(y + rng.uniform(-2, 2))
                c = pebbles or mix(color, (30, 20, 60), 0.3)
                s.set_at((px, py), c)
                s.set_at((px + 1, py), mix(c, (255, 255, 255), 0.25))


def sprite(rows, colors):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set_at((x, y), colors[ch])
    return s
