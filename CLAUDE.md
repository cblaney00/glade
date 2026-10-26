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

They lie on a map (`MAP` in `glade/scenes.py`): Waterfall up, Mossy Rocks down, Forest
left, River right of the Glade, each one step away with a single path back. **His rule
(2026-10-23): left only ever goes left, down only down** — every path's arrow (and the
keyboard) comes from `MAP`, never from where the board happens to sit, so a new place
must go on the map and its path art must run that way. A **minimap** board in the lower
screen's bottom-right corner (`Minimap` in `main.py`) shows the map with the place you
are in glowing; pointing at a place shows its name, clicking it goes there.

Objects in each place open his apps (tree hollow → Files, lantern → Terminal,
waterfall pool → Music, boat → Steam, mushroom ring → Browser, cave → Discord,
rune stone → Code editor). The mapping lives in `APPS` in `glade/main.py`; each one
has a carved wooden name board (`Signs` in `main.py`) with a pixel icon (`ICONS`) and
its name, always shown and never moving, so it is obvious where to click and easy to hit
(the board is clickable too). Paths to other places have the same boards, with an arrow.

**Art direction (his words):** pixel art, colours that really pop with lots of
pastels; mimic **Rain World**'s sprites, animation and colour, *but idyllic*. Then
(2026-10-22): it is **always night**; the sun/moon must **not** be the main light —
the light comes from fluorescent moss, glowing mushrooms/crystals, lanterns and
fireflies; lighting must not look flat; **more slugs** (not too many) and other
invertebrates; little **glowing squid** that, for no reason, swim through the air;
much more detail; plaques must not move; the words always shown, nicely.
In practice: depth planes fading into violet night mist, no outlines, moonlit rims and
shaded undersides, dense hanging plants, and everything gently moving.

## How it is built

Python + pygame (dev shell `vibe-python`; no numpy there, so everything is plain
pygame drawing). Drawn on a 960x540 canvas and scaled up 2x without smoothing (the
lower monitor: 800x450).

**Lighting** (`art.Lighting`): each picture has a light map — dim moonlit ambient, dark
near the ground — plus baked pools of coloured light around everything that glows
(`lamp`), contact shadows (`shadow`), and an `emit` layer of self-lit pixels. A frame is
drawn in true colours, multiplied by the light map plus that frame's moving lights,
then the glowing things are painted on top. So moving parts in `life.py` have up to
three passes: `draw` (before lighting), `light` (add to the light map), `shine` (after).

- `glade/art.py` — brushes, the depth/mist colour model (`at_depth`), `glowmoss`, lighting.
- `glade/life.py` — everything that moves: plants (Blades, Vines, Petals), light
  (Stars, Motes, Fireflies, Pulses, Shafts, Lantern, GlowThreads), water (Waterfall,
  River), creatures (Critter, Squid, Slug — with `shell` it is a snail — Millipede).
  Clickable creatures have `poke()`.
- `glade/scenes.py` — one `build_<place>()` per place; clickable `Spot`s per place.
- `glade/lower.py` — the lower monitor: the ground in front of whichever place is shown
  above, in its palette; paths leaving the upper screen continue here (specs are
  `sc.lower` in each scene builder, in lower-screen coords = upper x - 80).
- `glade/pond.py` — the Glade's lily pond on the lower screen (koi, lily pads, ripples).
- `glade/apex.py` — his easter egg: click the moon, type "apex". A legless blob of violet
  jelly (his ask: amorphous, not cat-like) eats every animal; what it eats keeps glowing
  inside it so the eating is obvious; then a long, characterful waddle off. The picture
  never zooms to follow it — he only wants it on screen.
- `glade/battle.py` — his second easter egg, Pokémon Showdown **Gen 3 OU** rules: click the
  moon (it shines bright while it listens), type "battle", click two animals (anywhere on
  the body; any place, any screen; not fireflies), and they walk onto a mossy field in the
  top screen's bottom-right corner and fight. You click your moves in the board in the
  bottom-left, and the foe picks its own. `Battle` is the rules engine (Gen 3 stat, damage, crit,
  accuracy, status, Protect, multi-hit, recoil, drain, Leftovers; physical/special by
  type). `Arena` is the picking, field and board. **Right-click any animal** for its base stats
  (`Card`; a tree squid has "Battle stats" in its menu). His rules for it: every animal
  is the **first of three evolutions** (base totals 300-320; a final stage would be 500-600,
  ~530 average). The later evolutions are not made yet, so don't add them unless he asks. The big
  violet slug lives in the middle strip of grass because the corner is the field.
- `glade/dex.py` — the **Forest Dex** (his Pokédex), opened from the stats card's "Open in
  Forest Dex" button. It has room for **260**. Each line of 3 evolutions takes 3 numbers in a row
  (`num` in `battle.SPECIES`; Critter #001, Squid #004 … Tree Squid #019, next new one #022),
  and the rest are "?" slots. Dex tab: pages of 48 slots. Compare tab: a table of everything
  found so far, sorted by clicking a column. On the right, the chosen one's stats and moves.
- `glade/main.py` — one window spanning every monitor (Glade on the one at +0+0, pond
  on the next), moved into place and made "below/sticky/skip_taskbar"
  with `wmctrl` so it sits behind every window; name boards, fades, app launching.
- `glade/wayland.py` — the same under Hyprland, as a layer-shell surface per monitor.

Run: `nix develop /home/insideabush/nixos-config#vibe-python --command python glade/main.py`
(Ctrl+Q quits, Home key jumps home). Review the art without a display:
`python glade/main.py --shots DIR` writes a PNG of every place.

Performance matters (it runs all day): keep surfaces 32-bit (`art.solid`), and see-through
layers trimmed to what is on them (`art.trimmed`). `--shots` prints ms per frame; keep it
around 10 ms for both screens.

It is installed on his system from a copy in the config repo (`pkgs/glade`), which is
started at login under Hyprland. Changing the installed copy is a config change → `ccn`.
