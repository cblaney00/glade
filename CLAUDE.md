# HUD — The Glade

*Created by the `vibe` command. Keep the two sections below current as the app grows —
a future session starts by reading them.*

> **The rules for working here are in `../CLAUDE.md`** (one directory up, alongside the
> other apps). They are loaded automatically; if for any reason they are not in your
> context, read that file before doing anything else.

## What this app is

Not really an app: a **living pixel-art desktop**. His main monitor becomes a forest
clearing (a glade) that he moves around by clicking paths, like the point-and-click
game *Putt-Putt Travels Through Time*. Places, each with paths to others:

- **The Glade** (home, the centre): blossom tree, signpost, paths to everywhere else.
- **The Waterfall**, **The River**, **The Forest**, **The Mossy Rocks**.

Objects in each place open his apps (tree hollow → Files, lantern → Terminal,
waterfall pool → Music, boat → Steam, mushroom ring → Browser, cave → Discord,
rune stone → Code editor). The mapping lives in `APPS` in `glade/main.py`.

**Art direction (his words):** pixel art, colours that really pop with lots of
pastels; mimic **Rain World**'s sprites, animation and colour, *but idyllic*. In
practice: depth planes fading into pastel mist, no outlines, sunlit rims, dense
hanging plants, and everything gently moving (grass, vines, pollen, glowing bugs,
water, a little tailed creature that wanders the Glade and hops when clicked).

## How it is built

Python + pygame (dev shell `vibe-python`; no numpy there, so everything is plain
pygame drawing). Drawn on a 480x270 canvas and scaled up 4x without smoothing.

- `glade/art.py` — drawing brushes and the depth/mist colour model (`at_depth`).
- `glade/life.py` — everything that moves (Blades, Vines, Motes, Bugs, Petals,
  Shafts, Waterfall, River, Lantern, Critter).
- `glade/scenes.py` — one `build_<place>()` per place; clickable `Spot`s per place.
- `glade/pond.py` — the lily pond shown on his lower monitor (koi, lily pads, ripples).
- `glade/main.py` — one window spanning every monitor (Glade on the one at +0+0, pond
  on the next), moved into place and made "below/sticky/skip_taskbar"
  with `wmctrl` so it sits behind every window; hover labels, fades, app launching.

Run: `nix develop /home/insideabush/nixos-config#vibe-python --command python glade/main.py`
(Ctrl+Q quits, Home key jumps home). Review the art without a display:
`python glade/main.py --shots DIR` writes a PNG of every place.

Not done yet: starting it automatically at login (that is a config change → `ccn`).
