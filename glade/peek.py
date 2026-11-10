"""A look at a place from the desktop's aerial home (2026-11-10, his ask; aerial.py).

Left-click a place in the aerial view and a small live window of it fades in over the top screen:
the real place, animals moving, in a wooden frame with its name and a "Wander there" board that
opens the game there. Right-click an animal in it for its card. It is only for looking: clicking
anywhere outside it, opening an app, or another window taking the focus closes it, and the place is
let go again, so only home runs in the background (desktop.py).

The place is built on a side thread in the gaps between frames (loading.py), so the desktop never
stutters; until it is ready the frame shows a soft shimmer, then the picture fades in.
"""

import math
import threading

import pygame

import art
import loading
from art import H, W, mix

PIC = (480, 270)  # the place's top screen, at half size
EDGE, BAR = 6, 18  # the frame's wood, and the strip under the picture with the name and the board
FADE = 0.4  # seconds to fade in
WOOD, WOOD2, TEXT = (92, 58, 92), (150, 104, 140), (255, 246, 236)
GOLD = (255, 214, 120)


class Seen:
    """An animal as it looks on the canvas shown (through the zoom, or in a peek): for its card."""

    def __init__(self, animal, to_screen):
        self._a, self._to = animal, to_screen

    def pos(self):
        return self._to(self._a.pos())

    def __getattr__(self, name):
        return getattr(self._a, name)


class Peek:
    def __init__(self, glade, key, title, near, t):
        """`near`: where on the canvas shown it was clicked; the window goes over it, kept on screen."""
        self.glade, self.key, self.title = glade, key, title
        self.scene, self.shown_at, self.closed = None, None, False
        self.canvas, self.pic, self.tick = None, None, 0
        w, h = PIC[0] + 2 * EDGE, PIC[1] + 2 * EDGE + BAR
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (round(near[0]), round(near[1]))
        self.rect.clamp_ip(pygame.Rect(8, 8, W - 16, H - 16))
        self.picture = pygame.Rect(self.rect.x + EDGE, self.rect.y + EDGE, *PIC)
        self.board = pygame.Rect(0, 0, 0, BAR - 4)
        self.t0 = t
        self.thread = threading.Thread(target=self.build, daemon=True)
        self.thread.start()

    def build(self):
        from scenes import BUILDERS
        loading.gate.side = threading.get_ident()
        try:
            with self.glade.building:
                if self.closed:
                    return
                sc = BUILDERS[self.key]()
            if not self.closed:
                self.canvas = art.solid()
                self.scene = sc
        except loading.Stopped:
            pass
        finally:
            loading.gate.side = None

    def close(self):
        self.closed = True
        self.scene = self.canvas = self.pic = None

    # --- where things are -------------------------------------------------------------------
    def inside(self, m):
        return m is not None and self.rect.collidepoint(m)

    def to_place(self, m):
        """A point on the canvas shown -> the same point in the place."""
        return ((m[0] - self.picture.x) * W / PIC[0], (m[1] - self.picture.y) * H / PIC[1])

    def to_screen(self, p):
        return (self.picture.x + p[0] * PIC[0] / W, self.picture.y + p[1] * PIC[1] / H)

    def animal_at(self, m, t):
        """(animal, species) right-clicked in the picture, as it looks on screen, or None."""
        if self.scene is None or not self.picture.collidepoint(m):
            return None
        from battle import animal_under
        found = animal_under(self.scene, None, self.to_place(m), False, t)
        if found is None:
            return None
        return Seen(found[0], self.to_screen), found[1]

    # --- running ----------------------------------------------------------------------------
    def draw(self, s, font, m, t):
        if self.scene is not None and self.shown_at is None:
            self.shown_at = t
        k = 0.0 if self.shown_at is None else min(1.0, (t - self.shown_at) / FADE)
        opening = min(1.0, (t - self.t0) / 0.2)  # the frame itself comes up quickly
        a = int(255 * opening)
        frame = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        r = frame.get_rect()
        pygame.draw.rect(frame, (*WOOD, 245), r, border_radius=7)
        pygame.draw.rect(frame, (*WOOD2, 255), r, 2, border_radius=7)
        pygame.draw.line(frame, (*mix(WOOD2, (255, 255, 255), 0.4), 255), (8, 1), (r.w - 9, 1))
        inner = pygame.Rect(EDGE - 1, EDGE - 1, PIC[0] + 2, PIC[1] + 2)
        pygame.draw.rect(frame, (30, 20, 48, 255), inner)
        frame.set_alpha(a)
        s.blit(frame, self.rect)
        if self.scene is not None:
            self.tick += 1
            if self.pic is None or self.tick % 2 == 0:  # the place moves at half the frames: plenty for a look
                self.scene.update(1 / 15)
                self.scene.draw(self.canvas, t)
                self.pic = pygame.transform.scale(self.canvas, PIC)
            self.pic.set_alpha(int(255 * k * k * (3 - 2 * k)))
        if k < 1:  # still loading: a soft shimmer of night mist
            veil = pygame.Surface(PIC, pygame.SRCALPHA)
            for i in range(6):
                x = (t * 60 + i * 97) % (PIC[0] + 80) - 40
                pygame.draw.ellipse(veil, (120, 100, 190, 40), (x - 40, 40 + i * 34, 120, 40))
            veil.set_alpha(int(a * (1 - k)))
            s.blit(veil, self.picture)
            dots = "Looking" + "." * (1 + int(t * 3) % 3)
            img = font.render(dots, False, TEXT)
            img.set_alpha(int(a * (1 - k)))
            s.blit(img, img.get_rect(center=self.picture.center))
        if self.pic is not None:
            s.blit(self.pic, self.picture)
        # the strip underneath: the place's name, and the board that goes there in the game
        y = self.picture.bottom + 2
        name = font.render(self.title, False, TEXT)
        name.set_alpha(a)
        s.blit(name, (self.picture.x + 2, y + (BAR - 4 - name.get_height()) // 2))
        words = "Wander there"
        bw = font.size(words)[0] + 14
        self.board = pygame.Rect(self.picture.right - bw, y, bw, BAR - 4)
        hot = m is not None and self.board.collidepoint(m)
        from battle import cloth
        cloth(s, self.board, GOLD, hot=hot, alpha=min(a, 235))
        img = font.render(words, False, (255, 255, 255))
        img.set_alpha(a)
        s.blit(img, img.get_rect(center=self.board.center))
        if hot:
            glow = 0.5 + 0.5 * math.sin(t * 5)
            pygame.draw.rect(s, mix(GOLD, (255, 255, 255), glow), self.board.inflate(2, 2), 1, border_radius=3)
