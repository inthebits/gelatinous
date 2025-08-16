"""
Weather Message Pools

Contains atmospheric descriptions for different weather types and times of day.
Messages are designed to synergize when combined with comma separation.
"""

# Weather intensity levels for message length/impact
WEATHER_INTENSITY = {
    # Mild weather (short, subtle messages)
    'clear': 'mild',
    'overcast': 'mild', 
    'windy': 'mild',
    
    # Moderate weather
    'fog': 'moderate',
    'rain': 'moderate',
    'soft_snow': 'moderate',
    'foggy_rain': 'moderate',
    'light_rain': 'moderate',
    
    # Intense weather (longer, attention-grabbing messages)
    'dry_thunderstorm': 'intense',
    'rainy_thunderstorm': 'intense',
    'hard_snow': 'intense',
    'blizzard': 'intense',
    'gray_pall': 'intense',
    'tox_rain': 'intense',
    'sandstorm': 'intense',
    'blind_fog': 'intense',
    'heavy_fog': 'intense',
    
    # Extreme weather (epic messages that demand attention)
    'flashstorm': 'extreme',
    'torrential_rain': 'extreme',
}

# Regional weather message pools
# Future expansion: multiple regions like 'mars_desert', 'orbital_station', etc.
WEATHER_MESSAGES = {
    'default': {
        # Clear weather variations by time of day (mild intensity)
        'clear_pre_dawn': {
            'visual': [
                "darkness holds dominion with hints of approaching light",
                "scattered lights pierce the deep shadows like stars",
                "the sky remains black velvet above"
            ],
            'auditory': [
                "silence broken only by distant mechanical whispers",
                "the world sleeps in hushed anticipation",
                "sporadic sounds echo in the stillness"
            ],
            'olfactory': [
                "cool air carries the scent of dew and night",
                "fresh moisture mingles with lingering traces",
                "the smell of dawn approaches on quiet winds"
            ],
            'atmospheric': [
                "the pre-dawn stillness feels heavy with potential",
                "expectant air holds its breath before sunrise",
                "there's a sense of worlds about to change"
            ]
        },
        
        'clear_dawn': {
            'visual': [
                "pale light filters through the awakening atmosphere",
                "long shadows stretch like fingers across surfaces",
                "the sky lightens to pearl and amber"
            ],
            'auditory': [
                "distant sounds begin their morning chorus",
                "the world awakens with scattered whispers of activity",
                "crisp air carries the echo of new beginnings"
            ],
            'olfactory': [
                "cool morning air carries hints of warming earth",
                "the scent of heated surfaces begins to rise",
                "faint aromas drift on the morning breeze"
            ],
            'atmospheric': [
                "the air feels clean despite surrounding complexity",
                "morning calm settles over everything like a blessing",
                "the day ahead pulses with hidden possibilities"
            ]
        },
        
        'clear_early_morning': {
            'visual': [
                "golden sunlight slants through the atmosphere",
                "harsh light glints off every reflective surface",
                "morning shadows create geometric patterns everywhere"
            ],
            'auditory': [
                "activity hums with increasing intensity around you",
                "engines warm and machinery comes to life",
                "the steady background noise of life grows stronger"
            ],
            'olfactory': [
                "warming surfaces release their stored scents",
                "exhaust and heated metal fill the air",
                "morning aromas mix in complex combinations"
            ],
            'atmospheric': [
                "the morning energy feels charged and electric",
                "visibility stretches sharp and clear in all directions",
                "everything feels alert and watchful around you"
            ]
        },
        
        'clear_late_morning': {
            'visual': [
                "bright sun climbs higher, shortening shadows",
                "everything basks in full daylight clarity",
                "peak activity unfolds under cloudless skies"
            ],
            'auditory': [
                "late morning brings energetic sounds and motion",
                "construction, traffic, and life create lively soundscapes",
                "productivity hums with forward momentum everywhere"
            ],
            'olfactory': [
                "warming surfaces begin releasing their heat",
                "food vendors and kitchens add rich aromas",
                "morning freshness mixes with heated air"
            ],
            'atmospheric': [
                "late morning feels dynamic and purposeful",
                "energetic quality fills the warming atmosphere",
                "productivity and ambition charge the air"
            ]
        },
        
        'clear_midday': {
            'visual': [
                "harsh sun beats down mercilessly",
                "heat shimmer rises from every baked surface",
                "shadows shrink to sharp, minimal lines"
            ],
            'auditory': [
                "everything thrums with peak activity and motion",
                "cooling systems hum and rattle desperately",
                "background noise forms a steady symphony"
            ],
            'olfactory': [
                "heated surfaces create distinctive burning scents",
                "exhaust and industrial odors hang heavy",
                "overheated machinery adds acrid notes"
            ],
            'atmospheric': [
                "heat creates pressing, almost oppressive weight",
                "the air itself vibrates with intense energy",
                "energy levels feel maxed out everywhere"
            ]
        },
        
        'clear_early_afternoon': {
            'visual': [
                "afternoon light takes on warmer, golden qualities",
                "long shadows begin creeping across everything",
                "sun's angle creates interesting light patterns"
            ],
            'auditory': [
                "post-lunch energy maintains its energetic pace",
                "traffic flows with occasional bursts and horns",
                "construction and activity blend into afternoon din"
            ],
            'olfactory': [
                "warming surfaces release stored heat and scents",
                "food preparation adds complex cooking aromas",
                "afternoon heat carries mixed industrial smells"
            ],
            'atmospheric': [
                "afternoon energy feels focused and purposeful",
                "productivity lingers in the warm air",
                "mid-day momentum continues building around you"
            ]
        },
        
        'clear_late_afternoon': {
            'visual': [
                "golden hour light bathes everything in amber",
                "surfaces glow with reflected sunlight",
                "shadows stretch long and dramatic everywhere"
            ],
            'auditory': [
                "rush hour traffic begins its evening crescendo",
                "pace quickens as people head toward destinations",
                "cooling systems work harder against accumulated heat"
            ],
            'olfactory': [
                "the day's heat has concentrated all scents",
                "hot surfaces dominate with metallic undertones",
                "ventilation systems add complex food aromas"
            ],
            'atmospheric': [
                "late afternoon carries anticipation of evening",
                "energy levels feel heightened but weary",
                "golden quality suffuses the warm, busy air"
            ]
        },
        
        'clear_dusk': {
            'visual': [
                "sky transforms into orange and deep purple",
                "artificial lights flicker on against darkening horizons",
                "illumination begins its evening glow against shadows"
            ],
            'auditory': [
                "evening sounds create steady flows of activity",
                "social spaces add voices to the mix",
                "day sounds transition to night rhythms"
            ],
            'olfactory': [
                "evening air carries cooled surfaces and accumulated scents",
                "food and entertainment aromas become more prominent",
                "exhaust mixes with hints of night-blooming plants"
            ],
            'atmospheric': [
                "dusk brings a sense of transition and possibility",
                "the air feels electric with evening energy",
                "anticipation fills the cooling, vibrant atmosphere"
            ]
        },
        
        'clear_early_evening': {
            'visual': [
                "artificial lights create vibrant tapestries of illumination",
                "windows glow warmly against deepening night",
                "everything transforms into constellations of human activity"
            ],
            'auditory': [
                "entertainment districts come alive with music and voices",
                "traffic maintains its steady hum with sirens",
                "soundscapes become richer and more varied"
            ],
            'olfactory': [
                "cool evening air carries scents from restaurants",
                "aromas become more complex and inviting",
                "exhaust mingles with food, perfume, and night air"
            ],
            'atmospheric': [
                "early evening energy feels social and dynamic",
                "excitement and possibility fill the cool air",
                "nightlife begins stirring with electric pulses"
            ]
        },
        
        'clear_late_evening': {
            'visual': [
                "artificial lights create glowing networks against darkness",
                "reflections dance on surfaces like liquid fire",
                "everything takes on a cinematic quality"
            ],
            'auditory': [
                "nightlife sounds mix with diminishing traffic",
                "music spills into the night air",
                "rhythms shift to evening tempos"
            ],
            'olfactory': [
                "night air carries complex blends of nightlife scents",
                "cooling surfaces release stored heat and odors",
                "food, alcohol, and exhaust create distinctive atmospheres"
            ],
            'atmospheric': [
                "late evening brings a sense of adventure",
                "the air feels alive with entertainment and possibility",
                "electric quality charges the cool, active night"
            ]
        },
        
        'clear_night': {
            'visual': [
                "deep night wraps everything in darkness and light",
                "illumination creates islands in vast shadows",
                "late establishments glow like beacons in quiet darkness"
            ],
            'auditory': [
                "everything settles into quieter night rhythms",
                "distant sounds provide low, steady background",
                "occasional night sounds echo clearly in stillness"
            ],
            'olfactory': [
                "cool night air carries concentrated scents",
                "darkness intensifies smells and aromas",
                "late-night food vendors add warm, comforting notes"
            ],
            'atmospheric': [
                "night brings solitude and mystery",
                "the air feels cooler and more intimate",
                "contemplative quality fills the quiet darkness"
            ]
        },
        
        'clear_late_night': {
            'visual': [
                "deep hours paint everything in stark contrasts",
                "only essential lighting creates dramatic scenes",
                "few active windows suggest insomniacs and workers"
            ],
            'auditory': [
                "everything reaches its quietest point",
                "night shift machinery and distant sounds carry clearly",
                "occasional emergency sounds stand out against silence"
            ],
            'olfactory': [
                "cold air sharpens scents into distinct, clear notes",
                "night operations add their own distinctive odors",
                "empty spaces and cooling surfaces dominate"
            ],
            'atmospheric': [
                "late night carries a sense of isolation",
                "the air feels thin and crisp with possibility",
                "something both lonely and peaceful fills the stillness"
            ]
        },

        # Rain weather (moderate intensity) - expanded across time periods
        'rain_pre_dawn': {
            'visual': [
                "steady rain turns surfaces into dark mirrors reflecting scattered light",
                "water streams down every surface pooling in shadowed corners",
                "pre-dawn takes on noir quality under rain-washed darkness"
            ],
            'auditory': [
                "rain patters against surfaces with rhythmic precision",
                "water splashes through puddles with wet hissing sounds",
                "rainfall creates white noise muffling other sounds"
            ],
            'olfactory': [
                "petrichor mingles with the scent of wet surfaces",
                "rain releases stored smells from pavement and gutters",
                "clean water fights against underlying industrial odors"
            ],
            'atmospheric': [
                "rain creates intimate, enclosed feeling despite open space",
                "everything feels washed clean yet somehow more mysterious",
                "there's renewal mixed with persistent grit"
            ]
        },
        
        'rain_dawn': {
            'visual': [
                "dawn light filters through falling rain like silver curtains",
                "water transforms everything into impressionist paintings",
                "morning shadows blur and soften in the steady downpour"
            ],
            'auditory': [
                "rain drums steadily against every surface around you",
                "morning sounds become muffled and distant in the deluge",
                "water gurgles through drains with urgent intensity"
            ],
            'olfactory': [
                "wet earth and fresh rain cleanse the morning air",
                "moisture brings out hidden scents from every crevice",
                "the smell of washing and renewal fills the atmosphere"
            ],
            'atmospheric': [
                "rain-soaked dawn feels like the world is being reborn",
                "moisture charges the air with electric possibility",
                "everything feels softer and more forgiving"
            ]
        },
        
        'rain_evening': {
            'visual': [
                "steady rain turns the streets into dark mirrors reflecting neon light",
                "water streams down building facades and pools in street corners",
                "the city takes on a noir-like quality under the rain-washed evening light"
            ],
            'auditory': [
                "rain patters steadily against concrete and metal surfaces",
                "tires splash through growing puddles with wet hissing sounds",
                "the rainfall creates a white noise that muffles other city sounds"
            ],
            'olfactory': [
                "petrichor mingles with urban scents of wet concrete and metal",
                "the rain releases stored smells from the pavement and gutters",
                "clean water scent fights against underlying industrial odors"
            ],
            'atmospheric': [
                "the rain creates an intimate, enclosed feeling despite the open space",
                "the city feels washed clean yet somehow more mysterious",
                "there's a sense of renewal mixed with urban grit"
            ]
        },
        
        'rain_night': {
            'visual': [
                "rain slicks every surface into black mirrors reflecting artificial light",
                "water creates streams of liquid silver down dark surfaces",
                "night becomes a canvas of rain and reflected illumination"
            ],
            'auditory': [
                "rain provides constant percussion against the night quiet",
                "water flows through hidden channels with liquid whispers",
                "the downpour transforms night sounds into something intimate"
            ],
            'olfactory': [
                "night rain intensifies every scent and aroma",
                "moisture brings out the deep, hidden smells of darkness",
                "wet air carries traces of secrets and possibilities"
            ],
            'atmospheric': [
                "rain-soaked night feels mysterious and full of potential",
                "moisture makes the darkness more intimate and personal",
                "there's something romantic and dangerous in the wet air"
            ]
        },
        
        # Torrential Rain (extreme intensity)
        'torrential_rain_night': {
            'visual': [
                "sheets of rain cascade down in torrents that transform everything into raging rivers of chaos",
                "the deluge overwhelms every drainage system creating waterfalls from rooftops and overhangs",
                "visibility drops to mere arm's length as rain falls like solid walls of liquid fury"
            ],
            'auditory': [
                "the thunderous roar of torrential rain drowns out absolutely every other sound in existence",
                "water crashes and gurgles through overwhelmed systems with violent, primal intensity",
                "the storm creates a deafening symphony of liquid percussion against every conceivable surface"
            ],
            'olfactory': [
                "the air fills with the overwhelming scent of churned earth and flood waters",
                "deluge carries the mingled odors of everything in its path creating choking mixtures",
                "ozone and rain-soaked debris create a powerful atmosphere that burns the nostrils"
            ],
            'atmospheric': [
                "the storm transforms familiar landscapes into alien water-worlds of chaos and raw power",
                "nature's fury makes every human construction feel fragile and temporary as matchsticks",
                "the air vibrates with primal energy of water reclaiming everything in its unstoppable path"
            ]
        },
        
        'torrential_rain_midday': {
            'visual': [
                "apocalyptic downpour transforms bright day into a gray-green nightmare of cascading water",
                "torrents pour from every surface creating instant rivers where none existed moments before",
                "the world disappears behind walls of rain falling with supernatural intensity and violence"
            ],
            'auditory': [
                "rain roars like freight trains colliding with the earth in endless, deafening percussion",
                "the storm drowns out sirens, machinery, and human voices in its liquid symphony of destruction",
                "water hammers against everything with the sound of ten thousand drums beating in perfect chaos"
            ],
            'olfactory': [
                "flood waters carry the scent of everything they've touched in a choking cocktail of urban debris",
                "the air reeks of displaced earth, overflowing sewers, and the metallic tang of electrical systems failing",
                "ozone mixes with organic decay creating an atmosphere thick enough to taste and fear"
            ],
            'atmospheric': [
                "the torrential storm makes the world feel like it's ending in slow motion drowning",
                "nature's absolute fury reduces human civilization to helpless spectators of elemental power",
                "the deluge transforms familiar reality into something alien, dangerous, and utterly unforgiving"
            ]
        },
        
        # Hot Weather - Flashstorm (extreme intensity)
        'flashstorm_midday': {
            'visual': [
                "the air shimmers with brutal heat waves that distort reality like a fever dream mirage",
                "metal surfaces become untouchable furnaces radiating visible waves of scorching, dancing air",
                "the sun blazes with merciless intensity that bleaches color from everything it touches"
            ],
            'auditory': [
                "oppressive silence of extreme heat broken only by the sharp ping and crack of expanding metal",
                "cooling systems strain and whine desperately against the overwhelming temperature like dying animals",
                "the very air hisses and whispers with the sound of moisture evaporating into nothingness"
            ],
            'olfactory': [
                "superheated surfaces release acrid chemical smells that burn nostrils and sear the throat",
                "the air carries metallic taste of overheated machinery and surfaces baking under relentless sun",
                "waves of heat bring sharp scents of sun-baked garbage and industrial chemicals melting together"
            ],
            'atmospheric': [
                "heat presses down like a physical weight making every breath feel like work",
                "everything becomes a furnace radiating stored solar energy from every conceivable surface",
                "the oppressive temperature transforms familiar environments into hellscapes of concrete and steel"
            ]
        },
        
        'flashstorm_early_afternoon': {
            'visual': [
                "heat mirages dance like ghosts across every surface turning the world into liquid illusion",
                "air itself becomes visible as superheated waves distort and bend light into impossible shapes",
                "the sun hangs like a malevolent eye burning everything beneath its unblinking gaze"
            ],
            'auditory': [
                "the silence of extreme heat broken by metal expanding with gunshot-sharp cracks and pops",
                "cooling systems work overtime creating a mechanical symphony of desperation and failing machinery",
                "even the air seems to scream as moisture turns to steam before it can form"
            ],
            'olfactory': [
                "the air tastes of burning metal, melting plastic, and surfaces cooking under relentless heat",
                "superheated pavement releases chemical vapors that create a toxic soup of industrial scents",
                "heat transforms every familiar smell into something sharp, acrid, and threatening to the senses"
            ],
            'atmospheric': [
                "the flashstorm heat makes survival feel like a constant battle against the elements themselves",
                "every surface radiates enough heat to cook flesh and every breath feels like inhaling fire",
                "the world becomes a furnace where human comfort is not just absent but actively hostile"
            ]
        },
        
        # Cold Weather - Blizzard (extreme intensity)
        'blizzard_night': {
            'visual': [
                "howling winds drive sheets of snow horizontally through the air like frozen bullets of ice",
                "the blizzard transforms everything into a white void where visibility drops to arm's length",
                "ice forms instantly on every surface while snow piles into massive drifts that bury everything"
            ],
            'auditory': [
                "the blizzard roars with primal fury drowning out all other sounds in its icy symphony of destruction",
                "wind shrieks through gaps and around corners with banshee intensity that chills the soul",
                "the storm creates constant howling punctuated by sharp cracks of ice and flying debris"
            ],
            'olfactory': [
                "air carries the clean, sharp scent of pure snow mixed with metallic bite of extreme cold",
                "frozen precipitation brings sterile smell of sub-zero temperatures that numbs every sense",
                "the blizzard strips away all warm scents leaving only crystalline purity of arctic air"
            ],
            'atmospheric': [
                "the storm transforms everything into an arctic wasteland where survival becomes the only priority",
                "nature's frozen fury makes every environment feel hostile and utterly alien to human life",
                "the blizzard brings primal cold that penetrates not just to bone but to soul itself"
            ]
        },
        
        'blizzard_early_morning': {
            'visual': [
                "dawn struggles to penetrate walls of wind-driven snow that turn the world into white chaos",
                "ice crystals fill the air like tiny razors cutting visibility to mere inches in every direction",
                "the blizzard creates a whiteout where up and down lose all meaning in the frozen maelstrom"
            ],
            'auditory': [
                "wind screams with the voices of a thousand demons tearing through the frozen air",
                "the storm drowns out every sound except the relentless howl of arctic fury unleashed",
                "snow and ice crash against surfaces like machine gun fire in the endless winter assault"
            ],
            'olfactory': [
                "the air burns with cold so intense it sears nostrils and throat like liquid nitrogen",
                "frozen air carries nothing but the sterile scent of ice and the metallic taste of extreme cold",
                "the blizzard strips every warm smell from existence leaving only the purity of arctic death"
            ],
            'atmospheric': [
                "the storm makes the world feel like an alien planet where warmth is just a distant memory",
                "blizzard fury transforms familiar places into landscapes of pure survival horror",
                "nature's frozen rage makes every breath a victory and every heartbeat a defiance of the cold"
            ]
        },
        
        # Soft Snow (moderate intensity)
        'soft_snow_early_morning': {
            'visual': [
                "gentle snowflakes drift down like confetti, coating everything in pristine white",
                "fresh snow muffles harsh edges with soft curves and gentle accumulation",
                "morning light reflects off snow cover creating ethereal landscapes"
            ],
            'auditory': [
                "sounds become muffled and distant beneath the soft blanket of falling snow",
                "footsteps crunch softly through accumulated powder with rhythmic precision",
                "snow creates peaceful hush that transforms usual cacophony into whispers"
            ],
            'olfactory': [
                "air carries clean, crisp scent of fresh snow and winter purity",
                "cold air brings sharp clarity that makes every breath feel cleansing",
                "snow masks harsh odors with neutral scent of frozen precipitation"
            ],
            'atmospheric': [
                "gentle snowfall creates sense of peace and temporary beauty",
                "cold brings invigorating clarity that sharpens awareness and focus",
                "winter scene transforms everything into something almost magical and serene"
            ]
        },
        
        'soft_snow_dusk': {
            'visual': [
                "snowflakes catch the last light like tiny stars falling from purple sky",
                "evening snow creates soft halos around every source of illumination",
                "dusk and snow combine to paint everything in gentle, muted tones"
            ],
            'auditory': [
                "evening sounds become hushed and intimate under falling snow",
                "the world takes on cathedral quiet broken only by soft whispers",
                "snow muffles everything into a peaceful, contemplative soundscape"
            ],
            'olfactory': [
                "cold air sharpens and purifies every scent into crystal clarity",
                "snow brings the clean smell of winter and fresh possibilities",
                "evening air mixed with snow creates bracing, invigorating atmosphere"
            ],
            'atmospheric': [
                "soft snow at dusk feels like the world is being tucked in for sleep",
                "there's magic in the way snow transforms familiar places into wonderland",
                "cold air and gentle precipitation create sense of renewal and peace"
            ]
        },
        
        # Sandstorm (extreme intensity)
        'sandstorm_afternoon': {
            'visual': [
                "walls of gritty dust and debris roar through the air like brown tsunamis of destruction",
                "the sandstorm reduces visibility to absolute zero while coating everything in abrasive particles",
                "air becomes choking cloud of dust transforming day into apocalyptic twilight of swirling chaos"
            ],
            'auditory': [
                "the storm howls with sound of millions of particles abrading against every surface",
                "wind-driven debris rattles and crashes with machine-gun intensity that never stops",
                "sandstorm creates constant roar punctuated by impacts of flying debris and grit"
            ],
            'olfactory': [
                "air fills with gritty taste and smell of pulverized earth, metal, and organic debris",
                "dust carries accumulated scents of everything in choking, abrasive mixture that burns the throat",
                "storm brings sharp, mineral smell of abraded stone and particles ground to powder"
            ],
            'atmospheric': [
                "sandstorm transforms everything into alien landscape of swirling, abrasive chaos that strips flesh",
                "the storm brings primal sense of nature's power to scour and reshape with relentless fury",
                "air itself becomes hostile turning every breath into a battle against elements gone mad"
            ]
        },
        
        'sandstorm_dusk': {
            'visual': [
                "dust storm turns sunset into hellish orange glow filtered through walls of flying grit",
                "sand fills every gap and crevice while wind howls with voices of desert fury",
                "the world disappears behind curtains of dust that turn day into something from nightmares"
            ],
            'auditory': [
                "wind screams through the storm carrying the sound of a world being ground to powder",
                "debris crashes and rattles in the endless assault of particles against every surface",
                "the sandstorm roars like a living thing hungry to devour everything in its path"
            ],
            'olfactory': [
                "dust clogs nostrils and throat with the taste of ancient earth and mineral decay",
                "air becomes unbreathable soup of grit that carries scents of destruction and erosion",
                "the storm brings smell of things being broken down and worn away by relentless abrasion"
            ],
            'atmospheric': [
                "sandstorm at dusk feels like witnessing the end of worlds in slow motion grinding",
                "nature's fury reduces everything to its component particles in endless, patient destruction",
                "the storm makes survival feel like defying the fundamental forces of entropy itself"
            ]
        },
        
        # Fog (moderate intensity)
        'fog_dawn': {
            'visual': [
                "thick fog rolls through everything, reducing the world to ghostly silhouettes",
                "moisture beads on every surface while mist transforms landmarks into mysteries",
                "fog creates intimate world where nothing exists beyond meters of gray visibility"
            ],
            'auditory': [
                "sounds become muffled and directionless in thick, moisture-laden air",
                "fog seems to absorb noise, creating pockets of eerie silence and unexpected sound",
                "distant noises emerge from mist without warning, then fade back into gray obscurity"
            ],
            'olfactory': [
                "air carries damp, neutral scent of water vapor mixed with hidden undertones",
                "moisture brings out subtle smells from hidden corners and crevices",
                "fog creates humid atmosphere that intensifies both pleasant and unpleasant odors"
            ],
            'atmospheric': [
                "fog creates sense of isolation and mystery in the middle of familiar spaces",
                "visibility becomes precious commodity in gray, moisture-heavy environment",
                "mist transforms everything into dreamscape where reality feels soft and uncertain"
            ]
        },
        
        'fog_evening': {
            'visual': [
                "evening fog transforms artificial lights into soft halos of diffused glow",
                "mist swallows everything beyond arm's reach in gray, shifting veils",
                "fog and night combine to create world of shadows and uncertain shapes"
            ],
            'auditory': [
                "evening sounds become intimate whispers in the moisture-heavy air",
                "fog dampens and muffles everything into cathedral quiet",
                "voices and footsteps seem to float disembodied in the gray void"
            ],
            'olfactory': [
                "humid air intensifies every scent into rich, complex layers",
                "moisture brings out hidden smells from every surface and corner",
                "fog carries traces of secrets and possibilities on the damp air"
            ],
            'atmospheric': [
                "evening fog creates sense of mystery and romantic danger",
                "mist makes everything feel closer and more intimate",
                "there's something both beautiful and ominous in the thick, gray air"
            ]
        },
        
        # Heavy Fog (intense intensity)  
        'heavy_fog_night': {
            'visual': [
                "impenetrable fog reduces the world to mere arm's length of gray visibility that swallows everything",
                "thick mist transforms familiar landmarks into alien shapes that loom and vanish like ghosts",
                "heavy fog creates a world where direction becomes meaningless and navigation purely by feel"
            ],
            'auditory': [
                "sounds become completely directionless in the soup-thick air that deadens all echoes and distance",
                "heavy fog swallows noises whole making voices seem to come from inside your own head",
                "the mist creates acoustic illusions where footsteps and voices appear and disappear like spirits"
            ],
            'olfactory': [
                "air becomes thick enough to taste with moisture that carries every scent in concentrated doses",
                "heavy fog intensifies smells until they become almost overwhelming in their clarity and presence",
                "the mist carries layers of odors that shift and change like the fog itself in endless combinations"
            ],
            'atmospheric': [
                "heavy fog creates a world that feels completely separate from normal reality and familiar spaces",
                "the mist makes everything feel dreamlike where the laws of physics seem negotiable and uncertain",
                "fog this thick transforms the familiar into something alien where survival instincts suddenly matter"
            ]
        },
        
        # Tox Rain (intense intensity)
        'tox_rain_evening': {
            'visual': [
                "acid rain falls in corrosive droplets that eat away at surfaces and leave ugly stains",
                "toxic precipitation leaves steam and discoloration wherever it touches organic matter",
                "warning lights flicker as caustic rainfall damages exposed electrical systems with chemical fury"
            ],
            'auditory': [
                "toxic rain hisses and bubbles as it makes contact with reactive surfaces in chemical symphony",
                "metal corrodes audibly under assault of caustic precipitation that eats through everything",
                "emergency sirens wail in distance as the world responds to the chemical threat from above"
            ],
            'olfactory': [
                "air reeks with sharp, burning smell of industrial chemicals and acid that sears the nostrils",
                "toxic vapors rise from every surface touched by corrosive rainfall creating poisonous clouds",
                "atmosphere carries metallic tang of dissolved metals and burning organic compounds in deadly mixture"
            ],
            'atmospheric': [
                "toxic rain transforms everything into hazardous chemical wasteland where exposure means death",
                "every breath feels dangerous as air fills with caustic vapors that burn lungs and throat",
                "environment becomes actively hostile to all forms of life and machinery in chemical warfare"
            ]
        },
        
        'tox_rain_night': {
            'visual': [
                "poisonous rain gleams with unnatural colors as it dissolves surfaces under artificial light",
                "toxic downpour creates streams of chemical death that flow like liquid horror through everything",
                "night becomes a hellscape where rain itself is the enemy in this chemical apocalypse"
            ],
            'auditory': [
                "chemical rain sizzles and pops as it eats through materials with the sound of dissolution",
                "toxic precipitation creates symphony of destruction as metal and organic matter surrender to acid",
                "emergency broadcasts echo through the poisonous night warning of chemical contamination everywhere"
            ],
            'olfactory': [
                "air becomes unbreathable cocktail of industrial toxins that burn every breath and sear the throat",
                "poisonous vapors rise in clouds of chemical death that make the atmosphere itself lethal",
                "toxic rain brings scents of dissolution and chemical breakdown that promise only death and decay"
            ],
            'atmospheric': [
                "tox rain at night feels like the end of the world in slow motion chemical dissolution",
                "poisonous precipitation makes every surface a threat and every breath a gamble with death",
                "the toxic storm transforms familiar night into alien landscape of chemical horror and dissolution"
            ]
        },
        
        # Gray Pall (intense intensity)
        'gray_pall_midday': {
            'visual': [
                "thick, choking gray haze blots out the sun and reduces the world to sepia tones of despair",
                "oppressive smog hangs like funeral shroud over everything in sight blocking out hope and light",
                "visibility drops to mere blocks as toxic atmosphere obscures distant landmarks in poisonous haze"
            ],
            'auditory': [
                "heavy air muffles all sounds, creating oppressive silence broken only by coughing and wheezing",
                "air filtration systems work overtime with constant mechanical wheeze and rattle of desperation",
                "everything sounds sick and struggling beneath the weight of poisoned atmosphere that chokes life"
            ],
            'olfactory': [
                "air carries acrid stench of burning chemicals, industrial waste, and organic decay in toxic mixture",
                "every breath brings taste of ash, metal particles, and unidentifiable toxins that coat the throat",
                "atmosphere feels thick and oily with accumulated pollution of industrial excess and environmental collapse"
            ],
            'atmospheric': [
                "gray pall creates sense of environmental apocalypse and systemic failure of civilization itself",
                "poisoned air makes survival feel precarious and every breath a calculated risk with death",
                "everything feels like drowning in its own industrial excess and toxic legacy of human greed"
            ]
        },
        
        # Windy (mild intensity)
        'windy_afternoon': {
            'visual': [
                "strong gusts whip through everything, sending debris dancing through the air",
                "wind catches loose papers and trash, creating impromptu tornadoes of detritus",
                "flags and signs flutter frantically in the persistent breeze"
            ],
            'auditory': [
                "wind whistles through gaps with varying pitch and intensity",
                "loose objects rattle and bang as gusts push them around",
                "constant breeze creates background symphony of movement and percussion"
            ],
            'olfactory': [
                "moving air carries mixture of scents from different places",
                "wind brings brief whiffs of distant cooking, exhaust, and processes",
                "breeze keeps air fresh and prevents stagnant odors from settling"
            ],
            'atmospheric': [
                "wind brings energy and movement to otherwise static environment",
                "constant breeze creates sense of change and motion",
                "moving air makes everything feel alive and dynamic"
            ]
        },
        
        'windy_evening': {
            'visual': [
                "evening wind carries the scents and sounds of distant places",
                "gusts make artificial lights flicker and dance like living things",
                "wind turns loose objects into temporary sculptures of motion"
            ],
            'auditory': [
                "evening breeze carries voices, music, and sounds from far away",
                "wind creates symphony of whispers, rattles, and distant echoes",
                "moving air brings the sound of the world in constant motion"
            ],
            'olfactory': [
                "wind carries evening scents from kitchens, gardens, and far places",
                "breeze brings complex mixture of aromas that tell stories",
                "moving air prevents any single scent from dominating the atmosphere"
            ],
            'atmospheric': [
                "evening wind feels like the world is breathing deeply",
                "breeze brings sense of connection to distant places and possibilities",
                "moving air makes the night feel alive with potential and mystery"
            ]
        },
        
        # Overcast (mild intensity)
        'overcast_morning': {
            'visual': [
                "gray clouds blanket the sky in uniform sheets",
                "diffused light creates soft shadows everywhere",
                "the world takes on muted, monochrome quality"
            ],
            'auditory': [
                "sounds seem flatter and more subdued under cloud cover",
                "the overcast sky dampens echoes and sharpens nearby noises",
                "everything feels acoustically intimate and close"
            ],
            'olfactory': [
                "humid air carries scents more intensely than clear sky",
                "moisture in the atmosphere brings out subtle aromas",
                "overcast conditions make smells linger and blend together"
            ],
            'atmospheric': [
                "gray sky creates contemplative, introspective mood",
                "overcast conditions feel expectant and pregnant with possibility",
                "the world feels hushed and waiting under cloud cover"
            ]
        },
        
        'overcast_afternoon': {
            'visual': [
                "thick cloud cover filters sunlight into soft, even illumination",
                "everything appears in gentle, diffused light without harsh shadows",
                "gray sky creates uniform backdrop for all activity below"
            ],
            'auditory': [
                "overcast sky muffles distant sounds while amplifying nearby ones",
                "clouds seem to press sound downward creating intimate acoustics",
                "the world feels smaller and more contained under gray cover"
            ],
            'olfactory': [
                "humid overcast air intensifies every scent and aroma",
                "moisture holds smells longer creating complex atmospheric layers",
                "cloud cover traps and concentrates all environmental odors"
            ],
            'atmospheric': [
                "overcast afternoon feels cozy despite being outside",
                "gray sky creates sense of enclosed intimacy in open space",
                "the world feels softened and gentled under cloud blanket"
            ]
        },
        
        # Light Rain (moderate intensity)
        'light_rain_morning': {
            'visual': [
                "gentle droplets fall with lazy, intermittent rhythm from gray sky",
                "light rain creates subtle patterns on surfaces without overwhelming them",
                "morning takes on soft, watercolor quality under gentle precipitation"
            ],
            'auditory': [
                "light rain patters softly with irregular, peaceful rhythm",
                "gentle precipitation creates whispered percussion against surfaces",
                "the world sounds cleaner and more intimate under light rain"
            ],
            'olfactory': [
                "light rain brings fresh, clean scent without overwhelming intensity",
                "gentle precipitation releases subtle earth and pavement aromas",
                "air carries hint of moisture and renewal in soft doses"
            ],
            'atmospheric': [
                "light rain feels refreshing without being inconvenient or threatening",
                "gentle precipitation creates sense of cleansing and renewal",
                "the world feels washed and brightened by soft, caring rain"
            ]
        },
        
        'light_rain_evening': {
            'visual': [
                "evening light rain creates gentle halos around every illumination source",
                "droplets catch and reflect artificial light in thousands of tiny mirrors",
                "light precipitation adds romantic softness to evening scene"
            ],
            'auditory': [
                "gentle rain provides soft soundtrack to evening activities",
                "light precipitation creates intimate whispers against windows and surfaces",
                "the world sounds hushed and peaceful under caring rain"
            ],
            'olfactory': [
                "light evening rain brings out the scents of cooling surfaces",
                "gentle precipitation carries hints of dinner, warmth, and home",
                "air feels fresh and clean without the intensity of heavy rain"
            ],
            'atmospheric': [
                "light evening rain feels romantic and contemplative",
                "gentle precipitation makes the world feel cozy and intimate",
                "there's something peaceful and restorative in the soft droplets"
            ]
        },
        
        # Foggy Rain (moderate intensity)  
        'foggy_rain_dawn': {
            'visual': [
                "rain falls through thick mist creating layered curtains of moisture",
                "fog and precipitation combine to reduce visibility to ghostly outlines",
                "the world becomes impressionist painting of gray, water, and shadow"
            ],
            'auditory': [
                "rain sounds muffled and directionless in the thick, moisture-heavy air",
                "fog absorbs and scatters sounds while rain provides constant background",
                "everything becomes acoustically intimate and mysteriously distant"
            ],
            'olfactory': [
                "fog and rain create super-saturated air thick with moisture and scents",
                "the combination intensifies every aroma into rich, complex layers",
                "air feels thick enough to taste with humidity and precipitation"
            ],
            'atmospheric': [
                "foggy rain transforms familiar spaces into alien, dreamlike landscapes",
                "the combination creates sense of mystery and romantic danger",
                "world feels both intimate and infinite under layers of water and mist"
            ]
        },
        
        'foggy_rain_evening': {
            'visual': [
                "rain and fog combine with artificial light to create cinematic atmosphere",
                "precipitation falls through mist creating complex veils of moisture everywhere",
                "evening becomes noir landscape of shadow, reflection, and mystery"
            ],
            'auditory': [
                "rain patters through fog creating layered symphony of water sounds",
                "voices and footsteps seem to float disembodied in moisture-thick air",
                "the world becomes acoustically surreal with muffled, phantom sounds"
            ],
            'olfactory': [
                "fog and rain create almost overwhelming intensity of atmospheric scents",
                "moisture carries every aroma in super-concentrated, complex mixtures",
                "air becomes thick soup of humidity, precipitation, and urban essence"
            ],
            'atmospheric': [
                "foggy rain at evening feels like stepping into detective story",
                "the combination creates perfect atmosphere for mystery and romance",
                "world feels dangerous and beautiful under layers of mist and rain"
            ]
        },
        
        # Hard Snow (intense intensity)
        'hard_snow_afternoon': {
            'visual': [
                "heavy snowflakes fall with determined intensity creating rapidly accumulating drifts everywhere",
                "hard snow reduces visibility while coating every surface in thick, white blankets",
                "the world transforms quickly from familiar to winter wonderland under heavy precipitation"
            ],
            'auditory': [
                "hard snow falls with audible intensity creating constant whisper of accumulation",
                "footsteps crunch loudly through rapidly deepening snow with crystalline precision",
                "the world becomes muffled yet sharp as snow absorbs sound while creating new textures"
            ],
            'olfactory': [
                "hard snow brings sharp, clean scent of intense winter and frozen precipitation",
                "air carries metallic bite of serious cold mixed with fresh snow purity",
                "heavy snowfall creates atmosphere thick with moisture and crystalline clarity"
            ],
            'atmospheric': [
                "hard snow feels urgent and transformative as it rapidly changes everything",
                "heavy precipitation creates sense of nature asserting dominance over human spaces",
                "the world feels alive with winter energy and the power of accumulating snow"
            ]
        },
        
        'hard_snow_night': {
            'visual': [
                "heavy snow falls through artificial light creating swirling columns of white intensity",
                "hard precipitation accumulates rapidly turning night into winter battlefield of white",
                "snow reduces everything to essential shapes and shadows under dramatic illumination"
            ],
            'auditory': [
                "hard snow creates constant, intense whisper of millions of flakes impacting surfaces",
                "the world becomes muffled cathedral where only snow sounds matter anymore",
                "heavy precipitation drowns out distant sounds while amplifying immediate winter ones"
            ],
            'olfactory': [
                "night air fills with sharp, crystalline scent of serious snowfall and winter intensity",
                "hard snow brings metallic tang of deep cold mixed with fresh precipitation purity",
                "atmosphere becomes thick with moisture and the clean smell of winter dominance"
            ],
            'atmospheric': [
                "hard snow at night feels like nature taking control of the urban landscape",
                "heavy precipitation creates sense of winter warfare between elements and civilization",
                "the world feels transformed into something primal and beautiful under intense snowfall"
            ]
        },
        
        # Dry Thunderstorm (intense intensity)
        'dry_thunderstorm_afternoon': {
            'visual': [
                "lightning splits the sky with violent electricity while no rain falls from threatening clouds",
                "thunder rolls across landscape promising storms that never deliver water relief",
                "the sky churns with dramatic energy while ground remains parched and desperate"
            ],
            'auditory': [
                "thunder crashes with earth-shaking intensity that rattles windows and bones alike",
                "electrical discharge creates sharp cracks followed by rolling booms that never end",
                "the storm produces sound and fury without the relief of precipitation to follow"
            ],
            'olfactory': [
                "air fills with ozone and electrical charge that makes every breath taste metallic",
                "dry thunder brings scent of lightning and heated air without moisture relief",
                "atmosphere carries sharp smell of electricity and frustrated weather systems"
            ],
            'atmospheric': [
                "dry thunderstorm feels like nature's cruel joke promising relief without delivery",
                "electrical energy charges the air with tension and unfulfilled expectation",
                "the storm creates sense of power and drama without providing any actual relief"
            ]
        },
        
        'dry_thunderstorm_evening': {
            'visual': [
                "evening lightning illuminates landscape in stark, dramatic flashes without rain's blessing",
                "dry thunder creates spectacular light show against darkening sky that promises nothing",
                "storm clouds gather and churn with electrical fury while earth remains thirsty below"
            ],
            'auditory': [
                "thunder echoes through evening air with dramatic intensity that shakes everything",
                "electrical storms create symphony of booms and crashes without rain's percussion",
                "the sky roars with power while ground waits desperately for moisture that won't come"
            ],
            'olfactory': [
                "evening air fills with ozone and electrical charge mixed with dust and heat",
                "dry thunder brings sharp scents of lightning without the blessing of petrichor",
                "atmosphere tastes of electricity, frustration, and promises that won't be kept"
            ],
            'atmospheric': [
                "dry evening thunderstorm feels like dramatic performance without substance",
                "electrical energy creates anticipation and excitement that leads to disappointment",
                "the storm charges air with power while delivering nothing but sound and fury"
            ]
        },
        
        # Rainy Thunderstorm (intense intensity)
        'rainy_thunderstorm_afternoon': {
            'visual': [
                "lightning illuminates sheets of rain falling with violent intensity from churning storm clouds",
                "thunder and downpour combine to create spectacular display of nature's raw power unleashed",
                "the world disappears behind walls of water punctuated by brilliant flashes of electricity"
            ],
            'auditory': [
                "thunder crashes over the roar of torrential rain creating deafening symphony of chaos",
                "storm produces overwhelming cacophony of electrical discharge and water percussion",
                "the world drowns in sound as thunder and deluge compete for acoustic dominance"
            ],
            'olfactory': [
                "air fills with ozone, petrichor, and electrical charge creating intoxicating storm atmosphere",
                "rainy thunder brings every scent alive with moisture, electricity, and primal energy",
                "atmosphere becomes thick cocktail of lightning, rain, and earth responding to bombardment"
            ],
            'atmospheric': [
                "rainy thunderstorm feels like witnessing nature's absolute fury and power unleashed completely",
                "storm creates sense of being small and vulnerable before elemental forces beyond control",
                "the world becomes primal battlefield where electricity and water wage war above"
            ]
        },
        
        'rainy_thunderstorm_night': {
            'visual': [
                "night storm illuminates cascading rain in brilliant flashes that turn water into liquid silver",
                "lightning reveals the fury of deluge for split seconds before darkness reclaims everything",
                "thunder and rain create dramatic night scene of power, water, and electrical violence"
            ],
            'auditory': [
                "nighttime storm produces overwhelming symphony of rain percussion and thunder explosions",
                "electrical discharge punctuates constant roar of water with sharp cracks and rolling booms",
                "the world becomes acoustic chaos where thunder and deluge create deafening natural music"
            ],
            'olfactory': [
                "night air fills with intoxicating mixture of ozone, rain, and electrical discharge energy",
                "storm brings every scent alive with moisture, lightning, and primal atmospheric power",
                "atmosphere becomes thick with the smell of electricity, water, and earth under assault"
            ],
            'atmospheric': [
                "rainy night thunderstorm feels like being inside nature's most powerful and beautiful tantrum",
                "storm creates sense of witnessing elemental forces that dwarf human concerns completely",
                "the world becomes cathedral of power where electricity and water create divine chaos"
            ]
        },
        
        # Blind Fog (intense intensity)
        'blind_fog_morning': {
            'visual': [
                "impenetrable fog reduces visibility to absolute zero creating world of pure gray nothingness",
                "thick mist swallows everything beyond arm's reach making navigation purely tactile experience",
                "blind fog transforms familiar landscape into alien void where sight becomes useless sense"
            ],
            'auditory': [
                "sounds become completely directionless and distorted in fog so thick it swallows echoes",
                "blind fog creates acoustic maze where familiar noises seem to come from everywhere",
                "the world becomes purely auditory as thick mist makes every sound mysterious and threatening"
            ],
            'olfactory': [
                "fog becomes so thick it carries concentrated essence of everything it touches",
                "blind mist intensifies every scent until air tastes of moisture and accumulated odors",
                "atmosphere becomes soup thick enough to drink with layers of smell and humidity"
            ],
            'atmospheric': [
                "blind fog creates sense of being completely cut off from normal world and reality",
                "thick mist makes every familiar space feel alien and potentially dangerous to navigate",
                "the world becomes pure sensory experience where sight fails and other senses must dominate"
            ]
        },
        
        'blind_fog_evening': {
            'visual': [
                "evening fog becomes so thick that artificial lights create useless halos in impenetrable mist",
                "blind fog swallows illumination whole making navigation impossible despite bright sources",
                "thick evening mist transforms well-lit areas into void where light becomes decoration only"
            ],
            'auditory': [
                "evening sounds become phantom whispers in fog so thick it distorts every acoustic reference",
                "blind mist makes familiar evening noises seem to come from inside your own head",
                "the world becomes purely auditory maze where sound travels through fog like liquid medium"
            ],
            'olfactory': [
                "evening fog carries concentrated mixture of every scent until air becomes almost solid",
                "blind mist intensifies evening aromas into overwhelming sensory assault that coats everything",
                "atmosphere becomes thick enough to chew with layers of humidity and accumulated essences"
            ],
            'atmospheric': [
                "blind evening fog creates sense of being trapped in gray void separate from reality",
                "thick mist makes familiar evening spaces feel like alien dimension of pure sensation",
                "the world becomes surreal experience where normal rules of navigation and sight fail completely"
            ]
        }
    }
}
