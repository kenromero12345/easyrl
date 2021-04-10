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

function load(btn) {
    /*TODO: what do you do to the uploaded file*/
    input = btn.previousElementSibling;
    input.style.display = "none";
    btn.style.display = "none";
}

function makeSaveComponentsVisible(button) {
    hideUploadDownload();
    input = button.nextElementSibling;
    if (input.style.display == "none") {
        input.style.display = "inline-block";
    } else {
        input.style.display = "none";
    }

    input = input.nextElementSibling;
    if (input.style.display == "none") {
        input.style.display = "inline-block";
    } else {
        input.style.display = "none";
    }
}

function save(btn) {
    /*
        TODO: get the value to be saved & Change "test content"
    */
    input = btn.previousElementSibling;
    download("test content", input.value, "txt")
    input.style.display = "none";
    btn.style.display = "none";
    input.value = "";
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