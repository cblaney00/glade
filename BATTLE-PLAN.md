# Saved for later: the "battle" easter egg (asked 2026-10-26)

**His ask:** click the moon and type "battle". Then click two animals. A battle box opens in the
**bottom-left of the top screen**, like Pokémon Showdown **Gen 3 OU**. Each animal gets random moves
that suit it, and stats as if it were a first or second evolution. You click the moves, and **all the
math works just like Gen 3**.

Nothing is written yet. Below is the plan I worked out, so the next session doesn't redo the research.

## Hooking it in
- `apex.Listener` only knows `WORD = "apex"`. Change it to keep the last few letters and report which
  word was heard ("apex" or "battle"). `Glade.typed` (main.py) then starts the Hunt or the battle.
  Under Hyprland the `glademoon` submap already forwards every letter, and `on_heard` turns it off.
- New file `glade/battle.py` with the engine (pure logic) and the box (drawing and clicks).
- Picking: reuse `apex.find_prey()` and `Prey.pos()` (shared coords, lower screen = +OFFSET) to find
  the animal nearest a click. Show a ring on each chosen one, plus a hint banner with Cancel. The 1st
  click is his animal and the 2nd is the opponent (simple AI). Fireflies: pick one from `swarm.now[i]`.
- `Glade.click`: while a battle is on, clicks inside the box go to the box first. Draw the box in
  `overlay` for the top view, with the same cloth style as `Popup`/`Signs.board` and `signs.font`.
- Box: foe panel (HP %), his panel (HP numbers), 3 log lines, 2x2 move buttons (type colour, PP),
  Run. The engine emits log lines with an HP/status snapshot each, and the box shows them one at a
  time (~0.9 s) while the HP bars animate. Pulse a glow on the animal that was hit. Close when done.

## Species (Lv100, 31 IVs, 84 EVs each, neutral nature, Leftovers)
HP/Atk/Def/SpA/SpD/Spe
- Critter (Critter): Normal, 70/75/60/45/60/95, Guts
- Squid (Squid, Nibbler, HollowSquid): Water/Psychic, 60/50/55/90/75/85, Levitate
- Slug (Slug): Poison, 90/60/70/60/80/20, Liquid Ooze
- Snail (Slug with shell): Bug/Rock, 65/60/115/40/85/15, Shell Armor
- Millipede: Bug/Poison, 55/85/70/40/55/80, Poison Point
- Koi (pond Fish): Water, 70/80/60/55/65/80, Swift Swim (does nothing, no rain)
- Firefly: Bug/Electric, 50/45/50/85/60/105, Static

## Move pools (pick 4: at least 1 STAB attack, at least 2 attacks, at most 2 status)
- Critter: Body Slam, Return(102), Quick Attack, Double-Edge, Bite, Crunch, Iron Tail, Swords Dance, Agility
- Squid: Surf, Water Pulse, Octazooka, Psychic, Psybeam, Ice Beam, Confuse Ray, Hypnosis, Recover, Calm Mind
- Slug: Sludge Bomb, Sludge, Toxic, Acid Armor, Giga Drain, Mud-Slap, Rest, Curse, Pain Split, Haze, Body Slam
- Snail: Rock Slide, Ancient Power, Silver Wind, Rock Tomb, Iron Defense, Withdraw, Protect, Toxic, Rest, Leech Life, Curse
- Millipede: Poison Tail, Pin Missile, Signal Beam, Sludge Bomb, Toxic, Swords Dance, Agility, Screech, Rock Tomb
- Koi: Waterfall, Hydro Pump, Surf, Dragon Dance, Return, Bubble Beam, Dragon Breath, Twister, Ice Beam, Body Slam
- Firefly: Thunderbolt, Thunder Wave, Tail Glow, Shock Wave, Spark, Signal Beam, Silver Wind, Double Team, Flash, Confuse Ray
Use the Gen 3 power/accuracy/PP and secondary chances (e.g. Toxic 85 acc, Flash 70, Giga Drain 60/5pp,
Crunch -SpD 20%, Waterfall no flinch, Protect +3 priority).

## Gen 3 rules to follow
- Physical or special is set by the **type** (Bug, Rock, Poison, Normal, Steel, Ground... are physical).
- Stats: HP = 2B+31+21+110, others = 2B+31+21+5. Stage ratios (2+n)/2. Accuracy/evasion table
  33,36,43,50,60,75,100,133,166,200,233,266,300 /100.
- Damage: floor(floor(A*P*42/D)/50) (+Guts x1.5 on A) +2, then x2 crit, then STAB x1.5, then each type
  (floored), then random 85-100%, min 1. A crit ignores the attacker's negative stages and the
  defender's positive ones. Crit stages 1/16, 1/8, 1/4, 1/3, 1/2 (Poison Tail +1). Shell Armor blocks crits.
- Order: priority, then speed (paralysis x0.25), and a tie is random. Flinch only works if the target
  hasn't moved yet. Protect: 1, 1/2, 1/4... when used in a row, and it fails if the user moves last.
- Sleep counter 2-5 (1-4 turns asleep, acts on the turn it wakes). Rest = 3 (2 turns asleep).
  Freeze thaws 20% per turn. Paralysis 25% full para. Confusion 2-5 turns, 50% hits itself for 40 power,
  typeless, no random. Poison 1/8. Toxic n/16. Poison/Steel can't be poisoned. Ground is immune to
  Thunder Wave. Levitate makes it immune to Ground.
- Static/Poison Point: 1/3 chance on contact. Recoil 1/3 (Double-Edge). Drain 1/2 (Liquid Ooze reverses).
  Multi-hit 2/3/4/5 = 3/8, 3/8, 1/8, 1/8. Curse (not Ghost): +Atk +Def -Spe. Struggle 50 power, 1/4 recoil.
- End of turn: Leftovers 1/16, then poison damage.
