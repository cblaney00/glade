"""Every evolution line lives in one place only (2026-11-10, his ask and pick: "creatures from
any area can be found at the main glade, but there are creatures (especially strong ones) that
should be limited to their own area"). The second wave (beasts.py) used to be in every place, and
the far places borrowed animals from each other; now each kind that was in more than one place has
its one home here, chosen by what it is and its type (and so each place keeps a few of its own).
The tiny background ones (Driftlet squid, Gloamooze slugs, Cairncurl snails, Lilyfin fish) are not
walkers or fliers and still live everywhere.

scenes.second_wave and lower.py ask `allowed`; lore.WHERE (where.py) is made from the result.
A new kind listed in several places must get its home here.
"""

HOME = {
    # the second wave, which used to be everywhere
    "toad": "river", "mole": "rocks", "sporeling": "hollow", "newt": "falls", "beetle": "forest",
    "bat": "ruins", "moth": "orchard", "drake": "waterfall", "wisp": "bog",
    # the Glade's own gentle ones
    "petal": "glade", "lulla": "glade", "wick": "glade", "hush": "glade",
    # the rest that more than one place had
    "murk": "grotto", "glint": "river", "goat": "ridge", "wish": "meadow", "ripple": "shore",
    "finch": "peak", "breeze": "bridge", "splash": "waterfall", "foam": "kelp", "bubbl": "kelp",
    "mire": "bog", "rubble": "rocks", "jelly": "springs", "umbra": "temple", "dream": "isles",
    "tuft": "hall", "spark": "gully", "rune": "ruins", "reed": "river", "silt": "bog", "sap": "gully",
    "pebble": "storm", "meteor": "comet", "kick": "bridge", "pom": "garden", "burr": "thorn",
    "mistm": "waterfall", "slate": "temple", "zing": "storm", "thistle": "forest", "bramble": "forest",
    "bark": "forest", "fern": "forest", "hollow": "temple", "smudge": "thorn", "quill": "rocks",
    "sigil": "ruins", "fox": "ridge", "glace": "falls", "capy": "springs", "gecko": "dunes",
    "ash": "springs", "hum": "hollow", "geode": "caverns", "zap": "storm", "starb": "hall",
    "dew": "meadow", "echo": "rocks", "snowp": "ridge", "shiver": "falls", "cone": "peak",
    "fizz": "storm", "sulf": "springs", "lava": "lava", "obsid": "lava", "bulb": "tower",
    "shard": "comet", "myce": "hollow", "quartz": "comet", "gem": "caverns", "twinkle": "meadow",
    "dust": "dunes",
}


def allowed(kind, key):
    """May this kind of animal live in that place?"""
    return HOME.get(kind, key) == key


def only(kinds, key):
    return tuple(k for k in kinds if allowed(k, key))
