# Fortnite Replay Companion

A Windows desktop application that monitors and processes Fortnite replay files, then sends the data to a Discord bot to display match results in Discord.

The Fortnite Replay Companion:
- Monitors the Fortnite replay folder for new replay files
- Processes and parses replay content when detected
- Sends the parsed game data to a Discord bot service
- Cleans up temporary data files after processing

## Running the Application

To start the application in development mode:
```
npm start
```

If via the Makefile, which is preferred as it will also remove any existing test replay files:
```
make start-dev
```

Ensure you create a local `config-local.json` file to override the default settings in `config.json`.

## Building for Distribution

To build the application as a Windows executable:
```
make build-win
```

This will create an executable in the `dist` folder.

### Variables Replacement

Make sure to replace `FORTNITE_DISCORD_BOT_GAME_URL` and `FORTNITE_DISCORD_BOT_API_TOKEN` in `replayProcessor.js` to the actual values. Otherwise the executable will pull the environment variables from the host Windows machine, which likely will not have these variables set up.

## Configuration

The application uses a configuration file for settings such as:
- Replay file monitoring location
- File monitoring polling and stability intervals

Create a `config-local.json` file to override any default settings from `config.json`.
