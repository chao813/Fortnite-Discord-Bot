const { log } = require('../utils/logger');

/**
 * Process replay files.
 * @param {string} filePath The file to process.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 */
function processFile(filePath, mainWindow) {
    log(`Processing: ${filePath}`, mainWindow);

    // Implement replays logic with https://github.com/xNocken/replay-reader

    log(`Completed: ${filePath}`, mainWindow);
}

module.exports = { processFile };
