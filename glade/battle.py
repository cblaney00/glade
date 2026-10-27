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

Every animal here is the first of three evolutions (the later ones don't exist yet), so
its base stats total 300-320, like Bulbasaur or Treecko; a fully evolved one would total
500-600, about 530 on average.
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
    "Ember": mv("Fire", 40, 100, 25, sec=(10, "brn")),
    "Flamethrower": mv("Fire", 95, 100, 15, sec=(10, "brn")),
    "Will-O-Wisp": mv("Fire", 0, 75, 15, st="brn"),
    "Stun Spore": mv("Grass", 0, 75, 30, st="par"),
    "Poison Powder": mv("Poison", 0, 75, 35, st="psn"),
    "Morning Sun": mv("Normal", 0, None, 5, st="recover"),
    "Gust": mv("Flying", 40, 100, 35),
    "Peck": mv("Flying", 35, 100, 35, c=1),
    "Wing Attack": mv("Flying", 60, 100, 35, c=1),
    "Aerial Ace": mv("Flying", 60, None, 20, c=1),
    "Air Cutter": mv("Flying", 55, 95, 25, highcrit=1),
    "Faint Attack": mv("Dark", 60, None, 20, c=1),
    "Supersonic": mv("Normal", 0, 55, 20, st="confuse"),
    "Dragon Claw": mv("Dragon", 80, 100, 15, c=1),
    "Shadow Ball": mv("Ghost", 80, 100, 15, sec=(20, {"spd": -1})),
    "Night Shade": mv("Ghost", 1, 100, 15, fixed=1),
    "Lick": mv("Ghost", 20, 100, 30, c=1, sec=(30, "par")),
    "Astonish": mv("Ghost", 30, 100, 15, c=1, sec=(30, "flinch")),
    "Karate Chop": mv("Fighting", 50, 100, 25, c=1, highcrit=1),
    "Brick Break": mv("Fighting", 75, 100, 15, c=1),
    "Mach Punch": mv("Fighting", 40, 100, 30, c=1, prio=1),
    "Bulk Up": mv("Fighting", 0, None, 20, up={"atk": 1, "def": 1}),
    "Take Down": mv("Normal", 90, 85, 20, c=1, recoil=4),
    "Mud Shot": mv("Ground", 55, 95, 15, sec=(100, {"spe": -1})),
    "Earthquake": mv("Ground", 100, 100, 10),
    "Fury Swipes": mv("Normal", 18, 80, 15, c=1, multi=1),
    "Sand-Attack": mv("Ground", 0, 100, 15, down={"acc": -1}),
    "Absorb": mv("Grass", 20, 100, 20, drain=1),
    "Leech Seed": mv("Grass", 0, 90, 10, st="seed"),
    "Aurora Beam": mv("Ice", 65, 100, 20, sec=(10, {"atk": -1})),
    "Powder Snow": mv("Ice", 40, 100, 25, sec=(10, "frz")),
    "Water Gun": mv("Water", 40, 100, 25),
    "Amnesia": mv("Psychic", 0, None, 20, up={"spd": 2}),
    "Metal Claw": mv("Steel", 50, 95, 35, c=1, sec=(10, ("self", {"atk": 1}))),
    "Harden": mv("Normal", 0, None, 30, up={"def": 1}),
    "Confusion": mv("Psychic", 50, 100, 25, sec=(10, "confuse")),
    "Slash": mv("Normal", 70, 100, 20, c=1, highcrit=1),
    "Hyper Fang": mv("Normal", 80, 90, 15, c=1, sec=(10, "flinch")),
    "Cross Chop": mv("Fighting", 100, 80, 5, c=1, highcrit=1),
    "Spore": mv("Grass", 0, 100, 15, st="slp"),
    "Heat Wave": mv("Fire", 100, 90, 10, sec=(10, "brn")),
    "Icy Wind": mv("Ice", 55, 95, 15, sec=(100, {"spe": -1})),
    "Fire Punch": mv("Fire", 75, 100, 15, c=1, sec=(10, "brn")),
    "Headbutt": mv("Normal", 70, 100, 15, c=1, sec=(30, "flinch")),
    "Blaze Kick": mv("Fire", 85, 90, 10, c=1, highcrit=1, sec=(10, "brn")),
    "Meteor Mash": mv("Steel", 100, 85, 10, c=1, sec=(20, ("self", {"atk": 1}))),
    "Struggle": mv("???", 50, None, 1, c=1, recoil=4),
}

# --- the animals ---------------------------------------------------------------------
# base stats: HP, Attack, Defense, Sp. Atk, Sp. Def, Speed — first stages, totals 300-320
# num: its Forest Dex number (dex.py). Each line of three evolutions takes three numbers in a
# row; the three starters' lines come first (#001-#009); room for 260.

SPECIES = {
    "Duskling": dict(num=10, types=("Normal",), base=(54, 58, 47, 35, 47, 74), ability="Guts",
                    pool=["Body Slam", "Return", "Quick Attack", "Double-Edge", "Bite", "Crunch", "Iron Tail",
                          "Swords Dance", "Agility"]),
    "Driftlet": dict(num=13, types=("Water", "Psychic"), base=(46, 39, 42, 69, 58, 66), ability="Levitate",
                  pool=["Surf", "Water Pulse", "Octazooka", "Psychic", "Psybeam", "Ice Beam", "Confuse Ray",
                        "Hypnosis", "Recover", "Calm Mind"]),
    "Gloamooze": dict(num=16, types=("Poison",), base=(73, 48, 56, 48, 64, 16), ability="Liquid Ooze",
                 pool=["Sludge Bomb", "Sludge", "Toxic", "Acid Armor", "Giga Drain", "Mud-Slap", "Rest", "Curse",
                       "Pain Split", "Haze", "Body Slam"]),
    "Cairncurl": dict(num=19, types=("Bug", "Rock"), base=(51, 47, 91, 32, 67, 12), ability="Shell Armor",
                  pool=["Rock Slide", "Ancient Power", "Silver Wind", "Rock Tomb", "Iron Defense", "Withdraw",
                        "Protect", "Toxic", "Rest", "Leech Life", "Curse"]),
    "Luminpede": dict(num=22, types=("Bug", "Poison"), base=(43, 66, 55, 31, 43, 62), ability="Poison Point",
                      pool=["Poison Tail", "Pin Missile", "Signal Beam", "Sludge Bomb", "Toxic", "Swords Dance",
                            "Agility", "Screech", "Rock Tomb"]),
    "Lilyfin": dict(num=25, types=("Water",), base=(53, 60, 45, 42, 49, 61), ability="Swift Swim",
                pool=["Waterfall", "Hydro Pump", "Surf", "Dragon Dance", "Return", "Bubble Beam", "Dragon Breath",
                      "Twister", "Ice Beam", "Body Slam"]),
    "Canopod": dict(num=28, types=("Water", "Grass"), base=(50, 42, 50, 62, 65, 46), ability="Suction Cups",
                       pool=["Giga Drain", "Mega Drain", "Magical Leaf", "Surf", "Water Pulse", "Bubble Beam",
                             "Octazooka", "Synthesis", "Sleep Powder"]),
    "Lanternwing": dict(num=31, types=("Bug", "Fire"), base=(45, 35, 40, 75, 55, 70), ability="Shield Dust",
                         pool=["Ember", "Flamethrower", "Silver Wind", "Signal Beam", "Will-O-Wisp", "Stun Spore",
                               "Morning Sun", "Gust"]),
    "Gloomflit": dict(num=34, types=("Dark", "Flying"), base=(50, 55, 40, 45, 45, 75), ability="Inner Focus",
                     pool=["Bite", "Crunch", "Wing Attack", "Aerial Ace", "Faint Attack", "Confuse Ray", "Supersonic",
                           "Leech Life", "Screech"]),
    "Glimmerfly": dict(num=37, types=("Dragon", "Flying"), base=(46, 62, 43, 50, 44, 75), ability="Levitate",
                          pool=["Dragon Breath", "Twister", "Dragon Claw", "Dragon Dance", "Wing Attack", "Aerial Ace",
                                "Quick Attack", "Silver Wind", "Double Team"]),
    "Mistwisp": dict(num=40, types=("Ghost",), base=(40, 35, 45, 70, 60, 60), ability="Levitate",
                      pool=["Shadow Ball", "Night Shade", "Lick", "Astonish", "Confuse Ray", "Will-O-Wisp",
                            "Hypnosis", "Psybeam", "Pain Split"]),
    "Brawlhop": dict(num=43, types=("Fighting",), base=(60, 70, 55, 30, 45, 50), ability="Thick Fat",
                       pool=["Karate Chop", "Brick Break", "Mach Punch", "Bulk Up", "Mud-Slap", "Body Slam",
                             "Rock Tomb", "Bubble Beam"]),
    "Mossdelve": dict(num=46, types=("Ground",), base=(55, 65, 60, 30, 40, 60), ability="Rock Head",
                      pool=["Mud Shot", "Earthquake", "Mud-Slap", "Take Down", "Fury Swipes", "Sand-Attack",
                            "Rock Slide", "Rock Tomb"]),
    "Sporeling": dict(num=49, types=("Grass", "Poison"), base=(60, 45, 55, 65, 60, 25), ability="Effect Spore",
                      pool=["Absorb", "Mega Drain", "Giga Drain", "Sludge Bomb", "Stun Spore", "Sleep Powder",
                            "Poison Powder", "Leech Seed", "Synthesis"]),
    "Rimeslink": dict(num=52, types=("Water", "Ice"), base=(50, 45, 50, 65, 50, 60), ability="Water Absorb",
                      pool=["Powder Snow", "Aurora Beam", "Ice Beam", "Water Gun", "Bubble Beam", "Surf", "Haze",
                            "Amnesia", "Quick Attack"]),
    "Coppernib": dict(num=55, types=("Steel", "Electric"), base=(50, 60, 70, 45, 45, 40), ability="Static",
                          pool=["Metal Claw", "Iron Tail", "Iron Defense", "Harden", "Spark", "Shock Wave",
                                "Thunder Wave", "Thunderbolt"]),
    "Moonhoot": dict(num=58, types=("Normal", "Flying"), base=(55, 45, 45, 55, 55, 55), ability="Keen Eye",
                       pool=["Peck", "Wing Attack", "Aerial Ace", "Air Cutter", "Hypnosis", "Confusion", "Return",
                             "Quick Attack"]),
    # the far places (2026-10-27): the Snowy Ridge (left of the Forest) ...
    "Frostpaw": dict(num=61, types=("Ice",), base=(45, 50, 40, 65, 50, 70), ability="Run Away",
                      pool=["Powder Snow", "Icy Wind", "Ice Beam", "Aurora Beam", "Quick Attack", "Bite", "Agility",
                            "Double Team", "Haze"]),
    "Fluffhorn": dict(num=64, types=("Rock", "Normal"), base=(60, 65, 70, 30, 45, 40), ability="Rock Head",
                      pool=["Headbutt", "Rock Slide", "Rock Tomb", "Take Down", "Double-Edge", "Iron Defense",
                            "Body Slam", "Icy Wind", "Rest"]),
    "Shimmerchirp": dict(num=67, types=("Ice", "Flying"), base=(40, 45, 40, 65, 55, 70), ability="Keen Eye",
                         pool=["Peck", "Aerial Ace", "Air Cutter", "Icy Wind", "Aurora Beam", "Powder Snow", "Agility",
                               "Haze", "Gust"]),
    # ... and the Hot Springs (right of the River)
    "Steambara": dict(num=70, types=("Water", "Fire"), base=(75, 45, 55, 55, 55, 30), ability="Oblivious",
                      pool=["Water Gun", "Surf", "Ember", "Flamethrower", "Rest", "Amnesia", "Body Slam", "Calm Mind",
                            "Haze"]),
    "Embercling": dict(num=73, types=("Fire", "Ground"), base=(45, 65, 45, 55, 40, 70), ability="Flash Fire",
                        pool=["Ember", "Fire Punch", "Flamethrower", "Mud Shot", "Mud-Slap", "Quick Attack", "Agility",
                              "Will-O-Wisp", "Rock Tomb"]),
    "Vaporwobble": dict(num=76, types=("Water", "Electric"), base=(50, 30, 40, 70, 65, 55), ability="Static",
                        pool=["Water Pulse", "Bubble Beam", "Spark", "Shock Wave", "Thunderbolt", "Thunder Wave",
                              "Confuse Ray", "Haze", "Recover"]),
    # the third wave (2026-10-27, his ask: 6 more, two each in the Forest, the Waterfall and
    # the River; one-word names with no real animal in them)
    "Bramblit": dict(num=79, types=("Grass", "Dark"), base=(50, 62, 55, 40, 45, 58), ability="Poison Point",
                     pool=["Absorb", "Mega Drain", "Leech Seed", "Bite", "Faint Attack", "Crunch", "Pin Missile",
                           "Swords Dance", "Fury Swipes"]),
    "Thistlume": dict(num=82, types=("Psychic", "Flying"), base=(45, 35, 40, 72, 63, 60), ability="Keen Eye",
                      pool=["Gust", "Confusion", "Psybeam", "Psychic", "Hypnosis", "Calm Mind", "Air Cutter",
                            "Magical Leaf", "Aerial Ace"]),
    "Runelet": dict(num=85, types=("Rock", "Ghost"), base=(50, 55, 72, 50, 55, 28), ability="Sturdy",
                    pool=["Rock Tomb", "Rock Slide", "Ancient Power", "Astonish", "Night Shade", "Shadow Ball",
                          "Curse", "Harden", "Confuse Ray"]),
    "Sparkfly": dict(num=88, types=("Electric", "Bug"), base=(40, 45, 38, 68, 45, 79), ability="Static",
                     pool=["Spark", "Shock Wave", "Thunderbolt", "Thunder Wave", "Signal Beam", "Silver Wind",
                           "Leech Life", "Tail Glow", "Double Team"]),
    "Murkling": dict(num=91, types=("Water", "Poison"), base=(65, 55, 50, 55, 58, 27), ability="Liquid Ooze",
                     pool=["Water Gun", "Water Pulse", "Sludge", "Sludge Bomb", "Acid Armor", "Toxic", "Haze",
                           "Octazooka", "Pain Split"]),
    "Glintshell": dict(num=94, types=("Steel",), base=(52, 66, 80, 30, 50, 35), ability="Shell Armor",
                       pool=["Metal Claw", "Iron Defense", "Iron Tail", "Withdraw", "Harden", "Rock Tomb", "Protect",
                             "Slash", "Mud Shot"]),
    # the three starters (2026-10-27): you choose one before your first battle (starter.py).
    # Each line's final form is designed already, so its theme leads somewhere: Mossprance ->
    # Lichenmane -> Eldermane (Grass/Ghost, an ancient spirit stag, antlers a moss-hung tree of
    # spirit lanterns); Kindlet -> Smoldershell -> Pyreclad (Fire/Steel, an armoured molten
    # knight of a pangolin that rolls as a blazing wheel); Pippalotl -> Frillotl -> Leviolotl
    # (Water/Dragon, a great river dragon of an axolotl, gills worn as a crown).
    "Mossprance": dict(num=1, types=("Grass",), base=(45, 55, 45, 60, 60, 52), ability="Overgrow",
                     pool=["Absorb", "Magical Leaf", "Giga Drain", "Leech Seed", "Synthesis", "Take Down",
                           "Quick Attack", "Astonish", "Confuse Ray"]),
    "Kindlet": dict(num=4, types=("Fire",), base=(46, 58, 62, 48, 50, 46), ability="Blaze",
                    pool=["Ember", "Fire Punch", "Flamethrower", "Metal Claw", "Iron Defense", "Rock Tomb",
                          "Quick Attack", "Iron Tail"]),
    "Pippalotl": dict(num=7, types=("Water",), base=(52, 48, 50, 60, 58, 46), ability="Torrent",
                      pool=["Water Gun", "Bubble Beam", "Water Pulse", "Surf", "Dragon Breath", "Twister", "Amnesia",
                            "Haze", "Rest"]),
    # the starters' later stages (2026-10-27): middle ~405, final 530, like Hoenn's starters
    "Lichenmane": dict(num=2, types=("Grass",), base=(60, 68, 58, 80, 76, 63), ability="Overgrow",
                       pool=["Magical Leaf", "Giga Drain", "Leech Seed", "Synthesis", "Calm Mind", "Take Down",
                             "Quick Attack", "Astonish", "Confuse Ray"]),
    "Eldermane": dict(num=3, types=("Grass", "Ghost"), base=(80, 85, 75, 110, 100, 80), ability="Overgrow",
                      pool=["Giga Drain", "Magical Leaf", "Shadow Ball", "Leech Seed", "Calm Mind", "Synthesis",
                            "Will-O-Wisp", "Confuse Ray", "Psychic", "Pain Split"]),
    "Smoldershell": dict(num=5, types=("Fire",), base=(62, 78, 82, 62, 64, 57), ability="Blaze",
                         pool=["Ember", "Fire Punch", "Blaze Kick", "Flamethrower", "Metal Claw", "Iron Defense",
                               "Rock Tomb", "Iron Tail"]),
    "Pyreclad": dict(num=6, types=("Fire", "Steel"), base=(85, 110, 105, 80, 80, 70), ability="Blaze",
                     pool=["Blaze Kick", "Fire Punch", "Flamethrower", "Meteor Mash", "Iron Tail", "Rock Slide",
                           "Earthquake", "Swords Dance", "Iron Defense", "Bulk Up"]),
    "Frillotl": dict(num=8, types=("Water",), base=(68, 60, 66, 78, 74, 59), ability="Torrent",
                     pool=["Water Pulse", "Bubble Beam", "Surf", "Dragon Breath", "Twister", "Ice Beam", "Amnesia",
                           "Haze", "Rest"]),
    "Leviolotl": dict(num=9, types=("Water", "Dragon"), base=(95, 80, 85, 105, 95, 70), ability="Torrent",
                      pool=["Surf", "Hydro Pump", "Dragon Claw", "Dragon Breath", "Ice Beam", "Dragon Dance",
                            "Waterfall", "Earthquake", "Calm Mind", "Rest"]),
    # middle evolutions (evolve.py): base totals about 410 (Ivysaur 405), same shape, a few
    # stronger moves; numbered right after their first stage
    "Glowtail": dict(num=11, types=("Normal",), base=(70, 75, 61, 46, 61, 96), ability="Guts",
                     pool=["Body Slam", "Return", "Quick Attack", "Double-Edge", "Bite", "Crunch", "Iron Tail",
                           "Swords Dance", "Agility", "Slash", "Hyper Fang"]),
    "Nimbusdrift": dict(num=14, types=("Water", "Psychic"), base=(59, 50, 54, 88, 74, 84), ability="Levitate",
                       pool=["Surf", "Water Pulse", "Octazooka", "Psychic", "Psybeam", "Ice Beam", "Confuse Ray",
                             "Hypnosis", "Recover", "Calm Mind", "Hydro Pump"]),
    "Beaconwing": dict(num=32, types=("Bug", "Fire"), base=(58, 45, 51, 96, 70, 90), ability="Shield Dust",
                        pool=["Ember", "Flamethrower", "Silver Wind", "Signal Beam", "Will-O-Wisp", "Stun Spore",
                              "Morning Sun", "Gust", "Heat Wave"]),
    "Thudhop": dict(num=44, types=("Fighting",), base=(79, 92, 73, 40, 59, 66), ability="Thick Fat",
                         pool=["Karate Chop", "Brick Break", "Mach Punch", "Bulk Up", "Mud-Slap", "Body Slam",
                               "Rock Tomb", "Bubble Beam", "Cross Chop"]),
    "Sporestride": dict(num=50, types=("Grass", "Poison"), base=(79, 59, 73, 86, 79, 33), ability="Effect Spore",
                        pool=["Absorb", "Mega Drain", "Giga Drain", "Sludge Bomb", "Stun Spore", "Sleep Powder",
                              "Poison Powder", "Leech Seed", "Synthesis", "Spore"]),
}

def _grown(first, num, types, base, ability, more):
    """A later stage: its first stage's moves plus `more`, stronger ones."""
    pool = list(dict.fromkeys(SPECIES[first]["pool"] + more))
    return dict(num=num, types=types, base=base, ability=ability, pool=pool)


# Page one of the Forest Dex filled in (2026-10-27, his ask; his approved names): every line
# from #010 to #048 now has all three stages. Middle stages ~410, finals 530.
_LATER = [  # in order, so each takes on the one before it
    ("Cometail", "Glowtail", 12, ("Normal",), (85, 100, 75, 60, 75, 135), "Guts",
                       ["Double-Edge", "Slash", "Swords Dance", "Iron Tail", "Shadow Ball"]),
    ("Skyveil", "Nimbusdrift", 15, ("Water", "Psychic"), (85, 60, 70, 120, 100, 95), "Levitate",
                      ["Hydro Pump", "Psychic", "Ice Beam", "Calm Mind", "Thunderbolt"]),
    ("Gloomdrape", "Gloamooze", 17, ("Poison",), (90, 62, 72, 62, 82, 42), "Liquid Ooze",
                         ["Sludge Bomb", "Giga Drain", "Pain Split"]),
    ("Nightmire", "Gloomdrape", 18, ("Poison", "Ghost"), (115, 80, 95, 85, 110, 45), "Liquid Ooze",
                        ["Shadow Ball", "Will-O-Wisp", "Confuse Ray", "Curse"]),
    ("Cairnspire", "Cairncurl", 20, ("Bug", "Rock"), (68, 64, 116, 44, 90, 28), "Shell Armor",
                         ["Rock Slide", "Ancient Power", "Iron Defense"]),
    ("Cairnhold", "Cairnspire", 21, ("Rock", "Bug"), (90, 85, 145, 55, 115, 40), "Shell Armor",
                        ["Earthquake", "Signal Beam", "Rest"]),
    ("Luminthread", "Luminpede", 23, ("Bug", "Poison"), (58, 86, 70, 42, 58, 96), "Poison Point",
                          ["Poison Tail", "Signal Beam", "Agility"]),
    ("Glowcoil", "Luminthread", 24, ("Bug", "Poison"), (75, 110, 90, 55, 75, 125), "Poison Point",
                       ["Sludge Bomb", "Swords Dance", "Earthquake"]),
    ("Lilyveil", "Lilyfin", 26, ("Water",), (70, 76, 60, 56, 66, 82), "Swift Swim",
                       ["Waterfall", "Surf", "Agility"]),
    ("Lotuscrest", "Lilyveil", 27, ("Water", "Grass"), (90, 95, 80, 80, 90, 95), "Swift Swim",
                         ["Giga Drain", "Magical Leaf", "Dragon Dance", "Synthesis", "Hydro Pump"]),
    ("Boughgrip", "Canopod", 29, ("Water", "Grass"), (66, 58, 70, 80, 82, 54), "Suction Cups",
                        ["Giga Drain", "Surf", "Leech Seed"]),
    ("Canopolis", "Boughgrip", 30, ("Grass", "Water"), (95, 70, 95, 105, 110, 55), "Suction Cups",
                        ["Synthesis", "Calm Mind", "Hydro Pump", "Sleep Powder", "Protect"]),
    ("Hearthwing", "Beaconwing", 33, ("Bug", "Fire"), (75, 55, 65, 125, 95, 115), "Shield Dust",
                         ["Flamethrower", "Heat Wave", "Tail Glow", "Morning Sun", "Will-O-Wisp"]),
    ("Gloomglide", "Gloomflit", 35, ("Dark", "Flying"), (66, 72, 54, 58, 60, 100), "Inner Focus",
                         ["Crunch", "Aerial Ace", "Agility"]),
    ("Nightshroud", "Gloomglide", 36, ("Dark", "Flying"), (85, 95, 70, 75, 80, 125), "Inner Focus",
                          ["Shadow Ball", "Confuse Ray", "Double Team"]),
    ("Glimmerwyrm", "Glimmerfly", 38, ("Dragon", "Flying"), (62, 82, 58, 66, 58, 84), "Levitate",
                          ["Dragon Claw", "Dragon Breath", "Agility"]),
    ("Prismwyrm", "Glimmerwyrm", 39, ("Dragon", "Flying"), (80, 110, 75, 85, 75, 105), "Levitate",
                        ["Dragon Dance", "Earthquake", "Ancient Power"]),
    ("Mistshade", "Mistwisp", 41, ("Ghost",), (55, 48, 60, 92, 80, 75), "Levitate",
                        ["Shadow Ball", "Will-O-Wisp", "Calm Mind"]),
    ("Mistwraith", "Mistshade", 42, ("Ghost",), (70, 60, 75, 125, 105, 95), "Levitate",
                         ["Psychic", "Pain Split", "Hypnosis"]),
    ("Titanhop", "Thudhop", 45, ("Fighting", "Rock"), (105, 130, 100, 50, 80, 65), "Thick Fat",
                       ["Cross Chop", "Rock Slide", "Earthquake", "Fire Punch"]),
    ("Mossburrow", "Mossdelve", 47, ("Ground", "Grass"), (72, 88, 80, 40, 54, 76), "Rock Head",
                         ["Giga Drain", "Leech Seed", "Mud Shot"]),
    ("Mossquake", "Mossburrow", 48, ("Ground", "Grass"), (95, 120, 105, 55, 70, 85), "Rock Head",
                        ["Earthquake", "Swords Dance", "Rock Slide", "Metal Claw"]),
]
for _name, *_args in _LATER:
    SPECIES[_name] = _grown(*_args)


def _spread(shape, total):
    """Base stats in the proportions of `shape`, adding up to `total`."""
    k = total / sum(shape)
    out = [max(10, round(v * k)) for v in shape]
    out[out.index(max(out))] += total - sum(out)
    return tuple(out)


# Forest Dex pages two and three (2026-10-27, his ask; names under his rules): page two's lines
# get their later stages, and page three is sixteen new lines from two new places, the Crystal
# Caverns and the Starfall Meadow (#097-#144). Each later stage: (name, from, num, types, shape,
# ability, more moves); its base stats keep the shape, totalling 410 (middle) or 530 (final).
_PAGE2 = [
    ("Sporecrown", "Sporestride", 51, ("Grass", "Poison"), None, "Effect Spore", ["Sludge Bomb", "Spore", "Earthquake"]),
    ("Frostslink", "Rimeslink", 53, ("Water", "Ice"), None, "Water Absorb", ["Ice Beam", "Surf", "Waterfall"]),
    ("Hailmaw", "Frostslink", 54, ("Water", "Ice"), (95, 90, 80, 100, 80, 85), "Water Absorb", ["Hydro Pump", "Crunch", "Rest"]),
    ("Copperclad", "Coppernib", 56, ("Steel", "Electric"), None, "Static", ["Metal Claw", "Thunderbolt", "Protect"]),
    ("Voltbastion", "Copperclad", 57, ("Steel", "Electric"), (80, 100, 120, 95, 75, 60), "Static", ["Meteor Mash", "Earthquake", "Swords Dance"]),
    ("Duskhoot", "Moonhoot", 59, ("Normal", "Flying"), None, "Keen Eye", ["Wing Attack", "Psybeam", "Faint Attack"]),
    ("Lunarch", "Duskhoot", 60, ("Psychic", "Flying"), (90, 70, 75, 115, 100, 80), "Keen Eye", ["Psychic", "Calm Mind", "Shadow Ball", "Hypnosis"]),
    ("Glimmerpaw", "Frostpaw", 62, ("Ice",), None, "Run Away", ["Ice Beam", "Crunch", "Icy Wind"]),
    ("Auroracle", "Glimmerpaw", 63, ("Ice", "Psychic"), (75, 70, 70, 115, 95, 105), "Run Away", ["Psychic", "Calm Mind", "Confuse Ray"]),
    ("Cragfluff", "Fluffhorn", 65, ("Rock", "Normal"), None, "Rock Head", ["Rock Slide", "Double-Edge", "Iron Defense"]),
    ("Peakcloak", "Cragfluff", 66, ("Rock", "Fighting"), (100, 115, 115, 55, 80, 65), "Rock Head", ["Cross Chop", "Earthquake", "Bulk Up"]),
    ("Shimmertrill", "Shimmerchirp", 68, ("Ice", "Flying"), None, "Keen Eye", ["Ice Beam", "Aerial Ace", "Air Cutter"]),
    ("Boreallume", "Shimmertrill", 69, ("Ice", "Flying"), (75, 70, 70, 110, 90, 115), "Keen Eye", ["Aurora Beam", "Calm Mind", "Twister"]),
    ("Steamsoak", "Steambara", 71, ("Water", "Fire"), None, "Oblivious", ["Surf", "Flamethrower", "Rest"]),
    ("Geyserbelly", "Steamsoak", 72, ("Water", "Fire"), (125, 70, 95, 100, 95, 45), "Oblivious", ["Hydro Pump", "Heat Wave", "Calm Mind"]),
    ("Cindercling", "Embercling", 74, ("Fire", "Ground"), None, "Flash Fire", ["Flamethrower", "Mud Shot", "Slash"]),
    ("Magmascale", "Cindercling", 75, ("Fire", "Ground"), (80, 110, 80, 95, 70, 95), "Flash Fire", ["Earthquake", "Blaze Kick", "Dragon Dance"]),
    ("Vaporbell", "Vaporwobble", 77, ("Water", "Electric"), None, "Static", ["Thunderbolt", "Surf", "Recover"]),
    ("Stormbloom", "Vaporbell", 78, ("Water", "Electric"), (90, 50, 75, 120, 115, 80), "Static", ["Hydro Pump", "Calm Mind", "Thunder Wave"]),
    ("Bramblesnare", "Bramblit", 80, ("Grass", "Dark"), None, "Poison Point", ["Giga Drain", "Crunch", "Leech Seed"]),
    ("Thornregent", "Bramblesnare", 81, ("Grass", "Dark"), (90, 115, 95, 75, 75, 80), "Poison Point", ["Swords Dance", "Slash", "Sludge Bomb"]),
    ("Thistlegaze", "Thistlume", 83, ("Psychic", "Flying"), None, "Keen Eye", ["Psychic", "Air Cutter", "Hypnosis"]),
    ("Thistleseer", "Thistlegaze", 84, ("Psychic", "Flying"), (70, 50, 65, 125, 110, 110), "Keen Eye", ["Calm Mind", "Shadow Ball", "Silver Wind"]),
    ("Runestand", "Runelet", 86, ("Rock", "Ghost"), None, "Sturdy", ["Shadow Ball", "Rock Slide", "Curse"]),
    ("Runewarden", "Runestand", 87, ("Rock", "Ghost"), (90, 100, 130, 90, 90, 30), "Sturdy", ["Earthquake", "Pain Split", "Calm Mind"]),
    ("Arcfly", "Sparkfly", 89, ("Electric", "Bug"), None, "Static", ["Thunderbolt", "Signal Beam", "Agility"]),
    ("Thunderfly", "Arcfly", 90, ("Electric", "Bug"), (70, 70, 65, 110, 80, 135), "Static", ["Tail Glow", "Silver Wind", "Double Team"]),
    ("Murkgloop", "Murkling", 92, ("Water", "Poison"), None, "Liquid Ooze", ["Sludge Bomb", "Surf", "Toxic"]),
    ("Murkdredge", "Murkgloop", 93, ("Water", "Poison"), (120, 80, 90, 95, 105, 40), "Liquid Ooze", ["Hydro Pump", "Recover", "Shadow Ball"]),
    ("Glintdome", "Glintshell", 95, ("Steel",), None, "Shell Armor", ["Iron Defense", "Metal Claw", "Rock Slide"]),
    ("Glintcitadel", "Glintdome", 96, ("Steel", "Rock"), (90, 105, 140, 60, 90, 45), "Shell Armor", ["Meteor Mash", "Earthquake", "Rest"]),
]

# page three: (first, middle, final, types, final types, shape, ability, moves)
_PAGE3 = [
    # the Crystal Caverns (above the Waterfall)
    ("Geodling", "Geodcrest", "Geodsage", ("Rock", "Psychic"), None, (70, 55, 95, 90, 85, 35), "Sturdy",
     ["Rock Tomb", "Confusion", "Harden", "Ancient Power", "Psybeam", "Rock Slide", "Calm Mind", "Psychic", "Iron Defense"]),
    ("Humlet", "Humchime", "Resonarch", ("Steel", "Psychic"), None, (60, 45, 85, 95, 85, 60), "Levitate",
     ["Confusion", "Metal Claw", "Supersonic", "Psybeam", "Iron Defense", "Hypnosis", "Psychic", "Screech", "Calm Mind"]),
    ("Dripling", "Dripspire", "Stalagdeep", ("Water", "Ground"), None, (85, 80, 85, 60, 70, 50), "Water Absorb",
     ["Water Gun", "Mud-Slap", "Mud Shot", "Water Pulse", "Rock Tomb", "Surf", "Earthquake", "Amnesia", "Rest"]),
    ("Lumicrawl", "Lumitrek", "Lumicaravan", ("Bug", "Rock"), None, (70, 90, 105, 50, 70, 45), "Shell Armor",
     ["Leech Life", "Harden", "Rock Tomb", "Signal Beam", "Pin Missile", "Rock Slide", "Flash", "Ancient Power", "Iron Defense"]),
    ("Umbrit", "Umbrage", "Umbravast", ("Dark", "Ghost"), None, (55, 85, 60, 85, 65, 95), "Levitate",
     ["Astonish", "Faint Attack", "Night Shade", "Confuse Ray", "Bite", "Shadow Ball", "Crunch", "Double Team", "Curse"]),
    ("Ferrodig", "Ferrodrill", "Ferrocore", ("Steel", "Ground"), None, (75, 105, 100, 45, 60, 65), "Rock Head",
     ["Metal Claw", "Mud-Slap", "Sand-Attack", "Iron Tail", "Mud Shot", "Iron Defense", "Earthquake", "Swords Dance", "Slash"]),
    ("Shardling", "Shardfang", "Shardsovereign", ("Dragon", "Ice"), None, (85, 115, 85, 90, 75, 80), "Sturdy",
     ["Dragon Breath", "Powder Snow", "Bite", "Icy Wind", "Dragon Claw", "Ice Beam", "Crunch", "Dragon Dance", "Twister"]),
    ("Pebblefist", "Cobblefist", "Quarryfist", ("Fighting", "Rock"), None, (85, 120, 100, 40, 75, 60), "Guts",
     ["Karate Chop", "Rock Tomb", "Mach Punch", "Harden", "Brick Break", "Rock Slide", "Bulk Up", "Cross Chop", "Fire Punch"]),
    # the Starfall Meadow (beside the Waterfall)
    ("Twinklet", "Twinkstride", "Celestide", ("Normal",), ("Normal", "Psychic"), (90, 70, 75, 95, 95, 75), "Keen Eye",
     ["Quick Attack", "Flash", "Confusion", "Return", "Psybeam", "Calm Mind", "Body Slam", "Psychic", "Morning Sun"]),
    ("Tufflet", "Tuftrot", "Meadowmane", ("Grass", "Normal"), None, (95, 95, 80, 70, 80, 80), "Overgrow",
     ["Absorb", "Quick Attack", "Magical Leaf", "Headbutt", "Leech Seed", "Body Slam", "Giga Drain", "Synthesis", "Double-Edge"]),
    ("Meteorlet", "Meteorblaze", "Starforge", ("Fire", "Rock"), None, (80, 110, 90, 100, 70, 80), "Flash Fire",
     ["Ember", "Rock Tomb", "Flamethrower", "Ancient Power", "Rock Slide", "Heat Wave", "Will-O-Wisp", "Meteor Mash", "Take Down"]),
    ("Kickbud", "Kickbloom", "Kickgrove", ("Fighting", "Grass"), None, (85, 120, 85, 60, 75, 105), "Guts",
     ["Karate Chop", "Absorb", "Mach Punch", "Magical Leaf", "Brick Break", "Blaze Kick", "Giga Drain", "Bulk Up", "Leech Seed"]),
    ("Zaplet", "Zapstreak", "Zaptempest", ("Electric", "Flying"), None, (70, 75, 65, 105, 75, 140), "Static",
     ["Spark", "Gust", "Thunder Wave", "Shock Wave", "Wing Attack", "Thunderbolt", "Agility", "Aerial Ace", "Air Cutter"]),
    ("Dreamote", "Dreamwing", "Dreamloom", ("Bug", "Psychic"), None, (70, 50, 70, 115, 105, 120), "Shield Dust",
     ["Confusion", "Silver Wind", "Sleep Powder", "Psybeam", "Signal Beam", "Hypnosis", "Psychic", "Calm Mind", "Morning Sun"]),
    ("Dustlet", "Dustwhirl", "Dustcyclone", ("Ground",), ("Ground", "Flying"), (75, 100, 75, 70, 70, 140), "Run Away",
     ["Sand-Attack", "Mud-Slap", "Quick Attack", "Mud Shot", "Gust", "Agility", "Earthquake", "Twister", "Double Team"]),
    ("Wishlet", "Wishlantern", "Wishhaven", ("Ghost", "Psychic"), None, (90, 50, 80, 110, 120, 80), "Levitate",
     ["Astonish", "Confusion", "Flash", "Night Shade", "Psybeam", "Morning Sun", "Shadow Ball", "Psychic", "Recover"]),
]


def _grown_shaped(name, first, num, types, shape, ability, more):
    total = 410 if num % 3 == 2 else 530  # middle stages sit in the middle of their line's three numbers
    d = _grown(first, num, types, _spread(shape or SPECIES[first]["base"], total), ability, more)
    return d


for _name, _first, _num, _types, _shape, _ability, _more in _PAGE2:
    SPECIES[_name] = _grown_shaped(_name, _first, _num, _types, _shape, _ability, _more)
for _i, (_a, _b, _c, _types, _final, _shape, _ability, _pool) in enumerate(_PAGE3):
    _num = 97 + _i * 3
    _first = list(_shape)
    _first[1 if _shape[1] >= _shape[3] else 3] += 8  # a first stage leans on its best attack a little more
    SPECIES[_a] = dict(num=_num, types=_types, base=_spread(_first, 312), ability=_ability, pool=_pool[:6])
    SPECIES[_b] = _grown(_a, _num + 1, _types, _spread(_shape, 410), _ability, _pool[6:8])
    SPECIES[_c] = _grown(_b, _num + 2, _final or _types, _spread(_shape, 530), _ability, _pool[8:])


# Forest Dex pages four to six (2026-10-27, his ask): 38 new three-stage lines (#145-#258), living
# in the ten places he already has, and two legendaries at #259-#260 that come out only rarely.
# (first, middle, final, types, final types, shape, ability, nine moves); drawn in wave5.py.
_PAGE4 = [
    # the Glade
    ("Petalpip", "Petalprim", "Petalregal", ("Grass",), ("Grass", "Normal"), (80, 75, 85, 90, 95, 75), "Effect Spore",
     ["Absorb", "Magical Leaf", "Sleep Powder", "Quick Attack", "Mega Drain", "Leech Seed", "Giga Drain", "Synthesis", "Body Slam"]),
    ("Lullabud", "Lullabloom", "Lullagrove", ("Grass", "Psychic"), None, (85, 55, 80, 110, 100, 70), "Keen Eye",
     ["Confusion", "Absorb", "Hypnosis", "Magical Leaf", "Psybeam", "Sleep Powder", "Psychic", "Calm Mind", "Giga Drain"]),
    ("Gleamwick", "Gleamtorch", "Gleambeacon", ("Fire",), ("Fire", "Ghost"), (65, 50, 70, 115, 90, 90), "Flash Fire",
     ["Ember", "Astonish", "Will-O-Wisp", "Confuse Ray", "Flamethrower", "Night Shade", "Shadow Ball", "Heat Wave", "Calm Mind"]),
    ("Hushling", "Hushveil", "Hushwarden", ("Ghost",), ("Ghost", "Normal"), (90, 60, 85, 90, 105, 50), "Levitate",
     ["Astonish", "Lick", "Night Shade", "Confuse Ray", "Hypnosis", "Shadow Ball", "Pain Split", "Rest", "Curse"]),
    # the Waterfall
    ("Splashkin", "Splashtide", "Cascadon", ("Water",), ("Water", "Fighting"), (90, 105, 80, 70, 75, 90), "Swift Swim",
     ["Water Gun", "Quick Attack", "Bubble Beam", "Mach Punch", "Water Pulse", "Brick Break", "Waterfall", "Bulk Up", "Cross Chop"]),
    ("Mistmote", "Mistplume", "Mistcrest", ("Water", "Flying"), None, (75, 70, 70, 95, 85, 110), "Keen Eye",
     ["Water Gun", "Gust", "Peck", "Wing Attack", "Bubble Beam", "Air Cutter", "Surf", "Aerial Ace", "Agility"]),
    ("Slatelet", "Slatebound", "Slatecliff", ("Rock", "Water"), None, (90, 100, 130, 60, 80, 35), "Sturdy",
     ["Rock Tomb", "Water Gun", "Harden", "Withdraw", "Rock Slide", "Bubble Beam", "Waterfall", "Iron Defense", "Earthquake"]),
    ("Foamlet", "Foamcurl", "Foamcrest", ("Water", "Psychic"), None, (95, 50, 75, 100, 105, 65), "Water Absorb",
     ["Water Gun", "Confusion", "Bubble Beam", "Amnesia", "Psybeam", "Water Pulse", "Psychic", "Recover", "Surf"]),
    # the River
    ("Reedlet", "Reedrunner", "Reedmarsh", ("Grass", "Water"), None, (75, 95, 75, 80, 75, 110), "Swift Swim",
     ["Absorb", "Water Gun", "Quick Attack", "Magical Leaf", "Water Pulse", "Leech Seed", "Giga Drain", "Surf", "Agility"]),
    ("Ripplet", "Rippleback", "Ripplelord", ("Water", "Ground"), None, (110, 85, 115, 70, 85, 30), "Shell Armor",
     ["Water Gun", "Mud-Slap", "Withdraw", "Mud Shot", "Water Pulse", "Rest", "Earthquake", "Surf", "Amnesia"]),
    ("Bubblo", "Bubblosh", "Bubblorb", ("Water", "Electric"), None, (80, 45, 70, 110, 90, 100), "Static",
     ["Bubble Beam", "Spark", "Water Gun", "Thunder Wave", "Shock Wave", "Water Pulse", "Thunderbolt", "Surf", "Recover"]),
    ("Siltpaw", "Siltstride", "Siltgrand", ("Ground", "Water"), None, (100, 110, 95, 55, 70, 75), "Water Absorb",
     ["Mud-Slap", "Water Gun", "Bite", "Mud Shot", "Take Down", "Waterfall", "Earthquake", "Crunch", "Body Slam"]),
    # the Forest
    ("Barkling", "Barkbrute", "Barkmonarch", ("Grass", "Fighting"), None, (100, 120, 105, 50, 75, 55), "Guts",
     ["Karate Chop", "Absorb", "Harden", "Mach Punch", "Magical Leaf", "Brick Break", "Bulk Up", "Giga Drain", "Cross Chop"]),
    ("Fernflit", "Fernglide", "Fernsong", ("Grass", "Flying"), None, (70, 75, 65, 90, 80, 120), "Keen Eye",
     ["Peck", "Absorb", "Gust", "Magical Leaf", "Wing Attack", "Air Cutter", "Giga Drain", "Aerial Ace", "Synthesis"]),
    ("Hollowink", "Hollowmask", "Hollowking", ("Ghost", "Grass"), None, (80, 100, 85, 95, 85, 75), "Levitate",
     ["Astonish", "Absorb", "Night Shade", "Leech Seed", "Faint Attack", "Shadow Ball", "Giga Drain", "Curse", "Confuse Ray"]),
    ("Sapsip", "Sapsurge", "Sapsentinel", ("Bug", "Grass"), None, (75, 80, 95, 85, 95, 70), "Shield Dust",
     ["Leech Life", "Absorb", "Harden", "Silver Wind", "Mega Drain", "Signal Beam", "Giga Drain", "Synthesis", "Iron Defense"]),
    # the Mossy Rocks
    ("Rubblet", "Rubbleback", "Rubblequake", ("Rock", "Ground"), None, (95, 115, 120, 45, 70, 55), "Rock Head",
     ["Rock Tomb", "Mud-Slap", "Harden", "Headbutt", "Rock Slide", "Mud Shot", "Earthquake", "Double-Edge", "Iron Defense"]),
    ("Quillnip", "Quillback", "Quillfortress", ("Rock", "Poison"), None, (80, 95, 115, 70, 80, 60), "Poison Point",
     ["Poison Tail", "Rock Tomb", "Harden", "Pin Missile", "Sludge", "Rock Slide", "Sludge Bomb", "Toxic", "Iron Defense"]),
    ("Echolet", "Echowing", "Echodome", ("Normal", "Flying"), ("Normal", "Psychic"), (85, 60, 75, 100, 90, 100), "Inner Focus",
     ["Supersonic", "Gust", "Quick Attack", "Confusion", "Wing Attack", "Psybeam", "Psychic", "Aerial Ace", "Hypnosis"]),
    ("Sigilet", "Sigilward", "Sigilcolossus", ("Rock", "Psychic"), None, (90, 75, 110, 105, 105, 35), "Sturdy",
     ["Confusion", "Rock Tomb", "Harden", "Psybeam", "Ancient Power", "Rock Slide", "Psychic", "Calm Mind", "Iron Defense"]),
    # the Snowy Ridge
    ("Snowpuff", "Snowcloak", "Snowmonarch", ("Ice",), ("Ice", "Normal"), (115, 80, 95, 75, 90, 45), "Thick Fat",
     ["Powder Snow", "Headbutt", "Rest", "Icy Wind", "Body Slam", "Amnesia", "Ice Beam", "Double-Edge", "Curse"]),
    ("Shiverling", "Shivershard", "Shiverspire", ("Ice", "Steel"), None, (70, 110, 105, 70, 70, 75), "Sturdy",
     ["Powder Snow", "Metal Claw", "Harden", "Icy Wind", "Iron Tail", "Slash", "Ice Beam", "Meteor Mash", "Swords Dance"]),
    ("Glacelet", "Glaceglide", "Glacewing", ("Ice", "Flying"), None, (70, 85, 70, 85, 75, 115), "Keen Eye",
     ["Powder Snow", "Peck", "Gust", "Icy Wind", "Wing Attack", "Aurora Beam", "Ice Beam", "Aerial Ace", "Agility"]),
    ("Conelet", "Conecrest", "Conelord", ("Grass", "Ice"), None, (95, 100, 100, 70, 85, 50), "Shell Armor",
     ["Absorb", "Powder Snow", "Harden", "Magical Leaf", "Icy Wind", "Leech Seed", "Giga Drain", "Ice Beam", "Iron Defense"]),
    # the Hot Springs
    ("Ashpaw", "Ashstride", "Ashcolossus", ("Fire",), ("Fire", "Normal"), (85, 110, 80, 80, 70, 95), "Flash Fire",
     ["Ember", "Quick Attack", "Bite", "Fire Punch", "Take Down", "Flamethrower", "Crunch", "Heat Wave", "Double-Edge"]),
    ("Sulfling", "Sulfspout", "Sulfgeyser", ("Poison", "Fire"), None, (100, 60, 85, 100, 95, 50), "Liquid Ooze",
     ["Sludge", "Ember", "Acid Armor", "Toxic", "Flamethrower", "Haze", "Sludge Bomb", "Heat Wave", "Recover"]),
    ("Lavalet", "Lavaglide", "Lavacrest", ("Fire", "Flying"), None, (75, 80, 70, 100, 80, 115), "Flash Fire",
     ["Ember", "Gust", "Peck", "Wing Attack", "Flamethrower", "Air Cutter", "Heat Wave", "Aerial Ace", "Morning Sun"]),
    ("Obsidling", "Obsidblade", "Obsidclaw", ("Dark", "Fire"), None, (75, 120, 90, 80, 70, 90), "Inner Focus",
     ["Bite", "Ember", "Faint Attack", "Slash", "Fire Punch", "Crunch", "Blaze Kick", "Swords Dance", "Flamethrower"]),
    # the Battle Tower
    ("Gongling", "Gongstrike", "Gongmaster", ("Steel", "Fighting"), None, (90, 115, 110, 60, 80, 70), "Inner Focus",
     ["Metal Claw", "Karate Chop", "Harden", "Brick Break", "Iron Tail", "Bulk Up", "Meteor Mash", "Cross Chop", "Iron Defense"]),
    ("Spirelet", "Spireguard", "Spirehalo", ("Steel", "Psychic"), None, (80, 60, 100, 105, 110, 55), "Levitate",
     ["Confusion", "Metal Claw", "Iron Defense", "Psybeam", "Flash", "Calm Mind", "Psychic", "Meteor Mash", "Recover"]),
    ("Dueljab", "Dueledge", "Duelheart", ("Fighting",), ("Fighting", "Dark"), (80, 120, 80, 60, 75, 105), "Guts",
     ["Karate Chop", "Quick Attack", "Mach Punch", "Faint Attack", "Brick Break", "Slash", "Cross Chop", "Crunch", "Swords Dance"]),
    # the Crystal Caverns
    ("Mycelet", "Mycespire", "Mycethrone", ("Grass", "Dark"), None, (95, 85, 90, 95, 95, 40), "Effect Spore",
     ["Absorb", "Faint Attack", "Spore", "Stun Spore", "Mega Drain", "Bite", "Giga Drain", "Crunch", "Synthesis"]),
    ("Deepling", "Deepglow", "Deepmaw", ("Water", "Dark"), None, (90, 115, 80, 75, 70, 90), "Swift Swim",
     ["Water Gun", "Bite", "Flash", "Faint Attack", "Waterfall", "Crunch", "Hydro Pump", "Dragon Dance", "Surf"]),
    ("Quartzlet", "Quartzback", "Quartzcolossus", ("Rock", "Steel"), None, (85, 105, 140, 50, 85, 35), "Sturdy",
     ["Rock Tomb", "Metal Claw", "Harden", "Iron Defense", "Rock Slide", "Iron Tail", "Meteor Mash", "Earthquake", "Rest"]),
    ("Gemmet", "Gemwing", "Gemflare", ("Bug", "Rock"), None, (70, 80, 80, 90, 75, 110), "Shield Dust",
     ["Leech Life", "Rock Tomb", "Silver Wind", "Signal Beam", "Ancient Power", "Agility", "Rock Slide", "Tail Glow", "Double Team"]),
    # the Starfall Meadow
    ("Starbud", "Starbloom", "Starblossom", ("Grass", "Psychic"), None, (80, 60, 80, 110, 105, 85), "Effect Spore",
     ["Absorb", "Confusion", "Sleep Powder", "Magical Leaf", "Psybeam", "Morning Sun", "Psychic", "Giga Drain", "Calm Mind"]),
    ("Breezlet", "Breezeplume", "Breezemonarch", ("Normal", "Flying"), None, (85, 90, 75, 75, 75, 120), "Keen Eye",
     ["Gust", "Quick Attack", "Peck", "Wing Attack", "Air Cutter", "Agility", "Aerial Ace", "Double-Edge", "Twister"]),
    ("Dewlet", "Dewglimmer", "Dewcascade", ("Water", "Grass"), None, (90, 55, 80, 105, 105, 75), "Water Absorb",
     ["Water Gun", "Absorb", "Bubble Beam", "Mega Drain", "Water Pulse", "Leech Seed", "Giga Drain", "Surf", "Recover"]),
]
LEGENDARY = {
    # his rules (2026-10-27): legendaries never evolve, total 570-700, the stronger the rarer; only
    # two may ever be 700 (a "main"/cover legendary), unless he asks for another. Moonward is one.
    "Elderglow": dict(num=259, types=("Grass", "Psychic"), base=(110, 85, 110, 115, 120, 100), ability="Levitate",
                      pool=["Giga Drain", "Psychic", "Calm Mind", "Synthesis", "Leech Seed", "Ancient Power",
                            "Magical Leaf", "Recover", "Shadow Ball", "Sleep Powder"]),
    "Moonward": dict(num=260, types=("Psychic", "Dragon"), base=(110, 110, 105, 140, 125, 110), ability="Levitate",
                     pool=["Dragon Claw", "Psychic", "Dragon Dance", "Calm Mind", "Ice Beam", "Twister",
                           "Shadow Ball", "Recover", "Thunderbolt", "Aerial Ace"]),
}
for _i, (_a, _b, _c, _types, _final, _shape, _ability, _pool) in enumerate(_PAGE4):
    _num = 145 + _i * 3
    _first = list(_shape)
    _first[1 if _shape[1] >= _shape[3] else 3] += 8
    SPECIES[_a] = dict(num=_num, types=_types, base=_spread(_first, 300 + (_num * 7) % 21), ability=_ability, pool=_pool[:6])
    SPECIES[_b] = _grown(_a, _num + 1, _types, _spread(_shape, 410), _ability, _pool[6:8])
    SPECIES[_c] = _grown(_b, _num + 2, _final or _types, _spread(_shape, 530), _ability, _pool[8:])
SPECIES.update(LEGENDARY)


def _retotal():
    """His ask (2026-10-27): a wider spread of base stat totals. Pokémon's own finals run from the
    470s to 600 (Beautifly 395, Dragonite 600); so do these now, each keeping the shape of its
    stats. Middle stages spread 380-440. The starters stay at 530 (Pokémon keeps its starters
    level); the two dragons that are nearly Dragonite's height are this Dex's pseudo-legendaries
    at 600; the legendaries are 600-620 on their own."""
    import zlib
    for name, d in SPECIES.items():
        num = d["num"]
        if num <= 9 or name in LEGENDARY:
            continue
        stage = (num - 1) % 3 + 1
        roll = zlib.crc32(name.encode()) % 1000 / 1000
        if stage == 3:
            total = 600 if name in ("Prismwyrm", "Shardsovereign") else round(465 + roll * 115)
        elif stage == 2:
            total = round(380 + roll * 60)
        else:
            continue
        d["base"] = _spread(d["base"], total)


_retotal()



STATS = ("atk", "def", "spa", "spd", "spe")
STAT_NAME = {"atk": "Attack", "def": "Defense", "spa": "Sp. Atk", "spd": "Sp. Def", "spe": "Speed",
             "acc": "accuracy", "eva": "evasiveness"}
STATUS_TAG = dict(par="PAR", psn="PSN", tox="TOX", slp="SLP", frz="FRZ", brn="BRN")
CRIT = (1 / 16, 1 / 8, 1 / 4, 1 / 3, 1 / 2)
# Gen 3 accuracy/evasion stages, -6..+6
ACC = ((33, 100), (36, 100), (43, 100), (50, 100), (60, 100), (75, 100), (1, 1),
       (133, 100), (166, 100), (2, 1), (233, 100), (133, 50), (3, 1))
LEVEL = 100


STARTER_ABILITY = {"Overgrow": "Grass", "Blaze": "Fire", "Torrent": "Water"}


def calc_stats(species, ivs, evs, nature):
    """Gen 3 stats at level 100: HP = (2*Base + IV + EV/4) * L/100 + L + 10; the others
    (2*Base + IV + EV/4) * L/100 + 5, then x1.1 or x0.9 for the nature. Returns (hp, {stat: v})."""
    from team import nature_effect
    hp, *rest = SPECIES[species]["base"]
    up, down = nature_effect(nature)
    maxhp = (2 * hp + ivs[0] + evs[0] // 4) * LEVEL // 100 + LEVEL + 10
    stats = {}
    for k, b, iv, ev in zip(STATS, rest, ivs[1:], evs[1:]):
        v = (2 * b + iv + ev // 4) * LEVEL // 100 + 5
        stats[k] = v * 11 // 10 if k == up else v * 9 // 10 if k == down else v
    return maxhp, stats


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
    def __init__(self, species, rng, foe=False, ivs=None, moves=None, label=None, nature=None, evs=None):
        """`ivs`: its own IVs (team.py), all 31 if not given; `moves`: its four, or random ones;
        `nature`: its nature (neutral if not given); `evs`: its effort values (84 each)."""
        from team import EVS
        sp = SPECIES[species]
        self.species, self.types, self.ability = species, sp["types"], sp["ability"]
        self.name = label or (("Foe " if foe else "") + species)
        self.ivs = tuple(ivs) if ivs else (31,) * 6
        self.nature = nature or "Hardy"
        self.evs = tuple(evs or EVS)
        self.maxhp, self.stats = calc_stats(species, self.ivs, self.evs, self.nature)
        self.hp = self.maxhp
        picked = [m for m in (moves or []) if m in MOVES] or moveset(species, rng)
        self.moves = [[m, MOVES[m]["pp"]] for m in picked]
        self.status, self.sleep, self.toxic, self.confused = None, 0, 0, 0
        self.boosts = dict.fromkeys(STATS + ("acc", "eva"), 0)
        self.flinch, self.protected, self.protect_run = False, False, 0
        self.seeded = False
        self.item = "Leftovers"

    def speed(self):
        s = staged(self.stats["spe"], self.boosts["spe"])
        return s // 4 if self.status == "par" else s

    def usable(self):
        return [i for i, (_, pp) in enumerate(self.moves) if pp > 0]


def as_mon(x, rng, foe):
    """A Mon from a species name, a (species, ivs, moves) tuple, or a team.Kept."""
    if isinstance(x, Mon):
        return x
    if isinstance(x, str):
        return Mon(x, rng, foe)
    if isinstance(x, tuple):
        species, ivs, moves, nature = (list(x) + [None, None, None])[:4]
        return Mon(species, rng, foe, ivs, moves, nature=nature or rng.choice(NATURE_LIST()))
    return Mon(x.species, rng, foe, x.ivs, x.moves, nature=x.nature, evs=x.evs)


def NATURE_LIST():
    from team import NATURES
    return NATURES


class Battle:
    """The rules. Each side is a team of one to six (Gen 3 singles: one out at a time).
    `turn(action)` plays a whole turn: `action` is a move's number, ("switch", i) or
    ("jar",) — a glow jar thrown at a wild animal. What happened is added to `events`:
    (text, (your hp, its hp), (your status, its status), who was hit, who acted, who is out)
    — sides are 0 (yours) and 1; "who acted" is -1 - side when that side faints; "who is out"
    is each side's place in its team. When yours faints and you have more, `need` is 0 until
    you send the next one out with ("switch", i)."""

    def __init__(self, mine, theirs, rng=None, wild=False, intro=None):
        self.rng = rng or random.Random()
        mine = mine if isinstance(mine, list) else [mine]
        theirs = theirs if isinstance(theirs, list) else [theirs]
        self.teams = [[as_mon(x, self.rng, False) for x in mine][:6], [as_mon(x, self.rng, True) for x in theirs][:6]]
        self.active = [0, 0]
        self.fought = {0}  # which of yours have been out in this battle
        self.wild = wild
        self.need = None
        self.caught = None
        self.events = []
        self.winner = None
        self.number = 0
        a, b = self.mons
        self.say(intro or (f"A wild {b.species} appeared! Go, {a.name}!" if wild else
                           f"A wild battle! {a.name} vs. {b.name}!"))

    @property
    def mons(self):
        return [self.teams[0][self.active[0]], self.teams[1][self.active[1]]]

    def left(self, side):
        """How many on that side can still fight."""
        return sum(1 for m in self.teams[side] if m.hp > 0)

    # --- reporting ---
    def say(self, text, hit=None, by=None):
        a, b = self.mons
        self.events.append((text, (a.hp, b.hp), (a.status, b.status), hit, by, tuple(self.active)))

    def side(self, mon):
        return self.mons.index(mon)

    # --- a turn ---
    def turn(self, action):
        if self.winner is not None:
            return
        if self.need == 0:  # yours fainted: sending the next one out is not a turn
            if isinstance(action, tuple) and action[0] == "switch":
                self.switch_in(0, action[1])
                self.need = None
            return
        self.number += 1
        for m in self.mons:
            m.protected = False
        acted = [False, False]
        if isinstance(action, tuple) and action[0] == "switch":  # switching goes before any move
            self.switch_in(0, action[1])
            acted[0] = True
        elif isinstance(action, tuple) and action[0] == "jar":
            self.jar()
            acted[0] = True
            if self.winner is not None:
                return
        foe_pick = self.move_of(self.mons[1], self.choose())
        picks = [None if acted[0] else self.move_of(self.mons[0], action), foe_pick]
        order = sorted((s for s in range(2) if picks[s]),
                       key=lambda s: (MOVES[picks[s]].get("prio", 0), self.mons[s].speed(), self.rng.random()),
                       reverse=True)
        for n, s in enumerate(order):
            if any(m.hp <= 0 for m in self.mons):
                break  # someone is down: the rest of the turn has nobody to aim at
            self.act(self.mons[s], self.mons[1 - s], picks[s], first=n == 0 and not acted[0])
        self.end_of_turn([0, 1])
        for m in self.mons:
            m.flinch = False
        self.resolve()

    def resolve(self):
        """After a turn: who has lost, and who has to send in the next one."""
        for side in (1, 0):
            if self.mons[side].hp > 0 or self.winner is not None:
                continue
            if self.left(side) == 0:
                self.winner = 1 - side
                if self.winner == 0:
                    self.say(f"You win! {self.mons[0].name} is the champion of the glade!" if len(self.teams[1]) == 1
                             else "You won the battle!")
                else:
                    self.say(f"You lost... {self.mons[1].name} wins!" if len(self.teams[0]) == 1
                             else "You're out of creatures who can fight... You lost.")
            elif side == 1:  # the foe sends in its next one
                nxt = next(i for i, m in enumerate(self.teams[1]) if m.hp > 0)
                self.switch_in(1, nxt)
            else:
                self.need = 0
                self.say("Who will you send out next?")

    def switch_in(self, side, i):
        team = self.teams[side]
        if not (0 <= i < len(team)) or team[i].hp <= 0 or i == self.active[side]:
            return
        old = self.mons[side]
        old.boosts = dict.fromkeys(old.boosts, 0)
        old.confused, old.seeded, old.protect_run, old.flinch = 0, False, 0, False
        if old.status == "tox":
            old.toxic = 0
        self.active[side] = i
        if side == 0:
            self.fought.add(i)
        new = self.mons[side]
        if side == 0:
            self.say(f"Come back, {old.name}! Go, {new.name}!" if old.hp > 0 else f"Go, {new.name}!")
        else:
            self.say(f"The foe sent out {new.species}!")

    def jar(self):
        """Throw a glow jar at a wild animal: it wobbles, and holds or breaks open."""
        from team import catch_shakes
        f = self.mons[1]
        self.say("You threw a glow jar!")
        n = catch_shakes(f.maxhp, f.hp, f.status, self.rng)
        for _ in range(min(n, 3)):
            self.say("... the jar wobbles ...")
        if n == 4:
            self.caught = f
            self.winner = 0
            self.say(f"Gotcha! {f.species} was caught!")
        else:
            self.say(("Oh no! It broke free!", "Aww! It appeared to be caught!", "Argh! Almost had it!",
                      "Shoot! It was so close, too!")[min(n, 3)])

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
        if u.flinch and u.ability != "Inner Focus":
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
        if u.hp <= 0 or f.hp <= 0 or not self.can_move(u):
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
        at_foe = m["p"] > 0 or m.get("st") in ("par", "psn", "tox", "slp", "brn", "confuse", "seed") or "down" in m
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
        if f.ability == "Thick Fat" and t in ("Fire", "Ice"):
            a //= 2
        if u.hp * 3 <= u.maxhp and STARTER_ABILITY.get(u.ability) == t:  # Overgrow, Blaze, Torrent
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
        if m["t"] == "Water" and f.ability == "Water Absorb":
            if f.hp < f.maxhp:
                f.hp = min(f.maxhp, f.hp + f.maxhp // 4)
                self.say(f"{f.name} restored HP using its Water Absorb!")
            else:
                self.say(f"{f.name}'s Water Absorb made it useless!")
            return
        if m.get("fixed"):  # Night Shade: as much damage as the user's level
            dmg = min(f.hp, LEVEL)
            f.hp -= dmg
            self.say("", hit=self.side(f))
            self.check_faint(f)
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
        if m.get("recoil") and (u.ability != "Rock Head" or name == "Struggle"):
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
        if m.get("c") and f.hp > 0 and u.hp > 0 and f.ability == "Effect Spore" and rng.random() < 0.1:
            self.inflict(u, rng.choice(("psn", "par", "slp")), f"{f.name}'s Effect Spore")
        sec = m.get("sec")
        if sec and rng.random() * 100 < sec[0]:
            what = sec[1]
            if isinstance(what, tuple):  # ("self", boosts): the user gets them
                for k, v in what[1].items():
                    self.boost(u, k, v)
            elif f.ability == "Shield Dust" and what != "allup":
                pass  # Shield Dust: no side effects of moves land on it
            elif what == "allup":
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
        elif st == "seed":
            if f.seeded or "Grass" in f.types:
                self.say(f"{f.name} evaded the attack!" if "Grass" in f.types else "But it failed!")
            else:
                f.seeded = True
                self.say(f"{f.name} was seeded!")
        elif st in ("par", "psn", "tox", "slp", "brn"):
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
        if st == "brn" and "Fire" in f.types:
            return False
        f.status = st
        if st == "slp":
            f.sleep = self.rng.randint(2, 5)  # 1-4 turns asleep; it acts on the turn it wakes
        if st == "tox":
            f.toxic = 0
        text = dict(par="is paralyzed! It may be unable to move!", psn="was poisoned!", tox="was badly poisoned!",
                    slp="fell asleep!", frz="was frozen solid!", brn="was burned!")[st]
        self.say(f"{cause}! {f.name} {text}" if cause else f"{f.name} {text}")
        return True

    def boost(self, mon, k, v):
        old = mon.boosts[k]
        new = max(-6, min(6, old + v))
        nm = STAT_NAME[k]
        if k == "acc" and v < 0 and mon.ability == "Keen Eye":
            self.say(f"{mon.name}'s Keen Eye prevents accuracy loss!")
            return
        if new == old:
            self.say(f"{mon.name}'s {nm} won't go any {'higher' if v > 0 else 'lower'}!")
            return
        mon.boosts[k] = new
        word = ("rose!" if v == 1 else "sharply rose!") if v > 0 else ("fell!" if v == -1 else "harshly fell!")
        self.say(f"{mon.name}'s {nm} {word}")

    def check_faint(self, mon):
        if mon.hp <= 0 and not getattr(mon, "down", False):
            mon.hp = 0
            mon.down = True
            self.say(f"{mon.name} fainted!", by=-1 - self.side(mon))

    def end_of_turn(self, order):
        for s in order:
            m = self.mons[s]
            if m.hp <= 0:
                continue
            if m.hp < m.maxhp:
                m.hp = min(m.maxhp, m.hp + max(1, m.maxhp // 16))
                self.say(f"{m.name} restored a little HP using its Leftovers!")
            if m.seeded and m.hp > 0:  # Leech Seed: it feeds the other one every turn
                other = self.mons[1 - s]
                amt = min(m.hp, max(1, m.maxhp // 8))
                m.hp -= amt
                if other.hp > 0:
                    if m.ability == "Liquid Ooze":
                        other.hp = max(0, other.hp - amt)
                    else:
                        other.hp = min(other.maxhp, other.hp + amt)
                self.say(f"{m.name}'s health is sapped by Leech Seed!", hit=s)
                self.check_faint(m)
                self.check_faint(other)
                if m.hp <= 0:
                    continue
            if m.status == "brn":
                m.hp = max(0, m.hp - max(1, m.maxhp // 8))
                self.say(f"{m.name} is hurt by its burn!", hit=s)
            if m.status == "psn":
                m.hp = max(0, m.hp - max(1, m.maxhp // 8))
                self.say(f"{m.name} is hurt by poison!", hit=s)
            elif m.status == "tox":
                m.toxic += 1
                m.hp = max(0, m.hp - max(1, m.maxhp * m.toxic // 16))
                self.say(f"{m.name} is hurt by poison!", hit=s)
            self.check_faint(m)

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
                    dmg = LEVEL if m.get("fixed") else self.damage(me, them, m, roll=92) * (3 if m.get("multi") else 1)
                    score = 1000 * acc if dmg >= them.hp else 100 * min(1.0, dmg / them.hp) * acc
            else:
                st = m.get("st")
                score = 0
                if "up" in m and all(me.boosts[k] < 2 for k, v in m["up"].items() if v > 0) and me.hp > me.maxhp * .6:
                    score = 45
                elif "down" in m:
                    score = 20
                elif st in ("par", "psn", "tox", "slp", "brn") and them.status is None:
                    score = 55 * acc
                elif st == "seed" and not them.seeded and "Grass" not in them.types:
                    score = 50 * acc
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
    if getattr(obj, "species", None):  # beasts.py: they say what they are
        return obj.species
    name = type(obj).__name__
    if name in ("Squid", "Nibbler", "HollowSquid"):
        return "Driftlet"
    if name == "Slug":
        return "Cairncurl" if getattr(obj, "shell", None) else "Gloamooze"
    if name == "Fish":
        return "Lilyfin"
    if name == "Millipede":
        return "Luminpede"
    if name == "Critter":
        return "Duskling"
    if name == "TreeSquid":
        return "Moonhoot" if getattr(obj, "kind", "squid") == "owlet" else "Canopod"
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
        out += [(Perched(sq), species_of(sq)) for sq in colony.squid.values()
                if sq.fade > 0.5 and not getattr(sq, "gone", False)]
    return out


# --- finding the animal under the pointer -------------------------------------------

KEY = (1, 254, 3)  # a colour nothing in the glade is drawn in
_patch = []


def animal_under(scene, lower, m, low, t, skip=(), exact=False):
    """The (animal, species) under the pointer `m` (in that screen's own pixels; `low`: the
    lower screen). Anywhere on its body counts: each one nearby is drawn into a tiny patch
    round the pointer, and if it puts any colour there, it was hit. Failing that, the
    nearest one close by (not when `exact`)."""
    x, y = (m[0] + OFFSET[0], m[1] + OFFSET[1]) if low else m
    near, hits = [], []
    for a, sp in animals(scene, lower):
        if a.low != low or getattr(a.obj, "gone", False) or any(a.obj is o for o in skip):
            continue
        ax, ay = a.pos()
        d = math.hypot(ax - x, ay - y)
        if d < 90:
            near.append((d, a, sp))
    near.sort(key=lambda n: n[0])
    hits = [n for n in near if touches(n[1], m, t)]
    best = hits[0] if hits else (near[0] if near and not exact else None)
    if best is None or (not hits and best[0] > 24):
        return None
    return best[1], best[2]


def touches(a, m, t):
    if not _patch:
        _patch.append(art.solid())
    patch = _patch[0]
    box = pygame.Rect(round(m[0]) - 4, round(m[1]) - 4, 9, 9).clip(patch.get_rect())
    if box.w <= 0 or box.h <= 0:
        return False
    patch.set_clip(box)
    patch.fill(KEY, box)
    o = a.obj
    if isinstance(a, Perched):
        o.shine(patch, t, 12)
    else:
        for part in ("draw", "shine"):
            fn = getattr(o, part, None)
            if fn:
                fn(patch, t)
    patch.set_clip(None)
    untouched = pygame.mask.from_threshold(patch.subsurface(box), KEY, (1, 1, 1, 255))
    return untouched.count() < box.w * box.h


# --- the battle box ------------------------------------------------------------------

EDGE = (24, 14, 34)
TEXT = (255, 238, 214)
DIM = (150, 136, 160)
CLOTH = (196, 140, 255)
MINE = (110, 255, 180)   # your animal: the paths' mint green
THEIRS = (255, 150, 214)  # its opponent: blossom pink
STEP = 0.95               # seconds each line of the log is shown before the next
WALK = 1.6                # seconds to walk onto the field (and home again)
# the field in the middle of the top screen: where each fighter stands (yours near,
# its opponent further back, as in the games) and the size of its mossy platform
SPOTS = ((400, 500), (570, 462))  # the middle of the screen, below the board
PADS = ((112, 26), (86, 20))


_CLOTHS = {}


def cloth(s, r, tint, hot=False, alpha=200):
    """A panel of the glade's glowing spirit-cloth, lit from above. Each look is made once
    and kept, since the same boards are drawn every frame."""
    r = pygame.Rect(r)
    key = (r.size, tuple(tint), hot, alpha)
    surf = _CLOTHS.get(key)
    if surf is None:
        if len(_CLOTHS) > 600:  # fades make a few hundred passing looks: forget them now and then
            _CLOTHS.clear()
        surf = _CLOTHS[key] = _weave(r, tint, hot, alpha)
    s.blit(surf, r)


def _weave(r, tint, hot, alpha):
    surf = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*mix(tint, EDGE, 0.72), alpha), surf.get_rect(), border_radius=4)
    light = pygame.Surface(r.size, pygame.SRCALPHA)  # drawn apart, then laid on top, so it blends
    for i in range(r.h - 4):
        a = round((80 if hot else 46) * (1 - i / r.h))
        pygame.draw.line(light, (*tint, a), (2, 2 + i), (r.w - 3, 2 + i))
    surf.blit(light, (0, 0))
    rim = (255, 255, 255) if hot else mix(tint, (255, 255, 255), 0.45)
    pygame.draw.rect(surf, (*rim, 230 if hot else 160), surf.get_rect(), 1, border_radius=4)
    return surf


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

    def face(self):
        """Turn to face the other side: yours (on the left) looks right, its foe looks left,
        and neither wanders off while it does."""
        o, f = self.a.obj, (1 if self.side == 0 else -1)
        if hasattr(o, "dir") and hasattr(o, "track"):  # a slug or millipede: the way it glides
            o.dir = f
            o.wait = max(getattr(o, "wait", 0.0), 0.5)
        if hasattr(o, "facing"):
            o.facing = f
            if hasattr(o, "wait"):
                o.wait = max(o.wait, 0.5)
                if isinstance(getattr(o, "target", None), (int, float)) and hasattr(o, "x"):
                    o.target = o.x
            if hasattr(o, "vx"):  # a flier: hovering
                o.vx, o.vy = 0.0, 0.0
                o.target = (o.x, o.y)

    def draw(self, s, ox, oy, t, scratch, here):
        al = self.alpha(t)
        if al <= 0:
            return
        if self.going_home is None and self.fainted is None:
            self.face()
        x, y = self.where(t, here)
        x, y = x - ox, y - oy
        if self.fainted is not None:
            y += 6 * (1 - al / 255)  # it sinks as it fades
        draw_elsewhere(s, self.a, (x, y), t, scratch, al, R=self.R)


def draw_elsewhere(s, a, at, t, scratch, alpha=255, cut=None, R=56):
    """Draw animal `a` (an apex.Prey or Perched) on `s` with its position moved to `at`
    (s's pixels): the patch of `s` round `at` is copied into `scratch` at the animal's
    real place, the animal draws itself there as usual, and the result goes back. `cut`:
    nothing below that line of `s` is drawn (sinking into a hole)."""
    px, py = a.pos()
    if a.low:
        px, py = px - OFFSET[0], py - OFFSET[1]
    dx, dy = round(at[0] - px), round(at[1] - py)
    dest = pygame.Rect(round(px) - R + dx, round(py) - R + dy, 2 * R, 2 * R)
    if cut is not None:
        dest.h = max(0, min(dest.bottom, round(cut)) - dest.top)
    dest = dest.clip(s.get_rect())
    src = dest.move(-dx, -dy).clip(scratch.get_rect())
    dest = src.move(dx, dy)
    if src.w <= 0 or src.h <= 0:
        return
    scratch.set_clip(src)
    scratch.blit(s, src.topleft, dest)
    o = a.obj
    if isinstance(a, Perched):
        o.shine(scratch, t, 12)
    else:
        for part in ("draw", "shine"):
            fn = getattr(o, part, None)
            if fn:
                fn(scratch, t)
    scratch.set_clip(None)
    piece = scratch.subsurface(src)
    if alpha < 255:
        piece = piece.copy()
        piece.set_alpha(alpha)
    s.blit(piece, dest.topleft)


class Arena:
    """The battle box. Three ways in:
    - "pick" (the moon egg): click two animals anywhere; one each, borrowed for the fight.
    - "wild" (an animal's stats card, "Battle it!"): your party (team.py) against that wild
      animal, and a glow jar to catch it with. With nobody caught yet, you click any animal
      to fight for you.
    - "tower" (the Battle Tower, tower.py): your chosen team against a trainer's six.
    It goes with him from place to place (`scene`/`lower`, kept up to date by the glade): the
    field and fighters are in whichever place he is looking at."""

    W, H = 380, 138
    PANEL_W = 262  # each side's name-and-health panel: yours on the left of the screen, its foe's on the right

    def __init__(self, scene, lower, font, t, mode="pick", foe=None, mine=None, foes=None, intro=None, after=None):
        """`foe`: (animal, species, its place) for a wild battle; `mine`: your team (team.Kept
        list); `foes`: the other side's team for the tower; `after(arena, t)`: the tower's
        buttons once a battle is over, [(label, action)]."""
        self.scene, self.lower, self.font = scene, lower, font
        self.rect = pygame.Rect(10, 540 - 10 - self.H, self.W, self.H)
        self.mode, self.foe, self.mine, self.foes, self.intro, self.after = mode, foe, mine or [], foes, intro, after
        self.phase = "pick"
        self.picked = []          # [(animal, species, the place it lives)]
        self.battle = None
        self.queue, self.log = [], []
        self.next_at = t
        self.hp = [0.0, 0.0]      # the bars, easing towards `target`
        self.target = [0, 0]
        self.status = [None, None]
        self.shown = [0, 0]       # who is out on each side, as far as the log has got
        self.hits = []            # (side, time): a glow on the animal that was hurt
        self.buttons = []         # (rect, action)
        self.menu = None          # "switch": choosing who to send in
        self.done = False
        self.t0 = t
        self.mouse = None  # the top view's pointer, set by the glade
        self.out = {}      # side -> the Fighter out on the field
        self.leavers = []  # fighters walking off (switched out) or fading (fainted)
        self.bodies = {}   # (side, place in team) -> a body made to be drawn (team.body)
        self.caught = None  # the wild animal, once it is in a jar
        self.leaving = None   # when they set off home
        self.scratch = art.solid()
        if mode == "tower" or (mode == "wild" and self.mine):
            self.start(t)

    @property
    def fighters(self):
        return list(self.out.values()) + self.leavers

    SPOTS = ((290, 26), (290, 96))  # where the board may sit, between the two panels, below the top bar

    def place(self, content):
        """Put the board where it covers none of this place's signs or icons (the first
        such spot; failing that, wherever it covers least)."""
        boards = [sp.boards[2] for sp in getattr(content, "spots", []) if getattr(sp, "boards", None)]
        if not boards:
            return
        def covered(xy):
            r = pygame.Rect(xy, (self.W, self.H))
            return sum(r.clip(b).w * r.clip(b).h for b in boards)
        best = min(self.SPOTS, key=covered)
        self.rect.topleft = best

    # --- clicks ---
    def click(self, glade, t):
        """True if the click was the battle's."""
        m = glade.top.mouse()
        cover = self.cover()
        if m and cover and cover.collidepoint(m):
            if any(sp.kind == "go" and sp.boards[2].collidepoint(m) for sp in self.paths(glade.here)):
                return False  # a path sign drawn over the box: the glade takes him there
            for r, action in self.buttons:
                if r.collidepoint(m):
                    action(t)
            return True
        if self.phase != "pick" or self.leaving is not None:
            return False
        for view, low in ((glade.top, False), (glade.bottom, True)):
            if view is None:
                continue
            m = view.mouse()
            if not m:
                continue
            hit = self.animal_at(m, low, t)
            if hit is not None:
                self.picked.append((*hit, self.scene))
                if len(self.picked) == (1 if self.mode == "wild" else 2):
                    self.start(t)
                return True
        return False

    def cover(self):
        """The part of the top screen the battle's board covers just now, if any."""
        if self.leaving is not None:
            return None
        if self.phase == "pick":
            return pygame.Rect(self.rect.x, self.rect.bottom - 48, self.rect.w, 48)
        return self.rect

    ZOOM = 1.8               # how close the top screen comes in on a battle (his ask, 2026-10-27)
    FOCUS = (485, 440)       # between the two fighters, a little above their feet
    ZOOM_TIME = 0.9          # seconds to glide in (and out)

    def camera(self, s, t):
        """The whole top screen glides in on the field for the battle and back out at its end;
        the boards are drawn afterwards, so they stay their normal size."""
        on = self.phase != "pick" and self.leaving is None
        last = getattr(self, "zoom_t", t)
        self.zoom_t = t
        step = (t - last) / self.ZOOM_TIME
        self.zoom = max(0.0, min(1.0, getattr(self, "zoom", 0.0) + (step if on else -step)))
        z = ease(self.zoom)
        if z <= 0.001:
            return
        k = 1 + (self.ZOOM - 1) * z
        w, h = round(960 / k), round(540 / k)
        cx = 480 + (self.FOCUS[0] - 480) * z
        cy = 270 + (self.FOCUS[1] - 270) * z
        view = pygame.Rect(0, 0, w, h)
        view.center = (round(cx), round(cy))
        view.clamp_ip(pygame.Rect(0, 0, 960, 540))
        s.blit(pygame.transform.scale(s.subsurface(view), (960, 540)), (0, 0))

    @property
    def zoomed(self):
        return getattr(self, "zoom", 0.0) > 0.0

    def paths(self, content):
        """The path signs the board would hide: they are drawn again on top of it."""
        cover = self.cover()
        return [sp for sp in content.spots if cover and sp.kind == "go" and getattr(sp, "boards", None)
                and sp.boards[2].colliderect(cover)]

    def animal_at(self, m, low, t):
        skip = [p[0].obj for p in self.picked] + ([self.foe[0].obj] if self.foe else [])
        return animal_under(self.scene, self.lower, m, low, t, skip=skip)

    # --- the battle ---
    def start(self, t):
        from team import ivs_of, nature_of
        own = lambda a, sp: (sp, ivs_of(a.obj), None, nature_of(a.obj))  # noqa: E731  an animal of the glade, its own self
        if self.mode == "pick":
            (a, sa, _), (b, sb, _) = self.picked
            self.battle = Battle([own(a, sa)], [own(b, sb)])
        elif self.mode == "wild":
            mine = self.mine or [own(self.picked[0][0], self.picked[0][1])]
            self.battle = Battle(mine, [own(self.foe[0], self.foe[1])], wild=True)
        else:
            self.battle = Battle(self.mine, self.foes, intro=self.intro)
        self.caught = None
        self.begin(t)

    def begin(self, t):
        a, b = self.battle.mons
        self.hp, self.target = [float(a.hp), float(b.hp)], [a.hp, b.hp]
        self.status = [None, None]
        self.phase = "fight"
        self.menu = None
        self.log, self.queue = [], []
        first = not self.out
        for side in (0, 1):
            self.send_out(side, self.battle.active[side], t)
        self.shown = list(self.battle.active)
        if first:  # they walk out onto the field, then the battle begins
            self.next_at = t + WALK
        self.feed(t)

    def restart(self, foes, intro, t):
        """The tower's next challenger: your team healed, a new team against it."""
        self.foes, self.intro = foes, intro
        self.battle = Battle(self.mine, foes, intro=intro)
        for side in (0, 1):  # whoever is out goes off; the new ones come on
            old = self.out.pop(side, None)
            if old is not None and old.fainted is None:
                old.going_home = t
                self.leavers.append(old)
        self.bodies = {}
        self.begin(t)
        self.next_at = t + WALK

    def animal(self, side, i):
        """What to draw for that side's i-th: a real animal of the glade, or a body made for it."""
        if self.mode == "pick":
            a, _, home = self.picked[side]
            return a, home
        if side == 1 and self.mode == "wild":
            return self.foe[0], self.foe[2]
        if side == 0 and self.mode == "wild" and not self.mine:
            a, _, home = self.picked[0]
            return a, home
        key = (side, i)
        if key not in self.bodies:
            from team import body
            self.bodies[key] = body(self.battle.teams[side][i].species, at=(300 + 360 * side, 260 + 40 * i))
        return self.bodies[key], None

    def send_out(self, side, i, t):
        old = self.out.get(side)
        if old is not None:
            if old.fainted is None:
                old.going_home = t
            self.leavers.append(old)
        a, home = self.animal(side, i)
        self.out[side] = Fighter(a, side, t, home)

    def leave(self, t):
        """Everyone goes home; the field fades away."""
        if self.leaving is not None:
            return
        self.leaving = t
        for f in self.fighters:
            f.going_home = t

    def finish(self):
        """Every animal back where it lives, and seen again — except one caught in a jar."""
        for f in self.fighters:
            if self.caught is not None and f.a.obj is self.caught:
                f.saved = None
                f.a.obj.gone = True
                f.a.obj.caught = True  # it lives in your boxes now (storm.py leaves it be)
            else:
                f.hide(False)
        self.out, self.leavers = {}, []

    def feed(self, t):
        self.queue.extend(self.battle.events)
        self.battle.events = []
        self.next_at = max(self.next_at, t)

    def act(self, action, t):
        if self.queue or self.battle.winner is not None:
            return
        self.menu = None
        self.battle.turn(action)
        b = self.battle
        if b.caught is not None and self.caught is None and self.foe:
            from team import Collection, Kept
            box = Collection()
            where = box.add(Kept(b.caught.species, b.caught.ivs, [m for m, _ in b.caught.moves], b.caught.nature))
            if where is not None:
                box.save()
                self.caught = self.foe[0].obj
                b.say(f"{b.caught.species} joined your party!" if where == "party" else f"{b.caught.species} was sent to {where}.")
            else:
                b.say("But your boxes are all full! It was let go.")
        self.feed(t)

    def use(self, i, t):
        self.act(i, t)

    def run(self, t):
        if self.phase == "pick" or self.battle is None or self.battle.winner is not None:
            self.leave(t)
            return
        if self.queue:
            return
        self.battle.winner = 1
        self.battle.say("You gave up the challenge." if self.mode == "tower" else "You got away safely!")
        self.feed(t)

    def again(self, t):
        self.start(t)

    # --- time passing ---
    def update(self, dt, t):
        while self.queue and t >= self.next_at:
            text, hp, st, hit, by, active = self.queue.pop(0)
            for side in (0, 1):
                if active[side] != self.shown[side]:
                    self.send_out(side, active[side], t)
                    self.shown[side] = active[side]
            self.target, self.status = list(hp), list(st)
            if by is not None and self.out:
                f = self.out.get(by if by >= 0 else -1 - by)
                if f is not None:
                    if by >= 0:
                        f.lunge = t
                    else:
                        f.fainted = t
            if text:
                self.log = (self.log + [text])[-3:]
            if hit is not None:
                self.hits.append((hit, t))
            self.next_at = t + (STEP if text else 0.45)
        for s in range(2):
            gap = self.target[s] - self.hp[s]
            self.hp[s] += gap * min(1.0, dt * 6) if abs(gap) > 0.5 else gap
        self.hits = [(s, h) for s, h in self.hits if t - h < 0.6]
        keep = []
        for f in self.leavers:  # off the field: a real animal is home and seen again
            gone = (f.fainted is not None and t - f.fainted > 1.0) or (f.going_home is not None and t - f.going_home > WALK)
            if gone and self.leaving is None:
                if f.scene is not None and f.a.obj is not self.caught and \
                        all(f.a.obj is not o.a.obj for o in self.out.values()):
                    f.hide(False)
            else:
                keep.append(f)
        self.leavers = keep
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
        cloth(s, r, tint, hot, alpha)

    def bar(self, s, x, y, w, hp, maxhp):
        f = max(0.0, min(1.0, hp / maxhp))
        c = (130, 255, 160) if f > 0.5 else (255, 220, 110) if f > 0.2 else (255, 110, 120)
        pygame.draw.rect(s, (20, 12, 30), (x, y, w, 5), border_radius=2)
        if f > 0:
            pygame.draw.rect(s, c, (x, y, max(1, round(w * f)), 5), border_radius=2)
            pygame.draw.line(s, mix(c, (255, 255, 255), 0.5), (x + 1, y + 1), (x + max(1, round(w * f)) - 2, y + 1))
        pygame.draw.rect(s, (*mix(c, EDGE, 0.3),), (x, y, w, 5), 1, border_radius=2)

    def orbs(self, s, side, x, y):
        """A glowing orb for each of that side's team: bright while it can fight, dark once down."""
        team = self.battle.teams[side]
        if len(team) < 2:
            return
        c = MINE if side == 0 else THEIRS
        for i, mon in enumerate(team):
            ox = x - i * 9
            if mon.hp > 0 or (i == self.shown[side] and self.hp[side] > 0.5):
                pygame.draw.circle(s, mix(c, (255, 255, 255), 0.3), (ox, y), 3)
                s.set_at((ox - 1, y - 1), (255, 255, 255))
            else:
                pygame.draw.circle(s, mix(c, EDGE, 0.7), (ox, y), 3, 1)

    def panel(self, s, side, x, y, w, tint):
        mon = self.battle.teams[side][self.shown[side]]
        self.cloth(s, pygame.Rect(x, y, w, 40), tint, alpha=170)
        hp = max(0, round(self.hp[side]))
        label = f"{hp}/{mon.maxhp}" if side == 0 else f"{math.ceil(100 * hp / mon.maxhp)}%"
        lw = self.text(s, label, x + w - 6, y + 3, TEXT, right=True)
        self.text(s, self.fit(f"{mon.name}  Lv100", w - 24 - lw), x + 6, y + 3, (255, 255, 255))
        self.bar(s, x + 6, y + 17, w - 12, self.hp[side], mon.maxhp)
        nx = x
        for k in mon.types:  # line two: its types and any status, and the team's orbs
            nx += self.badge(s, k, nx + 6, y + 25)
        st = self.status[side]
        if st:
            nx += self.badge(s, STATUS_TAG[st], nx + 6, y + 25)
        self.orbs(s, side, x + w - 10, y + 31)

    def draw(self, s, low, t):
        """`low`: drawing the lower screen (only animals on their way go there)."""
        if not low:
            self.field(s, t)
        ox, oy = OFFSET if low else (0, 0)
        for f in self.fighters:
            f.draw(s, ox, oy, t, self.scratch, self.scene)
            for side, h in self.hits:
                if f is self.out.get(side):
                    x, y = f.where(t, self.scene)
                    glow(s, x - ox, y - oy, 26, (255, 255, 255), q(140 * (1 - (t - h) / 0.6)))
        self.rings(s, low, t)
        if not low:
            self.camera(s, t)
        if low or self.leaving is not None:
            return
        self.buttons = []
        k = min(1.0, (t - self.t0) / 0.3)
        r = self.rect
        if self.phase == "pick":
            h = 48
            box = pygame.Rect(r.x, r.bottom - h, r.w, h)
            self.cloth(s, box, CLOTH, alpha=round(240 * k))
            if self.mode == "wild":
                line1, line2 = f"Battle the {self.foe[1]}!", "Nobody caught yet: click an animal to fight for you."
            elif not self.picked:
                line1, line2 = "BATTLE!", "Click an animal to be yours."
            else:
                line1, line2 = f"{self.picked[0][1]} is ready!", "Now click the animal it will fight."
            self.text(s, line1, box.x + 8, box.y + 7, MINE if self.picked else (255, 255, 255))
            self.text(s, self.fit(line2, box.w - 84), box.x + 8, box.y + 25)
            self.button(s, pygame.Rect(box.right - 66, box.y + 8, 58, 18), "Cancel", self.run, t)
            return
        b = self.battle
        # the two sides' panels on opposite sides of the screen, each above its own fighter
        self.cloth(s, pygame.Rect(10 - 4, 26, self.PANEL_W + 8, 48), MINE, alpha=200)
        self.panel(s, 0, 10, 30, self.PANEL_W, MINE)
        self.cloth(s, pygame.Rect(960 - 10 - self.PANEL_W - 4, 26, self.PANEL_W + 8, 48), THEIRS, alpha=200)
        self.panel(s, 1, 960 - 10 - self.PANEL_W, 30, self.PANEL_W, THEIRS)
        self.cloth(s, r, CLOTH, alpha=245)
        # the log: newest line brightest
        for i, line in enumerate(self.log):
            c = mix(DIM, TEXT, (i + 1) / len(self.log))
            self.text(s, self.fit(line, r.w - 20), r.x + 10, r.y + 6 + i * 13, c)
        busy = bool(self.queue)
        y0 = r.y + 48
        if b.winner is None:
            forced = b.need == 0
            if (self.menu == "switch" or forced) and not busy:
                self.switch_menu(s, r, y0, t, forced)
            else:
                me = b.mons[0]
                bw = (r.w - 18) // 2
                for i, (name, pp) in enumerate(me.moves):
                    m = MOVES[name]
                    br = pygame.Rect(r.x + 6 + (i % 2) * (bw + 6), y0 + (i // 2) * 34, bw, 30)
                    self.move_button(s, br, name, m, pp, not busy and pp > 0, t, i)
            x = r.right - 6
            for label, action, show in (("Give up" if self.mode == "tower" else "Run", self.run, not forced),
                                        ("Glow jar", self.throw, b.wild and not forced),
                                        ("Switch", self.open_switch, len(b.teams[0]) > 1 and not forced)):
                if show:
                    w = self.font.size(label)[0] + 12
                    x -= w
                    self.button(s, pygame.Rect(x, r.bottom - 17, w, 13), label, action, t, small=True,
                                enabled=not busy and (label != "Glow jar" or self.may_catch()),
                                gold=label == "Glow jar" and self.may_catch())
                    x -= 4
            if busy:
                self.text(s, "...", r.x + 8, r.bottom - 16, DIM)
            elif forced:
                self.text(s, "Choose who goes out next", r.x + 8, r.bottom - 16, DIM)
            elif b.wild and not self.may_catch():
                self.text(s, "Glow jars: after a Tower run", r.x + 8, r.bottom - 16, DIM)
            else:
                self.text(s, f"Turn {b.number + 1}", r.x + 8, r.bottom - 16, DIM)
        elif not busy:
            bw = (r.w - 18) // 2
            if self.mode == "tower" and self.after:
                choices = self.after(self, t)
            elif self.mode == "pick":
                choices = [("Battle again", self.again), ("Close", self.close)]
            else:
                choices = [("Close", self.close)]
            for i, (label, action) in enumerate(choices):
                w = (r.w - 12 - 6 * (len(choices) - 1)) // len(choices)
                self.button(s, pygame.Rect(r.x + 6 + i * (w + 6), y0 + 10, w, 28), label, action, t)

    def may_catch(self):
        """Catching opens up once you have done a run at the Battle Tower."""
        if not hasattr(self, "_may"):
            from team import Collection
            self._may = Collection().tried
        return self._may

    def throw(self, t):
        if self.may_catch():
            self.act(("jar",), t)

    def open_switch(self, t):
        self.menu = None if self.menu == "switch" else "switch"

    def switch_menu(self, s, r, y0, t, forced):
        """Your team, to pick who goes in: name and health; the one out and the fainted can't."""
        team = self.battle.teams[0]
        bw = (r.w - 24) // 3
        for i, mon in enumerate(team):
            br = pygame.Rect(r.x + 6 + (i % 3) * (bw + 6), y0 + (i // 3) * 34, bw, 30)
            ok = mon.hp > 0 and i != self.battle.active[0]
            hot = ok and self.hot(br)
            self.cloth(s, br, MINE if hot else mix(CLOTH, EDGE, 0.2 if ok else 0.55), hot=hot, alpha=215 if ok else 140)
            self.text(s, self.fit(mon.species, bw - 10), br.x + 5, br.y + 3, (255, 255, 255) if hot else TEXT if ok else DIM)
            self.bar(s, br.x + 5, br.y + 19, bw - 10, mon.hp, mon.maxhp)
            if ok:
                self.buttons.append((br, lambda t, i=i: self.act(("switch", i), t)))
        if not forced:
            self.button(s, pygame.Rect(r.x + 8, r.bottom - 17, 44, 13), "Back", self.open_switch, t, small=True)

    def close(self, t):
        self.leave(t)

    def fit(self, line, w):
        while self.font.size(line)[0] > w and len(line) > 4:
            line = line[:-2] + "…"
        return line

    def hot(self, r):
        m = self.mouse() if self.mouse else None
        return bool(m) and r.collidepoint(m)

    def button(self, s, r, label, action, t, small=False, enabled=True, gold=False):
        hot = enabled and self.hot(r)
        tint = (255, 214, 120) if gold else mix(CLOTH, EDGE, 0.2)
        self.cloth(s, r, MINE if hot else tint, hot=hot, alpha=210)
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
        """A soft glowing ring around each chosen animal (mint: yours, pink: its foe)."""
        if self.out:
            return
        ox, oy = OFFSET if low else (0, 0)
        chosen = list(self.picked) + ([self.foe] if self.foe else [])
        for n, (a, _, home) in enumerate(chosen):
            if a is None or home is not self.scene:
                continue
            x, y = a.pos()
            if (y >= OFFSET[1]) != low:
                continue
            x, y = x - ox, y - oy
            c = THEIRS if (self.foe and a is self.foe[0]) or n == 1 else MINE
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


# --- right-click an animal: its base stats ---------------------------------------------

def stat_color(v):
    """Showdown-style: the higher the stat, the cooler the colour."""
    return ((255, 110, 120) if v < 30 else (255, 170, 110) if v < 60 else (255, 226, 110) if v < 90
            else (150, 240, 130) if v < 120 else (110, 230, 220))


IV_AXES = ("HP", "Atk", "Def", "Spe", "SpD", "SpA")  # round the web, clockwise from the top
IV_ORDER = (0, 1, 2, 5, 4, 3)                        # where each axis's IV sits in (HP, Atk, Def, SpA, SpD, Spe)


def iv_web(s, font, ivs, centre, r, t=0.0):
    """A creature's IVs as a six-sided web: one spoke per stat, its point as far out as its
    IV (31, the best, at the rim), the shape filled in glowing mint, each number at its spoke."""
    cx, cy = centre
    ang = [-math.pi / 2 + i * math.tau / 6 for i in range(6)]
    for ring in (1.0, 0.66, 0.33):  # the guide rings
        pts = [(cx + math.cos(a) * r * ring, cy + math.sin(a) * r * ring) for a in ang]
        pygame.draw.polygon(s, mix(CLOTH, EDGE, 0.55 if ring < 1 else 0.3), pts, 1)
    for a in ang:
        pygame.draw.line(s, mix(CLOTH, EDGE, 0.55), (cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r))
    vals = [ivs[IV_ORDER[i]] for i in range(6)]
    pts = [(cx + math.cos(a) * r * max(0.06, v / 31), cy + math.sin(a) * r * max(0.06, v / 31)) for a, v in zip(ang, vals)]
    fill = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(fill, (*MINE, 90), pts)
    s.blit(fill, (0, 0))
    pygame.draw.polygon(s, mix(MINE, (255, 255, 255), 0.3), pts, 1)
    for (px, py), v in zip(pts, vals):
        s.set_at((round(px), round(py)), (255, 255, 255))
    for a, label, v in zip(ang, IV_AXES, vals):
        lx, ly = cx + math.cos(a) * (r + 16), cy + math.sin(a) * (r + 10)
        c = (255, 255, 255) if v == 31 else mix(stat_color(v * 4), TEXT, 0.3)
        img = font.render(f"{label} {v}", False, c)
        s.blit(img, img.get_rect(center=(round(lx), round(ly))))
    total = sum(ivs)
    for i, (line, c) in enumerate(((f"IVs {total} / {MAX_IVS} max", TEXT),
                                   (f"stronger than {iv_percentile(total)}%", DIM))):
        img = font.render(line, False, c)
        s.blit(img, img.get_rect(center=(round(cx), round(cy + r + 22 + i * 13))))


MAX_IVS = 31 * 6
_IV_TABLE = []


def iv_percentile(total):
    """How many creatures in a hundred have a lower IV total than this (every IV is a random
    0-31, so the totals cluster round 93)."""
    if not _IV_TABLE:
        dist = [1]
        for _ in range(6):  # the exact spread of the sum of six dice of 0-31
            new = [0] * (len(dist) + 31)
            for a, c in enumerate(dist):
                for b in range(32):
                    new[a + b] += c
            dist = new
        whole, below = sum(dist), 0
        for c in dist:
            _IV_TABLE.append(below / whole)
            below += c
    return min(99, int(_IV_TABLE[max(0, min(MAX_IVS, total))] * 100))

class Card:
    """A small board next to an animal with what it would be in a battle: its kind, types,
    ability and base stats, and a button that opens the Forest Dex at it (dex.py). Any
    other click closes it."""

    W = 200
    ROWS = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")

    WEB = 132  # the IV web's height

    def __init__(self, font, view, at, species, t, animal=None, evolves=None, ivs=None, fight=True, avoid=None):
        """`animal`: the one right-clicked; `evolves`: what it can evolve into, if anything
        (evolve.py) — then the card has an Evolve button too; `ivs`: its own IVs (team.py),
        drawn as a six-sided web; `fight`: whether it has a "Battle it!" button."""
        self.font, self.view, self.species, self.t = font, view, species, t
        self.animal, self.evolves, self.ivs = animal, evolves, ivs
        self.nature = getattr(animal, "nature", None)
        web = self.WEB + 40 if ivs else 0
        h = 8 + 16 + 16 + 14 + len(self.ROWS) * 13 + 18 + web + 24 + (22 if evolves else 0) + (22 if fight else 0)
        # beside the animal, never over it (`avoid`: where it is): right, left, above or below,
        # whichever fits on the screen without covering it
        screen = pygame.Rect(2, 2, view.w - 4, view.h - 4)
        ax, ay = round(at[0]), round(at[1])
        body = avoid or pygame.Rect(ax - 6, ay - 6, 12, 12)
        tries = [pygame.Rect(body.right + 8, ay - h // 2, self.W, h), pygame.Rect(body.x - 8 - self.W, ay - h // 2, self.W, h),
                 pygame.Rect(ax - self.W // 2, body.y - 8 - h, self.W, h), pygame.Rect(ax - self.W // 2, body.bottom + 8, self.W, h)]
        self.rect = None
        for r in tries:
            r = r.clamp(screen)
            if not r.colliderect(body):
                self.rect = r
                break
        if self.rect is None:  # no room anywhere: the side with the most of it showing
            self.rect = min((r.clamp(screen) for r in tries), key=lambda r: r.clip(body).w * r.clip(body).h)
        self.button = pygame.Rect(self.rect.x + 8, self.rect.bottom - 24, self.W - 16, 18)
        self.fight = self.button.move(0, -22) if fight else None
        self.evolve = (self.fight or self.button).move(0, -22) if evolves else None

    def text(self, s, words, x, y, color=TEXT, right=False):
        img = self.font.render(words, False, color)
        s.blit(img, (x - img.get_width() if right else x, y))
        return img.get_width()

    def fit(self, line, w):
        while self.font.size(line)[0] > w and len(line) > 4:
            line = line[:-2] + "…"
        return line

    def draw(self, s, t):
        k = ease((t - self.t) / 0.2)
        if k <= 0:
            return
        sp = SPECIES[self.species]
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        cloth(surf, surf.get_rect(), CLOTH, alpha=240)
        y = 5
        self.text(surf, self.fit(self.species, self.W - 16), 8, y, (255, 255, 255))
        y += 16
        x = 8
        for kind in sp["types"]:
            c = TYPE_COLOR.get(kind, (200, 200, 200))
            img = self.font.render(kind.upper(), False, EDGE)
            pygame.draw.rect(surf, c, (x, y, img.get_width() + 6, img.get_height() + 1), border_radius=3)
            surf.blit(img, (x + 3, y))
            x += img.get_width() + 9
        y += 16
        aw = self.text(surf, "Ability", 8, y, DIM)
        self.text(surf, self.fit(sp["ability"], self.W - 24 - aw), self.W - 8, y, TEXT, right=True)
        y += 16
        for label, v in zip(self.ROWS, sp["base"]):
            self.text(surf, label, 8, y, DIM)
            self.text(surf, str(v), 92, y, TEXT, right=True)
            bw = round(92 * min(1.0, v / 150))
            pygame.draw.rect(surf, (20, 12, 30), (100, y + 4, 92, 5), border_radius=2)
            pygame.draw.rect(surf, stat_color(v), (100, y + 4, bw, 5), border_radius=2)
            y += 13
        y += 3
        pygame.draw.line(surf, mix(CLOTH, EDGE, 0.4), (8, y - 2), (self.W - 8, y - 2))
        self.text(surf, "Total", 8, y, DIM)
        self.text(surf, str(sum(sp["base"])), 92, y, (255, 255, 255), right=True)
        if self.ivs:
            if self.nature:
                from team import nature_effect
                up, down = nature_effect(self.nature)
                short = dict(atk="Atk", spa="SpA", spd="SpD", spe="Spe", **{"def": "Def"})
                self.text(surf, "Nature", 8, y + 16, DIM)
                self.text(surf, self.fit(self.nature + (f" (+{short[up]} -{short[down]})" if up else ""), self.W - 70),
                          self.W - 8, y + 16, TEXT, right=True)
            self.text(surf, self.fit("IVs (this one's own)", self.W - 16), 8, y + 30, DIM)
            iv_web(surf, self.font, self.ivs, (self.W // 2, y + 94), 36, t)
        surf.set_alpha(round(255 * k))
        s.blit(surf, self.rect)
        mouse = getattr(self.view, "mouse", None)
        m = mouse() if mouse else None
        hot = bool(m) and self.button.collidepoint(m)
        cloth(s, self.button, MINE if hot else mix(CLOTH, EDGE, 0.2), hot=hot, alpha=round(220 * k))
        img = self.font.render("Open in Forest Dex", False, (255, 255, 255) if hot else TEXT)
        s.blit(img, img.get_rect(center=self.button.center))
        if self.fight is not None:
            locked = getattr(self, "locked", False)  # no starter yet: it says where to get one
            hot = bool(m) and self.fight.collidepoint(m) and not locked
            cloth(s, self.fight, (255, 150, 214) if hot else mix(THEIRS, EDGE, 0.55 if locked else 0.25), hot=hot,
                  alpha=round(220 * k))
            label = self.fit("Get a starter at the Tower", self.W - 16) if locked else "Battle it!"
            img = self.font.render(label, False, DIM if locked else (255, 255, 255) if hot else TEXT)
            s.blit(img, img.get_rect(center=self.fight.center))
        if self.evolve is not None:  # glowing gold: something special
            hot = bool(m) and self.evolve.collidepoint(m)
            cloth(s, self.evolve, (255, 214, 120), hot=hot, alpha=round(225 * k))
            img = self.font.render(self.fit(f"Evolve into {self.evolves}", self.W - 24), False,
                                   (255, 255, 255) if hot else (255, 240, 200))
            s.blit(img, img.get_rect(center=self.evolve.center))
