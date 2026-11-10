"""Remake glade/where.py (lore.WHERE): build every place and its lower screen, ask each animal its
line, and list every stage of the line where it lives. Run from the project folder:
    nix develop /home/insideabush/nixos-config#vibe-python --command python tools/make_where.py
"""

import collections
import os
import sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "glade")
sys.path.insert(0, HERE)
os.environ["SDL_VIDEODRIVER"] = "dummy"


def main():
    import pygame
    pygame.init()
    pygame.display.set_mode((960, 540))
    import carry
    import evolve
    import storm
    from battle import SPECIES
    from lower import Lower
    from scenes import BUILDERS
    fams = collections.defaultdict(set)
    for key, build in BUILDERS.items():
        sc = build()
        low = Lower(sc, 800, 450)
        for c in (sc, low):
            for o in carry.bodies(c) + ([c.critter] if getattr(c, "critter", None) else []):
                try:
                    f = storm.family(o)
                except Exception:  # (something that is not a creature)
                    continue
                if f and type(o).__name__ != "Nibbler":
                    fams[f].add(key)
    where = {}
    for f, ps in fams.items():
        for st in (1, 2, 3):
            sp = evolve.species_at(f, st) if st > 1 else f
            if sp and sp in SPECIES:
                where[sp] = tuple(p for p in BUILDERS if p in ps)
    for s in ("Canopod", "Moonhoot"):  # the trees' dwellers
        where[s] = ("glade",)
    for s in ("Mossprance", "Kindlet", "Pippalotl"):
        where[s] = ("tower",)
    out = ['"""Where each creature lives (lore.WHERE, the Forest Dex\'s "Found in" and the places\' own',
           'creatures for gyms and trainers). Made by building every place and asking each animal what it is,',
           'every stage of a line listed where its line lives (homes.py: each line in one place). Remake it',
           'when animals move: run tools/make_where.py."""', "", "WHERE = {"]
    for sp in sorted(where, key=lambda s: SPECIES[s].get("num", 999)):
        out.append(f"    {sp!r}: {where[sp]!r},")
    out.append("}")
    with open(os.path.join(HERE, "where.py"), "w") as f:
        f.write("\n".join(out) + "\n")
    print(len(where), "species")


if __name__ == "__main__":
    main()
