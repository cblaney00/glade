"""Wander and Rest (his ask, 2026-10-28).

The desktop is all looks and no play: the home clearing, its apps, Hide animals, Predator
vision, Thunderstorm and the Claude panel, with only storm.CAP creature families out. The
"Wander" board under "Your party" turns it into the whole game where it is, on both screens
(main.Glade.wander): the paths, minimap, far places, Battle Tower and battles. While the game
is on that board reads "Rest", which fades it back to the plain desktop and lets the far
places go (main.Glade.rest). The Forest Dex and Your party boards, right-clicking an animal
(its stats card) and clicking the moon also start the game, straight at that thing.
"""

import pygame

from battle import TEXT, cloth

WANDER = (196, 160, 255)


def rect(view):
    return pygame.Rect(8, 112, 150, 22)


def draw_button(s, view, font, playing):
    """A lilac board with a little footpath; "Wander" or "Rest"."""
    r = rect(view)
    m = view.mouse()
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, WANDER, hot=hot or playing, alpha=230)
    x, y = r.x + 7, r.centery
    for i, (dx, dy) in enumerate(((0, 4), (4, 1), (8, -2), (12, -5))):
        pygame.draw.ellipse(s, (250, 244, 255), (x + dx, y + dy - 1 + (i % 2), 4, 3))
    img = font.render("Rest" if playing else "Wander", False, (255, 255, 255) if hot or playing else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))
