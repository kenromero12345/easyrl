window.onload = function () {
//    update image for custom environments and agents
    imgs = document.getElementsByClassName("indexImg"); // get all custom environment and agents
    for (var i = 0; i < imgs.length; i++) {
        if (!file_exists(imgs[i].src)) { // check if image exists
            imgs[i].src = "/static/img/noImg.png"; // change image
        }
    }
}

// selecting the model
function modelSelected() {
    var environments = document.getElementsByName('optionsEnv'); // get environments
    var agents = document.getElementsByName('options'); // get agents
    var instances = document.getElementsByName('optionsInst'); // get instances
    var agent;
    var environment;
    var instance;
    //get chosen agent
    for(i = 0; i < agents.length; i++) {
        if(agents[i].checked) {
            agent = agents[i].id;
        }
    }

    //get chosen environment
    for(i = 0; i < environments.length; i++) {
        if(environments[i].checked) {
            environment = environments[i].id;
        }
    }

    //get chosen instance
    for(i = 0; i < instances.length; i++) {
        if(instances[i].checked) {
            instance = instances[i].id;
        }
    }

    if (isLogin) {
        if (agent && environment && instance) { // if agent and environment exists
//            loader.style.display = "inline-block";
//            console.log(loader)
//            setTimeout(doPoll, 1000);
            location.replace("/model/" + environment + "/" + agent + "/" + instance.split(' ')[0]); // change location to the new model
        } else {
            window.alert("You are missing an agent and/or an environment and/or an instance!"); // error
        }
    } else {
        if (agent && environment) { // if agent and environment exists
            location.replace("/model/" + environment + "/" + agent); // change location to the new model
        } else {
            window.alert("You are missing an agent and/or an environment!"); // error
        }
    }
}

//checks if url exist
function file_exists(url){
    var http = new XMLHttpRequest();

    http.open('HEAD', url, false);
    http.send();

    return http.status != 404; // no url exist
}

//chosen environement update
function envUpdate(inp, allowedEnvs, allowedAgents) {
    curAgents = allowedAgents[inp.id] // get agents allowed to pair
    if (curAgents.length != 0){ // if there are allowed agents
        agentsDiv = document.querySelectorAll(".agentBtn") // get all agents
        for (var i=0; i<agentsDiv.length; i++) { // iterate through all agents
            agentsIn = agentsDiv[i].firstElementChild; // get the input element of the agent
            if (curAgents.includes(agentsIn.id) || !agentsIn.id in allowedEnvs) { // if agent is not allowed
                agentsIn.disabled = false; // disable the agent
            } else {
                agentsIn.disabled = true; // enable the agent
            }
        }
    }
}

// chosen agent update
function agUpdate(inp, allowedEnvs, allowedAgents) {
    curEnvs = allowedEnvs[inp.id] // get environment allowed to pair
    if (curEnvs.length != 0){ // if there are allowed environments
        envsDiv = document.querySelectorAll(".environmentCustImg") //get all environments
        for (var i=0; i<envsDiv.length; i++) { // iterate through all environments
            envsIn = envsDiv[i].firstElementChild; // get the input element of the environment
            if (curEnvs.includes(envsIn.id) || !envsIn.id in allowedAgents) { // if environment is not allowed
                envsIn.disabled = false; // disable the environment
            } else {
                envsIn.disabled = true; // enable the environment
            }
        }
    }
}

// loading either a custom environment or agent
function loading(btn, route) {
    input = btn.previousElementSibling // input element

    // loading elements hide
    input.style.display = "none";
    btn.style.display = "none";

    window.alert("Upload Success"); // popup message

    var fr = new FileReader();
    var temp; // temporary space for input file text
    fr.onload=function(){ // when loading file text
        temp = fr.result; // get data string
        $.getJSON($SCRIPT_ROOT + route, { // communicate with flask
            file: temp //send data
        }, function(data) { // on success
            window.location.reload() // refresh page
        });
    }
    fr.readAsText(input.files[0]); // load input file text
}

// loading custom environment
function loadCustEnv(btn) {
    loading(btn, '/custEnv')
}

// loading custom agent
function loadCustAg(btn) {
    loading(btn, '/custAg')
}

//function doPoll (){
//    try {
//        $.getJSON('/poll', function (result) {
//            try {
//                var state = result["instanceState"]
//                var stateText = result["instanceStateText"]
//                if (stateText == "Idle") {
//                    location.replace("/model/" + environment + "/" + agent + "/" + instance.split(' ')[0]); // change location to the new model
//                }
//                setTimeout(doPoll, 1000);
//            } catch (e) {
//                setTimeout(doPoll, 1000);
//            }
//        });
//    } catch (e) {
//        setTimeout(doPoll, 5000);
//    }
//}

function awsAgUpdate (inp, envMap, agMap, env, ag) {
//    curEnvs = allowedEnvs[inp.id] // get environment allowed to pair
//    if (curEnvs.length != 0){ // if there are allowed environments
//        envsDiv = document.querySelectorAll(".environmentCustImg") //get all environments
//        for (var i=0; i<envsDiv.length; i++) { // iterate through all environments
//            envsIn = envsDiv[i].firstElementChild; // get the input element of the environment
//            if (curEnvs.includes(envsIn.id) || !envsIn.id in allowedAgents) { // if environment is not allowed
//                envsIn.disabled = false; // disable the environment
//            } else {
//                envsIn.disabled = true; // enable the environment
//            }
//        }
//    }
    var envsDiv = document.querySelectorAll(".environmentCustImg") //get all environments
    var supportedEnvs = null
    for (var i = 1; i <= ag.length; i++) {
//        console.log(envMap[i.toString()]["name"] + " " + inp.id)
        if (agMap[i.toString()]["name"] == inp.id) {
            supportedEnvs = agMap[i]["supportedEnvs"];
            break;
        }
    }
//    console.log(supportedEnvs)
    for (var j = 1; j <= env.length; j++) {
        var envsIn = envsDiv[j-1].firstElementChild; // get the input element of the agent
//        console.log(envIn.id)
//
//        console.log(envMap[j.toString()]["supportedEnvs"])
        if (supportedEnvs.includes(envMap[j.toString()]["type"])) {
            envsIn.disabled = false; // disable the agent
        } else {
            envsIn.disabled = true;
        }
    }
}

function awsEnvUpdate (inp, envMap, agMap, env, ag) {
//    console.log(envMap)
//    console.log(agMap)
    var agentsDiv = document.querySelectorAll(".agentBtn");
    var type = null;
    for (var i = 1; i <= env.length; i++) {
        if (envMap[i.toString()]["name"] == inp.id) {
            type = envMap[i]["type"];
            break;
        }
    }
//    console.log(type)
    for (var j = 1; j <= ag.length; j++) {
        var agentsIn = agentsDiv[j-1].firstElementChild; // get the input element of the agent
//        console.log(agentsIn.id)
//
//        console.log(agMap[j.toString()]["supportedEnvs"])
        if (agMap[j.toString()]["supportedEnvs"].includes(type)) {
            agentsIn.disabled = false; // disable the agent
        } else {
            agentsIn.disabled = true;
        }
    }
}