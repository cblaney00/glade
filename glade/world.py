"""The rest of the Glade, as its own window (his ask, 2026-10-28).

The desktop is just the home clearing now: its apps, the Forest Dex, your party, the Claude
panel and the Thunderstorm. Everything further out — the far places, the paths and minimap,
the Battle Tower and every battle — is a game in its own window on the top screen:
`glade --world`. The "Wander" board under "Your party" opens it; while it is open that board
says "Rest" (on the desktop and in the window) and closes it again.

The desktop is all looks and no play (his rule, 2026-10-28): the Forest Dex and Your party
boards, right-clicking an animal (its stats card), and clicking the moon all open the game
straight at that thing (`open_world`, handed over in $XDG_RUNTIME_DIR/glade-world.ask).

Only one window at a time: it keeps its process id in $XDG_RUNTIME_DIR/glade-world.pid.
"""

import json
import os
import signal
import subprocess
import sys
import time

import pygame

from battle import TEXT, cloth

PID = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "glade-world.pid")
ASK = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "glade-world.ask")
CLASS = "glade-world"  # the window's class, for the desktop's window rules
WANDER = (196, 160, 255)


def _pid():
    try:
        with open(PID) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


_seen = [0.0, False]


def is_open():
    """Whether the window is open (looked at twice a second at most: it is asked every frame)."""
    now = time.monotonic()
    if now - _seen[0] > 0.5:
        _seen[0], _seen[1] = now, _pid() is not None
    return _seen[1]


def open_world(do=None, species=None):
    """Open the game at `do` — "dex" (at `species`' page), "party", "card" (`species`' stats),
    "battle" (against `species`), "moon" (listening for a word) — or just open it. Already
    open: it does that and comes to the front."""
    try:
        with open(ASK, "w") as f:
            json.dump(dict(do=do, species=species), f)
    except OSError:
        pass
    if _pid() is not None:
        try:
            subprocess.Popen(["hyprctl", "dispatch", "focuswindow", f"class:^({CLASS})$"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
        return
    args = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), "--world"]
    try:
        subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _seen[0], _seen[1] = time.monotonic(), True
    except OSError:
        pass


def take():
    """In the game: what the desktop last asked for (once), or None."""
    try:
        with open(ASK) as f:
            req = json.load(f)
        os.remove(ASK)
        return req
    except (OSError, ValueError):
        return None


def close_world():
    pid = _pid()
    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    _seen[0], _seen[1] = time.monotonic(), False


def claim():
    """Called by the window itself: False if one is open already."""
    if _pid() is not None:
        return False
    with open(PID, "w") as f:
        f.write(str(os.getpid()))
    return True


def release():
    try:
        if _pid() == os.getpid():
            os.remove(PID)
    except OSError:
        pass


# --- the board, under "Your party" ------------------------------------------------------

def rect(view):
    return pygame.Rect(8, 112, 150, 22)


def draw_button(s, view, font, open_now):
    """A lilac board with a little footpath; "Wander" or "Rest"."""
    r = rect(view)
    m = view.mouse()
    hot = bool(m) and r.collidepoint(m)
    cloth(s, r, WANDER, hot=hot or open_now, alpha=230)
    x, y = r.x + 7, r.centery
    for i, (dx, dy) in enumerate(((0, 4), (4, 1), (8, -2), (12, -5))):
        pygame.draw.ellipse(s, (250, 244, 255), (x + dx, y + dy - 1 + (i % 2), 4, 3))
    img = font.render("Rest" if open_now else "Wander", False, (255, 255, 255) if hot or open_now else TEXT)
    s.blit(img, (r.x + 26, r.centery - img.get_height() // 2))


def find_foe(scene, species):
    """An animal of `species` in this place (its family, failing that) to battle, brought out
    if it was sheltering."""
    from battle import animals
    from storm import family
    found = [(a, sp) for a, sp in animals(scene, None) if not a.low and type(a).__name__ != "Perched"]
    for match in (lambda sp: sp == species, lambda sp: family(sp) == family(species)):
        picks = [f for f in found if match(f[1])]
        picks.sort(key=lambda f: bool(getattr(f[0].obj, "gone", False)))
        if picks:
            a, sp = picks[0]
            a.obj.gone = False
            return a, species if sp == species else sp
    return None
