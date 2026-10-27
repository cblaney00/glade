# ~/nixos-config/modules/home-manager/hyprland/desktops/glade/dock.py
#
# The glade's dock, and the window chores behind it (packaged by dock.nix).
#
#   glade-dock              the dock: his favourite apps on a wooden board along the
#                           bottom of the lower monitor, then whatever else is open. A dot
#                           under an app means it is open, a dim dot that it is minimised.
#   glade-dock minimize     minimise the focused window (the title bar's – button)
#   glade-dock restore ADDR bring a minimised window back
#   glade-dock watch        give each new window the keyboard as it opens, and bring a
#                           minimised window back whenever something focuses it (the top
#                           bar's window list)
#   glade-dock apps ARGS... the Apps menu (rofi ARGS), closed by a click outside it
#
# Hyprland has no minimise: a minimised window waits on the hidden workspace
# special:minimized, tagged with the monitor it came from so it goes back there.
# Arguments for the dock: a JSON list of favourite desktop-file ids, and the CSS file.

import json
import os
import shlex
import socket
import sys
import threading
import time

SIG = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
HYPR = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hypr", SIG)
MINIMIZED = "special:minimized"
TAG = "glade-min-"  # + the monitor it was minimised from


# --- talking to Hyprland ---------------------------------------------------------------

def ask(request):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(os.path.join(HYPR, ".socket.sock"))
        sock.sendall(request.encode())
        out = b""
        while chunk := sock.recv(65536):
            out += chunk
    return out.decode(errors="replace")


def get(what):
    try:
        return json.loads(ask("j/" + what))
    except (OSError, ValueError):
        return [] if what != "activewindow" else {}


def dispatch(*commands):
    try:
        ask("[[BATCH]]" + ";".join("dispatch " + c for c in commands))
    except OSError:
        pass


def events():
    """Hyprland's event lines, for as long as it runs (reconnecting if it drops)."""
    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(os.path.join(HYPR, ".socket2.sock"))
                buf = b""
                while chunk := sock.recv(4096):
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    for line in lines:
                        name, _, data = line.decode(errors="replace").partition(">>")
                        yield name, data
        except OSError:
            pass
        time.sleep(2)


def client(address):
    return next((c for c in get("clients") if c["address"] == address), None)


def is_minimized(c):
    return c["workspace"]["name"] == MINIMIZED


# --- minimise / restore ----------------------------------------------------------------

def minimize(address=None):
    c = client(address) if address else get("activewindow")
    if not c or not c.get("address") or is_minimized(c):
        return
    mon = next((m["name"] for m in get("monitors") if m["id"] == c["monitor"]), "")
    dispatch(f"tagwindow +{TAG}{mon} address:{c['address']}",
             f"movetoworkspacesilent {MINIMIZED},address:{c['address']}")
    # Hyprland leaves the keyboard on the hidden window: hand it to the window used
    # before it, if one is on screen, or else to nothing (going to an empty monitor
    # from another one is the only way to clear it).
    if get("activewindow").get("address") == c["address"]:
        monitors = get("monitors")
        shown = {m["activeWorkspace"]["id"] for m in monitors}
        rest = sorted((w for w in get("clients")
                       if w["workspace"]["id"] in shown and w["address"] != c["address"]),
                      key=lambda w: w.get("focusHistoryID", 0))
        others = [m["name"] for m in monitors if m["name"] != mon]
        if rest:
            focus(rest[0]["address"])
        elif others:
            dispatch(f"focusmonitor {others[0]}", f"focusmonitor {mon}")


def restore(address):
    """Back onto whatever its monitor is showing now, in front, with the keyboard."""
    c = client(address)
    if not c:
        return
    if not is_minimized(c):
        focus(address)
        return
    tags = [t for t in c.get("tags", []) if t.startswith(TAG)]
    monitors = get("monitors")
    want = tags[0][len(TAG):] if tags else ""
    mon = (next((m for m in monitors if m["name"] == want), None)
           or next((m for m in monitors if m["focused"]), None))
    if not mon:
        return
    steps = []
    # The minimised workspace itself must not stay open on screen (it does when the
    # top bar's list focused a window in it).
    for m in monitors:
        if m["specialWorkspace"]["name"] == MINIMIZED:
            steps.append("togglespecialworkspace minimized")
            break
    steps.append(f"movetoworkspacesilent {mon['activeWorkspace']['id']},address:{address}")
    steps += [f"tagwindow -{t} address:{address}" for t in tags]
    dispatch(*steps)
    focus(address)


def focus(address):
    dispatch("submap reset", f"focuswindow address:{address}", f"alterzorder top,address:{address}")
    lower_glade()


def lower_glade():
    """Tell the glade a window was picked from the dock: its Forest Dex, stats card or board, if one
    is in front, steps back behind the windows (his ask, 2026-10-27; wayland.Front)."""
    pipe = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "glade.ctl")
    try:
        fd = os.open(pipe, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fd, b"lower\n")
        os.close(fd)
    except OSError:
        pass


def watch():
    for name, data in events():
        if name == "openwindow":
            # ADDRESS,WORKSPACE,CLASS,TITLE — the address comes without its 0x
            address, ws = data.split(",")[:2]
            if not ws.startswith("special"):
                # The keys go to the new window, even if the glade's arrow-key steering
                # (its "glade" submap) was still on when it opened.
                focus("0x" + address)
        elif name == "activewindowv2" and data:
            c = client(data if data.startswith("0x") else "0x" + data)
            if c and is_minimized(c):
                restore(c["address"])


# --- the dock --------------------------------------------------------------------------

KEYS_HINT = "← ↑ → ↓ walk · Tab choose · Enter open · Home glade · Esc stop"


def dock(favourites, css_path):
    import gi
    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell

    ICON = 44

    def app_keys(app):
        """The window classes this app's windows are likely to have."""
        keys = set()
        did = (app.get_id() or "").removesuffix(".desktop").lower()
        if did:
            keys.add(did)
            last = did.rsplit(".", 1)[-1]
            if len(last) > 3 and last not in ("client", "desktop", "app"):
                keys.add(last)
        if app.get_startup_wm_class():
            keys.add(app.get_startup_wm_class().lower())
        exe = os.path.basename(app.get_executable() or "")
        if exe and exe not in ("flatpak", "env", "sh", "bash"):
            keys.add(exe.lower())
        return keys

    class Dock:
        def __init__(self):
            self.favs = [a for a in (Gio.DesktopAppInfo.new(f) for f in favourites) if a]
            self.index = {}  # window class -> app
            for app in self.favs + [a for a in Gio.AppInfo.get_all() if isinstance(a, Gio.DesktopAppInfo)]:
                for k in app_keys(app):
                    self.index.setdefault(k, app)
            self.pending = False

            win = self.win = Gtk.Window()
            GtkLayerShell.init_for_window(win)
            GtkLayerShell.set_namespace(win, "glade-dock")
            GtkLayerShell.set_layer(win, GtkLayerShell.Layer.TOP)
            GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_margin(win, GtkLayerShell.Edge.BOTTOM, 8)
            GtkLayerShell.auto_exclusive_zone_enable(win)  # maximised windows stop above it
            GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
            screen = win.get_screen()
            if screen.get_rgba_visual():
                win.set_visual(screen.get_rgba_visual())
            win.set_app_paintable(True)

            # The keyboard hint, a small line of glowing letters on top of the dock while
            # the keyboard is steering the glade (Hyprland's "glade" submap).
            self.hint = Gtk.Label(label=KEYS_HINT)
            self.hint.set_name("hint")
            self.hint.set_no_show_all(True)
            self.board = Gtk.Box(spacing=4)
            self.board.set_halign(Gtk.Align.CENTER)
            stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            stack.set_name("dock")
            stack.pack_start(self.hint, False, False, 0)
            stack.pack_start(self.board, False, False, 0)
            win.add(stack)

            display = Gdk.Display.get_default()
            display.connect("monitor-added", lambda *_: self.place())
            display.connect("monitor-removed", lambda *_: self.place())
            self.place()
            self.refresh()
            win.show_all()
            threading.Thread(target=self.follow, daemon=True).start()

        def place(self):
            # The lowest monitor: below the main one, the dock sits on the ground at the
            # front of the glade instead of across the path between the two screens.
            display = Gdk.Display.get_default()
            mons = [display.get_monitor(i) for i in range(display.get_n_monitors())]
            if mons:
                low = max(mons, key=lambda m: (m.get_geometry().y, -m.get_geometry().x))
                GtkLayerShell.set_monitor(self.win, low)

        def follow(self):
            for name, data in events():
                if name == "submap":
                    GLib.idle_add(self.hint.set_visible, data == "glade")
                elif name in ("openwindow", "closewindow", "movewindow", "movewindowv2", "configreloaded"):
                    GLib.idle_add(self.schedule)

        def schedule(self):
            if not self.pending:
                self.pending = True
                GLib.timeout_add(120, self.refresh)
            return False

        def match(self, c):
            for k in (c.get("class", ""), c.get("initialClass", "")):
                k = k.lower()
                if k in self.index:
                    return self.index[k]
                if k.rsplit(".", 1)[-1] in self.index:
                    return self.index[k.rsplit(".", 1)[-1]]
            return None

        def refresh(self):
            self.pending = False
            # favourites first, always there; then the other open apps, in the order they
            # were opened
            entries = [{"app": a, "key": a.get_id(), "windows": []} for a in self.favs]
            by_key = {e["key"]: e for e in entries}
            clients = [c for c in get("clients")
                       if c.get("mapped") and c.get("class")
                       and (not c["workspace"]["name"].startswith("special") or is_minimized(c))]
            clients.sort(key=lambda c: c.get("stableId") or c["address"])
            for c in clients:
                app = self.match(c)
                key = app.get_id() if app else c["class"].lower()
                if key not in by_key:
                    by_key[key] = {"app": app, "key": key, "windows": [], "class": c["class"]}
                    entries.append(by_key[key])
                by_key[key]["windows"].append(c)

            for child in self.board.get_children():
                self.board.remove(child)
            for e in entries:
                self.board.add(self.button(e))
            self.board.show_all()
            return False

        def button(self, e):
            app, wins = e["app"], e["windows"]
            btn = Gtk.Button()
            btn.get_style_context().add_class("app")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            img = Gtk.Image()
            if app and app.get_icon():
                img.set_from_gicon(app.get_icon(), Gtk.IconSize.DIALOG)
            else:
                img.set_from_icon_name(e.get("class", "application-x-executable").lower(), Gtk.IconSize.DIALOG)
            img.set_pixel_size(ICON)
            col.pack_start(img, False, False, 0)
            dot = Gtk.Box()
            dot.set_halign(Gtk.Align.CENTER)
            dot.get_style_context().add_class("dot")
            if wins:
                shown = [w for w in wins if not is_minimized(w)]
                dot.get_style_context().add_class("open" if shown else "minimized")
            col.pack_start(dot, False, False, 0)
            btn.add(col)

            name = app.get_display_name() if app else e.get("class", "")
            if not wins:
                tip = f"{name}\nClick to open it"
            elif all(is_minimized(w) for w in wins):
                tip = f"{name} — minimised\nClick to bring it back"
            else:
                tip = f"{name} — open\nClick to bring it forward"
            btn.set_tooltip_text(tip + "\nRight-click for more")
            btn.connect("button-release-event", self.clicked, e)
            return btn

        def launch(self, app):
            if app and app.get_filename():
                # through Hyprland, so the app is not a child of the dock
                dispatch("exec gio launch " + shlex.quote(app.get_filename()))

        def clicked(self, btn, event, e):
            if event.button == 2:
                self.launch(e["app"])
            elif event.button == 3:
                self.menu(e).popup_at_widget(btn, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, event)
            elif event.button == 1:
                self.activate(e)
            return True

        def activate(self, e):
            wins = e["windows"]
            if not wins:
                self.launch(e["app"])
                return
            recent = lambda w: w.get("focusHistoryID", 0)
            shown = sorted((w for w in wins if not is_minimized(w)), key=recent)
            hidden = sorted((w for w in wins if is_minimized(w)), key=recent)
            active = get("activewindow").get("address")
            mine = active in [w["address"] for w in shown]
            if hidden and (not shown or mine):
                restore(hidden[0]["address"])  # the one minimised last
            elif not mine:
                focus(shown[0]["address"])  # the one used last
            elif len(shown) > 1:
                focus(shown[-1]["address"])  # clicking again goes round its windows

        def menu(self, e):
            menu = Gtk.Menu()

            def item(label, action):
                mi = Gtk.MenuItem(label=label)
                mi.connect("activate", lambda *_: action())
                menu.append(mi)

            wins = e["windows"]
            if len(wins) > 1:
                for w in wins:
                    title = w["title"] if len(w["title"]) <= 40 else w["title"][:39] + "…"
                    if is_minimized(w):
                        title += "  (minimised)"
                    item(title, lambda a=w["address"]: restore(a))
                menu.append(Gtk.SeparatorMenuItem())
            if e["app"]:
                item("Open a new window" if wins else "Open", lambda: self.launch(e["app"]))
            if any(not is_minimized(w) for w in wins):
                item("Minimise", lambda: [minimize(w["address"]) for w in wins if not is_minimized(w)])
            if wins:
                item("Close" if len(wins) == 1 else "Close all its windows",
                     lambda: dispatch(*(f"closewindow address:{w['address']}" for w in wins)))
            menu.show_all()
            return menu

    provider = Gtk.CssProvider()
    provider.load_from_path(css_path)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
    Dock()
    Gtk.main()


# --- the Apps menu ---------------------------------------------------------------------

def apps_menu(rofi_args):
    """Open the Apps menu (rofi) so that a click anywhere outside it closes it.

    Wayland rofi has no click-to-exit and keeps the keyboard, which left him stuck until he
    picked something. On its own screen the menu now fills the screen and a click beside
    the card cancels it (rofi.nix, kb-cancel in desktop.nix). A click on the other screen
    never reaches rofi, so while it is open a clear sheet covers every monitor beneath it,
    and a click on the sheet closes the menu."""
    import subprocess

    import gi
    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import Gdk, GLib, Gtk, GtkLayerShell

    if subprocess.run(["pkill", "-x", "rofi"]).returncode == 0:
        return  # it was open: the button closes it

    rofi = subprocess.Popen(["rofi", *rofi_args])

    def close(*_):
        if rofi.poll() is None:
            rofi.terminate()
        return True

    display = Gdk.Display.get_default()
    for i in range(display.get_n_monitors()):
        win = Gtk.Window()
        win.set_app_paintable(True)
        visual = win.get_screen().get_rgba_visual()
        if visual:
            win.set_visual(visual)
        win.connect("draw", lambda w, cr: (cr.set_source_rgba(0, 0, 0, 0.01), cr.paint()) and False)
        GtkLayerShell.init_for_window(win)
        GtkLayerShell.set_namespace(win, "glade-apps-sheet")
        GtkLayerShell.set_layer(win, GtkLayerShell.Layer.TOP)  # rofi is on OVERLAY, above it
        GtkLayerShell.set_monitor(win, display.get_monitor(i))
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(win, edge, True)
        GtkLayerShell.set_exclusive_zone(win, -1)  # over the bar and the dock too
        GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
        win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        win.connect("button-press-event", close)
        win.show_all()

    def gone():
        if rofi.poll() is None:
            return True
        Gtk.main_quit()
        return False

    GLib.timeout_add(100, gone)
    Gtk.main()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["minimize"]:
        minimize(args[1] if len(args) > 1 else None)
    elif args[:1] == ["restore"] and len(args) > 1:
        restore(args[1])
    elif args[:1] == ["watch"]:
        watch()
    elif args[:1] == ["apps"]:
        apps_menu(args[1:])
    elif len(args) == 2:
        dock(json.loads(args[0]), args[1])
    else:
        sys.exit("usage: glade-dock FAVOURITES-JSON CSS | minimize [ADDR] | restore ADDR | watch | apps [ROFI-ARGS...]")
