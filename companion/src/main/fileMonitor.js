const chokidar = require('chokidar');

const { log, stripPath } = require('./utils/logger');
const { processFile } = require('./replayProcessor');

/**
 * Initializes file system watcher to monitor for new replay files.
 *
 * @param {BrowserWindow} mainWindow - Main app window for sending UI updates
 * @param {Object} config - Config object
 * @returns {void}
 */
function startReplayMonitoring(mainWindow, config) {
    log('Starting replays monitor', mainWindow);

    const replaysDirectory = config.fileMonitor.replays_directory;
    const watcherStartTime = Date.now();

    const watcher = chokidar.watch(replaysDirectory, {
        ignored: /(^|[\/\\])\../,
        ignoreInitial: false,
        persistent: true,
        awaitWriteFinish: {
            stabilityThreshold: config.fileMonitor.stable_threshold,
            pollInterval: config.fileMonitor.polling_interval
        },
        usePolling: true
    });

    watcher.on('add', async (filePath, stats) => {
        if (stats && stats.birthtimeMs && stats.birthtimeMs > watcherStartTime) {
            log(`Processing: ${stripPath(filePath)}`, mainWindow);

            try {
                await processFile(filePath, mainWindow, config);
            } catch (error) {
                log(`Error processing file: ${stripPath(filePath)}. ${error.message}`, mainWindow, 'error');
            }
        }
    });

    log(`Monitoring directory: ${replaysDirectory}`, mainWindow);
}

module.exports = {
    startReplayMonitoring
};
