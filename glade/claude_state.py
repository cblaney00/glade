"""What the Claude session he is talking to is up to, for the Claude panel (claude_panel.py).

His ask (2026-10-27): a small panel on the lower screen that is a minimised way of talking to
Claude: the task's title, a progress bar when there is one, Claude's latest message, a box to
reply in, and a gold glow when Claude needs him at the terminal (to pick options, say).

The session writes ~/.local/state/glade/claude.json through this file, run as a command
(`glade-status`, see the config's pkgs/glade). Plain Python only: it runs on every hook.

    glade-status hook             (Claude Code hooks: reads the hook's JSON on stdin)
    glade-status title TEXT       what the task is called on the panel
    glade-status progress N [NOW] a task of N steps begins, working on NOW
    glade-status step DONE [NEXT] DONE is finished, now on NEXT (update after EVERY step)
    glade-status attention TEXT   glow gold: he should come to the terminal (TEXT says why)
    glade-status calm             stop glowing
    glade-status done             the task is finished: the bar fills and says so, whatever was planned
    glade-status watch            (started by the hooks) every 5 s, Claude's latest message onto
                                  the panel; when the chat ends, the panel goes
"""

import json
import os
import pwd
import subprocess
import sys
import time

ASK_TOOLS = ("AskUserQuestion", "ExitPlanMode")


def home():
    """His home, even when Claude runs as `sudo claude` (as root)."""
    user = os.environ.get("SUDO_USER") or pwd.getpwuid(os.getuid()).pw_name
    try:
        return pwd.getpwnam(user).pw_dir
    except KeyError:
        return os.path.expanduser("~")


PATH = os.path.join(home(), ".local/state/glade/claude.json")


def load():
    try:
        with open(PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save(d):
    d["updated"] = time.time()
    folder = os.path.dirname(PATH)
    os.makedirs(folder, exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f)
    try:  # written as root: hand it to him, like the folder it is in
        st = os.stat(folder)
        os.chown(tmp, st.st_uid, st.st_gid)
    except OSError:
        pass
    os.chmod(tmp, 0o644)
    os.replace(tmp, PATH)


def claude_pid():
    """The `claude` process this is running under (hooks are started by it)."""
    pid = os.getppid()
    for _ in range(8):
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() in ("claude", ".claude-wrapped"):  # (Nix wraps it)
                    return pid
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return os.getppid()


def last_text(transcript):
    """The newest thing Claude said to him (its latest text, not tool calls)."""
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400_000))
            lines = f.read().decode(errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "assistant":
            continue
        content = (e.get("message") or {}).get("content") or []
        text = "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text").strip()
        if text:
            return text
    return None


def alive(pid):
    return bool(pid) and os.path.exists(f"/proc/{pid}")


def ancestors(pid):
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


def terminal_of(pid):
    """The kitty process Claude (process `pid`) runs under, if any."""
    for p in ancestors(pid):
        try:
            with open(f"/proc/{p}/comm") as f:
                if "kitty" in f.read():
                    return p
        except OSError:
            continue
    return None


def running(d):
    """Is the chat in `d` still open? Claude started with sudo can outlive its closed terminal
    window (it is handed to init and lingers), and the panel stayed up for it (2026-10-29), so
    the chat also counts as closed once Claude is no longer under the kitty it started in."""
    pid = d.get("pid")
    if not alive(pid):
        return False
    return not d.get("term") or d["term"] in ancestors(pid)


def watch():
    """His ask: the panel shows Claude's newest message within 5 seconds, even mid-turn (the hooks
    only fire around tool calls), and goes away once the chat is closed."""
    me = os.getpid()
    time.sleep(1)  # the hook that started it records it first
    while True:
        d = load()
        if not d or d.get("watcher") != me:
            return  # gone, or another watcher took over
        if not running(d):
            try:
                os.remove(PATH)
            except OSError:
                pass
            return
        text = last_text(d.get("transcript") or "")
        if text and text != d.get("message"):
            d = load()  # as fresh as can be, so a hook's change in between is not lost
            d["message"], d["message_at"] = text, time.time()
            save(d)
        time.sleep(5)


def ensure_watcher(d):
    if alive(d.get("watcher")):
        return
    try:
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "watch"], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        d["watcher"] = p.pid
    except OSError:
        pass


def hook(event):
    name = event.get("hook_event_name", "")
    d = load()
    pid = claude_pid()
    if name == "SessionStart" or d.get("pid") != pid:
        cwd = event.get("cwd") or os.getcwd()
        d = dict(pid=pid, session=event.get("session_id"), cwd=cwd,
                 title=d.get("title") if d.get("pid") == pid else None, message=d.get("message") if d.get("pid") == pid else None,
                 working=False, attention=None, progress=None, term=terminal_of(pid))
        if not d["title"]:
            d["title"] = "Claude: " + os.path.basename(cwd.rstrip("/"))
    if name == "SessionEnd":
        try:
            os.remove(PATH)
        except OSError:
            pass
        return
    tool = event.get("tool_name", "")
    if name == "UserPromptSubmit":
        d["working"], d["attention"] = True, None
    elif name == "PreToolUse" and tool in ASK_TOOLS:
        d["attention"] = "Claude has options for you to pick" if tool == "AskUserQuestion" \
            else "Claude has a plan for you to look at"
    elif name == "PostToolUse":
        d["working"] = True
        if tool in ASK_TOOLS:
            d["attention"] = None
    elif name == "Notification":
        msg = event.get("message", "")
        if "permission" in msg.lower() or "approve" in msg.lower():
            d["attention"] = "Claude needs your OK"
    elif name == "Stop":
        d["working"] = False
    if event.get("transcript_path"):
        d["transcript"] = event["transcript_path"]
    ensure_watcher(d)
    text = last_text(event.get("transcript_path", "")) if event.get("transcript_path") else None
    if text and text != d.get("message"):
        d["message"], d["message_at"] = text, time.time()
    save(d)


def main(args):
    cmd, rest = (args[0], args[1:]) if args else ("", [])
    if cmd == "watch":
        watch()
        return
    if cmd == "hook":
        try:
            hook(json.load(sys.stdin))
        except Exception:  # never get in Claude's way
            pass
        return
    d = load()
    if cmd == "title":
        d["title"] = " ".join(rest)
    elif cmd == "progress":
        d["progress"] = dict(total=int(rest[0]), done=0, names=[], now=" ".join(rest[1:]))
    elif cmd == "step":
        p = d.get("progress") or dict(total=1, done=0, names=[], now="")
        p["done"] = min(p["total"], p["done"] + 1)
        p["names"] = p["names"] + [rest[0]] if rest else p["names"]
        p["now"] = " ".join(rest[1:]) if p["done"] < p["total"] else ""
        if p["done"] >= p["total"]:
            p["finished"] = time.time()
        d["progress"] = p
    elif cmd == "done":
        p = d.get("progress")
        if p:
            p["total"] = p["done"] = max(1, p["done"])
            p["now"], p["finished"] = "", time.time()
            d["progress"] = p
    elif cmd == "attention":
        d["attention"] = " ".join(rest) or "Claude would like you to look at the terminal"
    elif cmd == "calm":
        d["attention"] = None
    else:
        print(__doc__)
        return
    save(d)


if __name__ == "__main__":
    main(sys.argv[1:])
