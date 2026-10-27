"""Giving each other room (his ask, 2026-10-27).

Animals used to pick where to go without looking, so two would often stop on top of each other
and be hard to click. Now a walker or a ground slug choosing somewhere new skips spots another
animal is standing on (or walking to), and one that finds itself resting on top of another soon
wanders off."""

GAP = 30  # how far apart (canvas pixels) they like to stop
KINDS = ("Walker", "Slug", "Critter", "Millipede")


def gather(content):
    """Let the ground animals of one place (or one lower screen) know about each other."""
    group, seen = [], set()
    for o in list(getattr(content, "lives", [])) + list(getattr(content, "parts", [])):
        if isinstance(o, tuple):  # a Scene's parts are (kind, thing)
            o = o[1]
        if id(o) not in seen and type(o).__name__ in KINDS:
            seen.add(id(o))
            group.append(o)
    for o in group:
        o.neighbours = group


def where(o):
    """Where an animal is, or where it is headed if it is walking somewhere."""
    name = type(o).__name__
    if name == "Walker":
        if o.wait <= 0:
            return o.target, o.ground(o.target)
        return o.x, o.ground(o.x)
    head = getattr(o, "head", None)
    if head is not None:
        return head[0], head[1]
    x, y = getattr(o, "x", None), getattr(o, "y", None)
    return (x, y) if x is not None and y is not None else None


def crowded(me, x, y, gap=GAP):
    """Is another animal (out, not in a battle) standing at x, y, or on its way there?"""
    for o in getattr(me, "neighbours", ()):
        if o is me or getattr(o, "gone", False):
            continue
        p = where(o)
        if p is not None and abs(p[0] - x) < gap and abs(p[1] - y) < gap * 0.6:
            return True
    return False


def tailing(me, gap=GAP):
    """Is `me` (a walker on its way) right behind another walker going the same way? Then the
    two would walk along on top of each other."""
    for o in getattr(me, "neighbours", ()):
        if o is me or getattr(o, "gone", False) or type(o).__name__ != "Walker":
            continue
        ahead = (o.x - me.x) * me.facing
        if 0 <= ahead < gap and abs(o.y - me.y) < gap * 0.6 and (o.wait > 0 or o.facing == me.facing):
            return True
    return False
