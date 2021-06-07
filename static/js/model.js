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
    if (!isRunning || isLogin) {
        //get parameters
        var lists = document.querySelectorAll(".hyperparameter input[type=range]"); // get parameter components

        if (!isLogin) {
            epSlider.max = lists[0].value;
            epSlider.min = 1
            epSlider.value = 1;
        }

        // send to start test
        $.getJSON($SCRIPT_ROOT + '/startTest', getParamsVal(lists), function(data) {
            if(!isLogin) {
                if (data.model) {
                    trainBtn.disabled = true; // disable train
                    updateLoadModDisabled(true); // disable loading model feature
                    isRunning = true;
                    chartReset();
                    testRecursion(); // start testing
                } else {
                    window.alert("Model has not been trained!");
                }
            } else {
                if (data["task"] == "testJob" &&
                        (data["message"] == "Job started" || data["message"] == "Job already running")) {
                    trainBtn.disabled = true; // disable train
                    updateLoadModDisabled(true); // disable loading model feature
                    isRunning = true;
                }
            }
        });
    }
}

//get paramater values
function getParamsVal(lists) {
    var params = {}
    for (var i = 0; i < lists.length; i++) {
        params[i] = lists[i].value;
    }
//    console.log(params)
    return params
}


//training the model
function train() {
    if (!isRunning || isLogin) {
        if (!isLogin) {
            testBtn.disabled = true; // disable testing
            updateLoadModDisabled(true); // disable load model feature
            isRunning = true;
        }
        chartReset()

        var lists = document.querySelectorAll(".hyperparameter input[type=range]"); // get parameter components
        if (!isLogin) {
            epSlider.max = lists[0].value;
            epSlider.min = 1
            epSlider.value = 1;
        }

        //send to start train
        $.getJSON($SCRIPT_ROOT + '/startTrain', getParamsVal(lists), function(data) {
//            console.log(data)
            if (!isLogin) {
                trainRecursion()
            } else {
                if (data["task"] == "runJob" &&
                        (data["message"] == "Job started" || data["message"] == "Job already running")) {
                    testBtn.disabled = true; // disable testing
                    updateLoadModDisabled(true); // disable load model feature
                    isRunning = true;
                }
            }
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
            // testing code
            chartRewardAdd(xVal, data.reward); //add reward to chart
            xVal++; // episode number +1
            chart.render();
            testRecursion();
            totalTrainingRewardVal += data.reward;
            totalTrainingReward.innerHTML = totalTrainingRewardVal.toFixed(2);
            rewardPerEpisode.innerHTML = (totalTrainingRewardVal/xVal).toFixed(2);
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
            //training code
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
    for(var i = 0; i < dpsReward.length; i++) {
        if (dpsLoss[i]) {
            results += (i+1) + ", " + dpsLoss[i].y + ", " + dpsReward[i].y + ", " + dpsEpsilon[i].y + "\n";
        } else {
            results += (i+1) + " ,_ , " + dpsReward[i].y + " ,_\n";
        }
    }
    if (results == "") { // if results is empty
        window.alert("No results to be saved");
    } else {
        download(results, input.value, "txt") // download to user's system
    }

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
        if (data.agent == "null") { // model is null
            window.alert("No model to be saved");
        } else {
            download(data.agent, input.value, "txt")// download to user's system
        }

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
        $.post($SCRIPT_ROOT + '/loadModel', { //send to load model
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
    $.getJSON($SCRIPT_ROOT + '/reset', function() {
        isRunning = false;
        chartReset();
        isDisplaying = true // helps to reset image
        displayRecursion(); // reset image
        trainBtn.disabled = false; // enable train
        updateLoadModDisabled(false); // enable loading model feature
        testBtn.disabled = false // enable test
        isReset = true;
        epSlider.value = 1
    }); // send to reset model
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
function displayUpdate(b) {
//    cbLbl = cb.nextElementSibling;
    if(b.classList.contains('bi-play')) {
        b.classList.remove('bi-play');
        b.classList.add('bi-pause');
        b.classList.remove('btn-success');
        b.classList.add('btn-warning');
        isDisplaying = true;
        displayRecursion();
        epSlider.disabled = false;
//        cbLbl.innerHTML = "Stop"
    } else {
        b.classList.add('bi-play');
        b.classList.remove('bi-pause');
        b.classList.add('btn-success');
        b.classList.remove('btn-warning');
        isDisplaying = false;
        epSlider.disabled = true;
//        cbLbl.innerHTML = "Start"
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
                epSlider.title = data.episode;
                epSlider.data = data.episode;
//                $('#epSlider').attr('data-bs-original-title', data.episode).tooltip('show');
                displayEnvStep.innerHTML = data.step;
//                console.log($("#epSlider:hover").length)
//                if ($("#epSlider:hover").length != 0) {
//                    epSlider.value = data.episode;
//                }
                epSlider.value = data.episode;
                if (data.finished) {
                    envSwitch.classList.add('bi-play');
                    envSwitch.classList.remove('bi-pause');
                    envSwitch.classList.add('btn-success');
                    envSwitch.classList.remove('btn-warning');
                    isDisplaying = false;
                    epSlider.disabled = true;
                }
                if (isReset) {
                    htmlImg.src = noImgUrl;
                    isReset = false;
                    isDisplaying = false;
                    displayEnvStep.innerHTML = 0;
                    displayEnvEp.innerHTML = 0;
                    epSlider.title = 0;
                    epSlider.data = 0;
                } else {
                    displayRecursion()
                }
            })
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
        htmlImg.style.height = "255px";
    }
}

//update the episode slider
function updateEpisodeSlider(sl) {
    $.get($SCRIPT_ROOT + '/changeDisplayEpisode',
    {
        episode: sl.value
    })
}


function doPoll() {
    try {
        var lists = document.querySelectorAll(".hyperparameter input[type=range]"); // get parameter components
        $.getJSON('/poll', getParamsVal(lists), function (result) {
        // process results here
//            console.log(result)
            try {
                updateAWSPage2(result)
                setTimeout(doPoll, 1000);
            } catch (e) {
//                console.log("error2")
//                console.log(e)
                setTimeout(doPoll, 1000);
            }
        });
    } catch (e) {
//        console.log("error1")
//        console.log(e)
        setTimeout(doPoll, 5000);
    }
}

function updateAWSPage2(result) {
    if (result == "") {
        alert("The response is empty");
    } else {
//        var state = result["instanceState"]
//        var stateText = result["instanceStateText"]

        var stateText = result["instanceStateText"]

        if (stateText == "Idle") {
            loaderWrapper.style.display = "none";
            //TODO: enable all buttons
        } else if (stateText == "Booting") {
            loaderWrapper.style.display = "flex";
        }
        if (result["progress"] != undefined && result["progress"] != "waiting") {
            var episodes = result["progress"]["episodes"]
//            console.log(state)
//            console.log(stateText)
//            console.log(episodes)
            //chart update
            chartReset()
            for (var index = 0; index < episodes.length; index++) {
//                console.log(episodes[index])
//                console.log(typeof episodes[index])
                chartLossAdd(index+1, episodes[index]["l"]);
                chartRewardAdd(index+1, episodes[index]["r"]);
                chartEpsilonAdd(index+1, episodes[index]["p"]);
                xVal = episodes[index]["e"]
            }
            chart.render()
            totalTrainingReward.innerHTML = result["progress"]['totalReward'];
            rewardPerEpisode.innerHTML = result["progress"]['avgReward'];

            var gifs = result["progress"]["gifs"];
            if (gifs.length > 0) {
//                $("#training_image").attr("src", gifs[gifs.length - 1]);
                displayEnvEp.innerHTML = gifs[gifs.length - 1].split("-episode-")[1].split(".")[0]
                htmlImg.src = gifs[gifs.length - 1]
            }

            if (result["progress"]["episodesCompleted"] == result["arguments"]["episodes"]-1) {
                isRunning = false
                testBtn.disabled = false;
                updateLoadModDisabled(false)
                trainBtn.disabled= false
            }
        }

    }
}