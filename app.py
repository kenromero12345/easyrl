from flask import Flask, render_template, g
import time
from Agents import qLearning, drqn, deepQ, adrqn, agent as ag, doubleDuelingQNative, drqnNative, drqnConvNative, ppoNative, \
    reinforceNative, actorCriticNative, cem, npg, ddpg, sac, trpo, rainbow
from Environments import cartPoleEnv, cartPoleEnvDiscrete, atariEnv, frozenLakeEnv, pendulumEnv, acrobotEnv, \
    mountainCarEnv
from Agents.sarsa import sarsa

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def indexPage():
    return render_template('index.html', envName=envName, agtName=agtName, allowedEnvs=allowedEnvs,
                           allowedAgents=allowedAgents)

@app.route('/model/<environment>/<agent>')
def modelPage(environment, agent):
    for curAgent in agents:
        if agent == curAgent.displayName:
            agent = curAgent
            break
    for curEnv in environments:
        if environment == curEnv.displayName:
            environment = curEnv
            break

    params = [ag.Agent.Parameter('Number of Episodes', 1, 655360, 1, 1000, True, True,
                                    "The number of episodes to run the model on"),
              ag.Agent.Parameter('Max Size', 1, 655360, 1, 200, True, True,
                                    "The max number of timesteps permitted in an episode")]
    for param in agent.parameters:
        params.append(param)
    return render_template('model.html', environment=environment, agent=agent, params=params)

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
    app.run()