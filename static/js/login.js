// loggin using the aws credential
function login() {
    $.get($SCRIPT_ROOT + '/loggingIn',
     {
        accessKey: document.getElementById("accessKey").value,
        secretKey: document.getElementById("secretKey").value,
        securityToken: document.getElementById("securityToken").value,
        session: session
     }, function(data) {
        if (data.success) { // login successful
            location.replace("/index/" + session);
        } else {
            alert("Login Unsuccessful!"); // login fail
        }
    })
}