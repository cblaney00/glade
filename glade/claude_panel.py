"""The Claude panel (his ask, 2026-10-27): a minimised way of talking to the Claude session
he has open, in the lower screen's top-right corner.

It shows what claude_state.py records: the task's title, whether Claude is working or waiting,
a progress bar with what is being worked on now (when the task has steps), and Claude's
latest message. Point at it and it opens out: the whole message, and a box to reply in that
grows as he types. Enter sends the reply into the terminal Claude is running in (kitty's
remote control, see send()), just as if he had typed it there. When Claude needs him at the
terminal (options to pick, a plan, a permission), the panel glows gold and says so.
"""

import glob
import json
import math
import os
import re
import subprocess
import threading
import time

import pygame

import claude_state
from art import glow, mix
from battle import TEXT, cloth

MINT = (130, 255, 190)
GOLD = (255, 206, 90)
DIM = (170, 160, 200)
W = 270          # its width, in canvas pixels
LINE = 13
SHORT = 4        # lines of the message shown while it is closed
DONE_FOR = 15.0  # seconds the "all done" line stays after a task's last step


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


class Panel:
    def __init__(self):
        self.state, self.checked = None, -10.0
        self.rect = None          # where it is on the canvas (for the pointer and clicks)
        self.box = None           # the reply box's rect, while it is open
        self.view = None
        self.typing = False
        self.draft = ""
        self.sent = None          # (when, "Sent" / why not)
        self.on_typing = None     # set by wayland.py: lets the panel have the keyboard, or not
        self.was_open = False

    # --- the state file ----------------------------------------------------------------

    def poll(self, t):
        if t - self.checked < 0.5:
            return
        self.checked = t
        d = claude_state.load()
        alive = d.get("pid") and os.path.exists(f"/proc/{d['pid']}")
        self.state = d if alive else None
        if self.state is None and self.typing:
            self.stop_typing()

    # --- pointer and keys --------------------------------------------------------------

    def hovered(self, m):
        return bool(m and self.rect and self.rect.collidepoint(m))

    def is_open(self, m):
        return self.typing or self.hovered(m) or bool(self.draft)

    def click(self, view, m):
        """A click on the panel is the panel's (True), never the glade's."""
        if self.state is None or view is not self.view or not self.hovered(m):
            if self.typing and view is self.view and not self.draft:
                self.stop_typing()
            return False
        if self.box and self.box.collidepoint(m):
            self.start_typing()
        return True

    def start_typing(self):
        if not self.typing:
            self.typing = True
            if self.on_typing:
                self.on_typing(True)

    def stop_typing(self):
        if self.typing:
            self.typing = False
            if self.on_typing:
                self.on_typing(False)

    def key(self, name, text=""):
        """A key while typing: name is "return", "escape", "backspace" or "" (text: what it types)."""
        if not self.typing:
            return False
        if name == "return":
            if self.draft.strip():
                self.send(self.draft.strip())
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

    def send(self, text):
        self.sent = (time.monotonic(), "Sending…")
        pid = (self.state or {}).get("pid")
        threading.Thread(target=self._send, args=(pid, text), daemon=True).start()

    def _send(self, pid, text):
        try:
            found = find_window(pid)
            if found is None:
                self.sent = (time.monotonic(), "Couldn't find Claude's terminal; reply there instead")
                return
            kitty, sock, wid = found
            base = [kitty, "@", "--to", "unix:" + sock]
            subprocess.run(base + ["send-text", "--match", f"id:{wid}", "--stdin"], input=text.encode(),
                           timeout=5, check=True, capture_output=True)
            time.sleep(0.35)
            subprocess.run(base + ["send-key", "--match", f"id:{wid}", "enter"], timeout=5, check=True,
                           capture_output=True)
            self.sent = (time.monotonic(), "Sent")
        except (OSError, subprocess.SubprocessError):
            self.sent = (time.monotonic(), "Couldn't send it; reply in the terminal instead")

    # --- drawing -------------------------------------------------------------------------

    def draw(self, s, view, font, t, below_storm):
        self.poll(t)
        self.view = view
        st = self.state
        if st is None:
            self.rect = self.box = None
            return
        m = view.mouse()
        is_open = self.is_open(m)
        if is_open != self.was_open:
            self.was_open = is_open
            if self.on_typing and not self.typing:  # pointing at it readies the keyboard for the box
                self.on_typing(is_open)
        x0, y0 = view.w - W - 8, 34 if below_storm else 8
        inner = W - 20
        rows = []  # (kind, payload)
        rows.append(("title", st.get("title") or "Claude"))
        if st.get("attention"):
            rows += [("attention", line) for line in wrap(font, "! " + st["attention"], inner)]
        p = st.get("progress")
        if p and not (p.get("finished") and time.time() - p["finished"] > DONE_FOR):
            rows.append(("bar", p))
            if p.get("finished"):
                rows.append(("done", f"All {p['total']} done!"))
            elif p.get("now"):
                rows.append(("now", p["now"]))
        msg = wrap(font, tidy(st.get("message") or ""), inner)
        if msg:
            if not is_open and len(msg) > SHORT:
                msg = msg[:SHORT - 1] + [msg[SHORT - 1].rstrip() + " …"]
            room = (view.h - y0 - 140) // LINE
            if is_open and len(msg) > room:  # too long to show it all: its end is what matters most
                msg = ["…"] + msg[-(room - 1):]
            rows.append(("gap", None))
            rows += [("msg", line) for line in msg]
        box_lines = []
        if is_open:
            box_lines = wrap(font, self.draft, inner - 10) if self.draft else []
            rows.append(("gap", None))
            rows.append(("box", box_lines))
            rows.append(("hint", None))
        h = 8
        for kind, v in rows:
            h += 8 + LINE * max(1, min(8, len(v))) if kind == "box" else {"bar": 14, "gap": 5}.get(kind, LINE)
        h += 4
        r = self.rect = pygame.Rect(x0, y0, W, h)
        attention = bool(st.get("attention"))
        tint = GOLD if attention else MINT
        if attention:  # it glows, gently pulsing, so he knows to look at the terminal
            k = 0.5 + 0.5 * math.sin(t * 3)
            glow(s, r.centerx, r.centery, W // 2 + 20, GOLD, 30 + round(40 * k) // 10 * 10)
        cloth(s, r, tint, hot=attention or is_open, alpha=235)
        if attention:
            pygame.draw.rect(s, mix(GOLD, (255, 255, 255), 0.3 + 0.3 * math.sin(t * 3)), r.inflate(2, 2), 1, border_radius=5)
        y = r.y + 5
        self.box = None
        for kind, v in rows:
            x = r.x + 10
            if kind == "title":
                working = st.get("working")
                c = MINT if working else mix(MINT, (255, 255, 255), 0.5)
                pygame.draw.circle(s, c, (x + 3, y + 6), 3)  # still: his ask, no working animation
                state = "working" if working else "waiting for you"
                tag = font.render(state, False, DIM)
                title = v
                while title and font.size(title)[0] > inner - 14 - tag.get_width() - 8:
                    title = title[:-2] + "…"
                s.blit(font.render(title, False, (255, 255, 255)), (x + 10, y))
                s.blit(tag, (r.right - 10 - tag.get_width(), y))
                y += LINE
            elif kind == "attention":
                s.blit(font.render(v, False, GOLD), (x, y))
                y += LINE
            elif kind == "bar":
                bar = pygame.Rect(x, y + 3, inner - 44, 8)
                pygame.draw.rect(s, (24, 40, 46), bar, border_radius=3)
                f = v["done"] / max(1, v["total"])
                if f > 0:
                    fill = bar.inflate(-2, -2)
                    fill.w = max(2, round(fill.w * f))
                    pygame.draw.rect(s, MINT, fill, border_radius=2)
                    gx = fill.right - 1 - ((t * 20) % max(1, fill.w))
                    pygame.draw.line(s, (240, 255, 248), (gx, fill.y), (gx, fill.bottom - 1))
                n = font.render(f"{v['done']}/{v['total']}", False, TEXT)
                s.blit(n, (r.right - 10 - n.get_width(), y))
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
                box = self.box = pygame.Rect(x, y, inner, 8 + LINE * n)
                pygame.draw.rect(s, (18, 14, 34), box, border_radius=3)
                rim = (255, 255, 255) if self.typing else mix(tint, (255, 255, 255), 0.3)
                pygame.draw.rect(s, rim, box, 1, border_radius=3)
                if not v:
                    hint = "Type here to reply to Claude" if self.typing else "Click here to reply to Claude"
                    s.blit(font.render(hint, False, DIM), (box.x + 5, box.y + 4))
                    cx = box.x + 5
                else:
                    shown = v[-8:]
                    for i, line in enumerate(shown):
                        s.blit(font.render(line, False, (255, 255, 255)), (box.x + 5, box.y + 4 + i * LINE))
                    cx = box.x + 5 + font.size(shown[-1])[0]
                if self.typing and int(t * 2) % 2 == 0:  # the caret
                    cy = box.bottom - 4 - LINE + 2
                    pygame.draw.line(s, (255, 255, 255), (cx + 1, cy), (cx + 1, cy + LINE - 3))
                y = box.bottom
            elif kind == "hint":
                if self.sent and time.monotonic() - self.sent[0] < 6:
                    hint, c = self.sent[1], MINT if self.sent[1] == "Sent" else GOLD
                elif self.typing:
                    hint, c = "Enter sends it · Esc stops typing", DIM
                else:
                    hint, c = "Your reply goes to Claude's terminal", DIM
                s.blit(font.render(hint, False, c), (x, y + 1))
                y += LINE
        if not is_open and self.sent and time.monotonic() - self.sent[0] < 6:
            img = font.render(self.sent[1], False, MINT if self.sent[1] == "Sent" else GOLD)
            s.blit(img, (r.right - 10 - img.get_width(), r.bottom + 2))


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
