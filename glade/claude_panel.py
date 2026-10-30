"""The Claude panel (his ask, 2026-10-27): a minimised way of talking to the Claude sessions
he has open, in the lower screen's top-right corner: one card per chat (his ask, 2026-10-30),
three in sight at once, the mouse wheel scrolling through the rest, each with a progress bar.

Each card shows what claude_state.py records: the task's title, whether Claude is working or waiting,
a progress bar with what is being worked on now (when the task has steps), and Claude's
latest message. Clicking it (anywhere but the reply box) brings up the terminal that chat is
running in. Point at it and it opens out: the whole message, and a box to reply in that
grows as he types. Enter sends the reply into the terminal Claude is running in (kitty's
remote control, see send()), just as if he had typed it there. When Claude needs him at the
terminal (options to pick, a plan, a permission), it says "Open terminal" in orange (his
wording, 2026-10-27), with the reason underneath while it is pointed at.
"""

import functools
import glob
import json
import os
import re
import subprocess
import threading
import time

import pygame

import claude_state
from art import mix
from battle import TEXT, cloth

MINT = (130, 255, 190)
GOLD = (255, 206, 90)
ORANGE = (255, 156, 70)   # "Open terminal": Claude wants him there
DIM = (170, 160, 200)
W = 270          # its width, in canvas pixels
LINE = 13
SHORT = 2        # lines of the message shown while a card is closed
SHOWN = 3        # cards in sight at once (his pick, 2026-10-30); the wheel scrolls through the rest
CARD_H = 72      # about how tall a closed card is
DONE_FOR = 15.0  # seconds the "all done" line stays after a task's last step


@functools.lru_cache(maxsize=8)
def tidy(text):
    """Claude writes Markdown; the panel shows it as plain words."""
    out = []
    for line in text.splitlines():
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^\s*[-*]\s+", "• ", line)
        line = line.replace("**", "").replace("`", "")
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        out.append(line)
    return "\n".join(out).strip()


@functools.lru_cache(maxsize=32)
def wrap(font, text, width):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            if lines and lines[-1]:
                lines.append("")
            continue
        line = ""
        for word in para.split(" "):
            test = (line + " " + word) if line else word
            if font.size(test)[0] <= width:
                line = test
                continue
            if line:
                lines.append(line)
            while font.size(word)[0] > width:  # a very long word: break it
                k = len(word)
                while k > 1 and font.size(word[:k])[0] > width:
                    k -= 1
                lines.append(word[:k])
                word = word[k:]
            line = word
        lines.append(line)
    return lines


class Card:
    """One chat's card: what it is drawn from and where it was drawn."""

    def __init__(self, st):
        self.st = st
        self.rect = None
        self.box = None  # its reply box, while it is open


class Panel:
    def __init__(self):
        self.sessions, self.checked = [], -10.0
        self.rect = None          # all of it, on the canvas (for the pointer and clicks)
        self.cards = []           # the cards drawn last frame
        self.hints = []           # (rect, -1 / +1): the "more above / below" lines
        self.view = None
        self.typing = None        # the pid of the chat a reply is being typed to
        self.draft = ""
        self.draft_for = None     # the pid that draft is for
        self.sent = None          # (when, "Sent" / why not, pid)
        self.on_typing = None     # set by wayland.py: lets the panel have the keyboard, or not
        self.was_open = False
        self.seen = {}            # pid: its terminal is on one of his screens (then its card stays away)
        self.looking = False
        self.first = 0            # the first card shown (his ask, 2026-10-30: scroll through them)
        self.wheel = 0.0

    # --- the state files ---------------------------------------------------------------

    def poll(self, t):
        if t - self.checked < 0.5:
            return
        self.checked = t
        self.sessions = claude_state.sessions()
        pids = {d["pid"] for d in self.sessions}
        if self.draft_for not in pids:
            self.draft = ""
            self.stop_typing()
        if self.sessions and not self.looking:
            self.looking = True
            threading.Thread(target=self._look, args=(sorted(pids),), daemon=True).start()

    def _look(self, pids):
        try:
            self.seen = {pid: terminal_seen(pid) for pid in pids}
        finally:
            self.looking = False

    def shown(self):
        """The chats with a card: his rule (2026-10-27), only while that chat's terminal is
        minimised or on no screen (and always the one he is typing a reply to)."""
        return [d for d in self.sessions if not self.seen.get(d["pid"]) or d["pid"] in (self.typing, self.draft_for)]

    # --- pointer and keys --------------------------------------------------------------

    def hovered(self, m):
        return bool(m and self.rect and self.rect.collidepoint(m))

    def card_at(self, m):
        return next((c for c in self.cards if m and c.rect.collidepoint(m)), None)

    def click(self, view, m):
        """A click on the panel is the panel's (True), never the glade's."""
        if not self.cards or view is not self.view or not self.hovered(m):
            if self.typing is not None and view is self.view and not self.draft:
                self.stop_typing()
            return False
        for r, step in self.hints:
            if r.collidepoint(m):
                self.move(step)
                return True
        c = self.card_at(m)
        if c is None:
            return True
        pid = c.st["pid"]
        if c.box and c.box.collidepoint(m):
            if self.typing not in (None, pid):
                self.draft = ""
            self.start_typing(pid)
        else:  # anywhere else on it: go to that chat's terminal
            self.stop_typing()
            threading.Thread(target=focus_terminal, args=(pid,), daemon=True).start()
        return True

    def scroll(self, view, m, dy):
        """The mouse wheel over the cards (his ask, 2026-10-30): one card up or down per notch."""
        if view is not self.view or not self.hovered(m):
            return False
        self.wheel += dy
        while abs(self.wheel) >= 1:
            step = 1 if self.wheel > 0 else -1
            self.wheel -= step
            self.move(step)
        return True

    def move(self, step):
        self.first = max(0, min(len(self.shown()) - SHOWN, self.first + step))

    def start_typing(self, pid):
        was = self.typing is not None
        self.typing = self.draft_for = pid
        if not was and self.on_typing:
            self.on_typing(True)

    def stop_typing(self):
        if self.typing is not None:
            self.typing = None
            if self.on_typing:
                self.on_typing(False)

    def key(self, name, text=""):
        """A key while typing: name is "return", "escape", "backspace" or "" (text: what it types)."""
        if self.typing is None:
            return False
        if name == "return":
            if self.draft.strip():
                self.send(self.typing, self.draft.strip())
                self.draft = ""
            self.stop_typing()
        elif name == "escape":
            self.stop_typing()
        elif name == "backspace":
            self.draft = self.draft[:-1]
        elif text and text.isprintable():
            self.draft += text
        return True

    # --- sending a reply into the terminal ---------------------------------------------

    def send(self, pid, text):
        self.sent = (time.monotonic(), "Sending…", pid)
        threading.Thread(target=self._send, args=(pid, text), daemon=True).start()

    def _send(self, pid, text):
        try:
            found = find_window(pid)
            if found is None:
                self.sent = (time.monotonic(), "Couldn't find Claude's terminal; reply there instead", pid)
                return
            kitty, sock, wid = found
            base = [kitty, "@", "--to", "unix:" + sock]
            subprocess.run(base + ["send-text", "--match", f"id:{wid}", "--stdin"], input=text.encode(),
                           timeout=5, check=True, capture_output=True)
            time.sleep(0.35)
            subprocess.run(base + ["send-key", "--match", f"id:{wid}", "enter"], timeout=5, check=True,
                           capture_output=True)
            self.sent = (time.monotonic(), "Sent", pid)
        except (OSError, subprocess.SubprocessError):
            self.sent = (time.monotonic(), "Couldn't send it; reply in the terminal instead", pid)

    # --- drawing -------------------------------------------------------------------------

    def draw(self, s, view, font, t, below_storm):
        self.poll(t)
        self.view = view
        shown = self.shown()
        m = view.mouse()
        # The card under the pointer opens out; the one he types in (or left a draft in) stays
        # open. It is picked from last frame's places, so the cards don't jump about under the pointer.
        under = self.card_at(m)
        if self.typing is not None:
            opened = self.typing
        elif self.draft:
            opened = self.draft_for
        else:
            opened = under.st["pid"] if under else None
        self.cards, self.hints = [], []
        if not shown:
            self.rect = None
            if self.was_open:
                self.was_open = False
                if self.on_typing:
                    self.on_typing(False)
            return
        self.first = max(0, min(self.first, len(shown) - SHOWN))
        if self.typing is not None or self.draft:  # the card being typed in stays in sight
            i = next((i for i, d in enumerate(shown) if d["pid"] == opened), None)
            if i is not None and not self.first <= i < self.first + SHOWN:
                self.first = max(0, min(i, len(shown) - SHOWN))
        x0, y = view.w - W - 8, 34 if below_storm else 8
        top = y
        above, below = shown[:self.first], shown[self.first + SHOWN:]
        if above:
            y = self.hint(s, font, x0, y, len(above), "above", any(d.get("attention") for d in above), -1)
        room = view.h - y - 30 - (CARD_H + 4) * (min(SHOWN, len(shown) - self.first) - 1)
        for d in shown[self.first:self.first + SHOWN]:
            c = Card(d)
            y = self.card(s, font, t, c, x0, y, d["pid"] == opened, room) + 4
            self.cards.append(c)
        if below:
            y = self.hint(s, font, x0, y, len(below), "below", any(d.get("attention") for d in below), 1)
        self.rect = pygame.Rect(x0, top, W, y - top)
        # The keyboard is the panel's only while the pointer is on a reply box or he is typing in
        # one, so a click on any window (his terminal above all) gets the keys straight back.
        want = self.typing is not None or any(c.box and m and c.box.collidepoint(m) for c in self.cards)
        if want != self.was_open:
            self.was_open = want
            if self.on_typing and self.typing is None:
                self.on_typing(want)

    def hint(self, s, font, x, y, n, where, needs, step):
        """'2 more above' (orange when one of them needs him): click or scroll to see them."""
        text = f"{n} more {where}" + (" · one needs you" if needs else "") + " · scroll"
        r = pygame.Rect(x, y, W, LINE + 4)
        cloth(s, r, ORANGE if needs else MINT, hot=False, alpha=200)
        img = font.render(text, False, ORANGE if needs else DIM)
        s.blit(img, (r.centerx - img.get_width() // 2, y + 2))
        self.hints.append((r, step))
        return r.bottom + 4

    def card(self, s, font, t, c, x0, y0, is_open, room):
        st = c.st
        inner = W - 20
        rows = [("title", st.get("title") or "Claude")]
        if st.get("attention"):
            rows.append(("open", None))
            if is_open:
                rows += [("attention", line) for line in wrap(font, st["attention"], inner)]
        p = st.get("progress")
        if p and p.get("finished") and time.time() - p["finished"] > DONE_FOR:
            p = None
        rows.append(("bar", p))  # his ask (2026-10-30): every card has a bar
        if p and p.get("finished"):
            rows.append(("done", f"All {p['total']} done!"))
        elif p and p.get("now"):
            rows.append(("now", p["now"]))
        msg = wrap(font, tidy(st.get("message") or ""), inner)
        if msg:
            if not is_open and len(msg) > SHORT:
                msg = msg[:SHORT - 1] + [msg[SHORT - 1].rstrip() + " …"]
            fit = max(SHORT, (room - 85) // LINE)
            if is_open and len(msg) > fit:  # too long to show it all: its end is what matters most
                msg = ["…"] + msg[-(fit - 1):]
            rows.append(("gap", None))
            rows += [("msg", line) for line in msg]
        mine = self.typing == st["pid"]
        if is_open:
            draft = self.draft if self.draft_for == st["pid"] else ""
            rows += [("gap", None), ("box", wrap(font, draft, inner - 10) if draft else []), ("hint", None)]
        h = 8
        for kind, v in rows:
            h += 8 + LINE * max(1, min(8, len(v))) if kind == "box" else {"bar": 14, "gap": 5}.get(kind, LINE)
        h += 4
        r = c.rect = pygame.Rect(x0, y0, W, h)
        tint = MINT
        cloth(s, r, tint, hot=is_open, alpha=235)
        if st.get("attention"):  # a calm orange rim: come to the terminal
            pygame.draw.rect(s, ORANGE, r.inflate(2, 2), 1, border_radius=5)
        y = r.y + 5
        working = st.get("working")
        for kind, v in rows:
            x = r.x + 10
            if kind == "title":
                col = MINT if working else mix(MINT, (255, 255, 255), 0.5)
                pygame.draw.circle(s, col, (x + 3, y + 6), 3)  # still: his ask, no working animation
                tag = font.render("working" if working else "waiting for you", False, DIM)
                title = v
                while title and font.size(title)[0] > inner - 14 - tag.get_width() - 8:
                    title = title[:-2] + "…"
                s.blit(font.render(title, False, (255, 255, 255)), (x + 10, y))
                s.blit(tag, (r.right - 10 - tag.get_width(), y))
                y += LINE
            elif kind == "open":
                s.blit(font.render("Open terminal", False, ORANGE), (x, y))
                y += LINE
            elif kind == "attention":
                s.blit(font.render(v, False, DIM), (x, y))
                y += LINE
            elif kind == "bar":
                self.bar(s, font, t, pygame.Rect(x, y + 3, inner - 44, 8), v, working, r.right - 10, y)
                y += 14
            elif kind == "now":
                dots = "." * (1 + int(t * 2) % 3)
                s.blit(font.render(f"Now: {v}{dots}", False, mix(TEXT, MINT, 0.4)), (x, y))
                y += LINE
            elif kind == "done":
                s.blit(font.render(v, False, MINT), (x, y))
                y += LINE
            elif kind == "gap":
                pygame.draw.line(s, mix(tint, (20, 20, 40), 0.6), (x, y + 2), (r.right - 10, y + 2))
                y += 5
            elif kind == "msg":
                s.blit(font.render(v, False, TEXT), (x, y))
                y += LINE
            elif kind == "box":
                n = max(1, min(8, len(v)))
                box = c.box = pygame.Rect(x, y, inner, 8 + LINE * n)
                pygame.draw.rect(s, (18, 14, 34), box, border_radius=3)
                rim = (255, 255, 255) if mine else mix(tint, (255, 255, 255), 0.3)
                pygame.draw.rect(s, rim, box, 1, border_radius=3)
                if not v:
                    hint = "Type here to reply to Claude" if mine else "Click here to reply to Claude"
                    s.blit(font.render(hint, False, DIM), (box.x + 5, box.y + 4))
                    cx = box.x + 5
                else:
                    lines = v[-8:]
                    for i, line in enumerate(lines):
                        s.blit(font.render(line, False, (255, 255, 255)), (box.x + 5, box.y + 4 + i * LINE))
                    cx = box.x + 5 + font.size(lines[-1])[0]
                if mine and int(t * 2) % 2 == 0:  # the caret
                    cy = box.bottom - 4 - LINE + 2
                    pygame.draw.line(s, (255, 255, 255), (cx + 1, cy), (cx + 1, cy + LINE - 3))
                y = box.bottom
            elif kind == "hint":
                sent = self.sent if self.sent and self.sent[2] == st["pid"] else None
                if sent and time.monotonic() - sent[0] < 6:
                    hint, col = sent[1], MINT if sent[1] == "Sent" else GOLD
                elif mine:
                    hint, col = "Enter sends it · Esc stops typing", DIM
                else:
                    hint, col = "Your reply goes to Claude's terminal", DIM
                s.blit(font.render(hint, False, col), (x, y + 1))
                y += LINE
        sent = self.sent if self.sent and self.sent[2] == st["pid"] else None
        if not is_open and sent and time.monotonic() - sent[0] < 6:
            img = font.render(sent[1], False, MINT if sent[1] == "Sent" else GOLD)
            s.blit(img, (r.right - 10 - img.get_width(), r.bottom + 2))
            return r.bottom + LINE
        return r.bottom

    def bar(self, s, font, t, bar, p, working, right, y):
        """Steps done (when Claude counted them), or else a soft glow drifting along it while
        Claude works and lying still while it waits (his pick, 2026-10-30)."""
        pygame.draw.rect(s, (24, 40, 46), bar, border_radius=3)
        fill = bar.inflate(-2, -2)
        if p:
            f = p["done"] / max(1, p["total"])
            if f > 0:
                fill.w = max(2, round(fill.w * f))
                pygame.draw.rect(s, MINT, fill, border_radius=2)
                gx = fill.right - 1 - ((t * 20) % max(1, fill.w))
                pygame.draw.line(s, (240, 255, 248), (gx, fill.y), (gx, fill.bottom - 1))
            label = f"{p['done']}/{p['total']}"
        else:
            span = fill.w + 40
            cx = fill.x - 20 + (t * 45) % span if working else fill.centerx
            for x in range(fill.x, fill.right):
                a = max(0.0, 1 - abs(x - cx) / 20)
                if not working:
                    a *= 0.35
                if a > 0:
                    pygame.draw.line(s, mix((24, 40, 46), MINT, a * 0.8), (x, fill.y), (x, fill.bottom - 1))
            label = "…" if working else ""
        if label:
            n = font.render(label, False, TEXT)
            s.blit(n, (right - n.get_width(), y))


def _ancestors(pid):
    chain = []
    for _ in range(12):
        if not pid or pid <= 1:
            break
        chain.append(pid)
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return chain


def focus_terminal(pid):
    """Bring up the window of the terminal Claude (process `pid`) runs in."""
    for p in _ancestors(pid):
        try:
            with open(f"/proc/{p}/comm") as f:
                if "kitty" not in f.read():
                    continue
        except OSError:
            continue
        try:
            subprocess.run(["hyprctl", "dispatch", "focuswindow", f"pid:{p}"], capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
        return


def terminal_seen(pid):
    """Is the kitty window Claude (process `pid`) runs in on a screen just now: on a workspace a
    monitor is showing, not minimised (the dock's special:minimized) or on a workspace out of sight?"""
    kitties = set()
    for p in _ancestors(pid):
        try:
            with open(f"/proc/{p}/comm") as f:
                if "kitty" in f.read():
                    kitties.add(p)
        except OSError:
            continue
    if not kitties:
        return False
    try:
        mons = json.loads(subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, timeout=3).stdout)
        clients = json.loads(subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, timeout=3).stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    shown = set()
    for m in mons:
        for key in ("activeWorkspace", "specialWorkspace"):
            ws = m.get(key) or {}
            if ws.get("id"):
                shown.add(ws["id"])
    return any(c.get("pid") in kitties and c.get("workspace", {}).get("id") in shown and not c.get("hidden")
               for c in clients)


def find_window(pid):
    """(kitty, socket, window id) of the kitty window Claude (process `pid`) runs in."""
    if not pid:
        return None
    chain = set(_ancestors(pid))
    kitty = "kitty"
    for cand in ("/etc/profiles/per-user/%s/bin/kitty" % os.environ.get("USER", ""), "/run/current-system/sw/bin/kitty"):
        if os.path.exists(cand):
            kitty = cand
            break
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    for sock in glob.glob(os.path.join(runtime, "kitty-*")) + glob.glob("/tmp/kitty-*"):
        try:
            out = subprocess.run([kitty, "@", "--to", "unix:" + sock, "ls"], capture_output=True, timeout=5).stdout
            for osw in json.loads(out or b"[]"):
                for tab in osw.get("tabs", []):
                    for w in tab.get("windows", []):
                        pids = {w.get("pid")} | {p.get("pid") for p in w.get("foreground_processes", [])}
                        if pids & chain:
                            return kitty, sock, w["id"]
        except (OSError, subprocess.SubprocessError, ValueError):
            continue
    return None
