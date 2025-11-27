function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);
    fetch('/api/auth/register', {
        method: 'POST',
        body: data
    })
    .then(response => response.json())
    .then(result => {
        if (result.user_id) {
            window.location.href = '/login';
        } else {
            alert(result.msg || 'Registration failed');
        }
    })
    .catch(() => alert('Registration error'));
}