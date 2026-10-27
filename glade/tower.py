"""The Battle Tower — like Pokémon Emerald's, but Gen 3 OU: six against six, singles.

Walk down past the Mossy Rocks to the Tower and click its door. The very first time, you
choose your starter there (starter.py), and catching wild animals only opens up once you
have done a run (`Collection.tried`). Trainers bring as many creatures as you do (up to
six). Your party goes in as it is (arrange it in your boxes, team.py / storage.py, at the shrine beside the door), and
takes on the tower's trainers one after another. Your team is healed before
every battle. Each win adds to your streak, and the trainers' creatures grow stronger the
further you get (better IVs); a loss ends the run. Your best streak is kept.
"""

import random

import pygame

from apex import ease
from battle import CLOTH, DIM, EDGE, SPECIES, TEXT, Arena, cloth, mix
from dex import MINT, WHITE, picture
from team import TEAM, Collection

TRAINERS = ["Moss Warden Ivy", "Lantern Keeper Bram", "Tidepool Nell", "Starwatcher Orrin", "Frost Herder Kip",
            "Ember Sage Ottilie", "Mushroom Scout Pell", "Owl Whisperer Wren", "Cave Dweller Moro", "Petal Dancer Suki",
            "Glowworm Hermit Tam", "Mist Walker Ysolde", "Thunder Chaser Rook", "Slug Racer Fen", "Aurora Seer Lumi"]


def trainer(streak, rng, size=TEAM):
    """The next challenger: a name, and as many creatures as you bring (six once your party
    is full), all different. The first few have middling IVs; from about the tenth on they
    are near perfect."""
    floor = min(28, 6 + streak * 3)
    team = []
    for species in rng.sample(sorted(SPECIES), max(1, min(TEAM, size))):
        team.append((species, tuple(rng.randint(floor, 31) for _ in range(6)), None))
    return rng.choice(TRAINERS), team


class Run:
    """One go at the tower: your team, the streak so far, and what happens between battles."""

    def __init__(self, team, glade):
        self.team, self.glade = team, glade
        self.streak = 0
        self.rng = random.Random()
        self.recorded = False

    def battle(self, t):
        name, foes = trainer(self.streak, self.rng, len(self.team))
        intro = f"{name} wants to battle! (Battle {self.streak + 1})"
        return foes, intro

    def open(self, t):
        g = self.glade
        foes, intro = self.battle(t)
        low = g.lower() if g.bottom else None
        arena = Arena(g.here, low, g.signs.font, t, mode="tower", mine=self.team, foes=foes, intro=intro,
                      after=self.after)
        arena.mouse = g.top.mouse
        return arena

    def record(self):
        box = Collection()
        if self.streak > box.best:
            box.best = self.streak
            box.save()

    def after(self, arena, t):
        """The buttons once a battle is over. The first one ever done opens up catching."""
        if not getattr(self, "tried", False):
            self.tried = True
            box = Collection()
            if not box.tried:
                box.tried = True
                box.save()
        if arena.battle.winner == 0:
            if not getattr(arena, "counted", False):
                arena.counted = True
                self.streak += 1
                self.record()

            def next_one(t):
                arena.counted = False
                foes, intro = self.battle(t)
                arena.restart(foes, intro, t)
            return [(f"Next challenger ({self.streak} won)", next_one), ("Rest", arena.close)]
        if not self.recorded:
            self.recorded = True
            self.record()
        return [(f"Close (streak: {self.streak})", arena.close)]


class TowerBoard:
    """At the tower door: your party (arrange it in your boxes), your best streak, and Begin."""

    def __init__(self, font, t):
        self.font, self.t = font, t
        self.rect = pygame.Rect(180, 60, 600, 380)
        box = Collection()
        self.party = box.members()
        self.best = box.best
        self.buttons = []
        self.closed = False
        self.begin = False
        self.boxes = False

    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    def team(self):
        return self.party

    def go(self):
        if self.party:
            self.begin, self.closed = True, True

    def open_boxes(self):
        self.boxes, self.closed = True, True

    def close(self):
        self.closed = True

    def text(self, s, words, x, y, color=TEXT, center=False):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() // 2 if center else x, y))

    def button(self, s, r, label, action, m, enabled=True):
        hot = enabled and bool(m) and r.collidepoint(m)
        cloth(s, r, MINT if hot else mix(CLOTH, EDGE, 0.2 if enabled else 0.55), hot=hot, alpha=215)
        img = self.font.render(label, False, WHITE if hot else TEXT if enabled else DIM)
        s.blit(img, img.get_rect(center=r.center))
        if enabled:
            self.buttons.append((r, action))

    def draw(self, s, m, t):
        self.buttons = []
        r = self.rect
        k = ease((t - self.t) / 0.2)
        cloth(s, r, CLOTH, alpha=round(248 * k))
        if k < 1:
            return
        self.text(s, "THE BATTLE TOWER", r.centerx, r.y + 12, WHITE, center=True)
        self.text(s, "Your party against trainer after trainer, six against six (Gen 3 OU).", r.centerx, r.y + 32,
                  DIM, center=True)
        self.text(s, "Healed before every battle. Win to keep your streak going.", r.centerx, r.y + 46, DIM,
                  center=True)
        for n in range(TEAM):
            cr = pygame.Rect(r.x + 20 + (n % 3) * 190, r.y + 70 + (n // 3) * 110, 180, 100)
            kept = self.party[n] if n < len(self.party) else None
            cloth(s, cr, mix(MINT, EDGE, 0.4) if kept else mix(CLOTH, EDGE, 0.55), alpha=180)
            self.text(s, str(n + 1), cr.x + 6, cr.y + 4, DIM)
            if kept:
                s.blit(picture(kept.species), (cr.centerx - 36, cr.y + 10))
                self.text(s, kept.species, cr.centerx, cr.y + 66, WHITE, center=True)
                self.text(s, f"IVs {sum(kept.ivs)}/186", cr.centerx, cr.y + 80, DIM, center=True)
        self.text(s, f"Best streak: {self.best}", r.x + 20, r.bottom - 32, TEXT)
        if not self.party:
            self.text(s, "Your party is empty: catch some creatures first!", r.centerx, r.bottom - 60, DIM, center=True)
        self.button(s, pygame.Rect(r.right - 330, r.bottom - 38, 120, 24), "Your boxes", self.open_boxes, m)
        self.button(s, pygame.Rect(r.right - 200, r.bottom - 38, 180, 24), "Begin the challenge!", self.go, m,
                    enabled=bool(self.party))
