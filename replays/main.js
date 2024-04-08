const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;
const replaysDirectory = "/Users/kevinl/Documents/GitHub/fortnite-discord-bot/replays/replay_files";

/**
 * TODO:
 * 1. Convert to TS
 * 2. Implement replays processor
 * 3. Either break out repo into client and server folders or toss this into a separate repo
 *
 * Instructions:
 * 1. [Tab 1] rm -f replay_files/test.replay && npm start
 * 2. [Tab 2] cp UnsavedReplay-2024.04.06-22.45.00.replay replay_files/test.replay
 * 3. [Tab 2] cp UnsavedReplay-2024.04.06-22.29.06.replay replay_files/test.replay
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

    // Start watching for new files once the main window is fully loaded
    mainWindow.webContents.on('did-finish-load', () => {
         // Delayed require until the window is ready
        const { watchForFileCreated } = require('./src/fileWatcher');
        watchForFileCreated(mainWindow, replaysDirectory);
    });

    // Automatically open DevTools for debugging (remove in production)
    mainWindow.webContents.openDevTools();

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
