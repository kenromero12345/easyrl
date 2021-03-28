window.onload = function () {

    //chart

    var dps = []; // dataPoints
    var chart = new CanvasJS.Chart("chartContainer", {
        title :{
          text: "Dynamic Data"
        },
        data: [{
          type: "line",
          dataPoints: dps
        }],
        exportEnabled: true,
        width: 600,
        height:250,
    });

    var xVal = 0;
    var yVal = 100;
    var updateInterval = 100;
    var dataLength = 20; // number of dataPoints visible at any point

    var updateChart = function (count) {

        count = count || 1;

        for (var j = 0; j < count; j++) {
            yVal = yVal +  Math.round(5 + Math.random() *(-5-5));
            dps.push({
                x: xVal,
                y: yVal
            });
            xVal++;
      }

//        if (dps.length > dataLength) {
//          dps.shift();
//        }

        chart.render();
    };

    updateChart(dataLength);
    setInterval(function(){updateChart()}, updateInterval);


    //TODO: use the parameters <agent> and <environment>

}

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

//function save() {
//    val = "";
//    mydoc = document.open();
//    mydoc.write(val);
//    mydoc.execCommand("saveAs",true,".txt"); //you can change the .txt to your extention
//    mydoc.close();
////    history.go(-1);
//}

function makeLoadVisible(button) {
    input = button.nextElementSibling;
    uploadBtn = input.nextElementSibling;
    console.log(input.style.display)
    if (input.style.display == "none") {
        input.style.display = "inline-block";
        uploadBtn.style.display = "inline-block";
    } else {
        input.style.display = "none";
        uploadBtn.style.display = "none";
    }
}

function load(btn) {
    /*TODO: what do you do to the uploaded file*/
    input = btn.previousElementSibling;
    input.style.display = "none";
    btn.style.display = "none";
}

function makeSaveComponentsVisible(button) {
    input = button.nextElementSibling;
    console.log(input.style.display)
    if (input.style.display == "none") {
        input.style.display = "inline-block";
    } else {
        input.style.display = "none";
    }

    input = input.nextElementSibling;
    console.log(input.style.display)
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