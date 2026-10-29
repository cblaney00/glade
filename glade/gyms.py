"""Gym leaders — one in each place, each with creatures that fit it (his design, 2026-10-29).

Walk to a place with a gym and click its banner stone. The leader brings creatures that live
there, of their own type. Gyms can be taken on in any order; what makes one hard is how many
you have already beaten (`level_for`): his rule is to go from about Lv 7 to Lv 55 (where a
casual player beats Emerald's Elite 4) over every place in the glade, not over eight gyms,
so it climbs slowly. The team grows too: 3 creatures, then 4, 5 and 6 (`size_for`).

Every trainer has an **ace** (`with_ace`): their last creature, a little stronger than the
rest (a stronger kind of the same stage, two levels up, good IVs), but not out of reach.

Beaten gyms are kept as badges (`Collection.badges`, in the order won). A beaten leader can
be fought again at the level they were won at, for practice.

Part one has three gyms (the Forest, the River, the Mossy Rocks). The Elite 4 come once
every gym is beaten (not made yet).
"""

import random

import pygame

import art
import evolve
from apex import ease
from battle import CLOTH, DIM, EDGE, LEGENDARY, SPECIES, TEXT, TYPE_COLOR, Arena, cloth, mix
from dex import MINT, WHITE, picture
from team import Collection, roll_ivs

PLACES = 30      # every place in the glade (scenes.MAP): the climb is spread over all of them
FIRST, LAST = 7, 55

# key: (leader's name, their types, the stone's spot (x, y) in that place, banner colour)
GYMS = {
    "forest": ("Leader Bramwen", ("Grass",), (690, 404), (150, 230, 120)),
    "river": ("Leader Marisel", ("Water",), (560, 500), (120, 200, 255)),
    "rocks": ("Leader Cragga", ("Rock", "Ground"), (320, 420), (220, 190, 140)),
}
TITLES = dict(forest="Forest Gym", river="River Gym", rocks="Mossy Rocks Gym")


def level_for(n):
    """The level of the n-th gym taken on (1 = the first)."""
    return round(FIRST + (n - 1) * (LAST - FIRST) / (PLACES - 1))


def size_for(n):
    return min(6, 2 + n)


def total(sp):
    return sum(SPECIES[sp]["base"])


def stage_for(level):
    return 3 if level >= 32 else 2 if level >= 16 else 1


def grown(first, level):
    """`first`'s line at the stage that level allows (or as far as the line goes)."""
    for st in range(stage_for(level), 0, -1):
        sp = evolve.species_at(first, st)
        if sp and sp in SPECIES:
            return sp
    return first


def locals_of(key):
    """The first stages that live in that place (lore.WHERE)."""
    import lore
    return sorted(s for s, w in lore.WHERE.items() if key in w and s in SPECIES and s not in LEGENDARY
                  and evolve.stage_of(s)[1] == 1 and "tower" not in w)


def themed(key):
    """The place's own creatures of the leader's type first, then the rest of its creatures."""
    types = set(GYMS[key][1])
    mine = locals_of(key)
    return [s for s in mine if types & set(SPECIES[s]["types"])], [s for s in mine if not types & set(SPECIES[s]["types"])]


def with_ace(team, rng, stronger=None):
    """Make the last creature the ace: a stronger kind of the same stage (base total 20-45
    up, from `stronger` if given), two levels higher, good IVs."""
    if not team:
        return team
    species, ivs, moves, nature, level = team[-1]
    _, stage = evolve.stage_of(species)
    taken = {t[0] for t in team}
    pool = stronger or [sp for sp in SPECIES if sp not in LEGENDARY and evolve.stage_of(sp)[1] == stage]
    pool = [sp for sp in pool if sp not in taken or sp == species]
    up = [sp for sp in pool if 20 <= total(sp) - total(species) <= 45]
    if not up:
        up = sorted(pool, key=total)[-1:] or [species]
    ace = rng.choice(sorted(up))
    ivs = tuple(max(v, 20) for v in (ivs or roll_ivs(rng)))
    team[-1] = (ace, ivs, None, None, (level or 5) + 2)
    return team


def leader_team(key, n, rng):
    """The leader's creatures for the n-th gym: the place's own, of their type where it can."""
    level = level_for(n)
    typed, others = themed(key)
    rng.shuffle(typed)
    rng.shuffle(others)
    picks = (typed + others)[:size_for(n)]
    # the ace is the strongest of their type, at the stage the level allows
    best = max(typed or picks, key=lambda f: total(grown(f, level)))
    picks = [f for f in picks if f != best][:size_for(n) - 1] + [best]
    team = [(grown(f, level), roll_ivs(rng), None, None, level) for f in picks]
    ace = team[-1]
    team[-1] = (ace[0], tuple(max(v, 20) for v in ace[1]), None, None, level + 2)
    return team


# --- where the gym stands ------------------------------------------------------------------------

def place(sc):
    """A carved banner stone with the gym's colour, and its clickable spot (Scene.done calls this)."""
    if sc.key not in GYMS:
        return
    from scenes import Spot
    name, types, (x, y), col = GYMS[sc.key]
    lay = art.plane()
    stone = sc.col("stone", 0.2) if hasattr(sc, "col") else (120, 110, 140)
    pygame.draw.ellipse(lay, (20, 12, 30), (x - 18, y - 4, 36, 9))
    pygame.draw.polygon(lay, mix(stone, (20, 10, 40), 0.3), [(x - 13, y), (x - 11, y - 40), (x, y - 46),
                                                              (x + 11, y - 40), (x + 13, y)])
    pygame.draw.polygon(lay, mix(stone, (255, 255, 255), 0.08), [(x - 11, y - 2), (x - 9, y - 38), (x, y - 43),
                                                                 (x, y - 2)])
    # a cloth banner in the leader's colour, with a badge ring
    pygame.draw.polygon(lay, col, [(x - 7, y - 34), (x + 7, y - 34), (x + 7, y - 12), (x, y - 16), (x - 7, y - 12)])
    pygame.draw.circle(lay, (255, 250, 230), (x, y - 26), 4, 1)
    sc.raw(lay)
    sc.lamp(x, y - 26, 50, col, 70)
    sc.shine(x, y - 26, 6, col, 90)
    sp = Spot("gym", (x - 16, y - 48, 32, 50), TITLES[sc.key], sc.key, (x, y - 20), sign=(x, y - 62))
    sc.spots.append(sp)


# --- the board at the stone ----------------------------------------------------------------------

class GymBoard:
    """The leader, their type, your badges, and Battle."""

    def __init__(self, font, t, key):
        self.font, self.t, self.key = font, t, key
        self.rect = pygame.Rect(230, 110, 500, 300)
        box = Collection()
        self.party = box.members()
        self.badges = list(box.badges)
        self.won = key in self.badges
        self.n = self.badges.index(key) + 1 if self.won else len(self.badges) + 1
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
        if self.party:
            self.begin, self.closed = True, True

    def close(self):
        self.closed = True

    def make_run(self, glade):
        return run(self, glade)

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
        name, types, _, col = GYMS[self.key]
        self.text(s, TITLES[self.key].upper(), r.centerx, r.y + 14, WHITE, center=True)
        self.text(s, f"{name}, who trains {' and '.join(types)} creatures", r.centerx, r.y + 36, TEXT, center=True)
        x = r.centerx - 30 * len(types)
        for kind in types:
            img = self.font.render(kind.upper(), False, EDGE)
            pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), (x, r.y + 54, img.get_width() + 8, 14),
                             border_radius=3)
            s.blit(img, (x + 4, r.y + 55))
            x += img.get_width() + 14
        level, size = level_for(self.n), size_for(self.n)
        if self.won:
            self.text(s, "You have this badge. A rematch, for practice:", r.centerx, r.y + 86, MINT, center=True)
        else:
            self.text(s, f"Your gym number {self.n}:", r.centerx, r.y + 86, DIM, center=True)
        self.text(s, f"{size} creatures at Lv{level}, their ace at Lv{level + 2}", r.centerx, r.y + 102, WHITE,
                  center=True)
        self.text(s, f"Badges: {len(self.badges)}", r.centerx, r.y + 130, TEXT, center=True)
        bx = r.centerx - 14 * len(self.badges)
        for b in self.badges:
            c = GYMS.get(b, (0, 0, 0, (200, 200, 200)))[3]
            pygame.draw.circle(s, c, (bx + 14, r.y + 160), 9)
            pygame.draw.circle(s, (255, 250, 230), (bx + 14, r.y + 160), 9, 1)
            bx += 28
        if not self.party:
            self.text(s, "Your party is empty: get a starter at the Battle Tower first!", r.centerx, r.bottom - 70,
                      DIM, center=True)
        self.button(s, pygame.Rect(r.centerx - 150, r.bottom - 40, 120, 24), "Not now", self.close, m)
        self.button(s, pygame.Rect(r.centerx + 30, r.bottom - 40, 120, 24), "Battle!", self.go, m,
                    enabled=bool(self.party))


def run(board, glade):
    from tower import Run

    class GymRun(Run):
        def battle(self, t):
            rng = random.Random()
            name = GYMS[board.key][0]
            return leader_team(board.key, board.n, rng), f"{name} wants to battle! ({TITLES[board.key]})"

        def after(self, arena, t):
            if arena.battle.winner == 0:
                if not getattr(arena, "counted", False):
                    arena.counted = True
                    box = Collection()
                    if board.key not in box.badges:
                        box.badges.append(board.key)
                        box.save()
                    self.evolve(arena)
                return [(f"You won the {TITLES[board.key]} badge!" if not board.won else "Rematch won!",
                         arena.close)]
            return [("Close", arena.close)]

    return GymRun(board.team(), glade)
