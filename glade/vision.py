"""Predator vision — see where every animal is.

A golden "Predator vision" button sits in the lower screen's top-left corner. Click it and,
for a few seconds, the whole glade drains to black and white except the animals: they
keep their colours and are traced in a glowing golden outline, so even one hiding in the
grass or behind a branch stands out. It eases in and out (nothing in the glade snaps).
"""

import pygame

import art
from apex import OFFSET, ease
from battle import TEXT, animals, cloth

GOLD = (255, 206, 90)
KEY = (1, 254, 3)  # a colour nothing in the glade is drawn in
IN, HOLD, OUT = 0.6, 4.0, 1.0
R = 44  # how far round an animal to look for its body


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
            box = pygame.Rect(round(x) - R, round(y) - R, 2 * R, 2 * R).clip(area)
            if box.w <= 0 or box.h <= 0:
                continue
            # the animal's body: draw it alone onto a key colour and see what it covered
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
            body = pygame.mask.from_threshold(self.scratch.subsurface(box), KEY, (1, 1, 1, 255))
            body.invert()
            if body.count() == 0:
                continue
            # its true colours back, from the picture as it was
            piece = art.plane(box.size)
            piece.blit(orig, (0, 0), box)
            s.blit(body.to_surface(setsurface=piece, unsetcolor=(0, 0, 0, 0)), box.topleft)
            # and a golden outline, two pixels wide, round all of it
            ring = pygame.mask.Mask(body.get_size())
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    if abs(dx) + abs(dy) <= 3:
                        ring.draw(body, (dx, dy))
            ring.erase(body, (0, 0))
            outline = ring.to_surface(setcolor=(*GOLD, round(255 * k)), unsetcolor=(0, 0, 0, 0))
            s.blit(outline, box.topleft)
            art.glow(s, x, y, 22, GOLD, round(40 * k) // 10 * 10)
