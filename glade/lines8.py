"""The 50 new lines of 2026-10-27 (his ask): two for each of the fifteen far places (kit.py,
faraway2-4.py) and twenty more spread over every place by theme. Typing was chosen to even out
the Dex: before them Dragon had 4 lines and Water 20; after, every type has 13-23.

Each row: kind, (first, middle, final), types, stat shape, final height (ft), flies?, body colour,
glow colour, speed, home. Stats, moves and heights are filled in from this by battle.py and
evolve.py; the drawing is in wave8.py.
"""

LINES = [
    # round one
    ("hoar", ("Hoarlet", "Hoarcoil", "Hoarcascade"), ("Ice", "Dragon"), (90, 95, 85, 95, 85, 80), 6.4, False, (170, 220, 250), (180, 240, 255), 10, "falls"),
    ("chill", ("Chillbell", "Chillchime", "Chillcarillon"), ("Ice", "Steel"), (70, 60, 110, 95, 100, 65), 3.9, True, (200, 226, 250), (210, 240, 255), 18, "falls"),
    ("veil", ("Veilet", "Veilshimmer", "Veilcrown"), ("Ice", "Ghost"), (70, 55, 70, 110, 105, 100), 5.6, True, (150, 255, 210), (160, 255, 220), 24, "peak"),
    ("bast", ("Bastlet", "Bastwall", "Bastionhold"), ("Fighting", "Steel"), (95, 120, 120, 40, 70, 55), 5.9, False, (130, 130, 160), (150, 230, 255), 5, "peak"),
    ("fiddle", ("Fiddlet", "Fiddlecoil", "Fiddlegrove"), ("Grass", "Poison"), (75, 90, 80, 95, 80, 80), 4.5, False, (110, 190, 120), (190, 255, 140), 12, "gully"),
    ("glid", ("Glidlet", "Glidrill", "Glidrapid"), ("Electric", "Bug"), (60, 70, 65, 100, 70, 135), 2.6, False, (90, 130, 170), (250, 250, 140), 40, "gully"),
    ("lamp", ("Lampip", "Lampfruit", "Lampbough"), ("Fire", "Grass"), (85, 70, 75, 100, 85, 85), 4.0, False, (250, 170, 110), (255, 200, 120), 12, "orchard"),
    ("rind", ("Rindle", "Rindshell", "Rindfort"), ("Grass", "Steel"), (100, 95, 120, 45, 80, 40), 4.7, False, (200, 190, 110), (255, 240, 160), 7, "orchard"),
    ("mask", ("Masklet", "Maskdrift", "Maskoracle"), ("Ghost", "Water"), (75, 65, 90, 105, 110, 55), 5.2, True, (150, 180, 170), (110, 230, 190), 12, "temple"),
    ("wyrm", ("Wyrmlet", "Wyrmcoil", "Wyrmshrine"), ("Dragon", "Dark"), (90, 110, 90, 80, 80, 90), 6.9, False, (80, 170, 140), (110, 255, 190), 9, "temple"),
    # round two
    ("dune", ("Dunelet", "Dunedrift", "Dunewraith"), ("Ground", "Ghost"), (90, 90, 95, 80, 80, 65), 5.0, False, (220, 190, 180), (200, 170, 255), 8, "dunes"),
    ("prickle", ("Pricklet", "Pricklejab", "Prickleking"), ("Grass", "Fighting"), (85, 115, 85, 60, 70, 85), 4.8, False, (110, 180, 140), (140, 255, 200), 10, "dunes"),
    ("cinder", ("Cinderlet", "Cindercrawl", "Cindermaw"), ("Fire", "Dragon"), (85, 110, 85, 100, 75, 85), 6.6, False, (90, 60, 70), (255, 140, 70), 9, "lava"),
    ("slag", ("Slaglet", "Slagshell", "Slagbastion"), ("Steel", "Fire"), (100, 85, 120, 80, 85, 30), 5.1, False, (80, 76, 90), (255, 150, 80), 4, "lava"),
    ("coral", ("Coralet", "Coralbloom", "Coralspire"), ("Poison", "Water"), (85, 70, 95, 95, 95, 60), 4.6, False, (255, 140, 170), (255, 170, 200), 5, "grotto"),
    ("pearl", ("Pearlet", "Pearlnight", "Pearlnoir"), ("Water", "Dark"), (75, 95, 110, 75, 95, 70), 3.6, False, (170, 150, 190), (200, 180, 255), 6, "grotto"),
    ("kelp", ("Kelplet", "Kelpcoil", "Kelpleviathan"), ("Grass", "Water"), (90, 85, 85, 95, 90, 85), 6.8, True, (80, 160, 110), (120, 240, 200), 16, "kelp"),
    ("lure", ("Lurelet", "Lurelamp", "Lureabyss"), ("Water", "Electric"), (70, 95, 65, 95, 65, 110), 4.2, True, (40, 50, 80), (120, 255, 240), 14, "kelp"),
    ("lens", ("Lenslet", "Lensflare", "Lensbeacon"), ("Electric", "Normal"), (75, 55, 80, 115, 85, 90), 4.4, False, (190, 220, 230), (255, 240, 190), 10, "lighthouse"),
    ("gust", ("Gustlet", "Gustcurl", "Gustgale"), ("Normal", "Flying"), (80, 85, 70, 70, 70, 125), 4.1, True, (230, 230, 245), (220, 240, 255), 60, "lighthouse"),
    # round three
    ("crater", ("Craterlet", "Cratermaw", "Craterhulk"), ("Ground", "Steel"), (95, 105, 115, 50, 70, 65), 5.7, False, (110, 104, 130), (180, 220, 255), 6, "comet"),
    ("nova", ("Novalet", "Novaflare", "Novaburst"), ("Ice", "Electric"), (65, 60, 70, 115, 80, 120), 3.8, True, (200, 230, 255), (180, 220, 255), 50, "comet"),
    ("wilt", ("Wiltlet", "Wiltbloom", "Wiltwraith"), ("Ghost", "Grass"), (75, 70, 75, 105, 105, 80), 4.9, True, (220, 220, 245), (240, 236, 255), 14, "garden"),
    ("spout", ("Spoutlet", "Spoutfount", "Spoutcascade"), ("Water", "Rock"), (105, 75, 95, 85, 90, 55), 4.3, False, (170, 166, 200), (150, 220, 255), 6, "garden"),
    ("clod", ("Clodlet", "Clodfloat", "Clodcontinent"), ("Ground", "Psychic"), (95, 85, 100, 95, 95, 40), 6.1, True, (140, 110, 100), (140, 255, 190), 8, "isles"),
    ("zeph", ("Zephlet", "Zephwing", "Zephyrion"), ("Dragon", "Flying"), (80, 100, 75, 95, 75, 115), 7.0, True, (200, 190, 255), (220, 210, 255), 70, "isles"),
    ("bolt", ("Boltlet", "Boltcoil", "Boltstrider"), ("Electric", "Dragon"), (75, 110, 75, 100, 70, 110), 6.2, False, (230, 220, 110), (250, 250, 140), 18, "storm"),
    ("thrum", ("Thrumlet", "Thrumcloud", "Thrumtempest"), ("Electric", "Dark"), (90, 95, 80, 80, 85, 80), 5.5, True, (60, 60, 90), (250, 250, 160), 20, "storm"),
    ("bane", ("Banelet", "Baneberry", "Banebramble"), ("Grass", "Poison"), (80, 85, 75, 95, 80, 85), 4.4, False, (60, 40, 70), (255, 80, 140), 8, "thorn"),
    ("shroud", ("Shroudlet", "Shroudweb", "Shroudweaver"), ("Bug", "Ghost"), (65, 90, 70, 95, 80, 110), 4.8, False, (50, 40, 70), (190, 110, 255), 20, "thorn"),
    # twenty more, spread over every place by theme
    ("clove", ("Clovelet", "Clovebrawl", "Clovechamp"), ("Grass", "Fighting"), (90, 110, 75, 50, 70, 105), 4.0, False, (110, 200, 130), (190, 255, 160), 24, "glade"),
    ("glaze", ("Glazelet", "Glazebash", "Glazebreaker"), ("Ice", "Fighting"), (90, 120, 95, 45, 70, 80), 5.4, False, (150, 200, 230), (190, 240, 255), 10, "waterfall"),
    ("dart", ("Dartlet", "Dartwing", "Dartblaze"), ("Bug", "Fire"), (65, 95, 60, 90, 60, 130), 3.5, True, (230, 130, 90), (255, 170, 90), 90, "river"),
    ("whisp", ("Whisplet", "Whispbark", "Whispelder"), ("Ghost", "Normal"), (90, 70, 80, 95, 95, 70), 5.3, True, (130, 100, 110), (170, 255, 200), 12, "forest"),
    ("flint", ("Flintlet", "Flintknock", "Flintcolossus"), ("Rock", "Fighting"), (90, 120, 110, 45, 65, 70), 6.0, False, (100, 96, 120), (255, 220, 150), 6, "rocks"),
    ("slush", ("Slushlet", "Slushmound", "Slushavalanche"), ("Ice", "Ground"), (110, 95, 95, 70, 80, 50), 5.8, False, (190, 200, 220), (200, 240, 255), 5, "ridge"),
    ("kiln", ("Kilnlet", "Kilnbake", "Kilnoracle"), ("Fire", "Psychic"), (80, 60, 95, 115, 100, 50), 4.6, False, (190, 110, 90), (255, 160, 90), 6, "springs"),
    ("thump", ("Thumplet", "Thumpbag", "Thumpchampion"), ("Fighting", "Dark"), (110, 115, 90, 45, 70, 70), 5.6, False, (150, 120, 110), (255, 200, 150), 10, "tower"),
    ("ooz", ("Oozite", "Oozestone", "Oozemonolith"), ("Poison", "Rock"), (90, 90, 115, 85, 80, 40), 6.3, False, (90, 80, 110), (170, 255, 120), 4, "caverns"),
    ("dande", ("Dandelet", "Dandeplume", "Dandedream"), ("Grass", "Flying"), (70, 55, 65, 110, 100, 100), 3.4, True, (240, 240, 230), (255, 250, 200), 14, "meadow"),
    ("cap", ("Caplet", "Capcluster", "Capcolony"), ("Grass", "Bug"), (80, 90, 95, 80, 85, 70), 3.7, False, (200, 90, 150), (255, 140, 210), 16, "hollow"),
    ("slough", ("Sloughlet", "Sloughcrawl", "Sloughmonarch"), ("Dragon", "Poison"), (95, 100, 90, 90, 80, 75), 6.7, False, (80, 110, 80), (170, 255, 140), 8, "bog"),
    ("gear", ("Gearlet", "Gearwork", "Gearcolossus"), ("Steel", "Ghost"), (70, 80, 120, 90, 100, 60), 5.0, True, (170, 150, 110), (150, 230, 255), 8, "ruins"),
    ("lurk", ("Lurklet", "Lurklog", "Lurkhulk"), ("Water", "Dark"), (85, 105, 80, 60, 70, 100), 4.9, False, (130, 110, 100), (255, 220, 140), 9, "shore"),
    ("mud", ("Mudlet", "Mudmound", "Mudcastle"), ("Ground", "Dark"), (95, 100, 100, 60, 80, 65), 5.2, False, (110, 80, 70), (200, 160, 255), 6, "gully"),
    ("zest", ("Zestlet", "Zestbolt", "Zestdynamo"), ("Grass", "Electric"), (70, 80, 70, 105, 75, 100), 3.9, False, (250, 220, 90), (255, 250, 140), 16, "orchard"),
    ("wail", ("Waillet", "Wailfrost", "Wailglacier"), ("Ghost", "Ice"), (70, 65, 85, 110, 100, 70), 5.5, True, (200, 230, 250), (180, 230, 255), 10, "falls"),
    ("grit", ("Gritlet", "Gritcrest", "Gritsovereign"), ("Dragon", "Ground"), (100, 110, 95, 70, 75, 80), 6.9, False, (210, 170, 140), (255, 210, 150), 10, "dunes"),
    ("astral", ("Astralet", "Astralcoil", "Astralsovereign"), ("Dragon", "Electric"), (80, 95, 75, 110, 80, 110), 6.5, True, (60, 60, 120), (200, 220, 255), 26, "comet"),
    ("buoy", ("Buoylet", "Buoyjolt", "Buoybeacon"), ("Water", "Steel"), (90, 105, 90, 80, 75, 70), 4.5, False, (240, 120, 120), (255, 240, 170), 5, "lighthouse"),
]

ABILITY = {"Normal": "Run Away", "Fire": "Flash Fire", "Water": "Swift Swim", "Grass": "Effect Spore",
           "Electric": "Static", "Ice": "Thick Fat", "Fighting": "Guts", "Poison": "Poison Point", "Ground": "Sturdy",
           "Flying": "Keen Eye", "Psychic": "Levitate", "Bug": "Shield Dust", "Rock": "Rock Head", "Ghost": "Levitate",
           "Dragon": "Inner Focus", "Dark": "Inner Focus", "Steel": "Shell Armor"}


def pool(types, moves):
    """Nine moves for a line from the moves its types have: the weaker first (stage one gets six),
    then two stronger, then the strongest. Flying lines get a Flying move even if it is second."""
    by = {}
    for name, m in moves.items():
        by.setdefault(m["t"], []).append((m["p"], name))
    hits = [sorted(n for n in by.get(t, []) if n[0] > 0) for t in types]
    status = [n for t in types for p, n in sorted(by.get(t, [])) if p == 0][:2]
    a, b = hits[0], hits[1] if len(hits) > 1 else []
    first = [a[0][1]] + ([b[0][1]] if b else []) + ["Quick Attack"] + status[:1] + ["Protect"]
    first += [a[min(1, len(a) - 1)][1]] if len(first) < 6 else []
    first = list(dict.fromkeys(first + ["Headbutt", "Double Team"]))[:6]
    middle = [a[len(a) // 2][1], (b[len(b) // 2][1] if b else "Body Slam")] + status[1:2]
    final = [a[-1][1]] + ([b[-1][1]] if b else ["Return"])
    out = list(dict.fromkeys(first + middle + final))
    return out[:6] + out[6:8] + out[8:]
