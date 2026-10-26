"""The Forest Dex — like a Pokédex, for the glade's animals.

Opened from an animal's right-click stats card ("Open in Forest Dex"), at that animal.
It has room for 260 animals. Each animal here is the first of three evolutions, so its
line takes three numbers in a row (SPECIES[...]["num"] in battle.py): the later two are
"?" until they are made. Two tabs: the Dex (every slot, in pages) and Compare (every
animal found so far in one table, sorted by whichever stat you click). The panel on the
right shows the chosen one in full.
"""

import pygame

from apex import ease
from battle import CLOTH, DIM, EDGE, MOVES, SPECIES, TEXT, TYPE_COLOR, cloth, mix, stat_color

TOTAL = 260
PER_PAGE = 48          # 8 x 6 slots
STATS = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")
LONG = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")
WHITE = (255, 255, 255)
MINT = (110, 255, 180)


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
            self.text(s, f"#{num:03}", cell.x + 4, cell.y + 3, WHITE if on else DIM)
            if name:
                words = name.split()  # "Tree Squid" goes on two lines
                for j, word in enumerate(words):
                    self.text(s, word, cell.centerx, cell.bottom - 16 - 13 * (len(words) - 1 - j),
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
