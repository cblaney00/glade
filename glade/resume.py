"""Updating the glade without losing your place (his ask, 2026-10-27).

After a rebuild the computer has a newer glade installed than the one running. Every few seconds
the running glade checks; when there is a newer one and nothing is happening that can't be picked
up again (a battle, a Battle Tower run, a creature evolving), it notes where you are (the place,
the Forest Dex's page and creature, the boxes) and steps aside. The desktop starts the new one at
once (pkgs/glade's glade-desktop loop), and it opens where you were.
"""

import json
import os
import shutil
import time

PATH = os.path.expanduser("~/.local/state/glade/resume.json")
FRESH = 600  # a note older than this (a reboot the next day, say) is not used


def busy(glade):
    return glade.arena is not None or glade.run is not None or glade.evolution is not None


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
        self.checked = -10.0

    def tick(self, glade, t):
        if t - self.checked < 5 or not RUNNING.startswith("/nix/store/"):
            return
        self.checked = t
        new = installed()
        if not new or new == RUNNING or not new.startswith("/nix/store/") or busy(glade):
            return
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
