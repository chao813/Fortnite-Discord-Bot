const fs = require('fs');
const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

/**
 * TODO:
 * 1. Convert to TypeScript
 * 2. After changing to not user USERPROFILE, no data shows up in the table anymore
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
    mainWindow.loadFile('../renderer/index.html');

    // Load configuration
    const configPath = path.join(__dirname, '../config/config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    console.log(`Using config replays_directory: ${config.fileMonitor.replays_directory}`);
    console.log(`Using config polling_interval: ${config.fileMonitor.polling_interval}`);
    console.log(`Using config stable_threshold: ${config.fileMonitor.stable_threshold}`);
    console.log(`Using config discard_threshold: ${config.fileMonitor.discard_threshold}`);

    // Start watching for new files once the main window is fully loaded
    mainWindow.webContents.on('did-finish-load', () => {
        // Delayed require until the window is ready
        const { watchForFileCreated } = require('./fileWatcher');
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
