# GitHub Pokédex Setup Guide

## What You're Getting

A retro ASCII-style Pokédex that displays your GitHub stats across 4 different "Pokémon":

1. **CHARIZARD** - Commit Streak (current, longest, days active)
2. **SNORLAX** - Issue Status (bugs squashed, open tickets, success rate)
3. **GYARADOS** - Total Commits (all-time, recent activity)
4. **DITTO** - Pull Requests (merged, opened, reviewed)

The stats auto-update daily at midnight UTC via GitHub Actions!

## Installation

### Step 1: Set Up Your Profile Repository

If you haven't already, create a repository with the same name as your GitHub username.

```bash
# Example: if your username is "johndoe", create repo "johndoe"
# This is a special repository that displays on your profile
```

### Step 2: Add Files to Your Repository

Copy these files to your profile repository:

```
your-username/
├── .github/
│   └── workflows/
│       └── update-stats.yml
├── generate_pokedex.py
├── github-pokedex.svg
├── mentoring-button.svg (optional)
└── README.md
```

### Step 3: Enable Workflow Permissions

This is **critical** for the auto-update to work:

1. Go to your repository **Settings**
2. Navigate to **Actions** > **General**
3. Scroll to **Workflow permissions**
4. Select **"Read and write permissions"**
5. Check **"Allow GitHub Actions to create and approve pull requests"**
6. Click **Save**

### Step 4: Trigger First Update

The GitHub Action will run automatically:
- On push to main branch (just now!)
- Daily at midnight UTC
- Manually via Actions tab

To manually trigger:
1. Go to your repository
2. Click **"Actions"** tab
3. Select **"Update GitHub Pokédex"**
4. Click **"Run workflow"**

### Step 5: Update Your README

Use the template provided in `README-template.md` or embed the Pokédex in your own README:

```markdown
## GitHub Stats Pokédex

<div align="center">

![GitHub Pokédex](./github-pokedex.svg)

</div>
```

## Customization

### Change Update Frequency

Edit `.github/workflows/update-stats.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours instead of daily
  - cron: '0 0 * * 1'    # Every Monday at midnight
  - cron: '0 12 * * *'   # Every day at noon
```

### Adjust Stat Calculations

Edit `generate_pokedex.py` to change how stats are calculated:

```python
# Example: Change streak calculation
current_streak = calculate_your_custom_streak()

# Example: Use different commit counting
total_commits = get_commits_from_different_source()
```

### Modify Pokémon Descriptions

In `generate_pokedex.py`, find the SVG template and edit the description text:

```python
# Find lines like:
<text>║ This one's tail flame shows coding         ║</text>

# Change to your own text:
<text>║ Your custom description here!              ║</text>
```

### Change Pokémon Order

Rearrange the Pokémon in the SVG by changing the animation timing in `generate_pokedex.py`.

## Troubleshooting

### Stats Not Updating?

1. **Check workflow permissions** (see Step 3 above)
2. **Check Actions tab** for error logs:
   - Click "Actions" tab
   - Click on the failed run
   - Click on the job to see error details
3. **Verify GitHub token** has correct permissions

### Numbers Look Wrong?

The GitHub API has limitations:
- **Commits**: Only counts from recent events (last 100)
- **PRs/Issues**: Uses GitHub Search API (may have rate limits)
- **Streaks**: Based on event activity, not commit history

For more accurate commit counts, you can integrate with additional APIs or use `git log` locally.

### SVG Not Displaying?

1. Make sure the file is named exactly `github-pokedex.svg`
2. Check that it's in the root of your repository
3. Try viewing the raw SVG directly in your browser
4. Clear your browser cache

### Workflow Not Running?

1. Check that the workflow file is in `.github/workflows/` directory
2. Verify the file is named with `.yml` or `.yaml` extension
3. Check repository settings allow Actions to run
4. For scheduled runs, note that GitHub may delay/skip runs during high load

## Understanding the Stats

### Charizard (Commit Streak)
- **Current Flame**: Days with activity in a row from today
- **Longest Blaze**: Maximum streak from available data
- **Days Active**: Unique days with any GitHub activity in last 30 days

### Snorlax (Issues)
- **Bugs Squashed**: Total issues you've closed
- **Snoozing On**: Issues you created that are still open
- **Wake-up Rate**: Percentage of your issues that got closed

### Gyarados (Commits)
- **Total Splashes**: Commits from recent events (estimated)
- **Recent Activity**: Commits in the last 30 days
- **Evolution**: Always maxed! You made it to Gyarados!

### Ditto (Pull Requests)
- **Merged Forms**: PRs you created that were merged
- **Opened Forms**: Total PRs you've opened
- **Reviewed**: Estimated from review events

## Tips

- **Let it run for a few days** to build up accurate streak data
- **Pin your profile repository** so visitors see it first
- **Add the mentoring button** to drive traffic to your coaching site
- **Customize the descriptions** to match your personality
- **Keep your README clean** - the Pokédex is eye-catching enough!

## Known Issues

- **Rate Limiting**: GitHub API may rate limit during peak times
- **Data Freshness**: Events API only shows last 100 events
- **Search Limits**: PR/Issue search may not show complete history for very active users
- **Timezone**: All times are in UTC

## Notes

- The Pokédex cycles through entries every 6 seconds (24-second loop for 4 Pokémon)
- Stats are approximate and based on GitHub API limitations
- Private repository activity won't be counted
- First run may show limited data until it accumulates

---

**Questions?** Open an issue or check the GitHub API docs at https://docs.github.com/rest
