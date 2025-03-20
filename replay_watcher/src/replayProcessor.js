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
 * @param {object} config Config file content
 */
async function processFile(filePath, mainWindow, config) {
    const replayBuffer = fs.readFileSync(filePath);

    const payload = {};
    sendToDiscordBot(payload, mainWindow)
        .then(data => {
            console.log(data);
        });

    parseReplay(replayBuffer, parserConfig).then((parsedReplay) => {
        fs.writeFileSync('replayData.json', JSON.stringify(parsedReplay));
        parseReplayContent(parsedReplay, mainWindow, config);

        deleteReplayDataFiles(mainWindow);

        log(`Completed: ${stripPath(filePath)}`, mainWindow);
    }).catch((err) => {
        log(`Failed to parse the replay file: ${err}`);
        console.error('An error occurred while parsing the replay: ', err);
    });
}

/**
 * Parse replay content to extract party killed and killed_by data
 * and then send them to the Discord bot.
 * @param {object} parsedReplay ReplayData JSON content
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 * @param {object} config Config file content
 */
function parseReplayContent(parsedReplay, mainWindow, config) {
    const playerIdsMap = config.fortnite.guidToPlayerId;

    const playerElimRecords = parsedReplay.events.reduce((accumulator, event) => {
        if (event.group !== 'playerElim') {
            return accumulator;
        }

        // TODO: Dedupe events by the same player, ex. killed player twice
        if (event.eliminator in playerIdsMap) {
            const playerId = playerIdsMap[event.eliminator];
            addToAccumulator(accumulator.killed, playerId, event.eliminated);
        } else if (event.eliminated in playerIdsMap) {
            const playerId = playerIdsMap[event.eliminated];
            addToAccumulator(accumulator.killed_by, playerId, event.eliminator);
        }
        return accumulator;
      }, { killed: {}, killed_by: {} });

    const payload = {
        game_mode: parsedReplay.gameData.playlistInfo,
        killed: playerElimRecords.killed,
        killed_by: playerElimRecords.killed_by
    };

    log(`Replay Content: ${JSON.stringify(payload)}`, mainWindow);

    sendToDiscordBot(payload, mainWindow)
        .then(response => {
            log(`Sent to Discord bot. Response: ${JSON.stringify(response)}`)
        });
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
        // await axios.post(
        const response = await axios.get(
            process.env.FORTNITE_REPLAY_ELIM_ENDPOINT,
            // "https://httpbin.org/uuid",
            payload,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'API-TOKEN': "onv13I1Pw4iVcJFew9gnAMadcQm_qoPqVozYA8w7CNY"
                    // 'API-TOKEN': process.env.FORTNITE_REPLAY_ELIM_API_TOKEN

                }
            }
        );
        return response.data
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
