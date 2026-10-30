"""The Glade Book: the game's encyclopedia (2026-10-30, his ask: "an encyclopedia for this game
that can be opened in an icon in the bottom right corner of the bottom screen").

A little book on a wooden plaque beside the minimap (`icon_rect`, drawn by `draw_icon`) opens
it over the top screen, like the Forest Dex. It is an open book: chapter ribbons along the top,
the chapter's topics down the left page, the chosen topic on the right page.

Chapters: Start here (how to play), Places (every place: what it is like, the ways out, who
lives there, its gym, and "Go there"), Types (each type's strengths and weaknesses, and the
whole chart), Battles (the rules), and Gyms & the Elite 4. Creatures are the Forest Dex's job,
so its button opens the Dex. Animals not yet found in the Dex are shown as "???".
"""

import math

import pygame

from apex import ease
from battle import CHART, PHYSICAL, TYPE_COLOR, effectiveness
from art import mix

COVER = (70, 44, 96)       # violet leather
COVER_HI = (110, 76, 140)
PAGE = (236, 230, 246)     # pale lavender paper
PAGE_SH = (206, 196, 226)  # the shade by the spine
INK = (56, 36, 84)         # dark plum words (his ask for the badge case: dark words read well)
FADED = (124, 104, 150)
HOT = (170, 70, 150)
GOLD = (220, 170, 70)
RIBBONS = [(255, 150, 200), (140, 210, 255), (170, 230, 140), (255, 190, 120), (200, 170, 255)]

TYPES = list(CHART)

# --- the words ---------------------------------------------------------------------------------

START = [
    ("Welcome", [
        "This is the Glade: a forest clearing that is always night, lit by glowing moss, mushrooms, "
        "lanterns and fireflies. Thirty-one places lie around it, joined by paths.",
        "Creatures live in every place. Find them, catch them, raise them, and battle gym leaders, "
        "the Battle Tower and, at last, the Elite 4.",
        "This book tells you how. Pick a chapter on the ribbons above."]),
    ("Getting around", [
        "Click a path's name board to walk that way. Left always goes left on the map, up always up.",
        "The minimap in the lower screen's corner shows every place; the one you are in glows. "
        "Point at a place to see its name, and click it to go straight there.",
        "The Home key takes you back to the Glade. Rest closes the game."]),
    ("Your first creature", [
        "Walk down past the Mossy Rocks to the Battle Tower and click its door. The first time, you "
        "choose your starter: Mossprance (Grass), Kindlet (Fire) or Pippalotl (Water).",
        "Starters are never found in the wild."]),
    ("Looking at animals", [
        "Right-click any animal to see its stats card: its types, base stats, and its own IVs drawn "
        "as a six-sided web. The card can open its Forest Dex page.",
        "Animals come and go like wild creatures do: each stays out a while, then slips away, and a "
        "new one comes out in its place. Now and then one is already evolved."]),
    ("Catching", [
        "On an animal's stats card, press Battle it! to fight it with your party.",
        "Glow jars catch it. They open up once you have tried a run at the Battle Tower. The weaker "
        "it is, the likelier it stays in the jar; asleep or frozen helps a lot, and paralysed, "
        "poisoned or burned helps a little.",
        "What you catch goes into your party of six, or your boxes when the party is full."]),
    ("Your party and boxes", [
        "Your party is the six you take into battle. Open it with the Your party board, or at the "
        "shrine by the Tower's door.",
        "Click a creature to pick it up and click a slot to put it down or swap. Pointing at one shows "
        "its full summary, and Change moves lets it learn any move its kind can learn."]),
    ("Predator vision", [
        "The golden button in the lower screen's corner turns the world grey for a few seconds, and "
        "only the animals keep their colour, outlined in gold.",
        "One with a thick, pulsing electric-blue outline has very good IVs: top five in a hundred. "
        "Worth catching."]),
    ("Thunderstorm", [
        "The Thunderstorm button brings rain and lightning. Everyone in sight shelters, and when it "
        "passes, a fresh mix of the animals who live there comes out.",
        "When a new version of the Glade is ready, it shows a gold notice: press Thunderstorm to load it."]),
    ("Hiding", [
        "When a game or film fills the screen, after a while the animals hide; when you come back they "
        "come out again, one by one. Keep animals out stops that."]),
    ("Secrets", [
        "The moon is listening. Click it, and it shines while it listens.",
        "Some say it answers to the right word."]),
]

BATTLES = [
    ("The rules", [
        "Battles follow Pokemon's third generation (Gen 3 OU): six against six at most, one out at "
        "a time. Each turn you pick a move or switch; the foe picks its own.",
        "A creature faints at 0 HP. When all of one side's have fainted, the other side wins."]),
    ("Moves", [
        "Each creature knows four moves. A move has a type, a power, an accuracy and a number of "
        "uses (PP). Status moves do no damage but change things: lowering stats, putting to sleep, "
        "Protect, and so on.",
        "In Gen 3 a move is physical or special because of its type: Normal, Fighting, Flying, "
        "Poison, Ground, Rock, Bug, Ghost and Steel moves are physical; the rest are special."]),
    ("Damage", [
        "Damage comes from the move's power, the attacker's Attack or Sp. Atk, the defender's Defense "
        "or Sp. Def, and the level.",
        "A move of the attacker's own type hits 1.5 times as hard. Type matchups multiply it by 2 "
        "(super effective), 0.5 (not very effective) or 0 (no effect); see the Types chapter.",
        "Now and then a hit is critical and does double."]),
    ("Status", [
        "Burned: hurt each turn, and physical hits are halved. Poisoned: hurt each turn (badly "
        "poisoned hurts more every turn). Paralysed: slower, and sometimes can't move. Asleep: can't "
        "move for a few turns. Frozen: can't move until it thaws. Confused: may hurt itself."]),
    ("Switching", [
        "Switch to bring in a better match. The one coming in takes the foe's move that turn. When "
        "one of yours faints, you choose who comes out next."]),
    ("Levels and experience", [
        "Wild creatures are Lv5 as a first stage, Lv16 as a middle stage, Lv32 as a final one.",
        "Beating a foe gives experience to yours who faced it and are still standing. Trainers' "
        "creatures give half again as much. Catching gives none."]),
    ("Evolving", [
        "Every line has three stages. Yours evolve at Lv16 and Lv32, after the battle they reach it "
        "in. You can press Stop to keep it as it is."]),
    ("IVs, EVs and natures", [
        "IVs are each creature's own strengths, 0 to 31 in each stat, rolled once when it is born. "
        "The web on its card shows them.",
        "Each creature has a nature, which raises one stat a little and lowers another. EVs are the "
        "same for everyone here."]),
    ("The Battle Tower", [
        "At the Tower's door: Begin the challenge for trainer after trainer, healed before each, "
        "until you lose. Your best streak is kept.",
        "Trainer battle for just one trainer. Trainers bring as many creatures as you, each matched "
        "to one of yours, at its level. Every trainer has an ace: their last, and a little stronger."]),
]


def place_words():
    """One line about each place, by its key."""
    return dict(
        glade="Home, in the middle of everything: the blossom tree, the signpost and the lily pond.",
        waterfall="A tall fall into a glowing pool, with a crystal-lit cave mouth in the cliff.",
        river="A slow river, a little boat, and lilyfin under the water.",
        forest="Tall dark trees hung with glowing vines.",
        rocks="Mossy boulders and standing stones; the Battle Tower is further down.",
        ridge="Pines, deep snow, a frozen lake and the aurora overhead.",
        springs="A sleeping volcano above steaming turquoise pools.",
        tower="The Battle Tower: trainer after trainer, and your starter's first home.",
        caverns="A cave full of glowing crystals and a still pool.",
        meadow="Wide grass where stars fall all night.",
        hollow="Giant glowing mushrooms, tall as trees.",
        bog="Misty water, dead trees and drifting lights.",
        ruins="Broken pillars and an old stone arch.",
        bridge="A rope bridge across the clouds, between two cliffs.",
        shore="A beach of glowing sand by a dark sea.",
        falls="A waterfall frozen in mid-fall.",
        peak="Tall stones under the brightest aurora.",
        gully="A deep green gully of ferns.",
        orchard="Fruit trees hung with little lanterns.",
        temple="An old temple, half sunk in the water.",
        dunes="Pale sand dunes under a huge moon.",
        lava="A lake of glowing lava under a dark cliff.",
        grotto="A sea cave with coral trees round a glowing pool.",
        kelp="Under the sea, among tall kelp and light from far above.",
        lighthouse="A striped lighthouse on a headland.",
        comet="A crater where a comet fell; it still glows.",
        garden="A walled garden of moonflowers round a fountain.",
        isles="Little islands floating in the night sky.",
        storm="Jagged peaks under constant lightning.",
        thorn="A dark wood of brambles and berries.",
        hall="The Moonlit Hall, where the Elite 4 wait.",
    )


# --- the book itself -------------------------------------------------------------------------------

class Book:
    CHAPTERS = ["Start here", "Places", "Types", "Battles", "Gyms & Elite 4"]

    def __init__(self, font, t, here=None):
        self.font, self.t = font, t
        self.rect = pygame.Rect(30, 18, 900, 504)
        self.chapter = 0
        self.topic = {c: 0 for c in self.CHAPTERS}
        self.here = here
        if here:  # Places opens on the place you are in
            keys = self.places()
            if here in keys:
                self.topic["Places"] = keys.index(here)
        self.buttons = []
        self.closed = False
        self.go_to = None      # a place to walk to as the book closes (game.after_board)
        self.open_dex = False  # open the Forest Dex as it closes
        self._texts = {}

    # --- what is in each chapter ---
    @staticmethod
    def places():
        from scenes import MAP
        return list(MAP)

    def topics(self, chapter):
        if chapter == "Start here":
            return [t for t, _ in START]
        if chapter == "Places":
            from game import Minimap
            return [Minimap.NAMES.get(k, k) for k in self.places()]
        if chapter == "Types":
            return ["The whole chart"] + TYPES
        if chapter == "Battles":
            return [t for t, _ in BATTLES]
        from gyms import GYMS, TITLES
        return ["How gyms work"] + [TITLES[k] for k in GYMS] + ["The Elite 4"]

    # --- clicks ---
    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    def close(self):
        self.closed = True

    # --- drawing helpers ---
    def text(self, s, words, x, y, color=INK, center=False, right=False):
        key = (words, color)
        img = self._texts.get(key)
        if img is None:
            if len(self._texts) > 3000:
                self._texts.clear()
            img = self._texts[key] = self.font.render(words, False, color)
        if center:
            x -= img.get_width() // 2
        elif right:
            x -= img.get_width()
        s.blit(img, (x, y))
        return img.get_width()

    def wrap(self, words, width):
        lines, line = [], ""
        for w in words.split():
            if line and self.font.size(line + " " + w)[0] > width:
                lines.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        return lines + [line] if line else lines

    def para(self, s, words, x, y, width, color=INK):
        lh = self.font.get_height() + 2
        for line in self.wrap(words, width):
            self.text(s, line, x, y, color)
            y += lh
        return y + 6

    def chip(self, s, kind, x, y, short=False):
        label = kind[:3].upper() if short else kind.upper()
        img = self.font.render(label, False, INK)
        r = pygame.Rect(x, y, img.get_width() + 6, img.get_height() + 1)
        pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), r, border_radius=3)
        s.blit(img, (x + 3, y))
        return r.w + 3

    def chips(self, s, kinds, x, y, width):
        """Type chips in rows; returns the y under them."""
        x0 = x
        h = self.font.get_height() + 4
        for kind in kinds:
            w = self.font.size(kind.upper())[0] + 9
            if x + w > x0 + width:
                x, y = x0, y + h
            x += self.chip(s, kind, x, y)
        return y + h + 4

    def button(self, s, r, label, action, m, color=None):
        hot = bool(m) and r.collidepoint(m)
        c = color or mix(COVER_HI, PAGE, 0.3)
        pygame.draw.rect(s, mix(c, (255, 255, 255), 0.25) if hot else c, r, border_radius=4)
        pygame.draw.rect(s, INK, r, 1, border_radius=4)
        img = self.font.render(label, False, INK)
        s.blit(img, img.get_rect(center=r.center))
        self.buttons.append((r, action))

    # --- the whole book ---
    def draw(self, s, m, t):
        self.buttons = []
        r = self.rect
        k = ease((t - self.t) / 0.2)
        if k < 1:  # it opens out from the spine
            w = max(4, round(r.w * k))
            pygame.draw.rect(s, COVER, (r.centerx - w // 2, r.y, w, r.h), border_radius=8)
            return
        pygame.draw.rect(s, (30, 18, 44), r.move(3, 4), border_radius=10)  # its shadow
        pygame.draw.rect(s, COVER, r, border_radius=10)
        pygame.draw.rect(s, COVER_HI, r, 2, border_radius=10)
        for cx, cy in ((r.x + 8, r.y + 8), (r.right - 9, r.y + 8), (r.x + 8, r.bottom - 9), (r.right - 9, r.bottom - 9)):
            pygame.draw.circle(s, GOLD, (cx, cy), 3)  # gold corners
        left = pygame.Rect(r.x + 16, r.y + 34, r.w // 2 - 18, r.h - 46)
        right = pygame.Rect(r.centerx + 2, left.y, left.w, left.h)
        for page, toward in ((left, 1), (right, -1)):
            pygame.draw.rect(s, PAGE, page, border_radius=3)
            for i in range(10):  # shade by the spine
                x = page.right - 1 - i if toward > 0 else page.x + i
                pygame.draw.line(s, mix(PAGE_SH, PAGE, i / 10), (x, page.y + 1), (x, page.bottom - 2))
        pygame.draw.line(s, (40, 24, 56), (r.centerx, left.y), (r.centerx, left.bottom), 2)
        # the title and the chapter ribbons
        self.text(s, "THE GLADE BOOK", r.x + 20, r.y + 10, (255, 236, 200))
        x = r.x + 150
        for i, name in enumerate(self.CHAPTERS):
            w = self.font.size(name)[0] + 18
            rr = pygame.Rect(x, r.y + 6, w, 22 if i == self.chapter else 18)
            c = RIBBONS[i]
            hot = bool(m) and rr.collidepoint(m)
            pygame.draw.rect(s, c if i == self.chapter or hot else mix(c, COVER, 0.45), rr, border_radius=3)
            if i == self.chapter:
                pygame.draw.polygon(s, c, [(rr.x, rr.bottom - 2), (rr.right, rr.bottom - 2), (rr.centerx, rr.bottom + 4)])
            self.text(s, name, rr.centerx, rr.y + 3, INK, center=True)
            self.buttons.append((rr, self.chooser(i)))
            x += w + 6
        self.button(s, pygame.Rect(r.right - 196, r.y + 7, 110, 18), "Forest Dex", self.to_dex, m,
                    color=(170, 230, 190))
        self.button(s, pygame.Rect(r.right - 80, r.y + 7, 60, 18), "Close", self.close, m)
        name = self.CHAPTERS[self.chapter]
        self.contents(s, left, m, name)
        page = right.inflate(-28, -24)
        if name == "Start here":
            self.words(s, page, START[self.topic[name]])
        elif name == "Battles":
            self.words(s, page, BATTLES[self.topic[name]])
        elif name == "Places":
            self.place(s, page, m, self.places()[self.topic[name]])
        elif name == "Types":
            i = self.topic[name]
            if i == 0:
                self.chart(s, page, m)
            else:
                self.type_page(s, page, TYPES[i - 1])
        else:
            self.gym_page(s, page, m)

    def chooser(self, i):
        def f():
            self.chapter = i
        return f

    def picker(self, chapter, i):
        def f():
            self.topic[chapter] = i
        return f

    def to_dex(self):
        self.open_dex, self.closed = True, True

    def contents(self, s, page, m, chapter):
        """The left page: the chapter's topics, in one or two columns."""
        names = self.topics(chapter)
        lh = self.font.get_height() + 3
        self.text(s, chapter, page.x + 16, page.y + 10, FADED)
        top = page.y + 30
        rows = (page.bottom - 10 - top) // lh
        cols = 1 if len(names) <= rows else 2
        cw = (page.w - 32) // cols
        for i, name in enumerate(names):
            x = page.x + 16 + (i // rows) * cw
            y = top + (i % rows) * lh
            rr = pygame.Rect(x - 4, y - 1, cw - 6, lh)
            on = i == self.topic[chapter]
            hot = bool(m) and rr.collidepoint(m)
            if on:
                pygame.draw.rect(s, mix(RIBBONS[self.chapter], PAGE, 0.35), rr, border_radius=3)
            elif chapter == "Places" and self.places()[i] == self.here:
                pygame.draw.rect(s, mix(GOLD, PAGE, 0.6), rr, border_radius=3)
            label = name
            if chapter == "Types" and i > 0:
                pygame.draw.rect(s, TYPE_COLOR[name], (x, y + 2, 8, lh - 6), border_radius=2)
                label = "   " + name
            self.text(s, label, x + 2, y, HOT if hot and not on else INK)
            self.buttons.append((rr, self.picker(chapter, i)))

    def words(self, s, page, topic):
        title, paras = topic
        self.text(s, title, page.x, page.y, INK)
        pygame.draw.line(s, FADED, (page.x, page.y + 16), (page.x + self.font.size(title)[0], page.y + 16))
        y = page.y + 26
        for p in paras:
            y = self.para(s, p, page.x, y, page.w)

    # --- a place ---
    def place(self, s, page, m, key):
        from game import Minimap
        from gyms import GYMS, TITLES, locals_of
        from scenes import LINKS, MAP, heading
        from team import Collection
        lh = self.font.get_height() + 2
        name = Minimap.NAMES.get(key, key)
        pygame.draw.rect(s, Minimap.COLORS.get(key, (200, 200, 200)), (page.x, page.y + 2, 10, 10), border_radius=2)
        self.text(s, name, page.x + 16, page.y, INK)
        if key == self.here:
            self.text(s, "you are here", page.right, page.y, FADED, right=True)
        y = self.para(s, place_words().get(key, ""), page.x, page.y + 22, page.w)
        self.text(s, "Paths", page.x, y, FADED)
        y += lh
        ways = {(0, -1): "Up", (0, 1): "Down", (-1, 0): "Left", (1, 0): "Right"}
        for a, b in LINKS:
            other = b if a == key else a if b == key else None
            if other:
                self.text(s, f"{ways[heading(key, other)]}: {Minimap.NAMES.get(other, other)}", page.x + 10, y)
                y += lh
        y += 6
        self.text(s, "Lives here", page.x, y, FADED)
        y += lh
        from dex import by_number
        known = set(by_number().values())
        lives = locals_of(key) if key in MAP else []
        if lives:
            line = ", ".join(sp if sp in known else "???" for sp in lives)
            y = self.para(s, line, page.x + 10, y, page.w - 10)
        else:
            y = self.para(s, "Only animals that wander in from elsewhere.", page.x + 10, y, page.w - 10, FADED)
        if key in GYMS:
            leader, types, _, col = GYMS[key]
            won = key in Collection().badges
            self.text(s, TITLES[key], page.x, y, FADED)
            y += lh
            pygame.draw.circle(s, col, (page.x + 15, y + 7), 6)
            pygame.draw.circle(s, INK, (page.x + 15, y + 7), 6, 1)
            x = page.x + 26 + self.text(s, leader, page.x + 26, y) + 8
            for kind in types:
                x += self.chip(s, kind, x, y)
            y += lh + 2
            self.text(s, "Badge won!" if won else "Badge not won yet", page.x + 26, y, HOT if won else FADED)
            y += lh
        if key != self.here:
            self.button(s, pygame.Rect(page.right - 120, page.bottom - 24, 120, 22), "Go there", self.goer(key), m,
                        color=(255, 220, 160))

    def goer(self, key):
        def f():
            self.go_to, self.closed = key, True
        return f

    # --- types ---
    def type_page(self, s, page, kind):
        lh = self.font.get_height() + 2
        self.chip(s, kind, page.x, page.y)
        self.text(s, "physical moves" if kind in PHYSICAL else "special moves", page.right, page.y, FADED, right=True)
        y = page.y + 26
        groups = [
            ("Its moves hit hard against", [d for d in TYPES if CHART[kind].get(d, 1) == 2]),
            ("Its moves are weak against", [d for d in TYPES if CHART[kind].get(d, 1) == 0.5]),
            ("Its moves do nothing to", [d for d in TYPES if CHART[kind].get(d, 1) == 0]),
            ("It is hurt most by", [a for a in TYPES if effectiveness(a, (kind,)) == 2]),
            ("It shrugs off", [a for a in TYPES if effectiveness(a, (kind,)) == 0.5]),
            ("It takes nothing from", [a for a in TYPES if effectiveness(a, (kind,)) == 0]),
        ]
        for title, kinds in groups:
            self.text(s, title, page.x, y, FADED)
            y += lh
            if kinds:
                y = self.chips(s, kinds, page.x + 10, y, page.w - 10)
            else:
                self.text(s, "nothing", page.x + 10, y)
                y += lh + 6
        y += 4
        self.para(s, "A creature with two types takes both into account: hard against both is four times, "
                     "and hard against one but weak against the other cancels out.", page.x, y, page.w, FADED)

    def chart(self, s, page, m):
        """Every attacking type (rows) against every defending type (columns)."""
        n = len(TYPES)
        cell = min(22, (page.w - 40) // n)
        x0, y0 = page.x + 40, page.y + 40
        self.text(s, "Attacking down the side, defending along the top", page.x, page.y, FADED)
        for j, d in enumerate(TYPES):
            pygame.draw.rect(s, TYPE_COLOR[d], (x0 + j * cell + 1, y0 - 14, cell - 2, 12), border_radius=2)
            self.text(s, d[:2], x0 + j * cell + cell // 2, y0 - 14, INK, center=True)
        pointed = None
        for i, a in enumerate(TYPES):
            pygame.draw.rect(s, TYPE_COLOR[a], (page.x, y0 + i * cell + 1, 36, cell - 2), border_radius=2)
            self.text(s, a[:3].upper(), page.x + 18, y0 + i * cell + (cell - 14) // 2, INK, center=True)
            for j, d in enumerate(TYPES):
                v = CHART[a].get(d, 1)
                rr = pygame.Rect(x0 + j * cell, y0 + i * cell, cell - 1, cell - 1)
                c = {2: (140, 220, 140), 0.5: (240, 160, 160), 0: (70, 56, 90)}.get(v, mix(PAGE, PAGE_SH, 0.5))
                pygame.draw.rect(s, c, rr)
                if m and rr.collidepoint(m):
                    pointed = (a, d, v)
                    pygame.draw.rect(s, INK, rr, 1)
        y = y0 + n * cell + 8
        x = page.x
        for c, words in (((140, 220, 140), "hits hard"), ((240, 160, 160), "weak"), ((70, 56, 90), "no effect")):
            pygame.draw.rect(s, c, (x, y + 2, 10, 10))
            x += 16 + self.text(s, words, x + 14, y) + 10
        if pointed:
            a, d, v = pointed
            words = {2: "hits hard against", 0.5: "is weak against", 0: "does nothing to"}.get(v, "is ordinary against")
            self.text(s, f"{a} {words} {d}", page.x, y + 20, HOT)

    # --- gyms and the Elite 4 ---
    def gym_page(self, s, page, m):
        from gyms import GYMS, TITLES, level_for, size_for
        from team import Collection
        lh = self.font.get_height() + 2
        i = self.topic["Gyms & Elite 4"]
        keys = list(GYMS)
        badges = [b for b in Collection().badges if b in GYMS]
        if i == 0:
            n = len(badges) + 1
            y = self.words_at(s, page, "How gyms work", [
                f"There is a gym in every place but the Tower: {len(GYMS)} in all. Click a gym's banner stone "
                "to meet its leader. Each leader brings creatures that live in their place, of their own type.",
                "Take them on in any order. What makes a gym hard is how many you have already beaten: the "
                "first is Lv7 with 3 creatures, and they climb slowly to Lv55 with 6.",
                "Every leader has an ace: their last creature, a little stronger and two levels up.",
                "A badge won shows as a gem in your badge case. Beaten leaders can be fought again for practice."])
            self.text(s, f"Badges won: {len(badges)} of {len(GYMS)}", page.x, y, HOT)
            if n <= len(GYMS):
                self.text(s, f"Your next gym: {size_for(n)} creatures at Lv{level_for(n)}", page.x, y + lh, FADED)
            return
        if i == len(keys) + 1:
            from elite import CHAMP_LEVEL, LEVELS, LINEUPS
            y = self.words_at(s, page, "The Elite 4", [
                "Up the moonlight stair from the Floating Isles is the Moonlit Hall. Its great door opens "
                "once you hold every gym badge.",
                f"Inside, four specialists wait, one after another, at Lv{LEVELS[0]} to Lv{LEVELS[-1]}, and then "
                f"the champion at Lv{CHAMP_LEVEL}. Your team is healed before each battle; a loss ends it.",
                "There are four line-ups, and which one is in the hall is chosen each time. Who the champion "
                "is, you find out when you get there."])
            for name, members in LINEUPS.items():
                self.text(s, name, page.x, y, INK)
                y += lh
                x = page.x + 10
                for kind in [m_[1][0] for m_ in members]:
                    x += self.chip(s, kind, x, y)
                y += lh + 4
            return
        key = keys[i - 1]
        leader, types, _, col = GYMS[key]
        from game import Minimap
        pygame.draw.circle(s, col, (page.x + 7, page.y + 8), 7)
        pygame.draw.circle(s, INK, (page.x + 7, page.y + 8), 7, 1)
        self.text(s, TITLES[key], page.x + 20, page.y, INK)
        y = page.y + 26
        self.text(s, leader, page.x, y)
        y += lh
        x = page.x
        for kind in types:
            x += self.chip(s, kind, x, y)
        y += lh + 8
        self.text(s, f"In {Minimap.NAMES.get(key, key)}", page.x, y, FADED)
        y += lh + 6
        if key in badges:
            self.text(s, f"Badge won (your gym number {badges.index(key) + 1}).", page.x, y, HOT)
        else:
            n = len(badges) + 1
            self.text(s, f"Not beaten yet. Now it would be {size_for(n)} creatures at Lv{level_for(n)},", page.x, y)
            self.text(s, f"their ace at Lv{level_for(n) + 2}.", page.x, y + lh)
        self.button(s, pygame.Rect(page.right - 120, page.bottom - 24, 120, 22), "Go there", self.goer(key), m,
                    color=(255, 220, 160))

    def words_at(self, s, page, title, paras):
        self.words(s, page, (title, paras))
        y = page.y + 26
        for p in paras:
            y += (self.font.get_height() + 2) * len(self.wrap(p, page.w)) + 6
        return y + 4


# --- the icon by the minimap -----------------------------------------------------------------------

def icon_rect(view, minimap_rect):
    """Just left of the minimap, its bottom level with the minimap's."""
    r = pygame.Rect(0, 0, 46, 50)
    r.bottomright = (minimap_rect.x - 6, minimap_rect.bottom)
    return r


def draw_icon(s, view, font, minimap_rect, m, t):
    from main import EDGE, HOT as LIT, TEXT, WOOD, WOOD_HI, WOOD_LO
    r = icon_rect(view, minimap_rect)
    hot = bool(m) and r.collidepoint(m)
    pygame.draw.rect(s, LIT if hot else EDGE, r.inflate(2, 2), border_radius=3)
    pygame.draw.rect(s, WOOD, r, border_radius=2)
    pygame.draw.line(s, WOOD_HI, (r.x + 2, r.y), (r.right - 3, r.y))
    pygame.draw.line(s, WOOD_LO, (r.x + 2, r.bottom - 1), (r.right - 3, r.bottom - 1))
    # a closed book: violet cover, gold corners, pale page edges, and a little glowing gem on it
    b = pygame.Rect(r.centerx - 11, r.y + 6, 22, 26)
    pygame.draw.rect(s, (236, 230, 246), b.move(2, 1), border_radius=2)   # pages
    pygame.draw.rect(s, COVER, b, border_radius=2)
    pygame.draw.rect(s, COVER_HI, b, 1, border_radius=2)
    pygame.draw.line(s, (40, 24, 56), (b.x + 3, b.y + 1), (b.x + 3, b.bottom - 2))
    for cx, cy in ((b.right - 2, b.y + 1), (b.right - 2, b.bottom - 2)):
        s.set_at((cx, cy), GOLD)
    k = 0.5 + 0.5 * math.sin(t * 2)
    gem = mix((150, 255, 200), (255, 255, 255), k * 0.4)
    pygame.draw.circle(s, gem, (b.centerx + 1, b.centery), 3)
    label = font.render("Book", False, LIT if hot else TEXT)
    s.blit(label, (r.centerx - label.get_width() // 2, r.bottom - label.get_height() - 2))
