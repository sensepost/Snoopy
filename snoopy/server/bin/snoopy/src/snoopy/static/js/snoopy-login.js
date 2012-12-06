$(document).ready(function() {
    $('input[type="text"]').toggleInputValue();

    $('form').submit(function(ev) {
        f = $(ev.target);
        user = f.find('input[name="username"]').val();
        pass = f.find('input[name="password"]').val();
        if (!user || user == 'username' || !pass) {
            alert('Invalid login');
            return false;
        }
        $('#flashmsg').text('Logging in...');
        $.post('/login', { username: user, password: pass })
            .success(function() {
                $('#flashmsg').text('Login successful.');
                window.setTimeout(function() { window.location = '/'; }, 1000);
            })
            .error(function() {
                $('#flashmsg').text('Login failed :(');
            });
        return false;
    });
});
