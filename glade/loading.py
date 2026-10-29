"""Loading the far places a little at a time (his ask, 2026-10-28).

Wander used to stutter for a while: the places were built on a side thread, but Python runs
one thread at a time, so every build took turns with the picture. Now the side thread only
works in the gaps between frames: the glade opens the gate when a frame is done
(`between_frames`), and the builder stops at the next `breathe()` when the gap is over. The
drawing code calls `breathe()` often (art.py), so the picture always comes first.

Every place is loaded, nearest first, and a bar under the Wander board shows how far it has
got (world.draw_loading), so he never has to guess whether it is all there.
"""

import threading
import time

SLACK = 0.008  # leave this much of each gap free, so the next frame starts on time


class Stopped(Exception):
    """Raised inside the builder when he went back to the desktop: the build is dropped."""


class Gate:
    def __init__(self):
        self.until = 0.0  # the builder may work until then
        self.open = threading.Event()
        self.side = None  # the builder thread's ident
        self.rush = False  # the picture is waiting for a place: build flat out
        self.stop = False


gate = Gate()


def breathe(need=0.0):
    """Called all through the drawing code; a pause point for the builder, nothing otherwise.
    `need`: the next step takes about this long in one go, so only start it if it fits in
    what is left of this gap (or at the start of the next one)."""
    g = gate
    if threading.get_ident() != g.side:
        return
    if g.stop:
        raise Stopped
    while not g.rush and time.monotonic() + need >= g.until:
        g.open.clear()
        if g.rush or time.monotonic() + need < g.until:  # opened meanwhile
            break
        if g.open.wait(0.25) and need:  # a new gap: a long step starts now, the best it can do
            break
        if g.stop:
            raise Stopped


def between_frames(next_frame):
    """A frame is on screen: the builder may use the time until the next one."""
    gate.until = next_frame - SLACK
    gate.open.set()


class Rush:
    """`with Rush():` the picture needs a place now, so the builder runs flat out meanwhile."""

    def __enter__(self):
        gate.rush = True
        gate.open.set()

    def __exit__(self, *exc):
        gate.rush = False
