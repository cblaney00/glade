# The Glade

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

**Desktop and Wander (his ask, 2026-10-28):** the desktop is all looks, no play: the home
clearing alone (its apps, Hide animals, Predator vision, Thunderstorm, the Claude panel), no
paths, minimap or battles, and only `storm.CAP` (20) creature families, re-picked at each
Thunderstorm. The **Wander** board under Your party turns it into the whole game where it is,
on both screens (`Glade.wander` in `main.py`; `glade/world.py` draws the board); it then reads
**Rest**, which fades back to the plain desktop and lets the far places go (`Glade.rest`).
Forest Dex, Your party, right-clicking an animal and clicking the moon also start the game,
straight at that thing. (A separate game window was tried first: it could only cover the top
screen, so he chose this.)

**Loading while wandering** (`glade/loading.py`, 2026-10-28, his ask: Wander stuttered for ~20 s and he
wanted to know when it is all loaded): Wander loads **every** place, nearest first, on a side thread
that only works in the gaps between frames (`loading.between_frames` after each frame in both loops;
`breathe()` pause points all through `art.py`, with `breathe(need)` before a long single step). A bar
under the Wander board (`world.draw_loading`) reads "Loading places N/30", then "Every place is ready"
for 4 s. All 30 take ~31 s; no frame over ~42 ms; ~0.8 GB once all are in, let go on Rest. Walking
somewhere not yet loaded builds it at once (`loading.Rush`, ~1.5 s pause). Builds hold `Glade.building`
(they share art's path state). `art.bounds` replaces pygame's slow `get_bounding_rect` (same answer).
Any new drawing helper that loops a lot should call `breathe()`.

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
  (2026-10-29, his ask) The one looked up always has a pulsing gold frame (`dex.CHOSEN`): its slot in the
  Dex tab and its row in Compare; each tab opens on the page that has it (`to_dex`, `to_compare`).
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
- **Room to stand** (`glade/spacing.py`, 2026-10-27, his ask: they were hard to click): walkers and ground slugs pick
  spots nobody stands on or is walking to, one resting on another soon moves on, and a walker right behind another
  going the same way pauses (`spacing.gather` gives each place's ground animals their `neighbours`).
  Each walker also has its own lane (`Walker.lane`, a strip 7 x size deep around its ground line), chosen free with
  each goal, so they pass beside each other rather than on one line.
- **Lilyfin in every water** (2026-10-27, his pick; not the Ridge's frozen lake): `pond.Shoal` in the River, the
  Waterfall's pool, the Caverns' pool and the Springs' two lower pools, set as the scene's `pond` so cards, battles,
  glow jars, storms and hiding find them. The apex only fishes in the Glade's own pond; elsewhere fish are prey.
- **Battle zoom** (2026-10-27, his ask; this undoes "the picture never zooms" for battles only): `Arena.camera`
  glides the top screen 1.8x in on the field for the whole battle (not the picking) and out as they walk home;
  the boards are drawn after, unzoomed. While zoomed the top screen shows and takes clicks only on path signs.
- **Hiding for games** (`glade/hiding.py`, 2026-10-27, his picks): a screen a full-screen window (`fullscreen` >= 2 in
  `hyprctl clients`; not Discord, `wayland.NOT_GAMES`) fills is not drawn (`Glade.covered`, set by `wayland.Keyboard.check_fullscreen`). After 30 s of it,
  everyone out where he is hides (storm `Shelter`s); when he is back they come out one by one over ~30 s. Lower screen,
  top-left, under the Dex button: **Keep animals out** (a switch, only stops this hiding; saved in
  `~/.local/state/glade/settings.json`) and **Your party** (opens the boxes).
- **Predator vision** (`glade/vision.py`, 2026-10-27): a golden button in the lower screen's top-left; for ~5 s everything turns grey except the animals, which keep their colour inside a golden outline. (2026-10-29, his ask: to find ones worth catching) An animal whose IV total is in the top 5% (`vision.STRONG`, 131 of 186) gets a thicker, pulsing electric-blue outline instead (his ask: no star, an obvious colour). Outlines trace the whole body however big (the box grows until nothing is cut off) and skip faint glow (`vision.FAINT`).
- **Changing moves** (`Storage.moves_panel` in `storage.py`, 2026-10-29, his ask: only in Your party): the right panel stays on the last creature pointed at; its "Change moves" button lists its four moves and everything its species can learn (`SPECIES[...]['pool']`); click a move, then one to learn. Saved at once (unless it is being carried).
- **Twice as many animals out** (his ask): a second of each second-wave animal per place (`scenes.second_wave`, `lower.py`), and `storm.crowd` doubles who is out at the start.
- **Natures and the summary** (2026-10-27): every creature has a Gen 3 nature (`team.NATURES`, `nature_of`; EVs are 84 each, `team.EVS`); stats via `battle.calc_stats`; the boxes' right panel is a full summary (base/IV/EV/stat table, moves, nature, IV web). Battles: your panel top-left, the foe's top-right, fighters face each other (`Fighter.face`).
- **Roaming** (2026-10-27): walkers wander between every stretch of ground in their place
  (`Walker.roam`, `scenes.MEADOW` + each place's grounds; a mole digs a new hole where it stops),
  ground slugs glide on to new spots (`Slug.wander`); climbers, fliers and fish keep to their
  own element. On the lower screen they never cross the pond.
- `glade/storm.py` — **animals take turns**. Not all are out at once: newcomers start
  `gone` (`storm.newcomer`). A **Thunderstorm**
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
around 10 ms for both screens. Anything drawn every frame that rarely changes is made once and kept:
`battle.cloth` keeps each board's look, the Claude panel's wrapped text and the Dex's scaled
pictures are cached, off-screen lifespans are checked once a second, and `wayland.py` hands the
canvas to cairo without copying it (2026-10-27 checkup).

It is installed on his system from a copy in the config repo (`pkgs/glade`), which is
started at login under Hyprland. Changing the installed copy is a config change → `ccn`.
- **The Claude panel** (`glade/claude_panel.py` + `glade/claude_state.py`, 2026-10-27, his ask; it
  replaced the creature progress board): a minimised way of talking to the Claude chat he has open,
  in the lower screen's top-right. Shows the task title (`glade-status title`), working/waiting,
  a progress bar with "Now: …" (`glade-status progress N FIRST`, then `step DONE NEXT` after EVERY
  step: he once saw a bar sit at 8/22 and read it as frozen), and Claude's latest message. Pointing
  at it opens it out: the whole message and a reply box that grows as he types; Enter sends the
  reply into Claude's kitty window by kitty remote control (`find_window`: the window whose
  processes include the `claude` pid). Says "Open terminal" in orange (a calm orange rim, no glow) when Claude needs him at the
  terminal; clicking the panel anywhere but the reply box always brings up Claude's kitty window
  (`focus_terminal`, hyprctl focuswindow pid:<kitty>). Triggered by (AskUserQuestion/ExitPlanMode/permissions via hooks, or `glade-status attention WHY`). State:
  `~/.local/state/glade/claude.json`, written by Claude Code hooks (`glade-status hook`; the
  config passes `share/glade/claude-hooks.json` with `--settings` from ccn, vibe, blaney-todo). Under
  Wayland the lower surface takes the keyboard (ON_DEMAND) only while the panel is pointed at or
  typed in. (2026-10-27, his rule) It only shows while Claude's kitty window is minimised or on a workspace
  no monitor shows (`terminal_seen`), or while he is typing a reply. After typing, the keys go back to the
  window he was in (`wayland.Surface.keyboard`, `Keyboard.last_window`).
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
- **Depth and more room** (2026-10-27, his ask): walkers' drawn size is their own size times
  `depth`, from `persp(y)` (`scenes.persp` upper screen: 1 at the meadow front, down to 0.42 far
  back; `lower.py` `near`: smaller further up the lower screen), updated as they walk, so they
  also move slower far away. `Walker.size` is a property over `_size` (what `set_stage` sets).
  Every place has `far=` stretches in its `second_wave` call (paths, the far river bank, the
  snowfield behind the lake, …): two walkers each that wander only there, plus a small far flier.
- **Heights** (2026-10-27, his rules): every species has a Pokédex-style height in feet
  (`evolve.HEIGHT`, shown in the Dex entry's picture corner). Middle stages ~2-4 ft, finals mostly
  4-6 ft; Dragonite's 7'03" is his absolute maximum and only for a rare few (Prismwyrm 7'02",
  Leviolotl 6'10"); never Steelix-big; with 200+ planned, most stay small. An evolved creature is
  drawn `evolve.growth` times its first stage: (height ratio) ** 0.6, capped at 3.2. Dex pictures
  and battle bodies cap that so they fit. **Give every new species a HEIGHT.**
- **Forest Dex pages two and three** (2026-10-27, his ask; names chosen by Claude under his rule, he
  said "just go"): all 144 numbers are filled. Page two's later stages (`battle._PAGE2`, stats keep
  the line's shape at 410/530 via `_spread`) are drawn as extras on their first stage in
  `glade/grown.py` (`grow_<kind>` after drawing, `glow_<kind>` after its lights, hooked into
  Walker/Flier draw/shine; Moonhoot's line through `owlet(..., stage)`). Page three is sixteen new
  three-stage lines (`battle._PAGE3`, #097-#144) in `glade/wave4.py`: each kind's `draw_<kind>` /
  `glow_<kind>` handles all three stages; `beasts.LIT` lists the kinds that light their surroundings.
  Heights for all of them in `evolve.HEIGHT`. Next new line: #145 (page four).
- **Two new places** (his picks): **The Crystal Caverns** (`build_caverns`, MAP (0,-2), up from the
  Waterfall through a crystal-lit cave mouth on its left flank) and **The Starfall Meadow**
  (`build_meadow`, MAP (1,-1), right from the Waterfall; falling stars). Page three's creatures live
  only there, eight lines each.
- **Additions to the older places** (his ask, Claude's picks): `scenes.additions` — strings of paper
  lanterns, fairy rings, rune cairns, hollow logs, glowing lotuses; skipped where they'd sit on a path.
- Claude panel: it takes the keyboard only while the pointer is on the reply box or he is typing, and
  stops typing as soon as a window is focused, so clicking his terminal always gets the keys back.
- **Forest Dex complete: pages four to six** (2026-10-27, his ask; he liked the designs, placement
  and legendaries were his pick of Claude's recommendation). 38 new three-stage lines (`battle._PAGE4`,
  #145-#258) in `glade/wave5.py`: each kind is a body plan (quad, biped, blob, serpent; bird, bug,
  float) dressed in features that appear from a given stage (`KINDS`), so new lines are cheap to add.
  `wave5.HOMES` puts 3-4 in each of the ten places (scenes.second_wave and lower.py read it).
  **Legendaries** #259 Elderglow (Glade) and #260 Moonward (Starfall Meadow), `battle.LEGENDARY`:
  never Tower trainers, out only rarely (`storm.RARE`, never at the start), "Legendary" in the Dex.
- **Stat spread** (his ask: too many finals at exactly 530): `battle._retotal` sets every final
  stage's total from 465 to 580 (by name, deterministic; Prismwyrm and Shardsovereign 600) and middles
  380-440, keeping each line's shape. Starters stay 530, legendaries 600/620. Keep new species varied too.
- **Redesign, no humanoids** (2026-10-27, his rules): no creature may be humanoid (no
  upright-body-with-arms). `wave5.py` now draws each of its 38 lines with its own body — most
  aren't animals at all (a rolling bud, a candle stub, a paper screen, a water-wheel, skipping
  stones, a gong on a stand, two sparring halves, a moving dark pool...). Pebblefist, Kickbud and
  Twinklet lines redrawn (wave4.py), Sporestride's arms became spore tassels, Runewarden's floating
  hands orbiting stones, and Smoldershell/Pyreclad never rear up. **Think outside the box for new
  designs; never reuse one body for several lines.**
- **Legendaries** (his rules): never evolve; the stronger, the rarer (`storm.rare`: 12% at 570
  down to 1.5% at 700). **The cover legendaries, Elderglow and Moonward, are 700; every other
  legendary, including any added later, is 570-615.** Don't
  borrow from Pokémon's cover legendaries (no antlered deer, no dark bird, no sky-serpent).
  Elderglow is a drifting wreath of roots with a seed of light; Moonward a crescent of night-glass
  with one eye and seven moons in their phases. He counts 525+ as a strong total.
- Dex names split onto two lines at a natural break (`dex.fit_name`); 27% fewer animals out at once
  (`storm.FEWER`); scenes a little brighter (`art.LIFT`, `art.THIN`); the floating lantern strings
  are gone; the open stats card is shown again in an overlay-layer window (`wayland.CardFront`) so it
  sits in front of windows, the bar and notifications.
- **Panels in front** (`wayland.Front`): the stats card, the Forest Dex, and the boards (boxes, Tower,
  starter) are each re-shown in an overlay-layer window while open, so windows, the bar and
  notifications never cover them.
- **Updates keep your place** (`glade/resume.py`, his ask): every 5 s the glade compares its own store
  path with the installed `glade`; when newer, a gold notice shows by the Thunderstorm button (which shows
  too) and pressing it, when not `busy` (no battle, Tower run or evolution), saves place/history/Dex page+pick+tab/boxes to `~/.local/state/glade/resume.json` and exits; the
  config's glade-desktop loop starts the installed glade, which restores it. **So after a rebuild, don't kill the
  glade by hand any more**: tell him to press Thunderstorm to load the new one.
- **Five more places** (2026-10-27, his picks; `glade/faraway.py`, added to `scenes.BUILDERS` at the end of
  scenes.py): **The Mushroom Hollow** (MAP (-1,1), down the Forest's lower screen), **The Misty Bog** ((1,1), down
  the River's lower screen), **The Old Ruins** ((-1,-1), up a path through the Forest's trees), **The Cloud Bridge**
  ((0,-3), up the steps to a crack of starlight in the Caverns) and **The Glow Shore** ((3,0), right of the Hot
  Springs). Animals there moved in from elsewhere (lore.WHERE lists them), plus two new lines in `glade/wave7.py`:
  Tanglet (#289-#291, Fighting/Flying, a living bit of rope) on the Bridge and Tumblet (#292-#294, Rock/Water,
  sea glass) on the Shore. Next new line: #295.
- **Fifteen far places** (2026-10-27, his picks, three rounds of five): built with `glade/kit.py` (`make`: a
  spec plus painters; `trail`/`exit_spot`/`lower_path` add the paths out, also used in the places they branch
  off). Round one `faraway2.py`: Frozen Falls (up from Ridge), Aurora Peak (left of Ridge), Fern Gully (left of
  Hollow), Lantern Orchard (down the Hollow's lower screen), Sunken Temple (down the Bog's lower screen). Round
  two `faraway3.py`: Moon Dunes (right of Bog), Lava Lake (up from Springs), Coral Grotto (right of Shore), Kelp
  Deep (down the Shore's lower screen; under the sea), Lighthouse Point (up the Shore's headland). Round three
  `faraway4.py`: Comet Crater (up from Meadow), Moonpetal Garden (through the Ruins' arch), Floating Isles
  (stepping stones up from the Bridge), Storm Peaks (right of Bridge), Thornwood (left of Gully). All 30 places
  are in `scenes.MAP`; the minimap's CELL went 22 → 18 to fit. All built, they take ~0.7 GB.
- **Fifty more lines, Dex to 450** (2026-10-27, his ask: two per far place plus twenty spread over every place
  by theme, "good type distribution"): data in `glade/lines8.py` (kind, names, types, stat shape, final height,
  home; moves come from `pool()` by type), drawn in `glade/wave8.py` (the far places' 30) and `glade/wave9.py`
  (the 20), stories in `glade/lore8.py`. #295-#444; legendaries moved to #449/#450 with DEX_SIZE. Types now 13-23
  lines each (Dragon 13 is the least, Water 23 the most). Next new line: #445 (only #445-#448 left before the
  legendaries; grow DEX_SIZE for more).
- **Levels and experience** (`glade/levels.py`, 2026-10-28, his ask: a reason to level your party, Emerald's
  exp math). Wild: first stages Lv5, middle Lv16, finals Lv32 (legendaries Lv50, Claude's pick). Stats use the
  creature's level (`calc_stats(..., level)`), as do damage and Night Shade. A fainted foe's exp (base exp x
  level / 7, shared by yours that faced it and still stand, x1.5 from a trainer; none for catching) goes to
  kept creatures only (`Mon.uid`); `Battle.share_exp`, saved each turn by `Arena.keep_exp`. Growth rates are
  Emerald's six, one per line from its first stage's name (starters Medium Slow, legendaries Slow); base exp
  is about 20/34/40% of the base total by stage. **Evolving is by level now (his pick): 16 and 32**, after the
  battle it was reached in (`Arena.ready` → `EvolveBoard`; Tower between battles, wild battles via main.py);
  Tower wins are still counted but no longer evolve anything. **Tower trainers' creatures are the same level as
  the one of yours each is paired with (his pick)**; their kind is still matched by base total. Old saves get the
  level a wild one of their stage would have.
- **Trainers, gyms, Elite 4 — part one** (`glade/gyms.py`, 2026-10-29, his design). The whole plan: normal trainer
  battles (Tower only), one gym leader per place with that place's creatures, then once every gym is beaten the
  Elite 4 (four type specialists, middle/final stages only, always together in the same order) and a random champion
  picked separately. **Every trainer has an ace** (`gyms.with_ace`: last creature, stronger kind, +2 levels, IVs
  >= 20; beatable). Done so far: the Tower board's **Trainer battle** (`Run(single=True)`: one trainer matched to your
  party, Another trainer/Close; Tower streak trainers have aces too) and gyms in the **Forest, River and Mossy Rocks**
  (a banner stone `Spot` kind "gym", placed by `gyms.place` from `Scene.done`; `GymBoard` → `GymRun`). Gym
  difficulty is by how many you have beaten, any order (his rule: Emerald's casual Elite 4 level ~55 spread over all
  30 places): `level_for(n)` = Lv 7 → 55, team 3, 4, 5 then 6. Badges in `Collection.badges`; rematches allowed.
  Next: gyms for the other places, then the Elite 4 and champion.
