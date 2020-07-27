# Fortnite Player Stats Discord Bot
Retrieve player statistics in Fortnite Battle Royale

## Table of Content

* [Features](#features)
* [Usage](#usage)
* [Examples](#examples)

## Features
- Calculates player statistics in different Game Modes (Solo, Duos, Squads)
- Calculates player's overall statistics
    > Statistics include:
    >    - KD 
    >    - Wins
    >    - Win Percentage
    >    - Kills
    >    - Matches Played

- Show player's level
- Quick view of player's KD (color of embed content)
    - Green : KD <= 1
    - Orange : 1 < KD <= 2
    - Red : 2 < KD <= 3
    - Purple : KD > 3
- Link to Fortnite Tracker player profile (click on username to navigate)
- Link to player's Twitch stream if currently streaming    


## Usage
```
!hunted EpicUsername
!wreckedby EpicUsername
!findnoob EpicUsername
!player EpicUsername

```

## Examples
Player Not Specified:
```
!hunted
```
![Alt text](/images/provide_username_example.png?raw=true)

Player Not Found:
```
!hunted EpicBotAccount
```
![Alt text](/images/fail_example.png?raw=true)

Player Found:
```
!hunted SypherPK
```
![Alt text](/images/example.png?raw=true)

Player Found and Streaming:
```
!hunted Scoped
```
![Alt text](/images/twitch_example.png?raw=true)


