"""The Battle Tower — like Pokémon Emerald's, but Gen 3 OU: six against six, singles.

Walk down past the Mossy Rocks to the Tower and click its door. The very first time, you
choose your starter there (starter.py), and catching wild animals only opens up once you
have done a run (`Collection.tried`). Trainers bring as many creatures as you do (up to
six). Your party goes in as it is (arrange it in your boxes, team.py / storage.py, at the shrine beside the door), and
takes on the tower's trainers one after another. Each trainer's team is a match for yours (`trainer`). Your team is healed before
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


def trainer(streak, rng, mine=TEAM):
    """The next challenger: a name, and one creature for each of yours (his rule: the tower is
    won by strategy and luck, not by grinding). Each of theirs is as strong as the one of yours
    it stands for: a different kind with a base-stat total within 20 of it (a first stage
    against a first stage, a final one against a final one), with IVs about as good as its
    own (each within 6, shuffled about). It is matched to whatever party you bring, so it stays
    fair as your party changes, and the streak does not make them stronger."""
    from team import roll_ivs
    if isinstance(mine, int):
        mine = [None] * mine
    totals = [sum(SPECIES[k.species]["base"]) if k else 310 for k in mine]
    taken = {k.species for k in mine if k}
    team = []
    for k, total in zip(mine[:TEAM], totals):
        near = [sp for sp, d in SPECIES.items() if abs(sum(d["base"]) - total) <= 20 and sp not in taken]
        if not near:
            near = sorted((sp for sp in SPECIES if sp not in taken), key=lambda sp: abs(sum(SPECIES[sp]["base"]) - total))[:3]
        species = rng.choice(sorted(near))
        taken.add(species)
        if k is None:
            ivs = roll_ivs(rng)
        else:
            ivs = [max(0, min(31, v + rng.randint(-6, 6))) for v in k.ivs]
            rng.shuffle(ivs)
        team.append((species, tuple(ivs), None))
    return rng.choice(TRAINERS), team


class Run:
    """One go at the tower: your team, the streak so far, and what happens between battles."""

    def __init__(self, team, glade):
        self.team, self.glade = team, glade
        self.streak = 0
        self.rng = random.Random()
        self.recorded = False

    def battle(self, t):
        name, foes = trainer(self.streak, self.rng, self.team)
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

    WINS_TO_EVOLVE = (3, 9)  # fought in 3 won battles: its middle form; 6 more: its final form

    def count_wins(self, battle):
        """Each of yours that went out in a won battle has one more Tower win; any that have
        enough may evolve (you can stop it: evolve_party.py)."""
        from evolve import EVOLVES, stage_of
        box = Collection()
        ready = []
        for i in sorted(battle.fought):
            if i >= len(self.team):
                continue
            mine = self.team[i]
            kept = box.find(mine.uid) or mine
            kept.wins += 1
            mine.wins = kept.wins
            nxt = EVOLVES.get(kept.species)
            _, stage = stage_of(kept.species)
            if nxt and kept.wins >= self.WINS_TO_EVOLVE[min(stage, 2) - 1]:
                ready.append(mine)
        box.save()
        if ready and self.glade.board is None:
            from evolve_party import EvolveBoard
            self.glade.board = EvolveBoard(self.glade.signs.font, ready, self.glade.now())

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
                self.count_wins(arena.battle)

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
