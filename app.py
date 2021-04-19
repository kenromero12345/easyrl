import io
from types import ModuleType
import PIL
from PIL.Image import Image
from flask import Flask, render_template, g, request, jsonify, send_file
import time
from Agents import qLearning, drqn, deepQ, adrqn, agent as ag, doubleDuelingQNative, drqnNative, drqnConvNative, ppoNative, \
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

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
@app.route('/index')
def indexPage():
    return render_template('index.html', envName=envName, agtName=agtName, allowedEnvs=allowedEnvs,
                           allowedAgents=allowedAgents)

@app.route('/custEnv')
def custEnv():
    file = request.args.get('file')
    module = ModuleType('customEnv')
    sys.modules['customEnv'] = module
    exec(file, module.__dict__)

    global environments
    environments = [module.CustomEnv] + environments
    global envName
    envName = [module.CustomEnv.displayName] + envName
    return jsonify(finished=True)

@app.route('/custAg')
def custAg():
    file = request.args.get('file')
    module = ModuleType('customAg')
    sys.modules['customAg'] = module
    exec(file, module.__dict__)

    global agents
    agents = [module.CustomAgent] + environments
    global agtName
    agtName = [module.CustomAgent.displayName] + agtName
    return jsonify(finished=True)

@app.route('/model/<environment>/<agent>')
def modelPage(environment, agent):
    for curAgent in agents:
        if agent == curAgent.displayName:
            mod.agent_class = curAgent
            break
    for curEnv in environments:
        if environment == curEnv.displayName:
            mod.environment_class = curEnv
            break
    mod.reset()
    params = [ag.Agent.Parameter('Number of Episodes', 1, 655360, 1, 1000, True, True,
                                    "The number of episodes to run the model on"),
              ag.Agent.Parameter('Max Size', 1, 655360, 1, 200, True, True,
                                    "The max number of timesteps permitted in an episode")]
    for param in mod.agent_class.parameters:
        params.append(param)
    return render_template('model.html', params=params)

@app.route('/saveModel')
def saveModel():
    temp = jsonpickle.encode(mod.agent)
    return jsonify(agent=temp)

@app.route('/loadModel')
def loadModel():
    temp = jsonpickle.decode(request.args.get('agent'))
    print(type(temp))
    print(mod.agent_class)
    if mod.agent_class == type(temp):
        print(True)
        mod.agent = temp
        return jsonify(success=True)
    return jsonify(success=False)

@app.route('/startTrain')
def startTrain():
    if mod.isRunning:
        return jsonify(finished=False)
    else:
        global inputParams, tempImages
        inputParams = []
        tempImages = []
        temp = request.args.get('0')
        i = 0
        while temp is not None:
            inputParams.append(float(temp))
            i += 1
            temp = request.args.get(str(i))

        threading.Thread(target=mod.run_learning, args=[msg, ] + inputParams).start()
        return jsonify(finished=True)

@app.route('/runTrain')
def runTrain():
    temp = msg.get(block=True)
    if temp.data == Model.Message.TRAIN_FINISHED:
        return jsonify(finished=True)

    episodeAccLoss= 0
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
                tempImages.append(temp.data.image)

        temp = msg.get(block=True)

    return jsonify(loss=episodeAccLoss/inputParams[1], reward=episodeAccReward,
                   epsilon=episodeAccEpsilon/inputParams[1], finished=False) #inputParams[1] is max size the hyperparameter

@app.route('/tempImage')
def tempImage():
    global noImg
    if len(tempImages) == 1:
        return serve_pil_image(tempImages[0])
    if tempImages:
        return serve_pil_image(tempImages.pop(0))
    else:
        return serve_pil_image(noImg)

@app.route('/startTest')
def startTest():
    if mod.isRunning:
        return jsonify(finished=False)
    else:
        if mod.agent:
            global inputParams, tempImages
            inputParams = []
            tempImages = []

            temp = request.args.get('0')
            i = 0
            while temp is not None:
                inputParams.append(float(temp))
                i += 1
                temp = request.args.get(str(i))

            threading.Thread(target=mod.run_testing, args=[msg, ] + inputParams).start()
            return jsonify(finished=True, model=True)
        else:
            return jsonify(finished=False, model=False)

@app.route('/runTest')
def runTest():
    temp = msg.get(block=True)
    if temp.data == Model.Message.TEST_FINISHED:
        return jsonify(finished=True)

    episodeAccReward = 0
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            if temp.data.reward:
                episodeAccReward += temp.data.reward

        temp = msg.get(block=True)

    return jsonify(reward=episodeAccReward, finished=False)

# # https://stackoverflow.com/questions/7877282/how-to-send-image-generated-by-pil-to-browser
def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

@app.route('/halt')
def halt():
    print("halting")
    if mod.isRunning:
        mod.halt_learning()
    return jsonify(finished=True)

@app.route('/reset')
def reset():
    print("reset")
    if mod.isRunning:
        mod.halt_learning()
    global tempImages
    tempImages = []
    global msg
    msg = queue.Queue()
    return jsonify(finished=True)

@app.route('/about')
def aboutPage():
    return render_template('about.html')

@app.route('/help')
def helpPage():
    return render_template('help.html')

@app.before_request
def before_request():
    g.start = time.time()

@app.after_request
def after_request(response):
    diff = time.time() - g.start
    print()
    if ((response.response) and
        (200 <= response.status_code < 300) and
        (response.content_type.startswith('text/html'))):
        response.set_data(response.get_data().replace(
            b'__EXECUTION_TIME__', bytes(str(diff), 'utf-8')))
    return response

if __name__ == "__main__":
    agents = [deepQ.DeepQ, deepQ.DeepQPrioritized, deepQ.DeepQHindsight, qLearning.QLearning, drqn.DRQN,
              drqn.DRQNPrioritized, drqn.DRQNHindsight, adrqn.ADRQN, adrqn.ADRQNPrioritized, adrqn.ADRQNHindsight,
              doubleDuelingQNative.DoubleDuelingQNative, drqnNative.DRQNNative, drqnConvNative.DRQNConvNative,
              ppoNative.PPONative, reinforceNative.ReinforceNative, actorCriticNative.ActorCriticNative, sarsa,
              cem.CEM, npg.NPG, ddpg.DDPG, sac.SAC, trpo.TRPO, rainbow.Rainbow]
    singleDimEnvs = [cartPoleEnv.CartPoleEnv, cartPoleEnvDiscrete.CartPoleEnvDiscrete, frozenLakeEnv.FrozenLakeEnv,
                    pendulumEnv.PendulumEnv, acrobotEnv.AcrobotEnv, mountainCarEnv.MountainCarEnv]
    environments = singleDimEnvs + atariEnv.AtariEnv.subEnvs
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
    allowedAgents = {}
    for agent, envs in allowedEnvs.items():
        for env in envs:
            curAgents = allowedAgents.get(env)
            if not curAgents:
                curAgents = []
                allowedAgents[env] = curAgents
            curAgents.append(agent)

    envName = [opt.displayName for opt in environments]
    agtName = [opt.displayName for opt in agents]
    msg = queue.Queue()
    mod = model.Model()
    params = None
    inputParams = []
    tempImages = []
    noImg = PIL.Image.open("./static/img/noImg.png")
    app.run()