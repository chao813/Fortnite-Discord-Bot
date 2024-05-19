const { log, stripPath } = require('../utils/logger');
const fs = require('fs');
const parseReplay = require('fortnite-replay-parser');
const axios = require('axios');

const parserConfig = {
    parseLevel: 10,
    debug: true,
}

const autoGeneratedFiles = [
    'netfieldexports.txt',
    'netGuidToPathName.txt',
    'notReadingGroups.txt'
]

/**
 * Process replay files.
 * @param {string} filePath The file to process.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 */
async function processFile(filePath, mainWindow) {
    const replayBuffer = fs.readFileSync(filePath);

    parseReplay(replayBuffer, parserConfig).then((parsedReplay) => {
        fs.writeFileSync('replayData.json', JSON.stringify(parsedReplay));
        parseReplayContent(parseReplay, mainWindow);
    }).catch((err) => {
        console.error('An error occurred while parsing the replay!', err);
    });

    deleteReplayDataFiles(mainWindow);

    log(`Completed: ${stripPath(filePath)}`, mainWindow);
}

/**
 * Parse replay content to extract party killed and killed_by data
 * and then send them to the Discord bot.
 * @param {object} parsedReplay ReplayData JSON content
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 */
function parseReplayContent(parsedReplay, mainWindow) {
    const playerIdsMap = getPlayerIdsMap();

    const playerElimRecords = parsedReplay.events.reduce((accumulator, event) => {
        if (event.group !== 'playerElim') {
            return accumulator;
        }
        if (event.eliminator in playerIdsMap) {
            const playerName = playerIdsMap[event.eliminator];
            addToAccumulator(accumulator.killed, playerName, event.eliminated);
        } else if (event.eliminated in playerIdsMap) {
            const player = playerIdsMap[event.eliminated];
            addToAccumulator(accumulator.killed_by, playerName, event.eliminator);
        }
        return accumulator;
      }, { killed: {}, killed_by: {} });

    const payload = {
        killed: playerElimRecords.killed,
        killed_by: playerElimRecords.killed_by
    };

    log(`Replay Content: ${payload}`, mainWindow);

    // await sendToDiscordBot(payload, mainWindow);
}

/**
 * Get mapping of player Fortnite UUID to in-game player name.
 * @returns {object} Mapping of UUID to player name.
 */
function getPlayerIdsMap() {
    const playerIds = process.env.SQUAD_PLAYERS_GUID_DICT;
    try {
        return JSON.parse(playerIds);
    } catch (e) {
        console.error('Failed to parse SQUAD_PLAYERS_GUID_DICT: ', e);
        throw e;
    }
}

/**
 * Push player information to the object key list.
 * @param {object} obj
 * @param {str} key
 * @param {str} value
 */
function addToAccumulator(obj, key, value) {
    if (!Array.isArray(obj[key])) {
        obj[key] = [value];
    } else {
        obj[key].push(value);
    }
}

/**
 * Send game elimination information to the Fortnite Discord bot.
 * @param {object} payload
 * @param {BrowserWindow} mainWindow The Electron window to log messages to
 */
const sendToDiscordBot = async(payload, mainWindow) => {
    try {
        await axios.post(
            process.env.FORTNITE_REPLAY_ELIM_ENDPOINT,
            payload,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'API-TOKEN': process.env.FORTNITE_REPLAY_ELIM_API_TOKEN
                }
            }
        );
    } catch (error) {
        if (error.response) {
            log(`Error: Failed to call Discord bot. ${error.response.status}: ${error.response.data}`, mainWindow, 'error');
        } else if (error.request) {
            // The request was made but no response was received
            log('Error: Failed to call Discord bot as no response was received.', mainWindow, 'error');
        } else {
            // Something happened in setting up the request that triggered an Error
            log(`Error: Failed to call Discord bot due to unexpected error. ${error.response.message}`, mainWindow, 'error');
        }
    }
}

/**
 * Delete replay data files created by the parser library.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to
 */
function deleteReplayDataFiles(mainWindow) {
    for (const file of autoGeneratedFiles) {
        try {
            fs.unlinkSync(file);
        } catch (err) {
            log(`Error: Failed to delete ${file}. ${err}`, mainWindow, 'error');
        }
    }
}

module.exports = { processFile };
