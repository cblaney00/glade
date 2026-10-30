"""Items in battle (2026-10-30, his design).

His rules: there is no shop and no money, and no items exist outside a battle. Some trainer battles
draw a few items (never more than 4; early on usually none, and one is a lot), and **both sides get
the very same items**, so it is an even playing field. Before turn 1, each side chooses which of
its creatures carries which (`Arena`'s "items" phase; the trainer chooses with `foe_assign`). The
set is random every battle (his pick), drawn by how strong the trainer's team is (`roll`). Wild
animals carry nothing, so wild battles have none. Leftovers is no longer held by everyone: it is
just one of the items.

Each creature carries at most one. They work by themselves (the rules are in battle.Battle):
berries and potions are used once, when the moment comes; the rest work all battle.
"""

import random

# name: (what kind, the words shown when choosing, the lowest foe level it can turn up at)
ITEMS = {
    "Oran Berry": ("heal", "Eaten at half HP or less: heals 10 HP.", 1),
    "Potion": ("heal", "Drunk at half HP or less: heals 20 HP.", 1),
    "Cheri Berry": ("cure", "Eaten when paralysed: cures it.", 1),
    "Chesto Berry": ("cure", "Eaten when asleep: wakes it up.", 1),
    "Pecha Berry": ("cure", "Eaten when poisoned: cures it.", 1),
    "Rawst Berry": ("cure", "Eaten when burned: cures it.", 1),
    "Sitrus Berry": ("heal", "Eaten at half HP or less: heals 30 HP.", 15),
    "Super Potion": ("heal", "Drunk at half HP or less: heals 50 HP.", 15),
    "Lum Berry": ("cure", "Eaten at the first status or confusion: cures it.", 15),
    "Quick Claw": ("held", "Sometimes lets it move first.", 15),
    "Bright Powder": ("held", "Foes' moves miss it a little more often.", 15),
    "Scope Lens": ("held", "Its moves land critical hits more often.", 15),
    "King's Rock": ("held", "Its hits sometimes make the foe flinch.", 15),
    "Leftovers": ("held", "Heals a little HP at the end of every turn.", 25),
    "Shell Bell": ("held", "Heals an eighth of the damage it deals.", 25),
    "Focus Band": ("held", "Sometimes hangs on with 1 HP instead of fainting.", 25),
    "Liechi Berry": ("pinch", "Eaten at a quarter HP or less: raises Attack.", 25),
    "Salac Berry": ("pinch", "Eaten at a quarter HP or less: raises Speed.", 25),
    "Petaya Berry": ("pinch", "Eaten at a quarter HP or less: raises Sp. Atk.", 25),
    "Hyper Potion": ("heal", "Drunk at half HP or less: heals 200 HP.", 40),
}
HEAL = {"Oran Berry": 10, "Potion": 20, "Sitrus Berry": 30, "Super Potion": 50, "Hyper Potion": 200}
CURE = {"Cheri Berry": ("par",), "Chesto Berry": ("slp",), "Pecha Berry": ("psn", "tox"), "Rawst Berry": ("brn",),
        "Lum Berry": ("par", "slp", "psn", "tox", "brn", "frz", "confuse")}
PINCH = {"Liechi Berry": "atk", "Salac Berry": "spe", "Petaya Berry": "spa"}
MOST = 4

# how many, by the foe team's average level: chances of 0, 1, 2, 3, 4
CHANCES = ((10, (65, 35, 0, 0, 0)), (20, (40, 45, 15, 0, 0)), (35, (20, 35, 30, 15, 0)),
           (50, (10, 20, 30, 25, 15)), (999, (5, 10, 25, 30, 30)))


def level_of(team):
    levels = [t[4] if isinstance(t, tuple) and len(t) > 4 and t[4] else getattr(t, "level", None) or 5 for t in team]
    return sum(levels) / max(1, len(levels))


def roll(foes, mine, rng=None):
    """The items for one battle: a few, or none, by how strong the foes are; never more than 4, and never
    more than either side has creatures (each carries at most one)."""
    rng = rng or random.Random()
    level = level_of(foes)
    weights = next(w for top, w in CHANCES if level < top)
    n = rng.choices(range(5), weights)[0]
    n = min(n, MOST, len(foes), len(mine))
    pool = sorted(k for k, (_, _, lowest) in ITEMS.items() if lowest <= level)
    return rng.sample(pool, n) if n else []


def foe_assign(items, team, rng=None):
    """The trainer's choice of who carries what (team: battle.Mon list). Sensible, not perfect:
    healing on its sturdiest, Quick Claw on a slow one, pinch berries where they help."""
    rng = rng or random.Random()
    free = list(range(len(team)))
    out = {}

    def take(i, item):
        out[i] = item
        free.remove(i)

    def bulk(i):
        m = team[i]
        return m.maxhp + m.stats["def"] + m.stats["spd"]

    for item in sorted(items, key=lambda k: ITEMS[k][0] != "held"):
        if not free:
            break
        kind = ITEMS[item][0]
        if item == "Quick Claw":
            i = min(free, key=lambda i: team[i].stats["spe"])
        elif kind == "pinch":
            stat = PINCH[item]
            i = max(free, key=lambda i: team[i].stats[stat if stat != "spe" else "atk"])
        elif kind == "heal" or item in ("Leftovers", "Shell Bell", "Focus Band"):
            i = max(free, key=bulk)
        else:
            i = rng.choice(free)
        take(i, item)
    return out
