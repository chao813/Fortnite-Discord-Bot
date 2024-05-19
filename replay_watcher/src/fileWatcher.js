const chokidar = require('chokidar');
const { log, stripPath } = require('../utils/logger');
const { processFile } = require('./replayProcessor');
const fs = require('fs');

// TODO: Add these as options in the UI. Also add dropdown selection for silent mode boolean
// const pollingInterval = 2000 // 2 seconds. Ideal: 10 seconds
// const pollingTimeout = 30000 // 15 seconds. Ideal: 30 minutes
// const stableThreshold = 5000 // 5 seconds. Ideal: 45 seconds


/**
 * Watches for new files created in the provided directory, monitors them until
 * they're finished writing, then processes the files and logs messages to the
 * Electron window.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 * @param {string} directoryToWatch The directory to watch for new files.
 */
function watchForFileCreated(mainWindow, config) {
    log('Starting replays watcher', mainWindow);

    const replaysDirectory = config.replays_directory;

    const filesBeingProcessed = new Map();
    const watcherStartTime = Date.now();

    const watcher = chokidar.watch(replaysDirectory, {
        ignored: /(^|[\/\\])\../, // Ignore dot-files
        ignoreInitial: false,
        persistent: true,
        awaitWriteFinish: {
            stabilityThreshold: 2000,
            pollInterval: 100
        },
        usePolling: true  // TODO: Disable this for prod, for some reason I need this
    });

    watcher.on('add', (filePath, stats) => {
        // Only consider the file "new" if it was created after this process started
        if (stats && stats.birthtimeMs && stats.birthtimeMs > watcherStartTime) {
            if (!filesBeingProcessed.has(filePath)) {
                log(`Detected: ${stripPath(filePath)}`, mainWindow);

                filesBeingProcessed.set(filePath, { lastSize: null, stableSince: null });
                monitorFile(filePath, mainWindow, config, filesBeingProcessed);
            }
        }
    });
}

/**
 * Monitors a file until it is finished writing, defined as having a stable file
 * size for 45 seconds.
 * @param {string} filePath The file to monitor.
 * @param {BrowserWindow} mainWindow The Electron window to log messages to.
 * @param {Map} filesBeingProcessed Map of files being monitored with their state.
 */
async function monitorFile(filePath, mainWindow, config, filesBeingProcessed) {
    let fileProcessed = false;

    // Promise to monitor file size changes
    const monitorPromise = new Promise((resolve, reject) => {
        const intervalId = setInterval(async () => {
            fs.stat(filePath, async (err, stats) => {
                if (err) {
                    log(`Error: Failed to retrieve file size for: ${stripPath(filePath)}. ${err.message}`, mainWindow, 'error');
                    clearInterval(intervalId);
                    filesBeingProcessed.delete(filePath);
                    reject(err);
                    return;
                }

                const fileRecord = filesBeingProcessed.get(filePath);
                if (fileRecord.lastSize === stats.size) {
                    // If the size hasn't changed since the last check
                    if (!fileRecord.stableSince) {
                        // Initialize stable timestamp if unchanged for the first time
                        fileRecord.stableSince = Date.now();
                    } else if (Date.now() - fileRecord.stableSince > config.stable_threshold) {
                        // If the file size is stable for at least 45 seconds, process the file
                        log(`Processing: ${stripPath(filePath)}`, mainWindow);
                        // await processFile(filePath, mainWindow);
                        clearInterval(intervalId);
                        filesBeingProcessed.delete(filePath);
                        fileProcessed = true;
                        resolve();
                    }
                } else {
                    // If the file size has changed, update the last size and reset stability timer
                    fileRecord.lastSize = stats.size;
                    fileRecord.stableSince = null;
                }
            });
        }, config.polling_interval);
    });

    // Wait for the monitoring to resolve or time out
    await monitorPromise;

    // Start the timeout to cancel monitoring if not already processed
    if (!fileProcessed) {
        setTimeout(() => {
            if (filesBeingProcessed.has(filePath)) {
                log(`Detected: Ignoring long-running file: ${filePath}`, mainWindow, 'warn');
                filesBeingProcessed.delete(filePath);
            }
        }, config.discard_threshold);
    }
}

module.exports = { watchForFileCreated };
