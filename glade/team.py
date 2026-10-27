"""Your creatures: the ones you have caught, and every animal's own strength.

- **IVs** (Gen 3 individual values, 0-31 in each of the six stats): every single animal in
  the glade has its own, rolled the first time anything asks (`ivs_of`), so two Frostpaws
  can be a strong one and a weak one. The stats card draws them as a six-sided web.
- **Catching**: battle a wild animal from its stats card, wear it down, then throw a glow
  jar (`catch_shakes`, the Gen 3 formula). What you catch leaves the wild and is kept in
  ~/.local/state/glade/creatures.json: species, IVs and its four moves. The first six are
  your team; the Battle Tower (tower.py) lets you pick any six.
- **Kept animals on the field**: a caught one has no body in the glade any more, so for a
  battle one is made just to be drawn (`body`, like the Forest Dex's pictures).
"""

import json
import math
import os
import random

HOME = os.path.expanduser("~")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local/state"), "glade",
                     "creatures.json")
TEAM = 6
CATCH_RATE = 120  # how easy the glade's animals are to catch (Gen 3 scale: 3 hard ... 255 easy)


# --- IVs -------------------------------------------------------------------------------------

def roll_ivs(rng=random):
    return tuple(rng.randint(0, 31) for _ in range(6))


def ivs_of(obj):
    """This animal's own IVs (HP, Atk, Def, SpA, SpD, Spe), rolled once and kept on it."""
    if obj is None:
        return roll_ivs()
    ivs = getattr(obj, "ivs", None)
    if ivs is None:
        ivs = roll_ivs()
        try:
            obj.ivs = ivs
        except AttributeError:
            pass
    return ivs


# --- natures (Gen 3: 25 of them; each raises one stat by 10% and lowers another, five are neutral) ---

NATURE_STATS = ("atk", "def", "spe", "spa", "spd")  # the Gen 3 order of the table
NATURES = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax",
           "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash",
           "Calm", "Gentle", "Sassy", "Careful", "Quirky"]
EVS = (84,) * 6  # every creature's effort values: 84 in each stat, the standard spread here


def nature_effect(nature):
    """(the stat it raises, the stat it lowers), or (None, None) for a neutral one."""
    i = NATURES.index(nature) if nature in NATURES else 0
    up, down = NATURE_STATS[i // 5], NATURE_STATS[i % 5]
    return (None, None) if up == down else (up, down)


def nature_of(obj):
    """This animal's own nature, chosen once and kept on it (like its IVs)."""
    if obj is None:
        return random.choice(NATURES)
    n = getattr(obj, "nature", None)
    if n is None:
        n = random.choice(NATURES)
        try:
            obj.nature = n
        except AttributeError:
            pass
    return n


# --- the creatures you have caught -------------------------------------------------------------
# Organised like the PC boxes in Pokémon Emerald: a party of six, and boxes of thirty you can
# move them in and out of (storage.py is the screen for it).

BOXES, PER_BOX = 8, 30


class Kept:
    """One caught creature."""

    def __init__(self, species, ivs, moves, nature=None, evs=None, uid=None, wins=0):
        self.species, self.ivs, self.moves = species, tuple(ivs), list(moves)
        self.nature = nature or random.choice(NATURES)
        self.evs = tuple(evs or EVS)
        self.uid = uid or "%08x" % random.getrandbits(32)  # which one it is, wherever it is kept
        self.wins = wins  # Battle Tower battles it fought in and won: at 3, then 6 more, it can evolve

    def as_dict(self):
        return dict(species=self.species, ivs=list(self.ivs), moves=self.moves, nature=self.nature,
                    evs=list(self.evs), uid=self.uid, wins=self.wins)


# His naming rule (2026-10-27): one word, no real animal in it (only an attached "fly"). Old
# saves still say the old names, so they are read through this.
RENAMED = {
    "Lantern Moth": "Lanternwing",
    "Beacon Moth": "Beaconwing",
    "Dusk Bat": "Gloomflit",
    "Glimmer Drake": "Glimmerfly",
    "Mist Wisp": "Mistwisp",
    "Bruiser Toad": "Thudhop",
    "Brawl Toad": "Brawlhop",
    "Moss Mole": "Mossdelve",
    "Rime Newt": "Rimeslink",
    "Copper Beetle": "Coppernib",
    "Moon Owlet": "Moonhoot",
    "Frost Kit": "Frostpaw",
    "Aurora Finch": "Shimmerchirp",
    "Ember Gecko": "Embercling",
    "Vapor Jelly": "Vaporwobble",
    "Gloamslug": "Gloamooze",
    "Cairnsnail": "Cairncurl",
    "Driftquid": "Driftlet",
    "Nimbusquid": "Nimbusdrift",
    "Mossfawn": "Mossprance",
    "Lichenhart": "Lichenmane",
    "Elderhart": "Eldermane",
    "Duskit": "Duskling",
}


def _kept(d):
    try:
        return Kept(RENAMED.get(d["species"], d["species"]), d["ivs"], d["moves"], d.get("nature"), d.get("evs"), d.get("uid"),
                    d.get("wins", 0)) if d else None
    except (KeyError, TypeError):
        return None


class Collection:
    """Everything you have caught: `party` (6 slots) and `boxes` (BOXES x PER_BOX slots);
    an empty slot is None."""

    def __init__(self):
        data = stats()
        party = [_kept(d) for d in data.get("party", [])][:TEAM]
        self.party = party + [None] * (TEAM - len(party))
        boxes = data.get("boxes", [])
        self.boxes = []
        for b in range(BOXES):
            row = [_kept(d) for d in (boxes[b] if b < len(boxes) else [])][:PER_BOX]
            self.boxes.append(row + [None] * (PER_BOX - len(row)))
        self.names = (data.get("box_names") or [f"Box {i + 1}" for i in range(BOXES)])[:BOXES]
        self.best = data.get("tower_best", 0)
        self.tried = data.get("tower_tried", False)  # a run at the Battle Tower: then you may catch
        saved = [d for d in data.get("party", []) if d] + [d for row in data.get("boxes", []) for d in row if d]
        if any(not d.get("nature") or not d.get("uid") for d in saved):
            self.save()  # creatures kept before natures (or ids) existed: theirs are chosen now, for good

    def find(self, uid):
        for k in self.everyone():
            if k.uid == uid:
                return k
        return None

    def members(self):
        return [k for k in self.party if k]

    def everyone(self):
        return self.members() + [k for row in self.boxes for k in row if k]

    def add(self, kept):
        """Into the party if there is room, otherwise the first free box slot. Returns where
        it went: "party" or the box's name, or None if everything is full."""
        for i, k in enumerate(self.party):
            if k is None:
                self.party[i] = kept
                return "party"
        for b, row in enumerate(self.boxes):
            for i, k in enumerate(row):
                if k is None:
                    row[i] = kept
                    return self.names[b]
        return None

    def compact(self):
        """The party has no gaps: everyone moves up."""
        members = self.members()
        self.party = members + [None] * (TEAM - len(members))

    def save(self):
        self.compact()
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        data = dict(party=[k.as_dict() if k else None for k in self.party],
                    boxes=[[k.as_dict() if k else None for k in row] for row in self.boxes],
                    box_names=self.names, tower_best=self.best, tower_tried=self.tried)
        tmp = STATE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, STATE)


def stats():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def team():
    return Collection().members()


# --- the glow jar (Gen 3 catch formula) --------------------------------------------------------

def catch_shakes(maxhp, hp, status, rng=random, rate=CATCH_RATE):
    """How many times the jar wobbles (0-3), or 4 if it holds. Gen 3: the lower its HP the
    likelier; asleep or frozen x2, paralyzed, poisoned or burned x1.5."""
    a = (3 * maxhp - 2 * hp) * rate // (3 * maxhp)
    if status in ("slp", "frz"):
        a *= 2
    elif status in ("par", "psn", "tox", "brn"):
        a = a * 3 // 2
    if a >= 255:
        return 4
    b = int(1048560 / math.sqrt(math.sqrt(16711680 / max(1, a))))
    for i in range(4):
        if rng.randint(0, 65535) >= b:
            return i
    return 4


# --- a body to draw a kept creature with -------------------------------------------------------

class Drawn:
    """A body made just to be drawn on the battle field, standing in for an animal in the
    glade (the same shape as apex.Prey: `obj`, `low`, `pos()`)."""

    low = False

    def __init__(self, obj, perched=False):
        self.obj, self.perched = obj, perched

    def pos(self):
        o = self.obj
        if self.perched:
            return o.x, o.y - 8 * o.size
        name = type(o).__name__
        if name == "Slug":
            return o.track.at(o.d)[:2]
        if name in ("Millipede", "Critter", "Fish"):
            pts = getattr(o, "pts", None)
            return pts[0][:2] if pts else o.track.at(o.d)[:2]
        return o.x, o.y


def body(species, at=(480, 300)):
    """A Drawn creature of `species`, standing at `at` (well inside the canvas, so the
    battle can copy it from there onto the field)."""
    import dex
    thing = dex.specimen(species)
    dx, dy = at[0] - dex.PW // 2, at[1] - dex.PH // 2
    if isinstance(thing, tuple):  # a tree dweller: draw it like a perched tree squid
        from squids import TreeSquid
        sq = TreeSquid({"kind": "app", "id": "kept"}, at[0], at[1], 1.0)
        if thing[1] == "owlet":
            sq.kind = "owlet"
        if len(thing) > 2:  # Boughgrip, Canopolis
            from evolve import growth, species_at
            sq.stage = thing[2]
            sq.size = min(1.6, growth(species_at("Moonhoot" if thing[1] == "owlet" else "Canopod", thing[2])))
        return Drawn(sq, perched=True)
    shift(thing, dx, dy)
    return Drawn(thing)


def shift(o, dx, dy):
    """Move a freshly made specimen by (dx, dy)."""
    for name in ("x", "home", "target"):
        v = getattr(o, name, None)
        if isinstance(v, (int, float)):
            setattr(o, name, v + dx)
        elif isinstance(v, tuple) and len(v) == 2:
            setattr(o, name, (v[0] + dx, v[1] + dy))
    if isinstance(getattr(o, "y", None), (int, float)):
        o.y += dy
    if hasattr(o, "xr") and isinstance(o.xr, tuple):
        o.xr = (o.xr[0] + dx, o.xr[1] + dx)
    if hasattr(o, "ground") and callable(o.ground):
        g = o.ground
        o.ground = lambda x, g=g: g(x - dx) + dy
    if hasattr(o, "region") and isinstance(o.region, tuple):
        x0, y0, w, h = o.region
        o.region = (x0 + dx, y0 + dy, w, h)
    for arm in getattr(o, "arms", None) or []:
        for p in arm:
            p[0] += dx
            p[1] += dy
    if hasattr(o, "trail") and isinstance(o.trail, list):
        o.trail = [(px + dx, py + dy) for px, py in o.trail] if o.trail and isinstance(o.trail[0], tuple) else o.trail
    if hasattr(o, "tail") and isinstance(o.tail, list):
        o.tail = [(px + dx, py + dy) for px, py in o.tail]
    if hasattr(o, "track"):
        from life import Track
        o.track = Track([(px + dx, py + dy) for px, py in o.track.pts], up=o.track.up)
    if hasattr(o, "pts") and isinstance(o.pts, list):
        o.pts = [[p[0] + dx, p[1] + dy] + list(p[2:]) for p in o.pts]
    water = getattr(o, "water", None)
    if water is not None and hasattr(water, "cx"):
        water.cx += dx
        water.cy += dy
