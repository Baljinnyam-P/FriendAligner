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
            window.location.href = '/main_menu';
        } else {
            alert(result.msg || 'Login failed');
        }
    })
    .catch(() => alert('Login error'));
}
