import random
import numpy as np
from Agents import cem, drqn, modelBasedAgent, modelFreeAgent
from Agents.Collections.TransitionFrame import TransitionFrame
import cProfile
from MVC import cloudBridge
import os.path

class Model:
    def __init__(self):
        # these can be set directly from the Controller based on user input from the View
        self.environment_class = None
        self.agent_class = None
        self.isHalted = False
        self.isRunning = False
        self.environment = None
        self.agent = None
        self.loadFilename = None
        self.cloudBridge = None
        self.isLoaded = False
        self.memload = None

    def createBridge(self, jobID, secretKey, accessKey, sessionToken):
        print("Bridge Created")
        if (self.cloudBridge is None):
            self.cloudBridge = cloudBridge.CloudBridge(jobID, secretKey, accessKey, sessionToken, self)

    # def run_learning(self, messageQueue, total_episodes, max_steps, *model_args):
    #     cProfile.runctx('self.run_learning2(messageQueue, total_episodes, max_steps, *model_args)', globals(), locals(),
    #                     'stats')

    # def run_learning2(self, messageQueue, total_episodes, max_steps, *model_args):
    def run_learning(self, messageQueue, total_episodes, max_steps, *model_args):
        self.isRunning = True

        if (self.cloudBridge is not None):
            self.cloudBridge.refresh()
            self.cloudBridge.setState("Training")

        if not self.environment:
            self.environment = self.environment_class()

        if self.isLoaded:
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
            self.agent.memload(self.memload)
            self.isLoaded = False
        elif self.loadFilename:
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
            self.agent.load(self.loadFilename)
            self.loadFilename = None
        elif not self.agent:
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
        else:  # if agent already exists, update the model arguments
            mem = self.agent.memsave()
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
            self.agent.memload(mem)
        
        if (isinstance(self.agent, modelFreeAgent.ModelFreeAgent)):
            '''
            Training algorithm for Model Free Agents.
            '''
            min_epsilon, max_epsilon, decay_rate = self.agent.min_epsilon, self.agent.max_epsilon, self.agent.decay_rate
            epsilon = max_epsilon

            for episode in range(int(total_episodes)):
                self.environment.reset()

                for step in range(int(max_steps)):
                    old_state = self.environment.state
                    exp_exp_tradeoff = random.uniform(0, 1)

                    if exp_exp_tradeoff > epsilon:
                        action = self.agent.choose_action(old_state)
                    else:
                        action = self.environment.sample_action()

                    reward = self.environment.step(action)

                    loss = self.agent.remember(old_state, action, reward, self.environment.state, self.environment.done)

                    if self.environment:
                        frame = self.environment.render()

                    if (self.cloudBridge is not None):
                        self.cloudBridge.submitStep(frame, epsilon, reward, loss)

                    modelState = Model.State(frame, epsilon, reward, loss, episode + 1, step + 1)
                    message = Model.Message(Model.Message.STATE, modelState)
                    messageQueue.put(message)

                    if self.isHalted or self.environment.done:
                        break

                if hasattr(self.agent, 'apply_hindsight') and callable(getattr(self.agent, 'apply_hindsight')):
                    self.agent.apply_hindsight()
                
                if (self.cloudBridge is not None):
                    self.cloudBridge.submitEpisode(episode, int(total_episodes))

                message = Model.Message(Model.Message.EVENT, Model.Message.EPISODE)
                messageQueue.put(message)

                epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay_rate * episode)

                if self.isHalted:
                    self.isHalted = False
                    break
        elif (isinstance(self.agent, modelBasedAgent.ModelBasedAgent)):
            '''
            Training algorithm for Model Based Agents.
            '''
            for episode in range(int(total_episodes)):
                # Reset the environment.
                state = self.environment.reset()
                
                
                # Evaluate the policy
                episode_trajectory = []
                loss = 0.0
                # CEM evaluates multiple policies.
                if (isinstance(self.agent, cem.CEM)):
                    for policy in self.agent.get_sample_policies():
                        # Reset the environment.
                        state = self.environment.reset()
                        # Sum of total policy rewards for this episode.
                        policy_trajectory = []
                        # Execute this episode for each policy.
                        for step in range(int(max_steps)):
                            # Execute one step.
                            old_state = self.environment.state
                            action = self.agent.choose_action(old_state, policy)
                            reward = self.environment.step(action)
                            
                            # Add the reward to the total policy reward
                            policy_trajectory.append(TransitionFrame(old_state, action, reward, self.environment.state, self.environment.done))
                            
                            # Render and save the step.
                            if self.environment:
                                frame = self.environment.render()

                            if (self.cloudBridge is not None):
                                self.cloudBridge.submitStep(frame, 0, reward, 0)
                            
                            # Send the state from the step.
                            modelState = Model.State(frame, None, reward, None, episode + 1, step + 1)
                            message = Model.Message(Model.Message.STATE, modelState)
                            messageQueue.put(message)

                            if self.environment.done or self.isHalted:
                                break
                    
                        # Add the policy rewards to the episode rewards.
                        episode_trajectory.append(policy_trajectory)
                        
                        if self.isHalted:
                            break
                    
                    # Update the agent only if all policies were evaluated.
                    if (len(episode_trajectory) == len(self.agent.get_sample_policies())):
                        loss = self.agent.update(episode_trajectory)
                        
                else:
                    # Execute this episode for each policy.
                    for step in range(int(max_steps)):
                        # Execute one step.
                        old_state = self.environment.state
                        action = self.agent.choose_action(old_state)
                        reward = self.environment.step(action)
                        
                        # Add the reward to the total policy reward
                        episode_trajectory.append(TransitionFrame(old_state, action, reward, self.environment.state, self.environment.done))
                        
                        # Render and save the step.
                        if self.environment:
                            frame = self.environment.render()

                        if (self.cloudBridge is not None):
                            self.cloudBridge.submitStep(frame, 0, reward, 0)
                        
                        # Send the state from the step.
                        modelState = Model.State(frame, None, reward, None, episode + 1, step + 1)
                        message = Model.Message(Model.Message.STATE, modelState)
                        messageQueue.put(message)

                        if self.environment.done or self.isHalted:
                            break
                    
                    # Improve the Policy
                    loss = self.agent.update(episode_trajectory)
                    
                # Send the loss of this episode.
                modelState = Model.State(None, None, 0, loss, episode + 1, step + 1)
                message = Model.Message(Model.Message.STATE, modelState)
                messageQueue.put(message)
                
                if (self.cloudBridge is not None):
                    self.cloudBridge.submitEpisode(episode, int(total_episodes))

                message = Model.Message(Model.Message.EVENT, Model.Message.EPISODE)
                messageQueue.put(message)
                
                if self.isHalted:
                    self.isHalted = False
                    break

        if (self.cloudBridge is not None):
            self.cloudBridge.submitTrainFinish()

        message = Model.Message(Model.Message.EVENT, Model.Message.TRAIN_FINISHED)
        messageQueue.put(message)
        self.isRunning = False
        print('learning done')

    def run_testing(self, messageQueue, total_episodes, max_steps, *model_args):
        total_episodes = int(total_episodes+0.5)
        max_steps = int(max_steps+0.5)
        self.isRunning = True

        if (self.cloudBridge is not None):
            self.cloudBridge.refresh()
            self.cloudBridge.setState("Testing")

        if not self.environment:
            self.environment = self.environment_class()

        if self.isLoaded:
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
            self.agent.memload(self.memload)
            self.isLoaded = False
        elif self.loadFilename:
            self.agent = self.agent_class(self.environment.state_size, self.environment.action_size, *model_args)
            self.agent.load(self.loadFilename)
            self.loadFilename = None
        elif not self.agent:
            return

        if self.agent:
            if (isinstance(self.agent, modelFreeAgent.ModelFreeAgent)):
                '''
                Testing algorithm for Model Free Agents.
                '''
                min_epsilon, max_epsilon, decay_rate = self.agent.min_epsilon, self.agent.max_epsilon, self.agent.decay_rate
                epsilon = max_epsilon

                for episode in range(int(total_episodes)):
                    self.environment.reset()

                    for step in range(int(max_steps)):
                        old_state = self.environment.state

                        exp_exp_tradeoff = random.uniform(0, 1)

                        if exp_exp_tradeoff > epsilon:
                            action = self.agent.choose_action(old_state)
                        else:
                            action = self.environment.sample_action()

                        reward = self.environment.step(action)

                        if isinstance(self.agent, drqn.DRQN):
                            self.agent.addToMemory(old_state, action, reward, self.environment.state, self.environment.done)
                            # self.agent.addToMemory(old_state, action, reward, self.environment.state, episode, self.environment.done)

                        if self.environment:
                            frame = self.environment.render()
                    
                        if (self.cloudBridge is not None):
                            self.cloudBridge.submitStep(frame, 0, reward, 0)
                        
                        # Send the state from the step.
                        modelState = Model.State(frame, None, reward, None, episode + 1, step + 1)
                        message = Model.Message(Model.Message.STATE, modelState)
                        messageQueue.put(message)

                        if self.environment.done or self.isHalted:
                            break

                    if (self.cloudBridge is not None):
                        self.cloudBridge.submitEpisode(episode, int(total_episodes))
                    
                    message = Model.Message(Model.Message.EVENT, Model.Message.EPISODE)
                    messageQueue.put(message)

                    epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay_rate * episode)

                    if self.isHalted:
                        self.isHalted = False
                        break
            elif (isinstance(self.agent, modelBasedAgent.ModelBasedAgent)):
                '''
                Testing algorithm for Model Based Agents.
                '''
                for episode in range(int(total_episodes)):
                    # Reset the environment.
                    self.environment.reset()

                    # Execute this episode.
                    for step in range(int(max_steps)):
                        # Execute one step.
                        old_state = self.environment.state
                        action = self.agent.choose_action(old_state)
                        reward = self.environment.step(action)
                        
                        # Render the step
                        if self.environment:
                            frame = self.environment.render()
                    
                        if (self.cloudBridge is not None):
                            self.cloudBridge.submitStep(frame, 0, reward, 0)
                        
                        modelState = Model.State(frame, None, reward, None, episode + 1, step + 1)
                        message = Model.Message(Model.Message.STATE, modelState)
                        messageQueue.put(message)

                        if self.environment.done or self.isHalted:
                            break

                    message = Model.Message(Model.Message.EVENT, Model.Message.EPISODE)
                    messageQueue.put(message)

                    if self.isHalted:
                        self.isHalted = False
                        break
                
                if (self.cloudBridge is not None):
                    self.cloudBridge.submitEpisode(episode, int(total_episodes))

            if (self.cloudBridge is not None):
                self.cloudBridge.submitTrainFinish()
            
            message = Model.Message(Model.Message.EVENT, Model.Message.TEST_FINISHED)
            messageQueue.put(message)
            print('testing done')
        self.isRunning = False

    def halt_learning(self):
        if self.isRunning:
            self.isHalted = True
            if (self.cloudBridge is not None):
                self.cloudBridge.setState("Halted")
                self.cloudBridge.terminate()

    def reset(self):
        self.environment = None
        self.agent = None
        self.memload = None

    def save(self, filename):
        if self.agent:
            self.agent.save(filename)

    def load(self, filename):
        self.loadFilename = filename

    class Message:
        # types of message
        STATE = 0
        EVENT = 1

        # event types
        TRAIN_FINISHED = 0
        TEST_FINISHED = 1
        EPISODE = 2

        def __init__(self, type, data):
            self.type = type
            self.data = data

    class State:
        def __init__(self, image, epsilon, reward, loss, episode, step):
            self.image = image
            self.epsilon = epsilon
            self.reward = reward
            self.loss = loss
            self.episode = episode
            self.step = step
