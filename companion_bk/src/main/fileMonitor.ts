import { BrowserWindow } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

// const directoryPath = 'path/to/replays'; // Update this with the correct path
const directoryPath = ".";

let lastFileSize = 0;
let stableCount = 0;

export const monitorFiles = (mainWindow: BrowserWindow) => {
    const logMessage = (msg: string) => {
        console.log(msg);
        // Send log messages to the renderer process
        mainWindow.webContents.send('log-message', msg);
    };

    const checkForNewFiles = async () => {
        try {
        const files = await fs.promises.readdir(directoryPath);
        const latestFile = files.sort((a, b) => fs.statSync(path.join(directoryPath, b)).mtime.getTime() - fs.statSync(path.join(directoryPath, a)).mtime.getTime())[0];

        if (latestFile) {
            const filePath = path.join(directoryPath, latestFile);
            const stats = await fs.promises.stat(filePath);

            if (stats.size !== lastFileSize) {
                lastFileSize = stats.size;
                stableCount = 0;
                logMessage(`File size changed: ${latestFile} (${lastFileSize})`);
            } else {
                stableCount++;
                logMessage(`File size stable: ${latestFile} - Check #${stableCount}`);
                if (stableCount >= 3) {
                    logMessage(`Processing file: ${latestFile}`);
                    processFile(filePath, logMessage);
                    stableCount = 0; // Reset after processing
                }
            }
        } else {
            logMessage('No files found.');
        }
        } catch (err) {
            const error = err as Error;
            logMessage(`Error reading directory: ${error.message}`);
        }
    };

    // Set interval to check for new files every 30 seconds
    setInterval(checkForNewFiles, 30000);
    };

    const processFile = async (filePath: string, logMessage: (msg: string) => void) => {
    // Placeholder logic for processing file
    try {
        const jsonFilePath = path.join(path.dirname(filePath), 'output.json');
        const jsonData = { /* placeholder data */ };

        await fs.promises.writeFile(jsonFilePath, JSON.stringify(jsonData, null, 2));
        logMessage(`JSON file created: ${jsonFilePath}`);

        // Example API call
        const response = await fetch('https://httpbin.org/status/200', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
        });

        logMessage(`API response: ${response.statusText}`);
    } catch (err) {
        const error = err as Error;
        logMessage(`Error processing file: ${error.message}`);
    }
};
