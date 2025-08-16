# Enhanced Look Command System Specification

## Overview

The enhanced look command system assembles rich, dynamic environmental descriptions through component-based sensory integration. The system builds upon the existing `return_appearance` method, combining sensory categories with modular description components that automatically assemble into cohesive room narratives.

## Current Implementation

**Existing Features:**
- Basic room description with name and desc
- Character and object listing via Evennia templates
- Custom exit categorization (regular exits vs. edges/gaps) 
- Flying object integration for throw mechanics
- Sky room filtering for exit display

**Current `return_appearance` Method:**
- Uses appearance template with header/name/desc/characters/things/footer
- Adds flying objects during throw mechanics
- Delegates exit display to custom footer method
- Filters sky room exits unless they're edges/gaps

## Enhanced System Architecture

### 1. Sensory Category Framework

**Core Sensory Categories:**
- **Visual**: Lighting, colors, visual effects, environmental details
- **Auditory**: Ambient sounds, distant noises, activity sounds
- **Olfactory**: Scents, odors, atmospheric smells
- **Tactile**: Temperature, humidity, air movement, surface textures
- **Atmospheric**: General mood, tension, environmental pressure

**Sensory Category Implementation:**
- **Equal Priority**: All sensory categories treated with equal importance
- **Artful Combination**: Room can be described three ways, then combined non-redundantly
- **Graceful Degradation**: Categories with no content simply don't display
- **Medical Condition Support**: By design - players with sensory limitations see reduced content
- **Complementary Description**: Multiple approaches to describing same space, combined artfully

### 2. Component-Based Description Assembly

**Assembly Order:**
1. **Room Name & Base Description**: Foundation sensory content
2. **@integrate Object Integration**: Objects stacked at end of room description
3. **Weather System Contribution**: Current weather sensory additions
4. **Crowd System Contribution**: Current crowd level sensory additions
5. **Traditional Object Listing**: Non-integrated objects listed separately
6. **Smart Exit Descriptions**: Context-aware exit information

### 3. @integrate Object System

**Integration Mechanism:**
Objects with `@integrate` attribute appear at end of room description, stacking together without limits.

**Integration Stacking:**
- **No Limits**: All @integrate objects display together
- **Stacking Order**: Objects stack in discovery/creation order
- **No Conflicts**: Multiple objects contributing similar content is acceptable
- **End Positioning**: @integrate content appears after base room description but before weather/crowds

**Enhanced Integration by Sensory Category:**
- **Visual Integration**: "bullet-ridden vehicles pass through", "colorful graffiti"
- **Auditory Integration**: Engine sounds, crowd noise, activity sounds
- **Olfactory Integration**: Vehicle exhaust, food smells, industrial odors
- **Tactile Integration**: Surface textures, temperature effects
- **Atmospheric Integration**: Tension, mood contributions

**Special Integration Systems:**
- **Graffiti System**: @integrate items with enhanced code logic for procedural variety
- **Vehicle System**: Moving objects that contribute dynamic sensory elements
- **Art/Architecture**: Static integrated elements adding atmosphere

### 4. Dynamic Message Pool Systems

**Weather System Design:**
Similar to combat message system architecture:
```python
weather_messages = {
    'rain': {
        'visual': ['acid rain falls from the platform above', 'moisture beads on metal surfaces'],
        'auditory': ['steady patter of raindrops', 'water dripping from overhangs'],
        'olfactory': ['petrichor mixed with industrial chemicals', 'wet concrete smell'],
        'tactile': ['cool dampness in the air', 'humidity clings to skin'],
        'atmospheric': ['oppressive gray atmosphere', 'dreary weather mood']
    },
    'clear': {
        'visual': ['harsh sunlight glints off metal', 'clear visibility'],
        'auditory': ['distant city hum more audible', 'no rain interference'],
        # ... etc
    }
}
```

**Crowd System Design:**
```python
crowd_messages = {
    'heavy': {
        'visual': ['people shoulder past each other', 'constant movement'],
        'auditory': ['mix of conversations', 'footsteps echo'],
        'atmospheric': ['bustling energy', 'urban intensity']
    },
    'moderate': {
        'visual': ['foot traffic starting to get heavy', 'still have personal space'],
        'auditory': ['occasional conversation fragments', 'moderate activity'],
        'atmospheric': ['building energy', 'comfortable activity level']
    }
}
```

**Message Selection System:**
- **Per Look Command**: New random selection each time room is looked at
- **Combat Message Architecture**: Uses room variables + weather system variables to select from description pools
- **No Weighting**: Equal probability for all messages in pool
- **Variable-Driven Selection**: Room attributes + weather state inform available message pools

**Message Pool Structure:**
```python
weather_pools = {
    'rain_heavy': {
        'visual': [pool of visual rain messages],
        'auditory': [pool of auditory rain messages],
        'tactile': [pool of tactile rain messages]
    }
}
# Selection based on: room.weather_intensity + weather_system.current_state
```

### 5. Smart Exit System Enhancement

**Room Type System:**
- **Storage**: `room.db.type` attribute for room classification
- **Auto-Detected Types**: `street`, `intersection`, `dead-end` (based on adjacent room analysis)
- **Custom Types**: `courier service`, `cube hotel`, `hospital`, `stairway` (builder-defined)
- **Integration**: Auto-detected and custom types work together for mixed scenarios

**Auto-Detection Rules:**
- **Intersection**: 3+ exits leading to rooms with `type="street"`
- **Dead-end**: 1 exit from a room with `type="street"`
- **Street**: Connected to other street-type rooms in linear fashion

**Natural Language Exit Patterns:**
1. **Grouped by Type**: "The street continues north and south"
2. **Individual Destinations**: "There is a courier service to the west and a cube hotel to the east"
3. **Mixed Integration**: "The street continues north. There is a hospital to the east and an edge to the south"
4. **Fallback Format**: "There is an exit to the south (s)" when no type information available

**Exit Display Examples:**
```
Example 1 (Mixed types):
"The street continues south and north. There is a courier service to the west and a cube hotel to the east."

Example 2 (Utilitarian/Complex):  
"There are exits to the east (e), west (w), C01 (01), C02 (02), C03 (03), C04 (04), C05 (05), C06 (06)."

Example 3 (Simple mixed):
"The street continues north. There is an intersection to the south and a stairway to the west."
```

**Alias Integration:**
- **Standard Format**: "north (n)" - shows direction and first alias
- **No Alias**: "north" - omits parentheses when no alias exists
- **Complex Exits**: Custom exit names with their primary alias

**Edge/Gap Integration:**
- **Natural Language**: "There is an edge to the south and west"
- **Mixed Content**: Edges integrated with other exit types naturally
- **Multiple Edges**: Grouped using natural language conjunctions

**Implementation Logic:**
1. **Analyze Destinations**: Check each exit's destination `room.db.type`
2. **Group by Type**: Collect exits leading to same destination types
3. **Apply Grouping Rules**: "street continues" for multiple street destinations
4. **Format Individual Types**: "There is a [type] to the [direction]"
5. **Integrate Edges/Gaps**: Include in natural language flow
6. **Fallback Handling**: Use generic format for unknown types

### 6. Character Integration Enhancement

**Sensory-Aware Character Descriptions:**
- **Visual**: Equipment, posture, condition visible elements
- **Auditory**: Character-generated sounds, movement noise
- **Atmospheric**: How characters affect room tension/mood

**Integration with Existing Systems:**
- **Hand/Inventory System**: What characters are visibly holding
- **Combat System**: Character condition affects their sensory contribution
- **Proximity System**: Character positioning and interactions

## Technical Implementation Details

### Message Pool Architecture

**System Design:**
```python
# Message pool structure following combat system patterns
weather_pools = {
    'clear_visual': [
        "clear evening sky shows above",
        "streetlights cast steady pools of amber light", 
        "shadows are sharp and well-defined"
    ],
    'rain_auditory': [
        "steady patter of rain on concrete",
        "splash of tires through puddles",
        "water dripping from gutters and awnings"
    ],
    'rain_tactile': [
        "dampness in the air",
        "cool moisture on exposed skin",
        "slick surfaces underfoot"
    ]
}

crowd_pools = {
    'sparse_atmospheric': [
        "quiet emptiness broken by occasional footsteps",
        "sense of solitude in urban space", 
        "echoes carry further in the empty air"
    ],
    'heavy_auditory': [
        "constant murmur of conversations",
        "shuffle and scrape of many feet",
        "occasional burst of laughter or shouting"
    ]
}
```

**Selection Mechanics:**
- Fresh random selection per look command (like combat messages)
- Optional probability weights for rare/common messages
- Variable substitution for dynamic content
- Conditional pools based on environmental state

### Component Integration System

**Assembly Order:**
1. **Room Name**: Static title
2. **Base Description**: Core room visual content  
3. **@integrate Objects**: Stacked at end of room description text
4. **Sensory Layer Assembly**: Weather/crowd/atmospheric content
5. **Character Listings**: Enhanced character descriptions
6. **Traditional Objects**: Remaining visible objects
7. **Exit Information**: Smart categorized exits

**Integration Processing:**
```python
def assemble_room_description(self, looker):
    components = []
    
    # 1. Base room description
    components.append(self.get_base_description())
    
    # 2. @integrate objects (stack at end of base description)
    integrate_content = self.get_integrated_objects()
    if integrate_content:
        components[-1] += " " + integrate_content
    
    # 3. Sensory layer assembly
    sensory_content = self.assemble_sensory_layers(looker)
    if sensory_content:
        components.append(sensory_content)
    
    # 4. Character descriptions  
    char_content = self.get_enhanced_character_descriptions(looker)
    if char_content:
        components.append(char_content)
    
    # 5. Traditional objects
    obj_content = self.get_traditional_objects(looker)
    if obj_content:
        components.append(obj_content)
    
    # 6. Exit information
    exit_content = self.get_smart_exits(looker)
    if exit_content:
        components.append(exit_content)
    
    return "\n\n".join(components)
```

**Performance Considerations:**
- Message pool evaluation happens per look command for freshness
- Static content caching where appropriate  
- Efficient variable substitution system
- Minimal database queries for dynamic content
- Graceful degradation when components unavailable

## Technical Implementation

### Enhanced Room Attributes

**Sensory Message Storage:**
```python
# Base sensory content
base_sensory = {
    'visual': "pungent smell floods your nostrils",
    'auditory': "sounds of traffic and urban activity", 
    'olfactory': "sewage and raw garbage",
    'tactile': "acidic moisture in the air",
    'atmospheric': "tension of dangerous territory"
}

# Integration settings
integration_settings = {
    'allow_weather': True,
    'allow_crowds': True,
    'weather_intensity': 'normal',
    'crowd_base_level': 'moderate'
}

# Room type for smart exit labeling
room.db.type = 'street'  # Can be auto-detected or manually set
# Auto-detected: 'street', 'intersection', 'dead-end'
# Custom: 'courier service', 'cube hotel', 'hospital', 'stairway', etc.
```

**Smart Exit Implementation:**
```python
def get_smart_exit_description(self, looker):
    """Generate natural language exit descriptions."""
    
    # Group exits by destination type and special properties
    exit_groups = {
        'streets': [],
        'edges': [],
        'gaps': [],
        'custom_types': {},
        'fallback': []
    }
    
    # Analyze each exit
    for exit_obj in self.exits:
        direction = exit_obj.key
        alias = exit_obj.aliases[0] if exit_obj.aliases else None
        destination = exit_obj.destination
        
        # Check for edge/gap first
        if getattr(exit_obj.db, "is_edge", False):
            exit_groups['edges'].append((direction, alias))
        elif getattr(exit_obj.db, "is_gap", False):
            exit_groups['gaps'].append((direction, alias))
        # Check destination type
        elif destination and hasattr(destination.db, 'type'):
            dest_type = destination.db.type
            if dest_type == 'street':
                exit_groups['streets'].append((direction, alias))
            else:
                if dest_type not in exit_groups['custom_types']:
                    exit_groups['custom_types'][dest_type] = []
                exit_groups['custom_types'][dest_type].append((direction, alias))
        else:
            # Fallback for exits without type information
            exit_groups['fallback'].append((direction, alias))
    
    # Generate natural language descriptions
    return self.format_exit_groups(exit_groups)
```

### Enhanced return_appearance Method

**Assembly Process:**
1. **Initialize Sensory Categories**: Start with base room sensory content
2. **Process @integrate Objects**: Add object sensory contributions to categories
3. **Apply Weather System**: Add current weather sensory messages
4. **Apply Crowd System**: Add current crowd sensory messages  
5. **Assemble Narrative**: Combine sensory categories into flowing description
6. **Add Traditional Objects**: List non-integrated objects separately
7. **Add Smart Exits**: Context-aware exit descriptions
8. **Apply Player Filters**: Modify based on player condition/equipment

**Method Signature:**
```python
def return_appearance(self, looker, **kwargs):
    """
    Enhanced appearance method with component-based sensory assembly.
    
    Assembles room description from:
    - Base room description and sensory content
    - @integrate objects woven into narrative  
    - Weather system sensory contributions
    - Crowd system sensory contributions
    - Smart exit descriptions
    - Traditional object listings
    
    Args:
        looker: Character looking at the room
        **kwargs: Additional parameters for customization
        
    Returns:
        str: Assembled room description with all components
    """
```

## Component System Details

### @integrate Object System

**Object Integration Attributes:**
```python
# On objects that should integrate into room description
@integrate = True
integration_priority = 10  # Higher = appears earlier in description
sensory_contributions = {
    'visual': "bullet-ridden vehicles pass through",
    'auditory': "engine noise and grinding gears",
    'atmospheric': "sense of urban danger"
}
```

**Integration Processing:**
- Objects with `@integrate = True` contribute to room description
- Priority determines integration order
- Sensory contributions added to appropriate categories
- Objects do not appear in traditional object listing

### Weather System Integration

**Weather State Management:**
- Current weather state affects all sensory categories
- Message pools provide variety like combat system
- Weather intensity affects message selection
- Integration with room base description

### Crowd System Integration

**Crowd Level Management:**
- Dynamic crowd levels: sparse, moderate, heavy, packed
- Each level has message pools for different sensory categories
- Crowd messages add to atmospheric and auditory primarily
- Integration with character listing and social dynamics

### Smart Exit Enhancement

**Exit Context Detection:**
- Analyze destination room types to determine exit labels
- Auto-detect intersections, dead ends, special areas
- Allow manual override for custom labeling
- Integrate exit information into room narrative flow

## Example Implementation

**Component Assembly Example:**
```
Base Room: "Large intersection where Sinn crosses Knife"
+ Weather (acid rain): "dismal acidic shower falls from platform above"  
+ Crowd (moderate): "foot traffic starting to get heavy but personal space"
+ @integrate Vehicles: "bullet-ridden vehicles pass through on drive-bys"
+ @integrate Graffiti: "walls daubed with colorful graffiti"
+ Traditional Objects: "You see a flyer [Nyrek the Unwired]"
+ Smart Exits: "street to the south/west/east" (intersection detected)
= Final assembled description
```

## Integration Points

### Weather System Integration
- Weather contributes to all sensory categories
- Message pools rotated like combat messages
- Conditional effects based on room type and settings

### Crowd System Integration  
- Crowd levels affect atmospheric and auditory categories
- Character interactions influenced by crowd density
- Dynamic social context for room descriptions

### Combat System Integration
- Character condition affects perception and sensory input
- Weapon visibility integrated with character descriptions
- Proximity system affects social positioning descriptions

### Inventory System Integration
- @integrate objects blend into room narrative
- Traditional objects listed separately
- Hand system integration for character equipment visibility

## Future Extensions

### Advanced Component Systems
- **Economic Activity**: Market sounds, commercial atmosphere
- **Security Level**: Patrol presence, safety indicators  
- **Time Cycling**: Day/night variations in all systems
- **Seasonal Changes**: Long-term environmental variations

### Enhanced Integration
- **Cross-Component Effects**: Weather affecting crowd behavior
- **Player Influence**: How player actions affect room atmosphere
- **Historical Layering**: Past events affecting current descriptions
- **Dynamic Events**: Real-time events integrated into descriptions

## Technical Implementation

### Enhanced Room Attributes

**New Room Properties:**
```python
# Sensory message storage
sensory_messages = {
    'visual': ['dim lighting', 'shadows in corners'],
    'auditory': ['distant traffic', 'muffled conversations'],
    'olfactory': ['stale air', 'hint of smoke'],
    'tactile': ['cool dampness', 'sticky humidity'],
    'atmospheric': ['tense quiet', 'underlying unease']
}

# Environmental conditions
environmental_state = {
    'weather': 'clear',
    'time_of_day': 'evening',
    'crowd_level': 'sparse',
    'activity_level': 'low'
}

# Building/design theme
room_theme = {
    'style': 'industrial',
    'condition': 'deteriorating',
    'lighting': 'artificial',
    'size': 'medium'
}
```

### Enhanced return_appearance Method

**Method Signature:**
```python
def return_appearance(self, looker, **kwargs):
    """
    Enhanced appearance method with sensory integration and conditional parsing.
    
    Args:
        looker: Character looking at the room
        **kwargs: Additional parameters for customization
        
    Returns:
        str: Formatted room description with integrated elements
    """
```

**Processing Flow:**
1. **Base Description Assembly**: Static room description
2. **Environmental Assessment**: Current weather, time, conditions
3. **Sensory Layer Selection**: Choose appropriate sensory messages
4. **Character Integration**: Enhanced character descriptions
5. **Object Contextualization**: Objects with interaction hints
6. **Exit Integration**: Descriptive exit information
7. **Atmosphere Addition**: Weather, crowd, ambient activity
8. **Player Filter Application**: Modify based on player conditions
9. **Final Assembly**: Combine all elements into cohesive narrative

### Character Enhancement Integration

**Enhanced Character Display:**
- Integration with existing hand/inventory system
- Weapon and equipment visibility based on wielded items
- Health status integration with combat system
- Proximity system awareness for social positioning

### Object System Integration

**Item Integration:**
- Leverage existing Item typeclass system
- Integration with throw mechanics and flying objects
- Proximity-based interaction hints
- State-aware descriptions

## Command Variations

### Primary Look Command
- `look` - Full room description with all enhancements
- `l` - Alias for look

### Targeted Look Commands  
- `look <character>` - Detailed character examination
- `look <object>` - Detailed object examination
- `examine <target>` - Deep examination with interaction hints

### Sensory Focus Commands
- `listen` - Focus on auditory information
- `smell` - Focus on olfactory information
- `feel` - Focus on tactile information

## Integration Points

### Weather System Integration
- Weather affects all sensory layers
- Temperature impacts tactile descriptions
- Precipitation affects visibility and sound

### Combat System Integration  
- Character status affects perception
- Weapon visibility based on wielded items
- Proximity system affects character positioning

### Inventory System Integration
- Held items affect available interactions
- Equipment affects sensory perception
- Item states visible in descriptions

### Building/Design System Integration
- Room themes affect sensory messages
- Architectural details impact descriptions
- Interactive environment elements

## Example Output

**Current Basic Output:**
```
Braddock Avenue
A wide street stretching north and south.

You see: Nick Kramer

Exits: north, south
Edges: down
```

**Enhanced Output:**
```
Braddock Avenue
A wide street stretching north and south, its cracked asphalt gleaming 
dully under the amber streetlights. Evening shadows pool in doorways 
and alcoves along the sidewalk.

The cool evening air carries hints of exhaust and distant cooking, while 
the soft murmur of traffic drifts from the main thoroughfare. A light 
breeze stirs loose papers along the gutter.

Nick Kramer stands near the center of the street, his Colt M1911 pistol 
held ready in his right hand. He appears alert, scanning the shadows 
with the practiced wariness of someone expecting trouble.

A manhole cover lies slightly askew near the curb, its edges worn smooth 
by countless footsteps.

The street continues north toward the commercial district and south into 
the residential area. A narrow gap between buildings to the east leads 
down into the underground maintenance tunnels.
```

## Future Extensions

### Scriptable City Generation Support

**Template-Driven Room Generation:**
```python
# Room generation templates for automated city building
room_templates = {
    'street_intersection': {
        'base_description_template': "{{size}} intersection where {{street1}} crosses {{street2}}",
        'sensory_pools': {
            'visual': ['urban_intersection_visual', 'traffic_visual'],
            'auditory': ['traffic_audio', 'urban_ambient'],
            'atmospheric': ['city_energy', 'intersection_mood']
        },
        'required_variables': ['street1', 'street2', 'size'],
        'optional_variables': ['district_type', 'time_period', 'economic_level']
    },
    'commercial_street': {
        'base_description_template': "{{street_name}}, lined with {{business_density}} storefronts",
        'sensory_pools': {
            'visual': ['commercial_visual', 'storefront_variety'],
            'auditory': ['commerce_sounds', 'foot_traffic'],
            'olfactory': ['food_smells', 'urban_scents']
        },
        'auto_integrate_objects': ['signs', 'storefronts', 'street_furniture']
    }
}
```

**Procedural Content Generation:**
- **Message Pool Inheritance**: Child rooms inherit and modify parent pools
- **Variable-Driven Content**: Template variables drive sensory message selection
- **Contextual Integration**: Auto-generate @integrate objects based on room type
- **Thematic Consistency**: Ensure generated content maintains narrative coherence

**Neighborhood-Scale Coordination:**
```python
# District-level coordination for consistent atmosphere
district_themes = {
    'industrial': {
        'ambient_weather_modifier': 'smoggy',
        'crowd_behavior_modifier': 'hurried',
        'base_sensory_palette': ['metallic', 'mechanical', 'industrial'],
        'integration_object_types': ['machinery', 'industrial_debris', 'worker_equipment']
    },
    'residential': {
        'ambient_weather_modifier': 'clean',
        'crowd_behavior_modifier': 'relaxed',
        'base_sensory_palette': ['domestic', 'peaceful', 'lived_in'],
        'integration_object_types': ['personal_items', 'garden_elements', 'home_features']
    }
}
```

**Automated Content Scaling:**
- **Performance Tiers**: Different detail levels for performance optimization
- **Content Density Controls**: Adjust richness based on server load
- **Batch Generation**: Efficient creation of large room networks
- **Consistency Validation**: Automated checks for thematic coherence

### Advanced Features
- **Seasonal Variations**: Descriptions change with game seasons
- **Historical Layering**: Rooms show signs of past events
- **Dynamic Events**: Real-time events affect descriptions
- **Player Memory**: Descriptions change based on player familiarity
- **Procedural Narrative**: AI-assisted content generation for unique descriptions

### Technical Enhancements
- **Caching System**: Optimize description generation
- **Template System**: Modular sensory message management
- **Scripting Integration**: Advanced conditional logic
- **Performance Optimization**: Efficient large-scale description handling
- **Generation API**: Standardized interface for automated room creation

### Automation-Friendly Design Principles

**Separation of Content and Logic:**
```python
# Content pools separate from display logic
class RoomContentManager:
    def __init__(self, room_type, district_theme, variables):
        self.content_pools = self.load_content_pools(room_type)
        self.theme_modifiers = self.load_theme_modifiers(district_theme)
        self.variables = variables
    
    def generate_description_components(self):
        """Generate all components for automated assembly"""
        return {
            'base_description': self.generate_base_description(),
            'sensory_content': self.generate_sensory_content(),
            'integrate_objects': self.generate_integration_objects(),
            'atmospheric_elements': self.generate_atmosphere()
        }
```

**Composable Component Architecture:**
- **Atomic Content Units**: Individual sensory messages as building blocks
- **Combinatorial Assembly**: Mix and match components for variety
- **Inheritance Hierarchies**: District → neighborhood → street → room content flow
- **Override Systems**: Specific rooms can override inherited content

**Data-Driven Configuration:**
```python
# Configuration-driven room generation
automation_config = {
    'content_density': {
        'minimal': {'sensory_messages_per_category': 1, 'integrate_objects_max': 2},
        'rich': {'sensory_messages_per_category': 3, 'integrate_objects_max': 5},
        'maximum': {'sensory_messages_per_category': 5, 'integrate_objects_max': 8}
    },
    'generation_constraints': {
        'performance_budget': 'medium',  # affects complexity of generated content
        'uniqueness_threshold': 0.7,     # how different rooms should be
        'theme_consistency': 'strict'    # how closely to follow district themes
    },
    'scalability_settings': {
        'batch_size': 50,               # rooms to generate per batch
        'cache_generated_content': True,
        'lazy_load_sensory_content': True
    }
}
```

**Validation and Quality Control:**
- **Coherence Checking**: Automated validation of generated content combinations
- **Uniqueness Scoring**: Prevent overly similar adjacent rooms
- **Performance Impact Assessment**: Estimate computational cost of generated rooms
- **Narrative Flow Validation**: Ensure descriptions read naturally

**Extension Points for Automation:**
- **Plugin Architecture**: Third-party content generators
- **Event Hooks**: Callbacks for room generation events
- **Content Validation API**: External quality control systems
- **Generation Metrics**: Track and optimize generation quality

## Implementation Priority

**Phase 1: Foundation**
1. Enhanced return_appearance method with sensory framework
2. Basic sensory message storage and retrieval
3. Simple environmental condition parsing

**Phase 2: Integration**
1. Character enhancement integration
2. Object detail level implementation
3. Weather system integration

**Phase 3: Advanced Features**
1. Complex conditional parsing
2. Dynamic environmental elements
3. Advanced sensory focus commands

**Phase 4: Optimization**
1. Performance optimization
2. Caching systems
3. Template management tools
