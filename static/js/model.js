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

function test() {
    if (!isRunning) {
        var lists = document.querySelectorAll("input[type=range]");
        var params = {}
        for (var i = 0; i < lists.length; i++) {
            params[i] = lists[i].value;
        }
        $.getJSON($SCRIPT_ROOT + '/startTest', params, function(data) {
            if (data.model) {
                trainBtn.disabled = true;
                updateLoadModDisabled(true);
                isRunning = true;
                chartReset();
                testRecursion();
            } else {
                window.alert("Model has not been trained!");
            }
        });
    }
}

function train() {
    if (!isRunning) {
        testBtn.disabled = true;
        updateLoadModDisabled(true);
        isRunning = true;
        chartReset()
        var lists = document.querySelectorAll("input[type=range]");
        var params = {}
        for (var i = 0; i < lists.length; i++) {
            params[i] = lists[i].value;
        }
        $.getJSON($SCRIPT_ROOT + '/startTrain', params, function(data) {
            trainRecursion()
        });
    }
}

function testRecursion() {
    $.getJSON($SCRIPT_ROOT + '/runTest', function(data) {
        if (data.finished) {
            isRunning = false;
            trainBtn.disabled = false;
            updateLoadModDisabled(false);
        } else {
            if (isReset) {
                isRunning = false;
                isReset = false;
                chartReset();
                trainBtn.disabled = false;
                updateLoadModDisabled(false);
            } else {
                chartRewardAdd(xVal, data.reward);
                xVal++;
                chart.render();
                testRecursion();
                totalTrainingRewardVal += data.reward;
                totalTrainingReward.innerHTML = totalTrainingRewardVal.toFixed(2);
                rewardPerEpisode.innerHTML = (totalTrainingRewardVal/xVal).toFixed(2);
            }
        }
    });
}

function trainRecursion() {
    $.getJSON($SCRIPT_ROOT + '/runTrain', function(data) {
        if (data.finished) {
            isRunning = false;
            testBtn.disabled = false;
            updateLoadModDisabled(false);
        } else {
            if (isReset) {
                isRunning = false;
                isReset = false;
                chartReset();
                testBtn.disabled = false;
                updateLoadModDisabled(false);
            } else {
                chartLossAdd(xVal, data.loss);
                chartRewardAdd(xVal, data.reward);
                chartEpsilonAdd(xVal, data.epsilon);
                xVal++;
                chart.render();
                trainRecursion();
                totalTrainingRewardVal += data.reward;
                totalTrainingReward.innerHTML = totalTrainingRewardVal.toFixed(2);
                rewardPerEpisode.innerHTML = (totalTrainingRewardVal/xVal).toFixed(2);
            }
        }
    });
}
function chartLossAdd(index, loss) {
    dpsLoss.push({
        x: index,
        y: loss
    });
}

function chartRewardAdd(index, reward) {
    dpsReward.push({
        x: index,
        y: reward
    });
}

function chartEpsilonAdd(index, epsilon) {
    dpsEpsilon.push({
        x: index,
        y: epsilon
    });
}

function saveResults(btn) {
    input = btn.previousElementSibling;
    var results = "";
    for(var i = 0; i < dpsLoss.length; i++) {
        results += (i+1) + ", " + dpsLoss[i].y + ", " + dpsReward[i].y + ", " + dpsEpsilon[i].y + "\n";
    }
    download(results, input.value, "txt")
    input.style.display = "none";
    btn.style.display = "none";
    input.value = "";
}

function saveModel(btn) {
    input = btn.previousElementSibling;
    $.getJSON($SCRIPT_ROOT + '/saveModel', function(data) {
        download(data.agent, input.value, "txt")
        input.style.display = "none";
        btn.style.display = "none";
        input.value = "";
    });
}

function loadModel(btn) {
    input = btn.previousElementSibling
    input.style.display = "none";
    btn.style.display = "none";
    var fr = new FileReader();
    var temp;
    fr.onload=function(){
        temp = fr.result;
        $.getJSON($SCRIPT_ROOT + '/loadModel', {
            agent: temp
        }, function(data) {
            if (data.success) {
                window.alert("Model Uploaded");
            } else {
                window.alert("Incorrect Model! Loading Unsuccessful");
            }
            input.style.display = "none";
            btn.style.display = "none";
            input.value = "";
        });
    }
    fr.readAsText(input.files[0]);
}

function toggleDataSeries(e) {
    if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
        e.dataSeries.visible = false;
    } else {
        e.dataSeries.visible = true;
    }
    e.chart.render();
}

function reset() {
    if (isRunning) {
        isRunning = false;
        isReset = true;
    } else {
        chartReset();
    }
    $.getJSON($SCRIPT_ROOT + '/reset');
}

function halt() {
    isRunning = false;
    $.getJSON($SCRIPT_ROOT + '/halt')
}

function chartReset() {
    dpsLoss = []
    dpsReward = []
    dpsEpsilon = []
    xVal = 1;
    chart = createChart()
    chart.render()
    totalTrainingRewardVal = 0
    totalTrainingReward.innerHTML = 0
    rewardPerEpisode.innerHTML = 0
}

function createChart() {
    var chart = new CanvasJS.Chart("chartContainer", {
        title :{
            text: "Dynamic Data"
        },
        legend: {
            cursor: "pointer",
            itemclick: toggleDataSeries
        },
        toolTip: {
            shared: true
        },
        axisY:[{
            title: "Reward",
            lineColor: "green",
            tickColor: "green",
            labelFontColor: "green",
            titleFontColor: "green",
            includeZero: true,
        },
        {
            title: "MSE Episode Loss",
            lineColor: "red",
            tickColor: "red",
            labelFontColor: "red",
            titleFontColor: "red",
            includeZero: true,
        },
        {
            title: "Epsilon",
            lineColor: "blue",
            tickColor: "blue",
            labelFontColor: "blue",
            titleFontColor: "blue",
            includeZero: true,
        }],
        data: [{
            type: "line",
            name: "MSE Episode Loss",
            dataPoints: dpsLoss,
            showInLegend: true,
            axisYIndex: 1,
            color: "red",
        }, {
            type: "line",
            name: "Reward",
            dataPoints: dpsReward,
            showInLegend: true,
            axisYIndex: 0,
            color: "green",
        }, {
            type: "line",
            name: "Epsilon",
            dataPoints: dpsEpsilon,
            showInLegend: true,
            axisYIndex: 2,
            color: "blue",
        }],
        exportEnabled: true,
        width: 600,
        height:250,
    });
    return chart;
}

function displayUpdate(cb) {
    if(cb.checked) {
        isDisplaying = true;
        displayRecursion();
    } else {
        isDisplaying = false;
    }
}

function updateLoadModDisabled(bool) {
    loadModBtn.disabled = bool;
    uploadModIn.disabled = bool;
    uploadModBtn.disabled = bool;
}

function displayRecursion() {
    if (isDisplaying) {
        $.get($SCRIPT_ROOT + '/tempImage', function() {
            htmlImg.src = tempImgUrl;
            displayRecursion()
        })
    }
}

window.onload = function () {
    chart = createChart();
    chart.render();
}