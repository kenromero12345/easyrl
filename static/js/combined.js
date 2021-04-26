
//making load elements visible
function makeLoadVisible(button) {
    input = button.nextElementSibling;
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