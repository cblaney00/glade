"""The Glade Nav (2026-10-30, his ask): a little device right under the badge case, with a map of
the trainers who want to battle (trainers.py).

Its look (Claude's pick, to sit beside his badge case): a pastel mint handheld with rounded
corners, a speaker grille and a little antenna light, and a dark glowing screen. The screen shows
the map (scenes.MAP) with a dot for every trainer: a gold "!" pulsing for one who wants to battle,
a dim dot for one beaten today. Pointing at a dot names the trainer; clicking it goes there.

A drop-down like the badge case: shut, only its top shows ("Glade Nav  27/29": how many want to battle). Only one of
the two is open at a time, so the corner never runs off the screen.
"""

import math

import pygame

import art
import badges
import corner
from apex import ease
from battle import EDGE, mix
from scenes import LINKS, MAP

SHELL = (150, 222, 196)       # pastel mint
SHELL_HI = (214, 250, 234)
SHELL_LO = (80, 150, 130)
SCREEN = (16, 30, 40)
SCREEN_HI = (40, 70, 80)
LINE = (60, 120, 120)
READY = (255, 214, 120)

TOP = 22    # the strip that shows when shut
CELL = 15


class State:
    open = False
    since = -10.0
    shown = TOP


corner.HEIGHT["nav"] = lambda: State.shown


def lid(view):
    r = corner.rect("nav")
    r.h = TOP
    return r


def full(view):
    r = corner.rect("nav")
    r.h = FULL
    return r


def rect(view):
    return corner.rect("nav")


def toggle(t):
    State.open = not State.open
    State.since = t
    if State.open and badges.State.open:  # one open at a time
        badges.toggle(t)


def close_for_badges(t):
    """The badge case is opening: the nav shuts."""
    if State.open:
        State.open = False
        State.since = t


def openness(t):
    k = ease(min(1.0, (t - State.since) / 0.22))
    return k if State.open else 1 - k


_xs = [x for x, _ in MAP.values()]
_ys = [y for _, y in MAP.values()]
X0, Y0 = min(_xs), min(_ys)
COLS, ROWS = max(_xs) - X0 + 1, max(_ys) - Y0 + 1
FULL = TOP + 4 + ROWS * CELL + 26 + 16  # the screen (map and a line of words) and the grille under it


def screen(r):
    return pygame.Rect(9, TOP + 4, r.w - 18, ROWS * CELL + 26)


def node(r, key):
    sc = screen(r)
    gx, gy = MAP[key]
    left = sc.x + (sc.w - COLS * CELL) // 2
    return left + (gx - X0) * CELL + CELL // 2, sc.y + 5 + (gy - Y0) * CELL + CELL // 2


def at(view, m):
    from trainers import TRAINERS
    if not State.open or m is None or not rect(view).collidepoint(m) or lid(view).collidepoint(m):
        return None
    r = full(view)
    for key in TRAINERS:
        nx, ny = node(r, key)
        if abs(m[0] - r.x - nx) <= 7 and abs(m[1] - r.y - ny) <= 7:
            return key
    return None


def counts():
    from trainers import TRAINERS, ready
    return sum(1 for k in TRAINERS if ready(k)), len(TRAINERS)


def shell(s, box, hot=False):
    pygame.draw.rect(s, EDGE, box, border_radius=9)
    pygame.draw.rect(s, SHELL_LO, box.inflate(-2, -2), border_radius=8)
    pygame.draw.rect(s, mix(SHELL, SHELL_HI, 0.3) if hot else SHELL, box.inflate(-2, -4).move(0, -1), border_radius=8)
    pygame.draw.line(s, SHELL_HI, (box.x + 9, box.y + 2), (box.right - 10, box.y + 2))


def title(s, r, font, n, total):
    # the antenna light, then the name and how many want to battle
    k = 1 if n else 0
    pygame.draw.circle(s, mix(SHELL_LO, READY, k), (r.x + 11, r.y + TOP // 2), 3)
    pygame.draw.circle(s, (255, 255, 255) if n else SHELL_HI, (r.x + 10, r.y + TOP // 2 - 1), 1)
    for words, x, right in (("Glade Nav", r.x + 19, False), (f"{n}/{total}", r.right - 10, True)):
        img = font.render(words, False, (255, 255, 255))
        shade = font.render(words, False, SHELL_LO)
        y = r.y + (TOP - img.get_height()) // 2
        x = x - img.get_width() if right else x
        s.blit(shade, (x + 1, y + 1))
        s.blit(img, (x, y))


def draw(s, view, font, t):
    from trainers import TRAINERS, ready, where
    n, total = counts()
    m = view.mouse()
    k = openness(t)
    State.shown = round(TOP + (FULL - TOP) * k)
    r = rect(view)
    if k <= 0:
        shell(s, r, bool(m) and r.collidepoint(m))
        title(s, r, font, n, total)
        return
    body = pygame.Surface((r.w, FULL), pygame.SRCALPHA)
    box = body.get_rect()
    shell(body, box)
    sc = screen(box)
    pygame.draw.rect(body, SHELL_LO, sc.inflate(4, 4), border_radius=5)
    pygame.draw.rect(body, SCREEN, sc, border_radius=4)
    for y in range(sc.y + 1, sc.bottom - 1, 2):  # scan lines
        pygame.draw.line(body, mix(SCREEN, SCREEN_HI, 0.25), (sc.x + 2, y), (sc.right - 3, y))
    for a, b in LINKS:
        pygame.draw.line(body, LINE, node(box, a), node(box, b), 1)
    for key in MAP:
        nx, ny = node(box, key)
        body.set_at((nx, ny), LINE)
    for gx in range(box.w // 2 - 16, box.w // 2 + 17, 4):  # the speaker grille under the screen
        pygame.draw.circle(body, SHELL_LO, (gx, box.bottom - 9), 1)
    s.blit(body, r.topleft, (0, 0, r.w, State.shown))
    title(s, r, font, n, total)
    if k < 1:
        return
    pointed = at(view, m)
    for i, key in enumerate(TRAINERS):
        nx, ny = node(box, key)
        x, y = r.x + nx, r.y + ny
        c = TRAINERS[key][3]
        if ready(key):
            p = 0.5 + 0.5 * math.sin(t * 3 + i * 0.7)
            art.glow(s, x, y, 8, READY, int(40 + 50 * p) // 10 * 10)
            pygame.draw.circle(s, mix(c, READY, 0.5), (x, y), 3)
            pygame.draw.line(s, (255, 250, 220), (x, y - 2), (x, y))
            s.set_at((x, y + 2), (255, 250, 220))
        else:
            pygame.draw.circle(s, mix(c, SCREEN, 0.7), (x, y), 2)
        if key == pointed:
            pygame.draw.circle(s, (255, 255, 255), (x, y), 6, 1)
    if pointed:
        words = f"{TRAINERS[pointed][0].split()[-1]}, {where(pointed)}"
        color = READY if ready(pointed) else (150, 180, 180)
    else:
        words, color = ("Gold = ready" if n else "All beaten today"), (150, 210, 200)
    img = font.render(words, False, color)
    if img.get_width() > sc.w - 6:
        img = font.render(TRAINERS[pointed][0].split()[-1] if pointed else words[:22], False, color)
    s.blit(img, (r.x + sc.centerx - img.get_width() // 2, r.y + sc.bottom - img.get_height() - 3))
