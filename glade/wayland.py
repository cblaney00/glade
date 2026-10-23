"""Running the glade as the desktop under Hyprland (or any wlroots-style compositor).

Wayland has a proper place for a desktop: a *layer-shell* surface on the "bottom"
layer, behind every window and under the bar, one per monitor. pygame cannot make
those, so GTK does (through gtk-layer-shell), and pygame keeps doing all the drawing
off-screen: each frame its small canvas is handed to cairo and blown up with
nearest-neighbour scaling, so the pixels stay crisp.

The main monitor (the one at the top-left of the layout) shows the glade; the next
one shows the ground in front of it, exactly as under XFCE.
"""

import os
import re
import socket
import subprocess
import threading
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # pygame draws off-screen only
# SDL would otherwise catch SIGTERM and turn it into a quit event nobody reads here (GTK
# runs the loop, not pygame), so the glade could not be stopped, e.g. at logout.
os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")

import cairo  # noqa: E402
import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell  # noqa: E402

import pygame  # noqa: E402

import main  # noqa: E402
from art import H, W  # noqa: E402

FPS = 30

# The pointer is the compositor's here (see Surface.set_cursor), so the scene must not
# draw its own copy as well.
CURSOR, main.CURSOR = main.CURSOR, pygame.Surface((1, 1), pygame.SRCALPHA)


class Surface:
    """One monitor's layer-shell window, showing one View of the glade."""

    def __init__(self, glade, view, monitor):
        self.glade, self.view = glade, view
        view.external = True
        win = self.win = Gtk.Window()
        GtkLayerShell.init_for_window(win)
        GtkLayerShell.set_namespace(win, "glade")
        GtkLayerShell.set_layer(win, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_monitor(win, monitor)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(win, edge, True)
        # -1: cover the whole monitor, ignoring the bar's reserved strip. The bar sits
        # on the layer above and simply draws over the top of the glade, which keeps
        # the canvas at an exact whole-number scale.
        GtkLayerShell.set_exclusive_zone(win, -1)
        GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
        area = self.area = Gtk.DrawingArea()
        area.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK)
        area.connect("draw", self.draw)
        area.connect("motion-notify-event", self.motion)
        area.connect("enter-notify-event", self.motion)
        area.connect("leave-notify-event", self.leave)
        area.connect("button-press-event", self.press)
        area.connect("size-allocate", self.resized)
        win.add(area)
        win.connect("realize", self.hide_cursor)
        win.show_all()

    def hide_cursor(self, win):
        self.set_cursor()

    def set_cursor(self):
        # The glade's little pixel cursor, at the same scale as the scene, handed to the
        # compositor as the real pointer. Drawn into the canvas it could only move when a
        # whole frame was repainted, which made the mouse feel laggy.
        gw = self.win.get_window()
        if gw is None:
            return
        scale = max(1, self.view.rect.w // self.view.w)
        img = pygame.transform.scale_by(CURSOR, scale)
        w, h = img.get_size()
        # The sprite is only fully opaque or fully clear, so it is already premultiplied.
        data = bytearray(pygame.image.tobytes(img, "BGRA"))
        surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
        gw.set_cursor(Gdk.Cursor.new_from_surface(gw.get_display(), surf, 0, 0))

    def resized(self, area, alloc):
        v = self.view
        v.rect = main.fit(pygame.Rect(0, 0, alloc.width, alloc.height), v.w, v.h)
        self.set_cursor()

    def motion(self, area, event):
        self.view.pointer = (event.x, event.y)
        return False

    def leave(self, area, event):
        self.view.pointer = None
        return False

    def press(self, area, event):
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.view.pointer = (event.x, event.y)
            KEYBOARD.clicked()
            self.glade.click(time.monotonic() - self.glade.t0)
        return True

    def draw(self, area, cr):
        v = self.view
        cr.set_source_rgb(*(c / 255 for c in main.INK))
        cr.paint()
        r = v.shown()
        shown = v.canvas.subsurface(r)
        data = bytearray(pygame.image.tobytes(shown, "BGRA"))
        img = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, r.w, r.h, r.w * 4)
        cr.translate(v.rect.x, v.rect.y)
        cr.scale(v.rect.w / r.w, v.rect.h / r.h)
        cr.set_source_surface(img, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_NEAREST)
        cr.paint()
        return True


class Keyboard:
    """Letting the keyboard steer the glade.

    A layer-shell surface at the back cannot count on getting the keyboard, so it is
    done with a Hyprland submap called "glade" (see glade.nix): while it is on, the
    arrows, Tab, Enter, Home, Backspace and Esc run `glade-ctl <command>`, which
    writes the command into a pipe this reads. It goes on with Super+Home or a click
    on the glade while no window has the focus, and off again with Esc, as soon as a
    window takes the focus, when an app is opened, or after a few idle minutes —
    so it can never keep those keys from a window."""

    IDLE = 180

    def __init__(self):
        self.glade = None
        self.window = None  # the focused window's address, if any
        self.used = time.monotonic()
        self.sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        self.pipe = os.path.join(runtime, "glade.ctl")

    def start(self, glade):
        self.glade = glade
        self.submap = ""
        glade.on_launch = self.off
        # the moon: while it listens, letters go to the glade ("glademoon" submap)
        glade.on_listen = lambda: self.dispatch("submap", "glademoon")
        glade.on_heard = self.off
        if not self.sig:
            return
        self.off()  # in case a previous glade left it on
        try:
            out = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, timeout=3).stdout
            self.window = re.search(r'"address": "(0x[0-9a-f]+)"', out).group(1)
        except (OSError, subprocess.SubprocessError, AttributeError):
            self.window = None
        try:
            if os.path.exists(self.pipe) and not os.path.isfile(self.pipe):
                os.unlink(self.pipe)
            os.mkfifo(self.pipe, 0o600)
        except FileExistsError:
            pass
        fd = os.open(self.pipe, os.O_RDONLY | os.O_NONBLOCK)
        os.open(self.pipe, os.O_WRONLY | os.O_NONBLOCK)  # held open so the pipe never reads as closed
        GLib.io_add_watch(fd, GLib.IO_IN, self.read)
        threading.Thread(target=self.events, daemon=True).start()
        GLib.timeout_add_seconds(1, self.idle)

    def dispatch(self, *args):
        try:
            subprocess.Popen(["hyprctl", "dispatch", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

    def on(self):
        self.used = time.monotonic()
        self.dispatch("submap", "glade")

    def off(self):
        if self.sig:
            self.dispatch("submap", "reset")

    def clicked(self):
        if self.sig and self.window is None and not self.glade.keys_on:
            self.on()

    def idle(self):
        if self.glade.keys_on and time.monotonic() - self.used > self.IDLE:
            self.off()
        t = time.monotonic() - self.glade.t0
        if self.submap == "glademoon" and not self.glade.listener.listening(t):
            self.off()  # the moon stopped listening: the letters are the windows' again
        return True

    def read(self, fd, cond):
        try:
            data = os.read(fd, 4096).decode(errors="replace")
        except BlockingIOError:
            return True
        for cmd in data.split():
            if cmd.startswith("key-") and len(cmd) == 5:
                self.glade.typed(cmd[4], time.monotonic() - self.glade.t0)
            elif cmd == "keys":
                self.window = None  # Super+Home has just cleared the windows away
                self.on()
            elif self.glade.keys_on:
                self.used = time.monotonic()
                self.glade.key(cmd, time.monotonic() - self.glade.t0)
        return True

    def events(self):
        """Follow Hyprland's event socket: which submap is on, and which window has focus."""
        path = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hypr", self.sig, ".socket2.sock")
        while True:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.connect(path)
                    buf = b""
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                        *lines, buf = buf.split(b"\n")
                        for line in lines:
                            GLib.idle_add(self.event, line.decode(errors="replace"))
            except OSError:
                pass
            time.sleep(2)

    def event(self, line):
        name, _, data = line.partition(">>")
        if name == "submap":
            self.submap = data
            self.glade.keys_on = data == "glade"
            if not self.glade.keys_on:
                self.glade.picked = None
        elif name == "activewindowv2":
            self.window = data if re.fullmatch(r"(0x)?[0-9a-f]+", data) else None
            if self.window and self.submap in ("glade", "glademoon"):
                self.off()  # a window has the focus: the keys are its again
        return False


KEYBOARD = Keyboard()


def monitors():
    display = Gdk.Display.get_default()
    mons = [display.get_monitor(i) for i in range(display.get_n_monitors())]
    # main = top-left of the layout, then the rest top-to-bottom, left-to-right
    def key(m):
        g = m.get_geometry()
        return ((g.x, g.y) != (0, 0), g.y, g.x)
    return sorted(mons, key=key)


def run():
    pygame.init()
    pygame.display.set_mode((1, 1))
    mons = monitors()
    g0 = mons[0].get_geometry()
    lower = None
    if len(mons) > 1:
        g1 = mons[1].get_geometry()
        lower = pygame.Rect(0, 0, g1.width, g1.height)
    glade = main.Glade(None, main.fit(pygame.Rect(0, 0, g0.width, g0.height), W, H), lower)
    KEYBOARD.start(glade)
    surfaces = [Surface(glade, glade.top, mons[0])]
    if glade.bottom:
        surfaces.append(Surface(glade, glade.bottom, mons[1]))

    last = [time.monotonic()]

    def tick():
        now = time.monotonic()
        dt, last[0] = min(0.1, now - last[0]), now
        glade.render(dt)
        for s in surfaces:
            s.area.queue_draw()
        return True

    GLib.timeout_add(1000 // FPS, tick)
    Gtk.main()
