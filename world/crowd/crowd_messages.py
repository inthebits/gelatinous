"""
Crowd system message pools following weather system architecture.
Provides atmospheric crowd descriptions for different density levels.
"""

# Crowd level intensity mapping
CROWD_INTENSITY = {
    0: 'none',      # No crowd messages
    1: 'sparse',    # Light crowd presence (6-10 word messages)
    2: 'moderate',  # Noticeable crowd activity (10-14 word messages)
    3: 'heavy',     # Busy crowd presence (14-18 word messages)
    4: 'packed',    # Dense crowd activity (18+ word messages)
}

CROWD_MESSAGES = {
    'default': {
        'sparse': {
            'visual': [
                "occasional pedestrians move purposefully along the street",
                "a few people drift past with measured, unhurried steps",
                "sparse foot traffic creates pockets of solitary space",
                "people maintain comfortable distances as they navigate",
                "scattered individuals move through the area independently"
            ],
            'auditory': [
                "occasional footsteps echo softly against concrete surfaces",
                "isolated conversations drift past before fading away",
                "the sound of individual movement punctuates the quiet",
                "distant voices blend into the background urban hum",
                "footfalls create sporadic rhythms on the pavement"
            ],
            'atmospheric': [
                "there's breathing room despite the urban setting",
                "a sense of personal space prevails among passersby",
                "the area feels populated but not crowded",
                "people move with unhurried, comfortable pacing",
                "individual presence doesn't overwhelm the space"
            ]
        },
        'moderate': {
            'visual': [
                "foot traffic starts to build with people moving in both directions",
                "pedestrians weave around each other with practiced urban navigation",
                "the flow of people creates subtle patterns of movement",
                "groups and individuals share the space in comfortable density",
                "people maintain awareness of others while pursuing their destinations"
            ],
            'auditory': [
                "conversations blend into a soft murmur of human activity",
                "footsteps create layered rhythms as people pass by",
                "the sound of movement builds into gentle urban symphony",
                "voices rise and fall as groups move through the area",
                "ambient human sounds add life to the urban backdrop"
            ],
            'atmospheric': [
                "there's a building energy as human activity increases",
                "the space feels alive with comfortable levels of occupation",
                "people move with purpose while remaining aware of others",
                "a sense of community presence without overwhelming density",
                "the area pulses with moderate but manageable human energy"
            ]
        },
        'heavy': {
            'visual': [
                "people shoulder past each other in the increasingly dense foot traffic",
                "pedestrians navigate through thickening crowds with practiced efficiency",
                "the constant flow of bodies creates shifting patterns of movement",
                "groups cluster and disperse as people work around each other",
                "individual space shrinks as the human density noticeably increases"
            ],
            'auditory': [
                "a steady mix of conversations creates persistent human noise",
                "footsteps merge into constant rhythmic movement on pavement",
                "voices overlap and blend into urban crowd symphony",
                "the sound of many people moving creates energetic backdrop",
                "human activity generates sustained ambient noise levels"
            ],
            'atmospheric': [
                "bustling energy fills the space as crowd density builds",
                "there's urban intensity as personal space becomes premium",
                "the area thrums with human activity and movement",
                "people adapt their pace to accommodate increasing density",
                "social awareness heightens as the crowd thickens around you"
            ]
        },
        'packed': {
            'visual': [
                "dense crowds press together as people navigate the heavily congested space",
                "bodies move in constrained patterns as the human flow reaches capacity",
                "pedestrians squeeze past each other in the tightly packed environment",
                "the sheer volume of people creates slow-moving human rivers through available space",
                "individual movement becomes challenging as the crowd density approaches uncomfortable levels"
            ],
            'auditory': [
                "the constant hum of many voices creates overwhelming acoustic presence throughout the area",
                "footsteps, conversations, and movement blend into sustained human cacophony",
                "sound levels rise dramatically as packed crowds generate persistent noise",
                "individual voices disappear into the collective audio wall of human activity",
                "the acoustic signature shifts to dense, layered human presence that dominates the soundscape"
            ],
            'atmospheric': [
                "the oppressive weight of human density creates palpable tension in the confined space",
                "personal boundaries dissolve as the packed crowd forces uncomfortably close proximity",
                "there's an electric intensity as too many people occupy limited space simultaneously",
                "the energy becomes claustrophobic as individual comfort zones collapse under crowd pressure",
                "social stress builds as the human density exceeds comfortable limits for most people"
            ]
        }
    }
}

def get_crowd_messages(crowd_level, message_category='all'):
    """
    Get crowd messages for specified level and category.
    
    Args:
        crowd_level (int): Crowd level (0-4+)
        message_category (str): 'visual', 'auditory', 'atmospheric', or 'all'
        
    Returns:
        dict or list: Message pools for the crowd level
    """
    intensity = CROWD_INTENSITY.get(crowd_level, 'packed')
    
    if intensity == 'none':
        return {} if message_category == 'all' else []
    
    if intensity not in CROWD_MESSAGES['default']:
        intensity = 'packed'  # Fallback for very high crowd levels
    
    crowd_pool = CROWD_MESSAGES['default'][intensity]
    
    if message_category == 'all':
        return crowd_pool
    elif message_category in crowd_pool:
        return crowd_pool[message_category]
    else:
        return []
