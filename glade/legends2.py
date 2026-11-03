"""Twelve more legendaries (2026-11-03, his ask: "add 12 legendaries within the legendary stat
range, none should evolve, remember all the rules"; he approved Claude's designs). One for each
of twelve places that had none. His rules: totals 570-615 (only the cover legendaries,
Elderglow and Moonward, are 700), they never evolve, the stronger the rarer (storm.rare), no
humanoids, nothing borrowed from Pokémon's cover legendaries, one-word names with no real
animal in them, a type that fits what it is, and a height under Dragonite's 7'03".

Each row: kind, name, home place, types, base stats, ability, moves, height (ft), flies?,
body colour, glow colour, speed, its Forest Dex story. Numbered #449-#460 (battle.py); drawn
in wave10.py.
"""

LEGENDS2 = [
    ("veilf", "Veilfall", "waterfall", ("Water", "Rock"), (110, 95, 125, 95, 110, 60), "Swift Swim",
     ["Surf", "Hydro Pump", "Waterfall", "Rock Slide", "Ancient Power", "Ice Beam", "Calm Mind", "Recover",
      "Iron Defense", "Rest"], 6.8, True, (96, 128, 150), (150, 230, 255), 8,
     "A veil of falling water that never reaches the ground, wrapped round a mossy stone heart. The "
     "Waterfall is said to be its breath."),
    ("rimeh", "Rimeheart", "ridge", ("Ice", "Psychic"), (90, 70, 95, 130, 120, 105), "Levitate",
     ["Ice Beam", "Psychic", "Aurora Beam", "Calm Mind", "Recover", "Icy Wind", "Haze", "Shadow Ball",
      "Thunderbolt", "Hypnosis"], 5.5, True, (210, 230, 255), (170, 255, 230), 10,
     "A snowflake as wide as a sledge, turning so slowly you could miss it. The aurora is the light "
     "it leaves behind."),
    ("calde", "Calderon", "springs", ("Fire", "Ground"), (105, 120, 110, 95, 80, 65), "Flash Fire",
     ["Flamethrower", "Earthquake", "Heat Wave", "Rock Slide", "Fire Punch", "Will-O-Wisp", "Iron Defense",
      "Mud Shot", "Body Slam", "Morning Sun"], 5.2, False, (92, 72, 82), (255, 140, 60), 4,
     "A little volcano that got up and walked. The Hot Springs stay warm wherever it has slept."),
    ("prism", "Prismcore", "caverns", ("Rock", "Electric"), (85, 90, 120, 115, 95, 85), "Sturdy",
     ["Thunderbolt", "Rock Slide", "Ancient Power", "Shock Wave", "Thunder Wave", "Iron Defense", "Rock Tomb",
      "Flash", "Rest", "Spark"], 4.6, True, (110, 100, 140), (200, 180, 255), 6,
     "A geode that floats through the Caverns. When it opens, its crystals crackle and every other "
     "crystal in the cave lights up to answer."),
    ("wispm", "Wispmire", "bog", ("Poison", "Ghost"), (95, 75, 85, 120, 105, 105), "Poison Point",
     ["Sludge Bomb", "Shadow Ball", "Toxic", "Confuse Ray", "Will-O-Wisp", "Pain Split", "Giga Drain",
      "Night Shade", "Haze", "Hypnosis"], 6.1, False, (62, 72, 62), (180, 255, 120), 5,
     "The marsh-light every traveller follows and none catch. It walks the Bog on stilts of root, "
     "its lantern swinging."),
    ("runet", "Runetome", "ruins", ("Psychic", "Steel"), (90, 70, 120, 120, 115, 65), "Levitate",
     ["Psychic", "Meteor Mash", "Calm Mind", "Iron Defense", "Shadow Ball", "Ancient Power", "Confusion",
      "Recover", "Thunder Wave", "Psybeam"], 4.0, True, (170, 130, 90), (150, 230, 255), 6,
     "A book of stone bound in bronze, older than the Ruins. Its runes leave the page and circle it "
     "when it reads you."),
    ("cloom", "Cloudloom", "bridge", ("Flying", "Normal"), (100, 80, 90, 110, 100, 120), "Keen Eye",
     ["Aerial Ace", "Air Cutter", "Return", "Body Slam", "Ice Beam", "Thunderbolt", "Recover", "Double Team",
      "Agility", "Gust"], 6.0, True, (226, 226, 244), (220, 230, 255), 14,
     "It weaves the clouds the Bridge is made of. A thread from its loom will hold a mountain."),
    ("tides", "Tidespindle", "shore", ("Water", "Electric"), (90, 85, 90, 125, 95, 115), "Static",
     ["Surf", "Thunderbolt", "Hydro Pump", "Spark", "Water Pulse", "Thunder Wave", "Ice Beam", "Recover",
      "Agility", "Shock Wave"], 5.8, True, (60, 110, 150), (120, 255, 240), 16,
     "A spinning whirl of the sea, full of glowing plankton. It winds the tides in and out like thread."),
    ("harve", "Harvestglow", "orchard", ("Grass", "Fire"), (105, 100, 95, 110, 100, 70), "Effect Spore",
     ["Giga Drain", "Flamethrower", "Leech Seed", "Synthesis", "Sleep Powder", "Heat Wave", "Magical Leaf",
      "Will-O-Wisp", "Fire Punch", "Return"], 4.8, True, (230, 150, 80), (255, 210, 120), 6,
     "The first lantern of the Orchard, a great fruit with a fire inside. Every seed it drops grows "
     "into a lantern tree."),
    ("hourd", "Hourdune", "dunes", ("Ground", "Psychic"), (100, 85, 115, 110, 110, 90), "Levitate",
     ["Earthquake", "Psychic", "Sand-Attack", "Calm Mind", "Rest", "Mud Shot", "Ancient Power", "Shadow Ball",
      "Haze", "Agility"], 6.5, True, (200, 180, 150), (220, 200, 255), 6,
     "A giant hourglass of moon-sand that turns itself over each night. The Dunes are the sand it "
     "has spilled."),
    ("anvil", "Anvilstorm", "storm", ("Electric", "Steel"), (95, 120, 120, 105, 85, 90), "Sturdy",
     ["Thunderbolt", "Meteor Mash", "Iron Tail", "Spark", "Iron Defense", "Thunder Wave", "Earthquake",
      "Shock Wave", "Brick Break", "Swords Dance"], 6.9, True, (80, 84, 110), (250, 250, 150), 10,
     "An iron anvil inside a thundercloud. Every strike of lightning on the Peaks is it being struck, "
     "and it rings for miles."),
    ("thornh", "Thornheart", "thorn", ("Grass", "Dark"), (95, 115, 100, 90, 95, 85), "Inner Focus",
     ["Giga Drain", "Crunch", "Leech Seed", "Faint Attack", "Sleep Powder", "Swords Dance", "Magical Leaf",
      "Bite", "Synthesis", "Toxic"], 4.4, True, (44, 32, 52), (255, 70, 110), 6,
     "A crown of black thorns round a single red rose. The Thornwood grew up to guard it."),
    # one more (2026-11-03, his pick of three): #461
    ("comef", "Cometfall", "comet", ("Dragon", "Rock"), (100, 120, 115, 100, 85, 85), "Rock Head",
     ["Dragon Claw", "Rock Slide", "Ancient Power", "Dragon Dance", "Earthquake", "Flamethrower", "Twister",
      "Dragon Breath", "Iron Defense", "Meteor Mash"], 6.7, True, (96, 88, 110), (255, 200, 140), 12,
     "The comet that made the Crater, still tumbling. Deep inside the stone a dragon's eye watches, "
     "waiting for the sky to call it home."),
]

FIRST_NUM = 449  # #449-#461; Elderglow and Moonward stay at the very end
