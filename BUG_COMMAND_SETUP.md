# Bug Command Setup Guide

## Quick Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Give it a descriptive name: "Gelatinous Bug Reporter"
3. Set expiration: No expiration (or choose your preference)
4. Select scopes:
   - ✅ **public_repo** (Access public repositories)
     - This is all you need since gelatinous is a public repository
     - Allows creating issues in public repos
5. Click "Generate token"
6. Copy the token (format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Note:** If your repository were private, you would need the full `repo` scope instead.

### 2. Add Token to Server Configuration

**On your production server** (`play.gel.monster`):

```bash
# SSH into server
ssh -i ~/.ssh/LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster

# Navigate to gelatinous directory
cd gel.monster/gelatinous

# Edit secret_settings.py
nano server/conf/secret_settings.py

# Add your GitHub token (replace with your actual token):
GITHUB_TOKEN = "ghp_your_actual_token_here"

# Save and exit (Ctrl+X, Y, Enter)
```

**On your local development environment:**

Edit `server/conf/secret_settings.py` and add your token:
```python
GITHUB_TOKEN = "ghp_your_actual_token_here"
```

### 3. Reload Evennia

**Production:**
```bash
sudo docker-compose exec evennia evennia reload
```

**Local:**
```bash
evennia reload
```

### 4. Test the Command

In-game:
```
@bug This is a test bug report to verify everything works!
```

You should see:
```
Creating bug report...

✓ Issue created: https://github.com/daiimus/gelatinous/issues/XX

Thank you for your report! The development team will investigate.
You have 29 bug reports remaining today.
```

Check your GitHub repository to verify the issue was created!

---

## Configuration Options

In `server/conf/secret_settings.py`:

```python
# GitHub Bug Reporting Configuration
GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"     # Your Personal Access Token
GITHUB_REPO = "daiimus/gelatinous"    # Repository name
BUG_REPORT_DAILY_LIMIT = 30           # Max reports per player per day
```

---

## Troubleshooting

### "Bug reporting is not currently configured"
- Ensure `GITHUB_TOKEN` is set in `secret_settings.py`
- Ensure it's not an empty string
- Reload Evennia after making changes

### "GitHub authentication failed"
- Check that your token is still valid (hasn't been revoked/expired)
- Ensure token has `repo` scope enabled
- Generate a new token if needed

### "Rate limited by GitHub"
- GitHub API has a 5000 requests/hour limit
- Wait a few minutes and try again
- Consider implementing caching if this becomes frequent

### "Unable to connect to GitHub"
- Check server internet connectivity
- Check if GitHub is experiencing issues: https://www.githubstatus.com/
- Verify firewall isn't blocking requests

---

## Security Notes

⚠️ **IMPORTANT:** Never commit `GITHUB_TOKEN` to git!

- `secret_settings.py` is already in `.gitignore`
- If you accidentally commit the token, revoke it immediately and generate a new one
- Tokens should be treated like passwords

---

## Usage Examples

**Simple bug report:**
```
@bug grenades aren't exploding when rigged to exits
```

**Check remaining reports:**
```
@bug test
```
(Shows remaining count after submission)

**When rate limited:**
```
You've reached the daily limit of 30 bug reports.
The limit resets in 4 hours, 23 minutes.
```

---

## What Gets Included in Reports

✅ **Included:**
- Account username
- Timestamp
- Current room #dbref
- Git commit hash
- Room typeclass

❌ **Not Included:**
- Email addresses
- Character names
- Character stats
- Room descriptive names
- IP addresses

---

## Next Steps (Phase 2)

Future enhancements planned:
- Web interface to view bugs
- Category tagging (`@bug/combat`, `@bug/medical`, etc.)
- Detailed report editor (`@bug/detail`)
- Admin commands (`@bug/list`, `@bug/close`)

---

*See `specs/BUG_COMMAND_SPEC.md` for complete technical documentation.*
