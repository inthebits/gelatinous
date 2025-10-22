"""
Bug reporting command for creating GitHub issues directly from in-game.

This module provides the @bug command that allows players to submit bug reports
that automatically create GitHub issues in the repository. Includes rate limiting,
input validation, and privacy-conscious reporting.
"""

from evennia import Command
from django.conf import settings
from datetime import datetime, timezone
import requests
import json


class CmdBug(Command):
    """
    Report a bug to the development team.
    
    Usage:
        @bug <description>
    
    Examples:
        @bug grenades aren't exploding when rigged to exits
        @bug combat handler not removing dead combatants
        @bug web character creation form validation error
    
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
        
        # Validate input
        if not self.args:
            caller.msg("|rUsage: @bug <description>|n")
            caller.msg("Example: |w@bug grenades aren't exploding|n")
            return
        
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
        
        # Create GitHub issue
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
            
            # Try reading from .git/refs/heads/master (works even without git command)
            git_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ref_file = os.path.join(git_dir, '.git', 'refs', 'heads', 'master')
            
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
                    timeout=2,
                    cwd=git_dir
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
            "title": f"[BUG] {description[:100]}",  # Truncate title if too long
            "body": body,
            "labels": ["bug", "player-reported"]
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
        body = f"""**Reported By:** {context['account_username']}
**Location:** {context['location_dbref']}

**Category:** Uncategorized

---

## Description

{description}

---

## Technical Environment

- **Server:** {context['server']}
- **Commit:** {context['commit_hash']}
"""
        
        return body
