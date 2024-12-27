from enum import Enum

class Ability(Enum):
	"""
	The four base ability-bonuses and other
	abilities
	
	"""

	GRT = "grit"
	RES = "resonance"
	INT = "intellect"
	MOT = "motorics"
	
ABILITY_REVERSE_MAP =  {
		"grt": Ability.GRT,
		"res": Ability.RES,
		"int": Ability.INT,
		"mot": Ability.MOT
	}