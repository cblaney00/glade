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
from battle import CLOTH, DIM, EDGE, MOVES, SPECIES, TEXT, TYPE_COLOR, calc_stats, cloth, iv_web, mix
from dex import MINT, WHITE, picture
from team import BOXES, PER_BOX, TEAM, Collection, nature_effect

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
        pic = pygame.transform.scale(picture(kept.species), (144, 104))
        s.blit(pic, (r.x + 6, r.y + 6))
        # beside the picture: who it is
        x0, y = r.x + 156, r.y + 10
        self.text(s, f"#{sp['num']:03d}", x0, y, DIM)
        self.text(s, fit(self.font, kept.species, r.right - 8 - x0), x0, y + 13, WHITE)
        x = x0
        for kind in sp["types"]:
            img = self.font.render(kind.upper(), False, EDGE)
            pygame.draw.rect(s, TYPE_COLOR.get(kind, (200, 200, 200)), (x, y + 30, img.get_width() + 6, img.get_height() + 1),
                             border_radius=3)
            s.blit(img, (x + 3, y + 30))
            x += img.get_width() + 9
        self.text(s, "Lv100", x0, y + 48, TEXT)
        self.text(s, fit(self.font, f"Nature: {kept.nature}", r.right - 8 - x0), x0, y + 62, TEXT)
        up, down = nature_effect(kept.nature)
        what = f"+{SHORT[up]} -{SHORT[down]}" if up else "no effect"
        self.text(s, what, x0, y + 75, DIM)
        self.text(s, fit(self.font, sp["ability"], r.right - 8 - x0), x0, y + 89, DIM)
        # the stats table: base, IV, EV and the stat itself (raised: mint, lowered: pink)
        maxhp, stats = calc_stats(kept.species, kept.ivs, kept.evs, kept.nature)
        values = [maxhp] + [stats[k] for k in ("atk", "def", "spa", "spd", "spe")]
        keys = [None, "atk", "def", "spa", "spd", "spe"]
        y = r.y + 118
        cols = (r.x + 10, r.x + 92, r.x + 136, r.x + 180, r.right - 10)
        for c, h in zip(cols, ("", "Base", "IV", "EV", "Stat")):
            self.text(s, h, c, y, DIM, right=c != cols[0])
        for i, (label, base, iv, ev, v, k) in enumerate(zip(LONG, sp["base"], kept.ivs, kept.evs, values, keys)):
            yy = y + 14 + i * 14
            tint = MINT if k and k == up else (255, 150, 200) if k and k == down else TEXT
            self.text(s, label + (" +" if k and k == up else " -" if k and k == down else ""), cols[0], yy, tint)
            self.text(s, str(base), cols[1], yy, TEXT, right=True)
            self.text(s, str(iv), cols[2], yy, WHITE if iv == 31 else TEXT, right=True)
            self.text(s, str(ev), cols[3], yy, TEXT, right=True)
            self.text(s, str(v), cols[4], yy, tint if k else WHITE, right=True)
        yy = y + 14 + 6 * 14
        self.text(s, "Total", cols[0], yy, DIM)
        self.text(s, str(sum(sp["base"])), cols[1], yy, DIM, right=True)
        self.text(s, str(sum(kept.ivs)), cols[2], yy, DIM, right=True)
        self.text(s, str(sum(kept.evs)), cols[3], yy, DIM, right=True)
        self.text(s, str(sum(values)), cols[4], yy, DIM, right=True)
        # its moves, with type, power, accuracy and PP
        y = yy + 20
        for i, name in enumerate(kept.moves[:4]):
            mv = MOVES.get(name)
            if not mv:
                continue
            c = TYPE_COLOR.get(mv["t"], TEXT)
            self.text(s, name, r.x + 10, y + i * 14, c)
            acc = f"{mv['a']}%" if mv['a'] else '-'
            info = f"{mv['p'] or '-'}  {acc}  {mv['pp']}pp"
            self.text(s, info, r.right - 10, y + i * 14, DIM, right=True)
        # and the IV web
        iv_web(s, self.font, kept.ivs, (r.centerx, y + 56 + 50), 40, t)


SHORT = dict(atk="Atk", spa="SpA", spd="SpD", spe="Spe", **{"def": "Def"})
LONG = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")


def fit(font, line, w):
    while font.size(line)[0] > w and len(line) > 4:
        line = line[:-2] + "…"
    return line
