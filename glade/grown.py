"""Later stages for the Forest Dex's page two (2026-10-27, his ask), drawn as extras on top of
their first stage, the way Pokémon grow on their old look.

beasts.Walker / beasts.Flier call `grow_<kind>(s, t, stage)` after drawing a creature (stage 2
or 3) and `glow_<kind>(s, t, stage, k)` after its lights (k: how freshly it was poked). They are
set on the classes at the bottom of this file. Page three's own creatures are in wave4.py.
"""

import math

import pygame

from art import glow, mix
from beasts import INK, AURORA, Flier, Walker
from life import q

WHITE = (255, 255, 255)
ICE = (200, 240, 255)


def spikes(s, pts, color, ln):
    for (x, y), (dx, dy) in pts:
        pygame.draw.line(s, color, (round(x), round(y)), (round(x + dx * ln), round(y + dy * ln)))


# --- walkers ------------------------------------------------------------------------------

def grow_sporeling(self, s, t, st):
    """Sporecrown: a ring of little caps round the top of its cap, hung with spore lanterns."""
    if st < 3:
        return
    z, x, f = self.size, self.x, self.facing
    y = self.y - 4 * z
    for i in range(5):
        cx = x + (i - 2) * 3.6 * z
        cy = y - 17.5 * z - (2 - abs(i - 2)) * 1.2 * z
        pygame.draw.ellipse(s, mix(self.color, INK, 0.35), (cx - 2.4 * z, cy - 2.2 * z + 1, 4.8 * z, 3 * z))
        pygame.draw.ellipse(s, mix(self.color, WHITE, 0.3), (cx - 2.4 * z, cy - 2.2 * z, 4.8 * z, 3 * z))
    for side in (-1, 1):  # lanterns of spores on threads from the cap's rim
        lx = x + side * 8 * z
        sway = math.sin(t * 1.6 + side) * z
        pygame.draw.line(s, mix(self.body, INK, 0.3), (lx, y - 9 * z), (lx + sway, y - 4 * z))


def glow_sporeling(self, s, t, st, k):
    if st < 3:
        return
    z, x = self.size, self.x
    y = self.y - 4 * z
    for side in (-1, 1):
        lx = x + side * 8 * z + math.sin(t * 1.6 + side) * z
        b = 0.6 + 0.4 * math.sin(t * 2 + side)
        glow(s, lx, y - 3.5 * z, int(5 * z), self.color, q(90 * b + 60 * k))
        s.set_at((round(lx), round(y - 3.5 * z)), mix(self.color, WHITE, 0.6))


def grow_newt(self, s, t, st):
    """Frostslink: ice frills along its back; Hailmaw: a crest of crystals and a jaw of icicles."""
    z, f, pts = self.size, self.facing, self.tail
    for i in range(1, 8):
        px, py = pts[i]
        h = (3 + (i % 2) * 1.5) * z * (1.4 if st > 2 else 1.0)
        pygame.draw.polygon(s, ICE, [(px - z, py - 4 * z), (px + z, py - 4 * z), (px, py - 4 * z - h)])
        pygame.draw.line(s, WHITE, (px, py - 4 * z), (px, py - 4 * z - h * 0.6))
    hx, hy = pts[0]
    hx += f * 2.5 * z
    if st > 2:
        for j in range(3):  # a crown of crystals
            cx = hx - f * (j - 0.5) * 2 * z
            pygame.draw.polygon(s, (170, 220, 255), [(cx - z, hy - 5.5 * z), (cx + z, hy - 5.5 * z), (cx, hy - (10 + j) * z)])
        for j in range(3):  # icicle teeth
            tx = hx + f * (1 + j) * z
            pygame.draw.line(s, WHITE, (tx, hy - 1.5 * z), (tx, hy + 0.5 * z))
        tx, ty = pts[-1]  # a fin of ice on the tail's end
        pygame.draw.polygon(s, ICE, [(tx, ty - 2 * z), (tx - f * 4 * z, ty - 5 * z), (tx - f * 3 * z, ty + z)])


def glow_newt(self, s, t, st, k):
    if st > 2:
        hx, hy = self.tail[0]
        hx += self.facing * 2.5 * self.size
        glow(s, hx, hy - 8 * self.size, int(8 * self.size), self.color, q(70 + 70 * k))


def grow_beetle(self, s, t, st):
    """Copperclad: riveted copper plates and a horn; Voltbastion: two coil horns that crackle."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    dark = mix(self.body, INK, 0.5)
    for j in (-4, 0, 4):
        pygame.draw.line(s, mix(self.body, WHITE, 0.25), (x + j * z, y - 9.5 * z), (x + j * z * 1.2, y - 2 * z))
        s.set_at((round(x + j * z), round(y - 6 * z)), (255, 230, 190))
    hx = x + f * 7 * z
    if st == 2:
        pygame.draw.polygon(s, self.body, [(hx, y - 7 * z), (hx + f * 2 * z, y - 7 * z), (hx + f * 4 * z, y - 12 * z)])
    else:
        for side in (-1, 1):  # copper coils, wound with wire
            bx = hx - side * f * z
            pygame.draw.line(s, dark, (bx, y - 7 * z), (bx + f * 2 * z, y - 15 * z), max(2, round(1.4 * z)))
            for j in range(4):
                cy = y - (8.5 + j * 1.6) * z
                cx = bx + f * (j + 0.7) * 0.5 * z
                pygame.draw.line(s, (255, 200, 140), (cx - z, cy), (cx + z, cy))
        for j in range(-6, 7, 3):  # battlement plates along its back
            pygame.draw.rect(s, mix(self.body, WHITE, 0.15), (x + j * z - z, y - 12 * z, 2 * z, 2.4 * z))


def glow_beetle(self, s, t, st, k):
    if st < 3:
        return
    z, x, y, f = self.size, self.x, self.y, self.facing
    hx = x + f * 7 * z
    tips = [(hx - side * f * z + f * 2 * z, y - 15 * z) for side in (-1, 1)]
    for tx, ty in tips:
        glow(s, tx, ty, int(5 * z), self.color, q(90 + 80 * k))
    if math.sin(t * 7) > 0.2 or k > 0:  # a spark jumps between them
        (ax, ay), (bx, by) = tips
        pts = [(ax + (bx - ax) * j / 4, ay - 3 * z * ((j % 2) * 2 - 1) * 0.4 - z) for j in range(5)]
        pygame.draw.lines(s, self.color, False, pts)


def grow_fox(self, s, t, st):
    """Glimmerpaw: a second tail and a frosty ruff; Auroracle: five tails fanned out in aurora light."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    shade = mix(self.body, (120, 140, 220), 0.35)
    n = 1 if st == 2 else 4
    for j in range(n):
        a = 0.6 + j * 0.45
        sway = math.sin(t * 2 + j + self.phase) * 1.5 * z
        tail = [(x - f * (6 + math.cos(a) * i * 3) * z, y - 5 * z - math.sin(a) * i * 3 * z + sway * i / 3) for i in range(1, 4)]
        for i, (px, py) in enumerate(tail):
            pygame.draw.circle(s, shade if i == 0 else self.body, (round(px), round(py)), max(2, round((3 - i * 0.4) * z)))
    hx, hy = x + f * 6 * z, y - 9 * z
    for j in range(5):  # a frosty ruff round its neck
        pygame.draw.circle(s, WHITE, (round(hx - f * 3 * z + (j - 2) * 0.6 * z), round(hy + 3 * z + abs(j - 2) * 0.5 * z)), max(1, round(1.6 * z)))
    if st > 2:
        pygame.draw.polygon(s, (190, 240, 255), [(hx - z, hy - 2.5 * z), (hx + z, hy - 2.5 * z), (hx, hy - 5 * z)])


def glow_fox(self, s, t, st, k):
    z, x, y, f = self.size, self.x, self.y, self.facing
    n = 1 if st == 2 else 4
    for j in range(n):
        a = 0.6 + j * 0.45
        sway = math.sin(t * 2 + j + self.phase) * 1.5 * z
        tx, ty = x - f * (6 + math.cos(a) * 9) * z, y - 5 * z - math.sin(a) * 9 * z + sway
        c = AURORA[(j + int(t * 0.8 + self.phase)) % len(AURORA)]
        glow(s, tx, ty, int(7 * z), c, q(60 + 60 * k))
        s.set_at((round(tx), round(ty)), mix(c, WHITE, 0.5))
    if st > 2:
        glow(s, x + f * 6 * z, y - 13 * z, int(5 * z), (190, 240, 255), q(110))


def grow_goat(self, s, t, st):
    """Cragfluff: crags of rock through its wool; Peakcloak: a cloak of snowy stone and a rocky crown."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    rock, rd = (150, 146, 180), (96, 90, 126)
    for j, (px, h) in enumerate(((-4, 4), (0, 6), (3, 4))):
        bx, by = x + px * z, y - 12 * z
        pts = [(bx - 1.6 * z, by), (bx, by - h * z), (bx + 1.6 * z, by)]
        pygame.draw.polygon(s, rd, [(a, b + 1) for a, b in pts])
        pygame.draw.polygon(s, rock, pts)
    if st > 2:
        cloak = [(x - 8 * z, y - 12 * z), (x + 5 * z, y - 13 * z), (x + 7 * z, y - 6 * z), (x - 9 * z, y - 3 * z)]
        pygame.draw.polygon(s, rd, cloak)
        pygame.draw.polygon(s, rock, [(a, b - 1) for a, b in cloak])
        pygame.draw.line(s, (240, 246, 255), cloak[0], cloak[1], max(2, round(1.6 * z)))  # snow along the top
        hx, hy = x + f * 7 * z, y - 11 * z
        for j in (-1, 0, 1):
            pygame.draw.polygon(s, rock, [(hx + j * 1.6 * z - z, hy - 3 * z), (hx + j * 1.6 * z + z, hy - 3 * z),
                                          (hx + j * 1.6 * z, hy - (6 + (j == 0) * 2) * z)])


def grow_capy(self, s, t, st):
    """Steamsoak: a little pool on its back; Geyserbelly: a hot spring there, ringed with stones."""
    z, x, y = self.size, self.x, self.y
    w = 8 if st == 2 else 12
    pygame.draw.ellipse(s, mix(self.body, INK, 0.3), (x - w * 0.5 * z, y - 13 * z, w * z, 4 * z))
    pygame.draw.ellipse(s, (110, 220, 220), (x - w * 0.4 * z, y - 12.5 * z, w * 0.8 * z, 3 * z))
    if st > 2:
        for j in range(6):
            a = j / 6 * math.tau
            pygame.draw.circle(s, (170, 160, 190), (round(x + math.cos(a) * w * 0.55 * z), round(y - 11 * z + math.sin(a) * 2 * z)), max(1, round(1.3 * z)))


def glow_capy(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    glow(s, x, y - 11.5 * z, int((6 if st == 2 else 9) * z), (110, 236, 226), q(60 + 50 * k))
    for i in range(3 if st == 2 else 6):  # steam (and, grown, a geyser now and then)
        kk = (t * 0.5 + i / 6 + self.phase) % 1.0
        s.set_at((round(x + math.sin(t + i * 2) * 3 * z), round(y - 13 * z - kk * 14 * z)), mix((230, 226, 255), (40, 30, 70), kk))
    if st > 2 and ((t + self.phase) % 9 < 1.2 or k > 0.3):
        h = 14 * z * math.sin(min(1.0, ((t + self.phase) % 9) / 1.2) * math.pi) if k <= 0.3 else 14 * z
        pygame.draw.line(s, (200, 250, 250), (x, y - 12 * z), (x, y - 12 * z - h), max(2, round(1.5 * z)))
        glow(s, x, y - 12 * z - h, int(6 * z), (200, 250, 250), q(90))


def grow_gecko(self, s, t, st):
    """Cindercling: obsidian spines; Magmascale: a magma crest and plated jaw."""
    z, f, pts = self.size, self.facing, self.tail
    for i in range(1, 7):
        px, py = pts[i]
        h = (2 + (st - 1) * 1.2) * z * (1 - i / 9)
        pygame.draw.polygon(s, (50, 36, 60), [(px - z, py - 4.5 * z), (px + z, py - 4.5 * z), (px - f * z * 0.5, py - 4.5 * z - h)])
    if st > 2:
        hx, hy = pts[0]
        hx += f * 3 * z
        for j in range(4):
            cx = hx - f * j * 1.5 * z
            pygame.draw.polygon(s, (90, 50, 60), [(cx - z, hy - 5.5 * z), (cx + z, hy - 5.5 * z), (cx - f * z, hy - (9 - j) * z)])


def glow_gecko(self, s, t, st, k):
    z, f, pts = self.size, self.facing, self.tail
    for i in range(1, 7):
        px, py = pts[i]
        b = 0.5 + 0.5 * math.sin(t * 3 - i + self.phase)
        h = (2 + (st - 1) * 1.2) * z * (1 - i / 9)
        s.set_at((round(px - f * z * 0.5), round(py - 4.5 * z - h)), mix(self.color, (255, 236, 160), b))
    if st > 2:
        hx, hy = pts[0]
        glow(s, hx + f * 3 * z, hy - 7 * z, int(8 * z), self.color, q(80 + 70 * k))


def grow_bramble(self, s, t, st):
    """Bramblesnare: thorny runners that reach out and curl; Thornregent: a crown of thorns and a rose."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    cx, cy = x, y - 7 * z
    vine = mix(self.body, (150, 210, 160), 0.2)
    for j in range(2 + st):
        a = math.pi + (j / (1 + st)) * math.pi + math.sin(t * 1.2 + j) * 0.2
        pts = []
        for i in range(6):
            r = 5.5 * z + i * 2.4 * z
            pts.append((cx + math.cos(a + i * 0.25 * (1 if j % 2 else -1)) * r, cy + math.sin(a + i * 0.25) * r * 0.5 + i * z))
        pygame.draw.lines(s, vine, False, pts, max(1, round(z * 0.8)))
        for px, py in pts[1::2]:
            s.set_at((round(px), round(py - z)), (220, 200, 210))
    if st > 2:
        for j in range(5):  # crown of thorns
            a = -math.pi / 2 + (j - 2) * 0.4
            bx, by = cx + math.cos(a) * 5.5 * z, cy + math.sin(a) * 5.5 * z
            pygame.draw.line(s, (60, 40, 60), (bx, by), (bx + math.cos(a) * 4 * z, by + math.sin(a) * 4 * z), max(1, round(z)))
        rx, ry = cx + f * 2 * z, cy - 6 * z  # a deep red rose on top
        for j in range(5):
            a = j / 5 * math.tau + t * 0.2
            pygame.draw.circle(s, (200, 40, 80), (round(rx + math.cos(a) * 1.5 * z), round(ry + math.sin(a) * 1.2 * z)), max(1, round(1.4 * z)))
        pygame.draw.circle(s, (255, 90, 130), (round(rx), round(ry)), max(1, round(z)))


def glow_bramble(self, s, t, st, k):
    if st > 2:
        z = self.size
        glow(s, self.x + self.facing * 2 * z, self.y - 13 * z, int(6 * z), self.color, q(60 + 70 * k))


def grow_rune(self, s, t, st):
    """Runestand: a second stone set across its head like a lintel; Runewarden: two small standing
    stones that circle it slowly, runes lit on them too."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    rock, dark = self.body, mix(self.body, INK, 0.4)
    lintel = pygame.Rect(0, 0, round(14 * z), round(3.4 * z))
    lintel.midbottom = (round(x), round(y - 14 * z))
    pygame.draw.rect(s, dark, lintel.move(0, 1))
    pygame.draw.rect(s, rock, lintel)
    pygame.draw.line(s, mix(rock, WHITE, 0.3), lintel.topleft, lintel.topright)
    if st > 2:
        for side in (-1, 1):
            a = t * 0.6 + (0 if side < 0 else math.pi)
            cx, cy = x + math.cos(a) * 11 * z, y - 3 * z + math.sin(a) * 2 * z
            stone = [(cx - 2 * z, cy), (cx + 2 * z, cy), (cx + 1.6 * z, cy - 6 * z), (cx, cy - 7.5 * z), (cx - 1.6 * z, cy - 6 * z)]
            pygame.draw.polygon(s, dark, [(px, py + 1) for px, py in stone])
            pygame.draw.polygon(s, rock, stone)
            self.__dict__.setdefault("_orbit", {})[side] = (cx, cy - 3.5 * z)


def glow_rune(self, s, t, st, k):
    z, x, y = self.size, self.x, self.y
    b = 0.6 + 0.4 * math.sin(t * 1.7 + self.phase)
    for j in (-1, 0, 1):  # runes along the lintel
        s.set_at((round(x + j * 4 * z), round(y - 15.6 * z)), mix(self.color, WHITE, 0.3 * b))
    if st > 2:
        for side in (-1, 1):
            hx, hy = getattr(self, "_orbit", {}).get(side, (x, y))
            glow(s, hx, hy, int(6 * z), self.color, q(60 * b + 60 * k))
            pygame.draw.line(s, self.color, (hx, hy - 2 * z), (hx, hy + 2 * z))


def grow_murk(self, s, t, st):
    """Murkgloop: a third eye and a ridge of slimy spines; Murkdredge: a ring of vents that bubble."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    dark = mix(self.body, INK, 0.4)
    sway = math.sin(t * 2.2 + self.phase) * z
    bx, by = x - f * 1 * z, y - 6 * z
    tip = (bx + sway, by - 7 * z)
    pygame.draw.line(s, dark, (bx, by), tip, max(1, round(z)))
    self._tips = list(getattr(self, "_tips", [])) + [tip]
    for j in range(-2, 3):
        px = x + j * 2.5 * z
        pygame.draw.polygon(s, mix(self.body, (160, 230, 220), 0.2), [(px - z, y - 6 * z), (px + z, y - 6 * z), (px, y - 8.5 * z)])
    if st > 2:
        self._vents = []
        for j in (-1, 1):
            vx, vy = x + j * 6 * z, y - 5 * z
            pygame.draw.rect(s, dark, (vx - 1.5 * z, vy - 5 * z, 3 * z, 5 * z))
            pygame.draw.ellipse(s, (40, 30, 60), (vx - 1.8 * z, vy - 5.8 * z, 3.6 * z, 1.8 * z))
            self._vents.append((vx, vy - 5 * z))


def glow_murk(self, s, t, st, k):
    z = self.size
    for tx, ty in getattr(self, "_tips", [])[2:]:
        glow(s, tx, ty, int(5 * z), self.color, q(90 + 60 * k))
        pygame.draw.circle(s, self.color, (round(tx), round(ty)), max(1, round(1.2 * z)))
    for i, (vx, vy) in enumerate(getattr(self, "_vents", []) if st > 2 else []):
        for j in range(3):
            kk = (t * 0.7 + j / 3 + i * 0.4) % 1.0
            pygame.draw.circle(s, mix(self.color, (40, 30, 70), kk), (round(vx + math.sin(t * 2 + j) * z), round(vy - kk * 10 * z)), max(1, round(1.2 * z)), 1)
        glow(s, vx, vy, int(4 * z), self.color, q(70))


def grow_glint(self, s, t, st):
    """Glintdome: a second ring of plates and a spike on top; Glintcitadel: its dome turns into
    a little fortress, with turrets and lit windows."""
    z, x, y = self.size, self.x, self.y
    dark = mix(self.body, INK, 0.5)
    for i in range(-3, 4):
        px = x + i * 2.2 * z
        pygame.draw.polygon(s, mix(self.body, WHITE, 0.2), [(px - z, y - 3 * z), (px + z, y - 3 * z), (px, y - 6 * z)])
    if st == 2:
        pygame.draw.polygon(s, self.body, [(x - 1.5 * z, y - 11 * z), (x + 1.5 * z, y - 11 * z), (x, y - 16 * z)])
        return
    for tx, h in ((-5, 7), (0, 10), (5, 7)):  # turrets
        r = pygame.Rect(0, 0, round(4 * z), round(h * z))
        r.midbottom = (round(x + tx * z), round(y - 8 * z))
        pygame.draw.rect(s, dark, r.move(0, 1))
        pygame.draw.rect(s, self.body, r)
        for b in range(2):
            pygame.draw.rect(s, self.body, (r.x + b * 2.2 * z, r.y - 1.4 * z, 1.6 * z, 1.4 * z))
        self.__dict__.setdefault("_windows", {})[tx] = (r.centerx, r.y + r.h * 0.4)


def glow_glint(self, s, t, st, k):
    if st < 3:
        return
    z = self.size
    for i, (wx, wy) in enumerate(getattr(self, "_windows", {}).values()):
        b = 0.7 + 0.3 * math.sin(t * 1.3 + i * 2)
        glow(s, wx, wy, int(4 * z), (255, 210, 120), q(100 * b + 40 * k))
        s.set_at((round(wx), round(wy)), (255, 236, 170))


# --- fliers -------------------------------------------------------------------------------

def grow_finch(self, s, t, st):
    """Shimmertrill: a longer crest and tipped wings; Boreallume: a great fan of crest feathers."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    n = 3 if st == 2 else 5
    for j in range(n):
        a = -math.pi / 2 - f * (0.3 + j * 0.22)
        ln = (6 + j * (1 if st == 2 else 2)) * z
        pygame.draw.line(s, mix(self.body, (150, 255, 220), j / n), (x + f * z, y - 4 * z),
                         (x + f * z + math.cos(a) * ln, y - 4 * z + math.sin(a) * ln))


def glow_finch(self, s, t, st, k):
    z, x, y, f = self.size, self.x, self.y, self.facing
    streams = 2 if st == 2 else 4
    for j in range(streams):  # more streamers of aurora behind it
        for i, (px, py) in enumerate(self.trail[1:]):
            c = mix(AURORA[(i + j + int(t * 3)) % len(AURORA)], (40, 40, 90), i / 9)
            s.set_at((round(px - f * (6 + j) * z), round(py + (j - streams / 2 + 0.5) * 1.5 * z)), c)
    if st > 2:
        glow(s, x, y, int(14 * z), AURORA[int(t) % 4], q(40 + 60 * k))


def glow_jelly(self, s, t, st, k):
    """Vaporbell: a second skirt of frills and longer tentacles; Stormbloom: a crown of storm
    cloud on its bell, and lightning running down it."""
    z, x, y = self.size, self.x, self.y
    for i in range(7):
        tx = x + (i - 3) * 2.2 * z
        pts = [(tx + math.sin(t * 2 + i + j * 0.8 + self.phase) * 1.4 * z, y + 4 * z + j * 3.5 * z) for j in range(5 + st)]
        pygame.draw.lines(s, mix(self.body, (60, 70, 150), 0.4), False, pts)
    if st > 2:
        for j in range(6):
            a = math.pi + j / 5 * math.pi
            cx, cy = x + math.cos(a) * 8 * z, y - 1 * z + math.sin(a) * 4 * z
            pygame.draw.circle(s, (150, 150, 200), (round(cx), round(cy + 1)), max(2, round(3 * z)))
            pygame.draw.circle(s, (220, 224, 250), (round(cx), round(cy)), max(2, round(2.6 * z)))
        if math.sin(t * 4.3 + self.phase) * math.sin(t * 1.9) > 0.5 or k > 0.2:
            px, py = x + 3 * z, y - 8 * z
            for j in range(4):
                nx, ny = px + (2 if j % 2 else -2) * z, py + 4 * z
                pygame.draw.line(s, self.color, (px, py), (nx, ny))
                px, py = nx, ny
            glow(s, x, y, int(18 * z), self.color, q(110))


def grow_thistle(self, s, t, st):
    """Thistlegaze: a second ring of down; Thistleseer: seed-heads floating round it in a halo."""
    z, x, y = self.size, self.x, self.y
    down = mix(self.body, (120, 110, 190), 0.3)
    for i in range(18):
        a = i / 18 * math.tau + math.sin(t * 1.3 + self.phase) * 0.2
        ln = (11 + i % 2) * z
        pygame.draw.line(s, down, (round(x + math.cos(a) * 6 * z), round(y + math.sin(a) * 6 * z)),
                         (round(x + math.cos(a) * ln), round(y + math.sin(a) * ln * 0.9)))


def glow_thistle(self, s, t, st, k):
    if st < 3:
        return
    z, x, y = self.size, self.x, self.y
    for j in range(5):
        a = j / 5 * math.tau + t * 0.5
        sx, sy = x + math.cos(a) * 16 * z, y + math.sin(a) * 6 * z - 4 * z
        glow(s, sx, sy, int(4 * z), self.color, q(70 + 40 * k))
        pygame.draw.circle(s, WHITE, (round(sx), round(sy)), max(1, round(z)))


def grow_spark(self, s, t, st):
    """Arcfly: a longer tail with a second lamp; Thunderfly: wings cut like lightning bolts."""
    z, x, y, f = self.size, self.x, self.y, self.facing
    if st > 2:  # a zig-zag bolt of a wing, flicking
        flick = 1 + 0.15 * math.sin(t * 30)
        for lean in (0, 1):
            ox = -f * lean * 3 * z
            pts = [(x + ox, y - 2 * z), (x + ox - f * 2 * z, y - 7 * z * flick), (x + ox + f * 1.5 * z, y - 7.5 * z * flick),
                   (x + ox - f * z, y - 13 * z * flick), (x + ox + f * 2.5 * z, y - 6 * z * flick), (x + ox + f * 0.5 * z, y - 5.5 * z * flick)]
            pygame.draw.polygon(s, mix(self.color, WHITE, 0.45 - lean * 0.2), pts)
            pygame.draw.lines(s, self.color, True, pts)
    for i in range(3, 5):
        pygame.draw.circle(s, mix(self.body, INK, 0.3), (round(x - f * (2 + i * 2) * z), round(y + i * 0.6 * z)), max(1, round(1.8 * z)))


def glow_spark(self, s, t, st, k):
    z, x, y, f = self.size, self.x, self.y, self.facing
    tx, ty = x - f * 10 * z, y + 2.4 * z
    b = 0.5 + 0.5 * math.sin(t * 5 + self.phase + 1.5)
    glow(s, tx, ty, int(6 * z), self.color, q(60 + 80 * b + 40 * k))
    s.set_at((round(tx), round(ty)), mix(self.color, WHITE, 0.5))


GROWN_WALK = ("sporeling", "newt", "beetle", "fox", "goat", "capy", "gecko", "bramble", "rune", "murk", "glint")
GROWN_FLY = ("finch", "jelly", "thistle", "spark")
for _kind in GROWN_WALK:
    for _part in ("grow", "glow"):
        _fn = globals().get(f"{_part}_{_kind}")
        if _fn:
            setattr(Walker, f"{_part}_{_kind}", _fn)
for _kind in GROWN_FLY:
    for _part in ("grow", "glow"):
        _fn = globals().get(f"{_part}_{_kind}")
        if _fn:
            setattr(Flier, f"{_part}_{_kind}", _fn)

import wave4  # noqa: E402,F401  (page three's creatures)
