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
            location.replace("/model/" + environment + "/" + agent + "/" + instance); // change location to the new model
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