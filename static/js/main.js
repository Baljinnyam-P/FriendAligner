// Logout logic
function logoutUser() {
	localStorage.clear();
	window.location.href = '/';
}

window.addEventListener('DOMContentLoaded', function() {
	const logoutBtns = document.querySelectorAll('.logoutMainPage');
	logoutBtns.forEach(btn => {
		btn.addEventListener('click', function(e) {
			e.preventDefault();
			logoutUser();
		});
	});
});

// Main Menu navigation
function goToEventFinder() {
	window.location.href = '/event_finder';
}

// Calendar Create page logic
if (document.getElementById('calendarCreateForm')) {
	function updateSelectedMonthYear() {
		const monthSelect = document.getElementById('month');
		const yearSelect = document.getElementById('year');
		const monthNames = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
		const month = monthSelect.value;
		const year = yearSelect.value;
		const label = document.getElementById('selectedMonthYear');
		if (month && year) {
			label.textContent = `${monthNames[parseInt(month)]} ${year}`;
		} else {
			label.textContent = "";
		}
	}
	document.getElementById('month').onchange = updateSelectedMonthYear;
	document.getElementById('year').onchange = updateSelectedMonthYear;
	updateSelectedMonthYear();

	document.getElementById('calendarCreateForm').onsubmit = async function(e) {
		e.preventDefault();
		const month = document.getElementById('month').value;
		const year = document.getElementById('year').value;
		const token = localStorage.getItem('jwt_token');
		if (!token) {
			alert('You must be logged in.');
			window.location.href = '/login';
			return;
		}
		const res = await authFetch('/api/calendar/calendar/create', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': 'Bearer ' + token
			},
			body: JSON.stringify({ name: `${month}/${year}` })
		});
		if (res.ok) {
			const data = await res.json();
			localStorage.setItem('calendar_id', data.calendar_id);
			localStorage.setItem('calendar_month', month);
			localStorage.setItem('calendar_year', year);
			window.location.href = '/calendar_view';
		} else {
			const err = await res.json();
			alert('Error: ' + (err.error || 'Failed to create calendar'));
		}
	};
}

// Date Selection page logic
document.getElementById('dateSelectionForm').onsubmit = async function(e) {
    e.preventDefault();
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;
    const day = document.getElementById('day').value;
    if (!month || !year || !day) {
        alert('Please select a valid date.');
        return;
    }
    const dateStr = `${year}-${month.padStart(2,'0')}-${day.padStart(2,'0')}`;
    localStorage.setItem('selected_date', dateStr);
    const token = localStorage.getItem('jwt_token');
    const email = localStorage.getItem('invite_email');
    if (!token || !email) {
        alert('Missing login or email.');
        window.location.href = '/login';
        return;
    }
    let invited_user_id = null;
    let group_id = null;
    let calendar_id = null;
    // Fetch user_id by email
    try {
        const userRes = await authFetch(`/api/auth/user_by_email?email=${encodeURIComponent(email)}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!userRes.ok) throw 'User not found';
        const userData = await userRes.json();
        invited_user_id = userData.user_id;
    } catch (err) {
        alert('Error: ' + err);
        return;
    }
    // Fetch calendar/group info from backend
    let calendarType = document.getElementById('calendarType')?.value || 'personal';
    try {
        const infoRes = await authFetch(`/api/calendar/user_info?type=${calendarType}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!infoRes.ok) throw 'Failed to fetch calendar/group info';
        const infoData = await infoRes.json();
        group_id = infoData.group_id;
        calendar_id = infoData.calendar_id;
    } catch (err) {
        alert('Error: ' + err);
        return;
    }
    // Build payload
    const payload = group_id ? { group_id, calendar_id, invited_user_id, date: dateStr } : { calendar_id, invited_user_id, date: dateStr };
    try {
        const inviteRes = await authFetch('/api/invite/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(payload)
        });
        if (inviteRes.ok) {
            window.location.href = '/invite_confirmation';
        } else {
            alert('Failed to send invite.');
        }
    } catch (err) {
        alert('Error: ' + err);
    }
};