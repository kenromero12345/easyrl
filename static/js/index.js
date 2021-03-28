function modelSelected() {
    var agents = document.getElementsByName('optionsEnv');
    var environments = document.getElementsByName('options');
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
        window.alert("the chosen agent and environment do not meet the requirement");
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