"""Predator vision — see where every animal is.

A golden "Predator vision" button sits in the lower screen's top-left corner. Click it and,
for a few seconds, the whole glade drains to black and white except the animals: they
keep their colours and are traced in a glowing golden outline, so even one hiding in the
grass or behind a branch stands out. It eases in and out (nothing in the glade snaps).

His ask (2026-10-29): the ones worth catching stand out too. An animal whose IVs add up to
`STRONG` or more (the top 5% of all rolls) is traced in shimmering pink-white instead of gold,
with a little four-pointed star twinkling over it. Then (same day, his ask) no star: a thicker,
pulsing electric-blue rim instead, a colour far from the gold so it is obvious.

Speed (2026-11-01, his ask: "everything lags when i click predator vision"): finding a body and
tracing its outline is the slow part, so each animal's is worked out only every `EVERY` frames
and moved along with it in between (`Vision.traced`), and the outline is one mask convolution
instead of dozens of separate draws (`ring`).
"""

import math

import pygame

import corner

import art
from apex import OFFSET, ease
from battle import TEXT, animals, cloth
from team import ivs_of

GOLD = (255, 206, 90)
KEY = (1, 254, 3)  # a colour nothing in the glade is drawn in
FAINT = 70  # a faint haze of light round an animal is not its body
IN, HOLD, OUT = 0.6, 4.0, 1.0
R = 44  # how far round an animal to look for its body at first
RMAX = 352  # and at most
STRONG = 131  # an IV total this high or more is the top 5% (of 186; worked out from the 32**6 rolls)
SHINE = (40, 230, 255)  # electric blue: nothing like the gold, so they jump out
EVERY = 4  # frames between tracing each animal afresh (it is moved along with it in between)
GREY_EVERY = 6  # frames between greying the world afresh (5 times a second; the two screens take turns)
_DISKS = {}


def disk(n):
    """A small diamond-ish brush `n` pixels out, for growing a body into its outline."""
    if n not in _DISKS:
        m = pygame.mask.Mask((2 * n + 1, 2 * n + 1))
        for dx in range(-n, n + 1):
            for dy in range(-n, n + 1):
                if abs(dx) + abs(dy) <= n + 1:
                    m.set_at((dx + n, dy + n))
        _DISKS[n] = m
    return _DISKS[n]


def strong(obj):
    """Is this animal's IV total in the top 5%?"""
    return sum(ivs_of(obj)) >= STRONG


def button_rect(view):
    return corner.rect("vision")


def draw_button(s, view, font, on):
    """The button: a golden board with a little eye."""
    r = button_rect(view)
    m = view.mouse()
    hot = on or (bool(m) and r.collidepoint(m))
    cloth(s, r, GOLD, hot=hot, alpha=230)
    ex, ey = r.x + 13, r.centery
    pygame.draw.ellipse(s, (255, 244, 200), (ex - 7, ey - 4, 14, 8))
    pygame.draw.circle(s, (60, 30, 20), (ex, ey), 3)
    s.set_at((ex - 1, ey - 1), (255, 255, 255))
    img = font.render("Predator vision", False, (255, 255, 255) if hot else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))


class Vision:
    def __init__(self, t):
        self.t0 = t
        self.scratch = art.solid()
        self.frame = {False: 0, True: 0}  # frames drawn, per screen
        self.traces = {}  # id(animal) -> (frame, x, y, box, body, outline, centre, strong)

    def strength(self, t):
        a = t - self.t0
        if a < IN:
            return ease(a / IN)
        if a < IN + HOLD:
            return 1.0
        return 1.0 - ease((a - IN - HOLD) / OUT)

    def body(self, a, box, t):
        """A mask of what animal `a` covers inside `box`."""
        self.scratch.set_clip(box)
        self.scratch.fill(KEY, box)
        o = a.obj
        if type(a).__name__ == "Perched":
            o.shine(self.scratch, t, 12)
        else:
            for part in ("draw", "shine"):
                fn = getattr(o, part, None)
                if fn:
                    fn(self.scratch, t)
        self.scratch.set_clip(None)
        body = pygame.mask.from_threshold(self.scratch.subsurface(box), KEY, (FAINT, FAINT, FAINT, 255))
        body.invert()
        return body

    @staticmethod
    def ring(body, n):
        """The `n`-pixel band just outside the body (one convolution with a small brush)."""
        w, h = body.get_size()
        grown = body.convolve(disk(n))  # (w + 2n) x (h + 2n), shifted n down and right
        ring = pygame.mask.Mask((w, h))
        ring.draw(grown, (-n, -n))
        ring.erase(body, (0, 0))
        return ring

    @staticmethod
    def cut(body, box, area):
        """Does the body reach an edge of `box` that is not also the screen's edge?"""
        w, h = body.get_size()
        for b in body.get_bounding_rects():
            if (b.left == 0 and box.left > area.left) or (b.top == 0 and box.top > area.top) \
                    or (b.right == w and box.right < area.right) or (b.bottom == h and box.bottom < area.bottom):
                return True
        return False

    @property
    def length(self):
        return IN + HOLD + OUT

    def done(self, t):
        return t - self.t0 >= self.length

    def draw(self, s, w, h, scene, lower, low, t):
        """Over one screen's picture `s` (its shown part is w x h): the world in grey, the
        animals in colour with a golden outline."""
        k = self.strength(t)
        if k <= 0:
            return
        self.frame[low] += 1
        area = pygame.Rect(0, 0, w, h)
        orig = s.subsurface(area).copy()
        gray = self.greyed(orig, w, h, scene.key, low)
        if k < 1:  # fully grey: an opaque copy, much quicker than a see-through one
            gray.set_alpha(round(255 * k))
        s.blit(gray, (0, 0))
        seen = set()
        for a, _ in animals(scene, lower):
            if a.low != low or getattr(a.obj, "gone", False):
                continue
            x, y = a.pos()
            if low:
                x, y = x - OFFSET[0], y - OFFSET[1]
            key = (id(a.obj), low)
            seen.add(key)
            got = self.traces.get(key)
            if got is None or self.frame[low] - got[0] >= EVERY:
                got = self.trace(a, x, y, area, low, t)
                self.traces[key] = got
            frame, x0, y0, box, body, outline, centre, is_strong = got
            if body is None:
                continue
            box = box.move(round(x - x0), round(y - y0))  # it has moved on a little since
            if not box.colliderect(area):
                continue
            # its true colours back, from the picture as it is now
            piece = art.plane(box.size)
            piece.blit(orig, (0, 0), box)
            s.blit(body.to_surface(setsurface=piece, unsetcolor=(0, 0, 0, 0)), box.topleft)
            cx, cy = centre[0] + box.x, centre[1] + box.y
            if is_strong:  # worth catching: a thicker electric-blue rim that pulses, and a stronger glow
                p = 0.5 + 0.5 * math.sin(t * 6)
                outline.set_alpha(round(255 * k * (0.7 + 0.3 * p)))
                s.blit(outline, box.topleft)
                art.glow(s, cx, cy, 36, SHINE, round(90 * k) // 10 * 10)
            else:  # a golden outline, two pixels wide, round all of it
                outline.set_alpha(round(255 * k))
                s.blit(outline, box.topleft)
                art.glow(s, cx, cy, 22, GOLD, round(40 * k) // 10 * 10)
        for key in [k_ for k_ in self.traces if k_[1] == low and k_ not in seen]:
            del self.traces[key]  # gone, or out of sight

    def greyed(self, orig, w, h, place, low):
        """The world in grey: made afresh only every `GREY_EVERY` frames, and at once when the place
        changes (greying the whole picture was the slowest part). Grey at the picture's own pixel
        size (it is drawn at 2x), a touch darker and cooler."""
        got = getattr(self, "grey", {}).get(low)
        if got is not None and got[1] == place and (self.frame[low] + 3 * low) % GREY_EVERY:
            return got[2]
        small = pygame.transform.scale(orig, (w // 2, h // 2))
        small = pygame.transform.grayscale(small)
        small.fill((150, 150, 170), special_flags=pygame.BLEND_RGB_MULT)
        gray = pygame.transform.scale(small, (w, h))
        if not hasattr(self, "grey"):
            self.grey = {}
        self.grey[low] = (self.frame[low], place, gray)
        return gray

    def trace(self, a, x, y, area, low, t):
        """Find animal `a`'s body round (x, y) and make its outline: (frame, x, y, box, body,
        outline surface, centre in the box, strong)."""
        # draw it alone onto a key colour and see what it covered. Big ones (evolved, close
        # up) can be larger than the first guess, so while the body runs off the edge of the
        # box (and not off the screen), look again in a bigger one
        r = R
        while True:
            box = pygame.Rect(round(x) - r, round(y) - r, 2 * r, 2 * r).clip(area)
            if box.w <= 0 or box.h <= 0:
                return (self.frame[low], x, y, box, None, None, None, False)
            body = self.body(a, box, t)
            if r >= RMAX or not self.cut(body, box, area):
                break
            r *= 2
        if body.count() == 0:
            return (self.frame[low], x, y, box, None, None, None, False)
        rects = body.get_bounding_rects()
        u = rects[0].unionall(rects)
        is_strong = strong(a.obj)
        if is_strong:
            outline = self.ring(body, 3).to_surface(setcolor=(*SHINE, 255), unsetcolor=(0, 0, 0, 0))
            light = self.ring(body, 1).to_surface(setcolor=(220, 250, 255, 255), unsetcolor=(0, 0, 0, 0))
            outline.blit(light, (0, 0))  # a bright inner edge, for the shimmer
        else:
            outline = self.ring(body, 2).to_surface(setcolor=(*GOLD, 255), unsetcolor=(0, 0, 0, 0))
        return (self.frame[low], x, y, box, body, outline, u.center, is_strong)
