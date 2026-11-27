"""Updating the glade without losing your place (his ask, 2026-10-27).

After a rebuild the computer has a newer glade installed than the one running. Every few seconds
the running glade checks; when there is a newer one, a notice shows by the Thunderstorm button
(which shows too), and pressing Thunderstorm loads it (his choice): it notes where you are (the
place, the Forest Dex's page and creature, the boxes) and steps aside. The desktop is started
again at once by pkgs/glade's glade-desktop loop; the game (world.py) starts the new version of
itself in its place (game.Game.restart), and it opens where you were. The button is the only
way it ever updates, and it always works when pressed, even mid-battle (his rule, 2026-10-27).

Thunderstorm always starts the glade afresh now, newer version or not (his ask, 2026-11-27: a screen
that blinked off came back black, and the button didn't fix it). The storm still comes: the fresh
glade finds the STORM note and starts it straight away.
"""

import json
import os
import shutil
import time

PATH = os.path.expanduser("~/.local/state/glade/resume.json")
FRESH = 600  # a note older than this (a reboot the next day, say) is not used
STORM = os.path.expanduser("~/.local/state/glade/storm-next")  # the fresh glade starts with a storm


def installed():
    """The store folder of the glade that is installed now (what a fresh start would run)."""
    exe = shutil.which("glade") or "/etc/profiles/per-user/%s/bin/glade" % os.environ.get("USER", "")
    try:
        return os.path.dirname(os.path.dirname(os.path.realpath(exe)))
    except OSError:
        return None


RUNNING = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # .../share/glade/resume.py


class Updater:
    def __init__(self):
        self.checked, self.waiting = -10.0, False
        self.storm_due = storm_note()

    def tick(self, glade, t):
        if self.storm_due:  # Thunderstorm restarted us: its storm comes now
            self.storm_due = False
            glade.thunderstorm(t)
        if t - self.checked < 5 or not RUNNING.startswith("/nix/store/"):
            return
        self.checked = t
        new = installed()
        self.waiting = bool(new) and new != RUNNING and new.startswith("/nix/store/")

    def load(self, glade):
        """Start the glade afresh now (the Thunderstorm button), the newer one if there is one,
        whatever is going on; the storm comes once it is back."""
        try:
            os.makedirs(os.path.dirname(STORM), exist_ok=True)
            with open(STORM, "w") as f:
                f.write(str(time.time()))
        except OSError:
            pass
        if hasattr(glade, "restart"):  # the game: it opens where you were, in its new version
            save(glade)
            glade.restart()
        os._exit(0)  # the desktop: its loop starts the new glade straight away


def storm_note():
    """Whether the glade was just restarted by Thunderstorm (and so owes a storm)."""
    try:
        with open(STORM) as f:
            when = float(f.read() or 0)
        os.remove(STORM)
    except (OSError, ValueError):
        return False
    return time.time() - when < 60


def save(glade):
    d = dict(when=time.time(), place=glade.here.key, history=list(glade.history[-20:]))
    if glade.dex is not None:
        d["dex"] = dict(page=glade.dex.page, pick=glade.dex.pick, tab=glade.dex.tab)
    if type(glade.board).__name__ == "Storage":
        d["boxes"] = True
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(d, f)


def restore(glade):
    try:
        with open(PATH) as f:
            d = json.load(f)
        os.remove(PATH)
    except (OSError, ValueError):
        return
    if time.time() - d.get("when", 0) > FRESH:
        return
    from dex import Dex
    from storage import Storage
    t = time.monotonic() - glade.t0
    try:
        if d.get("place") and d["place"] != glade.here.key:
            glade.here = glade.scene(d["place"])
        glade.history = list(d.get("history", []))
        if "dex" in d:
            glade.dex = Dex(glade.signs.font, None, t)
            glade.dex.page, glade.dex.pick, glade.dex.tab = d["dex"]["page"], d["dex"]["pick"], d["dex"]["tab"]
        if d.get("boxes"):
            glade.board = Storage(glade.signs.font, t)
    except Exception:  # an old note that no longer fits: just start at home
        pass
