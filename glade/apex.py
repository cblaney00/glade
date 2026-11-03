"""The moon's words, and the animals a predator can eat.

Click the moon (its halo swells: it is listening) and type "apex" (a Munchling comes and eats
everyone: munch.py, his redesign of 2026-11-03 that replaced the violet jelly blob) or "battle"
(battle.py). `Prey`/`find_prey` are the animals in a place, also used by battles and storms.

Everything here is in one shared coordinate space: the top screen's canvas as it is, and
the lower screen's canvas below it, shifted by OFFSET (the scenes are drawn to that
layout: lower x = upper x - 80).
"""

import math

import pygame

from art import glow, mix
from life import q, swell

OFFSET = (80, 540)

GOO = (170, 255, 90)          # fluorescent acid green
GOO_HI = (232, 255, 200)
INK = (14, 8, 24)
SKIN = (58, 38, 88)           # deep night violet
EYE = (238, 255, 226)
LILY = (70, 150, 110)

TIME_LIMIT = 30               # after this, whatever is left is finished off in a volley
WORD = "apex"
WORDS = (WORD, "battle")  # the moon also listens for "battle" (battle.py)


def ease(f):
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


# --- the animals it can eat ------------------------------------------------------------

class Prey:
    """One animal: where it is (shared coordinates), how to make it vanish and come back."""

    def __init__(self, obj, low, kind):
        self.obj, self.low, self.kind = obj, low, kind
        if kind == "fish":
            self.color = obj.colors[0]
        else:
            self.color = getattr(obj, "color", None) or getattr(obj, "body", None) or (200, 200, 220)
        self.mimic = "lily" if kind == "fish" else None
        self.eaten = False

    def pos(self):
        o = self.obj
        name = type(o).__name__
        if name == "Slug":
            x, y = o.track.at(o.d)[:2]
        elif name in ("Millipede", "Critter", "Fish"):
            pts = getattr(o, "pts", None)
            x, y = pts[0][:2] if pts else o.track.at(o.d)[:2]
        elif name == "HollowSquid":
            x, y = o.x, o.y - 12
        else:
            x, y = o.x, o.y
        if self.low:
            return x + OFFSET[0], y + OFFSET[1]
        return x, y

    def hide(self):
        self.obj.gone = True
        self.eaten = True

    def show(self):
        self.obj.gone = False


def find_prey(scene, lower):
    prey, swarms = [], []
    for content, low in ((scene, False), (lower, True)):
        if content is None:
            continue
        things = list(getattr(content, "lives", [])) + list(getattr(content, "parts", []))
        seen = set()
        for o in things:
            if id(o) in seen:
                continue
            seen.add(id(o))
            if getattr(o, "gone", False):  # sheltering from a storm (storm.py), or in a battle
                continue
            name = type(o).__name__
            if name in ("Squid", "Nibbler", "HollowSquid", "Flier"):
                prey.append(Prey(o, low, "fly"))
            elif name in ("Slug", "Millipede", "Critter", "Walker"):
                prey.append(Prey(o, low, "crawl"))
            elif name == "Fireflies":
                swarms.append((o, low))
        pond = getattr(content, "pond", None)
        if pond is not None and hasattr(pond, "fish"):
            for f in (f for f in pond.fish if not getattr(f, "gone", False)):
                prey.append(Prey(f, low, "fish"))
    return prey, swarms


# --- listening for the word ------------------------------------------------------------

class Listener:
    """After a click on the moon: collects what is typed for a while."""

    LISTEN = 10.0

    def __init__(self):
        self.until = -1.0
        self.typed = ""
        self.heard_at = -99.0

    def start(self, t):
        self.until, self.typed = t + self.LISTEN, ""

    def listening(self, t):
        return t < self.until

    def key(self, ch, t):
        """Returns the word, once one of WORDS has just been typed (else None)."""
        if not self.listening(t):
            return None
        self.typed = (self.typed + ch.lower())[-max(map(len, WORDS)):]
        for word in WORDS:
            if self.typed.endswith(word):
                self.until, self.heard_at = -1.0, t
                return word
        return None

    def draw_moon(self, s, moon, t):
        """The moon's halo swells while it listens, and dims for a moment once it hears."""
        if moon is None:
            return
        x, y, r = moon
        if self.listening(t):
            # lit up and pulsing while it listens, so it is clear a word can be typed
            k = 0.75 + 0.25 * math.sin(t * 2.2)
            glow(s, x, y, r * 6, (180, 200, 255), q(70 * k))
            glow(s, x, y, r * 3, (220, 230, 255), q(150 * k))
            pygame.draw.circle(s, (250, 250, 255), (x, y), r)
            pygame.draw.circle(s, mix((250, 250, 255), (200, 220, 255), k), (x, y), r + 2, 1)
        k = swell(t - self.heard_at, 0.6, 1.6)
        if k > 0:
            # the moon goes dark for a moment
            pygame.draw.circle(s, mix((236, 236, 255), (20, 18, 50), k), (x, y), r)
