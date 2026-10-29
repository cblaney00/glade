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
import subprocess
import threading

import pygame

from apex import ease
from battle import LEGENDARY, CLOTH, DIM, EDGE, SPECIES, TEXT, Arena, cloth, mix
from dex import MINT, WHITE, picture
from team import TEAM, Collection, reset

TRAINERS = ["Moss Warden Ivy", "Lantern Keeper Bram", "Tidepool Nell", "Starwatcher Orrin", "Frost Herder Kip",
            "Ember Sage Ottilie", "Mushroom Scout Pell", "Owl Whisperer Wren", "Cave Dweller Moro", "Petal Dancer Suki",
            "Glowworm Hermit Tam", "Mist Walker Ysolde", "Thunder Chaser Rook", "Slug Racer Fen", "Aurora Seer Lumi"]


def trainer(streak, rng, mine=TEAM):
    """The next challenger: a name, and one creature for each of yours (his rule: the tower is
    won by strategy and luck, not by grinding). Each of theirs is as strong as the one of yours
    it stands for: a different kind with a base-stat total within 20 of it (a first stage
    against a first stage, a final one against a final one), with IVs about as good as its
    own (each within 6, shuffled about). It is matched to whatever party you bring, so it stays
    fair as your party changes, and the streak does not make them stronger. Each is the same
    level as the one of yours it stands for."""
    from team import roll_ivs
    if isinstance(mine, int):
        mine = [None] * mine
    totals = [sum(SPECIES[k.species]["base"]) if k else 310 for k in mine]
    taken = {k.species for k in mine if k}
    team = []
    for k, total in zip(mine[:TEAM], totals):
        near = [sp for sp, d in SPECIES.items() if abs(sum(d["base"]) - total) <= 20 and sp not in taken
                and sp not in LEGENDARY]  # trainers never have a legendary
        if not near:
            near = sorted((sp for sp in SPECIES if sp not in taken and sp not in LEGENDARY), key=lambda sp: abs(sum(SPECIES[sp]["base"]) - total))[:3]
        species = rng.choice(sorted(near))
        taken.add(species)
        if k is None:
            ivs = roll_ivs(rng)
        else:
            ivs = [max(0, min(31, v + rng.randint(-6, 6))) for v in k.ivs]
            rng.shuffle(ivs)
        team.append((species, tuple(ivs), None, None, k.level if k else None))
    from gyms import with_ace
    return rng.choice(TRAINERS), with_ace(team, rng)  # every trainer has an ace (his rule)


class Run:
    """One go at the tower: your team, the streak so far, and what happens between battles."""

    def __init__(self, team, glade, single=False):
        self.team, self.glade = team, glade
        self.single = single  # a Trainer battle: one at a time, no streak
        self.streak = 0
        self.rng = random.Random()
        self.recorded = False

    def battle(self, t):
        name, foes = trainer(self.streak, self.rng, self.team)
        intro = f"{name} wants to battle!" if self.single else f"{name} wants to battle! (Battle {self.streak + 1})"
        return foes, intro

    def open(self, t):
        g = self.glade
        foes, intro = self.battle(t)
        low = g.lower() if g.bottom else None
        arena = Arena(g.here, low, g.signs.font, t, mode="tower", mine=self.team, foes=foes, intro=intro,
                      after=self.after)
        arena.mouse = g.top.mouse
        return arena

    def count_wins(self, battle):
        """Each of yours that went out in a won battle has one more Tower win (just counted now:
        they evolve by level, levels.py)."""
        box = Collection()
        for i in sorted(battle.fought):
            if i >= len(self.team):
                continue
            mine = self.team[i]
            kept = box.find(mine.uid) or mine
            kept.wins += 1
            mine.wins = kept.wins
        box.save()

    def evolve(self, arena):
        """Any of yours that grew to level 16 or 32 in that battle evolves now, between battles
        (you can stop it: evolve_party.py)."""
        ready = arena.ready()
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
        if self.single:
            if arena.battle.winner == 0 and not getattr(arena, "counted", False):
                arena.counted = True
                self.evolve(arena)

            def another(t):
                arena.counted = False
                foes, intro = self.battle(t)
                arena.restart(foes, intro, t)
            return [("Another trainer", another), ("Close", arena.close)]
        if arena.battle.winner == 0:
            if not getattr(arena, "counted", False):
                arena.counted = True
                self.streak += 1
                self.record()
                self.count_wins(arena.battle)
                self.evolve(arena)

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
        self.single = False     # Trainer battle: one battle against a trainer your level, not a streak
        self.boxes = False
        self.asking = None      # resetting: None, "sure" (the are-you-sure note), "password" or "wrong"

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

    def go_single(self):
        if self.party:
            self.single = True
            self.go()

    def make_run(self, glade):
        return Run(self.team(), glade, single=self.single)

    def open_boxes(self):
        self.boxes, self.closed = True, True

    def ask_reset(self):
        self.asking = "sure"

    def keep(self):
        self.asking = None

    def do_reset(self):
        """Only after his computer password (the usual password window, from polkit)."""
        self.asking = "password"

        def check():
            try:
                ok = subprocess.run(["/run/wrappers/bin/pkexec", "/run/current-system/sw/bin/true"],
                                    capture_output=True, timeout=300).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                ok = False
            if ok:
                reset()
                self.party, self.best, self.asking = [], 0, "done"
            else:
                self.asking = "wrong"
        threading.Thread(target=check, daemon=True).start()

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
                self.text(s, f"Lv{kept.level}   IVs {sum(kept.ivs)}/186", cr.centerx, cr.y + 80, DIM, center=True)
        self.text(s, f"Best streak: {self.best}", r.x + 20, r.bottom - 32, TEXT)
        if not self.party:
            self.text(s, "Your party is empty: catch some creatures first!", r.centerx, r.bottom - 60, DIM, center=True)
        self.button(s, pygame.Rect(r.right - 330, r.bottom - 38, 120, 24), "Your boxes", self.open_boxes, m)
        self.button(s, pygame.Rect(r.right - 200, r.bottom - 66, 180, 24), "Trainer battle", self.go_single, m,
                    enabled=bool(self.party))
        badges = Collection().badges if not hasattr(self, "badges") else self.badges
        self.badges = badges
        self.text(s, f"Gym badges: {len(badges)}", r.x + 20, r.bottom - 60, TEXT)
        self.button(s, pygame.Rect(r.right - 200, r.bottom - 38, 180, 24), "Begin the challenge!", self.go, m,
                    enabled=bool(self.party))
        self.button(s, pygame.Rect(r.x + 150, r.bottom - 38, 100, 24), "Reset all", self.ask_reset, m,
                    enabled=bool(self.party) or self.best > 0)
        if self.asking:
            self.note(s, m)

    NOTES = {
        "sure": ("Are you sure?", "Every creature you have caught is let go, and your best streak",
                 "goes back to 0. Then you choose a new starter."),
        "password": ("Type your computer password", "in the window that has opened, to reset everything.", ""),
        "wrong": ("Not reset", "The password wasn't given, so everything is just as it was.", ""),
        "done": ("All reset!", "Click the tower door again to choose a new starter.", ""),
    }

    def note(self, s, m):
        """The are-you-sure note over the board: only its own buttons can be clicked."""
        self.buttons = []
        r = self.rect
        n = pygame.Rect(r.centerx - 230, r.centery - 70, 460, 140)
        cloth(s, n, mix(CLOTH, EDGE, 0.15), alpha=250)
        title, line1, line2 = self.NOTES[self.asking]
        self.text(s, title, n.centerx, n.y + 14, WHITE, center=True)
        self.text(s, line1, n.centerx, n.y + 40, TEXT, center=True)
        self.text(s, line2, n.centerx, n.y + 54, TEXT, center=True)
        if self.asking == "sure":
            self.button(s, pygame.Rect(n.centerx - 190, n.bottom - 38, 180, 24), "No, keep them", self.keep, m)
            self.button(s, pygame.Rect(n.centerx + 10, n.bottom - 38, 180, 24), "Yes, reset everything",
                        self.do_reset, m)
        elif self.asking in ("wrong", "done"):
            self.button(s, pygame.Rect(n.centerx - 60, n.bottom - 38, 120, 24), "OK",
                        self.close if self.asking == "done" else self.keep, m)
