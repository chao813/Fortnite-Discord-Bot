const fs = require('fs');
const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

/**
 * TODO:
 * 1. Convert to TS
 * 3. Break out repo into client and server folders
 *
 * Instructions:
 * 1. [Tab 1] rm -f replay_files/test.replay && npm start
 * 2. [Tab 2 - Option 1] cp replay_files/UnsavedReplay-2024.04.06-22.45.00.replay replay_files/test.replay
 * 3. [Tab 2 - Option 2] cp replay_files/UnsavedReplay-2024.04.06-22.29.06.replay replay_files/test.replay
 */

/**
 * Create the main Electron application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true
        }
    });

    // Load HTML into the main window
    mainWindow.loadFile('index.html');

    // Load configuration; this should be UI options in the future
    const configPath = path.join(__dirname, 'config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    console.log(`Using config replays_directory: ${config.replays_directory}`);
    console.log(`Using config polling_interval: ${config.polling_interval}`);
    console.log(`Using config stable_threshold: ${config.stable_threshold}`);
    console.log(`Using config discard_threshold: ${config.discard_threshold}`);

    // Start watching for new files once the main window is fully loaded
    mainWindow.webContents.on('did-finish-load', () => {
         // Delayed require until the window is ready
        const { watchForFileCreated } = require('./src/fileWatcher');
        watchForFileCreated(mainWindow, config);
    });

    // Automatically open DevTools for debugging (remove in production)
    // mainWindow.webContents.openDevTools();

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
