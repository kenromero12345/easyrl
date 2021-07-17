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

# from storages.backends.s3boto3 import S3Boto3Storage

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
from utilities import get_aws_lambda, get_aws_s3, \
    invoke_aws_lambda_func, is_valid_aws_credential, generate_jobID
import apps
import logging

##no flask msg when running
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


app = Flask(__name__)  #intialiaze app
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # do not use cache in this application


# Starting application
# Sending environment and agent names and allowed environments and agents to be blocked
# displaying index page
@app.route('/')
@app.route('/index/<session>')
def indexPage(session=1):
    mh = getMH(session)  # get the session

    # create session if mh is None
    if mh is None:
        mh = ModelHelper(int(session))
        # mh.awsSession = int(session)
        mhList.append(mh)

    if mh.isLogin:
        # get info
        info = lambda_info(mh.accessKey,
                           mh.secretKey,
                           mh.securityToken,
                           mh.jobID, {})
        info = json.loads(info)

        # temp = [i.get('name') for i in info.get('environments')]

        # iterate through the environment
        for i in range(len(info.get('environments'))):
            name = info.get('environments')[i].get('name')
            name = name.lower().replace(" ", "_")
            info.get('environments')[i].update({"file": name})

        # global awsAg, awsEnv, awsEnvMap, awsAgMap, awsParam
        mh.awsEnv = info.get('environments')
        mh.awsAg = info.get('agents')
        mh.awsEnvMap = info.get('environmentsMap')
        mh.awsAgMap = info.get('agentsMap')
        mh.awsParam = info.get('parameters')
        return render_template('index.html', env=info.get('environments'), agt=info.get('agents'),
                               envMap=mh.awsEnvMap, agMap=mh.awsAgMap, isLogin=mh.isLogin, instances=instances,
                               session=mh.awsSession)
    else:
        return render_template('index.html', envName=envName, agtName=agtName, allowedEnvs=allowedEnvs,
                               allowedAgents=allowedAgents, isLogin=mh.isLogin, instances=instances,
                               session=mh.awsSession)


# get info using lambda function
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
    # print("{}lambda_info_job{}={}".format(apps.FORMAT_GREEN, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# login page of the application
@app.route('/login/<session>')
def loginPage(session):
    return render_template('login.html', session=session)


# get the model helper
def getMH(session):
    for i in mhList:
        if i.awsSession == int(session):
            return i
    return None


# logging in the AWS account
@app.route('/loggingIn')
def loggingIn():
    # global isLogin, accessKey, secretKey, securityToken, jobID
    mh = getMH(request.args.get('session'))  # get model helper from session
    mh.accessKey = request.args.get('accessKey')
    mh.secretKey = request.args.get('secretKey')
    mh.securityToken = request.args.get('securityToken')
    is_valid_aws_credential(mh.accessKey, mh.secretKey, mh.securityToken)  # check if credential works
    mh.isLogin = is_valid_aws_credential(mh.accessKey, mh.secretKey, mh.securityToken)
    # TODO: change
    # jobID = generate_jobID()
    mh.jobID = str(mh.awsSession)
    print(mh.isLogin)
    if mh.isLogin:
        # mod.createBridge(jobID, secretKey, accessKey, securityToken)
        # session = boto3.session.Session()
        # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        # global awsS3
        mh.awsS3 = get_aws_s3(mh.accessKey, mh.secretKey)  # get s3
        return jsonify(success=True)  # login success
    else:
        return jsonify(success=False)  # login fail


# logging out the AWS account
@app.route('/logout/<session>')
def logout(session):
    # global isLogin, jobID
    mh = getMH(session)  # get model helper from session
    mh.isLogin = False
    # TODO: replace request.post.get

    # terminate instance
    lambda_terminate_instance(
        mh.accessKey,
        mh.secretKey,
        mh.securityToken,
        mh.jobID,
        {
        }
    )

    # job id removed
    mh.jobID = None
    mh.accessKey = None
    mh.secretKey = None
    mh.securityToken = None

    return jsonify(success=True)


# terminate the instance of the given credentials and job id
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
    # print("{}lambda_terminate_instance{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, response['Payload'].read()))
    if response['StatusCode'] == 200:
        streambody = response['Payload'].read().decode()
        # print("{}stream_body{}={}".format(apps.FORMAT_BLUE, apps.FORMAT_RESET, streambody))
        return True
    return False


# gets the safe value of the given value
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
@app.route('/model/<environment>/<agent>/<session>')
def modelPage(environment, agent, session):
    # set agent class
    mh = getMH(session)
    for curAgent in agents:
        if agent == curAgent.displayName:
            mh.mod.agent_class = curAgent
            break

    # set environment class
    for curEnv in environments:
        if environment == curEnv.displayName:
            mh.mod.environment_class = curEnv
            break

    mh.mod.reset()  # reset model

    # set parameters to be sent
    params = [ag.Agent.Parameter('Number of Episodes', 1, 655360, 1, 1000, True, True,
                                 "The number of episodes to run the model on"),
              ag.Agent.Parameter('Max Size', 1, 655360, 1, 200, True, True,
                                 "The max number of timesteps permitted in an episode")]
    for param in mh.mod.agent_class.parameters:
        params.append(param)

    return render_template('model.html', params=params, isLogin=mh.isLogin, session=session)


# displaying model page
# sending parameters info
@app.route('/model/<environment>/<agent>/<instance>/<session>')
def modelPageAWS(environment, agent, instance, session):
    # global awsCurAg, awsCurEnv, awsInst
    mh = getMH(session)
    # set agent
    for i in mh.awsAg:
        if i.get('name') == agent:
            mh.awsCurAg = i
            break

    # set environment
    for i in mh.awsEnv:
        if i.get('name') == environment:
            mh.awsCurEnv = i
            break

    # set instance
    mh.awsInst = instance

    # set parameters
    tempParams = []
    for i in mh.awsCurAg.get('parameters'):
        for j in mh.awsParam:
            if j == i:
                mh.awsParam.get(j)['id'] = j
                tempParams.append(mh.awsParam.get(j))
    # print(tempParams)
    return render_template('model.html', params=tempParams, isLogin=mh.isLogin, session=session)


# saving model
@app.route('/saveModel')
def saveModel():
    mh = getMH(request.args.get('session'))  # get the model helper from the session
    if mh.isLogin:
        #  export the model through lambda function
        temp = lambda_export_model(
            mh.accessKey,
            mh.secretKey,
            mh.securityToken,
            mh.jobID,
            {
            }
        )
        return temp
    else:
        # encode the model
        temp = jsonpickle.encode((mh.mod.agent.displayName, mh.mod.agent.memsave()))
        return jsonify(agent=temp)


# exporting for the lambda function
def lambda_export_model(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_EXPORT_MODEL,
        "arguments": arguments
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    print("{}lambda_export_model{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# loading model
@app.route('/loadModel', methods=['POST'])
def loadModel():
    # TODO: post get session?
    mh = getMH(request.form.get('session'))  # get the model helper from the session
    # print(request.form.get('session'))
    # if mh is None:
    #     mh = request.files["session"]
    if mh.isLogin:
        if "upload" not in request.files:  # check if upload exists
            return "No file"

        # mem = request.form.get('agent')
        mem = request.files["upload"]

        if mem == "":  # check if file exists
            return "Please select a file"

        if mem:
            # print(mem)
            # name = "easyrl-{}{}".format(jobID, awsSession)
            name = "easyrl-{}".format(mh.jobID)  # name of the bucket
            # name = "easyrl"
            mh.awsS3.create_bucket(ACL='public-read', Bucket=name)
            upload_file_to_s3(mh, mem, name)

            # output = upload_file()
            # return str(output)
            # print(str(output))

            # import lambda function
            temp = lambda_import(
                mh.accessKey,
                mh.secretKey,
                mh.securityToken,
                mh.jobID,
                {}
            )
            print(temp)
            return temp

            # bucket = "easyrl-{}{}".format(jobID, awsSession)
            #
            # media_storage = S3Boto3Storage()
            # media_storage.location = ''
            # media_storage.file_overwrite = True
            # media_storage.access_key = accessKey
            # media_storage.secret_key = secretKey
            # media_storage.bucket_name = bucket
            #
            # s3_file_path = os.path.join(
            #     media_storage.location,
            #     'model.bin'
            # )
            #
            # media_storage.save(s3_file_path, mem)
            #
            # temp = lambda_import(
            #     accessKey,
            #     secretKey,
            #     securityToken,
            #     jobID,
            #     {}
            # )
            # print(mem)
            # print(temp)
            # return temp
    else:
        try:
            name, mem = jsonpickle.decode(request.form.get('agent'))  # decode model

            # validate the decoded model
            if mh.mod.agent_class.displayName == name:
                mh.mod.isLoaded = True
                mh.mod.memload = mem
                return jsonify(success=True)
        except ValueError:
            return jsonify(success=False)
        return jsonify(success=False)


# upload the file to s3
def upload_file_to_s3(mh, file, bucket_name, acl="public-read"):
    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """
    try:
        # upload file object to bucket
        mh.awsS3.upload_fileobj(
            file,
            bucket_name,
            "model.bin"
            ,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format('', file.filename)


# lambda import model function
def lambda_import(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_IMPORT,
        "arguments": arguments,
    }

    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    print("{}lambda_import{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, response['Payload'].read()))
    # if response['StatusCode'] == 200:
    #     streambody = response['Payload'].read().decode()
    #     print("{}stream_body{}={}".format(apps.FORMAT_BLUE, apps.FORMAT_RESET, streambody))
    #     return True
    # return False
    print(response)
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# starting training
@app.route('/startTrain')
def startTrain():
    # global inputParams, tempImages
    mh = getMH(request.args.get('session'))
    # print(mh.awsSession)
    if mh.isLogin:
        mh.inputParams = []
        mh.tempImages = []

        # set hyperparameters
        temp = request.args.get('0')
        i = 0
        while temp is not None:
            mh.inputParams.append(float(temp))
            i += 1
            temp = request.args.get(str(i))

        payload = setUpPayload(mh)

        return lambda_run_job(
            mh.accessKey,
            mh.secretKey,
            mh.securityToken,
            mh.jobID,
            payload
        )
    else:
        print(mh.mod)
        print(mh.msg)
        if mh.mod.isRunning:  # if model is running
            return jsonify(finished=False)
        else:
            # reset hyperparameters and image queue
            mh.inputParams = []
            mh.tempImages = []

            # set hyperparameters
            temp = request.args.get('0')
            i = 0
            while temp is not None:
                mh.inputParams.append(float(temp))
                i += 1
                temp = request.args.get(str(i))
            print(mh.inputParams)
            # run training
            # global curThread
            mh.curThread = threading.Thread(target=mh.mod.run_learning, args=[mh.msg, ] + mh.inputParams)
            # global curDisplayIndex
            mh.curDisplayIndex = 0
            mh.curThread.start()
            return jsonify(finished=True)


#
def setUpPayload(mh):
    payload = {
        "instanceType": get_safe_value(str, mh.awsInst, "c4.xlarge")
        , "killTime": get_safe_value(int, mh.awsKillTime, 600)
        , "environment": get_safe_value(int, mh.awsCurEnv.get('index'), 1)
        , "agent": get_safe_value(int, mh.awsCurAg.get('index'), 1)
        , "continuousTraining": get_safe_value(int, mh.awsContTrain, 0)
        # , "episodes": 20
        # , "steps": 50
        # , "gamma": 0.97
        # , "minEpsilon":  0.01
        # , "maxEpsilon":  0.99
        # , "decayRate":  0.01
        # , "batchSize": 32
        # , "memorySize":  1000
        # , "targetInterval":  10
        # , "alpha": 0.9
        # , "historyLength": 10
        #
        # , "delta":  0.001
        # , "sigma": 0.5
        # , "population":  10
        # , "elite": 0.2
        #
        # , "tau": 0.97
        # , "temperature": 0.97
        #
        # , "learningRate": 0.001
        # , "policyLearnRate": 0.001
        # , "valueLearnRate": 0.001
        # , "horizon": 50
        # , "epochSize": 500
        # , "ppoEpsilon": 0.2
        # , "ppoLambda": 0.95
        # , "valueLearnRatePlus": 0.001
    }

    for j in range(len(mh.awsCurAg.get('parameters'))):
        if "episodes" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 20)
        elif "steps" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 50)
        elif "gamma" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j], 0.97)
        elif "minEpsilon" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j], 0.01)
        elif "maxEpsilon" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j], 0.99)
        elif "decayRate" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j], 0.01)
        elif "batchSize" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 32)
        elif "memorySize" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 1000)
        elif "targetInterval" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 10)
        elif "historyLength" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 10)
        elif "alpha" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j], 0.9)
        elif "delta" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.001)  # TODO: change from int
        elif "sigma" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.5)  # TODO: change from int
        elif "population" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(int, mh.inputParams[j], 10)
        elif "elite" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.2)  # TODO: change from int
        elif "tau" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.97)  # TODO: change from int
        elif "temperature" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.97)  # TODO: change from int
        elif "learningRate" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.001)  # TODO: change from int
        elif "policyLearnRate" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.001)  # TODO: change from int
        elif "valueLearnRate" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.001)  # TODO: change from int
        elif "horizon" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       50)  # TODO: right? float?
        elif "epochSize" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       500)  # TODO: right? float?
        elif "ppoEpsilon" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.2)  # TODO: change from int
        elif "ppoLambda" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.95)  # TODO: change from int
        elif "valueLearnRatePlus" == mh.awsCurAg.get('parameters')[j]:
            payload[mh.awsCurAg.get('parameters')[j]] = get_safe_value(float, mh.inputParams[j],
                                                                       0.001)  # TODO: change from int
    return payload


# lambda run training task function
def lambda_run_job(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_RUN_JOB,
        "arguments": arguments,
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    # print("{}lambda_run_job{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# gets information per poll
@app.route('/poll')
def poll():
    mh = getMH(request.args.get('session'))  # get model helper from session
    if mh.jobID is None:
        return {
            "instanceState": "booting",
            "instanceStateText": "Loading...",
            "error": "No Job ID"
        }

    # global inputParams, tempImages
    mh.inputParams = []
    mh.tempImages = []

    # set hyperparameters
    temp = request.args.get('0')
    i = 0
    while temp is not None:
        mh.inputParams.append(float(temp))
        i += 1
        temp = request.args.get(str(i))

    try:
        # TODO: possibly don't run if access key, secret key, sec token, jobid are NONE
        temp = lambda_poll(
            mh.accessKey,
            mh.secretKey,
            mh.securityToken,
            mh.jobID,
            setUpPayload(mh)
        )
        print(temp)
        return temp
    except:
        return {
            "instanceState": "booting",
            "instanceStateText": "Loading..."
        }


# lambda poll function
def lambda_poll(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_POLL,
        "arguments": arguments,
    }
    # print(str(data).replace('\'', '"'))
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    # print("{}lambda_poll{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# running training
@app.route('/runTrain')
def runTrain():
    mh = getMH(request.args.get('session'))
    temp = mh.msg.get(block=True)  # receive message

    # train is finished
    if temp.data == Model.Message.TRAIN_FINISHED:
        return jsonify(finished=True)

    # test is still running
    mh.episodeAccLoss = 0
    mh.episodeAccEpsilon = 0
    mh.episodeAccReward = 0
    global tempImages
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            if temp.data.loss:
                mh.episodeAccLoss += temp.data.loss
            if temp.data.epsilon:
                mh.episodeAccEpsilon += temp.data.epsilon
            if temp.data.reward:
                mh.episodeAccReward += temp.data.reward
            if temp.data.image:
                mh.tempImages.append((temp.data.image, temp.data.episode, temp.data.step))

        temp = mh.msg.get(block=True)
    # print(mh.episodeAccLoss)
    # print(mh.episodeAccReward)
    # print(mh.episodeAccEpsilon)
    # print(mh.inputParams)
    return jsonify(loss=mh.episodeAccLoss / mh.inputParams[1], reward=mh.episodeAccReward,
                   epsilon=mh.episodeAccEpsilon / mh.inputParams[1],
                   finished=False)  # inputParams[1] is max size the hyperparameter


# display an image for this route
# TODO: session change
@app.route('/tempImage')
def tempImage():
    # global noImg, curEp, curStep, curFin, curDisplayIndex
    mh = getMH(request.args.get('session'))
    if tempImages:
        temp = tempImages[mh.curDisplayIndex]
        mh.curEp = temp[1]
        mh.curStep = temp[2]
        if mh.curDisplayIndex == len(tempImages) - 1:
            if mh.curThread.is_alive():
                mh.curFin = False
            else:
                mh.curFin = True
                mh.curDisplayIndex = 0
        else:
            mh.curFin = False
            mh.curDisplayIndex += 1
        return serve_pil_image(temp[0])  # image for model
    else:
        mh.curEp = 0
        mh.curStep = 0
        mh.curFin = True
        return serve_pil_image(noImg)  # image for no display


# display the episode and step number of the displayed environment
@app.route('/tempImageEpStep')
def tempImageEpStep():
    mh = getMH(request.args.get('session'))
    return jsonify(episode=mh.curEp, step=mh.curStep, finished=mh.curFin)


# starting testing
@app.route('/startTest')
def startTest():
    mh = getMH(request.args.get('session'))
    # global inputParams, tempImages
    if mh.isLogin:
        mh.inputParams = []
        mh.tempImages = []

        # set hyperparameters
        temp = request.args.get('0')
        i = 0
        while temp is not None:
            mh.inputParams.append(float(temp))
            i += 1
            temp = request.args.get(str(i))

        payload = setUpPayload(mh)

        return lambda_test_job(
            mh.accessKey,
            mh.secretKey,
            mh.securityToken,
            mh.jobID,
            payload
        )
    else:
        if mh.mod.isRunning:  # if model is running
            return jsonify(finished=False)
        else:
            if mh.mod.agent or mh.mod.isLoaded:
                # reset hyperparameters and image queue

                mh.inputParams = []
                mh.tempImages = []

                # set hyperparameters
                temp = request.args.get('0')
                i = 0
                while temp is not None:
                    mh.inputParams.append(float(temp))
                    i += 1
                    temp = request.args.get(str(i))

                # run testing
                # global curThread
                mh.curThread = threading.Thread(target=mh.mod.run_testing, args=[mh.msg, ] + mh.inputParams)
                # global curDisplayIndex
                mh.curDisplayIndex = 0
                mh.curThread.start()
                return jsonify(finished=True, model=True)
            else:
                return jsonify(finished=False, model=False)  # if agent doesn't exist


# lambda run testing job
def lambda_test_job(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_RUN_TEST,
        "arguments": arguments,
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    print("{}lambda_test_job{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# running testing
@app.route('/runTest')
def runTest():
    mh = getMH(request.args.get('session'))  # get model helper from session
    temp = mh.msg.get(block=True)  # receive message

    # test is finished
    if temp.data == Model.Message.TEST_FINISHED:
        return jsonify(finished=True)

    # test is still running
    mh.episodeAccReward = 0
    while temp.data != Model.Message.EPISODE:
        if temp.type == Model.Message.STATE:
            if temp.data.reward:
                mh.episodeAccReward += temp.data.reward
            if temp.data.image:
                mh.tempImages.append((temp.data.image, temp.data.episode, temp.data.step))
        temp = mh.msg.get(block=True)

    return jsonify(reward=mh.episodeAccReward, finished=False)


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
    mh = getMH(request.args.get('session'))  # get model helper from session
    if mh.isLogin:
        return lambda_halt_job(
            mh.accessKey,
            mh.secretKey,
            mh.securityToken,
            mh.jobID,
            {
            }
        )
    else:
        if mh.mod.isRunning:
            mh.mod.halt_learning()
        return jsonify(finished=True)


# lambda function to halt testing and training
def lambda_halt_job(aws_access_key, aws_secret_key, aws_security_token, job_id, arguments):
    lambdas = get_aws_lambda(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    data = {
        "accessKey": aws_access_key,
        "secretKey": aws_secret_key,
        "sessionToken": aws_security_token,
        "jobID": job_id,
        "task": apps.TASK_HALT_JOB,
        "arguments": arguments
    }
    response = invoke_aws_lambda_func(lambdas, str(data).replace('\'', '"'))
    payload = response['Payload'].read()
    print("{}lambda_halt_job{}={}".format(apps.FORMAT_RED, apps.FORMAT_RESET, payload))
    if len(payload) != 0:
        return "{}".format(payload)[2:-1]
    else:
        return ""


# change display episode
@app.route('/changeDisplayEpisode')
def changeDisplayEpisode():
    mh = getMH(request.args.get('session'))  # get model helper from session
    # global curDisplayIndex
    ep = int(request.args.get('episode'))  # get the episode number
    temp = tempImages[-1][1]
    if temp < ep:
        episode = binarySearchEpisode(tempImages, 0, len(tempImages), temp)
    else:
        episode = binarySearchEpisode(tempImages, 0, len(tempImages), ep)

    if episode == -1:
        print("error")
    else:
        mh.curDisplayIndex = episode
    return jsonify(finished=True)


# binary search helper for specifically finding a step
def binarySearchSteps(arr, low, high, x, ep):
    # Check base case
    if high >= low:

        mid = (high + low) // 2
        # If element is present at the middle itself
        if arr[mid][2] == x:
            return mid

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
    mh = getMH(request.args.get('session'))  # get the model helper from session
    # halting
    if mh.mod.isRunning:
        mh.mod.halt_learning()

    # global tempImages, msg
    # reset images
    mh.tempImages = []
    # reset messages
    mh.msg = queue.Queue()
    # reset model
    mh.mod.reset()
    # global curDisplayIndex
    mh.curDisplayIndex = 0
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


# get new window's session number
@app.route('/newWindow')
def newWindow():
    return jsonify(session=mhList[-1].awsSession + 1)


# running application
class ModelHelper:
    def __init__(self, session):
        self.msg = queue.Queue()  # messages queue
        self.mod = model.Model()  # model initialize

        self.params = None  # hyper parameters
        self.inputParams = []  # input hyper parameters
        self.tempImages = []  # image queue
        self.curEp = 0  # current episode
        self.curStep = 0  # current step
        self.curFin = False  # if task is finished
        self.curDisplayIndex = 0  # the index of the displayed environment
        self.curThread = None  # the thread that runs the task

        self.isLogin = False  # if aws credentials is used
        self.accessKey = None  # the aws access key
        self.secretKey = None  # the aws secret key
        self.securityToken = None  # the aws security token
        self.jobID = None  # the job id
        self.awsEnv = None  # the environment
        self.awsAg = None  # the agent
        self.awsCurEnv = None  # the current environment
        self.awsCurAg = None  # the current agent
        self.awsInst = None  # the instance
        self.awsEnvMap = None  # the environment map
        self.awsAgMap = None  # the agent map
        self.awsParam = None  # the parameters
        self.awsSession = session  # the aws session number
        self.awsKillTime = 31536000  # the kill time of the instance
        self.awsContTrain = 0  # to use continuous training functionality
        self.awsS3 = None


# main application
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

    # list of instances
    instances = ["c4.large ($0.10/hr)", "c4.xlarge ($0.19/hr)", "c4.2xlarge ($0.39/hr)", "c4.4xlarge ($0.79/hr)",
                 "c4.8xlarge ($1.59/hr)", "g4dn.xlarge ($0.52/hr)", "g4dn.2xlarge ($0.75/hr)",
                 "g4dn.4xlarge ($1.20/hr)", "g4dn.8xlarge ($2.17/hr)"]
    # awsEnv = None
    # awsAg = None
    # awsCurEnv = None
    # awsCurAg = None
    # awsInst = None
    # awsEnvMap, awsAgMap, awsParam = None, None, None
    # awsSession = 1
    # awsKillTime = 31536000
    # awsContTrain = 0
    # awsS3 = None

    mhList = []  # list of model helper for tab functionality

    noImg = PIL.Image.open("./static/img/noImg.png")  # image for when the agent has no image

    app.run()  # run the app

# class AWSLambdaKeys:
#
