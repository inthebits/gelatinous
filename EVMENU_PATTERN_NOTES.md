# EvMenu Pattern Notes - Lessons Learned

**Date:** October 14, 2025  
**Context:** Flash Cloning System character creation menu implementation

---

## The Problem

When implementing text-input nodes in EvMenu (where users type freeform text rather than selecting numbered options), we encountered two critical bugs that revealed important EvMenu behavior patterns.

---

## Bug #1: Blank Input Processing

**Symptom:**
```
Press <Enter> to begin character creation.
> [user presses Enter]
Invalid name: Name must be 2-30 characters.
```

**Root Cause:**
```python
def node(caller, raw_string, **kwargs):
    if raw_string:  # ❌ WRONG - empty string can still trigger this
        # Process input
```

**The Issue:** In Python, `if raw_string:` can be `True` for empty strings in some contexts, particularly in EvMenu's input handling.

**Solution:**
```python
def node(caller, raw_string, **kwargs):
    if raw_string and raw_string.strip():  # ✅ CORRECT
        # Process input - only when actual text entered
```

---

## Bug #2: Node Transition During Input Processing

**Symptom:**
```
What is your FIRST name?
> Akumamitsu
first_char_name_last    ← Debug output of node name!

> Wakka
Command 'Wakka' is not available.  ← Menu exited!
```

**Root Cause:**
```python
def first_char_name_first(caller, raw_string, **kwargs):
    if raw_string and raw_string.strip():
        # Validate and store
        caller.ndb.data['first_name'] = raw_string.strip()
        return "first_char_name_last"  # ❌ WRONG!
    
    text = "What is your FIRST name?"
    options = ({"key": "_default", "goto": "first_char_name_first"},)
    return text, options
```

**The Issue:** When processing input (i.e., `raw_string` is not empty), returning a string causes EvMenu to:
1. **Display that string as text** (which is why we saw "first_char_name_last" printed)
2. **Exit the menu** (which is why the next input became a command)

**Why This Happens:**
- EvMenu nodes have **two modes**:
  1. **Display mode:** `raw_string` is empty → return `(text, options)` tuple to show menu
  2. **Input mode:** `raw_string` has content → process input and navigate
  
- In **display mode**, returning a string is interpreted as error text
- In **input mode**, returning a string is interpreted as **text to display before exiting**

**Solution - Pattern #1: Return None to Re-Display**
```python
# ⚠️ WARNING: return None actually EXITS the menu!
# Use recursive call instead:
def node(caller, raw_string, **kwargs):
    if raw_string and raw_string.strip():
        # Validate
        if not valid:
            caller.msg("Error message")
            return node(caller, "", **kwargs)  # ✅ Re-displays current node
```

**Solution - Pattern #2: Call Next Node Directly**
```python
def node(caller, raw_string, **kwargs):
    if raw_string and raw_string.strip():
        # Validate and store
        caller.ndb.data['field'] = raw_string.strip()
        
        # Call next node function directly
        return next_node(caller, "", **kwargs)  # ✅ CORRECT
    
    text = "Prompt text"
    options = ({"key": "_default", "goto": "node"},)
    return text, options
```

---

## The Correct Patterns

### Pattern A: Numbered Menu with Goto-Callable

**Use Case:** Menu with numbered options, input routing via separate function.

```python
def menu_node(caller, raw_string, **kwargs):
    """Display menu with options."""
    text = """
Choose an option:
[1] Option 1
[2] Option 2
"""
    options = (
        {"key": "_default", "goto": process_choice},  # Callable, not string!
    )
    return text, options

def process_choice(caller, raw_string, **kwargs):
    """Process user's choice."""
    choice = raw_string.strip()
    
    if choice == "1":
        return "option1_node"  # OK - goto-callable can return node name
    elif choice == "2":
        return "option2_node"
    else:
        caller.msg("Invalid choice")
        return None  # Re-display menu
```

### Pattern B: Text Input Node (Self-Processing)

**Use Case:** Freeform text input (names, descriptions, etc.)

```python
def text_input_node(caller, raw_string, **kwargs):
    """Get text input from user."""
    
    # Input mode - process user's text
    if raw_string and raw_string.strip():
        text = raw_string.strip()
        
        # Validate
        if not is_valid(text):
            caller.msg("|rError: Invalid input|n")
            return None  # ✅ Re-display this node
        
        # Store and advance
        caller.ndb.data['field'] = text
        return next_input_node(caller, "", **kwargs)  # ✅ Call next node
    
    # Display mode - show prompt
    text = "|wEnter text:|n"
    options = (
        {"key": "_default", "goto": "text_input_node"},
    )
    return text, options
```

### Pattern C: Command Parser Node

**Use Case:** Multiple commands in one node (e.g., GRIM stat distribution)

```python
def command_parser_node(caller, raw_string, **kwargs):
    """Process multiple command types."""
    
    # Input mode
    if raw_string and raw_string.strip():
        args = raw_string.strip().lower().split()
        
        if not args:
            return None  # Re-display
        
        command = args[0]
        
        # Command: done - advance to next node
        if command == "done":
            if not validate_state():
                caller.msg("|rNot ready yet|n")
                return None  # Re-display
            return next_node(caller, "", **kwargs)  # ✅ Advance
        
        # Command: reset - modify state and re-display
        elif command == "reset":
            reset_values()
            return None  # ✅ Re-display with reset values
        
        # Command: set value - modify state and re-display
        elif command in ["stat1", "stat2"]:
            if len(args) < 2:
                caller.msg("|rUsage: stat <value>|n")
                return None
            try:
                value = int(args[1])
                caller.ndb.data[command] = value
            except ValueError:
                caller.msg("|rValue must be a number|n")
            return None  # ✅ Re-display with new values
        
        else:
            caller.msg("|rUnknown command|n")
            return None
    
    # Display mode
    stat1 = caller.ndb.data.get('stat1', 0)
    stat2 = caller.ndb.data.get('stat2', 0)
    
    text = f"""
Stat1: {stat1}
Stat2: {stat2}

Commands: stat1 <value>, stat2 <value>, reset, done
"""
    options = (
        {"key": "_default", "goto": "command_parser_node"},
    )
    return text, options
```

---

## Key Takeaways

### ✅ DO:
- Check `if raw_string and raw_string.strip():` for text input validation
- Return recursive call to re-display current node: `return current_node(caller, "", **kwargs)`
- Call next node function directly when advancing: `return next_node(caller, "", **kwargs)`
- Use goto-callables for menu option routing (they can return node name strings)

### ❌ DON'T:
- Return just `if raw_string:` (can trigger on empty input)
- Return node name string during input processing: `return "node_name"`
- Return `None` (this EXITS the menu, doesn't re-display!)
- Forget to pass empty string when calling nodes: `node(caller, "", **kwargs)`

### 🔍 Debugging:
If you see node names appearing as text output, you're returning a string during input processing instead of calling the node function.

---

## Implementation Checklist

When creating a new EvMenu text-input node:

- [ ] Input validation checks `if raw_string and raw_string.strip():`
- [ ] Errors return `None` (not node name string)
- [ ] Successful input calls next node: `return next_node(caller, "", **kwargs)`
- [ ] Display mode returns `(text, options)` tuple
- [ ] Options include `{"key": "_default", "goto": "self"}`
- [ ] Tested: blank input doesn't trigger validation
- [ ] Tested: valid input advances to next node
- [ ] Tested: invalid input re-displays with error message

---

## Fixed Files

**Date:** October 14, 2025  
**Files Modified:** `commands/charcreate.py`

**Nodes Fixed:**
- `first_char_name_first()` - Text input with validation
- `first_char_name_last()` - Text input with validation
- `first_char_grim()` - Command parser with multiple commands

**Pattern Applied:** Pattern B (text input) and Pattern C (command parser)

---

*This document should be consulted when implementing any future EvMenu systems requiring text input.*
