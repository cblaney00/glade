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
- Further out (2026-10-27, his picks): **The Snowy Ridge** past the Forest (pines, snow, a frozen
  lake, aurora) and **The Hot Springs** past the River (a sleeping volcano, steaming turquoise
  terrace pools, embers). Each brings 3 animals of its own (below).

They lie on a map (`MAP` in `glade/scenes.py`): Waterfall up, Mossy Rocks down, Forest
left, River right of the Glade; the Ridge one more step left of the Forest, the Springs one
more step right of the River. `LINKS` lists which places a path joins (the minimap draws
them). He is happy for the map to grow beyond the four directions, with more tiles. **His rule
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
  (`num` in `battle.SPECIES`; Critter #001 … Moonhoot #049, next new one #052), each with a
  picture (`dex.specimen`: one made just to be drawn; the entry's moves, the slots' are still),
  and the rest are "?" slots. Dex tab: pages of 48 slots. Compare tab: a table of everything
  found so far, sorted by clicking a column. On the right, the chosen one's stats and moves.
- `glade/beasts.py` — the **second wave** of animals (2026-10-26, his ask: 10 more first-stage
  creatures, varied typing, in keeping with the glade): `Flier` (Gloomflit, Lanternwing,
  Glimmerfly, Mistwisp), `Walker` (Brawlhop, Mossdelve, Sporeling, Rimeslink, Copper
  Beetle), the far places' own animals (2026-10-27, Dex #052-#067: Frostpaw, Fluffhorn and
  Shimmerchirp on the Ridge; Steambara, Embercling and Vaporwobble at the Springs — they live
  only there, and are out from the start; `second_wave(..., fliers, walkers, out)` and the
  `walkers`/`fliers`/`out` keys of `sc.lower`), and `owlet()`, the Moonhoot, a tree dweller that can hold the icons instead of
  the tree squid (`TreeSquid.kind`). Dex #022-#049. More areas are coming, so not every typing
  is covered yet.
- **Catching, teams and the Battle Tower** (2026-10-27, his asks):
  - `glade/team.py` — every animal has its **own IVs** (`ivs_of`, rolled once per animal), drawn on
    its stats card as a six-sided web (`battle.iv_web`; his choice over stars/numbers). Caught
    creatures live in `~/.local/state/glade/creatures.json` as a `Collection`: a party of 6 and 8
    boxes of 30, **like Emerald's PC boxes**. His party starts **empty**.
  - **Order (his rule): the Battle Tower first.** The Tower door with an empty party opens
    **choose your starter**, then the tower board; until then a card's button says "Get a starter at
    the Tower". Glow jars stay greyed out until a Tower run has been tried (`Collection.tried`), and
    Tower trainers bring as many creatures as you have (1v1 on the first run, up to 6v6).
  - `glade/starter.py` — the starter choice:
    Mossprance (Grass), Kindlet (Fire), Pippalotl (Water), Dex #001/#004/#007 (the first nine numbers
    are their lines; everything else moved down 9). Final forms are designed, not built: Eldermane
    Grass/Ghost spirit stag, Pyreclad Fire/Steel molten pangolin knight, Leviolotl Water/Dragon
    axolotl river dragon. Starter abilities Overgrow/Blaze/Torrent work. Starters are never wild.
  - Battles: `battle.Battle` is now team v team (1-6 a side) with switching, forced switches and a
    **glow jar** (Gen 3 catch formula, `team.catch_shakes`) in wild battles. `battle.Arena` modes:
    "pick" (the moon egg, unchanged), "wild" (the stats card's **Battle it!**), "tower".
  - `glade/storage.py` — the boxes screen (party left, box grid middle, info + IV web right; click
    to pick up, click to put down/swap). Opened at the Tower's shrine or the Dex's "Your creatures".
  - (2026-10-27) Tower fairness, his rule: strategy and luck, not grinding. `tower.trainer` matches each of your creatures with a different kind of a similar base total (±20) and similar IVs (±6), whatever party you bring; the streak does not raise them. Simulated: ~50% a battle.
  - `glade/tower.py` — **The Battle Tower**, a place below the Mossy Rocks (path down the lower
    screen). Your party as it is (no separate picking — his call) vs endless trainers' sixes; IVs
    rise with the streak; best streak saved.
  - Generic names were renamed (his ask): Critter→Duskling, Squid→Driftlet, Slug→Gloamooze,
    Snail→Cairncurl, Millipede→Luminpede, Koi→Lilyfin, Tree Squid→Canopod (species names only;
    the Python classes keep their old names).
- **Animals come and go, like wild Pokémon** (2026-10-27, his design): `storm.Lifespans` — every animal out has its own random time (0-5 min, `storm.LIFE`); when it is up it slips away for good and a *new* animal (fresh IVs, `storm.fresh`) emerges in its place, quietly, one at a time. No big event. Places off screen change at once; animals in a battle, evolving or with their card open stay.
- **Evolved animals in the wild** (2026-10-27, his odds): `evolve.wild_stage` — each animal that comes out is its middle stage 7% of the time, its final stage 1% (lines without one give the middle instead; `SET_STAGE_3` once final stages are drawn).
- **Starters fully evolved** (2026-10-27, Dex #001-#009): Mossprance → Lichenmane → Eldermane (Grass/Ghost), Kindlet → Smoldershell → Pyreclad (Fire/Steel), Pippalotl → Frillotl → Leviolotl (Water/Dragon); totals 405 / 530. Stages are 1-3 now (`evolve.EVOLVES` chains, `species_at`, `stage_of`, `SIZE`); a Walker draws `draw_<kind><stage>` / `shine_<kind><stage>` when it has one.
- **Your creatures evolve** (2026-10-27): each `Kept` has a `uid` and `wins`; a creature that fought in a won Tower battle gets a win (`Battle.fought`, `tower.Run.count_wins`); at 3, then 9, it evolves through `evolve_party.EvolveBoard`, which has a Stop button (his choice).
- **Predator vision** (`glade/vision.py`, 2026-10-27): a golden button in the lower screen's top-left; for ~5 s everything turns grey except the animals, which keep their colour inside a golden outline.
- **Twice as many animals out** (his ask): a second of each second-wave animal per place (`scenes.second_wave`, `lower.py`), and `storm.crowd` doubles who is out at the start.
- **Natures and the summary** (2026-10-27): every creature has a Gen 3 nature (`team.NATURES`, `nature_of`; EVs are 84 each, `team.EVS`); stats via `battle.calc_stats`; the boxes' right panel is a full summary (base/IV/EV/stat table, moves, nature, IV web). Battles: your panel top-left, the foe's top-right, fighters face each other (`Fighter.face`).
- **Roaming** (2026-10-27): walkers wander between every stretch of ground in their place
  (`Walker.roam`, `scenes.MEADOW` + each place's grounds; a mole digs a new hole where it stops),
  ground slugs glide on to new spots (`Slug.wander`); climbers, fliers and fish keep to their
  own element. On the lower screen they never cross the pond.
- `glade/storm.py` — **animals take turns**. Not all are out at once: newcomers start
  `gone` (`storm.newcomer`). While a stats card or the Forest Dex is open, a **Thunderstorm**
  button shows in the lower screen's top-right corner. It brings rain and lightning, everyone
  in sight shelters (diggers sink into a hole, fliers fly off, koi dive), and the same number
  come back out, a random mix of everyone who lives there (every place has one of each of the
  second wave: `scenes.second_wave`, plus all five walkers and four fliers on each lower screen).
  The trees always hold a mix of squid and owlets (each one is either), re-mixed by a storm. Places
  not on screen are re-shuffled at once. Animals in a battle are left alone.
- `glade/evolve.py` — **evolution** (his test, 2026-10-26): only the middle stages of his five
  best designs so far — Critter → Glowtail, Squid → Nimbusdrift, Lanternwing → Beaconwing,
  Brawlhop → Thudhop, Sporeling → Sporestride. They have base totals of about 410 and are
  numbered right after their first stage. An evolved animal is the same object with `stage = 2`
  (`set_stage`), and each class draws its extras for it, growing on the old look the way
  Pokémon does. The stats card's gold "Evolve into …" button plays a ~4 s evolution: dim, a
  white shape flickering faster between forms, a flash, and a banner. It does not persist
  across restarts yet. Final stages are not made yet: don't add them unless he asks.
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
- **Progress board** (`glade/making.py`, 2026-10-27, his ask; it stays as a feature): while a Claude
  session makes new creatures, it writes `~/.local/state/glade/making.json`
  (`{"what": "Making new creatures", "done": N, "total": M, "names": [...]}`) as each one is
  finished. The lower screen's top-right shows a mint board with a progress bar (under the
  Thunderstorm button when that shows); at `done == total` it becomes a "M new creatures are
  ready!" notice for 9 s. **Always use it when making creatures for him.**
- **Naming rule (his, 2026-10-27):** a creature's name is one word with no real animal's name in
  it, even attached (only an attached "fly" is fine, e.g. Glimmerfly). Every older name was
  renamed to fit; `team.RENAMED` maps old saves' names to the new ones.
- **Third wave** (2026-10-27, his ask: 6 first-stage creatures in existing places, Dex #079-#094;
  next new one #097): the Forest's **Bramblit** (Grass/Dark, a thorny bramble ball with berry
  eyes) and **Thistlume** (Psychic/Flying, a thistledown puff with one dreamy eye); the
  Waterfall's **Runelet** (Rock/Ghost, a walking standing stone with a glowing rune and a
  ghost-light) and **Sparkfly** (Electric/Bug); the River's **Murkling** (Water/Poison, a gliding
  ink blob with stalk eyes) and **Glintshell** (Steel, shy, under a silver dome). Kinds `bramble`,
  `thistle`, `rune`, `spark`, `murk`, `glint` in `beasts.py`; placed by `second_wave(..., new=...)`
  (own dice, so the rest of each place paints as before) and each place's `sc.lower` walkers/fliers.
- **Forest Dex page one filled** (2026-10-27, his ask, his approved names): every line #010-#048
  has all three stages (`battle._LATER`, built from the earlier stage's pool by `_grown`;
  `evolve.EVOLVES`). Each class draws its later stages from `stage`: Critter (Cometail), Squid
  (Skyveil), Slug (Gloomdrape/Nightmire without a shell, Cairnspire/Cairnhold with one), Millipede
  (Luminthread/Glowcoil: `set_stage` adds segments; the Dex coils them), Fish (Lilyveil/Lotuscrest),
  TreeSquid (Boughgrip/Canopolis: the Dex/battle tuple is `("perch", kind, stage)`; tree squids
  holding icons never evolve), Flier bat/moth/drake/wisp, Walker toad (`draw_toad3`) and mole.
