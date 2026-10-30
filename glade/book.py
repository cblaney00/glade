"""The Glade Book: the game's encyclopedia (2026-10-30, his ask: "an encyclopedia for this game
that can be opened in an icon in the bottom right corner of the bottom screen").

A little book on a wooden plaque beside the minimap (`icon_rect`, drawn by `draw_icon`) opens
it over the top screen, like the Forest Dex. It is an open book: chapter ribbons along the top,
the chapter's topics down the left page, the chosen topic on the right page.

Chapters: Start here (how to play), Places (a picture of every place, what it is like, the ways
out, who lives there, its gym and trainer, and "Go there"), Types (each type's strengths and
weaknesses with some of its creatures, and the whole chart), Battles (the rules), Gyms & the Elite 4
(each leader, their story and their team as it stands for you now), and Trainers (every trainer's
figure, story and team). His ask (2026-10-30): pictures and a bit more writing. Pointing at a
picture names it. The words are in book_words.py. Creatures are the Forest Dex's job, so its
button opens the Dex.
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
RIBBONS = [(255, 150, 200), (140, 210, 255), (170, 230, 140), (255, 190, 120), (200, 170, 255),
           (150, 222, 196)]

TYPES = list(CHART)

# --- pictures ------------------------------------------------------------------------------------

_pics = {}
_thumbs = {}


def pic(species, size):
    """A creature's Dex picture scaled to `size` wide, framed (kept once made)."""
    key = (species, size)
    if key not in _pics:
        from dex import PH, PW, picture
        full = picture(species)
        # zoom in on the creature: the part that isn't the plain background, in the tile's shape
        bg = full.get_at((0, 0))
        mask = pygame.mask.from_threshold(full, bg, (14, 14, 14, 255))
        mask.invert()
        boxes = mask.get_bounding_rects()
        area = boxes[0].unionall(boxes[1:]) if boxes else full.get_rect()
        area = area.inflate(8, 8)
        w = max(area.w, round(area.h * PW / PH), 24)
        area = pygame.Rect(0, 0, w, round(w * PH / PW))
        area.center = boxes[0].unionall(boxes[1:]).center if boxes else full.get_rect().center
        crop = pygame.Surface(area.size)
        crop.fill(bg)
        crop.blit(full, (0, 0), area)
        h = round(size * PH / PW)
        s = pygame.Surface((size + 2, h + 2))
        s.fill(INK)
        s.blit(pygame.transform.smoothscale(crop, (size, h)), (1, 1))
        _pics[key] = s
    return _pics[key]


def figure(key, scale):
    """A trainer's figure (trainers.Trainer), drawn `scale` times as big, standing still."""
    from trainers import Trainer
    small = pygame.Surface((48, 72), pygame.SRCALPHA)
    fig = Trainer(key, 22, 64)
    fig.draw(small, 2.0)
    fig.shine(small, 2.0)
    return pygame.transform.scale(small, (48 * scale, 72 * scale))


def thumb(scene, w, h):
    """A picture of a place (its top screen), drawn once and kept."""
    if scene.key not in _thumbs:
        from art import solid
        full = solid()
        scene.draw(full, 5.0)
        _thumbs[scene.key] = pygame.transform.smoothscale(full, (w, h))
    return _thumbs[scene.key]


# --- the book itself -------------------------------------------------------------------------------

class Book:
    CHAPTERS = ["Start here", "Places", "Types", "Battles", "Gyms & Elite 4", "Trainers"]

    def __init__(self, font, t, here=None, scenes=None):
        self.font, self.t = font, t
        self.rect = pygame.Rect(30, 18, 900, 504)
        self.chapter = 0
        self.topic = {c: 0 for c in self.CHAPTERS}
        self.here = here
        self.scenes = scenes if scenes is not None else {}  # the places built so far (for their pictures)
        for chapter in ("Places", "Trainers"):  # these open on the place you are in
            keys = self.places() if chapter == "Places" else self.trainer_keys()
            if here in keys:
                self.topic[chapter] = keys.index(here)
        self.buttons = []
        self.closed = False
        self.go_to = None      # a place to walk to as the book closes (game.after_board)
        self.open_dex = False  # open the Forest Dex as it closes
        self.named = None      # what the pointer is on, written under the picture rows
        self._texts = {}

    # --- what is in each chapter ---
    @staticmethod
    def places():
        from scenes import MAP
        return list(MAP)

    @staticmethod
    def trainer_keys():
        from trainers import TRAINERS
        return list(TRAINERS)

    def topics(self, chapter):
        from book_words import BATTLES, START
        if chapter == "Start here":
            return [t for t, *_ in START]
        if chapter == "Places":
            from game import Minimap
            return [Minimap.NAMES.get(k, k) for k in self.places()]
        if chapter == "Types":
            return ["The whole chart"] + TYPES
        if chapter == "Battles":
            return [t for t, *_ in BATTLES]
        if chapter == "Trainers":
            from trainers import TRAINERS
            return [TRAINERS[k][0] for k in self.trainer_keys()]
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

    def row(self, s, things, x, y, width, m, size=44, levels=None):
        """A row of pictures (species, or "trainer:<place>"), wrapping; pointing at one names it.
        Returns the y under them."""
        gap = 6
        x0, h = x, 0
        for i, thing in enumerate(things):
            if thing.startswith("trainer:"):
                img = figure(thing.split(":")[1], 1)
                from trainers import TRAINERS
                name = TRAINERS[thing.split(":")[1]][0]
            else:
                img = pic(thing, size)
                name = thing
            if x + img.get_width() > x0 + width:
                x, y, h = x0, y + h + gap + (12 if levels else 0), 0
            s.blit(img, (x, y))
            if levels:
                self.text(s, f"Lv{levels[i]}", x + img.get_width() // 2, y + img.get_height() + 1, FADED, center=True)
            r = pygame.Rect(x, y, img.get_width(), img.get_height())
            if m and r.collidepoint(m):
                self.named = name
                pygame.draw.rect(s, HOT, r.inflate(2, 2), 1)
            h = max(h, img.get_height())
            x += img.get_width() + gap
        return y + h + gap + (12 if levels else 0)

    def caption(self, s, page):
        """The name of whatever picture the pointer is on, at the foot of the page."""
        if self.named:
            self.text(s, self.named, page.x, page.bottom - 14, HOT)

    # --- the whole book ---
    def draw(self, s, m, t):
        self.buttons = []
        self.named = None
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
        x = r.x + 140
        for i, name in enumerate(self.CHAPTERS):
            w = self.font.size(name)[0] + 14
            rr = pygame.Rect(x, r.y + 6, w, 22 if i == self.chapter else 18)
            c = RIBBONS[i]
            hot = bool(m) and rr.collidepoint(m)
            pygame.draw.rect(s, c if i == self.chapter or hot else mix(c, COVER, 0.45), rr, border_radius=3)
            if i == self.chapter:
                pygame.draw.polygon(s, c, [(rr.x, rr.bottom - 2), (rr.right, rr.bottom - 2), (rr.centerx, rr.bottom + 4)])
            self.text(s, name, rr.centerx, rr.y + 3, INK, center=True)
            self.buttons.append((rr, self.chooser(i)))
            x += w + 5
        self.button(s, pygame.Rect(r.right - 168, r.y + 7, 90, 18), "Forest Dex", self.to_dex, m,
                    color=(170, 230, 190))
        self.button(s, pygame.Rect(r.right - 72, r.y + 7, 56, 18), "Close", self.close, m)
        name = self.CHAPTERS[self.chapter]
        self.contents(s, left, m, name)
        page = right.inflate(-28, -24)
        from book_words import BATTLES, START
        if name == "Start here":
            self.words(s, page, m, START[self.topic[name]])
        elif name == "Battles":
            self.words(s, page, m, BATTLES[self.topic[name]])
        elif name == "Places":
            self.place(s, page, m, self.places()[self.topic[name]])
        elif name == "Types":
            i = self.topic[name]
            if i == 0:
                self.chart(s, page, m)
            else:
                self.type_page(s, page, m, TYPES[i - 1])
        elif name == "Trainers":
            self.trainer_page(s, page, m, self.trainer_keys()[self.topic[name]])
        else:
            self.gym_page(s, page, m)
        self.caption(s, page)

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

    def goer(self, key):
        def f():
            self.go_to, self.closed = key, True
        return f

    def go_button(self, s, page, m, key):
        if key != self.here:
            self.button(s, pygame.Rect(page.right - 96, page.y - 2, 96, 18), "Go there", self.goer(key), m,
                        color=(255, 220, 160))
        else:
            self.text(s, "you are here", page.right, page.y, FADED, right=True)

    def contents(self, s, page, m, chapter):
        """The left page: the chapter's topics, in one or two columns."""
        names = self.topics(chapter)
        lh = self.font.get_height() + 3
        self.text(s, chapter, page.x + 16, page.y + 10, FADED)
        top = page.y + 30
        rows = (page.bottom - 10 - top) // lh
        cols = 1 if len(names) <= rows else 2
        cw = (page.w - 32) // cols
        keys = self.places() if chapter == "Places" else self.trainer_keys() if chapter == "Trainers" else []
        for i, name in enumerate(names):
            x = page.x + 16 + (i // rows) * cw
            y = top + (i % rows) * lh
            rr = pygame.Rect(x - 4, y - 1, cw - 6, lh)
            on = i == self.topic[chapter]
            hot = bool(m) and rr.collidepoint(m)
            if on:
                pygame.draw.rect(s, mix(RIBBONS[self.chapter], PAGE, 0.35), rr, border_radius=3)
            elif keys and keys[i] == self.here:
                pygame.draw.rect(s, mix(GOLD, PAGE, 0.6), rr, border_radius=3)
            label = name
            if chapter == "Types" and i > 0:
                pygame.draw.rect(s, TYPE_COLOR[name], (x, y + 2, 8, lh - 6), border_radius=2)
                label = "   " + name
            if chapter == "Trainers":
                from trainers import ready
                if ready(keys[i]):
                    pygame.draw.circle(s, GOLD, (x + cw - 16, y + lh // 2 - 1), 3)
            self.text(s, label, x + 2, y, HOT if hot and not on else INK)
            self.buttons.append((rr, self.picker(chapter, i)))

    def words(self, s, page, m, topic):
        title, paras, pics = topic
        self.text(s, title, page.x, page.y, INK)
        pygame.draw.line(s, FADED, (page.x, page.y + 16), (page.x + self.font.size(title)[0], page.y + 16))
        y = page.y + 26
        for p in paras:
            y = self.para(s, p, page.x, y, page.w)
        if pics:
            self.row(s, pics, page.x, y + 4, page.w, m, size=96)

    # --- a place ---
    def place(self, s, page, m, key):
        from book_words import PLACES
        from game import Minimap
        from gyms import GYMS, locals_of
        from scenes import LINKS, MAP, heading
        from team import Collection
        lh = self.font.get_height() + 2
        name = Minimap.NAMES.get(key, key)
        pygame.draw.rect(s, Minimap.COLORS.get(key, (200, 200, 200)), (page.x, page.y + 2, 10, 10), border_radius=2)
        self.text(s, name, page.x + 16, page.y, INK)
        self.go_button(s, page, m, key)
        # its picture, once it has been built (Wander builds every place, nearest first)
        tw, th = page.w, page.w * 9 // 16
        box = pygame.Rect(page.x, page.y + 22, tw, th)
        sc = self.scenes.get(key)
        if sc is not None:
            s.blit(thumb(sc, tw, th), box)
        else:
            pygame.draw.rect(s, PAGE_SH, box)
            self.text(s, "(its picture comes once the place has loaded)", box.centerx, box.centery - 6, FADED,
                      center=True)
        pygame.draw.rect(s, INK, box.inflate(2, 2), 1)
        y = self.para(s, PLACES.get(key, ""), page.x, box.bottom + 8, page.w)
        ways = {(0, -1): "up", (0, 1): "down", (-1, 0): "left", (1, 0): "right"}
        paths = [f"{Minimap.NAMES.get(o, o)} ({ways[heading(key, o)]})" for a, b in LINKS
                 for o in ((b,) if a == key else (a,) if b == key else ())]
        y = self.para(s, "Paths: " + ", ".join(paths), page.x, y - 2, page.w, FADED)
        lives = locals_of(key) if key in MAP else []
        if lives:
            size = min(48, (page.w - 6 * len(lives)) // len(lives) - 2)  # all on one line
            y = self.row(s, lives, page.x, y, page.w, m, size=size)
        notes = []
        if key in GYMS:
            leader, types, _, _ = GYMS[key]
            notes.append(f"Gym: {leader} ({' and '.join(types)})" + (", badge won" if key in Collection().badges else ""))
        from trainers import TRAINERS, ready
        if key in TRAINERS:
            notes.append(f"Trainer: {TRAINERS[key][0]}" + (", wants to battle" if ready(key) else ""))
        for n in notes:
            self.text(s, n, page.x, y, INK)
            y += lh

    # --- types ---
    def type_page(self, s, page, m, kind):
        from battle import SPECIES, LEGENDARY
        from book_words import TYPES as WORDS
        from evolve import stage_of
        lh = self.font.get_height() + 2
        self.chip(s, kind, page.x, page.y)
        self.text(s, "physical moves" if kind in PHYSICAL else "special moves", page.right, page.y, FADED, right=True)
        y = self.para(s, WORDS.get(kind, ""), page.x, page.y + 22, page.w)
        groups = [
            ("Hits hard against", [d for d in TYPES if CHART[kind].get(d, 1) == 2]),
            ("Weak against", [d for d in TYPES if CHART[kind].get(d, 1) == 0.5]),
            ("Does nothing to", [d for d in TYPES if CHART[kind].get(d, 1) == 0]),
            ("Hurt most by", [a for a in TYPES if effectiveness(a, (kind,)) == 2]),
            ("Shrugs off", [a for a in TYPES if effectiveness(a, (kind,)) == 0.5]),
            ("Takes nothing from", [a for a in TYPES if effectiveness(a, (kind,)) == 0]),
        ]
        for title, kinds in groups:
            if not kinds:
                continue
            self.text(s, title, page.x, y, FADED)
            y = self.chips(s, kinds, page.x + 130, y, page.w - 130) - 2
        y += 4
        self.text(s, f"Some {kind} creatures", page.x, y, FADED)
        firsts = sorted((sp for sp, d in SPECIES.items() if kind in d["types"] and sp not in LEGENDARY
                         and stage_of(sp)[1] == 1), key=lambda sp: SPECIES[sp]["num"])
        self.row(s, firsts[:14], page.x, y + lh + 2, page.w, m, size=44)

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
        from book_words import LEADERS
        from gyms import GYMS, TITLES, leader_team, level_for, size_for
        from team import Collection
        lh = self.font.get_height() + 2
        i = self.topic["Gyms & Elite 4"]
        keys = list(GYMS)
        badges = [b for b in Collection().badges if b in GYMS]
        if i == 0:
            n = len(badges) + 1
            y = self.words_at(s, page, "How gyms work", [
                f"There is a gym in every place but the Tower: {len(GYMS)} in all. Click a gym's banner stone "
                "to meet its leader. Each leader trains creatures that live in their place, of their own type.",
                "Take them on in any order. What makes a gym hard is how many you have already beaten: the "
                "first is Lv7 with 3 creatures, and they climb slowly to Lv55 with 6.",
                "Every leader keeps their own creatures. The more badges you have, the more of them they bring, "
                "and the further they have evolved. Their ace is always last, two levels up.",
                "A badge won shows as a gem in your badge case. Beaten leaders can be fought again for practice."])
            self.text(s, f"Badges won: {len(badges)} of {len(GYMS)}", page.x, y, HOT)
            if n <= len(GYMS):
                self.text(s, f"Your next gym: {size_for(n)} creatures at Lv{level_for(n)}", page.x, y + lh, FADED)
            return
        if i == len(keys) + 1:
            from elite import LINEUPS, levels
            lvls, champ = levels()
            y = self.words_at(s, page, "The Elite 4", [
                "Up the moonlight stair from the Floating Isles is the Moonlit Hall. Its great door opens "
                "once you hold every gym badge.",
                f"Inside, four specialists wait, one after another, at Lv{lvls[0]} to Lv{lvls[-1]}, and then "
                f"the champion at Lv{champ}. Your team is healed before each battle; a loss ends it.",
                "There are four line-ups, and which one is in the hall is chosen each time. Every member keeps "
                "their own six. Each time you become champion, they all come back three levels stronger."])
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
        pygame.draw.circle(s, col, (page.x + 7, page.y + 8), 7)
        pygame.draw.circle(s, INK, (page.x + 7, page.y + 8), 7, 1)
        self.text(s, TITLES[key], page.x + 20, page.y, INK)
        self.go_button(s, page, m, key)
        y = page.y + 24
        x = page.x + self.text(s, leader, page.x, y) + 8
        for kind in types:
            x += self.chip(s, kind, x, y)
        y = self.para(s, LEADERS.get(key, ""), page.x, y + lh + 6, page.w)
        if key in badges:
            n = badges.index(key) + 1
            self.text(s, f"Badge won (your gym number {n}). A rematch is at that level:", page.x, y, HOT)
        else:
            n = len(badges) + 1
            self.text(s, f"Not beaten yet. Their team for you now, Lv{level_for(n)}:", page.x, y)
        team = leader_team(key, n)
        self.row(s, [t_[0] for t_ in team], page.x, y + lh + 4, page.w, m, size=58, levels=[t_[4] for t_ in team])
        self.text(s, "Their ace is last.", page.x, page.bottom - 30, FADED)

    def words_at(self, s, page, title, paras):
        self.words(s, page, None, (title, paras, []))
        y = page.y + 26
        for p in paras:
            y += (self.font.get_height() + 2) * len(self.wrap(p, page.w)) + 6
        return y + 4

    # --- the trainers in every place ---
    def trainer_page(self, s, page, m, key):
        from book_words import TRAINERS as STORIES
        from trainers import TRAINERS, ready, team, where, wins
        lh = self.font.get_height() + 2
        name = TRAINERS[key][0]
        self.text(s, name, page.x, page.y, INK)
        self.go_button(s, page, m, key)
        s.blit(figure(key, 3), (page.x - 10, page.y + 10))
        x = page.x + 140
        y = page.y + 30
        self.text(s, f"Of {where(key)}", x, y, FADED)
        y = self.para(s, STORIES.get(key, ""), x, y + lh + 4, page.w - 140)
        n = wins(key)
        self.text(s, f"Beaten {n} time{'s' if n != 1 else ''}" if n else "Not beaten yet", x, y, INK)
        y += lh
        self.text(s, "Wants to battle!" if ready(key) else "Beaten today: a rematch tomorrow", x, y,
                  HOT if ready(key) else FADED)
        y = max(y + lh + 10, page.y + 230)
        self.text(s, "Their creatures, as they are now:", page.x, y, FADED)
        fielded = team(key)
        self.row(s, [t_[0] for t_ in fielded], page.x, y + lh + 4, page.w, m, size=58, levels=[t_[4] for t_ in fielded])
        self.para(s, "Always the same lines: they evolve, and one more joins at each rematch.", page.x,
                  page.bottom - 44, page.w, FADED)


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
