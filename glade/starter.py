"""Choosing your starter.

Your party starts empty. The first time you click "Battle it!" on a wild animal's stats
card, this board opens first: three creatures, Grass, Fire and Water, each alive in its
picture. Click one, say yes, and it joins your party (its own random IVs and moves); then
the battle you asked for begins. Their final forms are already decided (battle.SPECIES).
"""

import random

import pygame

import art
from apex import ease
from battle import CLOTH, DIM, EDGE, SPECIES, TEXT, TYPE_COLOR, cloth, mix, moveset
from dex import MINT, PH, PW, WHITE, paint, specimen
from team import Collection, Kept, roll_ivs

STARTERS = (
    ("Mossfawn", "A shy fawn of the deep glade, a lichen sprout between its ears.",
     "One day: Elderhart, Grass/Ghost - an ancient spirit stag."),
    ("Kindlet", "A tiny pangolin with embers glowing between its scales.",
     "One day: Pyreclad, Fire/Steel - a knight in molten armour."),
    ("Pippalotl", "A pastel axolotl whose feathery gills glow in the dark.",
     "One day: Leviolotl, Water/Dragon - a great river dragon."),
)


class StarterBoard:
    def __init__(self, font, t, then=None):
        """`then(t)`: what to do once one is chosen (the battle that was asked for)."""
        self.font, self.t, self.then = font, t, then
        self.rect = pygame.Rect(110, 40, 740, 456)
        self.things = [specimen(name) for name, _, _ in STARTERS]
        self.pics = [art.solid((PW, PH)) for _ in STARTERS]
        self.asking = None  # the one he clicked: "Choose it?"
        self.buttons = []
        self.closed = False
        self.chosen = None

    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    def close(self):
        self.closed = True

    def ask(self, i):
        def f():
            self.asking = i
        return f

    def choose(self):
        name = STARTERS[self.asking][0]
        box = Collection()
        box.add(Kept(name, roll_ivs(), moveset(name, random.Random())))
        box.save()
        self.chosen = name
        self.closed = True

    def text(self, s, words, x, y, color=TEXT, center=False):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() // 2 if center else x, y))

    def button(self, s, r, label, action, m, tint=None):
        hot = bool(m) and r.collidepoint(m)
        cloth(s, r, MINT if hot else tint or mix(CLOTH, EDGE, 0.2), hot=hot, alpha=215)
        img = self.font.render(label, False, WHITE if hot else TEXT)
        s.blit(img, img.get_rect(center=r.center))
        self.buttons.append((r, action))

    def draw(self, s, m, t):
        self.buttons = []
        r = self.rect
        k = ease((t - self.t) / 0.3)
        cloth(s, r, CLOTH, alpha=round(248 * k))
        if k < 1:
            return
        self.text(s, "CHOOSE YOUR STARTER", r.centerx, r.y + 12, WHITE, center=True)
        self.text(s, "Your party is empty. Pick the creature who will travel with you.", r.centerx, r.y + 30, DIM,
                  center=True)
        for i, (name, about, later) in enumerate(STARTERS):
            sp = SPECIES[name]
            tint = TYPE_COLOR[sp["types"][0]]
            cr = pygame.Rect(r.x + 16 + i * 240, r.y + 54, 228, 334)
            on = self.asking == i
            hot = bool(m) and cr.collidepoint(m)
            cloth(s, cr, tint if on or hot else mix(tint, EDGE, 0.45), hot=on or hot, alpha=200)
            paint(self.pics[i], self.things[i], t)
            big = pygame.transform.scale(self.pics[i], (PW * 3, PH * 3))
            s.blit(big, (cr.centerx - PW * 3 // 2, cr.y + 10))
            self.text(s, name, cr.centerx, cr.y + 176, WHITE, center=True)
            kind = sp["types"][0].upper()
            img = self.font.render(kind, False, EDGE)
            br = pygame.Rect(0, 0, img.get_width() + 8, img.get_height() + 2)
            br.center = (cr.centerx, cr.y + 200)
            pygame.draw.rect(s, tint, br, border_radius=3)
            s.blit(img, img.get_rect(center=br.center))
            for j, line in enumerate(wrap(self.font, about, cr.w - 16) + [""] + wrap(self.font, later, cr.w - 16)):
                self.text(s, line, cr.centerx, cr.y + 216 + j * 13, TEXT if j < 3 else DIM, center=True)
            self.buttons.append((cr, self.ask(i)))
        if self.asking is not None:
            name = STARTERS[self.asking][0]
            self.text(s, f"Choose {name}?", r.centerx - 120, r.bottom - 50, WHITE)
            self.button(s, pygame.Rect(r.centerx + 20, r.bottom - 54, 90, 22), "Yes!", self.choose, m, MINT)
            self.button(s, pygame.Rect(r.centerx + 118, r.bottom - 54, 70, 22), "Not yet", self.ask(None), m)
        else:
            self.text(s, "Click one to choose it.", r.centerx, r.bottom - 50, DIM, center=True)


def wrap(font, text, w):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.size(trial)[0] > w and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + ([line] if line else [])
