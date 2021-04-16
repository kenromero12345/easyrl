function updateSlider(slider) {
    var txtIn = slider.parentElement.querySelector(".customInput");
    txtIn.value = slider.value;
}

function updateInput(input) {
    var slider = input.parentElement.querySelector("input[type=range]");

    if (input.value > slider.max) {
        slider.value = slider.max;
        input.value = slider.max;
    } else if (input.value < slider.min) {
        slider.value = slider.min;
        input.value = slider.min;
    } else {
        slider.value = input.value;
    }
}

function makeSaveComponentsVisible(button) {
    input = button.nextElementSibling;
    downloadBtn = input.nextElementSibling;
    flag = input.style.display
    hideUploadDownload();
    if (flag == "none") {
        input.style.display = "inline-block";
        downloadBtn.style.display = "inline-block";
    }
}

/*
    Copied from stackoverflow
*/
function download(data, filename, type) {
    var file = new Blob([data], {type: type});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
                url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}