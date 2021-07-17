
//making load elements visible
function makeLoadVisible(button) {
    input = button.nextElementSibling;
//    console.log(input)
//    console.log(input.tagName)
    if (input.tagName == "FORM") {
        console.log(input)
        input = input.firstElementChild;
        console.log(input)
        input = input.nextElementSibling;
        console.log(input)
    }
    uploadBtn = input.nextElementSibling;
    flag = input.style.display
    hideUploadDownload();
    if (flag == "none") {
        input.style.display = "inline-block";
        uploadBtn.style.display = "inline-block";
    }
}

//hiding upload and download elements that could be hidden
function hideUploadDownload() {
    comps = document.querySelectorAll("input[type=file], .loadBtn, .saveName, .saveNameBtn");
    for (i = 0; i < comps.length; i++) {
        comps[i].style.display = "none";
    }
}

//logging out the aws account
function logout(session) {
    $.get($SCRIPT_ROOT + '/logout/' + session, function(data) {
        location.replace("/index/" + session);
    })
}

// start a new tab
function newTab(btn) {
    input = btn.nextElementSibling;
//    newVal = parseInt(input.title) + 1;
    $.get($SCRIPT_ROOT + '/newWindow', function(data) {
        window.open('/index/' + data.session);
    })
}