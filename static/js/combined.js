function makeLoadVisible(button) {
    input = button.nextElementSibling;
    uploadBtn = input.nextElementSibling;
//    console.log(input.style.display)
    flag = input.style.display
    hideUploadDownload();
    if (flag == "none") {
        input.style.display = "inline-block";
        uploadBtn.style.display = "inline-block";
    }
}

function hideUploadDownload() {
    comps = document.querySelectorAll("input[type=file], .loadBtn, .saveName, .saveNameBtn");
    for (i = 0; i < comps.length; i++) {
        comps[i].style.display = "none";
    }
}