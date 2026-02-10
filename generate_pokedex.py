#!/usr/bin/env python3
"""
GitHub Pokédex Stats Generator
Fetches real GitHub data and creates ASCII Pokédex SVG
"""

import os
import sys

import requests
from datetime import datetime, timedelta, date

# GitHub API setup
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'yourusername')

# Box drawing constants
LINE_WIDTH = 44  # inner width between ║ borders

# Animation constants
CARD_DISPLAY_SECONDS = 6  # how long each card is visible
FADE_SECONDS = 0.4  # crossfade duration between cards
NUM_CARDS = 4
CYCLE_SECONDS = CARD_DISPLAY_SECONDS * NUM_CARDS


def fetch_github_api(url, headers):
    """Fetch from GitHub API with basic error handling."""
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"  WARNING: {url} returned {response.status_code}", file=sys.stderr)
        return None
    return response.json()


def fetch_contributions(headers):
    """Fetch contribution data from GitHub's GraphQL API."""
    if not GITHUB_TOKEN:
        print("  WARNING: GITHUB_TOKEN required for contribution data", file=sys.stderr)
        return None

    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          totalCommitContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """

    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': {'username': GITHUB_USERNAME}},
        headers=headers,
    )

    if response.status_code != 200:
        print(f"  WARNING: GraphQL API returned {response.status_code}", file=sys.stderr)
        return None

    data = response.json()
    if 'errors' in data:
        print(f"  WARNING: GraphQL errors: {data['errors']}", file=sys.stderr)
        return None

    return data.get('data', {}).get('user', {}).get('contributionsCollection')


def calculate_streaks(contribution_days):
    """Calculate current and longest streaks from contribution calendar days."""
    today = date.today()
    current_streak = 0
    longest_streak = 0

    # contribution_days is already sorted chronologically from the API
    # Walk backwards from today
    streak = 0
    found_today = False
    for day in reversed(contribution_days):
        day_date = date.fromisoformat(day['date'])
        count = day['contributionCount']

        if day_date > today:
            continue

        if day_date == today:
            found_today = True
            if count > 0:
                streak = 1
            else:
                # Today has no contributions yet, check from yesterday
                streak = 0
            continue

        if found_today or day_date == today - timedelta(days=1):
            found_today = True
            if count > 0:
                streak += 1
            else:
                break

    current_streak = streak

    # Longest streak: scan all days
    streak = 0
    for day in contribution_days:
        if day['contributionCount'] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    longest_streak = max(longest_streak, current_streak)

    return current_streak, longest_streak


def fetch_github_stats():
    """Fetch stats from GitHub API"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

    print(f"Fetching data for {GITHUB_USERNAME}...")

    # Contribution data from GraphQL API
    contributions = fetch_contributions(headers)

    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    if contributions:
        total_commits = contributions['totalCommitContributions']

        # Flatten contribution calendar
        all_days = []
        for week in contributions['contributionCalendar']['weeks']:
            all_days.extend(week['contributionDays'])

        current_streak, longest_streak = calculate_streaks(all_days)

        # Recent activity: days with contributions in last 30 days
        recent_activity = 0
        recent_commits = 0
        for day in all_days:
            day_date = date.fromisoformat(day['date'])
            if day_date >= thirty_days_ago and day_date <= today:
                if day['contributionCount'] > 0:
                    recent_activity += 1
                    recent_commits += day['contributionCount']
    else:
        total_commits = 0
        current_streak = 0
        longest_streak = 0
        recent_activity = 0
        recent_commits = 0

    # PRs merged
    prs_merged_url = f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+type:pr+is:merged'
    prs_merged_data = fetch_github_api(prs_merged_url, headers)
    prs_merged = prs_merged_data.get('total_count', 0) if prs_merged_data else 0

    # PRs opened
    prs_opened_url = f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+type:pr'
    prs_opened_data = fetch_github_api(prs_opened_url, headers)
    prs_opened = prs_opened_data.get('total_count', 0) if prs_opened_data else 0

    # Issues closed
    issues_closed_url = f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+type:issue+is:closed'
    issues_closed_data = fetch_github_api(issues_closed_url, headers)
    issues_closed = issues_closed_data.get('total_count', 0) if issues_closed_data else 0

    # Issues opened
    issues_opened_url = f'https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+type:issue'
    issues_opened_data = fetch_github_api(issues_opened_url, headers)
    issues_opened = issues_opened_data.get('total_count', 0) if issues_opened_data else 0

    # PRs reviewed
    prs_reviewed_url = f'https://api.github.com/search/issues?q=reviewed-by:{GITHUB_USERNAME}+type:pr'
    prs_reviewed_data = fetch_github_api(prs_reviewed_url, headers)
    prs_reviewed = prs_reviewed_data.get('total_count', 0) if prs_reviewed_data else 0

    open_issues = max(issues_opened - issues_closed, 0)

    return {
        # Charizard - Commit Streak
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'days_active_month': recent_activity,

        # Snorlax - Issues
        'issues_closed': issues_closed,
        'issues_open': open_issues,
        'issue_close_rate': min(int((issues_closed / max(issues_opened, 1)) * 100), 100),

        # Gyarados - Total Commits
        'total_commits': total_commits,
        'recent_commits': recent_commits,

        # Ditto - Pull Requests
        'prs_merged': prs_merged,
        'prs_opened': prs_opened,
        'prs_reviewed': prs_reviewed,

        'updated': datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    }


def create_stat_bar(percent):
    """Create ASCII stat bar with blocks"""
    total_blocks = 20
    filled_blocks = int((percent / 100) * total_blocks)
    filled = '█' * filled_blocks
    empty = '░' * (total_blocks - filled_blocks)
    return filled + empty


def box_line(content):
    """Create a box line, padding or truncating content to LINE_WIDTH."""
    if len(content) > LINE_WIDTH:
        content = content[:LINE_WIDTH]
    return f"║{content:<{LINE_WIDTH}}║"


def box_top():
    return "╔" + "═" * LINE_WIDTH + "╗"


def box_bottom():
    return "╚" + "═" * LINE_WIDTH + "╝"


def box_separator():
    return box_line(" " + "─" * (LINE_WIDTH - 2) + " ")


def box_blank():
    return box_line("")


def box_stat(label, value):
    """Create a stat line like ' LABEL:                    VALUE'."""
    label_part = f" {label}:"
    available = LINE_WIDTH - len(label_part) - 1  # -1 for trailing space
    return box_line(f"{label_part}{value:>{available}} ")


def text_el(y, content, css_class="ascii-text"):
    """Create an SVG text element."""
    return f'        <text x="120" y="{y}" class="{css_class}" xml:space="preserve">{content}</text>'


def card_animation(card_index):
    """Generate SVG animate values and keyTimes for a card's 400ms crossfade.

    Each card fades in over FADE_SECONDS, holds, then fades out over FADE_SECONDS.
    Cards crossfade simultaneously (one fading out while next fades in).
    """
    fade_frac = FADE_SECONDS / CYCLE_SECONDS
    card_frac = CARD_DISPLAY_SECONDS / CYCLE_SECONDS

    # When this card's window starts and ends
    start = card_index * card_frac
    end = start + card_frac

    # Fade in: start → start + fade_frac
    # Fade out: end - fade_frac → end
    fade_in_start = start
    fade_in_end = start + fade_frac
    fade_out_start = end - fade_frac
    fade_out_end = end

    if card_index == 0:
        # First card: starts visible, fades out, then fades back in at end of cycle
        values = "1;1;0;0;1"
        key_times = f"0;{fade_out_start:.4f};{fade_out_end:.4f};{1 - fade_frac:.4f};1"
    elif card_index == NUM_CARDS - 1:
        # Last card: fades in, holds, fades out at cycle end (loops to card 0)
        values = "0;0;1;1;0"
        key_times = f"0;{fade_in_start:.4f};{fade_in_end:.4f};{fade_out_start:.4f};1"
    else:
        # Middle cards: hidden, fade in, hold, fade out, hidden
        values = "0;0;1;1;0;0"
        key_times = f"0;{fade_in_start:.4f};{fade_in_end:.4f};{fade_out_start:.4f};{fade_out_end:.4f};1"

    return values, key_times


def build_card(card_id, card_index, lines):
    """Build an SVG group for a Pokémon card."""
    opacity = ' opacity="0"' if card_index > 0 else ''
    values, key_times = card_animation(card_index)
    parts = [
        f'    <g id="{card_id}"{opacity}>',
        f'        <animate attributeName="opacity"',
        f'                 values="{values}"',
        f'                 keyTimes="{key_times}"',
        f'                 dur="{CYCLE_SECONDS}s"',
        f'                 repeatCount="indefinite"/>',
        '',
    ]
    y = 85
    for line in lines:
        parts.append(text_el(y, line))
        y += 20
    # Add blinking arrow overlaying the ENTRY line (second to last line)
    entry_y = y - 40
    parts.append(text_el(entry_y, box_line(f"{'▶':>{LINE_WIDTH - 1}} "), "ascii-text blink"))
    parts.append('    </g>')
    return '\n'.join(parts)


def generate_pokemon_svg(stats):
    """Generate the complete ASCII Pokédex SVG"""

    # Calculate percentages for stat bars
    streak_pct = min(int((stats['current_streak'] / max(stats['longest_streak'], 1)) * 100), 100)
    active_pct = int((stats['days_active_month'] / 30) * 100)
    close_rate = stats['issue_close_rate']
    snooze_pct = min(int((stats['issues_open'] / max(stats['issues_open'] + stats['issues_closed'], 1)) * 100), 100)
    recent_pct = min(int((stats['recent_commits'] / max(stats['total_commits'], 1)) * 100), 100)
    merged_pct = min(int((stats['prs_merged'] / max(stats['prs_opened'], 1)) * 100), 100)
    opened_pct = min(int((stats['prs_opened'] / max(stats['prs_opened'] + 50, 1)) * 100), 100)
    reviewed_pct = min(int((stats['prs_reviewed'] / max(stats['prs_reviewed'] + 50, 1)) * 100), 100)

    curr = stats['current_streak']
    longest = stats['longest_streak']
    active = stats['days_active_month']

    # Charizard card
    charizard_lines = [
        box_top(),
        box_line(f" No. 006{'CHARIZARD':>{LINE_WIDTH - 9}} "),
        box_separator(),
        box_blank(),
        box_line(" TYPE: FIRE"),
        box_blank(),
        box_stat("CURRENT FLAME", f"{curr} DAYS"),
        box_line(f" {create_stat_bar(streak_pct)}"),
        box_blank(),
        box_stat("LONGEST BLAZE", f"{longest} DAYS"),
        box_line(f" {'█' * 20}"),
        box_blank(),
        box_stat("DAYS ACTIVE", f"{active}/30 MONTH"),
        box_line(f" {create_stat_bar(active_pct)}"),
        box_blank(),
        box_line(" This one's tail flame shows coding"),
        box_line(" activity! Been keeping the fire"),
        box_line(f" alive for {curr} days. Feed it commits"),
        box_line(" to keep it happy!"),
        box_blank(),
        box_separator(),
        box_line(" ENTRY 1/4"),
        box_bottom(),
    ]

    # Snorlax card
    ic = stats['issues_closed']
    io = stats['issues_open']
    snorlax_lines = [
        box_top(),
        box_line(f" No. 143{'SNORLAX':>{LINE_WIDTH - 9}} "),
        box_separator(),
        box_blank(),
        box_line(" TYPE: REST"),
        box_blank(),
        box_stat("BUGS SQUASHED", str(ic)),
        box_line(f" {create_stat_bar(min(close_rate, 100))}"),
        box_blank(),
        box_stat("SNOOZING ON", f"{io} TICKETS"),
        box_line(f" {create_stat_bar(snooze_pct)}"),
        box_blank(),
        box_stat("WAKE-UP RATE", f"{close_rate}% SUCCESS"),
        box_line(f" {create_stat_bar(close_rate)}"),
        box_blank(),
        box_line(" Only wakes up to squash bugs. Has"),
        box_line(f" dozed off after defeating {ic}"),
        box_line(" issues. Currently snoring through"),
        box_line(f" {io} open tickets. Zzz..."),
        box_blank(),
        box_separator(),
        box_line(" ENTRY 2/4"),
        box_bottom(),
    ]

    # Gyarados card
    tc = stats['total_commits']
    rc = stats['recent_commits']
    commit_pct = min(int((tc / max(tc + 500, 1)) * 100), 100)
    gyarados_lines = [
        box_top(),
        box_line(f" No. 130{'GYARADOS':>{LINE_WIDTH - 9}} "),
        box_separator(),
        box_blank(),
        box_line(" TYPE: WATER/FLYING"),
        box_blank(),
        box_stat("TOTAL SPLASHES", str(tc)),
        box_line(f" {create_stat_bar(commit_pct)}"),
        box_blank(),
        box_stat("RECENT ACTIVITY", f"{rc}/MONTH"),
        box_line(f" {create_stat_bar(recent_pct)}"),
        box_blank(),
        box_stat("EVOLUTION LVL", "GYARADOS!"),
        box_line(f" {'█' * 20}"),
        box_blank(),
        box_line(" Started as Magikarp with 0 commits."),
        box_line(" Splashed around and evolved! Now a"),
        box_line(f" mighty Gyarados with {tc} commits."),
        box_line(" Keep splashing!"),
        box_blank(),
        box_separator(),
        box_line(" ENTRY 3/4"),
        box_bottom(),
    ]

    # Ditto card
    pm = stats['prs_merged']
    po = stats['prs_opened']
    pr = stats['prs_reviewed']
    ditto_lines = [
        box_top(),
        box_line(f" No. 132{'DITTO':>{LINE_WIDTH - 9}} "),
        box_separator(),
        box_blank(),
        box_line(" TYPE: TRANSFORM"),
        box_blank(),
        box_stat("MERGED FORMS", f"{pm} PRS"),
        box_line(f" {create_stat_bar(merged_pct)}"),
        box_blank(),
        box_stat("OPENED FORMS", f"{po} PRS"),
        box_line(f" {create_stat_bar(opened_pct)}"),
        box_blank(),
        box_stat("REVIEWED", str(pr)),
        box_line(f" {create_stat_bar(reviewed_pct)}"),
        box_blank(),
        box_line(" Transforms into whatever the"),
        box_line(" codebase needs! A true team player."),
        box_line(f" Merged {pm} PRs, opened {po},"),
        box_line(f" reviewed {pr}. Any coding style!"),
        box_blank(),
        box_separator(),
        box_line(" ENTRY 4/4"),
        box_bottom(),
    ]

    cards = [
        build_card("charizard", 0, charizard_lines),
        build_card("snorlax", 1, snorlax_lines),
        build_card("gyarados", 2, gyarados_lines),
        build_card("ditto", 3, ditto_lines),
    ]

    cards_svg = '\n'.join(cards)

    svg = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg width="800" height="700" xmlns="http://www.w3.org/2000/svg">',
        '    <defs>',
        '        <style>',
        '            .ascii-text {',
        "                font-family: 'Courier New', monospace;",
        '                font-weight: bold;',
        '                fill: #000000;',
        '                font-size: 14px;',
        '            }',
        '',
        '            @keyframes blink {',
        '                0%, 50% { opacity: 1; }',
        '                51%, 100% { opacity: 0; }',
        '            }',
        '',
        '            .blink { animation: blink 0.8s step-end infinite; }',
        '        </style>',
        '    </defs>',
        '',
        '    <!-- Background -->',
        '    <rect width="800" height="700" fill="#000000"/>',
        '',
        '    <!-- White container -->',
        '    <rect x="100" y="50" width="600" height="600" fill="#ffffff"/>',
        '',
        cards_svg,
        '',
        '    <!-- Controls -->',
        f'    <text x="400" y="670" class="ascii-text" text-anchor="middle" fill="#666666">AUTO: {CARD_DISPLAY_SECONDS}s | Updated: {stats["updated"]}</text>',
        '</svg>',
    ])

    return svg


def main():
    print("Generating GitHub Pokedex...")

    stats = fetch_github_stats()
    print(f"Fetched stats for {GITHUB_USERNAME}")
    print(f"  Streak: {stats['current_streak']} days (longest: {stats['longest_streak']})")
    print(f"  Issues closed: {stats['issues_closed']}")
    print(f"  Commits: {stats['total_commits']} (recent: {stats['recent_commits']})")
    print(f"  PRs merged: {stats['prs_merged']}")
    print(f"  PRs reviewed: {stats['prs_reviewed']}")

    svg_content = generate_pokemon_svg(stats)

    # Save SVG
    with open('github-pokedex.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print("Generated github-pokedex.svg")


if __name__ == '__main__':
    main()
