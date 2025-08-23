"""
Search and multimatch handling

This module provides custom search functionality that extends Evennia's
default search system to support ordinal numbers (1st, 2nd, 3rd, etc.)
in addition to the standard dash-number format (sword-1, sword-2, etc.).

This allows players to use either:
- get sword-1    (existing Evennia format)
- get 1st sword  (new ordinal format)

To use this module, add the following line to your settings file:
    SEARCH_AT_RESULT = "server.conf.at_search.at_search_result"

"""

import re
from collections import defaultdict
from django.utils.translation import gettext as _
from evennia.utils.utils import at_search_result as evennia_at_search_result


# Ordinal number mappings
ORDINAL_REGEX = re.compile(r'(?P<number>\d+)(?:st|nd|rd|th)\s+(?P<name>.*)', re.I)
ORDINAL_WORDS = {
    'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
    'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
    '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6,
    '7th': 7, '8th': 8, '9th': 9, '10th': 10, '11th': 11, '12th': 12,
    '13th': 13, '14th': 14, '15th': 15, '16th': 16, '17th': 17,
    '18th': 18, '19th': 19, '20th': 20
}


def try_ordinal_differentiators(raw_string):
    """
    Test if user tried to separate multi-matches with ordinal numbers
    (1st sword, 2nd ball, third mushroom, etc).
    
    Args:
        raw_string (str): The user input to parse.
        
    Returns:
        tuple: (match_index, new_raw_string) if ordinal found, (None, None) otherwise.
        match_index is 0-based (so "1st" returns 0, "2nd" returns 1, etc.)
        
    Examples:
        "1st sword" -> (0, "sword")
        "2nd ball" -> (1, "ball") 
        "third mushroom" -> (2, "mushroom")
        "10th item" -> (9, "item")
    """
    raw_string = raw_string.strip()
    
    # Try numeric ordinals first (1st, 2nd, 3rd, etc.)
    ordinal_match = ORDINAL_REGEX.match(raw_string)
    if ordinal_match:
        number = int(ordinal_match.group('number'))
        name = ordinal_match.group('name').strip()
        if number > 0:  # Convert 1-based to 0-based index
            return number - 1, name
    
    # Try word ordinals (first, second, third, etc.)
    words = raw_string.split()
    if len(words) >= 2:
        first_word = words[0].lower()
        if first_word in ORDINAL_WORDS:
            remaining_words = ' '.join(words[1:])
            return ORDINAL_WORDS[first_word] - 1, remaining_words
    
    return None, None


def at_search_result(matches, caller, query="", quiet=False, **kwargs):
    """
    Custom search result handler that supports both Evennia's default
    dash-number format (sword-1) and ordinal numbers (1st sword).
    
    This is called when object searches return multiple matches or no matches.
    It handles error messaging and allows users to disambiguate using either:
    - Traditional: get sword-1, get sword-2
    - Ordinal: get 1st sword, get 2nd sword
    
    Args:
        matches (list): List of matched objects
        caller (Object): The object performing the search
        query (str): The original search string
        quiet (bool): If True, don't display error messages
        **kwargs: Additional arguments
        
    Returns:
        Object or None: Single matched object, or None if error handled
    """
    
    # First, check if the query contains an ordinal differentiator
    match_index, base_query = try_ordinal_differentiators(query)
    if match_index is not None and matches:
        # User specified an ordinal like "1st sword" or "second mushroom"
        if 0 <= match_index < len(matches):
            return matches[match_index]
        else:
            # Ordinal number is out of range
            if not quiet:
                caller.msg(f"Only {len(matches)} matches found for '{base_query}', "
                          f"but you specified the {_ordinal_suffix(match_index + 1)} one.")
            return None
    
    # If no ordinal found, or if it's not a multimatch situation, 
    # use Evennia's default handler which already handles dash-number format
    result = evennia_at_search_result(matches, caller, query, quiet, **kwargs)
    
    # If it's a multimatch error, enhance the message to show ordinal options
    if not quiet and not result and matches and len(matches) > 1:
        _show_enhanced_multimatch_message(matches, caller, query)
        return None
        
    return result


def _ordinal_suffix(number):
    """
    Convert a number to its ordinal form (1st, 2nd, 3rd, etc.)
    
    Args:
        number (int): The number to convert
        
    Returns:
        str: The ordinal form (e.g., "1st", "2nd", "3rd")
    """
    if 10 <= number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
    return f"{number}{suffix}"


def _show_enhanced_multimatch_message(matches, caller, query):
    """
    Show an enhanced multimatch message that includes both traditional
    dash-number format and ordinal number examples.
    
    Args:
        matches (list): List of matched objects
        caller (Object): The object performing the search  
        query (str): The original search string
    """
    
    # Group results by display name to properly disambiguate
    grouped_matches = defaultdict(list)
    for item in matches:
        group_key = (
            item.get_display_name(caller) if hasattr(item, "get_display_name") else query
        )
        grouped_matches[group_key].append(item)

    error_lines = [f"More than one match for '{query}' (please narrow target):"]
    
    for key, match_list in grouped_matches.items():
        for num, result in enumerate(match_list):
            # Get aliases for display
            if hasattr(result.aliases, "all"):
                # Typeclassed entity where .aliases is an AliasHandler
                aliases = result.aliases.all(return_objs=True)
                aliases = [alias.db_key for alias in aliases if alias.db_category != "plural_key"]
            else:
                # Likely a Command where .aliases is a list of strings
                aliases = result.aliases or []

            # Traditional dash-number format
            alias_str = f" [{';'.join(aliases)}]" if aliases else ""
            error_lines.append(f" {key}-{num + 1}{alias_str}")

    # Add helpful hint about ordinal usage
    if len(matches) <= 5:  # Only show ordinal examples for small lists
        error_lines.append("")
        error_lines.append("You can also use ordinal numbers:")
        for i in range(min(3, len(matches))):  # Show first few examples
            ordinal = _ordinal_suffix(i + 1)
            error_lines.append(f" get {ordinal} {query}")
    
    caller.msg("\n".join(error_lines))
