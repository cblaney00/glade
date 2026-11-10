"""Which places you may walk to in the game (2026-11-10, his rule).

You start in the Glade and may go to the places next to it (scenes.LINKS); beating a place's gym
leader opens the places next to that one, so you choose which way to go. So a place is open when it
is the Glade, its gym is beaten, or it is next to the Glade or a beaten place. The Battle Tower is
always open: it has no gym, and it is where a new player gets their starter. His own badges count
as they are (his pick: beaten places and the ones next to them).

Everything that moves you goes through Game.go, which asks `can_go`; path boards, the minimap and
the badge case show a locked place dimmed, with a padlock and who to beat first (`reason`).
"""

import os

from scenes import LINKS, MAP

HOME = "glade"
ALWAYS = {HOME, "tower"}

_seen = {"stamp": None, "badges": ()}


def badges():
    """The gyms beaten, read from the save only when it has changed."""
    from team import Collection, STATE as SAVE
    try:
        stamp = os.stat(SAVE).st_mtime_ns
    except OSError:
        stamp = None
    if stamp != _seen["stamp"] or stamp is None:
        _seen["stamp"] = stamp
        _seen["badges"] = tuple(Collection().badges)
    return _seen["badges"]


def neighbours(key):
    return [b if a == key else a for a, b in LINKS if key in (a, b)]


def cleared(won=None):
    won = badges() if won is None else won
    return {HOME} | set(won)


def open_places(won=None):
    done = cleared(won)
    out = set(ALWAYS) | done
    for k in done:
        out.update(neighbours(k))
    return out


def can_go(key, won=None):
    return key in open_places(won)


def locked(won=None):
    """Every place not open yet."""
    return frozenset(MAP) - open_places(won)


def reason(key):
    """What opens a locked place: the gym of a place next to it ("Beat Leader Marisel first"), or,
    when none next to it is open yet, which place has to open first."""
    from gyms import GYMS
    from minimap import Minimap
    near = neighbours(key)
    for n in near:
        if n in open_places() and n in GYMS:
            return f"Beat {GYMS[n][0]} first"
    return f"Open {Minimap.NAMES.get(near[0], near[0])} first" if near else "Not open yet"
