"""Predator vision — see where every animal is.

A golden "Predator vision" button sits in the lower screen's top-left corner. Click it and,
for a few seconds, the whole glade drains to black and white except the animals: they
keep their colours and are traced in a glowing golden outline, so even one hiding in the
grass or behind a branch stands out. It eases in and out (nothing in the glade snaps).

His ask (2026-10-29): the ones worth catching stand out too. An animal whose IVs add up to
`STRONG` or more (the top 5% of all rolls) is traced in shimmering pink-white instead of gold,
with a little four-pointed star twinkling over it. Then (same day, his ask) no star: a thicker,
pulsing electric-blue rim instead, a colour far from the gold so it is obvious.
"""

import math

import pygame

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


def strong(obj):
    """Is this animal's IV total in the top 5%?"""
    return sum(ivs_of(obj)) >= STRONG


def button_rect(view):
    return pygame.Rect(8, 8, 150, 22)


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


DEX = (150, 230, 190)


def dex_rect(view):
    """The Forest Dex button, just under Predator vision."""
    return pygame.Rect(8, 34, 150, 22)


def draw_dex_button(s, view, font):
    """A mint board with a little open book."""
    r = dex_rect(view)
    m = view.mouse()
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, DEX, hot=hot, alpha=230)
    bx, by = r.x + 6, r.centery - 5
    pygame.draw.polygon(s, (240, 236, 220), [(bx, by), (bx + 7, by + 1), (bx + 7, by + 10), (bx, by + 9)])
    pygame.draw.polygon(s, (220, 214, 196), [(bx + 7, by + 1), (bx + 14, by), (bx + 14, by + 9), (bx + 7, by + 10)])
    pygame.draw.line(s, (120, 90, 110), (bx + 7, by + 1), (bx + 7, by + 10))
    img = font.render("Forest Dex", False, (255, 255, 255) if hot else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))


class Vision:
    def __init__(self, t):
        self.t0 = t
        self.scratch = art.solid()

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
        """The `n`-pixel band just outside the body."""
        ring = pygame.mask.Mask(body.get_size())
        for dx in range(-n, n + 1):
            for dy in range(-n, n + 1):
                if abs(dx) + abs(dy) <= n + 1:
                    ring.draw(body, (dx, dy))
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
        area = pygame.Rect(0, 0, w, h)
        orig = s.subsurface(area).copy()
        # grey at the picture's own pixel size (it is drawn at 2x), which is four times quicker
        small = pygame.transform.scale(orig, (w // 2, h // 2))
        small = pygame.transform.grayscale(small)
        small.fill((150, 150, 170), special_flags=pygame.BLEND_RGB_MULT)  # a touch darker and cooler
        gray = pygame.transform.scale(small, (w, h))
        if k < 1:  # fully grey: an opaque copy, much quicker than a see-through one
            gray.set_alpha(round(255 * k))
        s.blit(gray, (0, 0))
        for a, _ in animals(scene, lower):
            if a.low != low or getattr(a.obj, "gone", False):
                continue
            x, y = a.pos()
            if low:
                x, y = x - OFFSET[0], y - OFFSET[1]
            # the animal's body: draw it alone onto a key colour and see what it covered. Big
            # ones (evolved, close up) can be larger than the first guess, so while the body
            # runs off the edge of the box (and not off the screen), look again in a bigger one
            o = a.obj
            r = R
            while True:
                box = pygame.Rect(round(x) - r, round(y) - r, 2 * r, 2 * r).clip(area)
                if box.w <= 0 or box.h <= 0:
                    body = None
                    break
                body = self.body(a, box, t)
                if r >= RMAX or not self.cut(body, box, area):
                    break
                r *= 2
            if body is None or body.count() == 0:
                continue
            # its true colours back, from the picture as it was
            piece = art.plane(box.size)
            piece.blit(orig, (0, 0), box)
            s.blit(body.to_surface(setsurface=piece, unsetcolor=(0, 0, 0, 0)), box.topleft)
            rects = body.get_bounding_rects()
            cx, cy = (box.x + rects[0].unionall(rects).centerx, box.y + rects[0].unionall(rects).centery) if rects else (x, y)
            if strong(o):
                # worth catching: a thicker electric-blue rim that pulses, and a stronger glow
                ring = self.ring(body, 3)
                p = 0.5 + 0.5 * math.sin(t * 6)
                tint = tuple(round(c + (w - c) * p * 0.6) for c, w in zip(SHINE, (255, 255, 255)))
                outline = ring.to_surface(setcolor=(*tint, round(255 * k)), unsetcolor=(0, 0, 0, 0))
                s.blit(outline, box.topleft)
                art.glow(s, cx, cy, 36, SHINE, round(90 * k) // 10 * 10)
            else:
                # a golden outline, two pixels wide, round all of it
                outline = self.ring(body, 2).to_surface(setcolor=(*GOLD, round(255 * k)), unsetcolor=(0, 0, 0, 0))
                s.blit(outline, box.topleft)
                art.glow(s, cx, cy, 22, GOLD, round(40 * k) // 10 * 10)
