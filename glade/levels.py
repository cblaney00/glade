"""Levels and experience, worked out the way Pokémon Emerald does (2026-10-28, his ask).

- **Wild levels** (his numbers): a first stage is level 5, a middle stage 16, a final stage 32.
  Legendaries never evolve, so they get a level of their own: 50.
- **Evolving**: at level 16 into the middle stage, at 32 into the final one (his pick, in place
  of the old Tower wins).
- **Experience**: when a foe faints, each of yours that was out against it and is still standing
  gets (its base experience x its level / 7), shared between them, x1.5 against a trainer
  (Gen 3). Catching gives none, like Emerald.
- **Growth rates**: Emerald's six curves. Each line has one, chosen once from its first stage's
  name; the starters are Medium Slow like Pokémon's, legendaries Slow.
- **Base experience**: what a species gives when beaten, by stage like Pokémon's (Bulbasaur 64,
  Ivysaur 141, Venusaur 208): about a fifth of its base total for a first stage, a third for a
  middle stage, two fifths for a final one.
"""

import zlib

MAX = 100
START = {1: 5, 2: 16, 3: 32}
EVOLVE_AT = {1: 16, 2: 32}  # the stage it is -> the level it evolves at
LEGEND_LEVEL = 50
STARTERS = {"Mossprance", "Kindlet", "Pippalotl"}

GROWTHS = ("Medium Fast", "Medium Slow", "Fast", "Slow", "Erratic", "Fluctuating")
# how often each is picked for a line (Pokémon has mostly Medium Fast and Medium Slow)
WEIGHTS = (35, 30, 12, 13, 5, 5)


def exp_for(group, n):
    """The total experience a creature of that growth rate has at level n (Emerald's tables)."""
    if n <= 1:
        return 0
    c = n ** 3
    if group == "Fast":
        return 4 * c // 5
    if group == "Medium Slow":
        return max(0, 6 * c // 5 - 15 * n * n + 100 * n - 140)
    if group == "Slow":
        return 5 * c // 4
    if group == "Erratic":
        if n <= 50:
            return c * (100 - n) // 50
        if n <= 68:
            return c * (150 - n) // 100
        if n <= 98:
            return c * ((1911 - 10 * n) // 3) // 500
        return c * (160 - n) // 100
    if group == "Fluctuating":
        if n <= 15:
            return c * ((n + 1) // 3 + 24) // 50
        if n <= 35:
            return c * (n + 14) // 50
        return c * (n // 2 + 32) // 50
    return c  # Medium Fast


def growth(species):
    from battle import LEGENDARY
    from evolve import stage_of
    if species in LEGENDARY:
        return "Slow"
    first, _ = stage_of(species)
    if first in STARTERS:
        return "Medium Slow"
    r = zlib.crc32(first.encode()) % sum(WEIGHTS)
    for g, w in zip(GROWTHS, WEIGHTS):
        if r < w:
            return g
        r -= w
    return GROWTHS[0]


def stage(species):
    from evolve import stage_of
    return stage_of(species)[1]


def wild_level(species):
    """The level a creature of this species has when met in the wild (or caught before levels)."""
    from battle import LEGENDARY
    if species in LEGENDARY:
        return LEGEND_LEVEL
    return START.get(min(stage(species), 3), 5)


def base_exp(species):
    from battle import LEGENDARY, SPECIES
    total = sum(SPECIES[species]["base"])
    if species in LEGENDARY:
        return total * 3 // 10
    return total * (20, 34, 40)[min(stage(species), 3) - 1] // 100


def gained(foe_species, foe_level, sharing, trainer):
    """Experience each of `sharing` creatures gets for beating that foe (Gen 3)."""
    exp = base_exp(foe_species) * foe_level // 7
    exp = max(1, exp // max(1, sharing))
    if trainer:
        exp = exp * 3 // 2
    return exp


def level_at(group, exp):
    n = 1
    while n < MAX and exp >= exp_for(group, n + 1):
        n += 1
    return n


def ready_to_evolve(species, level):
    """The species it would evolve into at this level, or None."""
    from evolve import EVOLVES
    nxt = EVOLVES.get(species)
    at = EVOLVE_AT.get(stage(species))
    return nxt if nxt and at and level >= at else None
