"""Evolution — like Pokémon.

Five animals can evolve so far, into their middle stage (his test, 2026-10-26; the final
stages are not made yet): Critter → Glowtail, Squid → Nimbusdrift, Lanternwing → Beacon
Moth, Brawlhop → Thudhop, Sporeling → Sporestride. An evolved animal is the same
one, bigger, with more to it: each class draws its extras when `stage` is 2 (life.py,
beasts.py). Its battle stats are its new species' (battle.SPECIES).

From an animal's stats card, "Evolve" plays the evolution, about four seconds:
the screens dim and specks of light gather; the animal turns to a white shape that
flickers between its old and new forms, faster and faster; a white flash; and there it
is, evolved, with a banner saying so.
"""

import contextlib
import math
import random

import pygame

import art
import beasts
import life
from apex import OFFSET, ease
from art import glow, mix
from battle import cloth, draw_elsewhere, species_of

EVOLVES = {"Duskling": "Glowtail", "Driftlet": "Nimbusdrift", "Lanternwing": "Beaconwing",
           "Brawlhop": "Thudhop", "Sporeling": "Sporestride",
           # page one of the Forest Dex filled in (2026-10-27): every line #010-#048 has three stages
           "Glowtail": "Cometail", "Nimbusdrift": "Skyveil", "Beaconwing": "Hearthwing", "Thudhop": "Titanhop",
           "Gloamooze": "Gloomdrape", "Gloomdrape": "Nightmire", "Cairncurl": "Cairnspire", "Cairnspire": "Cairnhold",
           "Luminpede": "Luminthread", "Luminthread": "Glowcoil", "Lilyfin": "Lilyveil", "Lilyveil": "Lotuscrest",
           "Canopod": "Boughgrip", "Boughgrip": "Canopolis", "Gloomflit": "Gloomglide", "Gloomglide": "Nightshroud",
           "Glimmerfly": "Glimmerwyrm", "Glimmerwyrm": "Prismwyrm", "Mistwisp": "Mistshade", "Mistshade": "Mistwraith",
           "Mossdelve": "Mossburrow", "Mossburrow": "Mossquake",
           # the starters' lines, all three stages (2026-10-27)
           "Mossprance": "Lichenmane", "Lichenmane": "Eldermane",
           "Kindlet": "Smoldershell", "Smoldershell": "Pyreclad",
           "Pippalotl": "Frillotl", "Frillotl": "Leviolotl"}
# How tall each creature is, in feet, the way the Pokédex gives it (his rules, 2026-10-27):
# like Pokémon, a middle stage is about 2-4 ft and a final one mostly 4-6 ft; Dragonite's 7'03"
# is the most he will have, and only rarely (Prismwyrm and Leviolotl here); nothing like
# Steelix. With 200+ creatures planned, most stay small.
HEIGHT = {
    "Mossprance": 2.0, "Lichenmane": 3.6, "Eldermane": 6.2,
    "Kindlet": 1.4, "Smoldershell": 3.0, "Pyreclad": 5.6,
    "Pippalotl": 1.5, "Frillotl": 3.3, "Leviolotl": 6.8,
    "Duskling": 1.0, "Glowtail": 2.6, "Cometail": 4.6,
    "Driftlet": 0.8, "Nimbusdrift": 2.2, "Skyveil": 4.9,
    "Gloamooze": 1.2, "Gloomdrape": 2.4, "Nightmire": 3.9,
    "Cairncurl": 0.9, "Cairnspire": 2.0, "Cairnhold": 3.6,
    "Luminpede": 1.1, "Luminthread": 3.0, "Glowcoil": 5.9,
    "Lilyfin": 1.3, "Lilyveil": 2.8, "Lotuscrest": 4.8,
    "Canopod": 1.0, "Boughgrip": 2.2, "Canopolis": 4.0,
    "Lanternwing": 1.0, "Beaconwing": 2.1, "Hearthwing": 3.4,
    "Gloomflit": 0.8, "Gloomglide": 2.0, "Nightshroud": 4.4,
    "Glimmerfly": 1.1, "Glimmerwyrm": 3.1, "Prismwyrm": 7.2,
    "Mistwisp": 1.0, "Mistshade": 2.6, "Mistwraith": 4.9,
    "Brawlhop": 1.3, "Thudhop": 3.1, "Titanhop": 5.2,
    "Mossdelve": 0.9, "Mossburrow": 2.3, "Mossquake": 4.1,
    "Sporeling": 1.2, "Sporestride": 2.9,
    "Moonhoot": 1.0, "Frostpaw": 1.3, "Fluffhorn": 1.8, "Shimmerchirp": 0.7, "Steambara": 2.0,
    "Embercling": 1.1, "Vaporwobble": 1.4, "Rimeslink": 1.0, "Coppernib": 0.6, "Bramblit": 1.1,
    "Thistlume": 0.9, "Runelet": 1.4, "Sparkfly": 0.4, "Murkling": 1.2, "Glintshell": 0.9,
    # pages two and three (2026-10-27)
    "Sporecrown": 4.6, "Frostslink": 2.6, "Hailmaw": 5.0, "Copperclad": 1.8, "Voltbastion": 3.9,
    "Duskhoot": 2.2, "Lunarch": 4.4, "Glimmerpaw": 2.6, "Auroracle": 4.3, "Cragfluff": 3.0, "Peakcloak": 5.0,
    "Shimmertrill": 1.9, "Boreallume": 4.6, "Steamsoak": 3.4, "Geyserbelly": 5.1, "Cindercling": 2.4,
    "Magmascale": 4.8, "Vaporbell": 2.6, "Stormbloom": 4.4, "Bramblesnare": 2.4, "Thornregent": 4.5,
    "Thistlegaze": 2.0, "Thistleseer": 3.8, "Runestand": 3.2, "Runewarden": 5.5, "Arcfly": 1.1, "Thunderfly": 3.0,
    "Murkgloop": 2.5, "Murkdredge": 4.2, "Glintdome": 2.0, "Glintcitadel": 4.0,
    "Geodling": 1.2, "Geodcrest": 2.6, "Geodsage": 4.3, "Humlet": 0.8, "Humchime": 2.1, "Resonarch": 4.4,
    "Dripling": 1.0, "Dripspire": 2.5, "Stalagdeep": 4.7, "Lumicrawl": 1.0, "Lumitrek": 2.6, "Lumicaravan": 4.6,
    "Umbrit": 0.9, "Umbrage": 2.4, "Umbravast": 5.2, "Ferrodig": 1.3, "Ferrodrill": 2.9, "Ferrocore": 4.9,
    "Shardling": 1.5, "Shardfang": 3.4, "Shardsovereign": 6.6, "Pebblefist": 1.6, "Cobblefist": 3.3, "Quarryfist": 5.6,
    "Twinklet": 0.9, "Twinkstride": 2.4, "Celestide": 4.5, "Tufflet": 1.2, "Tuftrot": 2.8, "Meadowmane": 4.9,
    "Meteorlet": 0.7, "Meteorblaze": 2.2, "Starforge": 5.0, "Kickbud": 1.4, "Kickbloom": 3.1, "Kickgrove": 5.4,
    "Zaplet": 0.8, "Zapstreak": 2.3, "Zaptempest": 4.8, "Dreamote": 0.6, "Dreamwing": 2.0, "Dreamloom": 4.1,
    "Dustlet": 0.7, "Dustwhirl": 2.4, "Dustcyclone": 4.7, "Wishlet": 0.8, "Wishlantern": 2.3, "Wishhaven": 4.4,
}


# pages four to six (2026-10-27): (first, middle, final) heights in feet, and the two legendaries
_H4 = {
    "Petalpip": (0.8, 2.0, 3.6), "Lullabud": (1.0, 2.6, 4.4), "Gleamwick": (0.7, 1.8, 3.9), "Hushling": (1.0, 2.5, 4.6),
    "Splashkin": (1.4, 3.0, 5.2), "Mistmote": (0.6, 1.9, 3.8), "Slatelet": (1.1, 2.6, 4.9), "Foamlet": (0.9, 2.2, 4.0),
    "Reedlet": (1.3, 3.1, 5.0), "Ripplet": (0.8, 2.2, 4.8), "Bubblo": (0.6, 1.6, 3.4), "Siltpaw": (1.2, 2.8, 4.7),
    "Barkling": (1.5, 3.3, 5.8), "Fernflit": (0.7, 2.0, 3.9), "Hollowink": (1.1, 2.7, 5.1), "Sapsip": (0.5, 1.7, 3.5),
    "Rubblet": (1.0, 2.6, 4.5), "Quillnip": (0.9, 2.1, 4.2), "Echolet": (0.7, 2.0, 4.1), "Sigilet": (1.6, 3.4, 5.9),
    "Snowpuff": (1.0, 2.5, 4.6), "Shiverling": (1.2, 3.0, 5.4), "Glacelet": (0.7, 2.1, 4.3), "Conelet": (0.8, 2.0, 3.7),
    "Ashpaw": (1.1, 2.7, 4.9), "Sulfling": (1.0, 2.3, 4.2), "Lavalet": (0.8, 2.2, 4.4), "Obsidling": (1.3, 3.2, 5.6),
    "Gongling": (1.3, 3.1, 5.5), "Spirelet": (0.9, 2.4, 4.6), "Dueljab": (1.4, 3.3, 5.3), "Mycelet": (0.9, 2.4, 4.4),
    "Deepling": (1.0, 2.9, 5.7), "Quartzlet": (1.0, 2.5, 4.8), "Gemmet": (0.6, 1.8, 3.6), "Starbud": (0.9, 2.3, 4.1),
    "Breezlet": (0.6, 1.9, 4.0), "Dewlet": (0.7, 1.9, 3.8),
}
from battle import _PAGE4 as _P4  # noqa: E402
for _a, _b, _c, *_ in _P4:
    HEIGHT[_a], HEIGHT[_b], HEIGHT[_c] = _H4[_a]
HEIGHT.update(Elderglow=5.8, Moonward=6.3)
# page six (2026-10-27): (first, middle, final) heights in feet
_H6 = {
    "Burrlet": (0.5, 1.6, 3.4), "Zingle": (0.4, 1.3, 3.2), "Mirelet": (0.8, 2.2, 4.3), "Smudgit": (0.7, 2.0, 4.0),
    "Stumplet": (1.2, 2.9, 5.2), "Fizzlet": (0.7, 2.1, 4.6), "Fumelet": (0.9, 2.3, 4.4), "Bulblet": (0.6, 1.8, 3.9),
    "Delvelet": (1.1, 3.0, 5.9), "Pomlet": (0.6, 1.7, 3.8),
}
from battle import _PAGE6 as _P6  # noqa: E402
for _a, _b, _c, *_ in _P6:
    HEIGHT[_a], HEIGHT[_b], HEIGHT[_c] = _H6[_a]
HEIGHT.update(Tanglet=0.8, Tanglash=2.4, Tanglehold=4.6, Tumblet=0.4, Tumbleglass=1.5, Tumblereef=3.6)  # wave7.py


def feet(species):
    """Its height the Pokédex way, e.g. 3'07"."""
    h = HEIGHT.get(species)
    if h is None:
        return "?"
    inches = round(h * 12)
    return f"{inches // 12}'{inches % 12:02}\""


def growth(species):
    """How much bigger than its first stage an evolved creature is drawn: by how much taller
    it is, eased (a 6x taller final stage is drawn about 3x bigger, so it still fits the glade)."""
    first, _ = stage_of(species)
    a, b = HEIGHT.get(first), HEIGHT.get(species)
    if not a or not b:
        return 1.0
    return max(1.0, min(3.2, (b / a) ** 0.6))


def species_at(first, stage):
    """The name of `first`'s line at that stage (None if the line has not got that far)."""
    name = first
    for _ in range(stage - 1):
        name = EVOLVES.get(name)
        if name is None:
            return None
    return name


def stage_of(species):
    """(its line's first stage, which stage it is)."""
    n = 1
    while species in EVOLVED_FROM:
        species, n = EVOLVED_FROM[species], n + 1
    return species, n
# pages two and three of the Forest Dex (2026-10-27): every line from #049 to #144 has three stages
EVOLVES.update({
    "Sporestride": "Sporecrown", "Rimeslink": "Frostslink", "Frostslink": "Hailmaw",
    "Coppernib": "Copperclad", "Copperclad": "Voltbastion", "Moonhoot": "Duskhoot", "Duskhoot": "Lunarch",
    "Frostpaw": "Glimmerpaw", "Glimmerpaw": "Auroracle", "Fluffhorn": "Cragfluff", "Cragfluff": "Peakcloak",
    "Shimmerchirp": "Shimmertrill", "Shimmertrill": "Boreallume", "Steambara": "Steamsoak", "Steamsoak": "Geyserbelly",
    "Embercling": "Cindercling", "Cindercling": "Magmascale", "Vaporwobble": "Vaporbell", "Vaporbell": "Stormbloom",
    "Bramblit": "Bramblesnare", "Bramblesnare": "Thornregent", "Thistlume": "Thistlegaze", "Thistlegaze": "Thistleseer",
    "Runelet": "Runestand", "Runestand": "Runewarden", "Sparkfly": "Arcfly", "Arcfly": "Thunderfly",
    "Murkling": "Murkgloop", "Murkgloop": "Murkdredge", "Glintshell": "Glintdome", "Glintdome": "Glintcitadel",
})
from battle import _PAGE3, _PAGE4, _PAGE6, _PAGE7  # noqa: E402
for _a, _b, _c, *_ in _PAGE3 + _PAGE4 + _PAGE6 + _PAGE7:
    EVOLVES[_a], EVOLVES[_b] = _b, _c
EVOLVED_FROM = {v: k for k, v in EVOLVES.items()}
LENGTH = 4.0      # the evolution itself
BANNER = 2.6      # how long "… evolved into …!" stays up afterwards
KEY = (1, 254, 3)
SPARK = (200, 230, 255)


def set_stage(obj, stage):
    """Make an animal stage 1, 2 or 3 of its line. Reversible: the first-stage values are
    kept the first time."""
    first = obj.__dict__.setdefault("_first", dict(size=obj.__dict__.get("_size", getattr(obj, "size", None)), species=getattr(obj, "species", None),
                                                   name=species_of(obj)))
    obj.stage = stage
    if first["size"] is not None:
        obj.size = first["size"] * growth(species_at(first["name"], stage) or first["name"])
    obj.species = species_at(first["name"], stage) if stage > 1 else first["species"]
    if type(obj).__name__ == "Critter":
        if stage >= 2:
            obj.SEG = 6.2 if stage > 2 else 5.2  # a longer body and tail
        else:
            obj.__dict__.pop("SEG", None)
    if type(obj).__name__ == "Slug":
        obj.seg = 2.0 * obj.size  # its body grows with it
    if type(obj).__name__ == "Millipede":
        base = obj.__dict__.setdefault("_n", obj.n)
        obj.n = base + 6 * (stage - 1)  # more segments each stage
    if type(obj).__name__ == "Squid":
        long = obj.__dict__.setdefault("_long", [])
        if stage >= 2 and not long:  # two long hunting tentacles
            for _ in range(2):
                arm = [[obj.x, obj.y] for _ in range(16)]
                long.append(arm)
                obj.arms.append(arm)
        elif stage == 1 and long:
            obj.arms = [a for a in obj.arms if not any(a is b for b in long)]
            long.clear()


SECOND, THIRD = 0.07, 0.01  # his odds (2026-10-27) of a wild animal being its line's middle or final stage


def wild_stage(obj, rng=random):
    """Each animal that comes out in the wild: mostly a first stage, 7% of the time its
    middle stage, 1% its final one ("oh look, a … on my screen"). A line that has no such
    stage yet stays a first stage; one with no final stage yet gives its middle at 1% too."""
    first = obj.__dict__.get("_first", {}).get("name") or species_of(obj)
    second = EVOLVES.get(first)
    third = EVOLVES.get(second) if second else None
    r = rng.random()
    want = 1
    if r < THIRD and (third or second):
        want = 3 if third else 2
    elif r < THIRD + SECOND and second:
        want = 2
    if want != getattr(obj, "stage", 1):
        set_stage(obj, want)


@contextlib.contextmanager
def no_glow():
    """While drawing a silhouette: no soft glows, just the animal's own shape."""
    saved = life.glow, beasts.glow
    life.glow = beasts.glow = lambda *a, **k: None
    try:
        yield
    finally:
        life.glow, beasts.glow = saved


class Evolution:
    def __init__(self, animal, species, t):
        self.a, self.obj, self.t0, self.now = animal, animal.obj, t, t
        self.old, self.new = species, EVOLVES[species]
        self.was = getattr(animal.obj, "stage", 1)  # it goes from this stage to the next
        self.to = self.was + 1
        self.obj.gone = True  # drawn here until it is done
        self.swapped = self.shown = False
        self.scratch = art.solid()
        self.veils = {}
        rng = random.Random()
        self.sparks = [(rng.uniform(0, math.tau), rng.uniform(30, 90), rng.uniform(0.6, 1.4)) for _ in range(26)]

    @property
    def done(self):
        return self.now - self.t0 > LENGTH + BANNER

    def update(self, t):
        self.now = t
        f = t - self.t0
        if f >= 3.2 and not self.swapped:  # under the flash: it has evolved
            set_stage(self.obj, self.to)
            self.swapped = True
        if f >= 3.4 and not self.shown:
            self.obj.gone = False  # from here it is in the glade again, lit like everyone else
            self.shown = True

    def finish(self):
        """He walked away mid-way: it simply has evolved."""
        if not self.swapped:
            set_stage(self.obj, self.to)
            self.swapped = True
        self.obj.gone = False
        self.now = self.t0 + LENGTH + BANNER + 1

    def where(self):
        x, y = self.a.pos()
        return (x - OFFSET[0], y - OFFSET[1]) if self.a.low else (x, y)

    def silhouette(self, s, t, stage):
        """The animal (as `stage`) as a plain white shape, where it is."""
        set_stage(self.obj, stage)
        x, y = self.where()
        box = pygame.Rect(round(x) - 70, round(y) - 70, 140, 140).clip(self.scratch.get_rect())
        if box.w > 0 and box.h > 0:
            self.scratch.set_clip(box)
            self.scratch.fill(KEY, box)
            with no_glow():
                for part in ("draw", "shine"):
                    fn = getattr(self.obj, part, None)
                    if fn:
                        fn(self.scratch, t)
            self.scratch.set_clip(None)
            shape = pygame.mask.from_threshold(self.scratch.subsurface(box), KEY, (1, 1, 1, 255))
            shape.invert()
            s.blit(shape.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), box.topleft)
        set_stage(self.obj, self.to if self.swapped else self.was)

    def draw(self, s, low, t):
        self.now = t
        f = t - self.t0
        w, h = s.get_size()
        # the screens dim while it happens, and brighten again after
        dim = ease(f / 0.5) if f < LENGTH else 1 - ease((f - LENGTH) / 0.6)
        if dim > 0:
            veil = self.veils.get((w, h))
            if veil is None:
                veil = self.veils[(w, h)] = art.solid((w, h))
                veil.fill((8, 6, 22))
            veil.set_alpha(round(150 * dim))
            s.blit(veil, (0, 0))
        if low == self.a.low:
            x, y = self.where()
            if f < 0.6:  # it glows brighter and brighter
                draw_elsewhere(s, self.a, (x, y), t, self.scratch)
                glow(s, x, y, 30, SPARK, round(min(1.0, f / 0.6) * 140) // 12 * 12)
            elif f < 3.4:  # a white shape, flickering between old and new, faster and faster
                k = ease((f - 0.6) / 2.6)
                period = 0.5 - 0.44 * k
                stage = self.to if int((f - 0.6) / period) % 2 else self.was
                glow(s, x, y, int(28 + 20 * k), SPARK, round(100 + 100 * k) // 12 * 12)
                self.silhouette(s, t, stage)
            # specks of light gather in, then burst out once it has evolved
            for a, r, sp in self.sparks:
                if f < 3.2:
                    d = r * (1 - ((f * sp) % 1.0))
                    c = mix(SPARK, (255, 255, 255), 0.5)
                else:
                    d = r * ease((f - 3.2) / 1.2) * 1.4
                    c = mix(SPARK, (255, 236, 160), 0.5)
                if 0 < d and (f < 3.2 or f < 4.6):
                    s.set_at((round(x + math.cos(a + f) * d), round(y + math.sin(a + f) * d * 0.8)), c)
            self.banner(s, f)
        # the white flash
        flash = ease((f - 3.0) / 0.25) if f < 3.4 else 1 - ease((f - 3.4) / 0.6)
        if flash > 0:
            white = self.veils.get(("white", w, h))
            if white is None:
                white = self.veils[("white", w, h)] = art.solid((w, h))
                white.fill((255, 255, 255))
            white.set_alpha(round(255 * flash))
            s.blit(white, (0, 0))

    def banner(self, s, f):
        """What is happening, in words, at the top of that screen."""
        if f < 3.2:
            words = f"What? {self.old} is evolving!"
            k = ease(f / 0.4)
        else:
            words = f"Congratulations! Your {self.old} evolved into {self.new}!"
            k = ease((f - 3.6) / 0.4) * (1 - ease((f - LENGTH - BANNER + 0.5) / 0.5))
        if k <= 0 or self.font is None:
            return
        img = self.font.render(words, False, (255, 255, 255))
        r = pygame.Rect(0, 0, img.get_width() + 24, img.get_height() + 12)
        r.midtop = (s.get_width() // 2, 16)
        cloth(s, r, (196, 140, 255), alpha=round(235 * k))
        img.set_alpha(round(255 * k))
        s.blit(img, img.get_rect(center=r.center))

    font = None  # set by the glade

