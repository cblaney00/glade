"""Your creature boxes — like the PC boxes in Pokémon Emerald.

Opened at the Battle Tower's storage shrine, or with the Forest Dex's "Your creatures"
button. On the left your party (six), in the middle one box of thirty (arrows go through
the boxes), on the right whoever you are pointing at or holding: its picture, types, moves
and its IV web. Click a creature to pick it up, click a slot to put it down there (if
someone is already there, you pick them up instead: a swap). Everything is saved as soon
as it is put down (team.Collection).
"""

import pygame

from apex import ease
from battle import CLOTH, DIM, EDGE, MOVES, SPECIES, TEXT, TYPE_COLOR, cloth, iv_web, mix
from dex import MINT, WHITE, picture
from team import BOXES, PER_BOX, TEAM, Collection

COLS = 6


class Storage:
    def __init__(self, font, t):
        self.font, self.t = font, t
        self.rect = pygame.Rect(30, 18, 900, 504)
        self.box = Collection()
        self.page = 0
        self.held = None        # the creature on the pointer, picked up
        self.came_from = None   # (where, i): put it back there if the boards close
        self.buttons = []
        self.slots = []         # (rect, where, i): where is "party" or a box number
        self.closed = False

    # --- what is where ---
    def get(self, where, i):
        return self.box.party[i] if where == "party" else self.box.boxes[where][i]

    def put(self, where, i, kept):
        if where == "party":
            self.box.party[i] = kept
        else:
            self.box.boxes[where][i] = kept

    # --- clicks ---
    def click(self, m):
        for r, action in self.buttons:
            if r.collidepoint(m):
                action()
                return
        for r, where, i in self.slots:
            if r.collidepoint(m):
                self.slot(where, i)
                return

    def slot(self, where, i):
        there = self.get(where, i)
        if self.held is None:
            if there is not None:  # pick it up
                self.held, self.came_from = there, (where, i)
                self.put(where, i, None)
            return
        if where == "party" and there is None:
            i = sum(1 for k in self.box.party if k)  # the party has no gaps: it goes on the end
        self.put(where, i, self.held)
        self.held, self.came_from = there, ((where, i) if there is not None else None)
        if self.held is None:
            self.box.save()

    def close(self):
        if self.held is not None:  # never lose one: put it back where it came from
            where, i = self.came_from
            if self.get(where, i) is None:
                self.put(where, i, self.held)
            else:
                self.box.add(self.held)
            self.held = None
            self.box.save()
        self.closed = True

    def turn(self, d):
        def f():
            self.page = (self.page + d) % BOXES
        return f

    # --- drawing ---
    def text(self, s, words, x, y, color=TEXT, right=False, center=False):
        img = self.font.render(words, False, color)
        if right:
            x -= img.get_width()
        elif center:
            x -= img.get_width() // 2
        s.blit(img, (x, y))
        return img.get_width()

    def button(self, s, r, label, action, m):
        hot = r.collidepoint(m) if m else False
        cloth(s, r, MINT if hot else mix(CLOTH, EDGE, 0.2), hot=hot, alpha=215)
        img = self.font.render(label, False, WHITE if hot else TEXT)
        s.blit(img, img.get_rect(center=r.center))
        self.buttons.append((r, action))

    def cell(self, s, r, kept, m, label=True):
        hot = bool(m) and r.collidepoint(m)
        cloth(s, r, MINT if hot else mix(CLOTH, EDGE, 0.35), hot=hot, alpha=200 if kept else 120)
        if kept is not None:
            pic = picture(kept.species)
            w = min(r.w - 4, pic.get_width())
            h = round(pic.get_height() * w / pic.get_width())
            if label:
                h = min(h, r.h - 16)
            img = pygame.transform.scale(pic, (w, h))
            s.blit(img, img.get_rect(midtop=(r.centerx, r.y + 2)))
            if label:
                name = kept.species
                while self.font.size(name)[0] > r.w - 6 and len(name) > 3:
                    name = name[:-2] + "…"
                self.text(s, name, r.centerx, r.bottom - 14, WHITE if hot else TEXT, center=True)
        return hot

    def draw(self, s, m, t):
        self.buttons, self.slots = [], []
        r = self.rect
        k = ease((t - self.t) / 0.2)
        cloth(s, r, CLOTH, alpha=round(248 * k))
        if k < 1:
            return
        self.text(s, "YOUR CREATURES", r.x + 14, r.y + 10, WHITE)
        self.text(s, "Click one to pick it up, then click where it should go.", r.x + 160, r.y + 10, DIM)
        self.button(s, pygame.Rect(r.right - 70, r.y + 8, 58, 18), "Close", self.close, m)
        pointed = self.held
        # the party
        px, py = r.x + 14, r.y + 40
        self.text(s, "PARTY", px, py, MINT)
        for i in range(TEAM):
            cr = pygame.Rect(px, py + 18 + i * 74, 132, 70)
            if self.cell(s, cr, self.box.party[i], m) and self.box.party[i] and pointed is None:
                pointed = self.box.party[i]
            self.slots.append((cr, "party", i))
        # the box
        bx, by = r.x + 170, r.y + 40
        name = self.box.names[self.page]
        self.button(s, pygame.Rect(bx, by - 2, 22, 18), "<", self.turn(-1), m)
        self.text(s, f"{name}  ({self.page + 1}/{BOXES})", bx + 210, by, WHITE, center=True)
        self.button(s, pygame.Rect(bx + 398, by - 2, 22, 18), ">", self.turn(1), m)
        row = self.box.boxes[self.page]
        for i in range(PER_BOX):
            cr = pygame.Rect(bx + (i % COLS) * 71, by + 20 + (i // COLS) * 88, 66, 84)
            if self.cell(s, cr, row[i], m) and row[i] and pointed is None:
                pointed = row[i]
            self.slots.append((cr, self.page, i))
        # who you are pointing at (or holding)
        self.info(s, pygame.Rect(r.x + 608, r.y + 40, 278, 450), pointed, t)
        if self.held is not None and m:  # the one you are carrying, on the pointer
            pic = picture(self.held.species)
            pygame.draw.ellipse(s, mix(MINT, EDGE, 0.5), (m[0] - 30, m[1] + 16, 60, 10))
            s.blit(pic, pic.get_rect(center=(m[0], m[1] - 4)))

    def info(self, s, r, kept, t):
        cloth(s, r, mix(CLOTH, EDGE, 0.3), alpha=170)
        if kept is None:
            n = len(self.box.everyone())
            self.text(s, f"{n} caught", r.centerx, r.y + 12, TEXT, center=True)
            self.text(s, "Battle a wild animal from its", r.centerx, r.y + 40, DIM, center=True)
            self.text(s, "stats card, then throw a glow jar.", r.centerx, r.y + 54, DIM, center=True)
            return
        sp = SPECIES[kept.species]
        pic = pygame.transform.scale(picture(kept.species), (216, 156))
        s.blit(pic, (r.centerx - 108, r.y + 8))
        y = r.y + 170
        self.text(s, f"#{sp['num']:03d} {kept.species}", r.x + 10, y, WHITE)
        x = r.x + 10
        y += 16
        for kind in sp["types"]:
            img = self.font.render(kind.upper(), False, EDGE)
            pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), (x, y, img.get_width() + 6, img.get_height() + 1),
                             border_radius=3)
            s.blit(img, (x + 3, y))
            x += img.get_width() + 9
        self.text(s, sp["ability"], r.right - 10, y, DIM, right=True)
        y += 18
        for i, name in enumerate(kept.moves[:4]):
            mv = MOVES.get(name)
            c = TYPE_COLOR.get(mv["t"], TEXT) if mv else TEXT
            self.text(s, name, r.x + 10 + (i % 2) * 134, y + (i // 2) * 14, c)
        y += 34
        iv_web(s, self.font, kept.ivs, (r.centerx, y + 76), 54, t)
