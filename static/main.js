// Main JS for FriendAligner
// Notification icon/modal logic
document.addEventListener('DOMContentLoaded', function() {
	const notifIcon = document.getElementById('notifIcon');
	const notifModal = document.getElementById('notifModal');
	const notifCount = document.getElementById('notifCount');
	const notifList = document.getElementById('notifList');
	if (notifIcon) {
		notifIcon.onclick = function() {
			notifModal.style.display = 'block';
			loadNotifications();
		};
	}
	window.closeNotifModal = function() {
		notifModal.style.display = 'none';
	};
	async function loadNotifications() {
		const token = localStorage.getItem('jwt_token');
		if (!token) return;
		const res = await fetch('/api/notifications', {
			headers: { 'Authorization': 'Bearer ' + token }
		});
		if (!res.ok) return;
		const notifications = await res.json();
		let inviteCount = 0;
		notifList.innerHTML = '';
		for (const n of notifications) {
			const li = document.createElement('li');
			li.innerHTML = `<strong>${n.message}</strong><br><span style='color:#888;'>${n.type}</span>`;
			if (n.type === 'invite' && n.invite_id && n.status === 'pending') {
				inviteCount++;
				const actions = document.createElement('div');
				actions.style.marginTop = '0.5rem';
				actions.innerHTML = `
				  <button onclick="respondInvite(${n.invite_id}, 'accepted')">Accept</button>
				  <button onclick="respondInvite(${n.invite_id}, 'declined')">Decline</button>
				`;
				li.appendChild(actions);
			}
			notifList.appendChild(li);
		}
		notifCount.textContent = inviteCount;
		notifCount.style.display = inviteCount > 0 ? 'inline-block' : 'none';
	}
	window.respondInvite = async function(invite_id, response) {
		const token = localStorage.getItem('jwt_token');
		if (!token) return;
		const res = await fetch('/api/invite/respond', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': 'Bearer ' + token
			},
			body: JSON.stringify({ invite_id, response })
		});
		if (res.ok) {
			alert('Response recorded.');
			loadNotifications();
		} else {
			alert('Error responding to invite.');
		}
	};
	// Initial load for icon count
	if (notifIcon) {
		loadNotifications();
	}
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
		const res = await fetch('/api/calendar/calendar/create', {
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
if (document.getElementById('dateSelectionForm')) {
	document.getElementById('dateSelectionForm').onsubmit = function(e) {
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
		const group_id = localStorage.getItem('group_id');
		const calendar_id = localStorage.getItem('calendar_id');
		const email = localStorage.getItem('invite_email');
		if (!token || !email) {
			alert('Missing login or email.');
			window.location.href = '/login';
			return;
		}
		let invited_user_id = null;
		fetch(`/api/auth/user_by_email?email=${encodeURIComponent(email)}`, {
			headers: { 'Authorization': 'Bearer ' + token }
		})
		.then(res => res.ok ? res.json() : Promise.reject('User not found'))
		.then(data => {
			invited_user_id = data.user_id;
			const payload = group_id ? { group_id, invited_user_id, date: dateStr } : { calendar_id, invited_user_id, date: dateStr };
			return fetch('/api/invite/send', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': 'Bearer ' + token
				},
				body: JSON.stringify(payload)
			});
		})
		.then(async res2 => {
			if (res2.ok) {
				let result = {};
				const contentType = res2.headers.get('content-type');
				if (contentType && contentType.includes('application/json')) {
					result = await res2.json();
				}
				if (result.group_id) {
					localStorage.setItem('group_id', result.group_id);
				}
				window.location.href = '/invite_confirmation';
			} else {
				const contentType = res2.headers.get('content-type');
				if (contentType && contentType.includes('application/json')) {
					const err = await res2.json();
					throw err.error || 'Failed to send invite';
				} else {
					throw 'Failed to send invite (unexpected response)';
				}
			}
		})
		.catch(err => {
			alert('Error: ' + err);
		});
	};
}
