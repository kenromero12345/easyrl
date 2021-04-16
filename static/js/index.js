function modelSelected() {
    var environments = document.getElementsByName('optionsEnv');
    var agents = document.getElementsByName('options');
    var agent;
    var environment;

    for(i = 0; i < agents.length; i++) {
        if(agents[i].checked) {
            agent = agents[i].id;
        }
    }

    for(i = 0; i < environments.length; i++) {
        if(environments[i].checked) {
            environment = environments[i].id;
        }
    }

    if (agent && environment) {
        location.replace("/model/" + environment + "/" + agent);
    } else {
        window.alert("You are missing an agent and/or an environment!");
    }


}

function file_exists(url){
    var http = new XMLHttpRequest();

    http.open('HEAD', url, false);
    http.send();

    return http.status != 404;
}

window.onload = function () {
    imgs = document.getElementsByClassName("indexImg");
    for (var i = 0; i < imgs.length; i++) {
        if (!file_exists(imgs[i].src)) {
            console.log(imgs[i].src)
            imgs[i].src = "/static/img/noImg.png";
        }
    }
}

function envUpdate(inp, allowedEnvs, allowedAgents) {
    curAgents = allowedAgents[inp.id]
    if (curAgents.length != 0){
        agentsDiv = document.querySelectorAll(".agentBtn")
        for (var i=0; i<agentsDiv.length; i++) {
            agentsIn = agentsDiv[i].firstElementChild;
            if (curAgents.includes(agentsIn.id) || !agentsIn.id in allowedEnvs) {
                agentsIn.disabled = false;
            } else {
                agentsIn.disabled = true;
            }
        }
    }
}

function agUpdate(inp, allowedEnvs, allowedAgents) {
    curEnvs = allowedEnvs[inp.id]
    if (curEnvs.length != 0){
        envsDiv = document.querySelectorAll(".environmentCustImg")
        for (var i=0; i<envsDiv.length; i++) {
            envsIn = envsDiv[i].firstElementChild;
            if (curEnvs.includes(envsIn.id) || !envsIn.id in allowedAgents) {
                envsIn.disabled = false;
            } else {
                envsIn.disabled = true;
            }
        }
    }
}


