"""Trainers in every place (2026-10-30, his design): like Gen 3's route trainers.

His picks: one trainer stands in each place (not the Tower or the Moonlit Hall, which have their
own), on the lower screen. They are cloaked people dressed for their place (`TRAINERS`: cloak,
trim, and a charm on a staff that glows). Click one to battle. Beaten, they want a rematch the
next day, and come back stronger each time (`team`). A gold "!" bobs over the ones who want to
battle, and the Glade Nav (nav.py) shows them all on a map.

Their creatures are the place's own (gyms.locals_of). Level: two under the gym you would take on
next, then four more for every time you have beaten them, and one more creature each time
(two at first, up to six), evolving as the level allows; their ace is last, two levels up.

Saved in ~/.local/state/glade/trainers.json: {place: {"wins": n, "day": "YYYY-MM-DD"}}.
"""

import datetime
import json
import math
import os
import random

import pygame

from apex import ease
from art import glow, mix
from battle import CLOTH, DIM, EDGE, TEXT, cloth
from dex import MINT, WHITE
from life import q

# place: (name, cloak, trim, glow, charm)
TRAINERS = {
    "glade": ("Petal Keeper Rosalind", (236, 150, 196), (255, 230, 240), (255, 170, 220), "blossom"),
    "waterfall": ("Spray Diver Nerin", (90, 170, 190), (200, 245, 255), (140, 230, 255), "drop"),
    "river": ("Reed Poler Oswin", (80, 120, 190), (190, 220, 160), (120, 190, 255), "reed"),
    "forest": ("Bough Ranger Ivy", (80, 140, 90), (190, 150, 100), (160, 255, 140), "leaf"),
    "rocks": ("Moss Mason Bram", (120, 116, 130), (130, 200, 120), (150, 255, 190), "rune"),
    "ridge": ("Frost Herder Kip", (220, 230, 245), (255, 255, 255), (170, 230, 255), "flake"),
    "springs": ("Geyser Sage Mira", (210, 110, 80), (255, 210, 150), (255, 160, 90), "flame"),
    "caverns": ("Crystal Delver Moro", (110, 80, 170), (200, 170, 255), (200, 150, 255), "crystal"),
    "meadow": ("Star Catcher Lumi", (170, 150, 220), (255, 236, 160), (255, 240, 170), "star"),
    "hollow": ("Spore Gatherer Pell", (150, 100, 190), (255, 190, 120), (220, 160, 255), "shroom"),
    "bog": ("Mire Wader Fen", (80, 110, 90), (170, 200, 140), (170, 255, 200), "wisp"),
    "ruins": ("Rune Reader Isolde", (90, 100, 150), (210, 200, 170), (150, 230, 255), "rune"),
    "bridge": ("Cloud Walker Tam", (190, 186, 236), (255, 255, 255), (230, 230, 255), "feather"),
    "shore": ("Tide Comber Nell", (90, 200, 200), (240, 230, 200), (110, 255, 240), "shell"),
    "falls": ("Ice Climber Brynja", (150, 190, 230), (240, 250, 255), (180, 230, 255), "flake"),
    "peak": ("Aurora Watcher Sigrun", (90, 170, 150), (230, 200, 255), (150, 255, 210), "star"),
    "gully": ("Fern Forager Elm", (90, 150, 100), (210, 230, 150), (140, 240, 150), "leaf"),
    "orchard": ("Lantern Picker Clem", (200, 140, 80), (255, 220, 160), (255, 200, 110), "lantern"),
    "temple": ("Temple Diver Sable", (60, 140, 120), (220, 200, 120), (110, 240, 200), "rune"),
    "dunes": ("Sand Strider Zaid", (220, 190, 140), (150, 110, 200), (255, 230, 170), "moon"),
    "lava": ("Cinder Monk Basil", (170, 60, 50), (60, 40, 40), (255, 120, 70), "flame"),
    "grotto": ("Coral Diver Marina", (240, 150, 160), (255, 236, 220), (255, 160, 180), "shell"),
    "kelp": ("Deep Diver Kai", (40, 110, 110), (150, 220, 200), (90, 230, 210), "drop"),
    "lighthouse": ("Lamp Keeper Edwin", (230, 220, 200), (220, 110, 120), (255, 240, 180), "lantern"),
    "comet": ("Comet Chaser Vega", (120, 100, 200), (200, 230, 255), (200, 220, 255), "star"),
    "garden": ("Moon Gardener Liesel", (220, 214, 245), (180, 150, 230), (240, 236, 255), "moon"),
    "isles": ("Sky Pilgrim Aeris", (150, 200, 240), (255, 250, 230), (200, 236, 255), "feather"),
    "storm": ("Storm Caller Thane", (110, 110, 150), (250, 236, 100), (255, 245, 140), "bolt"),
    "thorn": ("Bramble Hermit Morwen", (80, 50, 90), (190, 60, 110), (255, 80, 140), "thorn"),
}
STATE = os.path.expanduser("~/.local/state/glade/trainers.json")
LEVEL_CAP = 70


def where(key):
    from game import Minimap
    return Minimap.NAMES.get(key, key)


# --- who has been beaten, and when ------------------------------------------------------------------

_seen = [None, {}]


def record():
    """{place: {"wins": n, "day": "YYYY-MM-DD"}}, read again only when the file changes."""
    try:
        stamp = os.stat(STATE).st_mtime
    except OSError:
        return {}
    if stamp != _seen[0]:
        try:
            with open(STATE) as f:
                _seen[1] = json.load(f)
        except (OSError, ValueError):
            _seen[1] = {}
        _seen[0] = stamp
    return _seen[1]


def today():
    return datetime.date.today().isoformat()


def wins(key):
    return record().get(key, {}).get("wins", 0)


def ready(key):
    """Wants to battle: never beaten, or last beaten before today (his pick: a rematch the next day)."""
    return record().get(key, {}).get("day") != today()


def beaten(key):
    data = dict(record())
    data[key] = dict(wins=wins(key) + 1, day=today())
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, STATE)


# --- their creatures ---------------------------------------------------------------------------------

def strength(key):
    """(level, how many) for this trainer now: tied to your gyms, stronger each rematch."""
    from gyms import GYMS, level_for
    from team import Collection
    n = len([b for b in Collection().badges if b in GYMS]) + 1
    r = wins(key)
    level = min(LEVEL_CAP, max(5, level_for(min(n, len(GYMS))) - 2 + 4 * r))
    return level, min(6, 2 + r)


def team(key):
    """The same team all day for the same rematch (seeded by place and rematch)."""
    from gyms import grown, locals_of
    from team import roll_ivs
    level, size = strength(key)
    rng = random.Random(f"{key}/{wins(key)}")
    firsts = locals_of(key)
    rng.shuffle(firsts)
    picks = firsts[:size]
    while len(picks) < size and firsts:  # a place with few kinds: some twice
        picks.append(rng.choice(firsts))
    out = [(grown(f, level), roll_ivs(rng), None, None, level) for f in picks]
    if out:
        sp, ivs, *_ = out[-1]
        out[-1] = (sp, tuple(max(v, 18) for v in ivs), None, None, min(LEVEL_CAP, level + 2))
    return out


# --- the figure ---------------------------------------------------------------------------------------

def charm(s, kind, x, y, c):
    """The little shape on top of the staff, in the glow colour."""
    hi = mix(c, (255, 255, 255), 0.6)
    if kind == "flake":
        for dx, dy in ((3, 0), (0, 3), (2, 2), (2, -2)):
            pygame.draw.line(s, hi, (x - dx, y - dy), (x + dx, y + dy))
    elif kind in ("flame", "drop", "wisp"):
        up = kind != "drop"
        pts = [(x - 2, y + (1 if up else -1)), (x, y + (-4 if up else 4)), (x + 2, y + (1 if up else -1))]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.circle(s, c, (x, y + (1 if up else -1)), 2)
        s.set_at((x, y), hi)
    elif kind == "leaf":
        pygame.draw.ellipse(s, c, (x - 2, y - 4, 5, 8))
        pygame.draw.line(s, hi, (x, y - 3), (x, y + 3))
    elif kind in ("star", "crystal"):
        if kind == "star":
            for dx, dy in ((3, 0), (0, 3)):
                pygame.draw.line(s, hi, (x - dx, y - dy), (x + dx, y + dy))
            s.set_at((x, y), (255, 255, 255))
        else:
            pygame.draw.polygon(s, c, [(x, y - 4), (x + 2, y), (x, y + 3), (x - 2, y)])
            s.set_at((x, y - 2), hi)
    elif kind == "moon":
        pygame.draw.circle(s, hi, (x, y), 3)
        pygame.draw.circle(s, (20, 14, 30), (x + 2, y - 1), 2)
    elif kind == "bolt":
        pygame.draw.lines(s, hi, False, [(x + 1, y - 4), (x - 1, y), (x + 1, y), (x - 1, y + 4)])
    elif kind == "lantern":
        pygame.draw.rect(s, mix(c, (60, 40, 40), 0.5), (x - 2, y - 3, 5, 6))
        pygame.draw.rect(s, hi, (x - 1, y - 2, 3, 4))
    elif kind == "shroom":
        pygame.draw.ellipse(s, c, (x - 3, y - 3, 7, 4))
        pygame.draw.line(s, hi, (x, y), (x, y + 2))
    elif kind == "shell":
        for a in range(-2, 3):
            pygame.draw.line(s, c if a % 2 else hi, (x, y + 2), (x + a * 2, y - 2))
    elif kind == "feather":
        pygame.draw.line(s, hi, (x - 2, y + 3), (x + 2, y - 4))
        pygame.draw.line(s, c, (x - 1, y + 1), (x + 2, y - 2), 2)
    elif kind == "thorn":
        pygame.draw.circle(s, c, (x, y), 2)
        for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            s.set_at((x + dx, y + dy), hi)
    elif kind == "blossom":
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            pygame.draw.circle(s, c, (x + dx, y + dy), 1)
        s.set_at((x, y), (255, 250, 200))
    elif kind == "reed":
        pygame.draw.ellipse(s, mix(c, (120, 80, 50), 0.6), (x - 1, y - 4, 3, 7))
    else:  # rune and anything else: a little glowing stone
        pygame.draw.rect(s, c, (x - 2, y - 3, 5, 6))
        pygame.draw.line(s, hi, (x, y - 2), (x, y + 1))


class Trainer:
    """A cloaked figure with a staff, breathing slowly, the cloak's hem stirring, the charm glowing.
    Drawn before the lighting (the cloak), lit by its charm, and the charm and "!" shine after."""

    def __init__(self, key, x, y):
        self.key, self.x, self.y = key, x, y
        self.name, self.cloak, self.trim, self.glow, self.kind = TRAINERS[key]
        self.phase = (sum(map(ord, key)) % 100) / 16

    def charm_at(self, t):
        bob = math.sin(t * 1.3 + self.phase)
        return self.x + 10, self.y - 39 + round(bob * 0.6)

    def draw(self, s, t):
        x, y = self.x, self.y
        breathe = round(math.sin(t * 1.3 + self.phase) * 0.6)
        sway = math.sin(t * 0.9 + self.phase) * 1.5
        shade = mix(self.cloak, (20, 10, 30), 0.45)
        pygame.draw.ellipse(s, (16, 10, 24), (x - 13, y - 3, 30, 7))  # its shadow
        # the staff, held out at its side
        pygame.draw.line(s, (90, 64, 50), (x + 10, y), (x + 10, y - 36 + breathe), 2)
        # the cloak: wide at the hem, which stirs; a darker fold down one side
        top = y - 26 + breathe
        hem = [(x - 11 + sway * 0.4, y), (x - 6 + sway, y + 1), (x + sway, y), (x + 5 + sway, y + 1), (x + 11 + sway * 0.4, y)]
        body = [(x - 7, top), (x + 7, top)] + hem[::-1]
        pygame.draw.polygon(s, self.cloak, body)
        pygame.draw.polygon(s, shade, [(x + 2, top + 2), (x + 7, top), hem[-1], hem[-2], (x + 3, y)])
        pygame.draw.lines(s, self.trim, False, hem, 2)                 # trim along the hem
        pygame.draw.line(s, self.trim, (x, top + 4), (x, y - 2))         # and down the front
        # the arm out to the staff, a sleeve with a hand
        pygame.draw.polygon(s, self.cloak, [(x + 4, top + 4), (x + 10, top + 10), (x + 9, top + 14), (x + 3, top + 10)])
        pygame.draw.circle(s, (230, 200, 180), (x + 10, top + 12), 2)
        # the hood: a round cowl with a point falling back, the face in its shadow
        pygame.draw.circle(s, self.cloak, (x, top - 4), 8)
        pygame.draw.polygon(s, self.cloak, [(x - 6, top - 9), (x - 12, top - 2 + sway * 0.3), (x - 5, top)])
        pygame.draw.circle(s, mix(self.trim, self.cloak, 0.3), (x, top - 4), 8, 1)
        pygame.draw.ellipse(s, (24, 16, 34), (x - 4, top - 7, 9, 9))
        pygame.draw.ellipse(s, (210, 180, 160), (x - 2, top - 2, 5, 3))  # a glimpse of a chin

    def light(self, lm, t):
        cx, cy = self.charm_at(t)
        k = 0.85 + 0.15 * math.sin(t * 2.1 + self.phase)
        glow(lm, cx, cy + 14, int(46 * k), self.glow, q(120 * k))

    def shine(self, s, t):
        cx, cy = self.charm_at(t)
        k = 0.8 + 0.2 * math.sin(t * 2.1 + self.phase)
        glow(s, cx, cy, int(9 * k), self.glow, q(110 * k))
        charm(s, self.kind, cx, cy, self.glow)
        # two pin-points of the charm's light in the hood
        top = self.y - 26 + round(math.sin(t * 1.3 + self.phase) * 0.6)
        for ex in (self.x - 2, self.x + 2):
            s.set_at((ex, top - 3), mix(self.glow, (255, 255, 255), 0.5))
        if ready(self.key):  # wants to battle: a gold "!" bobbing over the hood
            bx, by = self.x, top - 20 + round(math.sin(t * 3 + self.phase) * 1.5)
            glow(s, bx, by, 10, (255, 214, 120), 70)
            pygame.draw.rect(s, (255, 236, 160), (bx - 1, by - 5, 3, 7))
            pygame.draw.rect(s, (255, 236, 160), (bx - 1, by + 4, 3, 2))


HERE = dict(glade=(420, 120))  # the Glade's lily pond is not in its lower spec: stand above it
SPOTS = [(560, 200), (470, 250), (600, 140), (400, 190), (520, 300), (330, 280), (450, 120), (620, 180), (300, 120),
         (260, 310), (450, 370), (230, 200)]


def place(low, clear):
    """Stand this place's trainer on its lower screen, somewhere clear of paths and the pond."""
    from gyms import SHOW
    from scenes import Spot
    if low.key not in TRAINERS or not SHOW:
        return
    signs = [p["sign"] for p in getattr(low, "spec_paths", [])]

    def free(x, y):  # clear of paths and the pond, and its name board clear of the path signs
        return clear(x, y, 30) and all(math.hypot(x - sx, (y - sy) * 0.6) > 150 for sx, sy in signs)
    x, y = HERE.get(low.key) or next(((x, y) for x, y in SPOTS if free(x, y)), SPOTS[0])
    low.parts.append(Trainer(low.key, x, y))
    low.spots.append(Spot("trainer", (x - 14, y - 44, 30, 48), TRAINERS[low.key][0], low.key, (x, y - 20),
                          sign=(x, y - 66)))


# --- the board, when you click one -----------------------------------------------------------------

class TrainerBoard:
    def __init__(self, font, t, key):
        from team import Collection
        self.font, self.t, self.key = font, t, key
        self.rect = pygame.Rect(250, 130, 460, 260)
        self.party = Collection().members()
        self.ready = ready(key)
        self.wins = wins(key)
        self.level, self.size = strength(key)
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
        if self.party and self.ready:
            self.begin, self.closed = True, True

    def close(self):
        self.closed = True

    def make_run(self, glade):
        return run(self, glade)

    def text(self, s, words, x, y, color=TEXT):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() // 2, y))

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
        name, cloak, trim, glow_c, kind = TRAINERS[self.key]
        pic = pygame.Surface((48, 72), pygame.SRCALPHA)  # the trainer, drawn twice as big
        fig = Trainer(self.key, 22, 64)
        fig.draw(pic, t)
        fig.shine(pic, t)
        s.blit(pygame.transform.scale(pic, (96, 144)), (r.x + 18, r.y + 40))
        cx = r.centerx + 30
        self.text(s, name.upper(), cx, r.y + 18, WHITE)
        self.text(s, f"A wanderer of {where(self.key)}", cx, r.y + 38, DIM)
        if self.ready:
            self.text(s, "Wants to battle!" if not self.wins else f"Wants a rematch! (beaten {self.wins} "
                      f"time{'s' if self.wins > 1 else ''})", cx, r.y + 72, MINT)
            self.text(s, f"{self.size} creature{'s' if self.size > 1 else ''} at Lv{self.level}"
                      + (f", their ace at Lv{min(LEVEL_CAP, self.level + 2)}" if self.size > 1 else ""),
                      cx, r.y + 90, WHITE)
        else:
            self.text(s, "Beaten today. Come back tomorrow:", cx, r.y + 72, TEXT)
            self.text(s, "they will want a rematch, and be stronger.", cx, r.y + 90, TEXT)
        if not self.party:
            self.text(s, "Your party is empty: get a starter at the Battle Tower first!", r.centerx, r.bottom - 70, DIM)
        self.button(s, pygame.Rect(r.centerx - 150, r.bottom - 40, 120, 24), "Not now", self.close, m)
        self.button(s, pygame.Rect(r.centerx + 30, r.bottom - 40, 120, 24), "Battle!", self.go, m,
                    enabled=bool(self.party) and self.ready)


def run(board, glade):
    from tower import Run

    class TrainerRun(Run):
        def battle(self, t):
            return team(board.key), f"{TRAINERS[board.key][0]} wants to battle!"

        def after(self, arena, t):
            if arena.battle.winner == 0:
                if not getattr(arena, "counted", False):
                    arena.counted = True
                    beaten(board.key)
                    self.evolve(arena)
                return [("Won! They'll want a rematch tomorrow", arena.close)]
            return [("Close", arena.close)]

    return TrainerRun(board.team(), glade)
