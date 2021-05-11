import io
from types import ModuleType
import PIL
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
    return render_template('index.html', envName=envName, agtName=agtName, allowedEnvs=allowedEnvs,
                           allowedAgents=allowedAgents)


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


# saving model
@app.route('/saveModel')
def saveModel():
    # encode the model
    temp = jsonpickle.encode(mod.agent)
    return jsonify(agent=temp)


# loading model
@app.route('/loadModel')
def loadModel():
    temp = jsonpickle.decode(request.args.get('agent'))  # decode model

    # validate the decoded model
    if mod.agent_class == type(temp):
        mod.agent = temp
        return jsonify(success=True)
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
    temp = msg.get(block=True)  #receive message

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
        if mod.agent:
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
    temp = msg.get(block=True) #receive message

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
    curThread = None;
    app.run()
