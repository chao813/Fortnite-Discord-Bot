const path = require('path');

/**
 * Define loggers with different log levels.
 */
const loggers = {
    info: console.log,
    warn: console.warn,
    error: console.error
};

/**
 * Logs messages to both the terminal and Electron's renderer process.
 * @param {BrowserWindow} mainWindow - The reference to the main Electron window.
 * @param {string} message - The message to log.
 */
function log(message, mainWindow, level = 'info') {
    const logFn = loggers[level] || loggers.info;

    const timestampedMessage = `[${getTimestamp()}] ${message}`;
    logFn(timestampedMessage);

    // If the mainWindow is available and not destroyed, send log to Electron's window
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('log-event', { message, level });
    }
}

/**
 * Formats the current date and time for logging.
 * @returns {string} The current date and time in ISO format.
 */
function getTimestamp() {
    return new Date().toISOString();
}

/**
 * Returns the file name without the path
 * @param {string} filePath The file path
 * @returns {string} The file name without the path
 */
function stripPath(filePath) {
    return path.basename(filePath);
}

module.exports = { log, stripPath };
