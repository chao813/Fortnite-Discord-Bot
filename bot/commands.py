COMMANDS = {
    "Help": {
        "command": "commands",
        "aliases": ["list"],
        "description": "List available commands.",
        "examples": "`!commands`"
    },
    "Message": {
        "command": "message",
        "aliases": ["msg"],
        "description": "Send message in the Discord text channel.",
        "examples": "`!msg Hello`"
    },
    "Stats Game Mode": {
        "command": "mode",
        "aliases": ["m", "game_mode"],
        "description": "Set game mode for stats lookup",
        "examples": "`!mode ranked_reload`, `!m ranked_br`, `!m unranked_br`"
    },
    "Player Search": {
        "command": "hunted",
        "aliases": ["h", "player", "findnoob", "wreckedby"],
        "description": "Display player stats",
        "examples": "`!h LigmaBalls12`, `!hunted LigmaBalls12`"
    },
    "Track Squad": {
        "command": "track",
        "aliases": ["squad", "squads"],
        "description": ("Display current stats for the squad. If a username is provided, "
                        "display only stats for that player (ex: `!track LigmaBalls12`)."),
        "examples": "`!track`, `!squad`"
    },
    "Stats": {
        "command": "stats",
        "description": ("Display stats `diff` of a player or the squad, or average stats "
                        "of the opponents `played` today (ex: `!stats diff`, `!stats diff "
                        "LigmaBalls12`, `!stats played`)."),
        "diff_commands": ["diff"],
        "opponent_commands": ["played", "rate", "killed", "opponents", "enemy", "noobs"],
        "examples": "`!stats diff`, `!stats diff stoobish`, `!stats played`"
    },
    "Upgrade Locations": {
        "command": "upgrade",
        "aliases": ["up", "gold"],
        "description": "Show map of upgrade locations",
        "examples": "`!upgrade`, `!up`, `!gold`"
    },
    "Hireable NPC Locations": {
        "command": "hire",
        "description": "Show map of hireable NPC locations",
        "examples": "`!hire`"
    },
    "Chest Locations": {
        "command": "chest",
        "aliases": ["chests", "loot"],
        "description": "Show map of bunker and regular chest locations",
        "examples": "`!chests`, `!chest`, `!loot`"
    },
    "Replays": {
        "command": "replays",
        "aliases": ["r"],
        "description": ("Display stats of a player that eliminated squad player"
                        "or list all eliminations associated to squad players"),
        "eliminated_commands": ["elim", "elims", "kills", "killed"],
        "log_commands": ["log", "silent"],
        "examples": "`!replays`, `!replays LigmaBalls12`, `!replays kills`, `!replays kills LigmaBalls12`"
    },
    "Ask": {
        "command": "ask",
        "aliases": ["a", "chatgpt"],
        "description": "Ask OpenAI ChatGPT a question",
        "examples": "``!ask`, `!chatgpt`"
    }
}

# Help
HELP_COMMAND = COMMANDS["Help"]["command"]
HELP_ALIASES = COMMANDS["Help"]["aliases"]
HELP_DESCRIPTION = COMMANDS["Help"]["description"]
HELP_EXAMPLES = COMMANDS["Help"]["examples"]

# Message
MESSAGE_COMMAND = COMMANDS["Message"]["command"]
MESSAGE_ALIASES = COMMANDS["Message"]["aliases"]
MESSAGE_DESCRIPTION = COMMANDS["Message"]["description"]
MESSAGE_EXAMPLES = COMMANDS["Message"]["examples"]

# Stats Game Mode
STATS_GAME_MODE_COMMAND = COMMANDS["Stats Game Mode"]["command"]
STATS_GAME_MODE_ALIASES = COMMANDS["Stats Game Mode"]["aliases"]
STATS_GAME_MODE_DESCRIPTION = COMMANDS["Stats Game Mode"]["description"]
STATS_GAME_MODE_EXAMPLES = COMMANDS["Stats Game Mode"]["examples"]

# Player Search
PLAYER_SEARCH_COMMAND = COMMANDS["Player Search"]["command"]
PLAYER_SEARCH_ALIASES = COMMANDS["Player Search"]["aliases"]
PLAYER_SEARCH_DESCRIPTION = COMMANDS["Player Search"]["description"]
PLAYER_SEARCH_EXAMPLES = COMMANDS["Player Search"]["examples"]

# Track Squad
TRACK_COMMAND = COMMANDS["Track Squad"]["command"]
TRACK_ALIASES = COMMANDS["Track Squad"]["aliases"]
TRACK_DESCRIPTION = COMMANDS["Track Squad"]["description"]
TRACK_EXAMPLES = COMMANDS["Track Squad"]["examples"]

# Stats
STATS_COMMAND = COMMANDS["Stats"]["command"]
STATS_DESCRIPTION = COMMANDS["Stats"]["description"]
STATS_DIFF_COMMANDS = COMMANDS["Stats"]["diff_commands"]
STATS_OPPONENTS_COMMANDS = COMMANDS["Stats"]["opponent_commands"]
STATS_EXAMPLES = COMMANDS["Stats"]["examples"]

# Upgrade Locations
UPGRADE_COMMAND = COMMANDS["Upgrade Locations"]["command"]
UPGRADE_DESCRIPTION = COMMANDS["Upgrade Locations"]["description"]
UPGRADE_ALIASES = COMMANDS["Upgrade Locations"]["aliases"]
UPGRADE_EXAMPLES = COMMANDS["Upgrade Locations"]["examples"]

# Chest Locations
CHESTS_COMMAND = COMMANDS["Chest Locations"]["command"]
CHESTS_DESCRIPTION = COMMANDS["Chest Locations"]["description"]
CHESTS_ALIASES = COMMANDS["Chest Locations"]["aliases"]
CHESTS_EXAMPLES = COMMANDS["Chest Locations"]["examples"]

# Hireable NPC Locations
HIRE_COMMAND = COMMANDS["Hireable NPC Locations"]["command"]
HIRE_DESCRIPTION = COMMANDS["Hireable NPC Locations"]["description"]
HIRE_EXAMPLES = COMMANDS["Hireable NPC Locations"]["examples"]

# Replays
REPLAYS_COMMAND = COMMANDS["Replays"]["command"]
REPLAYS_DESCRIPTION = COMMANDS["Replays"]["description"]
REPLAYS_ELIMINATED_COMMANDS = COMMANDS["Replays"]["eliminated_commands"]
REPLAYS_LOG_COMMANDS = COMMANDS["Replays"]["log_commands"]
REPLAYS_EXAMPLES = COMMANDS["Replays"]["examples"]

# Ask OpenAI ChatGPT
ASK_COMMAND = COMMANDS["Ask"]["command"]
ASK_DESCRIPTION = COMMANDS["Ask"]["description"]
ASK_ALIASES = COMMANDS["Ask"]["aliases"]
ASK_EXAMPLES = COMMANDS["Ask"]["examples"]
