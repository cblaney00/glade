"""The minimap (moved out of game.py, 2026-11-10, so the desktop has it too: his ask, on the top
screen there; in the game it stays on the lower screen). Every place laid out as scenes.MAP, the
paths between them, the place you are in glowing; places not open yet (unlock.py) are dark with a
padlock, and pointing at one says who to beat first."""

import math

import pygame

import art
from art import mix
from main import EDGE, HOT, TEXT, WOOD, WOOD_HI, WOOD_LO
from scenes import LINKS, MAP

LOCK = (250, 214, 130)


def padlock(s, x, y, color=LOCK):
    """A tiny padlock, centred on (x, y): a shackle over a body."""
    pygame.draw.rect(s, (40, 26, 52), (x - 3, y - 1, 7, 6))
    pygame.draw.rect(s, color, (x - 2, y, 5, 4))
    pygame.draw.lines(s, color, False, [(x - 2, y - 1), (x - 2, y - 3), (x - 1, y - 4), (x + 1, y - 4), (x + 2, y - 3),
                                       (x + 2, y - 1)])
    s.set_at((x, y + 1), (40, 26, 52))


class Minimap:
    """A little carved board in the corner with every place laid out the way the paths
    run (scenes.MAP): the place you are in glows, and its name is written underneath.
    Pointing at another place shows its name; clicking it goes there."""

    NAMES = dict(glade="The Glade", waterfall="The Waterfall", river="The River", forest="The Forest",
                 rocks="The Mossy Rocks", ridge="The Snowy Ridge", springs="The Hot Springs", tower="The Battle Tower",
                 caverns="The Crystal Caverns", meadow="The Starfall Meadow", hollow="The Mushroom Hollow",
                 bog="The Misty Bog", ruins="The Old Ruins", bridge="The Cloud Bridge", shore="The Glow Shore")
    NAMES.update(dict(falls="The Frozen Falls", peak="Aurora Peak", gully="Fern Gully", orchard="The Lantern Orchard", temple="The Sunken Temple", dunes="The Moon Dunes", lava="The Lava Lake", grotto="The Coral Grotto", kelp="The Kelp Deep", lighthouse="Lighthouse Point", comet="The Comet Crater", garden="The Moonpetal Garden", isles="The Floating Isles", storm="The Storm Peaks", thorn="Thornwood", hall="The Moonlit Hall"))
    COLORS = dict(glade=(255, 150, 214), waterfall=(140, 226, 255), river=(110, 170, 255),
                  forest=(160, 236, 140), rocks=(196, 160, 255), ridge=(214, 240, 255), springs=(255, 160, 110),
                  tower=(255, 214, 236), caverns=(190, 140, 255), meadow=(255, 236, 160), hollow=(200, 255, 170),
                  bog=(190, 255, 210), ruins=(150, 230, 255), bridge=(220, 214, 255), shore=(90, 240, 230))
    COLORS.update(dict(falls=(170, 230, 255), peak=(190, 255, 220), gully=(110, 220, 150), orchard=(255, 196, 120), temple=(110, 230, 190), dunes=(240, 210, 160), lava=(255, 120, 80), grotto=(255, 150, 170), kelp=(70, 170, 160), lighthouse=(255, 240, 180), comet=(200, 170, 255), garden=(230, 220, 255), isles=(160, 220, 255), storm=(250, 250, 140), thorn=(170, 90, 150), hall=(255, 236, 170)))
    CELL = 18  # canvas pixels between neighbouring places (22 until the map grew to thirty places)

    def __init__(self, font):
        self.font = font
        self.locked = frozenset()  # places not open yet (unlock.py): dimmed, with a padlock
        xs = [x for x, _ in MAP.values()]
        ys = [y for _, y in MAP.values()]
        self.x0, self.y0 = min(xs), min(ys)
        cols, rows = max(xs) - self.x0 + 1, max(ys) - self.y0 + 1
        name_w = max(font.size(n)[0] for n in list(self.NAMES.values()) + ["Beat Leader Marisel first"])
        self.w = max(cols * self.CELL + 16, name_w + 16)
        self.map_h = rows * self.CELL + 6
        self.h = self.map_h + font.get_height() + 10
        self.cache = {}
        self.rect = None

    def place(self, view):
        """Bottom-right of the view."""
        self.rect = pygame.Rect(0, 0, self.w + 4, self.h + 7)
        self.rect.bottomright = (view.w - 6, view.h - 30)
        return self.rect

    def node(self, key):
        """Centre of a place's stone, in board coordinates."""
        gx, gy = MAP[key]
        cols = max(x for x, _ in MAP.values()) - self.x0 + 1
        left = 2 + (self.w - cols * self.CELL) // 2
        return (left + (gx - self.x0) * self.CELL + self.CELL // 2, 4 + 3 + (gy - self.y0) * self.CELL + self.CELL // 2)

    def at(self, m):
        """The place under the pointer `m` (canvas coordinates), or None."""
        if self.rect is None or m is None or not self.rect.collidepoint(m):
            return None
        bx, by = m[0] - self.rect.x, m[1] - self.rect.y
        for key in MAP:
            nx, ny = self.node(key)
            if abs(bx - nx) <= self.CELL // 2 and abs(by - ny) <= self.CELL // 2:
                return key
        return None

    def board(self, here, pointed):
        key = (here, pointed, self.locked)
        if len(self.cache) > 200:
            self.cache.clear()
        if key in self.cache:
            return self.cache[key]
        s = pygame.Surface((self.w + 4, self.h + 7), pygame.SRCALPHA)
        r = pygame.Rect(2, 4, self.w, self.h)
        pygame.draw.rect(s, EDGE, r.inflate(2, 2), border_radius=3)
        pygame.draw.rect(s, WOOD, r, border_radius=2)
        pygame.draw.line(s, WOOD_HI, (r.x + 2, r.y), (r.right - 3, r.y))
        pygame.draw.line(s, WOOD_LO, (r.x + 2, r.bottom - 1), (r.right - 3, r.bottom - 1))
        for gx in range(r.x + 4, r.right - 3, 7):  # wood grain
            s.set_at((gx, r.bottom - 5), WOOD_LO)
        # the paths between places (scenes.LINKS)
        trail = (150, 112, 150)
        for a, b in LINKS:
            pygame.draw.line(s, trail, self.node(a), self.node(b), 3)
        for k in MAP:
            nx, ny = self.node(k)
            c = self.COLORS[k]
            stone = pygame.Rect(0, 0, 12, 10)
            stone.center = (nx, ny)
            if k == here:
                pygame.draw.rect(s, (255, 255, 255), stone.inflate(4, 4), border_radius=3)
                pygame.draw.rect(s, c, stone, border_radius=2)
                s.set_at((stone.x + 2, stone.y + 2), (255, 255, 255))
            elif k in self.locked:  # not open yet: a dark stone with a little padlock
                pygame.draw.rect(s, HOT if k == pointed else EDGE, stone.inflate(2, 2), border_radius=3)
                pygame.draw.rect(s, mix(c, EDGE, 0.8), stone, border_radius=2)
                padlock(s, nx, ny)
            else:
                pygame.draw.rect(s, HOT if k == pointed else EDGE, stone.inflate(2, 2), border_radius=3)
                pygame.draw.rect(s, mix(c, WOOD, 0.55), stone, border_radius=2)
        label = self.NAMES[pointed or here]
        if pointed in self.locked:
            from unlock import reason
            label = reason(pointed)
        text = self.font.render(label, False, HOT if pointed and pointed != here else TEXT)
        shade = self.font.render(label, False, EDGE)
        tx, ty = r.centerx - text.get_width() // 2, r.y + self.map_h + 2
        s.blit(shade, (tx + 1, ty + 1))
        s.blit(text, (tx, ty))
        moss = (150, 255, 200)  # a tuft of glowing moss on the top-left corner
        for dx, dy in ((0, 0), (1, -1), (2, -1), (3, 0), (4, -1), (5, 0), (2, -2), (6, 0)):
            s.set_at((r.x + 3 + dx, r.y + dy), moss if dy < 0 else (90, 190, 150))
        self.cache[key] = s
        return s

    def draw(self, s, view, here, pointed, t, place=True):
        rect = self.place(view) if place else self.rect
        s.blit(self.board(here, pointed), rect)
        # you-are-here: a soft glow breathing slowly over the place you are in
        nx, ny = self.node(here)
        k = 0.5 + 0.5 * math.sin(t * 1.8)
        art.glow(s, rect.x + nx, rect.y + ny, 11, self.COLORS[here], int(50 + 50 * k) // 10 * 10)
