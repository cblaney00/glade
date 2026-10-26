"""Battle — an easter egg, Pokémon Showdown style (Gen 3 OU rules).

Click the moon and type "battle". A banner in the top screen's bottom-left corner asks
for two animals: click one (it is yours), then another (its opponent). They are given
random moves that suit them and fight it out in a battle box in that corner. You click
your moves; the opponent chooses its own.

All the numbers follow Gen 3 (Ruby/Sapphire/Emerald): level 100, perfect IVs, 84 EVs
in every stat, neutral natures, Leftovers. The stat and damage formulas, the critical
hit chances, accuracy stages, the type chart, whether a move is physical or special (by
its type, as in Gen 3), sleep/freeze/paralysis/poison/confusion, Protect, multi-hit,
recoil and drain all work the way they do in those games.

The animals and their base stats were chosen as if each were a first or second
evolution (base stat totals of about 380-410).
"""

import math
import random

import pygame

import art
from apex import OFFSET, ease, find_prey
from art import glow, mix
from life import Track, q

# --- types --------------------------------------------------------------------------

# attacking type -> {defending type: multiplier}; everything else is 1x (Gen 3 chart)
CHART = {
    "Normal": {"Rock": .5, "Steel": .5, "Ghost": 0},
    "Fire": {"Fire": .5, "Water": .5, "Grass": 2, "Ice": 2, "Bug": 2, "Rock": .5, "Dragon": .5, "Steel": 2},
    "Water": {"Fire": 2, "Water": .5, "Grass": .5, "Ground": 2, "Rock": 2, "Dragon": .5},
    "Electric": {"Water": 2, "Electric": .5, "Grass": .5, "Ground": 0, "Flying": 2, "Dragon": .5},
    "Grass": {"Fire": .5, "Water": 2, "Grass": .5, "Poison": .5, "Ground": 2, "Flying": .5, "Bug": .5,
              "Rock": 2, "Dragon": .5, "Steel": .5},
    "Ice": {"Fire": .5, "Water": .5, "Grass": 2, "Ice": .5, "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": .5},
    "Fighting": {"Normal": 2, "Ice": 2, "Poison": .5, "Flying": .5, "Psychic": .5, "Bug": .5, "Rock": 2,
                 "Ghost": 0, "Dark": 2, "Steel": 2},
    "Poison": {"Grass": 2, "Poison": .5, "Ground": .5, "Rock": .5, "Ghost": .5, "Steel": 0},
    "Ground": {"Fire": 2, "Electric": 2, "Grass": .5, "Poison": 2, "Flying": 0, "Bug": .5, "Rock": 2, "Steel": 2},
    "Flying": {"Electric": .5, "Grass": 2, "Fighting": 2, "Bug": 2, "Rock": .5, "Steel": .5},
    "Psychic": {"Fighting": 2, "Poison": 2, "Psychic": .5, "Dark": 0, "Steel": .5},
    "Bug": {"Fire": .5, "Grass": 2, "Fighting": .5, "Poison": .5, "Flying": .5, "Psychic": 2, "Ghost": .5,
            "Dark": 2, "Steel": .5},
    "Rock": {"Fire": 2, "Ice": 2, "Fighting": .5, "Ground": .5, "Flying": 2, "Bug": 2, "Steel": .5},
    "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": .5, "Steel": .5},
    "Dragon": {"Dragon": 2, "Steel": .5},
    "Dark": {"Fighting": .5, "Psychic": 2, "Ghost": 2, "Dark": .5, "Steel": .5},
    "Steel": {"Fire": .5, "Water": .5, "Electric": .5, "Ice": 2, "Rock": 2, "Steel": .5},
}
# in Gen 3 a move is physical or special because of its type
PHYSICAL = {"Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "???"}

# pastel badges for each type, in the glade's colours
TYPE_COLOR = {
    "Normal": (214, 206, 190), "Water": (120, 190, 255), "Psychic": (255, 140, 200), "Poison": (196, 130, 240),
    "Bug": (190, 230, 110), "Rock": (214, 186, 120), "Electric": (255, 226, 110), "Dark": (150, 130, 170),
    "Steel": (180, 200, 220), "Ice": (160, 236, 240), "Ghost": (150, 130, 230), "Grass": (130, 226, 140),
    "Ground": (226, 190, 130), "Dragon": (150, 140, 255), "Fire": (255, 160, 110), "Fighting": (230, 120, 110),
    "Flying": (180, 190, 255), "???": (140, 200, 180),
}


def effectiveness(mtype, types):
    m = 1.0
    for t in types:
        m *= CHART.get(mtype, {}).get(t, 1)
    return m


# --- moves (Gen 3 power / accuracy / PP) ---------------------------------------------
# p: power (0 = status move), a: accuracy (None never misses), c: makes contact,
# sec: (chance %, effect) on the target after damage, st: what a status move does,
# up: boosts to the user, down: drops to the target.

def mv(t, p, a, pp, **kw):
    return dict(t=t, p=p, a=a, pp=pp, **kw)


MOVES = {
    "Body Slam": mv("Normal", 85, 100, 15, c=1, sec=(30, "par")),
    "Return": mv("Normal", 102, 100, 20, c=1),
    "Quick Attack": mv("Normal", 40, 100, 30, c=1, prio=1),
    "Double-Edge": mv("Normal", 120, 100, 15, c=1, recoil=3),
    "Bite": mv("Dark", 60, 100, 25, c=1, sec=(30, "flinch")),
    "Crunch": mv("Dark", 80, 100, 15, c=1, sec=(20, {"spd": -1})),
    "Iron Tail": mv("Steel", 100, 75, 15, c=1, sec=(30, {"def": -1})),
    "Swords Dance": mv("Normal", 0, None, 30, up={"atk": 2}),
    "Agility": mv("Psychic", 0, None, 30, up={"spe": 2}),
    "Surf": mv("Water", 95, 100, 15),
    "Water Pulse": mv("Water", 60, 100, 20, sec=(20, "confuse")),
    "Octazooka": mv("Water", 65, 85, 10, sec=(50, {"acc": -1})),
    "Psychic": mv("Psychic", 90, 100, 10, sec=(10, {"spd": -1})),
    "Psybeam": mv("Psychic", 65, 100, 20, sec=(10, "confuse")),
    "Ice Beam": mv("Ice", 95, 100, 10, sec=(10, "frz")),
    "Confuse Ray": mv("Ghost", 0, 100, 10, st="confuse"),
    "Hypnosis": mv("Psychic", 0, 60, 20, st="slp"),
    "Recover": mv("Normal", 0, None, 20, st="recover"),
    "Calm Mind": mv("Psychic", 0, None, 20, up={"spa": 1, "spd": 1}),
    "Sludge Bomb": mv("Poison", 90, 100, 10, sec=(30, "psn")),
    "Sludge": mv("Poison", 65, 100, 20, sec=(30, "psn")),
    "Toxic": mv("Poison", 0, 85, 10, st="tox"),
    "Acid Armor": mv("Poison", 0, None, 40, up={"def": 2}),
    "Giga Drain": mv("Grass", 60, 100, 5, drain=1),
    "Mud-Slap": mv("Ground", 20, 100, 10, sec=(100, {"acc": -1})),
    "Rest": mv("Psychic", 0, None, 10, st="rest"),
    "Curse": mv("???", 0, None, 10, up={"atk": 1, "def": 1, "spe": -1}),
    "Pain Split": mv("Normal", 0, None, 20, st="painsplit"),
    "Haze": mv("Ice", 0, None, 30, st="haze"),
    "Rock Slide": mv("Rock", 75, 90, 10, sec=(30, "flinch")),
    "Ancient Power": mv("Rock", 60, 100, 5, sec=(10, "allup")),
    "Silver Wind": mv("Bug", 60, 100, 5, sec=(10, "allup")),
    "Rock Tomb": mv("Rock", 50, 80, 10, sec=(100, {"spe": -1})),
    "Iron Defense": mv("Steel", 0, None, 15, up={"def": 2}),
    "Withdraw": mv("Water", 0, None, 40, up={"def": 1}),
    "Protect": mv("Normal", 0, None, 10, st="protect", prio=3),
    "Leech Life": mv("Bug", 20, 100, 15, c=1, drain=1),
    "Poison Tail": mv("Poison", 50, 100, 25, c=1, highcrit=1, sec=(10, "psn")),
    "Pin Missile": mv("Bug", 14, 85, 20, multi=1),
    "Signal Beam": mv("Bug", 75, 100, 15, sec=(10, "confuse")),
    "Screech": mv("Normal", 0, 85, 40, down={"def": -2}),
    "Waterfall": mv("Water", 80, 100, 15, c=1),
    "Hydro Pump": mv("Water", 120, 80, 5),
    "Dragon Dance": mv("Dragon", 0, None, 20, up={"atk": 1, "spe": 1}),
    "Bubble Beam": mv("Water", 65, 100, 20, sec=(10, {"spe": -1})),
    "Dragon Breath": mv("Dragon", 60, 100, 20, sec=(30, "par")),
    "Twister": mv("Dragon", 40, 100, 20, sec=(20, "flinch")),
    "Thunderbolt": mv("Electric", 95, 100, 15, sec=(10, "par")),
    "Thunder Wave": mv("Electric", 0, 100, 20, st="par"),
    "Tail Glow": mv("Bug", 0, None, 20, up={"spa": 2}),
    "Shock Wave": mv("Electric", 60, None, 20),
    "Spark": mv("Electric", 65, 100, 20, c=1, sec=(30, "par")),
    "Double Team": mv("Normal", 0, None, 15, up={"eva": 1}),
    "Flash": mv("Normal", 0, 70, 20, down={"acc": -1}),
    "Mega Drain": mv("Grass", 40, 100, 15, drain=1),
    "Magical Leaf": mv("Grass", 60, None, 20),
    "Synthesis": mv("Grass", 0, None, 5, st="recover"),
    "Sleep Powder": mv("Grass", 0, 75, 15, st="slp"),
    "Struggle": mv("???", 50, None, 1, c=1, recoil=4),
}

# --- the animals ---------------------------------------------------------------------
# base stats: HP, Attack, Defense, Sp. Atk, Sp. Def, Speed

SPECIES = {
    "Critter": dict(types=("Normal",), base=(70, 75, 60, 45, 60, 95), ability="Guts",
                    pool=["Body Slam", "Return", "Quick Attack", "Double-Edge", "Bite", "Crunch", "Iron Tail",
                          "Swords Dance", "Agility"]),
    "Squid": dict(types=("Water", "Psychic"), base=(60, 50, 55, 90, 75, 85), ability="Levitate",
                  pool=["Surf", "Water Pulse", "Octazooka", "Psychic", "Psybeam", "Ice Beam", "Confuse Ray",
                        "Hypnosis", "Recover", "Calm Mind"]),
    "Slug": dict(types=("Poison",), base=(90, 60, 70, 60, 80, 20), ability="Liquid Ooze",
                 pool=["Sludge Bomb", "Sludge", "Toxic", "Acid Armor", "Giga Drain", "Mud-Slap", "Rest", "Curse",
                       "Pain Split", "Haze", "Body Slam"]),
    "Snail": dict(types=("Bug", "Rock"), base=(65, 60, 115, 40, 85, 15), ability="Shell Armor",
                  pool=["Rock Slide", "Ancient Power", "Silver Wind", "Rock Tomb", "Iron Defense", "Withdraw",
                        "Protect", "Toxic", "Rest", "Leech Life", "Curse"]),
    "Millipede": dict(types=("Bug", "Poison"), base=(55, 85, 70, 40, 55, 80), ability="Poison Point",
                      pool=["Poison Tail", "Pin Missile", "Signal Beam", "Sludge Bomb", "Toxic", "Swords Dance",
                            "Agility", "Screech", "Rock Tomb"]),
    "Koi": dict(types=("Water",), base=(70, 80, 60, 55, 65, 80), ability="Swift Swim",
                pool=["Waterfall", "Hydro Pump", "Surf", "Dragon Dance", "Return", "Bubble Beam", "Dragon Breath",
                      "Twister", "Ice Beam", "Body Slam"]),
    "Tree Squid": dict(types=("Water", "Grass"), base=(65, 55, 65, 80, 85, 60), ability="Suction Cups",
                       pool=["Giga Drain", "Mega Drain", "Magical Leaf", "Surf", "Water Pulse", "Bubble Beam",
                             "Octazooka", "Synthesis", "Sleep Powder"]),
}

STATS = ("atk", "def", "spa", "spd", "spe")
STAT_NAME = {"atk": "Attack", "def": "Defense", "spa": "Sp. Atk", "spd": "Sp. Def", "spe": "Speed",
             "acc": "accuracy", "eva": "evasiveness"}
STATUS_TAG = dict(par="PAR", psn="PSN", tox="TOX", slp="SLP", frz="FRZ", brn="BRN")
CRIT = (1 / 16, 1 / 8, 1 / 4, 1 / 3, 1 / 2)
# Gen 3 accuracy/evasion stages, -6..+6
ACC = ((33, 100), (36, 100), (43, 100), (50, 100), (60, 100), (75, 100), (1, 1),
       (133, 100), (166, 100), (2, 1), (233, 100), (133, 50), (3, 1))
LEVEL = 100


def staged(value, n):
    return value * (2 + n) // 2 if n >= 0 else value * 2 // (2 - n)


def moveset(species, rng):
    """Four random moves from the animal's pool: at least one attack of its own type,
    at least two attacks, at most two status moves."""
    sp = SPECIES[species]
    pool = sp["pool"][:]
    rng.shuffle(pool)
    stab = [m for m in pool if MOVES[m]["p"] and MOVES[m]["t"] in sp["types"]]
    pick = [stab[0]]
    for m in pool:
        if len(pick) == 4:
            break
        if m in pick:
            continue
        attacks = sum(1 for x in pick if MOVES[x]["p"])
        if not MOVES[m]["p"] and (len(pick) - attacks >= 2 or 4 - len(pick) <= 2 - attacks):
            continue
        pick.append(m)
    return pick


class Mon:
    def __init__(self, species, rng, foe=False):
        sp = SPECIES[species]
        self.species, self.types, self.ability = species, sp["types"], sp["ability"]
        self.name = ("Foe " if foe else "") + species
        hp, *rest = sp["base"]
        # Gen 3: ((2*Base + IV + EV/4) * Level / 100) + 5, HP + Level + 10; IV 31, EV 84
        self.maxhp = (2 * hp + 31 + 21) * LEVEL // 100 + LEVEL + 10
        self.stats = {k: (2 * b + 31 + 21) * LEVEL // 100 + 5 for k, b in zip(STATS, rest)}
        self.hp = self.maxhp
        self.moves = [[m, MOVES[m]["pp"]] for m in moveset(species, rng)]
        self.status, self.sleep, self.toxic, self.confused = None, 0, 0, 0
        self.boosts = dict.fromkeys(STATS + ("acc", "eva"), 0)
        self.flinch, self.protected, self.protect_run = False, False, 0
        self.item = "Leftovers"

    def speed(self):
        s = staged(self.stats["spe"], self.boosts["spe"])
        return s // 4 if self.status == "par" else s

    def usable(self):
        return [i for i, (_, pp) in enumerate(self.moves) if pp > 0]


class Battle:
    """The rules. `turn(i)` plays a whole turn with your move `i`; what happened is added to
    `events`: (text, (your hp, its hp), (your status, its status), who was hit, who acted) —
    sides are 0 (yours) and 1; "who acted" is -1 - side when that side faints."""

    def __init__(self, mine, theirs, rng=None):
        self.rng = rng or random.Random()
        self.mons = [Mon(mine, self.rng), Mon(theirs, self.rng, foe=True)]
        self.events = []
        self.winner = None
        self.number = 0
        self.say(f"A wild battle! {self.mons[0].name} vs. {self.mons[1].name}!")

    # --- reporting ---
    def say(self, text, hit=None, by=None):
        a, b = self.mons
        self.events.append((text, (a.hp, b.hp), (a.status, b.status), hit, by))

    def side(self, mon):
        return self.mons.index(mon)

    # --- a turn ---
    def turn(self, i):
        if self.winner is not None:
            return
        self.number += 1
        me, foe = self.mons
        picks = [self.move_of(me, i), self.move_of(foe, self.choose())]
        for m in self.mons:
            m.protected = False
        order = sorted(range(2), key=lambda s: (MOVES[picks[s]].get("prio", 0), self.mons[s].speed(),
                                                self.rng.random()), reverse=True)
        for n, s in enumerate(order):
            if self.winner is not None:
                break
            self.act(self.mons[s], self.mons[1 - s], picks[s], first=n == 0)
        if self.winner is None:
            self.end_of_turn(order)
        for m in self.mons:
            m.flinch = False

    def move_of(self, mon, i):
        if not mon.usable():
            return "Struggle"
        if i is None or mon.moves[i][1] <= 0:
            i = mon.usable()[0]
        mon.moves[i][1] -= 1
        return mon.moves[i][0]

    def can_move(self, u):
        rng = self.rng
        if u.status == "slp":
            u.sleep -= 1
            if u.sleep > 0:
                self.say(f"{u.name} is fast asleep.")
                return False
            u.status = None
            self.say(f"{u.name} woke up!")
        if u.status == "frz":
            if rng.random() < 0.2:
                u.status = None
                self.say(f"{u.name} thawed out!")
            else:
                self.say(f"{u.name} is frozen solid!")
                return False
        if u.flinch:
            self.say(f"{u.name} flinched!")
            return False
        if u.confused:
            u.confused -= 1
            if u.confused == 0:
                self.say(f"{u.name} snapped out of confusion!")
            else:
                self.say(f"{u.name} is confused!")
                if rng.random() < 0.5:
                    # 40 power, typeless, its own Attack against its own Defense, no crit or roll
                    a, d = staged(u.stats["atk"], u.boosts["atk"]), staged(u.stats["def"], u.boosts["def"])
                    dmg = min(u.hp, (a * 40 * (2 * LEVEL // 5 + 2) // d) // 50 + 2)
                    u.hp -= dmg
                    self.say("It hurt itself in its confusion!", hit=self.side(u))
                    self.check_faint(u)
                    return False
        if u.status == "par" and rng.random() < 0.25:
            self.say(f"{u.name} is paralyzed! It can't move!")
            return False
        return True

    def act(self, u, f, name, first):
        if u.hp <= 0 or not self.can_move(u):
            return
        m = MOVES[name]
        self.say(f"{u.name} used {name}!", by=self.side(u))
        if m.get("st") == "protect":
            # Gen 3: each Protect in a row is half as likely to work; it fails if it goes last
            if first and self.rng.random() < 1 / 2 ** u.protect_run:
                u.protected, u.protect_run = True, u.protect_run + 1
                self.say(f"{u.name} protected itself!")
            else:
                u.protect_run = 0
                self.say("But it failed!")
            return
        u.protect_run = 0
        at_foe = m["p"] > 0 or m.get("st") in ("par", "tox", "slp", "confuse") or "down" in m
        if at_foe and f.protected:
            self.say(f"{f.name} protected itself!")
            return
        if at_foe and m["a"] is not None:
            stage = max(-6, min(6, u.boosts["acc"] - f.boosts["eva"]))
            num, den = ACC[stage + 6]
            if self.rng.randint(1, 100) > m["a"] * num // den:
                self.say(f"{u.name}'s attack missed!")
                return
        if m["p"]:
            self.attack(u, f, name, m, first)
        else:
            self.status_move(u, f, name, m)

    def damage(self, u, f, m, crit=False, roll=None):
        t = m["t"]
        phys = t in PHYSICAL
        ak, dk = ("atk", "def") if phys else ("spa", "spd")
        ab, db = u.boosts[ak], f.boosts[dk]
        if crit:  # a critical hit ignores the attacker's drops and the defender's boosts
            ab, db = max(ab, 0), min(db, 0)
        a, d = staged(u.stats[ak], ab), staged(f.stats[dk], db)
        if phys and u.ability == "Guts" and u.status:
            a = a * 15 // 10
        dmg = (a * m["p"] * (2 * LEVEL // 5 + 2) // d) // 50
        if phys and u.status == "brn" and u.ability != "Guts":
            dmg //= 2
        dmg += 2
        if crit:
            dmg *= 2
        if t in u.types:
            dmg = dmg * 15 // 10
        for dt in f.types:
            e = CHART.get(t, {}).get(dt, 1)
            dmg = dmg * 2 if e == 2 else dmg // 2 if e == .5 else dmg * e
        dmg = dmg * (roll if roll is not None else self.rng.randint(85, 100)) // 100
        return max(1, int(dmg))

    def attack(self, u, f, name, m, first):
        rng = self.rng
        e = effectiveness(m["t"], f.types)
        if e == 0 or (m["t"] == "Ground" and f.ability == "Levitate"):
            self.say(f"It doesn't affect {f.name}...")
            return
        hits = 1
        if m.get("multi"):  # 2, 3, 4 or 5 hits: 3/8, 3/8, 1/8, 1/8
            hits = rng.choice((2, 2, 2, 3, 3, 3, 4, 5))
        total, n = 0, 0
        for _ in range(hits):
            if f.hp <= 0:
                break
            crit = False
            if f.ability != "Shell Armor":
                crit = rng.random() < CRIT[1 if m.get("highcrit") else 0]
            dmg = min(f.hp, self.damage(u, f, m, crit))
            f.hp -= dmg
            total += dmg
            n += 1
            self.say("A critical hit!" if crit else "", hit=self.side(f))
        if hits > 1:
            self.say(f"Hit {n} time{'s' if n > 1 else ''}!")
        if e > 1:
            self.say("It's super effective!")
        elif e < 1:
            self.say("It's not very effective...")
        if m.get("recoil"):
            r = max(1, total // m["recoil"])
            u.hp = max(0, u.hp - r)
            self.say(f"{u.name} is hit with recoil!", hit=self.side(u))
        if m.get("drain"):
            amt = max(1, total // 2)
            if f.ability == "Liquid Ooze":
                u.hp = max(0, u.hp - amt)
                self.say(f"{u.name} sucked up the liquid ooze!", hit=self.side(u))
            elif u.hp < u.maxhp:
                u.hp = min(u.maxhp, u.hp + amt)
                self.say(f"{f.name} had its energy drained!")
        if m.get("c") and f.hp > 0 and u.hp > 0 and rng.random() < 1 / 3:
            if f.ability == "Static":
                self.inflict(u, "par", f"{f.name}'s Static")
            elif f.ability == "Poison Point":
                self.inflict(u, "psn", f"{f.name}'s Poison Point")
        sec = m.get("sec")
        if sec and rng.random() * 100 < sec[0]:
            what = sec[1]
            if what == "allup":
                for k in STATS:
                    self.boost(u, k, 1)
            elif f.hp > 0:
                if what == "flinch":
                    f.flinch = first
                elif isinstance(what, dict):
                    for k, v in what.items():
                        self.boost(f, k, v)
                elif what == "confuse":
                    self.confuse(f, quiet=True)
                else:
                    self.inflict(f, what)
        self.check_faint(f)
        self.check_faint(u)

    def status_move(self, u, f, name, m):
        st = m.get("st")
        if "up" in m:
            if all(u.boosts[k] == (6 if v > 0 else -6) for k, v in m["up"].items()):
                self.say("But it failed!")
            for k, v in m["up"].items():
                self.boost(u, k, v)
        elif "down" in m:
            for k, v in m["down"].items():
                self.boost(f, k, v)
        elif st == "recover":
            if u.hp == u.maxhp:
                self.say(f"{u.name}'s HP is full!")
            else:
                u.hp = min(u.maxhp, u.hp + u.maxhp // 2)
                self.say(f"{u.name} regained health!")
        elif st == "rest":
            if u.hp == u.maxhp or u.status == "slp":
                self.say("But it failed!")
            else:
                u.status, u.sleep, u.toxic, u.hp = "slp", 3, 0, u.maxhp
                self.say(f"{u.name} slept and became healthy!")
        elif st == "painsplit":
            avg = (u.hp + f.hp) // 2
            u.hp, f.hp = min(u.maxhp, avg), min(f.maxhp, avg)
            self.say("The battlers shared their pain!")
        elif st == "haze":
            for mon in self.mons:
                mon.boosts = dict.fromkeys(mon.boosts, 0)
            self.say("All stat changes were eliminated!")
        elif st == "confuse":
            self.confuse(f)
        elif st == "par" and effectiveness(m["t"], f.types) == 0:
            self.say(f"It doesn't affect {f.name}...")
        elif st in ("par", "tox", "slp"):
            if not self.inflict(f, st):
                self.say("But it failed!")

    def confuse(self, f, quiet=False):
        """Confusion lasts 2-5 turns (it wears off as the turn starts)."""
        if f.confused:
            if not quiet:
                self.say(f"{f.name} is already confused!")
            return
        f.confused = self.rng.randint(2, 5)
        self.say(f"{f.name} became confused!")

    def inflict(self, f, st, cause=None):
        """Give `f` a status; False if it can't have it."""
        if f.status is not None or f.hp <= 0:
            return False
        if st in ("psn", "tox") and ("Poison" in f.types or "Steel" in f.types):
            return False
        if st == "frz" and "Ice" in f.types:
            return False
        f.status = st
        if st == "slp":
            f.sleep = self.rng.randint(2, 5)  # 1-4 turns asleep; it acts on the turn it wakes
        if st == "tox":
            f.toxic = 0
        text = dict(par="is paralyzed! It may be unable to move!", psn="was poisoned!", tox="was badly poisoned!",
                    slp="fell asleep!", frz="was frozen solid!")[st]
        self.say(f"{cause}! {f.name} {text}" if cause else f"{f.name} {text}")
        return True

    def boost(self, mon, k, v):
        old = mon.boosts[k]
        new = max(-6, min(6, old + v))
        nm = STAT_NAME[k]
        if new == old:
            self.say(f"{mon.name}'s {nm} won't go any {'higher' if v > 0 else 'lower'}!")
            return
        mon.boosts[k] = new
        word = ("rose!" if v == 1 else "sharply rose!") if v > 0 else ("fell!" if v == -1 else "harshly fell!")
        self.say(f"{mon.name}'s {nm} {word}")

    def check_faint(self, mon):
        if mon.hp <= 0 and self.winner is None:
            mon.hp = 0
            self.say(f"{mon.name} fainted!", by=-1 - self.side(mon))
            other = self.mons[1 - self.side(mon)]
            self.winner = self.side(other)
            if self.winner == 0:
                self.say(f"You win! {other.name} is the champion of the glade!")
            else:
                self.say(f"You lost... {other.name} wins!")

    def end_of_turn(self, order):
        for s in order:
            m = self.mons[s]
            if m.hp <= 0:
                continue
            if m.hp < m.maxhp:
                m.hp = min(m.maxhp, m.hp + max(1, m.maxhp // 16))
                self.say(f"{m.name} restored a little HP using its Leftovers!")
            if m.status == "psn":
                m.hp = max(0, m.hp - max(1, m.maxhp // 8))
                self.say(f"{m.name} is hurt by poison!", hit=s)
            elif m.status == "tox":
                m.toxic += 1
                m.hp = max(0, m.hp - max(1, m.maxhp * m.toxic // 16))
                self.say(f"{m.name} is hurt by poison!", hit=s)
            self.check_faint(m)
            if self.winner is not None:
                return

    # --- the opponent ---
    def choose(self):
        """The foe's move: a sure knock-out if it has one, otherwise mostly its hardest hit,
        with the odd sensible status move."""
        me, them = self.mons[1], self.mons[0]
        best, pick = -1.0, None
        for i in me.usable():
            name = me.moves[i][0]
            m = MOVES[name]
            acc = (m["a"] or 100) / 100
            if m["p"]:
                e = effectiveness(m["t"], them.types)
                if e == 0 or (m["t"] == "Ground" and them.ability == "Levitate"):
                    score = 0
                else:
                    dmg = self.damage(me, them, m, roll=92) * (3 if m.get("multi") else 1)
                    score = 1000 * acc if dmg >= them.hp else 100 * min(1.0, dmg / them.hp) * acc
            else:
                st = m.get("st")
                score = 0
                if "up" in m and all(me.boosts[k] < 2 for k, v in m["up"].items() if v > 0) and me.hp > me.maxhp * .6:
                    score = 45
                elif "down" in m:
                    score = 20
                elif st in ("par", "tox", "slp") and them.status is None:
                    score = 55 * acc
                elif st == "confuse" and not them.confused:
                    score = 35
                elif st == "recover" and me.hp < me.maxhp * .5:
                    score = 80
                elif st == "rest" and me.hp < me.maxhp * .35 and me.status != "slp":
                    score = 70
                elif st == "painsplit" and them.hp > me.hp * 1.5:
                    score = 60
                elif st == "haze" and (sum(them.boosts.values()) > 1 or sum(me.boosts.values()) < -1):
                    score = 60
                elif st == "protect":
                    score = 10
            score *= self.rng.uniform(0.75, 1.25)
            if score > best:
                best, pick = score, i
        return pick


# --- the animals in the scene --------------------------------------------------------

def species_of(obj):
    name = type(obj).__name__
    if name in ("Squid", "Nibbler", "HollowSquid"):
        return "Squid"
    if name == "Slug":
        return "Snail" if getattr(obj, "shell", None) else "Slug"
    if name == "Fish":
        return "Koi"
    if name in ("Millipede", "Critter"):
        return name
    if name == "TreeSquid":
        return "Tree Squid"
    return None


class Perched:
    """A tree squid (squids.py), standing in for an animal (same shape as apex.Prey)."""

    low = False

    def __init__(self, squid):
        self.obj = squid

    def pos(self):
        return self.obj.x, self.obj.y - 8 * self.obj.size


def animals(scene, lower):
    """Every animal you can pick (not the fireflies): (animal, species)."""
    prey, _ = find_prey(scene, lower)
    out = [(p, species_of(p.obj)) for p in prey if species_of(p.obj)]
    colony = getattr(scene, "colony", None)
    if colony is not None:
        out += [(Perched(sq), "Tree Squid") for sq in colony.squid.values() if sq.fade > 0.5]
    return out


# --- the battle box ------------------------------------------------------------------

EDGE = (24, 14, 34)
TEXT = (255, 238, 214)
DIM = (150, 136, 160)
CLOTH = (196, 140, 255)
MINE = (110, 255, 180)   # your animal: the paths' mint green
THEIRS = (255, 150, 214)  # its opponent: blossom pink
STEP = 0.95               # seconds each line of the log is shown before the next
WALK = 1.6                # seconds to walk onto the field (and home again)
# the field in the top screen's bottom-right corner: where each fighter stands (yours near,
# its opponent further back, as in the games) and the size of its mossy platform
SPOTS = ((690, 498), (862, 452))
PADS = ((112, 26), (86, 20))


class Fighter:
    """An animal on the field. It is hidden where it lives and drawn here instead: the
    patch of field it stands on is copied into a scratch picture at the animal's real
    place, the animal draws itself onto that as usual, and the result is copied back onto
    the field. So it keeps its own look and its own wriggling, just somewhere else."""

    R = 56  # how far round the animal to copy (a millipede is long)

    def __init__(self, animal, side, t, scene):
        self.a, self.side, self.t0, self.scene = animal, side, t, scene
        self.home = animal.pos()
        self.going_home, self.fainted, self.lunge = None, None, -9.0
        self.saved = None
        o = animal.obj
        if hasattr(o, "track"):
            # a crawler stands on level ground in the arena, even one that was climbing a
            # tree: it gets a short flat track right where it is until it goes home
            px, py = o.track.at(o.d)[:2]
            self.saved = (o.track, o.d, getattr(o, "trail", None))
            o.track, o.d = Track([(px - 60, py), (px + 60, py)]), 60.0
            if self.saved[2] is not None:
                o.trail = []
        self.hide(True)

    def hide(self, on):
        o = self.a.obj
        o.gone = on
        if not on and self.saved is not None:
            o.track, o.d, trail = self.saved
            if trail is not None:
                o.trail = []
            self.saved = None

    def where(self, t, here):
        """Where it is now, in shared coordinates: walking out in a little hop, standing
        on its platform, lunging when it attacks, or walking home. `here`: the place on
        screen; an animal from another place comes in over the edge (yours on the left,
        its foe on the right) and leaves that way."""
        sx, sy = SPOTS[self.side]
        hx, hy = self.home if here is self.scene else (-40 if self.side == 0 else 1000, sy)
        if self.going_home is not None:
            k = 1 - ease((t - self.going_home) / WALK)
        else:
            k = ease((t - self.t0) / WALK)
        x = hx + (sx - hx) * k
        y = hy + (sy - hy) * k - math.sin(k * math.pi) * 30
        f = (t - self.lunge) / 0.4
        if 0 <= f < 1:  # towards the other one and back
            d = math.sin(f * math.pi) * 16 * (1 if self.side == 0 else -1)
            x, y = x + d, y - d * 0.35
        return x, y

    def alpha(self, t):
        if self.fainted is None:
            return 255
        return round(255 * max(0.0, 1 - (t - self.fainted) / 0.9))

    def draw(self, s, ox, oy, t, scratch, here):
        al = self.alpha(t)
        if al <= 0:
            return
        x, y = self.where(t, here)
        x, y = x - ox, y - oy
        if self.fainted is not None:
            y += 6 * (1 - al / 255)  # it sinks as it fades
        px, py = self.a.pos()
        if self.a.low:
            px, py = px - OFFSET[0], py - OFFSET[1]
        dx, dy = round(x - px), round(y - py)
        R = self.R
        dest = pygame.Rect(round(px) - R + dx, round(py) - R + dy, 2 * R, 2 * R).clip(s.get_rect())
        src = dest.move(-dx, -dy).clip(scratch.get_rect())
        dest = src.move(dx, dy)
        if src.w <= 0 or src.h <= 0:
            return
        scratch.set_clip(src)
        scratch.blit(s, src.topleft, dest)
        o = self.a.obj
        if isinstance(self.a, Perched):
            o.shine(scratch, t, 12)
        else:
            for part in ("draw", "shine"):
                fn = getattr(o, part, None)
                if fn:
                    fn(scratch, t)
        scratch.set_clip(None)
        piece = scratch.subsurface(src)
        if al < 255:
            piece = piece.copy()
            piece.set_alpha(al)
        s.blit(piece, dest.topleft)


class Arena:
    """The whole egg: choosing two animals, then the battle box. It goes with him from place
    to place: he can pick an animal in one and its opponent in another, and the field
    and fighters are in whichever place he is looking at (`scene`/`lower`, kept up to date
    by the glade)."""

    W, H = 380, 206

    def __init__(self, scene, lower, font, t):
        self.scene, self.lower, self.font = scene, lower, font
        self.rect = pygame.Rect(10, 540 - 10 - self.H, self.W, self.H)
        self.phase = "pick"
        self.picked = []          # [(animal, species, the place it lives)]
        self.battle = None
        self.queue, self.log = [], []
        self.next_at = t
        self.hp = [0.0, 0.0]      # the bars, easing towards `target`
        self.target = [0, 0]
        self.status = [None, None]
        self.hits = []            # (side, time): a glow on the animal that was hurt
        self.buttons = []         # (rect, action)
        self.done = False
        self.t0 = t
        self.mouse = None  # the top view's pointer, set by the glade
        self.fighters = []
        self.leaving = None   # when they set off home
        self.scratch = art.solid()

    # --- clicks ---
    def click(self, glade, t):
        """True if the click was the battle's."""
        m = glade.top.mouse()
        if self.leaving is not None:
            return False
        if m and self.rect.collidepoint(m):
            for r, action in self.buttons:
                if r.collidepoint(m):
                    action(t)
            return True
        if self.phase != "pick":
            return False
        for view, low in ((glade.top, False), (glade.bottom, True)):
            if view is None:
                continue
            m = view.mouse()
            if not m:
                continue
            x, y = (m[0] + OFFSET[0], m[1] + OFFSET[1]) if low else m
            hit = self.animal_at(x, y)
            if hit is not None:
                self.picked.append((*hit, self.scene))
                if len(self.picked) == 2:
                    self.start(t)
                return True
        return False

    def animal_at(self, x, y):
        best, near = None, 24.0
        taken = [p[0] for p in self.picked]
        for a, sp in animals(self.scene, self.lower):
            if any(a.obj is b.obj for b in taken):
                continue
            if getattr(a.obj, "gone", False):
                continue
            ax, ay = a.pos()
            d = math.hypot(ax - x, ay - y)
            if d < near:
                best, near = (a, sp), d
        return best

    def start(self, t):
        self.battle = Battle(self.picked[0][1], self.picked[1][1])
        a, b = self.battle.mons
        self.hp, self.target = [float(a.hp), float(b.hp)], [a.hp, b.hp]
        self.phase = "fight"
        self.log, self.queue = [], []
        if not self.fighters:  # they walk out onto the field, then the battle begins
            self.fighters = [Fighter(animal, side, t, home) for side, (animal, _, home) in enumerate(self.picked)]
            self.next_at = t + WALK
        for f in self.fighters:
            f.fainted = None
        self.feed(t)

    def leave(self, t):
        """Everyone goes home; the field fades away."""
        if self.leaving is not None:
            return
        self.leaving = t
        for f in self.fighters:
            f.going_home = t

    def finish(self):
        """Every animal back where it lives, and seen again."""
        for f in self.fighters:
            f.hide(False)
        self.fighters = []

    def feed(self, t):
        self.queue.extend(self.battle.events)
        self.battle.events = []
        self.next_at = max(self.next_at, t)

    def use(self, i, t):
        if self.queue or self.battle.winner is not None:
            return
        self.battle.turn(i)
        self.feed(t)

    def run(self, t):
        if self.phase == "pick" or self.battle is None or self.battle.winner is not None:
            self.leave(t)
            return
        if self.queue:
            return
        self.battle.winner = 1
        self.battle.say("You got away safely!")
        self.feed(t)

    def again(self, t):
        self.start(t)

    # --- time passing ---
    def update(self, dt, t):
        while self.queue and t >= self.next_at:
            text, hp, st, hit, by = self.queue.pop(0)
            self.target, self.status = list(hp), list(st)
            if by is not None and self.fighters:
                if by >= 0:
                    self.fighters[by].lunge = t
                else:
                    self.fighters[-1 - by].fainted = t
            if text:
                self.log = (self.log + [text])[-3:]
            if hit is not None:
                self.hits.append((hit, t))
            self.next_at = t + (STEP if text else 0.45)
        for s in range(2):
            gap = self.target[s] - self.hp[s]
            self.hp[s] += gap * min(1.0, dt * 6) if abs(gap) > 0.5 else gap
        self.hits = [(s, h) for s, h in self.hits if t - h < 0.6]
        if self.leaving is not None and t - self.leaving > WALK:
            self.finish()
            self.done = True

    # --- drawing ---
    def text(self, s, words, x, y, color=TEXT, right=False):
        img = self.font.render(words, False, color)
        if right:
            x -= img.get_width()
        s.blit(img, (x, y))
        return img.get_width()

    def badge(self, s, kind, x, y):
        c = TYPE_COLOR.get(kind, (200, 200, 200))
        img = self.font.render(kind.upper(), False, EDGE)
        r = pygame.Rect(x, y, img.get_width() + 6, img.get_height() + 1)
        pygame.draw.rect(s, c, r, border_radius=3)
        s.blit(img, (x + 3, y))
        return r.w + 3

    def cloth(self, s, r, tint, hot=False, alpha=200):
        """A panel of the glade's glowing spirit-cloth, lit from above."""
        surf = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*mix(tint, EDGE, 0.72), alpha), surf.get_rect(), border_radius=4)
        light = pygame.Surface(r.size, pygame.SRCALPHA)  # drawn apart, then laid on top, so it blends
        for i in range(r.h - 4):
            a = round((80 if hot else 46) * (1 - i / r.h))
            pygame.draw.line(light, (*tint, a), (2, 2 + i), (r.w - 3, 2 + i))
        surf.blit(light, (0, 0))
        rim = (255, 255, 255) if hot else mix(tint, (255, 255, 255), 0.45)
        pygame.draw.rect(surf, (*rim, 230 if hot else 160), surf.get_rect(), 1, border_radius=4)
        s.blit(surf, r)

    def bar(self, s, x, y, w, hp, maxhp):
        f = max(0.0, min(1.0, hp / maxhp))
        c = (130, 255, 160) if f > 0.5 else (255, 220, 110) if f > 0.2 else (255, 110, 120)
        pygame.draw.rect(s, (20, 12, 30), (x, y, w, 5), border_radius=2)
        if f > 0:
            pygame.draw.rect(s, c, (x, y, max(1, round(w * f)), 5), border_radius=2)
            pygame.draw.line(s, mix(c, (255, 255, 255), 0.5), (x + 1, y + 1), (x + max(1, round(w * f)) - 2, y + 1))
        pygame.draw.rect(s, (*mix(c, EDGE, 0.3),), (x, y, w, 5), 1, border_radius=2)

    def panel(self, s, side, x, y, w, tint):
        mon = self.battle.mons[side]
        self.cloth(s, pygame.Rect(x, y, w, 30), tint, alpha=170)
        nx = x + 6 + self.text(s, mon.name, x + 6, y + 3, (255, 255, 255))
        nx += 6 + self.text(s, "Lv100", nx + 6, y + 3, DIM)
        for k in mon.types:
            nx += self.badge(s, k, nx + 6, y + 3)
        st = self.status[side]
        if st:
            nx += self.badge(s, STATUS_TAG[st], nx + 6, y + 3)
        self.bar(s, x + 6, y + 20, w - 12, self.hp[side], mon.maxhp)
        hp = max(0, round(self.hp[side]))
        label = f"{hp}/{mon.maxhp}" if side == 0 else f"{math.ceil(100 * hp / mon.maxhp)}%"
        self.text(s, label, x + w - 6, y + 3, TEXT, right=True)

    def draw(self, s, low, t):
        """`low`: drawing the lower screen (only animals on their way go there)."""
        if not low:
            self.field(s, t)
        ox, oy = OFFSET if low else (0, 0)
        for f in self.fighters:
            f.draw(s, ox, oy, t, self.scratch, self.scene)
            for side, h in self.hits:
                if side == f.side:
                    x, y = f.where(t, self.scene)
                    glow(s, x - ox, y - oy, 26, (255, 255, 255), q(140 * (1 - (t - h) / 0.6)))
        self.rings(s, low, t)
        if low or self.leaving is not None:
            return
        self.buttons = []
        k = min(1.0, (t - self.t0) / 0.3)
        r = self.rect
        if self.phase == "pick":
            h = 48
            box = pygame.Rect(r.x, r.bottom - h, r.w, h)
            self.cloth(s, box, CLOTH, alpha=round(240 * k))
            if not self.picked:
                line1, line2 = "BATTLE!", "Click an animal to be yours."
            else:
                line1, line2 = f"{self.picked[0][1]} is ready!", "Now click the animal it will fight."
            self.text(s, line1, box.x + 8, box.y + 7, MINE if self.picked else (255, 255, 255))
            self.text(s, line2, box.x + 8, box.y + 25)
            self.button(s, pygame.Rect(box.right - 66, box.y + 8, 58, 18), "Cancel", self.run, t)
            return
        self.cloth(s, r, CLOTH, alpha=245)
        self.panel(s, 1, r.x + 6, r.y + 6, r.w - 12, THEIRS)
        self.panel(s, 0, r.x + 6, r.y + 40, r.w - 12, MINE)
        # the log: newest line brightest
        for i, line in enumerate(self.log):
            c = mix(DIM, TEXT, (i + 1) / len(self.log))
            self.text(s, self.fit(line, r.w - 20), r.x + 10, r.y + 76 + i * 13, c)
        busy = bool(self.queue)
        y0 = r.y + 118
        if self.battle.winner is None:
            me = self.battle.mons[0]
            bw = (r.w - 18) // 2
            for i, (name, pp) in enumerate(me.moves):
                m = MOVES[name]
                br = pygame.Rect(r.x + 6 + (i % 2) * (bw + 6), y0 + (i // 2) * 34, bw, 30)
                ok = not busy and pp > 0
                self.move_button(s, br, name, m, pp, ok, t, i)
            self.button(s, pygame.Rect(r.right - 50, r.bottom - 17, 44, 13), "Run", self.run, t, small=True,
                        enabled=not busy)
            if busy:
                self.text(s, "...", r.x + 8, r.bottom - 16, DIM)
            else:
                self.text(s, f"Turn {self.battle.number + 1}: choose a move", r.x + 8, r.bottom - 16, DIM)
        elif not busy:
            self.button(s, pygame.Rect(r.x + 6, y0 + 10, (r.w - 18) // 2, 28), "Battle again", self.again, t)
            self.button(s, pygame.Rect(r.x + 12 + (r.w - 18) // 2, y0 + 10, (r.w - 18) // 2, 28), "Close",
                        self.close, t)

    def close(self, t):
        self.leave(t)

    def fit(self, line, w):
        while self.font.size(line)[0] > w and len(line) > 4:
            line = line[:-2] + "…"
        return line

    def hot(self, r):
        m = self.mouse() if self.mouse else None
        return bool(m) and r.collidepoint(m)

    def button(self, s, r, label, action, t, small=False, enabled=True):
        hot = enabled and self.hot(r)
        self.cloth(s, r, MINE if hot else mix(CLOTH, EDGE, 0.2), hot=hot, alpha=210)
        img = self.font.render(label, False, (255, 255, 255) if hot else TEXT if enabled else DIM)
        s.blit(img, img.get_rect(center=r.center))
        if enabled:
            self.buttons.append((r, action))

    def move_button(self, s, r, name, m, pp, ok, t, i):
        tint = TYPE_COLOR.get(m["t"], CLOTH)
        hot = ok and self.hot(r)
        self.cloth(s, r, tint if ok else mix(tint, EDGE, 0.5), hot=hot, alpha=215 if ok else 150)
        self.text(s, name, r.x + 6, r.y + 3, (255, 255, 255) if hot else TEXT if ok else DIM)
        info = f"{m['t'].upper()}  " + (f"{m['p']}" if m["p"] else "status")
        self.text(s, info, r.x + 6, r.y + 16, mix(tint, (255, 255, 255), 0.4) if ok else DIM)
        self.text(s, f"{pp}/{m['pp']}", r.right - 6, r.y + 16, TEXT if ok else DIM, right=True)
        if ok:
            self.buttons.append((r, lambda t, i=i: self.use(i, t)))

    def rings(self, s, low, t):
        """A soft glowing ring around each chosen animal (mint: yours, pink: its foe), and a
        flash on whichever one is hurt."""
        if self.fighters:
            return
        ox, oy = OFFSET if low else (0, 0)
        for n, (a, _, home) in enumerate(self.picked):
            if home is not self.scene:
                continue
            x, y = a.pos()
            if (y >= OFFSET[1]) != low:
                continue
            x, y = x - ox, y - oy
            c = MINE if n == 0 else THEIRS
            k = 0.6 + 0.4 * math.sin(t * 3 + n)
            glow(s, x, y, 18, c, round(40 * k))
            pygame.draw.ellipse(s, mix(c, (255, 255, 255), 0.3 * k), (round(x) - 13, round(y) - 9, 26, 18), 1)

    def field(self, s, t):
        """Two mossy platforms, glowing in each side's colour, growing out of the grass when
        the battle is called and sinking back when it is over."""
        k = ease((t - self.t0) / 0.8)
        if self.leaving is not None:
            k *= 1 - ease((t - self.leaving) / WALK)
        if k <= 0.02:
            return
        moss = (90, 200, 150)
        for side in (1, 0):
            (x, y), (w, h) = SPOTS[side], PADS[side]
            c = MINE if side == 0 else THEIRS
            y += 6
            w, h = round(w * k), max(2, round(h * k))
            glow(s, x, y, w * 0.6, c, q(50 * k))
            base = pygame.Rect(0, 0, w, h)
            base.center = (x, y)
            pygame.draw.ellipse(s, mix(c, EDGE, 0.82), base.move(0, 3))
            pygame.draw.ellipse(s, mix(moss, EDGE, 0.6), base)
            pygame.draw.ellipse(s, mix(moss, EDGE, 0.42), base.inflate(-w // 4, -h // 3))
            pygame.draw.ellipse(s, mix(c, (255, 255, 255), 0.25), base, 1)
            for i in range(16):  # spores round the rim, blinking slowly
                a = i / 16 * math.tau + t * 0.15
                b = 0.5 + 0.5 * math.sin(t * 2.2 + i * 1.7)
                if b > 0.45:
                    s.set_at((round(x + math.cos(a) * w / 2), round(y + math.sin(a) * h / 2)),
                             mix(c, (255, 255, 255), b * 0.6))
