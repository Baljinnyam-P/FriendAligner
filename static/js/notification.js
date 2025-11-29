
// Notification handling script
document.addEventListener('DOMContentLoaded', function() {
  //If we want to keep track of notification Count
  const notifCount = document.getElementById('notifCount');
  const notifList = document.getElementById('notifList');

  async function loadNotifications() {
    const token = localStorage.getItem('jwt_token');
    if (!token) return;
    const res = await authFetch('/api/notifications', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (!res || !res.ok) return;
    const notifications = await res.json();
    let inviteCount = 0;
    notifList.innerHTML = '';
    let latestPendingInviteId = null;
    for (const n of notifications) {
      if (n.type === 'invite' && n.invite_id && n.status === 'pending') {
        if (!latestPendingInviteId) latestPendingInviteId = n.invite_id;
      }
    }
    for (const n of notifications) {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${n.message}</strong><br><span style='color:#888;'>${n.type}</span>`;
      if (
        n.type === 'invite' &&
        n.invite_id &&
        n.status === 'pending' &&
        n.invite_id === latestPendingInviteId
      ) {
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
    // Update invite count badge, remove if dont want it
    if (notifCount) {
      notifCount.textContent = inviteCount;
      notifCount.style.display = inviteCount > 0 ? 'inline-block' : 'none';
    }
  }
  //Respond to invite
  window.respondInvite = async function(invite_id, response) {
    const token = localStorage.getItem('jwt_token');
    if (!token) return;
    const res = await authFetch('/api/invite/respond', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify({ invite_id, response })
    });
    if (res && res.ok) {
      alert('Response recorded.');
      loadNotifications();
    } else {
      alert('Error responding to invite.');
    }
  };

  loadNotifications(); // Always load on page load
});