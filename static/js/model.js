//slider change updates text input
function updateSlider(slider) {
    var txtIn = slider.parentElement.querySelector(".customInput"); //get input
    txtIn.value = slider.value;
}

//text input change updates slider
function updateInput(input) {
    var slider = input.parentElement.querySelector("input[type=range]"); //get slider

    //validation
    if (input.value > slider.max) { // if text input is above the max
        slider.value = slider.max;
        input.value = slider.max;
    } else if (input.value < slider.min) { // if text input is below the min
        slider.value = slider.min;
        input.value = slider.min;
    } else {
        slider.value = input.value;
    }
}

// save components visible
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
    Copied from stackoverflow to help download files
    https://stackoverflow.com/questions/3665115/how-to-create-a-file-in-memory-for-user-to-download-but-not-through-server
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

// testing model
function test() {
    if (!isRunning) {
        //get parameters
        var lists = document.querySelectorAll("input[type=range]"); // get parameter components
        var params = {}
        for (var i = 0; i < lists.length; i++) {
            params[i] = lists[i].value;
        }

        // send to start test
        $.getJSON($SCRIPT_ROOT + '/startTest', params, function(data) {
            if (data.model) {
                trainBtn.disabled = true; // disable train
                updateLoadModDisabled(true); // disable loading model feature
                isRunning = true;
                chartReset();
                testRecursion(); // start testing
            } else {
                window.alert("Model has not been trained!");
            }
        });
    }
}


//training the model
function train() {
    if (!isRunning) {
        testBtn.disabled = true; // disable testing
        updateLoadModDisabled(true); // disable load model feature
        isRunning = true;
        chartReset()

        //get parameters
        var lists = document.querySelectorAll(".hyperparameter input[type=range]"); // get parameter components
        var params = {}
        for (var i = 0; i < lists.length; i++) {
            params[i] = lists[i].value;
        }

        epSlider.max = lists[0].value;
        epSlider.min = 1

        //send to start train
        $.getJSON($SCRIPT_ROOT + '/startTrain', params, function(data) {
            trainRecursion()
        });
    }
}

//running testing per episode
function testRecursion() {
    //send to test an episode
    $.getJSON($SCRIPT_ROOT + '/runTest', function(data) {
        if (data.finished) { //testing is complete
            isRunning = false;
            trainBtn.disabled = false;
            updateLoadModDisabled(false);
        } else {
            if (isReset) { //reset is clicked while testing
                isRunning = false;
                isReset = false;
                chartReset();
                trainBtn.disabled = false;
                updateLoadModDisabled(false);
                epSlider.max = 0;
                epSlider.min = 0
            } else { // testing code
                chartRewardAdd(xVal, data.reward); //add reward to chart
                xVal++; // episode number +1
                chart.render();
                testRecursion();
                totalTrainingRewardVal += data.reward;
                totalTrainingReward.innerHTML = totalTrainingRewardVal.toFixed(2);
                rewardPerEpisode.innerHTML = (totalTrainingRewardVal/xVal).toFixed(2);
            }
        }
    });
}

//running training per episode
function trainRecursion() {
    $.getJSON($SCRIPT_ROOT + '/runTrain', function(data) {
        if (data.finished) { //training is complete
            isRunning = false;
            testBtn.disabled = false;
            updateLoadModDisabled(false);
        } else {
            if (isReset) { //reset is clicked while training
                isRunning = false;
                isReset = false;
                chartReset();
                testBtn.disabled = false;
                updateLoadModDisabled(false);
                epSlider.max = 0;
                epSlider.min = 0
            } else { //training code
                //add data to chart
                chartLossAdd(xVal, data.loss);
                chartRewardAdd(xVal, data.reward);
                chartEpsilonAdd(xVal, data.epsilon);

                xVal++;// episode number +1
                chart.render();
                trainRecursion();
                totalTrainingRewardVal += data.reward;
                totalTrainingReward.innerHTML = totalTrainingRewardVal.toFixed(2);
                rewardPerEpisode.innerHTML = (totalTrainingRewardVal/xVal).toFixed(2);
            }
        }
    });
}

//add loss to chart
function chartLossAdd(index, loss) {
    dpsLoss.push({
        x: index,
        y: loss
    });
}

//add reward to chart
function chartRewardAdd(index, reward) {
    dpsReward.push({
        x: index,
        y: reward
    });
}

//add epsilon to chart
function chartEpsilonAdd(index, epsilon) {
    dpsEpsilon.push({
        x: index,
        y: epsilon
    });
}

//save results of the chart data
function saveResults(btn) {
    input = btn.previousElementSibling;
    var results = "";
    for(var i = 0; i < dpsLoss.length; i++) {
        results += (i+1) + ", " + dpsLoss[i].y + ", " + dpsReward[i].y + ", " + dpsEpsilon[i].y + "\n";
    }

    download(results, input.value, "txt") // download to user's system

    // hide components
    input.style.display = "none";
    btn.style.display = "none";

    input.value = ""; // input text clear
}

// saving model
function saveModel(btn) {
    input = btn.previousElementSibling;

    //send to save the current model
    $.getJSON($SCRIPT_ROOT + '/saveModel', function(data) {
        download(data.agent, input.value, "txt")// download to user's system

        //hide components
        input.style.display = "none";
        btn.style.display = "none";

        input.value = ""; // input text clear
    });
}

//loading model
function loadModel(btn) {
    input = btn.previousElementSibling

    //loading file
    var fr = new FileReader();
    var temp;
    fr.onload=function(){
        temp = fr.result;
        $.getJSON($SCRIPT_ROOT + '/loadModel', { //send to load model
            agent: temp
        }, function(data) {
            if (data.success) { // data is loaded successfully
                window.alert("Model Uploaded");

                //load model components hidden
                input.style.display = "none";
                btn.style.display = "none";
                input.value = "";
            } else {
                window.alert("Incorrect Model! Loading Unsuccessful");
            }

        });
    }
    fr.readAsText(input.files[0]); //read file
}

//toggle the data in the graph
function toggleDataSeries(e) {
    if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
        e.dataSeries.visible = false;
    } else {
        e.dataSeries.visible = true;
    }
    e.chart.render();
}

//reset the graph, display, and the model
function reset() {
    if (isRunning) {
        isRunning = false;
        isReset = true; // reset flag is up
    } else {
        chartReset();
        isDisplaying = true // helps to reset image
        displayRecursion(); // reset image
    }
    $.getJSON($SCRIPT_ROOT + '/reset'); // send to reset model
}

//halt training or testing
function halt() {
    isRunning = false;
    $.getJSON($SCRIPT_ROOT + '/halt')
}

//reset the graph
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

//initialize the chart
function createChart() {
    var chart = new CanvasJS.Chart("chartContainer", {
//        title :{
//            text: "Dynamic Data"
//        },
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
        width: 800,
        height:250,
    });
    return chart;
}

//display change if an image exist
function displayUpdate(cb) {
    if(cb.checked) {
        isDisplaying = true;
        displayRecursion();
        epSlider.disabled = false
    } else {
        isDisplaying = false;
        epSlider.disabled = true
    }
}

//disable load model components
function updateLoadModDisabled(bool) {
    loadModBtn.disabled = bool;
    uploadModIn.disabled = bool;
    uploadModBtn.disabled = bool;
}

//display change helper recursion
function displayRecursion() {
    if (isDisplaying) {
        $.get($SCRIPT_ROOT + '/tempImage', function() {
            htmlImg.src = tempImgUrl;
            $.get($SCRIPT_ROOT + '/tempImageEpStep', function(data) {
                displayEnvEp.innerHTML = data.episode;
                displayEnvStep.innerHTML = data.step;
                epSlider.value = data.episode;
                if (data.finished) {
                    envSwitch.checked = false;
                    isDisplaying = false;
                    epSlider.disabled = true;
                }
            })
            displayRecursion()
        })
    }
}

//load the chart
window.onload = function () {
    chart = createChart();
    chart.render();
}

//toggles the display's ratio aspect to on or off
function ratioUpdate(cb) {
    if(cb.checked) {
        htmlImg.style.height = "auto";
    } else {
        htmlImg.style.height = "235px";
    }
}

//update the episode slider
function updateEpisodeSlider(sl) {
    $.get($SCRIPT_ROOT + '/changeDisplayEpisode',
    {
        episode: sl.value
    })
}