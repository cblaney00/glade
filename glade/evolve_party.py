"""Your own creatures evolving, after a battle in which they grew a level.

A creature evolves into its middle form at level 16 and its final form at 32 (levels.py,
like Pokémon). After the battle in which it gets there (the Tower's, or a wild one), this
board opens: "What? Pippalotl is evolving!", its picture glowing and flickering between its old and
new forms, faster and faster, then a flash and "Congratulations!". Like in Pokémon you may
press Stop while it flickers; it stays as it is and will try again the next time it grows a level.
"""

import random

import pygame

import art
from apex import ease
from battle import CLOTH, DIM, EDGE, TEXT, cloth, mix, moveset
from dex import MINT, PH, PW, WHITE, picture
from evolve import EVOLVES
from team import Collection

FLICKER, FLASH, AFTER = 5.0, 0.6, 0.0
SPARK = (200, 230, 255)


def silhouette(species):
    """The creature (drawn as in the Forest Dex, settled into its pose) as a plain white shape."""
    import dex
    from evolve import no_glow
    key = (1, 254, 3)
    thing = dex.specimen(species)
    pic = art.solid((PW, PH))
    with no_glow():
        for i in range(12):
            pic.fill(key)
            for part in ("draw", "shine"):
                fn = getattr(thing, part, None)
                if fn:
                    fn(pic, 1.0 + i * 0.1)
    body = pygame.mask.from_threshold(pic, key, (1, 1, 1, 255))
    body.invert()
    return body.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


class EvolveBoard:
    def __init__(self, font, ready, t):
        self.font = font
        self.queue = list(ready)  # team.Kept, in the order they evolve
        self.rect = pygame.Rect(230, 70, 500, 360)
        self.buttons = []
        self.closed = False
        self.begin(t)

    def begin(self, t):
        self.kept = self.queue.pop(0)
        self.old, self.new = self.kept.species, EVOLVES[self.kept.species]
        self.t = t
        self.state = "evolving"   # then "done" or "stopped"
        self.pics = [picture(self.old), picture(self.new)]
        self.shapes = [silhouette(self.old), silhouette(self.new)]

    # --- clicks ---
    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    def close(self):
        if self.state == "evolving":  # closing it mid-way is like pressing Stop
            self.state = "stopped"
        self.closed = True

    def stop(self):
        if self.state == "evolving":
            self.state = "stopped"

    def next(self):
        if self.queue:
            self.begin(self.now)
        else:
            self.closed = True

    def finish(self):
        """It has evolved: the new species, kept for good."""
        box = Collection()
        kept = box.find(self.kept.uid)
        for k in (kept, self.kept):
            if k is not None:
                k.species = self.new
                if not k.moves:
                    k.moves = moveset(self.new, random.Random())
        box.save()
        self.state = "done"

    # --- drawing ---
    def text(self, s, words, x, y, color=TEXT):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() // 2, y))

    def button(self, s, r, label, action, m, tint=None):
        hot = bool(m) and r.collidepoint(m)
        cloth(s, r, MINT if hot else tint or mix(CLOTH, EDGE, 0.2), hot=hot, alpha=215)
        img = self.font.render(label, False, WHITE if hot else TEXT)
        s.blit(img, img.get_rect(center=r.center))
        self.buttons.append((r, action))

    def draw(self, s, m, t):
        self.now = t
        self.buttons = []
        r = self.rect
        f = t - self.t
        cloth(s, r, CLOTH, alpha=round(248 * ease(f / 0.3)))
        if f < 0.3:
            return
        cx, cy = r.centerx, r.y + 160
        big = (PW * 4, PH * 4)
        if self.state == "evolving" and f >= FLICKER + FLASH:
            self.finish()
        if self.state == "evolving":
            self.text(s, f"What? {self.old} is evolving!", cx, r.y + 18, WHITE)
            k = ease(f / FLICKER)
            if f < 0.8:  # it glows, then turns to light
                pic = self.pics[0]
            else:
                period = 0.55 - 0.48 * k
                pic = self.shapes[1 if int((f - 0.8) / period) % 2 else 0]
            art.glow(s, cx, cy, int(70 + 40 * k), SPARK, round(60 + 100 * k) // 12 * 12)
            img = pygame.transform.scale(pic, big)
            s.blit(img, img.get_rect(center=(cx, cy)))
            if f >= FLICKER:  # the flash
                white = art.plane(r.size)
                white.fill((255, 255, 255, round(255 * (1 - abs(f - FLICKER - FLASH / 2) / (FLASH / 2)))))
                s.blit(white, r.topleft)
            self.button(s, pygame.Rect(cx - 50, r.bottom - 44, 100, 26), "Stop", self.stop, m)
            self.text(s, "Press Stop to keep it as it is.", cx, r.bottom - 66, DIM)
            return
        if self.state == "done":
            img = pygame.transform.scale(self.pics[1], big)
            s.blit(img, img.get_rect(center=(cx, cy)))
            self.text(s, "Congratulations!", cx, r.y + 18, WHITE)
            self.text(s, f"Your {self.old} evolved into {self.new}!", cx, r.y + 36, MINT)
        else:
            img = pygame.transform.scale(self.pics[0], big)
            s.blit(img, img.get_rect(center=(cx, cy)))
            self.text(s, f"Huh? {self.old} stopped evolving!", cx, r.y + 18, WHITE)
            self.text(s, "It will try again when it next grows a level.", cx, r.y + 36, DIM)
        self.button(s, pygame.Rect(cx - 50, r.bottom - 44, 100, 26), "Next" if self.queue else "OK", self.next, m)
