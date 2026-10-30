"""The Glade Book's words (book.py draws them). Keep them true to the game when it changes.

Each START / BATTLES topic is (title, paragraphs, pictures): pictures are species names, or
"trainer:<place>" for a trainer's figure.
"""

START = [
    ("Welcome", [
        "This is the Glade: a forest clearing where it is always night. The light comes from glowing "
        "moss, mushrooms, crystals, lanterns and fireflies, and little squid swim through the air for "
        "no reason at all.",
        "Thirty-one places lie around it, joined by paths. Creatures live in every one of them: find "
        "them, catch them, raise them, and battle the trainers, the gym leaders, the Battle Tower and, "
        "at last, the Elite 4.",
        "Pick a chapter on the ribbons above. Pointing at a picture in this book names it."],
        ["Mossprance", "Duskling", "Driftlet", "Gloamooze"]),
    ("Getting around", [
        "Click a path's name board to walk that way. The map has one rule: left always goes left, up "
        "always goes up, so you can find your way by heading.",
        "The minimap in the lower screen's corner shows every place; the one you are in glows. Point at "
        "a place to see its name, and click it to go straight there. In this book, every place and "
        "trainer has a Go there button too.",
        "The Home key takes you back to the Glade. Rest closes the game."], []),
    ("Your first creature", [
        "Walk down past the Mossy Rocks to the Battle Tower and click its door. The first time, you "
        "choose your starter, and the Tower's challenge opens.",
        "Mossprance is a moss-maned fawn of Grass that grows into a ghostly stag. Kindlet is a little "
        "Fire pangolin that becomes a molten knight of Steel. Pippalotl is a Water axolotl that grows "
        "into a river dragon. Starters are never found in the wild."],
        ["Mossprance", "Kindlet", "Pippalotl"]),
    ("Looking at animals", [
        "Right-click any animal to see its stats card: its types, its base stats, and its own IVs, drawn "
        "as a six-sided web. The card can open its Forest Dex page, or start a battle with it.",
        "Animals come and go like wild creatures do: each stays out a while, then slips away, and a new "
        "one comes out in its place. Now and then one is already evolved, and very rarely a legendary "
        "shows itself."],
        ["Glowtail", "Nimbusdrift", "Beaconwing"]),
    ("Catching", [
        "On an animal's stats card, press Battle it! to fight it with your party.",
        "Glow jars catch it. They open up once you have tried a run at the Battle Tower. The weaker it "
        "is, the likelier it stays in the jar; asleep or frozen helps a lot, and paralysed, poisoned or "
        "burned helps a little. A jar wobbles up to three times before it holds.",
        "What you catch goes into your party of six, or your boxes when the party is full."], []),
    ("Your party and boxes", [
        "Your party is the six you take into battle. Open it with the Your party board, or at the shrine "
        "by the Tower's door. There are eight boxes of thirty for the rest.",
        "Click a creature to pick it up and click a slot to put it down or swap. Pointing at one shows its "
        "full summary: stats, nature, moves and IV web. Change moves lets it learn any move its kind can."],
        []),
    ("Trainers", [
        "A cloaked trainer stands on the lower screen of every place, dressed for where they live. A gold "
        "! over the hood means they want to battle: click them.",
        "Every trainer keeps their own creatures. Beat one and they want a rematch the next day, and each "
        "time they come back a little stronger, with one more creature (up to six), and their creatures "
        "evolve as they grow.",
        "The Glade Nav, under your badge case, maps every trainer: a gold dot wants to battle. Click a dot "
        "to go there. The Trainers chapter of this book has them all."],
        ["trainer:ridge", "trainer:lava", "trainer:shore", "trainer:hollow"]),
    ("Predator vision", [
        "The golden button in the lower screen's corner turns the world grey for a few seconds, and only "
        "the animals keep their colour, outlined in gold.",
        "One with a thick, pulsing electric-blue outline has very good IVs, in the top five in a hundred. "
        "Worth catching."], []),
    ("Thunderstorm", [
        "The Thunderstorm button brings rain and lightning. Everyone in sight shelters: diggers sink into "
        "their holes, fliers fly off, fish dive. When it passes, a fresh mix of the animals who live there "
        "comes out.",
        "When a new version of the Glade is ready, a gold notice shows by the button: press Thunderstorm "
        "to load it. You come back right where you were."], []),
    ("Hiding", [
        "When a game or a film fills the screen, after a while the animals hide; when you come back they "
        "come out again, one by one. Keep animals out stops that."], []),
    ("Secrets", [
        "The moon is listening. Click it, and it shines while it listens.",
        "Some say it answers to the right word. Some say there is more than one."], []),
]

BATTLES = [
    ("The rules", [
        "Battles follow Pokemon's third generation, Gen 3 OU: up to six against six, one out at a time. "
        "Each turn you pick a move or a switch, and the foe picks its own. The faster one moves first, "
        "unless a move goes first by itself.",
        "A creature faints at 0 HP. When all of one side's creatures have fainted, the other side wins."],
        []),
    ("Moves", [
        "Each creature knows four moves. A move has a type, a power, an accuracy and a number of uses "
        "(PP). Status moves do no damage but change things: lowering stats, putting the foe to sleep, "
        "shielding with Protect, and so on.",
        "In Gen 3 a move is physical or special because of its type: Normal, Fighting, Flying, Poison, "
        "Ground, Rock, Bug, Ghost and Steel moves are physical and use Attack; the rest are special and "
        "use Sp. Atk."], []),
    ("Damage", [
        "Damage comes from the move's power, the attacker's Attack or Sp. Atk against the defender's "
        "Defense or Sp. Def, and the level.",
        "A move of the attacker's own type hits 1.5 times as hard. Type matchups multiply it by 2 (super "
        "effective), 0.5 (not very effective) or 0 (no effect); see the Types chapter.",
        "Now and then a hit is critical and does double. Some moves land critical hits more often."], []),
    ("Status", [
        "Burned: hurt each turn, and its physical hits are halved. Poisoned: hurt each turn; badly "
        "poisoned hurts more every turn. Paralysed: much slower, and sometimes can't move. Asleep: "
        "can't move for a few turns. Frozen: can't move until it thaws. Confused: may hurt itself instead.",
        "A creature holding Leftovers heals a little at the end of every turn."], []),
    ("Switching", [
        "Switch to bring in a better match. The one coming in takes the foe's move that turn, so switch "
        "to one that shrugs that move off. When one of yours faints, you choose who comes out next."], []),
    ("Levels and experience", [
        "Wild creatures are Lv5 as a first stage, Lv16 as a middle stage, Lv32 as a final one.",
        "Beating a foe gives experience to yours who faced it and are still standing. Trainers' creatures "
        "give half again as much. Catching gives none. Each line grows at its own pace."], []),
    ("Evolving", [
        "Every line has three stages. Yours evolve at Lv16 and Lv32, after the battle they reach it in. "
        "You can press Stop to keep it as it is.",
        "An evolved creature keeps its old look and grows into it, bigger and stronger."],
        ["Mossprance", "Lichenmane", "Eldermane"]),
    ("IVs, EVs and natures", [
        "IVs are each creature's own strengths, 0 to 31 in each stat, rolled once when it is born and never "
        "changing. The web on its card shows them: the bigger the web, the better.",
        "Each creature has a nature, which raises one stat a little and lowers another. EVs are the same for "
        "everyone here."], []),
    ("The Battle Tower", [
        "At the Tower's door, Begin the challenge for trainer after trainer, healed before each, until you "
        "lose. Your best streak is kept.",
        "Trainer battle is just one trainer. Tower trainers bring as many creatures as you, each matched to "
        "one of yours by strength and level, so the Tower is won by strategy and luck, not grinding. Every "
        "trainer has an ace: their last, and a little stronger."], []),
]

PLACES = dict(
    glade="Home, in the middle of everything. The blossom tree glows with fruit, the old signpost points every "
          "way, and koi-bright lilyfin swim in the lily pond on the lower screen.",
    waterfall="A tall fall pours into a glowing pool, its cliff hung with vines. A crystal-lit cave mouth leads "
              "up to the Caverns, and a path runs right to the Starfall Meadow.",
    river="A slow, wide river with a little boat moored on it. Lilyfin swim under the water, and a path follows "
          "the bank down to the Misty Bog.",
    forest="Tall dark trees hung with glowing vines and moss. Paths lead deeper: left to the snow, down to the "
           "mushrooms, up to the old ruins.",
    rocks="Mossy boulders and standing stones, soft with glowing moss. The Battle Tower stands further down.",
    ridge="Pines in deep snow, a frozen lake, and the aurora rippling overhead. Its animals live nowhere warmer.",
    springs="A sleeping volcano above terraces of steaming turquoise pools. Embers drift up into the dark.",
    tower="The Battle Tower: trainer after trainer, for as long as you can last. Your first starter waits here.",
    caverns="A cave full of glowing crystals around a still, dark pool. Steps climb up to a crack of starlight.",
    meadow="Wide soft grass where stars fall all night long. The Comet Crater is up the hill.",
    hollow="Giant glowing mushrooms, tall as trees, with smaller ones lighting the grass.",
    bog="Misty water, dead silver trees and drifting will-o'-wisps. Lanterns mark the way across.",
    ruins="Broken pillars and an old stone arch from people long gone. Through the arch lies a moonlit garden.",
    bridge="A rope bridge strung across the clouds between two cliffs. Stepping stones float up to the isles.",
    shore="A beach of glowing sand by a dark, sparkling sea. Paths lead to a lighthouse, a grotto and under the sea.",
    falls="A whole waterfall frozen in mid-fall, glowing blue from within. Crystals of ice grow in the grass.",
    peak="Tall stones standing under the brightest aurora in the glade.",
    gully="A deep green gully thick with ferns. A dark wood of brambles lies beyond.",
    orchard="Rows of fruit trees hung with little lanterns, warm and gold.",
    temple="An old temple half sunk in the water, its steps going down into the green.",
    dunes="Pale sand dunes under a huge moon, with glowing cacti and the odd half-buried stone.",
    lava="A lake of glowing lava under a dark cliff. The air shimmers with heat.",
    grotto="A sea cave with coral trees round a glowing pool, and a window of night sky in its roof.",
    kelp="Under the sea, among tall swaying kelp, with light falling from far above.",
    lighthouse="A striped lighthouse on a grassy headland, its beam sweeping the dark sea.",
    comet="A crater where a comet fell. Its heart still glows, ringed with crystals.",
    garden="A walled garden of moonflowers around a fountain.",
    isles="Little islands float in the night sky. A stair of moonlight climbs to the Moonlit Hall.",
    storm="Jagged iron-dark peaks under clouds that never stop flashing.",
    thorn="A dark wood of brambles and bright berries, where the thorns glow.",
    hall="The Moonlit Hall, pale stone and glass at the top of the world. The Elite 4 wait behind its gold door.",
)

TYPES = {
    "Normal": "Plain and steady. Nothing is weak to it, and only Fighting hits it hard.",
    "Fire": "Embers, lava and lanterns. Burns through Grass, Ice, Bug and Steel.",
    "Water": "Pools, rivers and the sea. Puts out Fire and wears down Rock and Ground.",
    "Electric": "Sparks and storms. Strikes Water and Flying, but Ground swallows it whole.",
    "Grass": "Moss, ferns and flowers. Drinks up Water and roots into Rock and Ground.",
    "Ice": "Snow, frost and frozen falls. Freezes Dragon, Flying, Grass and Ground.",
    "Fighting": "Strength and skill. Breaks Normal, Rock, Ice, Steel and Dark.",
    "Poison": "Bogs, spores and stings. Withers Grass; Steel cannot be poisoned.",
    "Ground": "Sand, earth and digging. Topples Fire, Electric, Rock, Poison and Steel.",
    "Flying": "Wings and wind. Above Ground's reach, and quick against Grass, Bug and Fighting.",
    "Psychic": "Dreams and starlight. Outwits Fighting and Poison, but Dark is a blind spot.",
    "Bug": "Small, many and quick. Good against Grass, Psychic and Dark.",
    "Rock": "Stone and crystal. Knocks down Fire, Ice, Flying and Bug.",
    "Ghost": "Spirits and shadows. Normal and Fighting pass right through it.",
    "Dragon": "Old and strong. Only Ice and other Dragons hit it hard.",
    "Dark": "Night and cunning. Psychic can't touch it, and it preys on Ghost.",
    "Steel": "Metal and armour. Shrugs off almost everything, but Fire, Fighting and Ground get through.",
}

LEADERS = dict(
    glade="The first to welcome anyone new, and the hardest to rattle. Keeps a little of everything, like the Glade.",
    waterfall="Trains under the falling water every night; the cold keeps the mind sharp.",
    meadow="Reads the falling stars and swears each battle is already written in them.",
    hollow="Knows every mushroom in the hollow by name, the poisonous ones best of all.",
    bog="Lives on a raft in the mist and never seems to need sleep.",
    ruins="An old scholar of the ruins who battles the way stones wear down: slowly, completely.",
    bridge="Crosses the rope bridge on its handrail for fun, and fights with fists and feathers.",
    shore="Collects glowing shells and the patience of the tide.",
    falls="Climbs the frozen falls before dawn, and fights as cold as the ice.",
    peak="Says the aurora is full of spirits, and battles with them.",
    orchard="Lights every lantern in the orchard by hand, every night.",
    dunes="Crosses the dunes by moonlight and never leaves a footprint.",
    lava="Swims in the lava lake's heat haze; the only thing hotter is the temper.",
    grotto="Dives for coral and comes back up with stranger things.",
    kelp="Has lived among the kelp so long that the eels follow like pets.",
    lighthouse="Keeps the lamp burning and sees every challenger coming from miles away.",
    comet="Saw the comet fall and has guarded the crater ever since.",
    garden="Tends the moonflowers, and the shadows that grow between them.",
    forest="Has walked every path in the forest and battles like the trees grow: patient, then all at once.",
    river="Poles a boat up and down the river and reads the current like a book.",
    rocks="Built the standing stones, they say, one at a time.",
    springs="Bathes in the hottest pool and laughs at the steam.",
    ridge="Herds the snow creatures across the ridge and fears no cold.",
    storm="Climbs the peaks in the worst weather to catch lightning in a jar.",
    temple="Haunts the sunken temple; nobody has seen the face under the hood.",
    isles="Hops between the floating isles as if gravity were a suggestion.",
    thorn="Walks the bramble wood at night and knows every hidden path.",
    gully="Knows the name of every bug in the gully, and they know theirs.",
    caverns="Polishes the crystals of the caverns until they ring.",
)

TRAINERS = dict(
    glade="Sweeps fallen blossom from the paths and dreams of being a gym leader one day.",
    waterfall="Dives off the top of the waterfall to show off. Every time.",
    river="Poles a raft of reeds and talks to the lilyfin.",
    forest="Keeps watch over the forest paths and never gets lost.",
    rocks="Mends the standing stones and carves runes into the moss.",
    ridge="Herds the fluffy snow creatures home before the aurora fades.",
    springs="Knows which pools are warm and which will cook an egg.",
    caverns="Maps the crystal caves by the sound they make when tapped.",
    meadow="Catches falling stars in a net; never has, yet.",
    hollow="Gathers glowing spores in little jars and trades them for stories.",
    bog="Wades the bog in tall boots and follows the will-o'-wisps on purpose.",
    ruins="Can read half the runes on the old stones, and guesses the rest.",
    bridge="Walks the clouds and hates going back down.",
    shore="Combs the glowing sand for shells after every tide.",
    falls="Climbs the frozen fall with two ice picks and no fear.",
    peak="Counts the colours in the aurora every night.",
    gully="Forages ferns for soup; nobody has dared try it.",
    orchard="Picks fruit by lantern light and always shares.",
    temple="Dives for the temple's lost treasures, and keeps finding creatures instead.",
    dunes="Crosses the dunes by the moon's light alone.",
    lava="Meditates on the warm rocks by the lava lake; very hard to annoy.",
    grotto="Swims with the coral creatures and comes up pink with glow.",
    kelp="Explores the deep with a lantern that never goes out.",
    lighthouse="Keeps the lighthouse lamp clean and challenges every passer-by.",
    comet="Chases every falling star, sure the next comet is coming soon.",
    garden="Plants moonflowers that only open when someone is battling nearby.",
    isles="Walks from isle to isle and never looks down.",
    storm="Calls the lightning down for fun, and sometimes it comes.",
    thorn="Lives in the brambles and knows which berries are safe.",
)
