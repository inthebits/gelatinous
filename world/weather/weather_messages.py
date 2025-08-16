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
        # Clear weather variations by time of day
        'clear_pre_dawn': {
            'visual': [
                "darkness still holds the city in its grip with only hints of coming light",
                "streetlights cast isolated pools of yellow illumination",
                "the sky remains deep and starless above the urban sprawl"
            ],
            'auditory': [
                "the city sleeps with only distant hums and occasional sounds",
                "night shift machinery provides a low mechanical backdrop",
                "sporadic traffic creates brief interruptions in the quiet"
            ],
            'olfactory': [
                "cool night air carries traces of exhaust and urban decay",
                "the smell of dew begins to mix with concrete dust",
                "industrial odors from the night shift drift through empty streets"
            ],
            'atmospheric': [
                "the pre-dawn stillness feels heavy and expectant",
                "there's a sense that the world is holding its breath",
                "the air carries the promise of approaching dawn"
            ]
        },
        
        'clear_dawn': {
            'visual': [
                "pale dawn light filters through the urban haze",
                "morning shadows stretch long between buildings",
                "the sky lightens to a dirty yellow-gray above the cityscape"
            ],
            'auditory': [
                "distant traffic begins its daily drone",
                "the city slowly awakens with scattered sounds of activity",
                "footsteps echo in the crisp morning air"
            ],
            'olfactory': [
                "cool morning air carries hints of exhaust and concrete",
                "the scent of warming asphalt begins to rise",
                "faint smells of breakfast cooking drift from nearby buildings"
            ],
            'atmospheric': [
                "the air feels fresh despite the urban setting",
                "morning calm settles over the concrete landscape",
                "the day feels full of potential and hidden dangers"
            ]
        },
        
        'clear_early_morning': {
            'visual': [
                "golden sunlight slants between the towering structures",
                "harsh light glints off metal surfaces and broken glass",
                "morning shadows create a checkerboard pattern on the pavement"
            ],
            'auditory': [
                "the city hums with increasing activity",
                "vehicle engines warm up in distant parking areas",
                "the steady background noise of urban life grows stronger"
            ],
            'olfactory': [
                "warming concrete releases its stored heat and embedded odors",
                "exhaust fumes begin to thicken in the still air",
                "industrial scents mix with the smell of hot metal"
            ],
            'atmospheric': [
                "the morning energy feels charged with possibility",
                "visibility is sharp and clear in all directions",
                "the urban jungle feels alert and watchful"
            ]
        },
        
        'clear_late_morning': {
            'visual': [
                "bright morning sun climbs higher, casting shorter shadows",
                "the city basks in full daylight with crisp visibility",
                "business districts show peak activity under clear skies"
            ],
            'auditory': [
                "late morning brings peak urban activity and energy",
                "construction, traffic, and business create a lively soundscape",
                "the city hums with productivity and forward momentum"
            ],
            'olfactory': [
                "warming asphalt and concrete begin to release their heat",
                "coffee shops and food vendors add rich aromas to the air",
                "the morning's fresh air starts mixing with urban industrial scents"
            ],
            'atmospheric': [
                "late morning feels dynamic and full of purpose",
                "there's an energetic quality to the warming air",
                "productivity and ambition seem to fill the urban atmosphere"
            ]
        },
        
        'clear_midday': {
            'visual': [
                "harsh midday sun beats down on the concrete and steel",
                "heat shimmer rises from the baking asphalt surfaces",
                "shadows are short and sharp beneath the intense light"
            ],
            'auditory': [
                "the city thrums with peak activity and constant motion",
                "air conditioning units hum and rattle from every building",
                "the background noise forms a steady urban symphony"
            ],
            'olfactory': [
                "hot concrete and metal create a distinctive urban smell",
                "exhaust and industrial odors hang heavy in the still air",
                "the scent of overheated machinery drifts from building vents"
            ],
            'atmospheric': [
                "the heat creates a pressing, almost oppressive feeling",
                "the air itself seems to vibrate with urban intensity",
                "energy levels feel maxed out across the concrete landscape"
            ]
        },
        
        'clear_early_afternoon': {
            'visual': [
                "afternoon light starts to take on a warmer, golden quality",
                "long shadows begin to creep across the urban landscape",
                "the sun's angle creates interesting patterns through the city grid"
            ],
            'auditory': [
                "the post-lunch city maintains its energetic pace",
                "traffic continues its steady flow with occasional horn bursts",
                "construction and business sounds blend into the afternoon din"
            ],
            'olfactory': [
                "warming concrete releases stored heat with distinctive urban scents",
                "food vendors and restaurants add cooking aromas to the air",
                "the afternoon heat carries exhaust and industrial smells"
            ],
            'atmospheric': [
                "the afternoon energy feels focused and purposeful",
                "there's a sense of productivity in the warm air",
                "the city hums with mid-day momentum"
            ]
        },
        
        'clear_late_afternoon': {
            'visual': [
                "golden hour light bathes the city in warm, amber tones",
                "building facades glow with reflected sunlight",
                "shadows stretch long and dramatic across streets and plazas"
            ],
            'auditory': [
                "rush hour traffic begins its evening crescendo",
                "the city's pace quickens as people head home",
                "air conditioning units work harder against the day's accumulated heat"
            ],
            'olfactory': [
                "the day's heat has concentrated all urban scents",
                "hot asphalt and concrete dominate with metallic undertones",
                "restaurant ventilation systems add complex food aromas"
            ],
            'atmospheric': [
                "the late afternoon carries anticipation of evening",
                "energy levels feel heightened but tinged with weariness",
                "there's a golden quality to the warm, busy air"
            ]
        },
        
        'clear_dusk': {
            'visual': [
                "the sky transforms into shades of orange and deep purple",
                "city lights begin to flicker on against the darkening horizon",
                "neon signs start their evening glow against twilight shadows"
            ],
            'auditory': [
                "evening traffic creates a steady flow of urban sound",
                "restaurant patios and street life add voices to the mix",
                "the city transitions from day sounds to night rhythms"
            ],
            'olfactory': [
                "evening air carries cooled concrete and the day's accumulated scents",
                "restaurant and food vendor aromas become more prominent",
                "exhaust mixes with hints of night-blooming urban plants"
            ],
            'atmospheric': [
                "dusk brings a sense of transition and possibility",
                "the air feels electric with evening energy",
                "there's anticipation in the cooling, vibrant atmosphere"
            ]
        },
        
        'clear_early_evening': {
            'visual': [
                "street lights and neon create a vibrant urban tapestry",
                "windows glow warmly against the deepening night",
                "the city transforms into a constellation of human activity"
            ],
            'auditory': [
                "evening entertainment districts come alive with music and voices",
                "traffic maintains its steady hum with occasional sirens",
                "the soundscape becomes richer and more varied"
            ],
            'olfactory': [
                "cool evening air carries scents from restaurants and bars",
                "the urban fragrance becomes more complex and inviting",
                "exhaust mingles with food, perfume, and night air"
            ],
            'atmospheric': [
                "early evening energy feels social and dynamic",
                "there's excitement and possibility in the cool air",
                "the city pulses with nightlife beginning to stir"
            ]
        },
        
        'clear_late_evening': {
            'visual': [
                "city lights create a glowing network against the dark sky",
                "neon reflections dance on wet pavement and building surfaces",
                "the urban landscape takes on a cinematic quality"
            ],
            'auditory': [
                "nightlife sounds mix with diminishing traffic",
                "music spills from clubs and bars into the night air",
                "the city's rhythm shifts to its evening tempo"
            ],
            'olfactory': [
                "night air carries a complex blend of urban nightlife scents",
                "cooling concrete releases the day's stored heat and odors",
                "food, alcohol, and exhaust create a distinctive late evening atmosphere"
            ],
            'atmospheric': [
                "late evening brings a sense of urban adventure",
                "the air feels alive with entertainment and possibility",
                "there's an electric quality to the cool, active night"
            ]
        },
        
        'clear_night': {
            'visual': [
                "deep night wraps the city in darkness punctuated by artificial light",
                "street lamps create islands of illumination in urban shadows",
                "late-night establishments glow like beacons in the quiet darkness"
            ],
            'auditory': [
                "the city settles into its quieter night rhythm",
                "distant traffic provides a low, steady background hum",
                "occasional late-night sounds echo more clearly in the stillness"
            ],
            'olfactory': [
                "cool night air carries concentrated urban scents",
                "the darkness seems to intensify smells of concrete and metal",
                "late-night food vendors add warm, comforting aromas"
            ],
            'atmospheric': [
                "night brings a sense of urban solitude and mystery",
                "the air feels cooler and more intimate",
                "there's a contemplative quality to the quiet darkness"
            ]
        },
        
        'clear_late_night': {
            'visual': [
                "the deep hours paint the city in stark contrasts of light and shadow",
                "only essential lighting remains, creating dramatic urban scenes",
                "the few active windows suggest insomniacs and night shift workers"
            ],
            'auditory': [
                "the city reaches its quietest point with minimal traffic",
                "night shift machinery and distant sounds carry clearly",
                "occasional sirens or late vehicles stand out against the silence"
            ],
            'olfactory': [
                "cold air sharpens urban scents into distinct, clear notes",
                "industrial night operations add their own distinctive odors",
                "the smell of empty streets and cooling concrete dominates"
            ],
            'atmospheric': [
                "late night carries a sense of urban isolation",
                "the air feels thin and crisp with possibility",
                "there's something both lonely and peaceful in the stillness"
            ]
        },

        # Rain weather
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
        
        # Torrential Rain (extreme)
        'torrential_rain_night': {
            'visual': [
                "sheets of rain cascade down in torrents that transform streets into raging rivers",
                "the deluge overwhelms storm drains and creates urban waterfalls from every rooftop",
                "visibility drops to mere meters as the rain falls like a solid wall of water"
            ],
            'auditory': [
                "the thunderous roar of torrential rain drowns out all other sounds completely",
                "water crashes and gurgles through overwhelmed drainage systems with violent intensity",
                "the storm creates a deafening symphony of liquid percussion against every surface"
            ],
            'olfactory': [
                "the air fills with the overwhelming scent of churned earth and flooded concrete",
                "flood waters carry the mingled odors of the entire urban landscape",
                "ozone and rain-soaked debris create a powerful, almost choking atmosphere"
            ],
            'atmospheric': [
                "the storm transforms the familiar cityscape into an alien water-world of chaos and power",
                "nature's raw fury makes the urban environment feel fragile and temporary",
                "the air vibrates with the primal energy of water reclaiming the concrete jungle"
            ]
        },
        
        # Hot Weather - Flashstorm (extreme heat)
        'flashstorm_midday': {
            'visual': [
                "the air shimmers with brutal heat waves that distort the entire cityscape like a mirage",
                "metal surfaces become untouchable furnaces radiating visible waves of scorching air",
                "the sun blazes down with merciless intensity that bleaches color from everything"
            ],
            'auditory': [
                "the oppressive silence of extreme heat broken only by the ping and crack of expanding metal",
                "air conditioning systems strain and whine desperately against the overwhelming temperature",
                "the very air seems to hiss and whisper with the sound of evaporating moisture"
            ],
            'olfactory': [
                "superheated concrete and asphalt release acrid chemical smells that burn the nostrils",
                "the air carries the metallic taste of overheated machinery and baking urban surfaces",
                "waves of heat bring the sharp scent of sun-baked garbage and industrial chemicals"
            ],
            'atmospheric': [
                "the heat presses down like a physical weight that makes every breath an effort",
                "the city becomes a furnace that radiates stored solar energy from every surface",
                "the oppressive temperature transforms the urban environment into a hellscape of concrete and steel"
            ]
        },
        
        # Cold Weather - Blizzard (extreme)
        'blizzard_night': {
            'visual': [
                "howling winds drive sheets of snow horizontally through the urban canyon",
                "the blizzard transforms the city into a white void where visibility drops to arm's length",
                "ice forms instantly on every surface while snow piles into massive drifts against buildings"
            ],
            'auditory': [
                "the blizzard roars with primal fury that drowns out all other sounds in its icy symphony",
                "wind shrieks through building gaps and around corners with banshee-like intensity",
                "the storm creates a constant howl punctuated by the crack of ice and flying debris"
            ],
            'olfactory': [
                "the air carries the clean, sharp scent of pure snow mixed with the metallic bite of extreme cold",
                "frozen precipitation brings the sterile smell of sub-zero temperatures that numbs the senses",
                "the blizzard strips away all warm scents, leaving only the crystalline purity of arctic air"
            ],
            'atmospheric': [
                "the storm transforms the city into an arctic wasteland where survival becomes the only priority",
                "nature's frozen fury makes the urban environment feel hostile and alien",
                "the blizzard brings a primal cold that penetrates to the bone and soul"
            ]
        },
        
        # Soft Snow (moderate cold)
        'soft_snow_early_morning': {
            'visual': [
                "gentle snowflakes drift down like urban confetti, coating the city in pristine white",
                "the fresh snow muffles the harsh edges of concrete and steel with soft curves",
                "morning light reflects off the snow cover, creating an almost ethereal urban landscape"
            ],
            'auditory': [
                "the city sounds muffled and distant beneath the soft blanket of falling snow",
                "footsteps crunch softly through the accumulated powder with rhythmic precision",
                "the snow creates a peaceful hush that transforms the usual urban cacophony"
            ],
            'olfactory': [
                "the air carries the clean, crisp scent of fresh snow and winter purity",
                "cold air brings sharp clarity that makes every breath feel cleansing",
                "the snow masks urban odors with the neutral scent of frozen precipitation"
            ],
            'atmospheric': [
                "the gentle snowfall creates a sense of peace and temporary beauty in the urban setting",
                "the cold brings invigorating clarity that sharpens awareness and focus",
                "the winter scene transforms the city into something almost magical and serene"
            ]
        },
        
        # Sandstorm (extreme)
        'sandstorm_afternoon': {
            'visual': [
                "walls of gritty dust and debris roar through the urban canyon like a brown tsunami",
                "the sandstorm reduces visibility to zero while coating everything in abrasive particles",
                "the air becomes a choking cloud of dust that transforms day into an apocalyptic twilight"
            ],
            'auditory': [
                "the storm howls with the sound of millions of sand grains abrading against concrete and metal",
                "wind-driven debris rattles and crashes against buildings with machine-gun intensity",
                "the sandstorm creates a constant roar punctuated by the impact of flying urban detritus"
            ],
            'olfactory': [
                "the air fills with the gritty taste and smell of pulverized concrete, metal, and organic debris",
                "dust carries the accumulated scents of the entire city in a choking, abrasive mixture",
                "the storm brings the sharp, mineral smell of abraded stone and industrial particles"
            ],
            'atmospheric': [
                "the sandstorm transforms the city into an alien landscape of swirling, abrasive chaos",
                "the storm brings a primal sense of nature's power to scour and reshape the urban environment",
                "the air itself becomes hostile, turning every breath into a battle against the elements"
            ]
        },
        
        # Fog (moderate)
        'fog_dawn': {
            'visual': [
                "thick fog rolls through the urban canyon, reducing the city to ghostly silhouettes",
                "moisture beads on every surface while the mist transforms familiar landmarks into mysteries",
                "the fog creates an intimate world where nothing exists beyond a few meters of gray visibility"
            ],
            'auditory': [
                "sounds become muffled and directionless in the thick, moisture-laden air",
                "the fog seems to absorb noise, creating pockets of eerie silence and unexpected sound",
                "distant noises emerge from the mist without warning, then fade back into gray obscurity"
            ],
            'olfactory': [
                "the air carries the damp, neutral scent of water vapor mixed with urban undertones",
                "moisture brings out subtle smells from concrete, metal, and hidden corners of the city",
                "the fog creates a humid atmosphere that intensifies both pleasant and unpleasant odors"
            ],
            'atmospheric': [
                "the fog creates a sense of isolation and mystery in the middle of the urban landscape",
                "visibility becomes a precious commodity in the gray, moisture-heavy environment",
                "the mist transforms the city into a dreamscape where reality feels soft and uncertain"
            ]
        },
        
        # Tox Rain (intense)
        'tox_rain_evening': {
            'visual': [
                "acid rain falls in corrosive droplets that eat away at metal surfaces and paint",
                "the toxic precipitation leaves ugly stains and steam wherever it touches organic matter",
                "warning lights flicker as the caustic rainfall damages exposed electrical systems"
            ],
            'auditory': [
                "the toxic rain hisses and bubbles as it makes contact with reactive surfaces",
                "metal corrodes audibly under the assault of the caustic precipitation",
                "emergency sirens wail in the distance as the city responds to the chemical threat"
            ],
            'olfactory': [
                "the air reeks with the sharp, burning smell of industrial chemicals and acid",
                "toxic vapors rise from every surface touched by the corrosive rainfall",
                "the atmosphere carries the metallic tang of dissolved metals and burning organic compounds"
            ],
            'atmospheric': [
                "the toxic rain transforms the city into a hazardous chemical wasteland",
                "every breath feels dangerous as the air fills with caustic vapors",
                "the environment becomes actively hostile to all forms of life and machinery"
            ]
        },
        
        # Gray Pall (intense)
        'gray_pall_midday': {
            'visual': [
                "a thick, choking gray haze blots out the sun and reduces the world to sepia tones",
                "the oppressive smog hangs like a funeral shroud over the entire cityscape",
                "visibility drops to a few blocks as the toxic atmosphere obscures all distant landmarks"
            ],
            'auditory': [
                "the heavy air muffles all sounds, creating an oppressive silence broken only by coughing",
                "air filtration systems work overtime with a constant mechanical wheeze and rattle",
                "the city sounds sick and struggling beneath the weight of the poisoned atmosphere"
            ],
            'olfactory': [
                "the air carries the acrid stench of burning chemicals, industrial waste, and organic decay",
                "every breath brings the taste of ash, metal particles, and unidentifiable toxins",
                "the atmosphere feels thick and oily with the accumulated pollution of urban excess"
            ],
            'atmospheric': [
                "the gray pall creates a sense of environmental apocalypse and systemic failure",
                "the poisoned air makes survival feel precarious and every breath a calculated risk",
                "the city feels like it's drowning in its own industrial excess and toxic legacy"
            ]
        },
        
        # Windy (mild)
        'windy_afternoon': {
            'visual': [
                "strong gusts whip through the urban canyon, sending debris dancing through the air",
                "wind catches loose papers and trash, creating impromptu tornadoes of urban detritus",
                "building flags and signs flutter frantically in the persistent breeze"
            ],
            'auditory': [
                "wind whistles through gaps between buildings with varying pitch and intensity",
                "loose objects rattle and bang as the gusts push them against walls and barriers",
                "the constant breeze creates a background symphony of urban wind chimes and percussion"
            ],
            'olfactory': [
                "the moving air carries a mixture of scents from different parts of the city",
                "wind brings brief whiffs of distant cooking, exhaust, and industrial processes",
                "the breeze keeps the air fresh and prevents stagnant odors from settling"
            ],
            'atmospheric': [
                "the wind brings energy and movement to the otherwise static urban environment",
                "the constant breeze creates a sense of change and motion in the concrete landscape",
                "the moving air makes the city feel alive and dynamic despite its rigid structure"
            ]
        }
    }
}
