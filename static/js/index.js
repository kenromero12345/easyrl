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

//window.onload = function () {
//    var labelContainer = document.getElementsByClassName("environmentLblContainer")
//    var input = document.getElementsByClassName("environmentInput")
//    if (input.checked) {
//        labelContainer
//    } else {
//
//    }
////    input.onchange = function () {
////        labelContainer.style.visibility = this.checked ? 'visible' : 'hidden';
////    };
//}

//var input = document.getElementsByClassName("environmentInput")
//
//input.onchange = function(radio) {
//
//}

//function updateEnvironmentInputStyle(input) {
//    var container = input.parentElement.parentElement.querySelector(".environmentLblContainer");
//
//    if (input.checked) {
//        container.style.outline = "2px solid red";
//    } else {
//        container.style.outline = "";
//    }
//}


//function load(btn) {
//    /*TODO: what do you do to the uploaded file*/
//    input = btn.previousElementSibling;
//    input.style.display = "none";
//    btn.style.display = "none";
//}

function file_exists(url){
    var http = new XMLHttpRequest();

    http.open('HEAD', url, false);
    http.send();

    return http.status != 404;
}

window.onload = function () {
//    environmentsIn = document.querySelectorAll("input[type=radio]:checked");
//    console.log(environmentsIn.length)
//    for (var i = 0; i < environmentsIn.length; i++) {
//        environmentsIn.parentElement.style.outline = "5px solid grey;"
//    }

    imgs = document.getElementsByClassName("indexImg");
    for (var i = 0; i < imgs.length; i++) {
        if (!file_exists(imgs[i].src)) {
            console.log(imgs[i].src)
            imgs[i].src = "/static/img/noImg.png";
        }
    }
}

//function environmentUpdate(inp) {
//    console.log(inp.checked)
//    if (inp.checked) {
//        inp.parentElement.style.outline = "5px solid grey;"
//    } else {
//        inp.parentElement.style.outline = "1px solid grey"
//    }
//}

function envUpdate(inp, allowedEnvs, allowedAgents) {
    curAgents = allowedAgents[inp.id]
//    console.log(curAgents)
    if (curAgents.length != 0){
        agentsDiv = document.querySelectorAll(".agentBtn")
        for (var i=0; i<agentsDiv.length; i++) {
            agentsIn = agentsDiv[i].firstElementChild;
//            console.log(agentsIn.id)
//            console.log(curAgents.includes("Deep Q"))
//            console.log(curAgents.includes(agentsIn.id))
//            console.log(!agentsIn in allowedEnvs)
            if (curAgents.includes(agentsIn.id) || !agentsIn.id in allowedEnvs) {
//                console.log("no")
                agentsIn.disabled = false;
            } else {
//                console.log("yay")
                agentsIn.disabled = true;
            }
        }
    }
    //TODO: Missing else
}

function agUpdate(inp, allowedEnvs, allowedAgents) {
    curEnvs = allowedEnvs[inp.id]
//    console.log(curAgents)
    if (curEnvs.length != 0){
        envsDiv = document.querySelectorAll(".environmentCustImg")
        for (var i=0; i<envsDiv.length; i++) {
            envsIn = envsDiv[i].firstElementChild;
//            console.log(agentsIn.id)
//            console.log(curAgents.includes("Deep Q"))
//            console.log(curAgents.includes(agentsIn.id))
//            console.log(!agentsIn in allowedEnvs)
            if (curEnvs.includes(envsIn.id) || !envsIn.id in allowedAgents) {
//                console.log("no")
                envsIn.disabled = false;
            } else {
//                console.log("yay")
                envsIn.disabled = true;
            }
        }
    }
    //TODO: Missing else
}