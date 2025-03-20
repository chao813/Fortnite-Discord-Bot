# Fortnite Player Stats Discord Bot
Retrieve player statistics in Fortnite Battle Royale

> :warning: **Note: This project is a personal project and was created for research and educational purposes only.**

## Table of Content

* [Features](#features)
* [Usage](#usage)
* [Examples](#examples)
* [Setup](#setup)

## Features
- Asks if you want to see current squad stats when joining Fortnite discord channel

Fortnite API search (Default):
If player profile is not found in fortnitetracker.com, fall back to using Fortnite API
- Show player's level
- Calculates player overall season statistics in different Game Modes (Solo, Duos, Squads)
- Calculates player's overall statistics
    > Statistics include:
    >    - KD
    >    - Wins
    >    - Win Percentage
    >    - Kills
    >    - Matches Played
- Link to player's Twitch stream if currently streaming
----------------------------------------------------------------------------------
Fortnite Tracker search (:x: Deprecated, API no longer supported):
- Calculates player current season statistics in different Game Modes (Solo, Duos, Trios, Squads)
- Calculates player's overall statistics
    > Statistics include:
    >    - KD
    >    - Wins
    >    - Win Percentage
    >    - Matches Played
    >    - TRN
----------------------------------------------------------------------------------

- Link to Fortnite Tracker player profile (click on username to navigate)
- Quick view of player's KD (color of embed content)
    - Green : KD <= 1
    - Orange : 1 < KD <= 2
    - Red : 2 < KD <= 3
    - Purple : KD > 3
- Quick view of player's current ranking and progress
- Display current stats for the squad. If a username is provided, display only stats for that player (ex: `!track LigmaBalls12`).")
- Display stats difference of a player or the squad, or average stats of the opponents played today (ex: `!stats diff`, `!stats diff LigmaBalls12`, `!stats played`)."
- Display average stats of all opponents faced today
- Show map of all upgrade locations
- Show map of all bunker chest locations
- Show map of all hireable NPC locations

## Usage
```
!h EpicUsername
!hunted EpicUsername
!wreckedby EpicUsername
!findnoob EpicUsername
!player EpicUsername

!track
!squad
!track EpicUsername
!squad EpicUsername

!stats diff
!stats today

!stats played
!stats opponents
!stats noobs
!stats enemy

!upgrade
!gold

!chests
!loot

!hire
```

## Examples
Prompt when joining Fortnite Discord channel:\
![Alt text](/core/images/prompt_example.png?raw=true)

Player Not Specified:
```
!hunted
```
![Alt text](/core/images/provide_username_example.png?raw=true)

Player Not Found:
```
!hunted EpicBotAccount
```
![Alt text](/core/images/fail_example.png?raw=true)

Player Found (Fortnite API search):
```
!hunted SypherPK
```
![Alt text](/core/images/example.png?raw=true)

Player Found (Fortnite API search) and Streaming:
```
!hunted Fresh
```
![Alt text](/core/images/twitch_example.png?raw=true)

Stats Difference for Squad:
```
!stats diff
```
![Alt text](/core/images/stats_diff_example.png?raw=true)

Average Stats of all Opponent Faced Today:
```
!stats noobs
```
![Alt text](/core/images/stats_noobs_example.png?raw=true)

## Setup
### Install Fortnite Replay Reader
To install the Fortnite Replay Reader pip package, you need to install the package's dependencies first otherwise the requirements.txt install will fail.

To do so, run:
```
pip install wheel bitstring pycryptodome
```

Then:
```
pip install -r requirements.txt
```

### Generate Windows executable
**TODO**
