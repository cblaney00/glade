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
        # The glade draws its own little pixel cursor; hide the system one over it.
        gw = win.get_window()
        if gw is not None:
            gw.set_cursor(Gdk.Cursor.new_from_name(gw.get_display(), "none"))

    def resized(self, area, alloc):
        v = self.view
        v.rect = main.fit(pygame.Rect(0, 0, alloc.width, alloc.height), v.w, v.h)

    def motion(self, area, event):
        self.view.pointer = (event.x, event.y)
        return False

    def leave(self, area, event):
        self.view.pointer = None
        return False

    def press(self, area, event):
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.view.pointer = (event.x, event.y)
            self.glade.click(time.monotonic() - self.glade.t0)
        return True

    def draw(self, area, cr):
        v = self.view
        cr.set_source_rgb(*(c / 255 for c in main.INK))
        cr.paint()
        shown = v.canvas.subsurface((0, 0, v.w, v.h))
        data = bytearray(pygame.image.tobytes(shown, "BGRA"))
        img = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, v.w, v.h, v.w * 4)
        cr.translate(v.rect.x, v.rect.y)
        cr.scale(v.rect.w / v.w, v.rect.h / v.h)
        cr.set_source_surface(img, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_NEAREST)
        cr.paint()
        return True


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
