const ul = document.getElementById('log');

// Render with context bridge
window.api.receive('log-event', (data) => {
    const logContainer = document.getElementById('log-tbody');
    const { message, level = 'info' } = data;

    const newRow = document.createElement('tr');
    const timeCell = document.createElement('td');
    const messageCell = document.createElement('td');

    newRow.classList.add(`log-${level}`);

    timeCell.textContent = new Date().toLocaleTimeString();
    messageCell.textContent = message;

    newRow.appendChild(timeCell);
    newRow.appendChild(messageCell);
    logContainer.appendChild(newRow);
});
