// core/static/js/notifications.js

document.addEventListener('DOMContentLoaded', function() {
    const notificationSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/notifications/'
    );

    notificationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        // Display the notification to the user
        alert(data.message);
    };

    notificationSocket.onclose = function(e) {
        console.error('Notification socket closed unexpectedly');
    };
});