// Utility function to get query parameters by name
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}
let injectedGroupId = getQueryParam('group_id');
// Calendar state
let currentMonth = (new Date()).getMonth() + 1;
let currentYear = (new Date()).getFullYear();

function updateMonthYearLabel() {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const label = document.getElementById("calendarMonthYear");
    if (label) label.textContent = `${monthNames[currentMonth-1]} ${currentYear}`;
}

// Fetch user, group, and calendar info from backend for session
function fetchUserContext() {
    const token = localStorage.getItem('jwt_token');
    if (!token) return Promise.reject('Missing token');
    let url = `/api/calendar/user_info?type=${selectedCalendarType}`;
    if (selectedCalendarType === 'group' && injectedGroupId) {
        url += `&group_id=${injectedGroupId}`;
    }
    return authFetch(url, {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(response => response.json())
    .then(data => ({
        user_id: data.user_id,
        group_id: data.group_id,
        calendar_id: data.calendar_id,
        calendar_type: data.calendar_type
    }));
}

// Render calendar grid for personal calendar
function renderPersonalCalendarGrid(calendar_id, user_id, token) {
    const calendar = document.getElementById("calendarGrid");
    if (!calendar) return;
    calendar.innerHTML = "";
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const firstDay = new Date(currentYear, currentMonth-1, 1).getDay();

    authFetch(`/api/calendar/personal/${user_id}/${currentYear}/${currentMonth}`, {
        method: "GET",
        headers: {"Authorization": "Bearer " + token}
    })
    .then(response => response.json())
    .then(data => {
        const avails = data.availabilities || [];
        const events = data.events || [];
        const availMap = {};
        const eventMap = {};
        // Map availabilities by date
        avails.forEach(a => {
            availMap[a.date] = { status: a.status, description: a.description };
            if (a.status === 'event') eventMap[a.date] = a;
        });
        // Map events by date
        const eventsByDate = {};
        events.forEach(e => {
            eventsByDate[e.date] = e;
        });
        // Render empty cells before first day
        for (let i = 0; i < firstDay; i++) {
            const emptyDiv = document.createElement("div");
            emptyDiv.className = "day empty";
            calendar.appendChild(emptyDiv);
        }
        // Render each day of the month
        for(let d = 1; d <= daysInMonth; d++) {
            const dayDiv = document.createElement("div");
            dayDiv.className = "day";
            dayDiv.textContent = d;
            const dateStr = `${currentYear}-${String(currentMonth).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            let hasEvent = false;
            // Render availability status and description
            if (availMap[dateStr]) {
                const statusDiv = document.createElement("div");
                statusDiv.className = "status";
                const status = availMap[dateStr].status;
                statusDiv.textContent = status;
                if (status === "available") {
                    statusDiv.classList.add("status-available");
                } else if (status === "busy") {
                    statusDiv.classList.add("status-busy");
                } else if (status === "not sure") {
                    statusDiv.classList.add("status-not-sure");
                }
                dayDiv.appendChild(statusDiv);
                if (availMap[dateStr].description) {
                    const descDiv = document.createElement("div");
                    descDiv.className = "availability-description status-desc";
                    descDiv.textContent = availMap[dateStr].description;
                    dayDiv.appendChild(descDiv);
                }
            }
            // Render event from Events table
            if (eventsByDate[dateStr]) {
                hasEvent = true;
                const eventDiv = document.createElement("div");
                eventDiv.className = "event-status";
                eventDiv.textContent = eventsByDate[dateStr].name || "Event";
                dayDiv.appendChild(eventDiv);
            }
            // Modal logic: pass event details if present
            dayDiv.onclick = () => {
                if (hasEvent) {
                    openModal(dateStr, eventsByDate[dateStr], calendar_id, user_id, token, "personal");
                } else if (eventMap[dateStr]) {
                    openModal(dateStr, eventMap[dateStr], calendar_id, user_id, token, "personal");
                } else {
                    openModal(dateStr, null, calendar_id, user_id, token, "personal");
                }
            };
            calendar.appendChild(dayDiv);
        }
    });
}

// Render calendar grid for group calendar (multiple users per date)
function renderGroupCalendarGrid(calendar_id, group_id, token) {
    const calendar = document.getElementById("calendarGrid");
    if (!calendar) return;
    calendar.innerHTML = "";
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();

    // Fetch availabilities and events from backend
    Promise.all([
        authFetch(`/api/calendar/${calendar_id}/availabilities`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        }).then(response => response.json()),
        authFetch(`/api/events/group/${group_id}`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        }).then(response => response.json())
    ]).then(([availabilities, events]) => {
        const dateMap = {};
        availabilities = availabilities || [];
        events = events || [];
        availabilities.forEach(a => {
            let normalizedDate = a.date;
            if (typeof normalizedDate === "string" && normalizedDate.includes("T")) {
                normalizedDate = normalizedDate.split("T")[0];
            }
            if (!dateMap[normalizedDate]) dateMap[normalizedDate] = [];
            //for each date, push all user availabilities
            dateMap[normalizedDate].push({
                user_id: a.user_id,
                user_name: a.user_name,
                status: a.status,
                description: a.description
            });
        });
        // Map events by date
        const eventsByDate = {};
        events.forEach(e => {
            const eventDate = e.date.split('T')[0];
            eventsByDate[eventDate] = e;
        });
        // Render empty cells before first day
        for (let i = 0; i < firstDay; i++) {
            const emptyDiv = document.createElement("div");
            emptyDiv.className = "day empty";
            calendar.appendChild(emptyDiv);
        }
        // Render each day of the month
        for (let d = 1; d <= daysInMonth; d++) {
            const dayDiv = document.createElement("div");
            dayDiv.className = "day";
            dayDiv.textContent = d;
            const dateStr = `${currentYear}-${String(currentMonth).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                // Render each group member's status and description
                if (dateMap[dateStr]) {
                    dateMap[dateStr].forEach(avail => {
                        const memberDiv = document.createElement("div");
                        memberDiv.className = "group-member-availability";
                        let statusClass = "";
                        if (avail.status === "available") statusClass = "status-available";
                        else if (avail.status === "busy") statusClass = "status-busy";
                        else if (avail.status === "not sure") statusClass = "status-not-sure";
                        memberDiv.innerHTML = `<strong class='${statusClass}'>${avail.user_name}:</strong> <span class='${statusClass}'>${avail.status}</span>`;
                        dayDiv.appendChild(memberDiv);
                    });
                // Store details for modal expansion
                dayDiv.dataset.availDetails = JSON.stringify(dateMap[dateStr]);
                }
            // Render event from Events table
                let hasEvent = false;
                if (eventsByDate[dateStr]) {
                    hasEvent = true;
                    const event = eventsByDate[dateStr];
                    const eventDiv = document.createElement("div");
                    eventDiv.className = "event";
                    if (event.status === "finalized") {
                        const badge = document.createElement("span");
                        badge.className = "finalized-badge";
                        badge.textContent = "Event Finalized";
                        eventDiv.appendChild(badge);
                    } else if (event.status === "suggested") {
                        const badge = document.createElement("span");
                        badge.className = "suggested-badge";
                        badge.textContent = "Event Suggested";
                        eventDiv.appendChild(badge);
                    }
                    // Event name
                    const titleSpan = document.createElement("span");
                    titleSpan.className = "event-title";
                    titleSpan.textContent = event.name || "Event";
                    eventDiv.appendChild(titleSpan);
                    dayDiv.appendChild(eventDiv);
                }
            // Modal logic: pass event details if present
            dayDiv.onclick = () => {
                // If group calendar, expand modal to show all member availabilities for this date
                let availDetails = [];
                if (dayDiv.dataset.availDetails) {
                    try {
                        availDetails = JSON.parse(dayDiv.dataset.availDetails);
                    } catch {}
                }
                openModal(dateStr, hasEvent ? eventsByDate[dateStr] : null, calendar_id, null, token, "group", availDetails);
            };
            calendar.appendChild(dayDiv);
        }
    });
}


// Remove events from both calendars
function deleteEventFromCalendar(event_id, calendar_id, token) {
    if (!event_id || !token) return;
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
// Remove event from personal calendar
function removePersonalEvent(availability_id, dateStr, calendar_id, token) {
    if (!availability_id || !token || !calendar_id) return;
    authFetch(`/api/events/remove_personal_event/${availability_id}`, {
        method: "DELETE",
        headers: {"Authorization": "Bearer " + token}
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || "Event removed.");
        renderCalendar();
    })
    .catch(() => {
        alert("Error removing event.");
    });
}

// Modal logic, fetch context from backend first
function openModal(date, eventDetails, calendar_id, user_id, token, calendar_type, groupAvailDetails = []) {
    document.getElementById("modal").style.display = "block";
    document.getElementById("modalDate").textContent = date;
    document.getElementById("availabilityInput").value = "";
    document.getElementById("availabilityStatusDropdown").value = "available";
    // If groupAvailDetails provided, render all member availabilities in modal
    const groupAvailDiv = document.getElementById("groupAvailDetails");
    if (groupAvailDiv) {
        groupAvailDiv.innerHTML = "";
        if (groupAvailDetails.length > 0) {
            groupAvailDiv.innerHTML = `<h4>Group Member Availabilities</h4>`;
            groupAvailDetails.forEach(avail => {
                const memberDiv = document.createElement("div");
                memberDiv.className = "group-member-availability";
                memberDiv.innerHTML = `<strong>${avail.user_name}</strong>: ${avail.status}` + (avail.description ? ` <span class='status-user-desc'>(${avail.description})</span>` : "");
                groupAvailDiv.appendChild(memberDiv);
            });
        }
    }

    const eventFinderBtn = document.getElementById("goToEventFinderBtn");
    if (eventFinderBtn) {
        eventFinderBtn.onclick = function() {
            window.location.href = '/event_finder?date=' + encodeURIComponent(date);
        };
    }
    if (eventDetails) {
        // Build modal HTML for event details using CSS classes for styling
        let infoHtml = `<div class='event-modal-content'>`;
        // Event name: place_url link (clicking on it goes to google places on map)
        if (eventDetails.place_url || eventDetails.address) {
            const mapsUrl = eventDetails.place_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(eventDetails.address || eventDetails.name)}`;
            infoHtml += `<p><strong>Name:</strong> <a href='${mapsUrl}' target='_blank' class='event-modal-title-link'>${eventDetails.name || 'Event'}</a></p>`;
        } else {
            infoHtml += `<p><strong>Name:</strong> ${eventDetails.name || 'Event'}</p>`;
        }
        // Place link (Google Maps Place URL) if available
        if (eventDetails.place_url) {
            if (eventDetails.address) {
                const mapsUrl = eventDetails.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(eventDetails.address)}`;
                infoHtml += `<p><strong>Address:</strong> <a href='${mapsUrl}' target='_blank' class='event-modal-address'>${eventDetails.address}</a></p>`;
            }
        } else if (eventDetails.address) {
            const mapsUrl = eventDetails.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(eventDetails.address)}`;
            infoHtml += `<p><strong>Address:</strong> <a href='${mapsUrl}' target='_blank' class='event-modal-address'>${eventDetails.address}</a></p>`;
        }
        // Render images on the modal, Optional
        if (eventDetails.image_url) infoHtml += `<img src='${eventDetails.image_url}' alt='Event image' class='event-modal-image'>`;
        // Modal action buttons (edit/delete)
        infoHtml += `<div class='event-modal-actions'>`;
        // Remove button for Events table events
        if (eventDetails.event_id) {
            infoHtml += `<button class='remove-event-btn' title='Delete Event'><span class='remove-icon'>&#128465;</span> Remove Event</button>`;
        }
        // Remove button for Availability Event
        if (eventDetails.availability_id) {
            infoHtml += `<button class='remove-availability-btn' title='Remove Event'><span class='remove-icon'>&#128465;</span> Remove Event</button>`;
        }
        // Show finalize button in modal if organizer and event is suggested
        if (
            eventDetails &&
            eventDetails.status === "suggested" &&
            String(localStorage.getItem("user_id")) === String(localStorage.getItem("organizer_id"))
        ) {
            infoHtml += `<button class='finalize-btn' id='finalizeEventBtn'>Finalize</button>`;
        }
        infoHtml += `</div>`;
        infoHtml += `</div>`;
        document.getElementById("availabilityInfo").innerHTML = infoHtml;
        window.currentAvailabilityId = eventDetails.availability_id || null;
        // If status matches dropdown, set dropdown, else set description
        const statusDropdown = document.getElementById("availabilityStatusDropdown");
        const statusInput = document.getElementById("availabilityInput");
        if (statusDropdown && statusInput) {
            const statusVal = eventDetails.status || '';
            if (["available","busy","not sure"].includes(statusVal)) {
                statusDropdown.value = statusVal;
                statusInput.value = eventDetails.description || '';
            } else {
                statusDropdown.value = "available";
                statusInput.value = statusVal;
            }
        }
        // Attach icon button actions
        const removeBtn = document.querySelector('.remove-event-btn');
        if (removeBtn && eventDetails.event_id) {
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                if (confirm("Delete this event from your calendar?")) {
                    if (typeof deleteEventFromCalendar === 'function') {
                        deleteEventFromCalendar(eventDetails.event_id, calendar_id, token);
                    } else if (window.deleteEventFromCalendar) {
                        window.deleteEventFromCalendar(eventDetails.event_id, calendar_id, token);
                    }
                    closeModal();
                }
            };
        }
        const removeAvailBtn = document.querySelector('.remove-availability-btn');
        if (removeAvailBtn && eventDetails.availability_id) {
            removeAvailBtn.onclick = (e) => {
                e.stopPropagation();
                if (confirm("Remove this event from your calendar?")) {
                    removePersonalEvent(eventDetails.availability_id, date, calendar_id, token);
                    closeModal();
                }
            };
        }
        // Finalize button logic
        const finalizeBtn = document.getElementById("finalizeEventBtn");
        if (finalizeBtn && eventDetails && eventDetails.event_id) {
            finalizeBtn.onclick = function(e) {
                e.stopPropagation();
                fetch(`/api/events/finalize/${eventDetails.event_id}`, {
                    method: "POST",
                    headers: { "Authorization": "Bearer " + token }
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    closeModal();
                    renderCalendar();
                });
            };
        }
        return;
    }
    document.getElementById("availabilityInfo").textContent = "Loading...";
    if (!calendar_id || !user_id || !token) {
        document.getElementById("availabilityInfo").textContent = "Missing calendar or user info.";
        return;
    }
    window.currentAvailabilityId = null;
    window.activeCalendarId = calendar_id;
    // For group calendar, fetch user's availability for the date
    let url = calendar_type === "group"
        ? `/api/calendar/${calendar_id}/availability/${user_id}/${date}`
        : `/api/calendar/${calendar_id}/availability/${user_id}/${date}`;
    authFetch(url, {
        method: "GET",
        headers: {"Authorization": "Bearer " + token}
    })
    .then(response => response.json())
    .then(data => {
        const statusDropdown = document.getElementById("availabilityStatusDropdown");
        const statusInput = document.getElementById("availabilityInput");
        if (data.status) {
            document.getElementById("availabilityInfo").textContent = `Status: ${data.status}`;
            if (["available","busy","not sure"].includes(data.status)) {
                statusDropdown.value = data.status;
                statusInput.value = data.description || '';
            } else {
                statusDropdown.value = "available";
                statusInput.value = data.status;
            }
            window.currentAvailabilityId = data.availability_id;
        } else if (data.error) {
            document.getElementById("availabilityInfo").textContent = data.error;
        } else {
            document.getElementById("availabilityInfo").textContent = "No availability found.";
        }
    })
    .catch(() => {
        document.getElementById("availabilityInfo").textContent = "Error fetching availability.";
    });
}

function closeModal() {
    document.getElementById("modal").style.display = "none";
    document.getElementById("availabilityInput").value = "";
}

function saveAvailability() {
    fetchUserContext().then(ctx => {
        const date = document.getElementById("modalDate").textContent;
        const status = document.getElementById("availabilityStatusDropdown").value;
        const description = document.getElementById("availabilityInput").value;
        const token = localStorage.getItem('jwt_token');
        const calendar_id = ctx.calendar_id;
        const group_id = ctx.group_id;
        if (!calendar_id || !token) {
            alert('Missing calendar or login info.');
            return;
        }
        const payload = { date, status };
        if (description) payload.description = description;
        //If currentAvailabilityId exists, do PUT to update, else POST to create new
        if (window.currentAvailabilityId) {
            authFetch(`/api/calendar/${calendar_id}/availability/${window.currentAvailabilityId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || 'Availability updated.');
                closeModal();
                renderCalendar();
            })
            .catch(() => {
                alert('Error updating availability.');
            });
        } else {
            authFetch(`/api/calendar/${calendar_id}/availability`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || 'Availability saved.');
                closeModal();
                renderCalendar();
            })
            .catch(() => {
                alert('Error saving availability.');
            });
        }
    });
}

// Main render function: auto-detect calendar type and render accordingly
function renderCalendar() {
    updateMonthYearLabel();
    const token = localStorage.getItem('jwt_token');
    if (selectedCalendarType === "group" && injectedGroupId) {
        // Fetch calendar_id for this group from backend
        fetchUserContext().then(ctx => {
            const calendar_id = ctx.calendar_id;
            if (!calendar_id || !token) {
                document.getElementById("calendarGrid").innerHTML = '<div class="calendar-error">Missing calendar or user info.';
                return;
            }
            renderGroupCalendarGrid(calendar_id, injectedGroupId, token);
        }).catch(() => {
            document.getElementById("calendarGrid").innerHTML = '<div class="calendar-error">Failed to fetch calendar context.';
        });
        return;
    }
    fetchUserContext().then(ctx => {
        const { calendar_id, user_id, group_id, calendar_type } = ctx;
        if (!calendar_id || !token) {
            document.getElementById("calendarGrid").innerHTML = '<div class="calendar-error">Missing calendar or user info.</div>';
            return;
        }
        if (calendar_type === "group") {
            renderGroupCalendarGrid(calendar_id, group_id, token);
        } else {
            renderPersonalCalendarGrid(calendar_id, user_id, token);
        }
    }).catch(() => {
        document.getElementById("calendarGrid").innerHTML = '<div class="calendar-error">Failed to fetch calendar context.</div>';
    });
}

//When DOM is loaded, setup buttons and render calendar
// Event listeners for month navigation and modal actions
window.addEventListener('DOMContentLoaded', function() {
    const prevBtn = document.getElementById("prevMonthBtn");
    const nextBtn = document.getElementById("nextMonthBtn");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const saveAvailabilityBtn = document.getElementById("saveAvailabilityBtn");

    
    if (prevBtn) prevBtn.onclick = function() {
        currentMonth--;
        if (currentMonth < 1) {
            currentMonth = 12;
            currentYear--;
        }
        renderCalendar();
    };
    
    if (nextBtn) nextBtn.onclick = function() {
        currentMonth++;
        if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
        }
        renderCalendar();
    };
    
    if (closeModalBtn) closeModalBtn.onclick = closeModal;
    if (saveAvailabilityBtn) saveAvailabilityBtn.onclick = saveAvailability;
    
    // Fetch and render group info if on shared calendar
    if (selectedCalendarType === "group") {
        const token = localStorage.getItem('jwt_token');
        fetchUserContext().then(function(ctx) {
    if (ctx.group_id) {
        fetchAndRenderGroupMembers(ctx.group_id, token, ctx.user_id);
        }
    });
    }
    renderCalendar();
});

function removeMemberFromGroup(group_id, user_id, token, memberElem) {
    authFetch(`/api/group/${group_id}/remove_member`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ user_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            // re-fetch and re-render members:
            fetchAndRenderGroupMembers(group_id, token);
            renderCalendar();
        } else {
            alert(data.error || "Failed to remove member.");
        }
    })
    .catch(() => {
        alert("Error removing member.");
    });
}

function fetchAndRenderGroupMembers(group_id, token, currentUserId) {
    authFetch(`/api/group/${group_id}/members`, {
        method: "GET",
        headers: { "Authorization": "Bearer " + token }
    })
    .then(response => response.json())
    .then(data => {
        // Store organizer_id for later use
        localStorage.setItem("organizer_id", data.organizer_id);
        document.getElementById("groupName").textContent = data.group_name ? `Group: ${data.group_name}` : "Group";
        const membersDiv = document.getElementById("groupMembers");
        membersDiv.innerHTML = '<strong>Members:</strong> ';
        (data.members || []).forEach(m => {
            const memberSpan = document.createElement('span');
            memberSpan.textContent = `${m.first_name || ""} ${m.last_name || ""}`.trim();
            memberSpan.className = "group-member-name";
            // Only show remove button if current user is organizer and member is not organizer
            if (Number(currentUserId) === Number(data.organizer_id) && m.user_id !== data.organizer_id) {
                const removeBtn = document.createElement('button');
                removeBtn.textContent = "Remove";
                removeBtn.className = "remove-member-btn";
                removeBtn.onclick = function() {
                    if (confirm(`Remove ${memberSpan.textContent} from group? This will also remove their availabilities.`)) {
                        removeMemberFromGroup(group_id, m.user_id, token, currentUserId);
                    }
                };
                memberSpan.appendChild(removeBtn);
            }
            membersDiv.appendChild(memberSpan);
            membersDiv.appendChild(document.createTextNode(", "));
        });
        // Remove trailing comma
        if (membersDiv.lastChild) membersDiv.removeChild(membersDiv.lastChild);
    });
}