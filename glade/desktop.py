"""The Glade desktop: all looks, no play (world.py; Lando's rule, his picks, 2026-10-29).

The home clearing alone: its apps, its animals coming and going (only storm.CAP families, new
ones each Thunderstorm), Hide animals, the badge case and the Claude panel. Its play boards —
Forest Dex, Your party, a badge-case gem, the Glade Nav, Wander and a stats card's Battle it! /
Forest Dex buttons — open the game (game.py) straight at that thing; while the game is open the
desktop steps aside for it. Right-clicking an animal shows its card here, and the moon does nothing
(2026-11-02, his ask: the game starting by accident made the screen jitter).
Home's top screen is the aerial view (aerial.py, 2026-11-10, his ask): the mouse wheel zooms it
(`Camera`), and clicking a place there opens a small live look at it (peek.py).
It is built on the same Glade as the game (main.Glade) and adds only this.
"""

import random

import pygame

import badges
import carry
import corner
import gyms
import nav
import hiding
import storm
import world
from art import H, W
from main import CALM_AFTER, HOME, Glade
from peek import Peek, Seen


class Camera:
    """The mouse wheel zooms the aerial home in and out (his picks, 2026-11-10): it starts all the
    way out; all the way in is about as close as the Glade used to look; the point under the pointer
    stays put while zooming; after a few idle minutes it drifts back out by itself."""

    MOST = 2.0  # all the way in
    STEP = 1.15  # one notch of the wheel
    SPEED = 8.0  # how quickly it glides to where the wheel asked

    def __init__(self):
        self.k, self.want = 1.0, 1.0
        self.anchor = (W / 2, H / 2, W / 2, H / 2)  # (the picture's point, where on screen it stays)

    def wheel(self, view, dy):
        m = view.screen_mouse()
        if m is None:
            return
        world_at = view.mouse()
        self.want = max(1.0, min(self.MOST, self.want * (self.STEP ** -dy)))
        self.anchor = (world_at[0], world_at[1], m[0], m[1])

    def rect(self):
        wx, wy, sx, sy = self.anchor
        w, h = W / self.k, H / self.k
        x = max(0.0, min(W - w, wx - sx / self.k))
        y = max(0.0, min(H - h, wy - sy / self.k))
        return pygame.Rect(round(x), round(y), round(w), round(h))

    def apply(self, view, dt, out):
        if out:
            self.want = 1.0
        self.k += (self.want - self.k) * min(1.0, dt * self.SPEED)
        if abs(self.k - self.want) < 0.004:
            self.k = self.want
        if self.k <= 1.0001:
            view.cam = None
            return
        if self.anchor is not None and view.screen_mouse() is None and out:
            self.anchor = (W / 2, H / 2, W / 2, H / 2)
        r = self.rect()
        view.cam = r
        s = view.canvas
        s.blit(pygame.transform.scale(s.subsurface(r), (W, H)), (0, 0))


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
        self.cam = Camera()
        self.cam_t = None
        self.peek = None  # the small live look at a place (peek.py), while it is open
        from minimap import Minimap
        self.minimap = Minimap(self.signs.font)  # on the top screen here (his ask, 2026-11-10)

    def builder(self, key):
        if key == HOME:
            from aerial import build_aerial
            return build_aerial()  # the aerial view, only here: the game keeps the old clearing
        return super().builder(key)

    def close_peek(self):
        if self.peek is not None:
            self.peek.close()
            self.peek = None

    def window_focused(self):
        self.close_peek()

    def scroll(self, dy):
        if self.top.screen_mouse() is not None and self.here.key == HOME:
            self.cam.wheel(self.top, dy)
            return
        super().scroll(dy)

    def camera(self, view, t):
        if view is not self.top:
            return
        dt = 0.0 if self.cam_t is None else min(0.1, t - self.cam_t)
        self.cam_t = t
        idle = self.now() - self.stirred > CALM_AFTER / 2  # a few idle minutes: back out it goes
        self.cam.apply(view, dt, idle)
        if idle:
            self.close_peek()

    def to_shown(self, view, p):
        """A point on the picture -> where it is on the canvas shown (through the zoom)."""
        c = view.cam
        if c is None:
            return p
        return ((p[0] - c.x) * view.w / c.w, (p[1] - c.y) * view.h / c.h)

    def activate_play(self, view, content, sp, t):
        if sp.kind != "peek":
            return False
        if self.peek is not None and self.peek.key == sp.target:
            return True
        self.close_peek()
        at = self.to_shown(view, sp.mark)
        self.peek = Peek(self, sp.target, sp.label, (at[0], at[1] - 40), t)
        return True

    def storm_started(self):
        self.close_peek()

    def paused(self):
        """The game is open in the desktop's place: the desktop steps aside and waits."""
        away = self.pausable and world.showing()
        if away:
            self.close_peek()
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
        import unlock
        if not unlock.can_go(key):  # not open yet (unlock.py): say who to beat, don't open the game
            self.denied = (unlock.reason(key), self.now())
            return
        world.open_world("go", place=key)

    def draw_map(self, s, t):
        """The minimap in the top screen's bottom-right corner, over the zoom; a place on it opens the
        game there (when it is open)."""
        import unlock
        self.minimap.locked = unlock.locked()
        rect = self.minimap.place(self.top)
        rect.bottomright = (self.top.w - 6, self.top.h - 6)
        m = self.top.screen_mouse()
        pointed = self.minimap.at(m)
        self.minimap.draw(s, self.top, HOME, pointed, t, place=False)

    def show_card(self, view, m, species, t, animal=None):
        """The card is drawn over the zoom, so it goes where the animal looks to be."""
        if view.cam is not None:
            m = self.to_shown(view, m)
            if animal is not None:
                animal = Seen(animal, lambda p, v=view: self.to_shown(v, p))
        self.card = self.make_card(Flat(view), m, species, t, animal)

    def above(self, view, content, t):
        if view is self.top:
            self.draw_map(view.canvas, t)
            self.draw_denied(view.canvas, t)
        if self.peek is not None and view is self.top:
            self.peek.draw(view.canvas, self.signs.font, view.screen_mouse(), t)
        if self.card is not None and self.card.view.base is view:
            self.card.draw(view.canvas, t)

    def play_right_click(self, t):
        """Right-click an animal in the peek: its card. Anywhere else in the peek: nothing."""
        if self.peek is None:
            return False
        m = self.top.screen_mouse()
        if not self.peek.inside(m):
            return False
        self.card = None
        found = self.peek.animal_at(m, t)
        if found is not None:
            self.card = self.make_card(Flat(self.top), m, found[1], t, found[0])
        return True

    def play_click_late(self, t):
        """With a peek open: its board goes there in the game, the rest of it does nothing, and a
        click anywhere else closes it (and goes on to whatever was clicked)."""
        m = self.top.screen_mouse()
        place = self.minimap.at(m)
        if place is not None or (m and self.minimap.rect and self.minimap.rect.collidepoint(m)):
            self.close_peek()
            if place is not None and place != HOME:
                self.to_place(place, t)
            return True
        if self.peek is None:
            return False
        if self.peek.inside(m):
            if self.peek.board.collidepoint(m):
                key = self.peek.key
                self.close_peek()
                self.to_place(key, t)
            return True
        self.close_peek()
        return False

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


class Flat:
    """A view as the card sees it: the pointer where it is on the canvas shown (the card is drawn
    over the zoom), and everything else the view's own."""

    def __init__(self, view):
        self.base = view

    def mouse(self):
        return self.base.screen_mouse()

    def __getattr__(self, name):
        return getattr(self.base, name)
