import io
import json
import os
from types import ModuleType
import PIL
import boto3
import botocore
from PIL.Image import Image
from flask import Flask, render_template, g, request, jsonify, send_file
import time
from Agents import qLearning, drqn, deepQ, adrqn, agent as ag, doubleDuelingQNative, drqnNative, drqnConvNative, \
    ppoNative, \
    reinforceNative, actorCriticNative, cem, npg, ddpg, sac, trpo, rainbow
from Environments import cartPoleEnv, cartPoleEnvDiscrete, atariEnv, frozenLakeEnv, pendulumEnv, acrobotEnv, \
    mountainCarEnv
from Agents.sarsa import sarsa
from MVC import model
import threading
import queue
from MVC.model import Model
import sys
import jsonpickle
from utilities import get_aws_lambda, \
    invoke_aws_lambda_func, is_valid_aws_credential, generate_jobID
import apps
import logging

##no flask msg when running
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # do not use cache in this application


# Starting application
# Sending environment and agent names and allowed environments and agents to be blocked
# displaying index page
@app.route('/')
@app.route('/index')
def indexPage():
    if isLogin:

        info = lambda_info(accessKey,
                           secretKey,
                           securityToken,
                           jobID, {})
        info = json.loads(info)
        # temp = [i.get('name') for i in info.get('environments')]
        for i in range(len(info.get('environments'))):
            name = info.get('environments')[i].get('name')
            name = name.lower().replace(" ", "_")
            info.get('environments')[i].update({"file": name})
        return render_template('index.html', envName=info.get('environments'), agtName=info.get('agents'),
                               allowedEnvs=None, allowedAgents=None, isLogin=isLogin, instances=instances)
    else:
        return render_template('index.html', envName=envName, agtName=agtName, allowedEnvs=allowedEnvs,
                               allowedAgents=allowedAgents, isLogin=isLogin, instances=instances)


def lambda_info(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_INFO,
        "arguments": arguments,
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    print("{}lambda_info_job{}={}".format(apps.FORMAT_GREEN, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# login page of the application
@app.route('/login')
def loginPage():
    return render_template('login.html')


# logging in the AWS account
@app.route('/loggingIn')
def loggingIn():
    global isLogin, accessKey, secretKey, securityToken
    accessKey = request.args.get('accessKey')
    secretKey = request.args.get('secretKey')
    securityToken = request.args.get('securityToken')
    is_valid_aws_credential(accessKey, secretKey, securityToken)
    isLogin = is_valid_aws_credential(accessKey, secretKey, securityToken)
    if isLogin:
        return jsonify(success=True)
    else:
        return jsonify(success=False)


# logging out the AWS account
@app.route('/logout')
def logout():
    global isLogin
    isLogin = False

    # TODO: replace request.post.get
    lambda_terminate_instance(
        accessKey,
        secretKey,
        securityToken,
        jobID,
        {
            "instanceType": get_safe_value(str, request.POST.get("instanceType"), "c4.xlarge")
            , "instanceID": get_safe_value(str, request.POST.get("instanceID"), "")
            , "killTime": get_safe_value(int, request.POST.get("killTime"), 600)
            , "environment": get_safe_value(int, request.POST.get("environment"), 1)
            , "continuousTraining": get_safe_value(str, request.POST.get("continuousTraining"), "False")
            , "agent": get_safe_value(int, request.POST.get("agent"), 1)
            , "episodes": get_safe_value(int, request.POST.get("episodes"), 20)
            , "steps": get_safe_value(int, request.POST.get("steps"), 50)
            , "gamma": get_safe_value(float, request.POST.get("gamma"), 0.97)
            , "minEpsilon": get_safe_value(float, request.POST.get("minEpsilon"), 0.01)
            , "maxEpsilon": get_safe_value(float, request.POST.get("maxEpsilon"), 0.99)
            , "decayRate": get_safe_value(float, request.POST.get("decayRate"), 0.01)
            , "batchSize": get_safe_value(int, request.POST.get("batchSize"), 32)
            , "memorySize": get_safe_value(int, request.POST.get("memorySize"), 1000)
            , "targetInterval": get_safe_value(int, request.POST.get("targetInterval"), 10)
            , "alpha": get_safe_value(float, request.POST.get("alpha"), 0.9)
            , "historyLength": get_safe_value(int, request.POST.get("historyLength"), 10)

            , "delta": get_safe_value(int, request.POST.get("delta"), 0.001)
            , "sigma": get_safe_value(int, request.POST.get("sigma"), 0.5)
            , "population": get_safe_value(int, request.POST.get("population"), 10)
            , "elite": get_safe_value(int, request.POST.get("elite"), 0.2)

            , "tau": get_safe_value(int, request.POST.get("tau"), 0.97)
            , "temperature": get_safe_value(int, request.POST.get("temperature"), 0.97)

            , "learningRate": get_safe_value(int, request.POST.get("learningRate"), 0.001)
            , "policyLearnRate": get_safe_value(int, request.POST.get("policyLearnRate"), 0.001)
            , "valueLearnRate": get_safe_value(int, request.POST.get("valueLearnRate"), 0.001)
            , "horizon": get_safe_value(int, request.POST.get("horizon"), 50)
            , "epochSize": get_safe_value(int, request.POST.get("epochSize"), 500)
            , "ppoEpsilon": get_safe_value(int, request.POST.get("ppoEpsilon"), 0.2)
            , "ppoLambda": get_safe_value(int, request.POST.get("ppoLambda"), 0.95)
            , "valueLearnRatePlus": get_safe_value(int, request.POST.get("valueLearnRatePlus"), 0.001)
        }
    )

    return jsonify(success=True)


def lambda_terminate_instance(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_TERMINAL_INSTANCE,
        "arguments": arguments,
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    print("{}lambda_terminate_instance{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, response['Payload'].read()))
    if response['StatusCode'] == 200:
        streambody = response['Payload'].read().decode()
        print("{}stream_body{}={}".format(apps.FORMAT_BLUE, apps.FORMAT_RESET, streambody))
        return True
    return False


def get_safe_value(convert_function, input_value, default_value):
    try:
        return convert_function(input_value)
    except ValueError as _:
        return default_value
    except Exception as _:
        return default_value


# When clicking the loading custom environment button
@app.route('/custEnv')
def custEnv():
    file = request.args.get('file')  # get file argument

    # executing custom environment
    module = ModuleType('customEnv')
    sys.modules['customEnv'] = module
    exec(file, module.__dict__)

    # adding custom environment
    global environments, envName
    environments = [module.CustomEnv] + environments
    envName = [module.CustomEnv.displayName] + envName
    return jsonify(finished=True)


# When clicking the loading custom agent button
@app.route('/custAg')
def custAg():
    file = request.args.get('file')  # get file argument

    # executing custom agent
    module = ModuleType('customAg')
    sys.modules['customAg'] = module
    exec(file, module.__dict__)

    # adding custom agent
    global agents, agtName
    agents = [module.CustomAgent] + environments
    agtName = [module.CustomAgent.displayName] + agtName
    return jsonify(finished=True)


# displaying model page
# sending parameters info
@app.route('/model/<environment>/<agent>')
def modelPage(environment, agent):
    # set agent class
    for curAgent in agents:
        if agent == curAgent.displayName:
            mod.agent_class = curAgent
            break

    # set environment class
    for curEnv in environments:
        if environment == curEnv.displayName:
            mod.environment_class = curEnv
            break

    mod.reset()  # reset model

    # set parameters to be sent
    params = [ag.Agent.Parameter('Number of Episodes', 1, 655360, 1, 1000, True, True,
                                 "The number of episodes to run the model on"),
              ag.Agent.Parameter('Max Size', 1, 655360, 1, 200, True, True,
                                 "The max number of timesteps permitted in an episode")]
    for param in mod.agent_class.parameters:
        params.append(param)

    return render_template('model.html', params=params)


# displaying model page
# sending parameters info
@app.route('/model/<environment>/<agent>/<instance>')
def modelPageAWS(environment, agent, instance):
    # set agent class
    for curAgent in agents:
        if agent == curAgent.displayName:
            mod.agent_class = curAgent
            break

    # set environment class
    for curEnv in environments:
        if environment == curEnv.displayName:
            mod.environment_class = curEnv
            break

    # TODO: get instance
    for curIns in instances:
        if instance == 

    mod.reset()  # reset model

    # set parameters to be sent
    params = [ag.Agent.Parameter('Number of Episodes', 1, 655360, 1, 1000, True, True,
                                 "The number of episodes to run the model on"),
              ag.Agent.Parameter('Max Size', 1, 655360, 1, 200, True, True,
                                 "The max number of timesteps permitted in an episode")]
    for param in mod.agent_class.parameters:
        params.append(param)

    return render_template('model.html', params=params)


# saving model
@app.route('/saveModel')
def saveModel():
    # encode the model
    temp = jsonpickle.encode((mod.agent.displayName, mod.agent.memsave()))
    return jsonify(agent=temp)


# loading model
@app.route('/loadModel', methods=['POST'])
def loadModel():
    try:
        name, mem = jsonpickle.decode(request.form.get('agent'))  # decode model

        # validate the decoded model
        if mod.agent_class.displayName == name:
            mod.isLoaded = True
            mod.memload = mem
            return jsonify(success=True)
    except ValueError:
        return jsonify(success=False)
    return jsonify(success=False)


# starting training
@app.route('/startTrain')
def startTrain():
    if mod.isRunning:  # if model is running
        return jsonify(finished=False)
    else:
        # reset hyperparameters and image queue
        global inputParams, tempImages
        inputParams = []
        tempImages = []

        # set hyperparameters
        temp = request.args.get('0')
        i = 0
        while temp is not None:
            inputParams.append(float(temp))
            i += 1
            temp = request.args.get(str(i))

        # run training
        global curThread
        curThread = threading.Thread(target=mod.run_learning, args=[msg, ] + inputParams)
        global curDisplayIndex
        curDisplayIndex = 0
        curThread.start()
        return jsonify(finished=True)


# running training
@app.route('/runTrain')
def runTrain():
    temp = msg.get(block=True)  # receive message

    # train is finished
    if temp.data == Model.Message.TRAIN_FINISHED:
        return jsonify(finished=True)

    # test is still running
    episodeAccLoss = 0
    episodeAccEpsilon = 0
    episodeAccReward = 0
    global tempImages
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            if temp.data.loss:
                episodeAccLoss += temp.data.loss
            if temp.data.epsilon:
                episodeAccEpsilon += temp.data.epsilon
            if temp.data.reward:
                episodeAccReward += temp.data.reward
            if temp.data.image:
                tempImages.append((temp.data.image, temp.data.episode, temp.data.step))

        temp = msg.get(block=True)

    return jsonify(loss=episodeAccLoss / inputParams[1], reward=episodeAccReward,
                   epsilon=episodeAccEpsilon / inputParams[1],
                   finished=False)  # inputParams[1] is max size the hyperparameter


# display an image for this route
@app.route('/tempImage')
def tempImage():
    global noImg, curEp, curStep, curFin, curDisplayIndex
    if tempImages:
        temp = tempImages[curDisplayIndex]
        curEp = temp[1]
        curStep = temp[2]
        if curDisplayIndex == len(tempImages) - 1:
            if curThread.is_alive():
                curFin = False
            else:
                curFin = True
                curDisplayIndex = 0
        else:
            curFin = False
            curDisplayIndex += 1
        return serve_pil_image(temp[0])  # image for model
    else:
        curEp = 0
        curStep = 0
        curFin = True
        return serve_pil_image(noImg)  # image for no display


# display the episode and step number of the displayed environment
@app.route('/tempImageEpStep')
def tempImageEpStep():
    return jsonify(episode=curEp, step=curStep, finished=curFin)


# starting testing
@app.route('/startTest')
def startTest():
    if mod.isRunning:  # if model is running
        return jsonify(finished=False)
    else:
        if mod.agent or mod.isLoaded:
            # reset hyperparameters and image queue
            global inputParams, tempImages
            inputParams = []
            tempImages = []

            # set hyperparameters
            temp = request.args.get('0')
            i = 0
            while temp is not None:
                inputParams.append(float(temp))
                i += 1
                temp = request.args.get(str(i))

            # run testing
            global curThread
            curThread = threading.Thread(target=mod.run_testing, args=[msg, ] + inputParams)
            global curDisplayIndex
            curDisplayIndex = 0
            curThread.start()
            return jsonify(finished=True, model=True)
        else:
            return jsonify(finished=False, model=False)  # if agent doesn't exist


# running testing
@app.route('/runTest')
def runTest():
    temp = msg.get(block=True)  # receive message

    # test is finished
    if temp.data == Model.Message.TEST_FINISHED:
        return jsonify(finished=True)

    # test is still running
    episodeAccReward = 0
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            if temp.data.reward:
                episodeAccReward += temp.data.reward
            if temp.data.image:
                tempImages.append((temp.data.image, temp.data.episode, temp.data.step))
        temp = msg.get(block=True)

    return jsonify(reward=episodeAccReward, finished=False)


# display image as a route
# https://stackoverflow.com/questions/7877282/how-to-send-image-generated-by-pil-to-browser
def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


# stop training or testing
@app.route('/halt')
def halt():
    if mod.isRunning:
        mod.halt_learning()
    return jsonify(finished=True)


# change display episode
@app.route('/changeDisplayEpisode')
def changeDisplayEpisode():
    global curDisplayIndex
    ep = int(request.args.get('episode'))
    temp = tempImages[-1][1]
    if temp < ep:
        episode = binarySearchEpisode(tempImages, 0, len(tempImages), temp)
    else:
        episode = binarySearchEpisode(tempImages, 0, len(tempImages), ep)

    if episode == -1:
        print("error")
    else:
        curDisplayIndex = episode
    return jsonify(finished=True)


# binary search helper for specifically finding a step
def binarySearchSteps(arr, low, high, x, ep):
    # Check base case
    if high >= low:

        mid = (high + low) // 2
        # If element is present at the middle itself
        if arr[mid][2] == x:
            return mid;

        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif (ep == arr[mid][1] and arr[mid][2] > x) or (ep < arr[mid][1]):

            return binarySearchSteps(arr, low, mid - 1, x, ep)

        # Else the element can only be present in right subarray
        else:
            return binarySearchSteps(arr, mid + 1, high, x, ep)

    else:
        # Element is not present in the array
        return -1


# binary search helper for updating the episode
def binarySearchEpisode(arr, low, high, x):
    # Check base case
    if high >= low:

        mid = (high + low) // 2

        # If element is present at the middle itself
        if arr[mid][1] == x:
            return binarySearchSteps(arr, low, high, 1, arr[mid][1])

        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif arr[mid][1] > x:

            return binarySearchEpisode(arr, low, mid - 1, x)

        # Else the element can only be present in right subarray
        else:
            return binarySearchEpisode(arr, mid + 1, high, x)

    else:
        # Element is not present in the array
        return -1


# Reset model
@app.route('/reset')
def reset():
    # halting
    if mod.isRunning:
        mod.halt_learning()

    global tempImages, msg
    # reset images
    tempImages = []
    # reset messages
    msg = queue.Queue()
    # reset model
    mod.reset()
    global curDisplayIndex
    curDisplayIndex = 0
    return jsonify(finished=True)


# displaying about page
@app.route('/about')
def aboutPage():
    return render_template('about.html')


# displaying help page
@app.route('/help')
def helpPage():
    return render_template('help.html')


# Turnaround time metric
@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


# validate AWS credentials
def is_valid_aws_credential(aws_access_key_id, aws_secret_access_key, aws_session_token=None):
    try:
        boto3.client('sts',
                     aws_access_key_id=aws_access_key_id,
                     aws_secret_access_key=aws_secret_access_key,
                     aws_session_token=aws_session_token,
                     ).get_caller_identity()
        return True
    except botocore.exceptions.ClientError:
        return False


# running application
if __name__ == "__main__":
    # list of agents
    agents = [deepQ.DeepQ, deepQ.DeepQPrioritized, deepQ.DeepQHindsight, qLearning.QLearning, drqn.DRQN,
              drqn.DRQNPrioritized, drqn.DRQNHindsight, adrqn.ADRQN, adrqn.ADRQNPrioritized, adrqn.ADRQNHindsight,
              doubleDuelingQNative.DoubleDuelingQNative, drqnNative.DRQNNative, drqnConvNative.DRQNConvNative,
              ppoNative.PPONative, reinforceNative.ReinforceNative, actorCriticNative.ActorCriticNative, sarsa,
              cem.CEM, npg.NPG, ddpg.DDPG, sac.SAC, trpo.TRPO, rainbow.Rainbow]

    # list of environments
    singleDimEnvs = [cartPoleEnv.CartPoleEnv, cartPoleEnvDiscrete.CartPoleEnvDiscrete, frozenLakeEnv.FrozenLakeEnv,
                     pendulumEnv.PendulumEnv, acrobotEnv.AcrobotEnv, mountainCarEnv.MountainCarEnv]
    environments = singleDimEnvs + atariEnv.AtariEnv.subEnvs

    # list of allowed environments to pair up
    allowedEnvs = {
        deepQ.DeepQ: singleDimEnvs,
        deepQ.DeepQPrioritized: singleDimEnvs,
        deepQ.DeepQHindsight: singleDimEnvs,
        qLearning.QLearning: [cartPoleEnvDiscrete.CartPoleEnvDiscrete, frozenLakeEnv.FrozenLakeEnv],
        drqn.DRQN: environments,
        drqn.DRQNPrioritized: environments,
        drqn.DRQNHindsight: environments,
        adrqn.ADRQN: environments,
        adrqn.ADRQNPrioritized: environments,
        adrqn.ADRQNHindsight: environments,
        doubleDuelingQNative.DoubleDuelingQNative: singleDimEnvs,
        drqnNative.DRQNNative: singleDimEnvs,
        drqnConvNative.DRQNConvNative: atariEnv.AtariEnv.subEnvs,
        ppoNative.PPONative: singleDimEnvs,
        reinforceNative.ReinforceNative: singleDimEnvs,
        actorCriticNative.ActorCriticNative: singleDimEnvs,
        sarsa: [cartPoleEnvDiscrete.CartPoleEnvDiscrete, frozenLakeEnv.FrozenLakeEnv],
        trpo.TRPO: singleDimEnvs,
        rainbow.Rainbow: singleDimEnvs,
        cem.CEM: environments,
        npg.NPG: environments,
        ddpg.DDPG: environments,
        sac.SAC: environments
    }
    allowedEnvs = {agent.displayName: [env.displayName for env in envs] for (agent, envs) in allowedEnvs.items()}

    # list of allowed agents to pair up
    allowedAgents = {}
    for agent, envs in allowedEnvs.items():
        for env in envs:
            curAgents = allowedAgents.get(env)
            if not curAgents:
                curAgents = []
                allowedAgents[env] = curAgents
            curAgents.append(agent)

    envName = [opt.displayName for opt in environments]  # environment names
    agtName = [opt.displayName for opt in agents]  # agent names

    msg = queue.Queue()  # messages queue
    mod = model.Model()  # model initialize

    params = None  # hyper parameters
    inputParams = []  # input hyper parameters
    tempImages = []  # image queue
    noImg = PIL.Image.open("./static/img/noImg.png")  # image for when the agent has no image
    curEp = 0
    curStep = 0
    curFin = False
    curDisplayIndex = 0
    curThread = None
    isLogin = False
    accessKey = None
    secretKey = None
    securityToken = None
    jobID = generate_jobID()
    instances = ["c4.large ($0.10/hr)", "c4.xlarge ($0.19/hr)", "c4.2xlarge ($0.39/hr)", "c4.4xlarge ($0.79/hr)",
                 "c4.8xlarge ($1.59/hr)", "g4dn.xlarge ($0.52/hr)", "g4dn.2xlarge ($0.75/hr)",
                 "g4dn.4xlarge ($1.20/hr)", "g4dn.8xlarge ($2.17/hr)"]
    app.run()
