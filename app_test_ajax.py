from flask import Flask, url_for, render_template, g, request, jsonify, flash
import random
import time
from MVC import model
import threading
import queue
from MVC.model import Model

from Agents import qLearning, drqn, deepQ, adrqn, doubleDuelingQNative, drqnNative, drqnConvNative, ppoNative, \
    reinforceNative, actorCriticNative, cem, npg, ddpg, sac, trpo, rainbow
from Environments import cartPoleEnv, cartPoleEnvDiscrete, atariEnv, frozenLakeEnv, pendulumEnv, acrobotEnv, \
    mountainCarEnv

app = Flask(__name__)
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
@app.route('/ajax')
def index():
    # flash(1000)
    return render_template('ajax.html')

@app.route('/startTrain')
def startTrain():
    mod = model.Model()
    mod.environment_class = cartPoleEnvDiscrete.CartPoleEnvDiscrete
    mod.agent_class = qLearning.QLearning
    threading.Thread(target=mod.run_learning, args=[msg, ] + [1000,200,0.97,0.1,1,0.018,0.18]).start()
    # while msg.empty():
    #     print("empty")
    #
    # print("not empty")
    # print(msg.get(block=True).data.loss)
    # else:
    #     message = msg.get()
    # if msg.type == Model.Message.STATE:
    #     print("state")
    #     if message.data == Model.Message.EPISODE:
    #         print("episode")
    #     elif message.data == Model.Message.TRAIN_FINISHED:
    #         print("train fin")
    #     elif message.data == Model.Message.TEST_FINISHED:
    #         print("test fin")
    # elif msg.type == Model.Message.EVENT:
    #     print("event")
    #     print(msg.get().data.reward)

    return jsonify(result=1000)

@app.route('/runTrain')
def runTrain():
    temp = msg.get(block=True)
    episodeAccLoss= 0
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            episodeAccLoss += temp.data.loss
        temp = msg.get(block=True)
    return jsonify(loss=episodeAccLoss/200)

    # train = None
    # finished = None
    # episode = None
    # image = None
    # epsilon = None
    # reward = None
    # loss = None
    # temp = msg.get(block=True)
    # if temp.type == Model.Message.EVENT:
    #     print("state")
    #     if temp.data == Model.Message.EPISODE:
    #         episode = True
    #     elif temp.data == Model.Message.TRAIN_FINISHED:
    #         train = True
    #         finished = True
    #     elif temp.data == Model.Message.TEST_FINISHED:
    #         test = True
    #         finished = True
    # elif temp.type == Model.Message.STATE:
    #     image = temp.data.image
    #     epsilon = temp.data.epsilon
    #     reward = temp.data.reward
    #     loss = temp.data.loss

    # return jsonify(train=train, test=test, finished=finished, episode=episode, image=image, epsilon=epsilon,
    #                reward=reward, loss=loss)

# @app.route('/add1')
# def add_numbers():
#     input = request.args.get('input', 0, type=int)
#     return jsonify(result=random.randint(0, 100))
#
# # @app.route('/flash')
# # def flashing():
# #     flash("1000");
#
# @app.route('/add1Infinity')
# def add_1():
#     # input = request.args.get('input', 0, type=int)
#     return jsonify(result=random.randint(0, 100))
# flag = False;

# @app.route('/add1Initialize')
# def add_1_initialize():
#     # flag=True;
#     # if
#     # input = request.args.get('input', 0, type=int)
#     return jsonify(result=10)
#     # start_flashing();
#
# # def start_flashing():
# #     while(True):
# #         flashing();
# #
# # def flashing():
# #     flash(random.randint(0, 9))

if __name__ == "__main__":
    msg = queue.Queue()
    app.run()