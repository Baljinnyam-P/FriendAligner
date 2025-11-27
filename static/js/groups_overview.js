// Fetch and render user's groups for groups_overview.html

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
        document.querySelector('.container').innerHTML = '<div style="text-align:center; margin-top:2rem; color:red;">You must be logged in to view your groups.</div>';
        return;
    }
    fetch('/api/group/user/groups', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(response => response.json())
    .then(data => {
        const groups = data.groups || [];
        if (groups.length === 0) {
            document.querySelector('.container').innerHTML = '<div style="text-align:center; margin-top:2rem;">You are not in any groups yet.</div>';
            return;
        }
        renderGroups(groups);
    })
    .catch(() => {
        document.querySelector('.container').innerHTML = '<div style="text-align:center; margin-top:2rem; color:red;">Failed to load groups.</div>';
    });
});

// Render after DOMContentLoaded
function renderGroups(groups) {
    const container = document.querySelector('.container');
    let html = '<h2 style="text-align:center; margin-bottom:2rem;">Your Groups</h2>';
    html += '<div class="main-menu-row">';
    groups.forEach(group => {
        html += `<div class="menu-box">
            <h3>${group.group_name}</h3>
            <div style="margin-bottom:0.5em; font-size:0.95em;"><strong>Organizer:</strong> ${group.organizer.first_name} ${group.organizer.last_name}</div>
            <div style="margin-bottom:0.5em; font-size:0.95em;"><strong>Members:</strong> `;
        group.members.forEach(member => {
            html += `<span class="nameDiv">${member.first_name} ${member.last_name}</span> `;
        });
        html += `</div>
            <a href="/shared_calendar_view?group_id=${group.group_id}" class="btn view-group-calendar-btn" data-group-id="${group.group_id}">View Shared Calendar</a>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
    attachCalendarListeners();
}

function attachCalendarListeners() {
    document.querySelectorAll('.view-group-calendar-btn').forEach(btn => {
        btn.onclick = function(e) {
        };
    });
}

// Add this function to handle navigation
function goToGroupCalendar(groupId) {
    window.location.href = `/shared_calendar_view?group_id=${groupId}`;
}
