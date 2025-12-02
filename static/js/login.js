// Login form submission handler, go to main menu
function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);
    fetch('/api/auth/login', {
        method: 'POST',
        body: data
    })
    .then(response => response.json())
    .then(result => {
        if (result.access_token) {
            localStorage.setItem('jwt_token', result.access_token);
            if (result.refresh_token) {
                localStorage.setItem('refresh_token', result.refresh_token);
            }
            if (result.user_id) {
                localStorage.setItem('user_id', result.user_id);
            }
            window.location.href = '/main_menu';
        } else {
            alert(result.msg || 'Login failed');
        }
    })
    .catch(() => alert('Login error'));
}