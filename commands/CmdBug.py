"""
Bug reporting command for creating GitHub issues directly from in-game.

This module provides the @bug command that allows players to submit bug reports
that automatically create GitHub issues in the repository. Includes rate limiting,
input validation, and privacy-conscious reporting.
"""

from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from django.conf import settings
from datetime import datetime, timezone
import requests
import json


class CmdBug(MuxCommand):
    """
    Report a bug to the development team.
    
    Usage:
        @bug <description>
        @bug/combat <description>
        @bug/medical <description>
        @bug/category <description>
        @bug/list [count]
        @bug/detail
    
    Switches:
        combat    - Tag as combat-related bug
        medical   - Tag as medical system bug
        movement  - Tag as movement/navigation bug
        items     - Tag as inventory/items bug
        commands  - Tag as command parsing bug
        web       - Tag as web interface bug
        world     - Tag as room/environment bug
        social    - Tag as communication bug
        system    - Tag as server/performance bug
        other     - Tag as uncategorized
        list      - Show your recent bug reports
        detail    - Open multi-line editor for detailed reports
    
    Examples:
        @bug grenades aren't exploding when rigged to exits
        @bug/combat grapple doesn't release target properly
        @bug/medical healing not restoring HP correctly
        @bug/list
        @bug/detail
    
    Submit a bug report that will be created as a GitHub issue for the
    development team to review. All players can submit up to 30 bug reports
    per day. Be clear and descriptive - good bug reports help us fix issues
    faster!
    
    Your report will include:
    - Your account username
    - Current location (#dbref)
    - Server version (commit hash)
    
    Your report will NOT include:
    - Email address
    - Character names
    - Character stats
    - Room names (only #dbref)
    - Timestamps (GitHub tracks this)
    """
    
    key = "@bug"
    aliases = ["bug"]
    locks = "cmd:all()"
    help_category = "General"
    
    # Valid bug categories
    VALID_CATEGORIES = {
        'combat', 'medical', 'movement', 'items', 'commands',
        'web', 'world', 'social', 'system', 'other'
    }
    
    def func(self):
        """Execute the bug report command."""
        caller = self.caller
        account = caller.account
        
        # Check if bug reporting is configured
        if not hasattr(settings, 'GITHUB_TOKEN') or not settings.GITHUB_TOKEN:
            caller.msg("|rBug reporting is not currently configured.|n")
            caller.msg("Please contact staff directly to report bugs.")
            return
        
        if not hasattr(settings, 'GITHUB_REPO') or not settings.GITHUB_REPO:
            caller.msg("|rBug reporting is not currently configured.|n")
            caller.msg("Please contact staff directly to report bugs.")
            return
        
        # Handle /list switch (doesn't need args)
        if 'list' in self.switches:
            self.show_bug_list(caller, account)
            return
        
        # Handle /detail switch (doesn't need args)
        if 'detail' in self.switches:
            self.start_detail_editor(caller)
            return
        
        # Validate input - required for bug submission
        if not self.args:
            caller.msg("|rUsage: @bug <description>|n")
            caller.msg("Example: |w@bug grenades aren't exploding|n")
            caller.msg("Or with category: |w@bug/combat grapple release broken|n")
            caller.msg("\nFor other options:")
            caller.msg("  |w@bug/list|n - Show your recent bug reports")
            caller.msg("  |w@bug/detail|n - Open detailed bug editor (coming soon)")
            caller.msg("\nFor full help: |whelp @bug|n")
            return
        
        # Determine category from switches
        category = None
        for switch in self.switches:
            if switch.lower() in self.VALID_CATEGORIES:
                category = switch.lower()
                break
        
        description = self.args.strip()
        
        # Validate description length
        if len(description) < 10:
            caller.msg("|rPlease provide a more detailed description (at least 10 characters).|n")
            return
        
        if len(description) > 5000:
            caller.msg("|rDescription too long. Please keep it under 5000 characters.|n")
            return
        
        # Check rate limit
        if not self.check_rate_limit(account):
            remaining_time = self.get_time_until_reset(account)
            caller.msg("|rYou've reached the daily limit of 30 bug reports.|n")
            caller.msg(f"The limit resets in {remaining_time}.")
            caller.msg("\nIf you have an urgent issue, please contact staff directly.")
            return
        
        # Get environment context
        context = self.gather_context(caller)
        context['category'] = category
        
        # Create GitHub issue
        if category:
            caller.msg(f"|gCreating bug report (category: |c{category}|g)...|n")
        else:
            caller.msg("|gCreating bug report...|n")
        
        success, result = self.create_github_issue(description, context)
        
        if success:
            issue_url = result.get('html_url', '')
            issue_number = result.get('number', '?')
            
            # Increment bug report counter
            self.increment_report_count(account)
            remaining = 30 - account.db.bug_report_count
            
            caller.msg(f"\n|g✓|n Issue created: |c{issue_url}|n")
            caller.msg("\nThank you for your report! The development team will investigate.")
            
            if remaining <= 5:
                caller.msg(f"You have |y{remaining}|n bug reports remaining today.")
            else:
                caller.msg(f"You have {remaining} bug reports remaining today.")
        else:
            error_msg = result
            caller.msg(f"\n|rFailed to create bug report:|n {error_msg}")
            caller.msg("|yPlease try again in a moment. If the problem persists, contact staff.|n")
    
    def check_rate_limit(self, account):
        """Check if account is within rate limit."""
        today = datetime.now(timezone.utc).date()
        last_date = account.db.bug_report_date
        
        # Reset counter if it's a new day
        if last_date != today:
            account.db.bug_report_count = 0
            account.db.bug_report_date = today
        
        count = account.db.bug_report_count or 0
        limit = getattr(settings, 'BUG_REPORT_DAILY_LIMIT', 30)
        
        return count < limit
    
    def increment_report_count(self, account):
        """Increment the bug report counter for the account."""
        today = datetime.now(timezone.utc).date()
        
        if account.db.bug_report_date != today:
            account.db.bug_report_count = 1
            account.db.bug_report_date = today
        else:
            account.db.bug_report_count = (account.db.bug_report_count or 0) + 1
    
    def get_time_until_reset(self, account):
        """Get human-readable time until rate limit resets."""
        now = datetime.now(timezone.utc)
        tomorrow = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)
        
        delta = tomorrow - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def gather_context(self, caller):
        """Gather environmental context for the bug report."""
        account = caller.account
        location = caller.location
        
        # Get git commit hash
        commit_hash = self.get_git_commit_hash()
        
        # Get location info
        if location:
            location_dbref = f"#{location.id}"
        else:
            location_dbref = "None"
        
        context = {
            'account_username': account.key,
            'location_dbref': location_dbref,
            'commit_hash': commit_hash,
            'server': 'play.gel.monster'
        }
        
        return context
    
    def get_git_commit_hash(self):
        """Get the current git commit hash."""
        try:
            import os
            
            # In Docker, the game is mounted at /usr/src/game
            # Try multiple possible paths
            possible_paths = [
                '/usr/src/game/.git/refs/heads/master',  # Docker absolute path
                os.path.join(os.getcwd(), '.git', 'refs', 'heads', 'master'),  # From current working dir
            ]
            
            # Also try calculating from this file's location
            try:
                git_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                possible_paths.append(os.path.join(git_dir, '.git', 'refs', 'heads', 'master'))
            except:
                pass
            
            # Try each possible path
            for ref_file in possible_paths:
                if os.path.exists(ref_file):
                    with open(ref_file, 'r') as f:
                        full_hash = f.read().strip()
                        # Return short hash (first 7 characters)
                        return full_hash[:7] if full_hash else "unknown"
            
            # Fallback: try git command if available
            try:
                import subprocess
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
                
        except Exception:
            pass
        
        return "unknown"
    
    def sanitize_description(self, text):
        """Sanitize user input to prevent issues."""
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "\n\n[Description truncated at 5000 characters]"
        
        # Basic sanitization - preserve most formatting but prevent extreme cases
        text = text.strip()
        
        return text
    
    def create_github_issue(self, description, context):
        """
        Create a GitHub issue via the API.
        
        Returns:
            tuple: (success: bool, result: dict or error_message: str)
        """
        # Sanitize description
        description = self.sanitize_description(description)
        
        # Build issue body
        body = self.format_issue_body(description, context)
        
        # Prepare API request
        url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/issues"
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Gelatinous-MUD-Bug-Reporter"
        }
        
        payload = {
            "title": description[:100],  # Use description directly, truncate if too long
            "body": body,
            "labels": self.get_labels(context)
        }
        
        # Make API request
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            
            # Success
            return (True, response.json())
            
        except requests.exceptions.Timeout:
            return (False, "Request timed out. Please try again.")
        
        except requests.exceptions.ConnectionError:
            return (False, "Unable to connect to GitHub. Please try again later.")
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            
            if status_code == 401:
                return (False, "GitHub authentication failed. Please contact staff.")
            elif status_code == 403:
                return (False, "Rate limited by GitHub. Please try again later.")
            elif status_code == 422:
                return (False, "Invalid request data. Please contact staff.")
            else:
                return (False, f"GitHub API error (status {status_code})")
        
        except Exception as e:
            return (False, f"Unexpected error: {str(e)}")
    
    def format_issue_body(self, description, context):
        """Format the GitHub issue body with context."""
        category = context.get('category', None)
        category_display = category.capitalize() if category else "Uncategorized"
        
        body = f"""**Reported By:** {context['account_username']}
**Location:** {context['location_dbref']}

**Category:** {category_display}

---

## Description

{description}

---

## Technical Environment

- **Server:** {context['server']}
- **Commit:** {context['commit_hash']}
"""
        
        return body
    
    def get_labels(self, context):
        """Get GitHub labels for the issue based on category."""
        labels = ["bug", "player-reported"]
        
        category = context.get('category')
        if category and category in self.VALID_CATEGORIES:
            labels.append(category)
        
        return labels
    
    def show_bug_list(self, caller, account):
        """Show the player's recent bug reports."""
        caller.msg("|c@bug/list|n - Fetching your recent bug reports...")
        caller.msg("|yThis feature is coming soon!|n")
        caller.msg("\nFor now, check GitHub directly:")
        caller.msg(f"|chttps://github.com/{settings.GITHUB_REPO}/issues|n")
    
    def start_detail_editor(self, caller):
        """Start the multi-line detail editor for bug reports."""
        caller.msg("|c@bug/detail|n - Opening detailed bug report editor...")
        caller.msg("|yThis feature is coming soon!|n")
        caller.msg("\nFor now, use: |w@bug <description>|n")
        caller.msg("Or submit a detailed report directly on GitHub:")
