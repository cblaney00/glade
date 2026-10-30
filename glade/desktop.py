"""The Glade desktop: all looks, no play (world.py; Lando's rule, his picks, 2026-10-29).

The home clearing alone: its apps, its animals coming and going (only storm.CAP families, new
ones each Thunderstorm), Hide animals, the badge case and the Claude panel. Its play boards —
Forest Dex, Your party, a badge-case gem, Wander, right-clicking an animal, the moon — open the
game (game.py) straight at that thing; while the game is open the desktop steps aside for it.
It is built on the same Glade as the game (main.Glade) and adds only this.
"""

import random

import badges
import corner
import gyms
import hiding
import storm
import world
from main import Glade


class Desktop(Glade):
    def __init__(self, screen, rect, lower=None):
        corner.ORDER = ["dex", "keep", "party", "badges", "world"]  # no Predator vision here (his pick)
        gyms.SHOW = False  # the Glade's gym stone is the game's
        super().__init__(screen, rect, lower)
        storm.limit([self.here] + list(self.lowers.values()), random.Random())  # 20 families, till a storm
        self.pausable = False  # set by wayland.py: there the game takes the desktop's place

    def paused(self):
        """The game is open in the desktop's place: the desktop steps aside and waits."""
        return self.pausable and world.showing()

    def home_only(self, content):
        """The paths lead nowhere here: the far places, the Tower and gyms are the game's."""
        content.paths = [sp for sp in content.spots if sp.kind in ("go", "tower", "gym")]
        content.spots[:] = [sp for sp in content.spots if sp.kind not in ("go", "tower", "gym")]
        return content

    def corner(self, view, t):
        hiding.draw_dex_button(view.canvas, view, self.signs.font)
        hiding.draw_buttons(view.canvas, view, self.signs.font, self.hide)
        badges.draw(view.canvas, view, self.signs.font, t)
        world.draw_button(view.canvas, view, self.signs.font, False)

    def corner_click(self, view, m, t):
        if hiding.dex_rect(view).collidepoint(m):
            world.open_world("dex")
            return True
        if hiding.party_rect(view).collidepoint(m):
            world.open_world("party")
            return True
        if world.rect(view).collidepoint(m):
            world.open_world()
            return True
        return False

    def to_place(self, key, t):
        world.open_world("go", place=key)

    def moon_clicked(self, t):
        world.open_world("moon")

    def show_card(self, view, m, species, t, animal=None):
        world.open_world("card", species)
