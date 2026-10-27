"""Hiding while he plays — and the two boards that go with it.

When a game (any window) fills a screen, the glade stops drawing that screen: nobody can see
it, so it is left as it was. If the game is still full screen after half a minute, every animal
out where he is goes into hiding (diggers sink into the ground, fliers fly off, koi dive), the
same way they shelter from a storm. When he comes back, they peek out again one by one over
about half a minute (his picks, 2026-10-27).

The "Keep animals out" board (lower screen, top-left) switches the hiding off; the animals
still come and go over time as usual. It is remembered across restarts. "Your party" opens the
creature boxes (storage.py)."""

import json
import os
import random

import pygame

from battle import TEXT, cloth
from storm import Shelter, roster
from team import STATE

WAIT = 30.0     # seconds of full-screen game before they hide
BACK = 28.0     # how long they take to all come back out
SETTINGS = os.path.join(os.path.dirname(STATE), "settings.json")


def load_keep_out():
    try:
        with open(SETTINGS) as f:
            return bool(json.load(f).get("keep_out", False))
    except (OSError, ValueError, AttributeError):
        return False


def save_keep_out(on):
    try:
        os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
        try:
            with open(SETTINGS) as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        data["keep_out"] = bool(on)
        tmp = SETTINGS + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, SETTINGS)
    except OSError:
        pass


class Hiding:
    """Everyone out where he is goes into hiding; later they come back, one at a time."""

    def __init__(self, glade, t, keep):
        self.rng = random.Random()
        self.scene = glade.here
        self.low = glade.lower() if glade.bottom else None
        self.moves, self.hidden = [], []
        self.returning = False
        n = 0
        for content, low in ((self.scene, False), (self.low, True)):
            if content is None:
                continue
            pond = getattr(content, "pond", None)  # the koi dive too, as in a storm
            for o in list(roster(content)) + list(getattr(pond, "fish", []) if pond is not None else []):
                if not getattr(o, "gone", False) and not any(o is k for k in keep):
                    self.moves.append(Shelter(o, low, True, t + n * 0.12 + self.rng.uniform(0, 0.3), self.rng))
                    self.hidden.append((o, low))
                    n += 1

    @property
    def done(self):
        return self.returning and all(m.done for m in self.moves)

    def come_back(self, t):
        """He is back: they peek out one after another, in a random order."""
        if self.returning:
            return
        self.settle()
        self.returning = True
        self.rng.shuffle(self.hidden)
        gap = min(2.0, BACK / max(1, len(self.hidden)))
        self.moves = [Shelter(o, low, False, t + 1.0 + i * gap + self.rng.uniform(0, gap * 0.5), self.rng)
                      for i, (o, low) in enumerate(self.hidden)]

    def settle(self):
        for m in self.moves:
            m.begun = m.done = True
            m.obj.gone = m.out
        self.moves = []

    def finish(self):
        """He walked off (or a storm came): whoever was hiding is simply out again."""
        self.settle()
        for o, _ in self.hidden:
            o.gone = False
        self.hidden = []
        self.returning = True

    def update(self, t):
        for m in self.moves:
            m.update(t)

    def draw(self, s, low, t, scratch):
        for m in self.moves:
            m.draw(s, low, t, scratch)


# --- the two boards, under Predator vision and the Forest Dex -------------------------

KEEP = (170, 214, 120)
PARTY = (150, 190, 255)


def keep_rect(view):
    return pygame.Rect(8, 60, 150, 22)


def party_rect(view):
    return pygame.Rect(8, 86, 150, 22)


def draw_buttons(s, view, font, keep_out):
    m = view.mouse()
    # "Keep animals out": a switch, a little leaf that lights up while it is on
    r = keep_rect(view)
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, KEEP, hot=hot or keep_out, alpha=230)
    lx, ly = r.x + 13, r.centery
    leaf = (250, 255, 200) if keep_out else (110, 140, 90)
    pygame.draw.ellipse(s, leaf, (lx - 6, ly - 4, 12, 8))
    pygame.draw.line(s, (60, 80, 50), (lx - 5, ly), (lx + 5, ly))
    label = "Animals stay out" if keep_out else "Keep animals out"
    img = font.render(label, False, (255, 255, 255) if hot or keep_out else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))
    # "Your party": six little orbs
    r = party_rect(view)
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, PARTY, hot=hot, alpha=230)
    for i in range(6):
        cx, cy = r.x + 6 + (i % 3) * 5, r.centery - 3 + (i // 3) * 6
        pygame.draw.circle(s, (240, 246, 255), (cx, cy), 2)
    img = font.render("Your party", False, (255, 255, 255) if hot else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))
