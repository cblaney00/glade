"""The boards down the lower screen's top-left corner, stacked in order with no gaps.

The desktop and the game show different boards there (the desktop has no Predator vision,
his pick 2026-10-29), so each sets ORDER once at the start and every board's rect asks
`rect(name)` where it goes. The badge case's height changes as it opens (badges.py
registers it in HEIGHT); the rest are 22 pixels tall.
"""

import pygame

X, TOP, W, GAP = 8, 8, 150, 4
ORDER = ["vision", "dex", "keep", "party", "badges", "nav", "world"]
HEIGHT = {}  # name -> a function giving its height now


def rect(name):
    y = TOP
    for n in ORDER:
        h = HEIGHT[n]() if n in HEIGHT else 22
        if n == name:
            return pygame.Rect(X, y, W, h)
        y += h + GAP
    return pygame.Rect(-1000, -1000, 0, 0)  # not shown in this app: nothing to point at
