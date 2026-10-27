"""The Forest Dex — like a Pokédex, for the glade's animals.

Opened from an animal's right-click stats card ("Open in Forest Dex"), at that animal.
It has room for 260 animals. Each animal here is the first of three evolutions, so its
line takes three numbers in a row (SPECIES[...]["num"] in battle.py): the later two are
"?" until they are made. Two tabs: the Dex (every slot, in pages) and Compare (every
animal found so far in one table, sorted by whichever stat you click). The panel on the
right shows the chosen one in full, with a living picture of it.
"""

import math
import random

import pygame

import art
from apex import ease
from art import GLOW, glow
from battle import CLOTH, DIM, EDGE, MOVES, SPECIES, TEXT, TYPE_COLOR, cloth, mix, stat_color
from beasts import FLIERS, WALKERS, Flier, Walker, owlet
from life import Critter, Millipede, Slug, Squid, Track
from pond import KOI, Fish, Water

TOTAL = 260
PER_PAGE = 48          # 8 x 6 slots
STATS = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")
LONG = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")
WHITE = (255, 255, 255)
MINT = (110, 255, 180)


# --- pictures --------------------------------------------------------------------------

PW, PH = 72, 52            # a picture, in canvas pixels (shown at 2x in the entry)
NIGHT = (22, 16, 42)


def specimen(species):
    """One of the species made just to be drawn here, standing in the middle of a picture.
    Trees' dwellers come back as ("perch", kind)."""
    from evolve import EVOLVED_FROM, set_stage, stage_of
    if species in EVOLVED_FROM:  # an evolved one: its first stage, grown
        first, n = stage_of(species)
        thing = specimen(first)
        if isinstance(thing, tuple):  # a tree dweller: (perch, kind, stage)
            return thing[:2] + (n,)
        if first == "Luminpede":  # the long ones lie coiled up, so all of them fits in
            rng = random.Random(7)
            cx, cy = PW // 2, PH - 26
            spiral = [(cx + math.cos(a / 6) * (3 + a * 0.45), cy + math.sin(a / 6) * (2 + a * 0.28)) for a in range(60, -1, -1)]
            thing = Millipede(rng, Track(spiral), (150, 110, 184), GLOW["cyan"], n=14, speed=0)
            set_stage(thing, n)
            thing.dir, thing.d = 1, thing.track.length - 3
            return thing
        set_stage(thing, n)
        if hasattr(thing, "size"):  # pictures (and the battle field) have room for only so much:
            from evolve import growth  # a big one is drawn smaller there (its height is written by it)
            g = growth(species)
            thing.size *= min(1.0, (1.25 if n == 2 else 1.15) / g)
        return thing
    rng = random.Random(7)
    cx, cy = PW // 2, PH - 12
    if species == "Duskling":
        return Critter(rng, lambda x: cy + 8, (cx + 18, cx + 18))
    if species == "Driftlet":
        return Squid(rng, (cx, cy - 12, 0, 0), GLOW["cyan"], size=1.1)
    if species in ("Gloamooze", "Cairncurl"):
        snail = species == "Cairncurl"
        o = Slug(rng, Track([(2, cy + 4), (PW - 2, cy + 4)]), (220, 196, 180) if snail else (214, 170, 222),
                 size=1.3, speed=0, shell=(226, 170, 140) if snail else None)
        o.dir, o.d = 1, o.track.length * 0.78
        return o
    if species == "Luminpede":
        o = Millipede(rng, Track([(-10, cy + 4), (PW - 4, cy + 4)]), (150, 110, 184), GLOW["cyan"], n=14, speed=0)
        o.dir, o.d = 1, o.track.length - 6
        return o
    if species == "Lilyfin":
        f = Fish(rng, Water(cx, cy, 20, 8), KOI[1], (78, 138, 228))
        f.pts = [[cx + 16 - i * Fish.SEG * 0.8, cy - 6 + (i % 2) * 0.5] for i in range(7)]
        return f
    if species in ("Canopod", "Moonhoot"):
        return ("perch", "owlet" if species == "Moonhoot" else "squid")
    for kind, spec in FLIERS.items():
        if spec["species"] == species:
            return Flier(rng, (cx, cy - 14, 0, 0), kind, 1.4)
    for kind, spec in WALKERS.items():
        if spec["species"] == species:
            return Walker(rng, lambda x: cy + 6, (cx, cx), kind, 1.4)
    return None


def paint(pic, thing, t):
    """Draw `thing` (a specimen) onto the picture `pic` at time t."""
    pic.fill(NIGHT)
    glow(pic, PW // 2, PH - 8, 30, (90, 200, 150), 36)
    pygame.draw.ellipse(pic, (34, 58, 62), (PW // 2 - 26, PH - 12, 52, 10))  # a mossy mound to stand on
    pygame.draw.ellipse(pic, (54, 96, 92), (PW // 2 - 22, PH - 12, 44, 5))
    if thing is None:
        return
    if isinstance(thing, tuple):  # a tree's dweller on a bit of trunk, holding an icon
        x, y = PW // 2, PH - 26
        pygame.draw.rect(pic, (96, 70, 110), (x - 7, 0, 14, PH))
        pygame.draw.rect(pic, (120, 92, 136), (x - 7, 0, 3, PH))
        pad = pygame.Rect(0, 0, 13, 13)
        pad.center = (x, y + 15)
        pygame.draw.rect(pic, mix(GLOW["violet"], EDGE, 0.5), pad, border_radius=3)
        pygame.draw.rect(pic, mix(GLOW["violet"], (255, 255, 255), 0.4), pad, 1, border_radius=3)
        if thing[1] == "owlet":
            owlet(pic, x, y, 0.8, GLOW["violet"], t, 1.0, None, -10)
        else:
            from squids import TreeSquid
            sq = TreeSquid({"kind": "app", "id": "dex"}, x, y + (4 if len(thing) > 2 else 0), 0.8 if len(thing) < 3 else 0.7)
            sq.stage = thing[2] if len(thing) > 2 else 1
            sq.shine(pic, t, 14)
        return
    if isinstance(thing, Squid):  # keep it from swimming out of the picture
        thing.x += (PW // 2 - thing.x) * 0.2
        thing.y += (PH // 2 - 4 - thing.y) * 0.2
    for part in ("draw", "shine"):
        fn = getattr(thing, part, None)
        if fn:
            fn(pic, t)


_still = {}


def picture(species):
    """A still picture of a species, made once."""
    if species not in _still:
        pic = art.solid((PW, PH))
        thing = specimen(species)
        for i in range(12):  # let it settle into a natural pose first
            paint(pic, thing, 1.0 + i * 0.1)
        _still[species] = pic
    return _still[species]


def by_number():
    return {sp["num"]: name for name, sp in SPECIES.items()}


class Dex:
    def __init__(self, font, species, t):
        self.font, self.t = font, t
        self.rect = pygame.Rect(30, 18, 900, 504)
        self.known = by_number()
        self.pick = SPECIES[species]["num"] if species in SPECIES else 1
        self.page = (self.pick - 1) // PER_PAGE
        self.tab = "dex"
        self.sort, self.desc = "No.", False
        self.buttons = []  # (rect, action), rebuilt every frame
        self.closed = False
        self.live = None  # (species, specimen, picture): the one shown in the entry, moving
        self.now = t

    def open_boxes(self):
        """Your creature boxes (storage.py) instead: the glade opens them as the dex closes."""
        self.boxes, self.closed = True, True

    # --- clicks ---
    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return

    # --- drawing helpers ---
    def text(self, s, words, x, y, color=TEXT, right=False, center=False):
        img = self.font.render(words, False, color)
        if right:
            x -= img.get_width()
        elif center:
            x -= img.get_width() // 2
        s.blit(img, (x, y))
        return img.get_width()

    def badge(self, s, kind, x, y, short=False):
        label = kind[:3].upper() if short else kind.upper()
        img = self.font.render(label, False, EDGE)
        r = pygame.Rect(x, y, img.get_width() + 6, img.get_height() + 1)
        pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), r, border_radius=3)
        s.blit(img, (x + 3, y))
        return r.w + 3

    def button(self, s, r, label, action, m, on=False):
        hot = r.collidepoint(m) if m else False
        cloth(s, r, MINT if hot or on else mix(CLOTH, EDGE, 0.2), hot=hot or on, alpha=215)
        img = self.font.render(label, False, WHITE if hot or on else TEXT)
        s.blit(img, img.get_rect(center=r.center))
        self.buttons.append((r, action))

    def choose(self, num):
        def f():
            self.pick = num
        return f

    # --- the whole board ---
    def draw(self, s, m, t):
        self.buttons = []
        self.now = t
        r = self.rect
        k = ease((t - self.t) / 0.2)
        cloth(s, r, CLOTH, alpha=round(248 * k))
        if k < 1:
            return
        self.text(s, "FOREST DEX", r.x + 14, r.y + 10, WHITE)
        self.text(s, f"Found {len(self.known)} of {TOTAL}", r.x + 104, r.y + 10, DIM)
        self.button(s, pygame.Rect(r.x + 250, r.y + 7, 60, 18), "Dex", lambda: setattr(self, "tab", "dex"), m,
                    on=self.tab == "dex")
        self.button(s, pygame.Rect(r.x + 314, r.y + 7, 76, 18), "Compare", lambda: setattr(self, "tab", "compare"),
                    m, on=self.tab == "compare")
        self.button(s, pygame.Rect(r.x + 394, r.y + 7, 112, 18), "Your creatures", self.open_boxes, m)
        self.button(s, pygame.Rect(r.right - 66, r.y + 7, 56, 18), "Close", lambda: setattr(self, "closed", True), m)
        left = pygame.Rect(r.x + 10, r.y + 34, 540, r.h - 44)
        right = pygame.Rect(left.right + 10, left.y, r.right - left.right - 20, left.h)
        if self.tab == "dex":
            self.grid(s, left, m)
        else:
            self.table(s, left, m)
        self.entry(s, right)

    def grid(self, s, area, m):
        cols, rows = 8, 6
        cw, ch = area.w // cols, (area.h - 26) // rows
        first = self.page * PER_PAGE + 1
        for i in range(PER_PAGE):
            num = first + i
            if num > TOTAL:
                break
            cell = pygame.Rect(area.x + (i % cols) * cw, area.y + (i // cols) * ch, cw - 3, ch - 3)
            name = self.known.get(num)
            hot = cell.collidepoint(m) if m else False
            on = num == self.pick
            tint = TYPE_COLOR[SPECIES[name]["types"][0]] if name else mix(CLOTH, EDGE, 0.45)
            cloth(s, cell, tint if name else mix(CLOTH, EDGE, 0.3), hot=hot or on, alpha=200 if name else 150)
            if name:
                pic = picture(name)
                w = cell.w - 12
                h = round(PH * w / PW)
                s.blit(pygame.transform.scale(pic, (w, h)), (cell.x + 6, cell.y + 3))
            self.text(s, f"#{num:03}", cell.x + 4, cell.y + 3, WHITE if on else DIM)
            if name:
                words = name.split()  # "Tree Squid" goes on two lines
                lines = [name] if self.font.size(name)[0] <= cell.w - 4 else words  # long names: two lines
                for j, line in enumerate(lines):
                    self.text(s, line, cell.centerx, cell.bottom - 14 - 12 * (len(lines) - 1 - j),
                              WHITE if hot or on else TEXT, center=True)
            else:
                self.text(s, "?", cell.centerx, cell.centery - 4, DIM, center=True)
            self.buttons.append((cell, self.choose(num)))
        pages = (TOTAL + PER_PAGE - 1) // PER_PAGE
        y = area.bottom - 20
        if self.page > 0:
            self.button(s, pygame.Rect(area.x, y, 70, 18), "< Prev", lambda: setattr(self, "page", self.page - 1), m)
        if self.page < pages - 1:
            self.button(s, pygame.Rect(area.right - 70, y, 70, 18), "Next >",
                        lambda: setattr(self, "page", self.page + 1), m)
        last = min(TOTAL, first + PER_PAGE - 1)
        self.text(s, f"Page {self.page + 1} of {pages}   #{first:03}-#{last:03}", area.centerx, y + 3, DIM,
                  center=True)

    def table(self, s, area, m):
        cols = [("No.", 0, 34), ("Name", 1, 84), ("Types", 2, 84)] + \
               [(st, 3 + i, 42) for i, st in enumerate(STATS)] + [("Total", 9, 56)]
        rows = []
        for num, name in self.known.items():
            sp = SPECIES[name]
            rows.append((num, name, sp["types"], *sp["base"], sum(sp["base"])))
        col = next(i for label, i, _ in cols if label == self.sort)
        rows.sort(key=lambda row: row[col] if col != 2 else row[2][0], reverse=self.desc)
        x = area.x
        for label, i, w in cols:  # the header: click a column to sort by it (again: flip)
            hr = pygame.Rect(x, area.y, w - 2, 18)
            on = label == self.sort
            hot = hr.collidepoint(m) if m else False
            arrow = (" v" if self.desc else " ^") if on else ""
            self.text(s, label + arrow, hr.x + 2, hr.y + 3, WHITE if on or hot else DIM)

            def sort(label=label):
                if self.sort == label:
                    self.desc = not self.desc
                else:  # stats start highest-first, the rest A-Z / lowest-first
                    self.sort, self.desc = label, label in STATS or label == "Total"
            self.buttons.append((hr, sort))
            x += w
        pygame.draw.line(s, mix(CLOTH, EDGE, 0.3), (area.x, area.y + 20), (area.right, area.y + 20))
        for n, row in enumerate(rows):
            y = area.y + 24 + n * 20
            rr = pygame.Rect(area.x, y - 2, area.w, 19)
            hot = rr.collidepoint(m) if m else False
            if row[0] == self.pick or hot:
                cloth(s, rr, MINT if row[0] == self.pick else CLOTH, alpha=120)
            x = area.x
            for label, i, w in cols:
                v = row[i]
                if label == "No.":
                    self.text(s, f"#{v:03}", x + 2, y, DIM)
                elif label == "Types":
                    bx = x + 2
                    for kind in v:
                        bx += self.badge(s, kind, bx, y, short=True)
                elif label == "Name":
                    self.text(s, v, x + 2, y, WHITE if hot else TEXT)
                else:
                    self.text(s, str(v), x + w - 8, y, WHITE if label == "Total" else stat_color(v), right=True)
                x += w
            self.buttons.append((rr, self.choose(row[0])))
        self.text(s, f"{len(rows)} found so far. Click a column to sort; click an animal to see it.",
                  area.x + 2, area.bottom - 16, DIM)

    def entry(self, s, area):
        cloth(s, area, mix(CLOTH, EDGE, 0.25), alpha=200)
        x, y = area.x + 12, area.y + 10
        name = self.known.get(self.pick)
        line_start = (self.pick - 1) // 3 * 3 + 1
        stage = self.pick - line_start + 1
        self.text(s, f"#{self.pick:03}", x, y, DIM)
        self.text(s, name or "???", x + 44, y, WHITE)
        y += 20
        if name is None:
            self.text(s, "?", area.centerx, area.centery - 30, DIM, center=True)
            self.text(s, "Not discovered yet.", area.centerx, area.centery, DIM, center=True)
            base = self.known.get(line_start)
            if base and stage > 1:
                self.text(s, f"Stage {stage} of the {base} line.", area.centerx, area.centery + 16, DIM,
                          center=True)
            return
        sp = SPECIES[name]
        bx = x
        for kind in sp["types"]:
            bx += self.badge(s, kind, bx, y)
        self.text(s, f"Stage {stage} of 3", area.right - 12, y, DIM, right=True)
        y += 20
        if self.live is None or self.live[0] != name:
            self.live = (name, specimen(name), art.solid((PW, PH)))
        _, thing, pic = self.live
        paint(pic, thing, self.now)
        big = pygame.transform.scale(pic, (PW * 2, PH * 2))
        frame = big.get_rect(midtop=(area.centerx, y))
        s.blit(big, frame)
        pygame.draw.rect(s, mix(CLOTH, (255, 255, 255), 0.3), frame.inflate(2, 2), 1, border_radius=3)
        from evolve import feet
        self.text(s, feet(name), frame.right - 6, frame.bottom - 16, TEXT, right=True)  # how tall it is
        y = frame.bottom + 8
        self.text(s, "Ability", x, y, DIM)
        self.text(s, sp["ability"], area.right - 12, y, TEXT, right=True)
        y += 20
        for label, v in zip(LONG, sp["base"]):
            self.text(s, label, x, y, DIM)
            self.text(s, str(v), x + 96, y, TEXT, right=True)
            bw = area.right - 12 - (x + 104)
            pygame.draw.rect(s, (20, 12, 30), (x + 104, y + 4, bw, 5), border_radius=2)
            pygame.draw.rect(s, stat_color(v), (x + 104, y + 4, round(bw * min(1.0, v / 150)), 5),
                             border_radius=2)
            y += 15
        pygame.draw.line(s, mix(CLOTH, EDGE, 0.4), (x, y + 1), (area.right - 12, y + 1))
        y += 4
        self.text(s, "Total", x, y, DIM)
        self.text(s, str(sum(sp["base"])), x + 96, y, WHITE, right=True)
        y += 24
        self.text(s, "Moves it can learn", x, y, DIM)
        y += 16
        half = (len(sp["pool"]) + 1) // 2
        for i, mv in enumerate(sp["pool"]):
            cx = x + (i // half) * ((area.w - 24) // 2)
            cy = y + (i % half) * 15
            pygame.draw.rect(s, TYPE_COLOR.get(MOVES[mv]["t"], (200, 200, 200)), (cx, cy + 3, 4, 7))
            self.text(s, mv, cx + 8, cy, TEXT)
        y += half * 15 + 10
        nxt = self.known.get(self.pick + 1)
        if stage < 3:
            self.text(s, f"Evolves into: #{self.pick + 1:03} {nxt or '?'}", x, y, DIM)
