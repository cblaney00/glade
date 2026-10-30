"""The Elite 4 and the champion (2026-10-30, his design), in the Moonlit Hall (hall.py).

The hall's great door opens once every gym badge is won (gyms.GYMS). Then you take on four
type specialists one after another, and then the champion. His picks: there are a few fixed
**line-ups** (`LINEUPS`), each four members with their own types in their own order, and one
line-up is picked at random for each challenge; the champion is picked separately
(`CHAMPIONS`), and shown only when you reach them.

Each member's creatures are fixed (seeded by their name): six of their type, middle and final
stages only, the strongest last as their ace (two levels up, good IVs). Levels carry on from the
last gym (Lv 55): the four are Lv 57-60, the champion Lv 62, each ace two more. Your team is
healed before every battle, like the Tower (there are no items to heal with). A loss ends the
challenge; beating the champion counts in `Collection.champion`.
"""

import random

import pygame

import evolve
from apex import ease
from battle import CLOTH, DIM, EDGE, LEGENDARY, SPECIES, TEXT, TYPE_COLOR, cloth, mix
from dex import MINT, WHITE
from gyms import GYMS, grown, total
from team import Collection

# name of the line-up: four members (name, their types, colour) in the order you meet them
LINEUPS = {
    "The Night Council": [("Umbrine", ("Ghost",), (170, 130, 255)), ("Corvane", ("Dark",), (120, 90, 150)),
                          ("Mirelle", ("Psychic",), (255, 150, 210)), ("Drakhon", ("Dragon",), (150, 130, 255))],
    "The Tide and Storm": [("Thalassa", ("Water",), (110, 200, 255)), ("Volta", ("Electric",), (250, 236, 100)),
                           ("Ferris", ("Steel",), (205, 215, 230)), ("Skye", ("Flying",), (190, 220, 255))],
    "The Ember Court": [("Ignatia", ("Fire",), (255, 140, 90)), ("Terrak", ("Ground",), (235, 205, 150)),
                        ("Basalt", ("Rock",), (205, 185, 150)), ("Brawna", ("Fighting",), (245, 170, 120))],
    "The Wild Ring": [("Verdane", ("Grass",), (150, 225, 110)), ("Toxica", ("Poison",), (185, 115, 220)),
                      ("Rimewyn", ("Ice",), (175, 215, 255)), ("Chitra", ("Bug",), (180, 225, 90))],
}
CHAMPIONS = [("Champion Solenne", (255, 236, 170)), ("Champion Orrick", (200, 230, 255)),
             ("Champion Vael", (230, 200, 255))]
BASE_LEVELS = [57, 58, 59, 60]
BASE_CHAMP = 62
GROWTH = 3   # levels they all gain each time you become champion (his rule: trainers grow stronger)
CAP = 80


def boost():
    return min(CAP - BASE_CHAMP - 2, GROWTH * Collection().champion)


def levels():
    return [lv + boost() for lv in BASE_LEVELS], BASE_CHAMP + boost()


LEVELS, CHAMP_LEVEL = BASE_LEVELS, BASE_CHAMP  # before any championship (the book reads levels())
TEAM_SIZE = 6


def stage(sp):
    return evolve.stage_of(sp)[1]


def member_team(name, types, level):
    """A member's own six, the same every time: their type, middle and final stages, ace last."""
    rng = random.Random(name)
    firsts = sorted({evolve.species_at(sp, 1) or sp for sp in SPECIES
                     if sp not in LEGENDARY and set(types) & set(SPECIES[sp]["types"])})
    pool = sorted({grown(f, level) for f in firsts if f in SPECIES})
    pool = [sp for sp in pool if stage(sp) >= 2 and set(types) & set(SPECIES[sp]["types"])]
    rng.shuffle(pool)
    picks = sorted(pool[:TEAM_SIZE + 2], key=total)[-TEAM_SIZE:]  # a little choosy: the stronger of a few more
    rng.shuffle(picks)
    best = max(picks, key=total)
    picks = [sp for sp in picks if sp != best] + [best]
    team = []
    for sp in picks:
        ivs = tuple(rng.randint(16, 31) for _ in range(6))
        team.append((sp, ivs, None, None, level))
    sp, ivs, *_ = team[-1]
    team[-1] = (sp, tuple(max(v, 24) for v in ivs), None, None, level + 2)
    return team


def champion_team(name):
    """The champion's six: strong final stages of six different types, the strongest last."""
    rng = random.Random(name)
    finals = sorted(sp for sp in SPECIES if sp not in LEGENDARY and stage(sp) == 3 and total(sp) >= 500)
    rng.shuffle(finals)
    picks, seen = [], set()
    for sp in finals:
        kind = SPECIES[sp]["types"][0]
        if kind not in seen:
            seen.add(kind)
            picks.append(sp)
        if len(picks) == TEAM_SIZE:
            break
    best = max(picks, key=total)
    picks = [sp for sp in picks if sp != best] + [best]
    champ = levels()[1]
    team = [(sp, tuple(rng.randint(20, 31) for _ in range(6)), None, None, champ) for sp in picks]
    sp, ivs, *_ = team[-1]
    team[-1] = (sp, tuple(max(v, 26) for v in ivs), None, None, champ + 2)
    return team


def opened():
    """The door opens once every gym's badge is won."""
    return set(GYMS) <= set(Collection().badges)


# --- the great door -------------------------------------------------------------------------------

def place(sc):
    from hall import DOOR
    from scenes import Spot
    x, y = DOOR
    sc.spots.append(Spot("elite", (x - 44, y - 116, 88, 116), "The Elite 4", "hall", (x, y - 50), sign=(x, y - 132)))


class EliteBoard:
    """At the great door: shut until every badge is won; then tonight's line-up, and Battle."""

    def __init__(self, font, t):
        self.font, self.t = font, t
        self.rect = pygame.Rect(200, 90, 560, 340)
        box = Collection()
        self.party = box.members()
        self.have = len([b for b in box.badges if b in GYMS])
        self.open = opened()
        self.champion = getattr(box, "champion", 0)
        self.lineup = random.choice(sorted(LINEUPS))
        self.buttons = []
        self.closed = False
        self.begin = False

    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    def team(self):
        return self.party

    def go(self):
        if self.party and self.open:
            self.begin, self.closed = True, True

    def close(self):
        self.closed = True

    def make_run(self, glade):
        return run(self, glade)

    def text(self, s, words, x, y, color=TEXT, center=False):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() // 2 if center else x, y))
        return img.get_width()

    def button(self, s, r, label, action, m, enabled=True):
        hot = enabled and bool(m) and r.collidepoint(m)
        cloth(s, r, MINT if hot else mix(CLOTH, EDGE, 0.2 if enabled else 0.55), hot=hot, alpha=215)
        img = self.font.render(label, False, WHITE if hot else TEXT if enabled else DIM)
        s.blit(img, img.get_rect(center=r.center))
        if enabled:
            self.buttons.append((r, action))

    def chip(self, s, kind, x, y):
        img = self.font.render(kind.upper(), False, EDGE)
        pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), (x, y, img.get_width() + 8, 14), border_radius=3)
        s.blit(img, (x + 4, y + 1))
        return img.get_width() + 8

    def draw(self, s, m, t):
        self.buttons = []
        r = self.rect
        k = ease((t - self.t) / 0.2)
        cloth(s, r, CLOTH, alpha=round(248 * k))
        if k < 1:
            return
        self.text(s, "THE MOONLIT HALL", r.centerx, r.y + 14, WHITE, center=True)
        if not self.open:
            self.text(s, "The great door is shut.", r.centerx, r.y + 70, TEXT, center=True)
            self.text(s, "It opens for those who hold every gym badge.", r.centerx, r.y + 90, TEXT, center=True)
            self.text(s, f"You have {self.have} of {len(GYMS)}.", r.centerx, r.y + 120, MINT, center=True)
            self.button(s, pygame.Rect(r.centerx - 60, r.bottom - 40, 120, 24), "Not now", self.close, m)
            return
        self.text(s, "The Elite 4 are waiting. Tonight it is", r.centerx, r.y + 36, TEXT, center=True)
        self.text(s, self.lineup, r.centerx, r.y + 52, WHITE, center=True)
        lvls, champ = levels()
        for i, ((name, types, col), level) in enumerate(zip(LINEUPS[self.lineup], lvls)):
            y = r.y + 80 + i * 30
            pygame.draw.circle(s, col, (r.x + 60, y + 7), 7)
            pygame.draw.circle(s, (255, 250, 230), (r.x + 60, y + 7), 7, 1)
            self.text(s, f"{i + 1}.  {name}", r.x + 80, y, WHITE)
            x = r.x + 230
            for kind in types:
                x += self.chip(s, kind, x, y) + 6
            self.text(s, f"6 creatures, Lv{level} (ace Lv{level + 2})", r.x + 320, y, DIM)
        y = r.y + 80 + 4 * 30
        pygame.draw.circle(s, (255, 236, 170), (r.x + 60, y + 7), 7)
        self.text(s, "5.  The Champion: whoever is in the hall tonight", r.x + 80, y, WHITE)
        self.text(s, f"Lv{champ} (ace Lv{champ + 2})", r.x + 420, y, DIM)
        self.text(s, "One after another; your team is healed before each. A loss ends the challenge.",
                  r.centerx, r.y + 236, DIM, center=True)
        if self.champion:
            self.text(s, f"You have been Champion {self.champion} time{'s' if self.champion > 1 else ''}.",
                      r.centerx, r.y + 254, MINT, center=True)
        if not self.party:
            self.text(s, "Your party is empty!", r.centerx, r.bottom - 66, DIM, center=True)
        self.button(s, pygame.Rect(r.centerx - 150, r.bottom - 40, 120, 24), "Not now", self.close, m)
        self.button(s, pygame.Rect(r.centerx + 30, r.bottom - 40, 120, 24), "Battle!", self.go, m,
                    enabled=bool(self.party))


def run(board, glade):
    from tower import Run

    class EliteRun(Run):
        """Four members, then the champion. `self.streak` counts who is beaten."""

        def battle(self, t):
            members = LINEUPS[board.lineup]
            if self.streak < len(members):
                name, types, _ = members[self.streak]
                level = levels()[0][self.streak]
                return (member_team(name, types, level),
                        f"Elite 4 {name} wants to battle! ({self.streak + 1} of 4, {' and '.join(types)})")
            name, _ = self.champ
            return champion_team(name), f"{name} wants to battle! The last battle."

        def after(self, arena, t):
            members = LINEUPS[board.lineup]
            if arena.battle.winner == 0:
                if not getattr(arena, "counted", False):
                    arena.counted = True
                    self.streak += 1
                    self.evolve(arena)
                    if self.streak > len(members):
                        box = Collection()
                        box.champion = getattr(box, "champion", 0) + 1
                        box.save()
                if self.streak > len(members):
                    return [("You are the Champion!", arena.close)]

                def next_one(t):
                    arena.counted = False
                    foes, intro = self.battle(t)
                    arena.restart(foes, intro, t)
                if self.streak < len(members):
                    label = f"On to {members[self.streak][0]}"
                else:
                    label = "On to the Champion"
                return [(label, next_one), ("Give up", arena.close)]
            return [("Close", arena.close)]

    r = EliteRun(board.team(), glade)
    r.champ = random.choice(CHAMPIONS)
    return r
