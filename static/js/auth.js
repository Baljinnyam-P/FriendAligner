// Get JWT token from localStorage
function getJwtToken() {
    return localStorage.getItem('jwt_token');
}

// Instead of normal fetch, this fetch function is used to fetch
//endpoints that requires authentication with JWT token.
// It automatically handles token refresh if access token is expired.
async function authFetch(url, options = {}) {
    let accessToken = localStorage.getItem('jwt_token');
    let refreshToken = localStorage.getItem('refresh_token');
    options.headers = options.headers || {};
    options.headers['Authorization'] = 'Bearer ' + accessToken;

    let res = await fetch(url, options);
    if (res.status === 401 && refreshToken) {
        // Try to refresh the access token
        const refreshRes = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + refreshToken }
        });
        if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem('jwt_token', data.access_token);
            options.headers['Authorization'] = 'Bearer ' + data.access_token;
            res = await fetch(url, options); // Retry original request
        } else {
            // Refresh failed, logout
            localStorage.clear();
            window.location.href = '/login';
            return;
        }
    }
    return res;
}

// Export to window for global use
window.getJwtToken = getJwtToken;
window.authFetch = authFetch;
