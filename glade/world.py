"""The desktop and the game: two programs, one glade (Lando's rule, his picks, 2026-10-29).

The **desktop** (`glade`, desktop.py) is all looks: the home clearing with its apps, animals,
Thunderstorm, Hide animals, the badge case and the Claude panel, and only storm.CAP creature
families out. The **game** (`glade --game`, game.py) is all the play: every place, paths and
minimap, Predator vision, stats cards, battles, the Dex, your party, the Tower and gyms. Both are
built on the same shared code (main.Glade), so nothing is written twice.

The desktop's play boards open the game straight at that thing (`open_world`, handed over in
$XDG_RUNTIME_DIR/glade-world.ask): Wander, Forest Dex, Your party, a badge-case gem, a right-click
on an animal, the moon. While the game is open on a desktop it takes the desktop's place, behind
the windows on both screens (his pick), and the desktop steps aside; its Rest board closes it.
On a computer without the Glade desktop the game is an ordinary window with both screens in it.

Only one game at a time: it keeps its process id in $XDG_RUNTIME_DIR/glade-world.pid (the desktop
keeps its own in glade-desktop.pid, so the game knows whether it has a desktop to stand in for).
"""

import json
import os
import signal
import subprocess
import sys
import time

import pygame

import corner

from battle import TEXT, cloth

RUN = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
PID = os.path.join(RUN, "glade-world.pid")
DESKTOP_PID = os.path.join(RUN, "glade-desktop.pid")
ASK = os.path.join(RUN, "glade-world.ask")
READY = os.path.join(RUN, "glade-world.ready")  # the game is on screen (the desktop steps aside then)
CLASS = "glade-world"  # the game window's class (when it is a window)


def _pid(path=PID):
    try:
        with open(path) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


_seen = [-10.0, False, False]


def is_open():
    """Whether the game is running (looked at twice a second at most: it is asked every frame)."""
    now = time.monotonic()
    if now - _seen[0] > 0.5:
        _seen[0], _seen[1] = now, _pid() is not None
        _seen[2] = _seen[1] and os.path.exists(READY)
    return _seen[1]


def showing():
    """Whether the game is running and already on screen."""
    is_open()
    return _seen[2]


def mark_ready():
    try:
        open(READY, "w").close()
    except OSError:
        pass


def open_world(do=None, species=None, place=None):
    """Open the game at `do`: "dex" (at `species`' page), "party", "card" (`species`' stats),
    "moon" (listening for a word), "go" (to `place`), or just open it. Already open: it does that."""
    try:
        with open(ASK, "w") as f:
            json.dump(dict(do=do, species=species, place=place), f)
    except OSError:
        pass
    if _pid() is not None:
        if not desktop_running():  # a window: bring it forward
            try:
                subprocess.Popen(["hyprctl", "dispatch", "focuswindow", f"class:^({CLASS})$"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass
        return
    args = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), "--game"]
    try:
        subprocess.Popen(args, start_new_session=True, stdout=None, stderr=None)
        _seen[0], _seen[1], _seen[2] = time.monotonic(), True, False
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


def claim(path=PID):
    """Called by the game (or the desktop, with DESKTOP_PID) itself: False if one is running already."""
    pid = _pid(path)
    if pid is not None and pid != os.getpid():
        return False
    with open(path, "w") as f:
        f.write(str(os.getpid()))
    return True


def release(path=PID):
    try:
        if _pid(path) == os.getpid():
            os.remove(path)
            if path == PID and os.path.exists(READY):
                os.remove(READY)
    except OSError:
        pass


def desktop_running():
    return _pid(DESKTOP_PID) is not None


def close_world():
    pid = _pid()
    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    _seen[0], _seen[1], _seen[2] = time.monotonic(), False, False


def find_animal(scene, species):
    """An animal of `species` in this place (its family, failing that), brought out if it was
    sheltering: the desktop's animal stands for one of the game's own."""
    from battle import animals
    from storm import family
    found = [(a, sp) for a, sp in animals(scene, None) if not a.low and type(a).__name__ != "Perched"]
    for match in (lambda sp: sp == species, lambda sp: family(sp) == family(species)):
        picks = [f for f in found if match(f[1])]
        picks.sort(key=lambda f: bool(getattr(f[0].obj, "gone", False)))
        if picks:
            a, sp = picks[0]
            a.obj.gone = False
            return a, sp
    return None


# --- the board, under the badge case ----------------------------------------------------

WANDER = (196, 160, 255)


def rect(view):
    return corner.rect("world")  # under the badge case, open or shut


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


def loading_rect(view):
    r = rect(view)
    return pygame.Rect(r.x, r.bottom + 4, r.w, 22)


def draw_loading(s, view, font, done, total, since, t):
    """Under the Wander board while the far places load (loading.py): how many are ready, and
    a filling bar, so he never has to guess. When all are in it says so for a few seconds,
    then goes. `since`: when the last one came in (None while loading)."""
    if since is not None and t - since > 4:
        return
    r = loading_rect(view)
    full = since is not None
    cloth(s, r, (150, 236, 190) if full else WANDER, hot=full, alpha=215)
    msg = "Every place is ready" if full else f"Loading places {done}/{total}"
    img = font.render(msg, False, (255, 255, 255) if full else TEXT)
    s.blit(img, (r.x + 7, r.y + 2))
    bar = pygame.Rect(r.x + 7, r.bottom - 6, r.w - 14, 3)
    pygame.draw.rect(s, (60, 40, 96), bar)
    k = 1.0 if full else done / max(1, total)
    pygame.draw.rect(s, (255, 255, 255) if full else (238, 222, 255), (bar.x, bar.y, max(1, int(bar.w * k)), bar.h))
