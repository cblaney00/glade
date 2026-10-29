"""The badge case (his ask, 2026-10-29): right under "Your party", the gym badges he has won,
laid out like the minimap (scenes.MAP) with a slot at every place that has a gym.

His look: a pouch for precious stones, but modern, like a glasses case. So: a smooth pastel
hard shell with a glossy band and a gold clasp on its lid, opened onto deep violet velvet with
gold stitching round it; the paths between places are pressed into the velvet, every gym is
a little socket there, and a won badge sits in its socket as a cut gem in its leader's colour,
glowing softly and now and then glinting. Pointing at a slot names its gym.

It is a drop-down (his ask): closed, only the lid shows ("Badges 3/11"); clicking the lid
opens the case under it, and again closes it. Clicking a gem or an empty slot goes to that
place, like the minimap (main.Glade.click; from the desktop it starts Wander first).
"""

import json
import math
import os

import pygame

import art
import corner
from apex import ease
from battle import EDGE, mix
from gyms import GYMS, TITLES
from scenes import LINKS, MAP
from team import STATE

SHELL = (172, 150, 214)      # the hard shell: a pastel lilac
SHELL_HI = (226, 214, 250)
SHELL_LO = (104, 84, 146)
VELVET = (46, 26, 70)
VELVET_LO = (28, 14, 46)
VELVET_HI = (70, 44, 100)
GOLD = (255, 214, 120)
GOLD_LO = (176, 128, 60)

CELL = 15   # velvet pixels between neighbouring places
LID = 18    # the lid strip at the top, where "Badges" is written


FULL = 154  # the open case's height; closed it is just the lid, as tall as the boards above


class State:
    open = False
    since = -10.0   # when it was last opened or closed
    shown = 22      # the height drawn last frame (world.rect puts the Wander board under it)


corner.HEIGHT["badges"] = lambda: State.shown


def full(view):
    """Right under the Your party board (hiding.party_rect), the same width, open."""
    r = corner.rect("badges")
    r.h = FULL
    return r


def lid(view):
    r = corner.rect("badges")
    r.h = 22
    return r


def rect(view):
    """What is on screen now: the lid, the open case, or something between while it moves."""
    return corner.rect("badges")


def toggle(t):
    State.open = not State.open
    State.since = t


def openness(t):
    k = ease(min(1.0, (t - State.since) / 0.22))
    return k if State.open else 1 - k


# --- which badges are won: read from the save, only when it changes -------------------------

_seen = [None, ()]


def won():
    try:
        stamp = os.stat(STATE).st_mtime
    except OSError:
        return ()
    if stamp != _seen[0]:
        try:
            with open(STATE) as f:
                _seen[1] = tuple(b for b in json.load(f).get("badges", []) if b in GYMS)
        except (OSError, ValueError):
            _seen[1] = ()
        _seen[0] = stamp
    return _seen[1]


# --- layout -----------------------------------------------------------------------------------

_xs = [x for x, _ in MAP.values()]
_ys = [y for _, y in MAP.values()]
X0, Y0 = min(_xs), min(_ys)
COLS, ROWS = max(_xs) - X0 + 1, max(_ys) - Y0 + 1


def tray(r):
    """The velvet inside the case, in case coordinates."""
    return pygame.Rect(7, LID + 5, r.w - 14, ROWS * CELL + 8)


def node(r, key):
    t = tray(r)
    gx, gy = MAP[key]
    left = t.x + (t.w - COLS * CELL) // 2
    return left + (gx - X0) * CELL + CELL // 2, t.y + 4 + (gy - Y0) * CELL + CELL // 2


def at(view, m):
    """The gym slot under the pointer, or None."""
    r = full(view)
    if not State.open or m is None or not rect(view).collidepoint(m) or lid(view).collidepoint(m):
        return None
    for key in GYMS:
        nx, ny = node(r, key)
        if abs(m[0] - r.x - nx) <= 7 and abs(m[1] - r.y - ny) <= 7:
            return key
    return None


# --- drawing ----------------------------------------------------------------------------------

def gem(s, x, y, c):
    """A small cut gem: a bright crown over a pointed pavilion, with a lit facet."""
    crown = [(x - 5, y - 1), (x - 3, y - 4), (x + 3, y - 4), (x + 5, y - 1)]
    pygame.draw.polygon(s, mix(c, EDGE, 0.25), [(x - 5, y - 1), (x + 5, y - 1), (x, y + 5)])
    pygame.draw.polygon(s, c, [(x - 5, y - 1), (x, y - 1), (x, y + 5)])           # the lit side
    pygame.draw.polygon(s, mix(c, (255, 255, 255), 0.4), crown)
    pygame.draw.line(s, mix(c, (255, 255, 255), 0.75), (x - 2, y - 4), (x + 2, y - 4))  # the table
    pygame.draw.line(s, mix(c, EDGE, 0.45), (x - 5, y - 1), (x + 5, y - 1))       # the girdle
    s.set_at((x - 2, y - 3), (255, 255, 255))
    s.set_at((x - 1, y + 1), mix(c, (255, 255, 255), 0.6))


def socket(s, x, y, c):
    """An empty slot pressed into the velvet, with a faint ring of its gym's colour."""
    pygame.draw.circle(s, VELVET_LO, (x, y), 6)
    pygame.draw.circle(s, mix(c, VELVET, 0.5), (x, y), 6, 1)
    pygame.draw.arc(s, VELVET_HI, (x - 6, y - 5, 12, 12), math.pi * 1.15, math.pi * 1.85, 1)  # lit lower lip


_cache = {}


def case(r, have, pointed, font):
    key = (r.size, have, pointed)
    if key in _cache:
        return _cache[key]
    if len(_cache) > 40:
        _cache.clear()
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    box = s.get_rect()
    # the hard shell, rounded like a glasses case, with a glossy band across the lid
    pygame.draw.rect(s, EDGE, box, border_radius=12)
    pygame.draw.rect(s, SHELL_LO, box.inflate(-2, -2), border_radius=11)
    pygame.draw.rect(s, SHELL, box.inflate(-2, -4).move(0, -1), border_radius=11)
    pygame.draw.line(s, SHELL_HI, (12, 2), (r.w - 13, 2))
    pygame.draw.line(s, mix(SHELL, SHELL_HI, 0.5), (8, 4), (r.w - 9, 4))
    pygame.draw.line(s, SHELL_LO, (6, LID + 1), (r.w - 7, LID + 1))   # where the lid opens
    pygame.draw.line(s, SHELL_HI, (6, LID + 2), (r.w - 7, LID + 2))
    # the gold clasp at the middle of the lid's edge
    cx = r.w // 2
    pygame.draw.rect(s, GOLD_LO, (cx - 7, LID - 3, 14, 7), border_radius=2)
    pygame.draw.rect(s, GOLD, (cx - 6, LID - 3, 12, 5), border_radius=2)
    s.set_at((cx - 4, LID - 2), (255, 250, 220))
    # "Badges" on the lid, either side of the clasp
    for words, x, right in (("Badges", 12, False), (f"{len(have)}/{len(GYMS)}", r.w - 22, True)):
        img = font.render(words, False, (255, 255, 255))
        shade = font.render(words, False, SHELL_LO)
        y = 3 + (LID - 3 - img.get_height()) // 2
        x = x - img.get_width() if right else x
        s.blit(shade, (x + 1, y + 1))
        s.blit(img, (x, y))
    ax, ay = r.w - 15, LID // 2 - 1  # a small arrow: click the lid to shut it
    pygame.draw.polygon(s, (255, 255, 255), [(ax - 3, ay + 3), (ax + 3, ay + 3), (ax, ay)])
    # the velvet, softly napped, with gold stitching round its edge
    t = tray(r)
    pygame.draw.rect(s, VELVET_LO, t.inflate(2, 2), border_radius=6)
    pygame.draw.rect(s, VELVET, t, border_radius=5)
    for y in range(t.y + 2, t.bottom - 2, 2):
        for x in range(t.x + 2 + (y // 2) % 3, t.right - 2, 5):
            s.set_at((x, y), mix(VELVET, VELVET_HI, 0.35))
    stitch = t.inflate(-6, -6)
    for x in range(stitch.x + 3, stitch.right - 3, 4):
        for y in (stitch.y, stitch.bottom - 1):
            s.set_at((x, y), GOLD_LO)
            s.set_at((x + 1, y), GOLD_LO)
    for y in range(stitch.y + 3, stitch.bottom - 3, 4):
        for x in (stitch.x, stitch.right - 1):
            s.set_at((x, y), GOLD_LO)
            s.set_at((x, y + 1), GOLD_LO)
    # the paths pressed into the velvet, and a little dimple at every place
    for a, b in LINKS:
        (ax, ay), (bx, by) = node(r, a), node(r, b)
        pygame.draw.line(s, VELVET_HI, (ax, ay + 1), (bx, by + 1), 2)
        pygame.draw.line(s, VELVET_LO, (ax, ay), (bx, by), 2)
    for k in MAP:
        if k not in GYMS:
            nx, ny = node(r, k)
            pygame.draw.rect(s, VELVET_LO, (nx - 1, ny - 1, 3, 3))
            s.set_at((nx, ny + 1), VELVET_HI)
    for k, (_, _, _, c) in GYMS.items():
        nx, ny = node(r, k)
        socket(s, nx, ny, c)
        if k in have:
            gem(s, nx, ny, c)
        if k == pointed:
            pygame.draw.circle(s, (255, 255, 255), (nx, ny), 8, 1)
    # under the velvet: the gym pointed at, or a hint
    if pointed:
        words = TITLES[pointed] + ("" if pointed in have else " (not yet)")
        color = (34, 16, 56) if pointed in have else (64, 42, 96)
    else:
        words, color = ("Every badge won!" if len(have) == len(GYMS) else "A gem for every gym"), (64, 42, 96)
    # dark plum, pressed into the pale shell (his ask: light words there were hard to read)
    img = font.render(words, False, color)
    lit = font.render(words, False, SHELL_HI)
    x, y = (r.w - img.get_width()) // 2, t.bottom + (r.h - t.bottom - img.get_height()) // 2 - 1
    s.blit(lit, (x, y + 1))
    s.blit(img, (x, y))
    _cache[key] = s
    return s


def closed(r, have, hot, font):
    """The case shut: a slim pastel capsule with the clasp and a little arrow saying it opens."""
    key = ("shut", r.size, len(have), hot)
    if key in _cache:
        return _cache[key]
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    box = s.get_rect()
    shell = mix(SHELL, SHELL_HI, 0.3) if hot else SHELL
    pygame.draw.rect(s, EDGE, box, border_radius=10)
    pygame.draw.rect(s, SHELL_LO, box.inflate(-2, -2), border_radius=9)
    pygame.draw.rect(s, shell, box.inflate(-2, -4).move(0, -1), border_radius=9)
    pygame.draw.line(s, SHELL_HI, (10, 2), (r.w - 11, 2))
    pygame.draw.line(s, SHELL_LO, (6, r.h - 6), (r.w - 7, r.h - 6))  # the seam where it opens
    cx = r.w // 2
    pygame.draw.rect(s, GOLD_LO, (cx - 7, r.h - 9, 14, 6), border_radius=2)
    pygame.draw.rect(s, GOLD, (cx - 6, r.h - 9, 12, 4), border_radius=2)
    s.set_at((cx - 4, r.h - 8), (255, 250, 220))
    for words, x, right in (("Badges", 12, False), (f"{len(have)}/{len(GYMS)}", r.w - 22, True)):
        img = font.render(words, False, (255, 255, 255))
        shade = font.render(words, False, SHELL_LO)
        y = 1 + (r.h - 6 - img.get_height()) // 2
        x = x - img.get_width() if right else x
        s.blit(shade, (x + 1, y + 1))
        s.blit(img, (x, y))
    ax, ay = r.w - 15, r.h // 2 - 3  # a small arrow: it drops down
    pygame.draw.polygon(s, (255, 255, 255), [(ax - 3, ay), (ax + 3, ay), (ax, ay + 3)])
    _cache[key] = s
    return s


def draw(s, view, font, t):
    r = full(view)
    have = won()
    m = view.mouse()
    k = openness(t)
    State.shown = round(lid(view).h + (FULL - lid(view).h) * k)
    if k <= 0:
        s.blit(closed(lid(view), have, bool(m) and lid(view).collidepoint(m), font), r)
        return
    pointed = at(view, m) if k >= 1 else None
    s.blit(case(r, have, pointed, font), r, (0, 0, r.w, State.shown))
    if k < 1:
        return
    # the won gems glow softly and, one after another, catch the light
    for i, k in enumerate(have):
        nx, ny = node(r, k)
        x, y = r.x + nx, r.y + ny
        c = GYMS[k][3]
        k_ = 0.5 + 0.5 * math.sin(t * 1.4 + i * 1.3)
        art.glow(s, x, y, 9, c, int(30 + 40 * k_) // 10 * 10)
        glint = (t * 0.6 + i * 0.37) % 3.0
        if glint < 0.25:  # a little four-point star flashes on the crown
            a = 1 - abs(glint - 0.125) / 0.125
            star = mix(c, (255, 255, 255), 0.5 + 0.5 * a)
            sx, sy = x + 2, y - 4
            s.set_at((sx, sy), (255, 255, 255))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s.set_at((sx + dx, sy + dy), star)
            if a > 0.5:
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                    s.set_at((sx + dx, sy + dy), star)
