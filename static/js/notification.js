
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
      // Add mark as read button if unread
      if (!n.read) {
        const markBtn = document.createElement('button');
        markBtn.textContent = 'Mark as Read';
        markBtn.className = 'notif-mark-read-btn';
        markBtn.style.marginLeft = '1em';
        markBtn.onclick = async function() {
          await markNotificationRead(n.notification_id);
          li.style.opacity = '0.5';
          markBtn.disabled = true;
          // Update notification count badge in navbar immediately
          updateNotifCount();
        };
        li.appendChild(markBtn);
      }
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
    // Helper to update notification count badge
    function updateNotifCount() {
      const unreadCount = notifications.filter(n => !n.read).length;
      if (notifCount) {
        notifCount.textContent = unreadCount;
        notifCount.style.display = unreadCount > 0 ? 'inline-block' : 'none';
      }
    }
    // Mark notification as read
    async function markNotificationRead(notification_id) {
      const token = localStorage.getItem('jwt_token');
      if (!token) return;
      await authFetch(`/api/notifications/${notification_id}/read`, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token }
      });
    }
    // Update notification count badge in navbar (show only unread)
    if (notifCount) {
      const unreadCount = notifications.filter(n => !n.read).length;
      notifCount.textContent = unreadCount;
      notifCount.style.display = unreadCount > 0 ? 'inline-block' : 'none';
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