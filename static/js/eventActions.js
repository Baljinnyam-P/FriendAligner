// Delete event from Events table (personal calendar)
function deleteEventFromCalendar(event_id, calendar_id, token) {
    if (!event_id || !token || !calendar_id) return;
    authFetch(`/api/events/${event_id}`, {
        method: "DELETE",
        headers: {"Authorization": "Bearer " + token}
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || "Event deleted.");
        renderCalendar();
    })
    .catch(() => {
        alert("Error deleting event.");
    });
}
