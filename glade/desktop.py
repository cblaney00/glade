"""The Glade desktop: all looks, no play (world.py; Lando's rule, his picks, 2026-10-29).

The home clearing alone: its apps, its animals coming and going (only storm.CAP families, new
ones each Thunderstorm), Hide animals, the badge case and the Claude panel. Its play boards —
Forest Dex, Your party, a badge-case gem, the Glade Nav, Wander and a stats card's Battle it! /
Forest Dex buttons — open the game (game.py) straight at that thing; while the game is open the
desktop steps aside for it. Right-clicking an animal shows its card here, and the moon does nothing
(2026-11-02, his ask: the game starting by accident made the screen jitter).
It is built on the same Glade as the game (main.Glade) and adds only this.
"""

import random

import badges
import carry
import corner
import gyms
import nav
import hiding
import storm
import world
from main import Glade


class Desktop(Glade):
    def __init__(self, screen, rect, lower=None):
        corner.ORDER = ["dex", "keep", "party", "badges", "nav", "world"]  # no Predator vision here (his pick)
        gyms.SHOW = False  # the Glade's gym stone is the game's
        super().__init__(screen, rect, lower)
        storm.limit([self.here] + list(self.lowers.values()), random.Random())  # 20 families, till a storm
        self.pausable = False  # set by wayland.py: there the game takes the desktop's place
        self.card = None  # an animal's stats card, from a right-click (only its buttons open the game)
        self.away = False  # the game is open in its place
        world.before_open = lambda: carry.save(self)  # the game starts with these very animals (carry.py)

    def paused(self):
        """The game is open in the desktop's place: the desktop steps aside and waits."""
        away = self.pausable and world.showing()
        if self.away and not away:  # back from the game: its animals come home with it
            carry.load(self)
        self.away = away
        return away

    def home_only(self, content):
        """The paths lead nowhere here: the far places, the Tower and gyms are the game's."""
        content.paths = [sp for sp in content.spots if sp.kind in ("go", "tower", "gym", "trainer")]
        content.spots[:] = [sp for sp in content.spots if sp.kind not in ("go", "tower", "gym", "trainer")]
        return content

    def corner(self, view, t):
        hiding.draw_dex_button(view.canvas, view, self.signs.font)
        hiding.draw_buttons(view.canvas, view, self.signs.font, self.hide)
        badges.draw(view.canvas, view, self.signs.font, t)
        nav.draw(view.canvas, view, self.signs.font, t)
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

    def show_card(self, view, m, species, t, animal=None):
        self.card = self.make_card(view, m, species, t, animal)

    def above(self, view, content, t):
        if self.card is not None and self.card.view is view:
            self.card.draw(view.canvas, t)

    def play_click(self, t):
        """A click while the card is open closes it; its buttons open the game at that animal."""
        if self.card is None:
            return False
        card, self.card = self.card, None
        m = card.view.mouse()
        if m and card.button.collidepoint(m):
            world.open_world("dex", card.species)
        elif m and card.fight is not None and card.fight.collidepoint(m) and not card.locked:
            world.open_world("battle", card.species, mon=world.who(card.animal, card.species))
        return True
