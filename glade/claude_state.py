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
"""

import json
import os
import pwd
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
                if f.read().strip() == "claude":
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


def hook(event):
    name = event.get("hook_event_name", "")
    d = load()
    pid = claude_pid()
    if name == "SessionStart" or d.get("pid") != pid:
        cwd = event.get("cwd") or os.getcwd()
        d = dict(pid=pid, session=event.get("session_id"), cwd=cwd,
                 title=d.get("title") if d.get("pid") == pid else None, message=d.get("message") if d.get("pid") == pid else None,
                 working=False, attention=None, progress=None)
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
        d["attention"] = "Claude has options for you to pick in the terminal" if tool == "AskUserQuestion" \
            else "Claude has a plan for you to look at in the terminal"
    elif name == "PostToolUse":
        d["working"] = True
        if tool in ASK_TOOLS:
            d["attention"] = None
    elif name == "Notification":
        msg = event.get("message", "")
        if "permission" in msg.lower() or "approve" in msg.lower():
            d["attention"] = "Claude needs your OK in the terminal"
    elif name == "Stop":
        d["working"] = False
    text = last_text(event.get("transcript_path", "")) if event.get("transcript_path") else None
    if text and text != d.get("message"):
        d["message"], d["message_at"] = text, time.time()
    save(d)


def main(args):
    cmd, rest = (args[0], args[1:]) if args else ("", [])
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
