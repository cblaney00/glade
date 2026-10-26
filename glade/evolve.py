"""Evolution — like Pokémon.

Five animals can evolve so far, into their middle stage (his test, 2026-10-26; the final
stages are not made yet): Critter → Glowtail, Squid → Nimbusquid, Lantern Moth → Beacon
Moth, Brawl Toad → Bruiser Toad, Sporeling → Sporestride. An evolved animal is the same
one, bigger, with more to it: each class draws its extras when `stage` is 2 (life.py,
beasts.py). Its battle stats are its new species' (battle.SPECIES).

From an animal's stats card, "Evolve" plays the evolution, about four seconds:
the screens dim and specks of light gather; the animal turns to a white shape that
flickers between its old and new forms, faster and faster; a white flash; and there it
is, evolved, with a banner saying so.
"""

import contextlib
import math
import random

import pygame

import art
import beasts
import life
from apex import OFFSET, ease
from art import glow, mix
from battle import cloth, draw_elsewhere, species_of

EVOLVES = {"Critter": "Glowtail", "Squid": "Nimbusquid", "Lantern Moth": "Beacon Moth",
           "Brawl Toad": "Bruiser Toad", "Sporeling": "Sporestride"}
EVOLVED_FROM = {v: k for k, v in EVOLVES.items()}
LENGTH = 4.0      # the evolution itself
BANNER = 2.6      # how long "… evolved into …!" stays up afterwards
KEY = (1, 254, 3)
SPARK = (200, 230, 255)


def set_stage(obj, stage):
    """Make an animal its first (1) or middle (2) stage. Reversible: the first-stage
    values are kept the first time."""
    first = obj.__dict__.setdefault("_first", dict(size=getattr(obj, "size", None), species=getattr(obj, "species", None),
                                                   name=species_of(obj)))
    obj.stage = stage
    if first["size"] is not None:
        obj.size = first["size"] * (1.3 if stage == 2 else 1.0)
    obj.species = EVOLVES[first["name"]] if stage == 2 else first["species"]
    if type(obj).__name__ == "Critter":
        if stage == 2:
            obj.SEG = 5.2  # a longer body and tail
        else:
            obj.__dict__.pop("SEG", None)
    if type(obj).__name__ == "Squid":
        long = obj.__dict__.setdefault("_long", [])
        if stage == 2 and not long:  # two long hunting tentacles
            for _ in range(2):
                arm = [[obj.x, obj.y] for _ in range(16)]
                long.append(arm)
                obj.arms.append(arm)
        elif stage == 1 and long:
            obj.arms = [a for a in obj.arms if not any(a is b for b in long)]
            long.clear()


@contextlib.contextmanager
def no_glow():
    """While drawing a silhouette: no soft glows, just the animal's own shape."""
    saved = life.glow, beasts.glow
    life.glow = beasts.glow = lambda *a, **k: None
    try:
        yield
    finally:
        life.glow, beasts.glow = saved


class Evolution:
    def __init__(self, animal, species, t):
        self.a, self.obj, self.t0, self.now = animal, animal.obj, t, t
        self.old, self.new = species, EVOLVES[species]
        self.obj.gone = True  # drawn here until it is done
        self.swapped = self.shown = False
        self.scratch = art.solid()
        self.veils = {}
        rng = random.Random()
        self.sparks = [(rng.uniform(0, math.tau), rng.uniform(30, 90), rng.uniform(0.6, 1.4)) for _ in range(26)]

    @property
    def done(self):
        return self.now - self.t0 > LENGTH + BANNER

    def update(self, t):
        self.now = t
        f = t - self.t0
        if f >= 3.2 and not self.swapped:  # under the flash: it has evolved
            set_stage(self.obj, 2)
            self.swapped = True
        if f >= 3.4 and not self.shown:
            self.obj.gone = False  # from here it is in the glade again, lit like everyone else
            self.shown = True

    def finish(self):
        """He walked away mid-way: it simply has evolved."""
        if not self.swapped:
            set_stage(self.obj, 2)
            self.swapped = True
        self.obj.gone = False
        self.now = self.t0 + LENGTH + BANNER + 1

    def where(self):
        x, y = self.a.pos()
        return (x - OFFSET[0], y - OFFSET[1]) if self.a.low else (x, y)

    def silhouette(self, s, t, stage):
        """The animal (as `stage`) as a plain white shape, where it is."""
        set_stage(self.obj, stage)
        x, y = self.where()
        box = pygame.Rect(round(x) - 70, round(y) - 70, 140, 140).clip(self.scratch.get_rect())
        if box.w > 0 and box.h > 0:
            self.scratch.set_clip(box)
            self.scratch.fill(KEY, box)
            with no_glow():
                for part in ("draw", "shine"):
                    fn = getattr(self.obj, part, None)
                    if fn:
                        fn(self.scratch, t)
            self.scratch.set_clip(None)
            shape = pygame.mask.from_threshold(self.scratch.subsurface(box), KEY, (1, 1, 1, 255))
            shape.invert()
            s.blit(shape.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), box.topleft)
        set_stage(self.obj, 2 if self.swapped else 1)

    def draw(self, s, low, t):
        self.now = t
        f = t - self.t0
        w, h = s.get_size()
        # the screens dim while it happens, and brighten again after
        dim = ease(f / 0.5) if f < LENGTH else 1 - ease((f - LENGTH) / 0.6)
        if dim > 0:
            veil = self.veils.get((w, h))
            if veil is None:
                veil = self.veils[(w, h)] = art.solid((w, h))
                veil.fill((8, 6, 22))
            veil.set_alpha(round(150 * dim))
            s.blit(veil, (0, 0))
        if low == self.a.low:
            x, y = self.where()
            if f < 0.6:  # it glows brighter and brighter
                draw_elsewhere(s, self.a, (x, y), t, self.scratch)
                glow(s, x, y, 30, SPARK, round(min(1.0, f / 0.6) * 140) // 12 * 12)
            elif f < 3.4:  # a white shape, flickering between old and new, faster and faster
                k = ease((f - 0.6) / 2.6)
                period = 0.5 - 0.44 * k
                stage = 2 if int((f - 0.6) / period) % 2 else 1
                glow(s, x, y, int(28 + 20 * k), SPARK, round(100 + 100 * k) // 12 * 12)
                self.silhouette(s, t, stage)
            # specks of light gather in, then burst out once it has evolved
            for a, r, sp in self.sparks:
                if f < 3.2:
                    d = r * (1 - ((f * sp) % 1.0))
                    c = mix(SPARK, (255, 255, 255), 0.5)
                else:
                    d = r * ease((f - 3.2) / 1.2) * 1.4
                    c = mix(SPARK, (255, 236, 160), 0.5)
                if 0 < d and (f < 3.2 or f < 4.6):
                    s.set_at((round(x + math.cos(a + f) * d), round(y + math.sin(a + f) * d * 0.8)), c)
            self.banner(s, f)
        # the white flash
        flash = ease((f - 3.0) / 0.25) if f < 3.4 else 1 - ease((f - 3.4) / 0.6)
        if flash > 0:
            white = self.veils.get(("white", w, h))
            if white is None:
                white = self.veils[("white", w, h)] = art.solid((w, h))
                white.fill((255, 255, 255))
            white.set_alpha(round(255 * flash))
            s.blit(white, (0, 0))

    def banner(self, s, f):
        """What is happening, in words, at the top of that screen."""
        if f < 3.2:
            words = f"What? {self.old} is evolving!"
            k = ease(f / 0.4)
        else:
            words = f"Congratulations! Your {self.old} evolved into {self.new}!"
            k = ease((f - 3.6) / 0.4) * (1 - ease((f - LENGTH - BANNER + 0.5) / 0.5))
        if k <= 0 or self.font is None:
            return
        img = self.font.render(words, False, (255, 255, 255))
        r = pygame.Rect(0, 0, img.get_width() + 24, img.get_height() + 12)
        r.midtop = (s.get_width() // 2, 16)
        cloth(s, r, (196, 140, 255), alpha=round(235 * k))
        img.set_alpha(round(255 * k))
        s.blit(img, img.get_rect(center=r.center))

    font = None  # set by the glade

