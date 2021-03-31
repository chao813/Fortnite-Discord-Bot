COMMANDS = {
    "Help": {
        "command": "commands",
        "aliases": ["list"],
        "description": "List available commands."
    },
    "Player Search": {
        "command": "hunted",
        "aliases": ["h", "player", "findnoob", "wreckedby"],
        "description": "Display player stats (ex: `!hunted LigmaBalls12`)."
    },
    "Track Squad": {
        "command": "track",
        "aliases": ["squad"],
        "description": ("Display current stats for the squad. If a username is provided, "
                        "display only stats for that player (ex: `!track LigmaBalls12`).")
    },
    "Stats": {
        "command": "stats",
        "description": ("Display stats `diff` of a player or the squad, or average stats "
                        "of the opponents `played` today (ex: `!stats diff`, `!stats diff "
                        "LigmaBalls12`, `!stats played`)."),
        "diff_commands": ["today", "diff"],
        "opponent_commands": ["played", "opp", "opponents", "noobs", "enemy"]
    },
    "Rate Difficulty": {
        "command": "rate",
        "aliases": ["gg"],
        "description": "Rate how good opponents are today"
    },
    "Upgrade Locations": {
        "command": "upgrade",
        "aliases": ["up", "gold"],
        "description": "Show map of upgrade locations"
    },
    "Hireable NPC Locations": {
        "command": "hire",
        "description": "Show map of hireable NPC locations"
    },
    "Chest Locations": {
        "command": "chest",
        "aliases": ["chests", "loot"],
        "description": "Show map of bunker and regular chest locations"
    }
}

# Help
HELP_COMMAND = COMMANDS["Help"]["command"]
HELP_ALIASES = COMMANDS["Help"]["aliases"]
HELP_DESCRIPTION = COMMANDS["Help"]["description"]

# Player Search
PLAYER_SEARCH_COMMAND = COMMANDS["Player Search"]["command"]
PLAYER_SEARCH_ALIASES =COMMANDS["Player Search"]["aliases"]
PLAYER_SEARCH_DESCRIPTION =COMMANDS["Player Search"]["description"]

# Track Squad
TRACK_COMMAND = COMMANDS["Track Squad"]["command"]
TRACK_ALIASES = COMMANDS["Track Squad"]["aliases"]
TRACK_DESCRIPTION = COMMANDS["Track Squad"]["description"]

# Stats
STATS_COMMAND = COMMANDS["Stats"]["command"]
STATS_DESCRIPTION = COMMANDS["Stats"]["description"]
STATS_DIFF_COMMANDS = COMMANDS["Stats"]["diff_commands"]
STATS_OPPONENTS_COMMANDS = COMMANDS["Stats"]["opponent_commands"]

# Rate Difficulty
RATE_COMMAND = COMMANDS["Rate Difficulty"]["command"]
RATE_DESCRIPTION = COMMANDS["Rate Difficulty"]["description"]
RATE_ALIASES = COMMANDS["Rate Difficulty"]["aliases"]

# Upgrade Locations
UPGRADE_COMMAND = COMMANDS["Upgrade Locations"]["command"]
UPGRADE_DESCRIPTION = COMMANDS["Upgrade Locations"]["description"]
UPGRADE_ALIASES = COMMANDS["Upgrade Locations"]["aliases"]

# Chest Locations
CHESTS_COMMAND = COMMANDS["Chest Locations"]["command"]
CHESTS_DESCRIPTION = COMMANDS["Chest Locations"]["description"]
CHESTS_ALIASES = COMMANDS["Chest Locations"]["aliases"]

# Hireable NPC Locations
HIRE_COMMAND = COMMANDS["Hireable NPC Locations"]["command"]
HIRE_DESCRIPTION = COMMANDS["Hireable NPC Locations"]["description"]
