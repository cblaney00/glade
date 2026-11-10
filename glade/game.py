"""The Glade game: all the play (world.py; Lando's rule, his picks, 2026-10-29).

Every place with its paths and the minimap, the far places loading on the side, Predator vision,
stats cards, wild battles, the moon's secrets, the Forest Dex, your party, the Battle Tower and
the gyms. It is built on the same Glade as the desktop (main.Glade) and adds only the play.

Run:  python glade/main.py --game
On his desktop it takes the desktop's place behind the windows on both screens (wayland.py);
anywhere else it is an ordinary window with both screens in it, one above the other (`window`).
"""

import os
import random
import sys
import threading

import pygame

import hiding
import badges
import carry
import book
import nav
import loading
import resume
import storm
import vision
import world
import munch
from apex import Listener
from battle import Arena
from dex import Dex
from evolve import EVOLVES, Evolution
from lower import Lower
from minimap import Minimap  # noqa: F401 (others find it here too)
import unlock
from main import HOME, Glade
from scenes import BUILDERS, LINKS
from starter import StarterBoard
from storage import Storage
from team import Collection
from tower import Run, TowerBoard
from art import H, W


NEAR = 2    # places this many paths away or less are kept ready (loaded on the side)
FORGET = 3  # places further away than this are let go of


class Game(Glade):
    def __init__(self, screen, rect, lower=None):
        # the far places, built on the side while he plays, so the game never freezes (warm)
        self.ready, self.ready_lock, self.warmer, self.gen = {}, threading.Lock(), None, 0
        self.loaded_at = None  # when the last far place came in (for the loading bar)
        storm.new_season(random.Random())  # each time the game opens, a new season (storm.py)
        super().__init__(screen, rect, lower)
        self.minimap = Minimap(self.signs.font)
        self.listener = Listener()  # the easter eggs (apex.py): click the moon, type the word
        self.hunt = None  # a Munchling's visit (munch.py), from its board or the moon's word "apex"
        self.arena = None  # a battle (battle.py)
        self.card = None   # an animal's battle stats (battle.py), from a right-click
        self.dex = None    # the Forest Dex (dex.py)
        self.board = None  # the Tower's, a gym's or the starter's board, or your creature boxes (storage.py)
        self.run = None    # a go at the Battle Tower, a trainer or a gym
        self.vision = None  # Predator vision (vision.py), for a few seconds after its button
        self.evolution = None  # an animal evolving (evolve.py), from its stats card
        self.running = True
        self.quit = None  # how to close the game (set by whatever runs it)
        self.asked_at = 0.0
        storm.FAMILIES = None  # every family may come out
        if self.bottom:
            self.lower()
        carry.load(self)  # the animals the desktop had out at home, the very same ones
        resume.restore(self)  # after an update: where he was
        self.follow(world.take(), self.now())  # what the desktop opened it for

    # --- the far places -------------------------------------------------------------------
    def scene(self, key):
        self.take_ready(key)
        return super().scene(key)

    def lower(self):
        self.take_ready(self.here.key)
        return super().lower()

    def steps(self):
        """How many paths away each place is from where he is."""
        far, order = {self.here.key: 0}, [self.here.key]
        for key in order:
            for a, b in LINKS:
                if key in (a, b):
                    other = b if a == key else a
                    if other not in far and other in BUILDERS:
                        far[other] = far[key] + 1
                        order.append(other)
        return far

    def nearest(self):
        """The places kept ready (NEAR paths away or less), nearest first."""
        far = self.steps()
        return sorted((k for k in far if far[k] <= NEAR), key=far.get)

    def loading(self):
        """(nearby places loaded, nearby places) for the bar under Rest."""
        with self.ready_lock:
            ready = set(self.ready)
        near = set(self.nearest())
        return len((set(self.scenes) | ready) & near), len(near)

    def forget(self):
        """Let go of places more than FORGET paths away (his pick, 2026-11-02: much less memory;
        walking back to one builds it again, a short pause). Never one something is happening in."""
        far = self.steps()
        busy = {getattr(getattr(x, "scene", None), "key", None) for x in (self.arena, self.storm, self.hiding, self.hunt)}
        for key in [k for k in self.scenes if far.get(k, FORGET + 1) > FORGET and k != self.here.key and k not in busy]:
            del self.scenes[key]
            self.lowers.pop(key, None)

    def idle_work(self, t):
        self.warm()

    def warm(self):
        """Load every place, nearest first, so going anywhere is instant. Each takes about a
        second, so a side thread builds them a little at a time, only in the gaps between frames
        (loading.py): the picture never waits, and the bar under Rest shows how far it is."""
        for key in list(self.ready):
            self.take_ready(key)
        if self.warmer is not None and self.warmer.is_alive():
            return True
        if self.building.acquire(blocking=False):
            try:
                self.forget()
            finally:
                self.building.release()
        todo = [k for k in self.nearest() if k not in self.scenes]
        if not todo:
            if self.loaded_at is None:
                self.loaded_at = self.now()
            return False
        gen, size = self.gen, (self.bottom.w, self.bottom.h) if self.bottom else None
        loading.gate.stop = False

        def build():
            loading.gate.side = threading.get_ident()
            try:
                for key in todo:
                    with self.building:
                        if self.gen != gen:
                            return
                        if key in self.scenes:  # (he walked there first)
                            continue
                        sc = BUILDERS[key]()
                        low = Lower(sc, *size) if size else None
                        with self.ready_lock:
                            if self.gen == gen:
                                self.ready[key] = (sc, low)
            except loading.Stopped:
                pass
            finally:
                loading.gate.side = None

        self.warmer = threading.Thread(target=build, daemon=True)
        self.warmer.start()
        return True

    def take_ready(self, key):
        """A place the side thread has finished: it joins the game."""
        with self.ready_lock:
            got = self.ready.pop(key, None)
        if got is not None and key not in self.scenes:
            self.scenes[key] = got[0]
            if got[1] is not None and key not in self.lowers:
                self.lowers[key] = got[1]

    # --- opening and closing --------------------------------------------------------------
    def follow(self, req, t):
        """Do what the desktop asked for (world.open_world)."""
        if not req:
            return
        do, species = req.get("do"), req.get("species")
        self.popup = None
        if do in ("dex", "party", "card", "battle") and self.board is not None:
            self.board.close()
            self.board = None
        if do in ("dex", "party", "card", "battle"):
            self.dex = self.card = None
        if do == "dex":
            self.dex = Dex(self.signs.font, species, t)
        elif do == "party":
            self.board = Storage(self.signs.font, t)
        elif do == "moon":
            self.moon_clicked(t)
        elif do == "go" and req.get("place") in BUILDERS:
            self.go(req["place"])
        elif do in ("card", "battle") and species:
            if self.here.key != HOME:  # the animal was at home
                self.go(HOME, remember=False)
            found = world.find_animal(self.here, species)
            if found is None or found[1] != species:
                self.dex = Dex(self.signs.font, species, t)  # nobody just like it here: its Dex page
                return
            a = found[0]
            if do == "battle" and self.arena is None and Collection().members():
                world.become(a.obj, req)  # the very one clicked on the desktop: its IVs, nature, level
                low = self.lower() if self.bottom else None
                self.arena = Arena(self.here, low, self.signs.font, t, mode="wild",
                                   foe=(a, species, self.here), mine=Collection().members())
                self.arena.mouse = self.top.mouse
            else:
                self.show_card(self.top, a.pos(), species, t, a)

    def rest(self, t):
        """Rest: the game closes and the desktop comes back."""
        for thing in (self.arena, self.hunt, self.storm, self.evolution, self.hiding):
            if thing is not None:
                thing.finish()
        if self.board is not None:
            self.board.close()
        loading.gate.stop = True
        self.running = False
        carry.save(self)  # the desktop takes the animals at home back
        world.release()
        if self.quit:
            self.quit()

    def restart(self):
        """A newer glade is installed (resume.Updater): the game starts again as the new one (the same
        process, so it keeps its claim and the desktop stays out of the way)."""
        new = os.path.join(resume.installed() or "", "bin", "glade")
        if os.path.exists(new):
            os.execv(new, [new, "--game"])
        os.execv(sys.executable, [sys.executable, os.path.join(os.path.dirname(__file__), "main.py"), "--game"])

    # --- the hooks (main.Glade) -----------------------------------------------------------
    def after_board(self, board, t):
        """A board has closed: begin the tower challenge, or open the boxes, if that was asked."""
        if getattr(board, "chosen", None) and board.then:
            board.then(t)
        elif getattr(board, "begin", False) and self.arena is None:
            self.run = board.make_run(self) if hasattr(board, "make_run") else Run(board.team(), self)
            self.arena = self.run.open(t)
        elif getattr(board, "boxes", False):
            self.board = Storage(self.signs.font, t)
        elif getattr(board, "go_to", None):  # the Glade Book's "Go there"
            self.go(board.go_to)
        elif getattr(board, "open_dex", False):  # the Glade Book's Forest Dex button
            self.dex = Dex(self.signs.font, None, t)

    def activate_play(self, view, content, sp, t):
        if sp.kind == "tower":  # the Battle Tower's door
            if self.arena is None:
                if Collection().members():
                    self.board = TowerBoard(self.signs.font, t)
                else:  # the very first visit: choose your starter, then on to the tower's board
                    self.board = StarterBoard(self.signs.font, t,
                                              then=lambda t: setattr(self, "board", TowerBoard(self.signs.font, t)))
            return True
        if sp.kind == "gym":  # a gym leader's banner stone (gyms.py)
            if self.arena is None:
                from gyms import GymBoard
                self.board = GymBoard(self.signs.font, t, sp.target)
            return True
        if sp.kind == "trainer":  # a trainer standing on the lower screen (trainers.py)
            if self.arena is None:
                from trainers import TrainerBoard
                self.board = TrainerBoard(self.signs.font, t, sp.target)
            return True
        if sp.kind == "elite":  # the Moonlit Hall's great door (elite.py)
            if self.arena is None:
                from elite import EliteBoard
                self.board = EliteBoard(self.signs.font, t)
            return True
        if sp.kind == "boxes":  # the shrine where your creatures are kept
            self.board = Storage(self.signs.font, t)
            return True
        return False

    def corner_free(self):
        return self.board is None and self.dex is None

    def corner(self, view, t):
        vision.draw_button(view.canvas, view, self.signs.font, self.vision is not None)
        munch.draw_button(view.canvas, view, self.signs.font, self.hunt is not None)
        hiding.draw_dex_button(view.canvas, view, self.signs.font)
        hiding.draw_buttons(view.canvas, view, self.signs.font, self.hide)
        badges.draw(view.canvas, view, self.signs.font, t)
        nav.draw(view.canvas, view, self.signs.font, t)
        world.draw_button(view.canvas, view, self.signs.font, True)
        world.draw_loading(view.canvas, view, self.signs.font, *self.loading(), self.loaded_at, t)

    def corner_click(self, view, m, t):
        if vision.button_rect(view).collidepoint(m):
            if self.vision is None:
                self.vision = vision.Vision(t)
            return True
        if munch.button_rect(view).collidepoint(m):
            self.call_munchling(t)
            return True
        if hiding.dex_rect(view).collidepoint(m):
            self.popup, self.card = None, None
            self.dex = Dex(self.signs.font, None, t)  # the quick way into the Forest Dex
            return True
        if hiding.party_rect(view).collidepoint(m):
            self.popup, self.card = None, None
            self.board = Storage(self.signs.font, t)  # your party, in the creature boxes
            return True
        if world.rect(view).collidepoint(m):
            self.rest(t)
            return True
        return False

    def to_place(self, key, t):
        self.go(key)

    def storm_started(self):
        self.card, self.dex = None, None

    def storm_blocked(self):
        return self.evolution is not None or self.hunt is not None

    def play_click(self, t):
        if self.board is not None:  # the tower's board or the boxes: like the dex
            m = self.top.mouse()
            board = self.board
            if m and board.rect.collidepoint(m):
                board.click(m)
            else:
                board.close()
            if board.closed:
                self.board = None
                self.after_board(board, t)
            return True
        if self.dex is not None:  # the dex takes clicks on it; one outside it closes it
            m = self.top.mouse()
            if m and self.dex.rect.collidepoint(m):
                self.dex.click(m)
                if self.dex.closed:
                    if getattr(self.dex, "boxes", False):
                        self.board = Storage(self.signs.font, t)
                    self.dex = None
            else:
                self.dex = None
            return True
        if self.card is not None:  # a click closes the stats card, opens the dex, or evolves it
            card, self.card = self.card, None
            m = card.view.mouse()
            if m and card.button.collidepoint(m):
                self.dex = Dex(self.signs.font, card.species, t)
            elif m and card.fight is not None and card.fight.collidepoint(m) and self.arena is None \
                    and not getattr(card, "locked", False):
                low = self.lower() if self.bottom else None  # a wild battle: your party against it
                self.arena = Arena(self.here, low, self.signs.font, t, mode="wild",
                                   foe=(card.animal, card.species, self.here), mine=Collection().members())
                self.arena.mouse = self.top.mouse
            elif m and card.evolve is not None and card.evolve.collidepoint(m) and self.evolution is None:
                self.evolution = Evolution(card.animal, card.species, t)
                self.evolution.font, self.evolution.scene = self.signs.font, self.here
            return True
        return False

    def play_click_late(self, t):
        return self.arena is not None and self.arena.click(self, t)

    def map_click(self, view, content, m, t):
        if view is self.map_view():
            place = self.minimap.at(m)
            if place is not None:
                self.go(place)
                return True
            if self.minimap.rect and self.minimap.rect.collidepoint(m):
                return True
            if self.minimap.rect and book.icon_rect(view, self.minimap.rect).collidepoint(m):
                self.popup, self.card = None, None
                self.board = book.Book(self.signs.font, t, self.here.key, self.scenes)  # the Glade Book
                return True
        if self.zoomed(view):  # zoomed in on a battle: only its path signs are there to click
            sp = view.hovered([sp for sp in content.spots if sp.kind == "go"])
            if sp is not None:
                self.activate(view, content, sp, t)
            return True
        return False

    def moon_clicked(self, t):
        self.listener.start(t)  # the moon listens...
        if self.on_listen:
            self.on_listen()

    def play_right_click(self, t):
        self.card = None
        if self.board is not None:
            self.board.close()
            self.board = None
            return True
        if self.dex is not None:
            self.dex = None
            return True
        return False

    def show_card(self, view, m, species, t, animal=None):
        evolves = EVOLVES.get(species) if animal is not None and self.evolution is None else None
        self.card = self.make_card(view, m, species, t, animal, evolves,
                                   fight=animal is not None and self.arena is None)  # every creature can be battled

    def typed(self, ch, t):
        """A letter typed while the moon is listening."""
        word = self.listener.key(ch, t)
        if word:
            if self.on_heard:
                self.on_heard()
            if word == "battle":
                if self.arena is None:
                    low = self.lower() if self.bottom else None
                    self.arena = Arena(self.here, low, self.signs.font, t)
                    self.arena.mouse = self.top.mouse
            else:
                self.call_munchling(t)

    def call_munchling(self, t):
        """A Munchling comes and eats every animal here, and new ones come out (munch.py)."""
        if self.hunt is None and self.storm is None and self.evolution is None:
            self.hunt = munch.Munch(self, t)

    def zoomed(self, view):
        """The top screen is zoomed in on a battle (battle.Arena.camera)."""
        return view is self.top and self.arena is not None and self.arena.zoomed

    def update_play(self, dt, t):
        if t - self.asked_at > 0.5:  # the desktop may ask for something while the game is open
            self.asked_at = t
            self.follow(world.take(), t)
        if self.hunt is not None:
            if self.hunt.done or self.hunt.scene is not self.here or self.storm is not None:
                self.hunt.finish()  # finished, or he went elsewhere: the new ones are simply out
                self.hunt = None
            else:
                self.hunt.update(dt, t)

    def update_play_late(self, dt, t):
        if self.evolution is not None:
            if self.evolution.scene is not self.here:
                self.evolution.finish()  # he walked off: it has simply evolved
                self.evolution = None
            elif self.evolution.done:
                self.evolution = None
            else:
                self.evolution.update(t)
        if self.arena is not None and self.arena.mode != "tower" and self.board is None:
            ready = self.arena.ready()  # a wild battle over: anyone who reached level 16 or 32 evolves
            if ready:
                from evolve_party import EvolveBoard
                self.board = EvolveBoard(self.signs.font, ready, t)
        if self.arena is not None:
            if self.arena.done:
                self.arena.finish()  # closed: everyone is home
                self.arena = None
            elif not self.fade_to:  # it comes along to whichever place he goes
                self.arena.scene = self.here
                self.arena.place(self.here)  # clear of this place's signs
                self.arena.lower = self.lower() if self.bottom else None
                self.arena.update(dt, t)

    def under(self, view, content, t):
        if view is self.top:
            self.listener.draw_moon(view.canvas, getattr(content, "moon", None), t)
        if self.hunt is not None:
            self.hunt.draw(view.canvas, view is self.bottom, t, self.storm_scratch)

    def seen(self, view, content, t):
        if self.vision is not None:
            if self.vision.done(t) or self.fade_to:
                self.vision = None
            else:
                self.vision.draw(view.canvas, view.w, view.h, self.here, self.lower() if self.bottom else None,
                                 view is self.bottom, t)

    def can_go(self, key):
        return unlock.can_go(key)

    def refused(self, key):
        self.denied = (unlock.reason(key), self.now())

    def lock_of(self, sp):
        if sp.kind == "go" and sp.target in unlock.locked():
            return unlock.reason(sp.target)
        return None

    def map_overlay(self, view, t):
        if view is self.top:
            self.draw_denied(view.canvas, t)
        if view is self.map_view():
            self.minimap.locked = unlock.locked()
            pointed = None if self.fade_to else self.minimap.at(view.mouse())
            self.minimap.draw(view.canvas, view, self.here.key, pointed, t)
            book.draw_icon(view.canvas, view, self.signs.font, self.minimap.rect, view.mouse(), t)

    def above(self, view, content, t):
        if self.arena is not None:
            self.arena.draw(view.canvas, view is self.bottom, t)
            if view is self.top:  # path signs stay on top of the battle board, and clickable
                m = view.mouse()
                paths = [sp for sp in content.spots if sp.kind == "go"] if self.zoomed(view) else self.arena.paths(content)
                for sp in paths:  # (a place first walked into mid-battle has no boards yet)
                    self.signs.prepare(sp, view.w, view.h)
                    self.signs.draw(view.canvas, sp, bool(m) and sp.boards[2].collidepoint(m), t)
        if self.card is not None and self.card.view is view:
            self.card.draw(view.canvas, t)
        if self.dex is not None and view is self.top:
            self.dex.draw(view.canvas, view.mouse(), t)
        if self.board is not None and view is self.top:
            self.board.draw(view.canvas, view.mouse(), t)
        if self.evolution is not None:
            self.evolution.draw(view.canvas, view is self.bottom, t)


# --- as a window, anywhere without the Glade desktop -------------------------------------------

LOWER_X = 80  # the lower screen sits this far in from the top one's left, as on his desk


def layout(game, size):
    """Both screens in one window, the top one above the lower one, as big as fits."""
    tw, th = W, H
    lw, lh = (game.bottom.w, game.bottom.h) if game.bottom else (0, 0)
    total_h = th + lh
    scale = min(size[0] / tw, size[1] / total_h)
    ox = (size[0] - tw * scale) / 2
    oy = (size[1] - total_h * scale) / 2
    game.top.rect = pygame.Rect(round(ox), round(oy), round(tw * scale), round(th * scale))
    if game.bottom:
        game.bottom.rect = pygame.Rect(round(ox + LOWER_X * scale), round(oy + th * scale),
                                       round(lw * scale), round(lh * scale))


def window():
    """The game as an ordinary window: both screens, one above the other (a computer without
    the Glade desktop, Lando's machines, or the desktop under X11)."""
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":  # (handed down from the desktop: it would never show)
        del os.environ["SDL_VIDEODRIVER"]
    os.environ["SDL_VIDEO_X11_WMCLASS"] = world.CLASS
    os.environ["SDL_VIDEO_WAYLAND_WMCLASS"] = world.CLASS
    pygame.init()
    dw, dh = pygame.display.get_desktop_sizes()[0]
    lw, lh = 800, 450
    scale = max(0.5, min((dw * 0.92) / W, (dh * 0.88) / (H + lh)))
    if scale >= 1:
        scale = int(scale)  # whole pixels when there is room
    pygame.display.set_caption("The Glade")
    screen = pygame.display.set_mode((round(W * scale), round((H + lh) * scale)), pygame.RESIZABLE)
    pygame.mouse.set_visible(False)
    game = Game(screen, pygame.Rect(0, 0, W, H), pygame.Rect(0, 0, lw, lh))
    game.show_panel = False
    game.resized = lambda size: (setattr(game, "screen", pygame.display.get_surface()), layout(game, size))
    layout(game, screen.get_size())
    from main import loop
    try:
        loop(game)
    finally:
        world.release()


def run():
    if not world.claim():  # already open: what was asked was handed over (world.open_world)
        return
    try:
        if os.environ.get("WAYLAND_DISPLAY") and world.desktop_running() and "--window" not in sys.argv:
            import wayland  # in the desktop's place, behind the windows, on both screens (his pick)
            return wayland.run(Game)
        return window()
    finally:
        world.release()
