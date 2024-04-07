const ul = document.getElementById('log');

// renderer.js (with context bridge)
window.api.receive('log-event', (message) => {
    // Create log entries in the HTML
    const logContainer = document.getElementById('log');
    const logEntry = document.createElement('div');
    logEntry.textContent = message;
    logContainer.appendChild(logEntry);
});
