function login() {
    $.get($SCRIPT_ROOT + '/loggingIn',
     {
        accessKey: document.getElementById("accessKey").value,
        secretKey: document.getElementById("secretKey").value,
        securityToken: document.getElementById("securityToken").value
     }, function(data) {
        if (data.success) {
            location.replace("/index");
        } else {
            alert("Login Unsuccessful!");
        }
    })
}