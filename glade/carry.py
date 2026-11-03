"""The same animals in the desktop and the game (his ask, 2026-11-03: "what if I find a strong one I
want, then it goes away when I click Wander").

The desktop and the game are two programs, each building the home clearing for itself, so each used
to have its own animals out. Now, when Wander (or any board) opens the game, the desktop notes who
is out at home, above and below, each with its own self (IVs, nature, level, stage, how long it has
left), in $XDG_RUNTIME_DIR/glade-animals.json, and the game's home takes them on. On Rest the game
notes its home the same way and the desktop takes them back. Both build home the same way, so the
animals line up one for one; if they ever don't (a newer glade with other animals), nothing changes.
"""

import json
import os
import time

import world

PATH = os.path.join(world.RUN, "glade-animals.json")
FRESH = 60  # seconds: a note older than this is from some other time


def bodies(content):
    """Every animal of a place in a fixed order: the ones taking turns, the fish, the trees' dwellers."""
    import storm
    if content is None:
        return []
    out = storm.roster(content, everyone=True, any_family=True)
    pond = getattr(content, "pond", None)
    out += list(getattr(pond, "fish", []) if pond is not None else [])
    colony = getattr(content, "colony", None)
    if colony is not None:
        out += [colony.squid[k] for k in sorted(colony.squid, key=str)]
    return out


def homes(glade):
    home = glade.scenes.get("glade")
    return [home, glade.lowers.get("glade")] if home is not None else []


def self_of(o, t):
    from battle import species_of
    from team import ivs_of, nature_of
    import levels
    sp = species_of(o)
    leave = getattr(o, "leave_at", None)
    return dict(kind=type(o).__name__, sp=sp, stage=getattr(o, "stage", 1), gone=bool(getattr(o, "gone", False)),
                caught=bool(getattr(o, "caught", False)), dweller=getattr(o, "kind", None),
                ivs=list(ivs_of(o)), nature=nature_of(o), level=levels.level_of(o, sp) if sp else None,
                left=None if leave is None else max(0.0, leave - t))


def save(glade):
    """Note who is out at home just now, and who they are."""
    if getattr(glade, "lifespans", None) is not None:
        glade.lifespans.settle()  # anyone half-way in or out: done
    t = glade.now()
    note = dict(when=time.time(), places=[[self_of(o, t) for o in bodies(c)] for c in homes(glade)])
    try:
        with open(PATH, "w") as f:
            json.dump(note, f)
    except OSError:
        pass


def load(glade):
    """Home takes on the animals in the note (once; then the note is gone)."""
    try:
        with open(PATH) as f:
            note = json.load(f)
        os.remove(PATH)
    except (OSError, ValueError):
        return False
    if time.time() - note.get("when", 0) > FRESH:
        return False
    from evolve import set_stage
    from battle import species_of
    import storm
    t = glade.now()
    places = [bodies(c) for c in homes(glade)]
    if len(places) != len(note["places"]) or any(len(a) != len(b) for a, b in zip(places, note["places"])):
        return False
    if any(type(o).__name__ != d["kind"] for objs, ds in zip(places, note["places"]) for o, d in zip(objs, ds)):
        return False
    if getattr(glade, "lifespans", None) is not None:
        glade.lifespans.settle()
    for objs, ds in zip(places, note["places"]):
        for o, d in zip(objs, ds):
            try:
                if d["dweller"] is not None and type(o).__name__ == "TreeSquid":  # a tree squid or a Moonhoot
                    o.kind = d["dweller"]
                if d["stage"] != getattr(o, "stage", 1):
                    set_stage(o, d["stage"])
                o.gone, o.caught = d["gone"], d["caught"]
                o.ivs, o.nature = tuple(d["ivs"]), d["nature"]
                if d["level"]:
                    o.wild_level = (species_of(o), d["level"])
                o.leave_at = None if d["left"] is None else t + d["left"]
            except (AttributeError, KeyError, TypeError):
                pass
    if storm.FAMILIES is not None:  # the desktop: whoever came back from the game may stay out
        storm.FAMILIES |= {storm.family(o) for c in homes(glade) for o in storm.roster(c, any_family=True)
                           if not getattr(o, "gone", False)} - {None}
    return True
