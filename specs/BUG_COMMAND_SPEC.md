# Bug Command Specification

## Overview

The `@bug` command allows players and staff to submit bug reports directly to the GitHub repository as issues. This integrates in-game feedback with the development workflow while maintaining appropriate privacy boundaries.

## Design Principles

1. **Accessible**: All players can report bugs
2. **Privacy-Conscious**: No email addresses or sensitive player data exposed
3. **Context-Rich**: Captures technical environment for debugging
4. **Generous Rate Limiting**: Players can report up to 30 bugs per day
5. **Developer-Friendly**: Issues created with proper formatting and labels

---

## Command Syntax

### Basic Usage
```
@bug <brief description>
```
Creates a simple one-line bug report.

**Example:**
```
@bug grenades aren't exploding when rigged to exits
```

### Detailed Reports
```
@bug/detail
```
Opens a multi-line text editor for detailed bug descriptions with reproduction steps.

### Category Tagging
```
@bug/category <category> <description>
```
Tag the bug with a specific category for better organization.

**Categories:**
- `combat` - Combat system issues (attacks, grappling, damage)
- `medical` - Medical system, injuries, healing
- `movement` - Movement commands, exits, navigation
- `items` - Inventory, equipment, objects
- `commands` - General command parsing or execution
- `web` - Web interface, character creation, respawn
- `world` - Rooms, descriptions, environment
- `social` - Communication, channels, emotes
- `system` - Server errors, crashes, performance
- `other` - Uncategorized issues

**Example:**
```
@bug/combat grapple command isn't releasing target properly
```

### List Recent Bugs (Admin Only)
```
@bug/list [count]
```
Shows recently created issues from the game. Defaults to 5, max 20.

---

## GitHub Issue Format

### Issue Title
```
[BUG] <player's brief description>
```

### Issue Labels
- `bug` (always applied)
- `player-reported` (always applied)
- `<category>` (if specified, e.g., `combat`, `medical`)

### Issue Body Template
```markdown
**Reported By:** <account_username>
**Location:** <room #dbref>

**Category:** <category or "Uncategorized">

---

## Description

<player's detailed description>

---

## Technical Environment

- **Server:** play.gel.monster
- **Commit:** <git commit hash>
```

### Privacy Considerations

**✅ INCLUDED:**
- Account username (display name, not email)
- Current room #dbref (for context)
- Git commit hash (for version tracking)

**❌ EXCLUDED:**
- Email addresses
- Character names
- Character G.R.I.M. stats
- Room descriptive names (only #dbref)
- Account IP addresses
- Session information
- Personal identifying information
- Timestamps (GitHub Issues tracks creation time automatically)

---

## Technical Implementation

### File Structure
```
commands/
  CmdBug.py          # New command implementation
  default_cmdsets.py # Add CmdBug to default cmdset

server/conf/
  secret_settings.py # Store GITHUB_TOKEN (gitignored)
```

### GitHub API Integration

**Endpoint:**
```
POST https://api.github.com/repos/daiimus/gelatinous/issues
```

**Authentication:**
- Personal Access Token (PAT) stored in `secret_settings.py`
- Required scope: `public_repo` (for issue creation in public repositories)
  - Note: If repository were private, would need full `repo` scope
- Token format: `GITHUB_TOKEN = "ghp_your_token_here"`

**Request Headers:**
```python
{
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Gelatinous-MUD-Bug-Reporter"
}
```

**Request Payload:**
```python
{
    "title": f"[BUG] {player_description}",
    "body": formatted_issue_body,
    "labels": ["bug", "player-reported", category]
}
```

### Dependencies
- `requests` library (HTTP client for GitHub API)
- `json` (standard library, payload formatting)
- `datetime` (standard library, timestamps)
- `git` command line (to get current commit hash)

---

## Rate Limiting

### Per-Player Limits
- **Daily Limit:** 30 bug reports per account per day (resets at midnight UTC)
- **Cooldown:** None (no delay between reports)
- **Storage:** Track in `account.db.bug_reports_today` with date stamp

### Rate Limit Messages
```python
# When limit reached
"You've reached the daily limit of 30 bug reports. Please try again tomorrow."

# When limit approaching
"Bug report submitted! (You have {remaining} reports remaining today.)"
```

### Reset Logic
```python
def check_rate_limit(account):
    today = datetime.now(UTC).date()
    last_date = account.db.bug_report_date
    
    if last_date != today:
        # New day, reset counter
        account.db.bug_report_count = 0
        account.db.bug_report_date = today
    
    count = account.db.bug_report_count or 0
    return count < 30
```

---

## User Experience Flow

### Successful Report
```
> @bug grenades aren't exploding when rigged to exits

|gCreating bug report...|n

|g✓|n Issue created: |chttps://github.com/daiimus/gelatinous/issues/42|n

Thank you for your report! The development team will investigate.
You have |y29|n bug reports remaining today.
```

### Detailed Report Flow
```
> @bug/detail

|cOpening bug report editor...|n
|yPlease provide a detailed description including:|n
  - What you were trying to do
  - What you expected to happen
  - What actually happened
  - Steps to reproduce (if possible)

|yType your report below. Use @@ on a new line when finished.|n

> I tried to rig a grenade to the north exit.
> I expected it to explode when someone walked north.
> Instead, nothing happens and the grenade disappears.
> 
> Steps:
> 1. Get grenade from inventory
> 2. Type "rig grenade to north"
> 3. Command succeeds but grenade vanishes
> 4. Walk through exit - no explosion
> @@

|gCreating detailed bug report...|n

|g✓|n Issue created: |chttps://github.com/daiimus/gelatinous/issues/43|n

Thank you for the detailed report! This helps us fix the issue faster.
You have |y28|n bug reports remaining today.
```

### Category Report
```
> @bug/combat grapple release doesn't work after knockout

|gCreating bug report (category: |ccombat|g)...|n

|g✓|n Issue created: |chttps://github.com/daiimus/gelatinous/issues/44|n

Thank you for your report! The development team will investigate.
You have |y27|n bug reports remaining today.
```

### Rate Limit Reached
```
> @bug another issue here

|rYou've reached the daily limit of 30 bug reports.|n
The limit resets at midnight UTC (in 4 hours, 23 minutes).

If you have an urgent issue, please contact staff directly.
```

### Network Error
```
> @bug test bug

|rFailed to create bug report: Unable to connect to GitHub.|n
|yPlease try again in a moment. If the problem persists, contact staff.|n
```

---

## Error Handling

### Network Failures
```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
except requests.exceptions.Timeout:
    caller.msg("|rBug report timed out. Please try again.|n")
except requests.exceptions.ConnectionError:
    caller.msg("|rUnable to connect to GitHub. Please try again later.|n")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        caller.msg("|rGitHub authentication failed. Please contact staff.|n")
    elif e.response.status_code == 403:
        caller.msg("|rRate limited by GitHub. Please try again later.|n")
    else:
        caller.msg(f"|rGitHub API error: {e.response.status_code}|n")
```

### Input Validation
```python
def sanitize_bug_description(text):
    """Sanitize user input to prevent markdown injection or excessive content."""
    # Limit length
    if len(text) > 5000:
        return text[:5000] + "\n\n[Description truncated at 5000 characters]"
    
    # Escape potential markdown injection (but allow basic formatting)
    # Keep newlines, basic formatting, but escape potentially malicious patterns
    
    return text.strip()
```

### Missing Configuration
```python
if not hasattr(settings, 'GITHUB_TOKEN') or not settings.GITHUB_TOKEN:
    caller.msg("|rBug reporting is not configured. Please contact staff.|n")
    return
```

---

## Admin Features

### List Recent Issues
```
@bug/list [count]
```

**Example Output:**
```
> @bug/list 5

|cRecent Bug Reports (Last 5):|n

|y#44|n [combat] Grapple release doesn't work after knockout
  Reported by: Alice (2 hours ago)
  |chttps://github.com/daiimus/gelatinous/issues/44|n

|y#43|n Grenades vanish when rigged to exits
  Reported by: Bob (3 hours ago)
  |chttps://github.com/daiimus/gelatinous/issues/43|n

|y#42|n Web character creation form validation error
  Reported by: Carol (5 hours ago)
  |chttps://github.com/daiimus/gelatinous/issues/42|n

[... truncated ...]
```

### Future Admin Commands (Phase 2)
- `@bug/close <issue_number>` - Close an issue from in-game
- `@bug/comment <issue_number> <comment>` - Add comment to issue
- `@bug/search <query>` - Search existing issues

---

## Security Considerations

### Token Security
- ✅ Store token in `secret_settings.py` (gitignored)
- ✅ Never log or display token in error messages
- ✅ Use environment variable as fallback: `os.getenv('GITHUB_TOKEN')`
- ✅ Restrict token scope to minimum required (`repo` only)

### Input Sanitization
- ✅ Limit description length (5000 characters)
- ✅ Strip potentially malicious markdown patterns
- ✅ Validate category against whitelist
- ✅ Escape special characters appropriately

### Rate Limiting
- ✅ 30 reports per account per day
- ✅ Prevent spam/abuse
- ✅ No cooldown between reports (trust players)

### Data Privacy
- ✅ No email addresses exposed
- ✅ No G.R.I.M. stats leaked
- ✅ Only #dbref for location (not descriptive room name)
- ✅ Account username only (not internal IDs)

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Simple bug report creates issue successfully
- [ ] Detailed report with multi-line editor works
- [ ] Category tagging applies correct labels
- [ ] Rate limiting enforces 30/day limit
- [ ] Rate limit resets at midnight UTC
- [ ] GitHub link is returned and functional
- [ ] Error handling for network failures
- [ ] Error handling for invalid GitHub token
- [ ] Input sanitization prevents injection
- [ ] Privacy: no emails or stats in issues

### Test Cases
```python
# Test 1: Basic report
@bug test basic bug report
# Expected: Issue created with title "[BUG] test basic bug report"

# Test 2: Category tagging
@bug/combat test combat bug
# Expected: Issue has labels ["bug", "player-reported", "combat"]

# Test 3: Rate limiting
# Create 30 reports rapidly
# Expected: 30th succeeds, 31st fails with rate limit message

# Test 4: Detailed report
@bug/detail
# Enter multi-line text
# Expected: Full description appears in issue body

# Test 5: Network error
# Disable internet connection
@bug test during outage
# Expected: Graceful error message, no crash
```

---

## Future Enhancements (Phase 2+)

### Duplicate Detection
- Check for similar existing issues before creating
- Suggest existing issues to reporter
- "Did you mean issue #42?"

### Attachment Support
- Capture recent command history (last 10 commands)
- Include recent combat log entries (if applicable)
- Screenshot support (via web interface)

### Issue Tracking
- Allow players to check status of their reports
- `@bug/status` - Show your open bugs
- Notify players when their bugs are closed/fixed

### Prioritization
- Allow staff to set priority from in-game
- Auto-tag critical bugs (crashes, data loss)
- Escalate urgent issues automatically

### Integration with Channels
- Broadcast new bug reports to staff channel
- Optional: Public bug report announcements
- Link to fixed bugs in patch notes

---

## Implementation Phases

### Phase 1: Core Functionality (MVP)
- ✅ Basic `@bug <description>` command
- ✅ GitHub issue creation via API
- ✅ Rate limiting (30/day)
- ✅ Privacy-conscious issue format
- ✅ Error handling

### Phase 2: Enhanced Reporting
- ⏳ Detailed report editor (`@bug/detail`)
- ⏳ Category tagging system
- ⏳ Admin list command (`@bug/list`)

### Phase 3: Advanced Features
- ⏳ Duplicate detection
- ⏳ Issue status tracking
- ⏳ Admin close/comment commands
- ⏳ Player notification on bug resolution

---

## Configuration

### secret_settings.py
```python
# GitHub Bug Reporting Configuration
GITHUB_TOKEN = "ghp_your_personal_access_token_here"
GITHUB_REPO = "daiimus/gelatinous"
BUG_REPORT_DAILY_LIMIT = 30
```

### settings.py (if needed)
```python
# Bug reporting defaults (can override in secret_settings.py)
BUG_REPORT_DAILY_LIMIT = getattr(secret_settings, 'BUG_REPORT_DAILY_LIMIT', 30)
GITHUB_REPO = getattr(secret_settings, 'GITHUB_REPO', 'daiimus/gelatinous')
```

---

## Success Metrics

### Adoption
- Number of bug reports submitted per week
- Percentage of players who use the command
- Average time to first bug report (new players)

### Quality
- Actionable bug reports (contain enough info to reproduce)
- False positive rate (non-bugs reported as bugs)
- Duplicate report rate

### Developer Impact
- Bugs fixed from player reports vs. other sources
- Average time from report to fix
- Player satisfaction with bug resolution

---

## Documentation

### In-Game Help
```
> help @bug

@bug - Submit a bug report to the development team

Usage:
  @bug <brief description>
  @bug/detail              (opens editor for detailed reports)
  @bug/combat <description> (tag as combat-related)
  
Examples:
  @bug grenades aren't exploding
  @bug/detail
  @bug/medical healing doesn't restore HP
  
All players can submit up to 30 bug reports per day. Your reports
help make the game better for everyone!

Categories: combat, medical, movement, items, commands, web, world,
           social, system, other

See also: help feedback, help @idea
```

### Player Documentation
Add section to `README.md` or create `CONTRIBUTING_PLAYERS.md`:
- How to write good bug reports
- What information to include
- When to use @bug vs contacting staff directly
- Expected response times

---

*This specification should be reviewed and updated as the bug reporting system evolves.*
