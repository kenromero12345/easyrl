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