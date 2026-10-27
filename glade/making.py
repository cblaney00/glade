"""While new creatures are being made (his ask, 2026-10-27): a progress board in the lower
screen's top-right corner, and a little notice when they are all done.

Whoever is making them (a Claude session) writes ~/.local/state/glade/making.json:
    {"what": "Making new creatures", "done": 2, "total": 6, "names": ["Bramblit", "Sparkfly"],
     "now": "Runelet"}
`done` counts up as each one is finished; `names` are the finished ones; `now` is the one being
worked on, shown under the bar so it never looks stuck. When `done` reaches `total`, the board
turns into the notice, then goes. Deleting the file takes the board away. The glade looks at
the file about once a second.

The easy way to write it (his rule, 2026-10-27: update it after EVERY creature, not in jumps):
    python glade/making.py start 22 Cometail     # 22 to make, starting on Cometail
    python glade/making.py step Cometail Skyveil  # Cometail done, now on Skyveil
    python glade/making.py step Mossquake         # the last one: the notice goes up
"""

import json
import math
import os
import time

import pygame

from art import glow, mix
from battle import TEXT, cloth

PATH = os.path.expanduser("~/.local/state/glade/making.json")
MINT = (130, 255, 190)
NOTICE = 15.0    # seconds the "done" notice stays
STALE = 120.0    # a finished file older than this (e.g. after a restart) is not shown again


class Making:
    def __init__(self):
        self.state, self.mtime, self.checked = None, None, -10.0
        self.finished_at = None  # when the notice went up (monotonic), for the file seen now

    def poll(self, t):
        if t - self.checked < 1.0:
            return
        self.checked = t
        try:
            mtime = os.path.getmtime(PATH)
        except OSError:
            self.state, self.mtime = None, None
            return
        if mtime == self.mtime:
            return
        self.mtime = mtime
        try:
            with open(PATH) as f:
                d = json.load(f)
            total = max(1, int(d.get("total", 1)))
            self.state = dict(what=str(d.get("what", "Making new creatures")), total=total,
                              done=max(0, min(total, int(d.get("done", 0)))),
                              names=[str(n) for n in d.get("names", [])], now=str(d.get("now") or ""))
        except (OSError, ValueError, TypeError):
            return
        if self.state["done"] >= self.state["total"]:
            old = time.time() - mtime > STALE
            self.finished_at = None if old else t
            if old:
                self.state = None
        else:
            self.finished_at = None

    def draw(self, s, view, font, t, below_storm):
        self.poll(t)
        st = self.state
        if st is None:
            return
        y = 34 if below_storm else 8
        if self.finished_at is not None:
            self.notice(s, view, font, t - self.finished_at, y)
            return
        r = pygame.Rect(view.w - 172, y, 164, 50 if st["now"] else 36)
        cloth(s, r, MINT, alpha=230)
        img = font.render(st["what"], False, TEXT)
        s.blit(img, (r.x + 8, r.y + 3))
        bar = pygame.Rect(r.x + 8, r.y + 21, r.w - 52, 8)
        pygame.draw.rect(s, (24, 40, 46), bar, border_radius=3)
        f = st["done"] / st["total"]
        if f > 0:
            fill = bar.inflate(-2, -2)
            fill.w = max(2, round(fill.w * f))
            pygame.draw.rect(s, MINT, fill, border_radius=2)
            sx = fill.right - 1 - ((t * 20) % max(1, fill.w))  # a glint running along it
            pygame.draw.line(s, (240, 255, 248), (sx, fill.y), (sx, fill.bottom - 1))
            glow(s, fill.right, fill.centery, 9, MINT, 60 + round(30 * math.sin(t * 3)) // 10 * 10)
        n = font.render(f"{st['done']}/{st['total']}", False, TEXT)
        s.blit(n, (r.right - 8 - n.get_width(), bar.centery - n.get_height() // 2))
        if st["now"]:  # what is being made right now, with dots that keep moving
            dots = "." * (1 + int(t * 2) % 3)
            img = font.render(f"Now: {st['now']}{dots}", False, mix(TEXT, MINT, 0.4))
            s.blit(img, (r.x + 8, r.y + 33))

    def notice(self, s, view, font, a, y):
        if a > NOTICE:
            self.state = None
            return
        k = min(1.0, a / 0.4, (NOTICE - a) / 0.8)
        k = k * k * (3 - 2 * k)
        st = self.state
        lines = [f"{st['total']} new creatures are ready!"]
        names = st["names"]
        while names:  # their names, a few to a line
            row, names = names[:3], names[3:]
            lines.append(", ".join(row))
        w = max(font.size(line)[0] for line in lines) + 20
        r = pygame.Rect(0, 0, max(164, w), 10 + 14 * len(lines))
        r.topright = (view.w - 8 + round((1 - k) * 60), y)
        surf = pygame.Surface(view.canvas.get_size() if hasattr(view, "canvas") else s.get_size(), pygame.SRCALPHA)
        cloth(surf, r, MINT, hot=a < 2.0, alpha=235)
        glow(surf, r.x + 10, r.y + 11, 10, MINT, 90)
        for i, line in enumerate(lines):
            img = font.render(line, False, (255, 255, 255) if i == 0 else TEXT)
            surf.blit(img, (r.x + 10, r.y + 5 + 14 * i))
        surf.set_alpha(round(255 * k))
        s.blit(surf, (0, 0))


def _write(d):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f)
    os.replace(tmp, PATH)


if __name__ == "__main__":  # python making.py start TOTAL [NOW] | step DONE_NAME [NOW] | stop
    import sys
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "start":
        _write(dict(what="Making new creatures", done=0, total=int(args[0]), names=[], now=args[1] if len(args) > 1 else ""))
    elif cmd == "step":
        with open(PATH) as f:
            d = json.load(f)
        d["names"] = d.get("names", []) + [args[0]]
        d["done"] = min(d["total"], d.get("done", 0) + 1)
        d["now"] = args[1] if len(args) > 1 and d["done"] < d["total"] else ""
        _write(d)
    elif cmd == "stop":
        os.remove(PATH)
