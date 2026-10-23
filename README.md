# The Glade

A living pixel-art desktop: a forest clearing at night, lit by glowing moss, fireflies
and little sky-squid, that you move around by clicking paths (or with the keyboard).
Objects and name boards in each place open your apps; fruit in the blossom tree are
the apps and files you used lately.

Python + pygame. It runs as the desktop layer under Hyprland (`glade/wayland.py`,
GTK + gtk-layer-shell, one surface per monitor) or as a window kept behind the others
under X11 (`glade/main.py`).

```sh
python glade/main.py              # run it (Ctrl+Q quits)
python glade/main.py --shots DIR  # render a picture of every place, then exit
```

Packaged for NixOS in [landonreekstin/nixos-config](https://github.com/landonreekstin/nixos-config)
(`pkgs/glade`).
