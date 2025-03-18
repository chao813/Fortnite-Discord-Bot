import { ipcRenderer } from 'electron';

window.onload = () => {
    const logContainer = document.createElement('div');
    logContainer.style.maxHeight = '400px';
    logContainer.style.overflowY = 'scroll';
    logContainer.style.border = '1px solid #ccc';
    logContainer.style.padding = '10px';

    document.body.appendChild(logContainer);

    const heading = document.createElement('h1');
    heading.textContent = 'Fortnite Replay Monitor';
    document.body.insertBefore(heading, logContainer);

    ipcRenderer.on('log-message', (event, message) => {
        console.log(`Received log: ${message}}`)
        const logEntry = document.createElement('p');
        logEntry.textContent = message;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    });
};
