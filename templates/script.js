document.getElementById('loginForm').addEventListener('submit', function(event) {
    var username = document.getElementById('username').value.trim();
    var password = document.getElementById('password').value.trim();
    var errorElement = document.getElementById('error');

    if (username === '' || password === '') {
        errorElement.innerHTML = '<p>All fields are required.</p>';
        event.preventDefault();
    }
});
