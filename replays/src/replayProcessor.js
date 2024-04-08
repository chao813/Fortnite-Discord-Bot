const { log } = require('../utils/logger');
const fs = require('fs');
const parseReplay = require('fortnite-replay-parser');

const parserConfig = {
    parseLevel: 10,
    debug: true,
}

/**
 * Process replay files.
 * @param {string} filePath The file to process.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 */
function processFile(filePath, mainWindow) {
    log(`Processing: ${filePath}`, mainWindow);

    const replayBuffer = fs.readFileSync(filePath);

    parseReplay(replayBuffer, parserConfig).then((parsedReplay) => {
        fs.writeFileSync('replayData.json', JSON.stringify(parsedReplay));
    }).catch((err) => {
        console.error('An error occured while parsing the replay!', err);
    });

    /**
     * Check out under "events": "473C0E12449D0A53638E4B867536C5BF"
     * "eliminated": "4f8dad253c4842c689e05c251af1f660",
     * "eliminator": "3b82f92adc1d4d28acbf17f4c58d2571",  // chunchun
     *
     * The Python implementation has these UUID to usernames hardcoded in .env
     */

    log(`Completed: ${filePath}`, mainWindow);
}

module.exports = { processFile };
