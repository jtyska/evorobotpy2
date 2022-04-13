#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
   This file belong to https://github.com/snolfi/evorobotpy
   and has been written by Stefano Nolfi and Paolo Pagliuca, stefano.nolfi@istc.cnr.it, paolo.pagliuca@istc.cnr.it

   evoalgo.py contains methods for showing, saving and loading data 

 """

import numpy as np
import time
import pandas as pd

class EvoAlgo(object):
    def __init__(self, env, policy, seed, fileini, filedir):
        self.env = env                       # the environment
        self.policy = policy                 # the policy
        self.seed = seed                     # the seed of the experiment
        self.fileini = fileini               # the name of the file with the hyperparameters
        self.filedir = filedir               # the directory used to save/load files
        self.bestfit = -999999999.0          # the fitness of the best agent so far
        self.bestsol = None                  # the genotype of the best agent so far
        self.bestgfit = -999999999.0         # the performance of the best post-evaluated agent so far
        self.bestgsol = None                 # the genotype of the best postevaluated agent so far
        self.stat = np.arange(0, dtype=np.float64) # a vector containing progress data across generations
        self.avgfit = 0.0                    # the average fitness of the population
        self.last_save_time = time.time()    # the last time in which data have been saved
        self.robustness_test = 1
        
    def reset(self):
        self.bestfit = -999999999.0
        self.bestsol = None
        self.bestgfit = -999999999.0
        self.bestgsol = None
        self.stat = np.arange(0, dtype=np.float64)
        self.avgfit = 0.0
        self.last_save_time = time.time()

    def run(self, nevals):
        # Run method depends on the algorithm
        raise NotImplementedError

    def test(self, testfile):  # postevaluate an agent 
        if (self.robustness_test != 1 and self.policy.test == 1 and "Bullet" in self.policy.environment):
            self.env.render(mode="human")    # Pybullet render require this initialization
        if testfile is not None:
            if self.filedir.endswith("/"):
                fname = self.filedir + testfile
            else:
                fname = self.filedir + "/" + testfile
            if (self.policy.normalize == 0):
                bestgeno = np.load(fname)
            else:
                geno = np.load(fname)
                for i in range(self.policy.ninputs * 2):
                    self.policy.normvector[i] = geno[self.policy.nparams + i]
                bestgeno = geno[0:self.policy.nparams]
                self.policy.nn.setNormalizationVectors()
            self.policy.set_trainable_flat(bestgeno)
        else:
            self.policy.reset()
        if self.robustness_test == 1:                
            corr_n_steps_list = list(range(1,11))
<<<<<<< Updated upstream
            noise_level_list = np.linspace(0.01,0.55,10)            
            n_trials_per_condition = 10
            
=======
            noise_level_list = np.linspace(0.01,0.55,10)
            n_trials_per_condition = 10                

>>>>>>> Stashed changes
            #corr_n_steps_list = [1,15]
            #noise_level_list = [0.3]
            #n_trials_per_condition = 10
            
            print(f'######## ENTERING ROBUSTNESS TEST - number of total trials = {len(corr_n_steps_list)*len(noise_level_list)*n_trials_per_condition} ###########')
            results = pd.DataFrame(columns=["corr_n_steps","noise_level","Trial","Reward","steps_taken"])
            
            self.policy.nttrials = n_trials_per_condition
            for corr_n_steps in corr_n_steps_list:
                self.policy.nn.setStepsCorrNoise(corr_n_steps)
                for noise_level in noise_level_list:                    
                    self.policy.nn.setActionNoise(noise_level)
                    local_rew = 0
                    local_eval_length = 0
                    for t in range(self.policy.nttrials):                                                                    
                        eval_rews, eval_length = self.policy.rollout(1, render=False, seed=(self.seed + 100000 + t))
                        local_rew += eval_rews
                        local_eval_length += eval_length                        
                        #appending the results
                        s_row = pd.Series([corr_n_steps,noise_level,t,eval_rews,eval_length], index=results.columns)
                        results = results.append(s_row,ignore_index=True)
                    print("Postevauation: noise_n_steps = %i; noise_level = %.2f; Average Fitness %.2f Total Steps %d" % (corr_n_steps, noise_level, local_rew/n_trials_per_condition, local_eval_length))
            results.to_csv("robustness_"+testfile+".csv")
        else:
            if (self.policy.nttrials > 0):
                ntrials = self.policy.nttrials
            else:
                ntrials = self.policy.ntrials
            eval_rews, eval_length = self.policy.rollout(ntrials, render=True, seed=self.policy.get_seed + 100000,dont_sleep=self.robustness_test)
            print("Postevauation: Average Fitness %.2f Total Steps %d" % (eval_rews, eval_length))

    def updateBest(self, fit, ind):  # checks whether this is the best agent so far and in case store it
        if fit > self.bestfit:
            self.bestfit = fit
            if (self.policy.normalize == 0):
                self.bestsol = np.copy(ind)
            else:
                self.bestsol = np.append(ind,self.policy.normvector)

    def updateBestg(self, fit, ind): # checks whether this is the best postevaluated agent so far and eventually store it
        if fit > self.bestgfit:
            self.bestgfit = fit
            if (self.policy.normalize == 0):
                self.bestgsol = np.copy(ind)
            else:
                self.bestgsol = np.append(ind,self.policy.normvector)
                       
    def save(self):                  # save the best agent so far, the best postevaluated agent so far, and the statistical data
            print('save data')
            fname = self.filedir + "/bestS" + str(self.seed)
            np.save(fname, self.bestsol)
            fname = self.filedir + "/bestgS" + str(self.seed)
            np.save(fname, self.bestgsol)             
            fname = self.filedir + "/statS" + str(self.seed)
            np.save(fname, self.stat)



