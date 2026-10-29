"""Updating the glade without losing your place (his ask, 2026-10-27).

After a rebuild the computer has a newer glade installed than the one running. Every few seconds
the running glade checks; when there is a newer one, a notice shows by the Thunderstorm button
(which shows too), and pressing Thunderstorm loads it (his choice): it notes where you are (the
place, the Forest Dex's page and creature, the boxes) and steps aside; the desktop starts the new
one at once (pkgs/glade's glade-desktop loop), and it opens where you were. The button is the only
way it ever updates, and it always works when pressed, even mid-battle (his rule, 2026-10-27).
"""

import json
import os
import shutil
import time

PATH = os.path.expanduser("~/.local/state/glade/resume.json")
FRESH = 600  # a note older than this (a reboot the next day, say) is not used


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

    def tick(self, glade, t):
        if t - self.checked < 5 or not RUNNING.startswith("/nix/store/"):
            return
        self.checked = t
        new = installed()
        self.waiting = bool(new) and new != RUNNING and new.startswith("/nix/store/")

    def load(self, glade):
        """Switch to the newer glade now (the Thunderstorm button), whatever is going on."""
        if not self.waiting:
            return False
        save(glade)
        os._exit(0)  # the desktop starts the new glade straight away


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
        if d.get("place") and d["place"] != glade.here.key and not glade.desktop:  # (the desktop is home only)
            glade.here = glade.scene(d["place"])
        glade.history = list(d.get("history", []))
        if "dex" in d:
            glade.dex = Dex(glade.signs.font, None, t)
            glade.dex.page, glade.dex.pick, glade.dex.tab = d["dex"]["page"], d["dex"]["pick"], d["dex"]["tab"]
        if d.get("boxes"):
            glade.board = Storage(glade.signs.font, t)
    except Exception:  # an old note that no longer fits: just start at home
        pass
