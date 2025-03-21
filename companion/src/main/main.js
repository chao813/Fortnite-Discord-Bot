const path = require('path');

const { app, BrowserWindow } = require('electron');

const { initializeConfig } = require('./config/configLoader');

let mainWindow;

/**
 * TODO:
 * 1. Convert to TypeScript
 *
 * Instructions:
 * 1. [Tab 1] rm -f replay_files/test.replay && npm start
 * 2. [Tab 2 - Option 1] cp replay_files/UnsavedReplay-2024.04.06-22.45.00.replay replay_files/test.replay
 * 3. [Tab 2 - Option 2] cp replay_files/UnsavedReplay-2024.04.06-22.29.06.replay replay_files/test.replay
 */

/**
 * Creates the main app window, loads the UI, and initializes the replay file monitor.
 *
 * @function createWindow
 * @returns {void}
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            enableRemoteModule: false
        }
    });

    mainWindow.loadFile('../renderer/index.html');

    const config = initializeConfig()
    console.log(`Using config:`, {
        replays_directory: config.fileMonitor.replays_directory,
        polling_interval: config.fileMonitor.polling_interval,
        stable_threshold: config.fileMonitor.stable_threshold
    });

    mainWindow.webContents.on('did-finish-load', () => {
        // Delayed import until the window is ready
        const { startReplayMonitoring } = require('./fileMonitor');
        startReplayMonitoring(mainWindow, config);
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/**
 * Initialize app when Electron is ready
 */
app.whenReady().then(createWindow);

/**
 * Handle MacOS specific behavior
 */
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

/**
 * Quit the application when all windows are closed (except on macOS)
 */
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
