const ul = document.getElementById('log');

// Render with context bridge
window.api.receive('log-event', (message) => {
    const logContainer = document.getElementById('log-tbody');

    const newRow = document.createElement('tr');
    const time_cell = document.createElement('td');
    const message_cell = document.createElement('td');

    time_cell.textContent = new Date().toLocaleTimeString();
    message_cell.textContent = message;

    newRow.appendChild(time_cell);
    newRow.appendChild(message_cell);
    logContainer.appendChild(newRow);
});
