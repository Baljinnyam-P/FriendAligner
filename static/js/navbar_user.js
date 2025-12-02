// Display logged-in user's name in navbar
async function displayNavbarUser() {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    try {
      // Get user id from token (if available)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const userId = payload.sub || payload.identity || payload.user_id;
      let url = '/api/auth/user_by_email';
      let email = null;
      if (payload.email) {
        email = payload.email;
        url += `?email=${encodeURIComponent(email)}`;
      }
      const res = await fetch(url, {
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        method: 'GET',
      });
      if (res.ok) {
        const user = await res.json();
        if (user.first_name && user.last_name) {
          document.getElementById('navbarUser').textContent = user.first_name + ' ' + user.last_name;
        } else if (user.email) {
          document.getElementById('navbarUser').textContent = user.email;
        }
      }
    } catch {}
  }
}

document.addEventListener('DOMContentLoaded', function() {
  displayNavbarUser();
  // Global unread notification counter
  async function updateGlobalNotifCount() {
    const notifCount = document.getElementById('notifCount');
    const token = localStorage.getItem('jwt_token');
    if (!notifCount || !token) return;
    try {
      const res = await fetch('/api/notifications', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (!res.ok) return;
      const notifications = await res.json();
      const unreadCount = notifications.filter(n => !n.read).length;
      notifCount.textContent = unreadCount;
      notifCount.style.display = unreadCount > 0 ? 'inline-block' : 'none';
    } catch {}
  }
  updateGlobalNotifCount();
  // Logout link logic
  const logoutLink = document.querySelector('.logout-link');
  if (logoutLink) {
    logoutLink.onclick = function(e) {
      e.preventDefault();
      localStorage.clear();
      window.location.href = '/';
    };
  }
});