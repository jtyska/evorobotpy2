#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
   This file belong to https://github.com/snolfi/evorobotpy
   and has been written by Stefano Nolfi and Paolo Pagliuca, stefano.nolfi@istc.cnr.it, paolo.pagliuca@istc.cnr.it
   salimans.py include an implementation of the OpenAI-ES algorithm described in
   Salimans T., Ho J., Chen X., Sidor S & Sutskever I. (2017). Evolution strategies as a scalable alternative to reinforcement learning. arXiv:1703.03864v2
   requires es.py, policy.py, and evoalgo.py 
"""

import numpy as np
from numpy import zeros, ones, dot, sqrt
import math
import time
from evoalgo import EvoAlgo
from utils import ascendent_sort
import sys
import os
import configparser
import pandas as pd

# Parallel implementation of Open-AI-ES algorithm developed by Salimans et al. (2017)
# the workers evaluate a fraction of the population in parallel
# the master post-evaluate the best sample of the last generation and eventually update the input normalization vector

class Algo(EvoAlgo):
    def __init__(self, env, policy, seed, fileini, filedir):
        EvoAlgo.__init__(self, env, policy, seed, fileini, filedir)
        self.ievReg = []
        self.cvReg = []

    def loadhyperparameters(self):

        if os.path.isfile(self.fileini):

            config = configparser.ConfigParser()
            config.read(self.fileini)
            self.maxsteps = 1000000
            self.stepsize = 0.01
            self.batchSize = 20
            self.noiseStdDev = 0.02
            self.wdecay = 0
            self.symseed = 1
            self.saveeach = 60
            self.percentual_env_var = 1
            self.fine_tuning_period = 0
            self.increase_env_var_each = 0
            self.increase_env_var_by = 0
            self.robustness_test = 0
            options = config.options("ALGO")
            for o in options:
                if o == "maxmsteps":
                    self.maxsteps = config.getint("ALGO","maxmsteps") * 1000000                    
                elif o == "stepsize":
                    self.stepsize = config.getfloat("ALGO","stepsize")                    
                elif o == "noisestddev":
                    self.noiseStdDev = config.getfloat("ALGO","noiseStdDev")                    
                elif o == "samplesize":
                    self.batchSize = config.getint("ALGO","sampleSize")                    
                elif o == "wdecay":
                    self.wdecay = config.getint("ALGO","wdecay")                    
                elif o == "symseed":
                    self.symseed = config.getint("ALGO","symseed")                    
                elif o == "saveeach":
                    self.saveeach = config.getint("ALGO","saveeach")
                elif o == "percentual_env_var":
                    self.percentual_env_var = config.getfloat("ALGO","percentual_env_var")
                elif o == "fine_tuning_period":
                    self.fine_tuning_period = config.getfloat("ALGO","fine_tuning_period")
                elif o == "increase_env_var_each":
                    self.increase_env_var_each = config.getfloat("ALGO","increase_env_var_each")
                elif o == "increase_env_var_by":
                    self.increase_env_var_by = config.getfloat("ALGO","increase_env_var_by")
                elif o == "robustness_test":
                    self.robustness_test = config.getint("ALGO","robustness_test")
                else:
                    print("\033[1mOption %s in section [ALGO] of %s file is unknown\033[0m" % (o, filename))
                    print("available hyperparameters are: ")
                    print("maxmsteps [integer]       : max number of (million) steps (default 1)")
                    print("stepsize [float]          : learning stepsize (default 0.01)")
                    print("samplesize [int]          : popsize/2 (default 20)")
                    print("noiseStdDev [float]       : samples noise (default 0.02)")
                    print("wdecay [0/2]              : weight decay (default 0), 1 = L1, 2 = L2")
                    print("symseed [0/1]             : same environmental seed to evaluate symmetrical samples [default 1]")
                    print("saveeach [integer]        : save file every N minutes (default 60)")

                    sys.exit()
        else:
            print("\033[1mERROR: configuration file %s does not exist\033[0m" % (self.fileini))
    


    def setProcess(self):
        self.loadhyperparameters()               # load hyperparameters
        self.center = np.copy(self.policy.get_trainable_flat())  # the initial centroid
        self.nparams = len(self.center)          # number of adaptive parameters
        self.cgen = 0                            # currrent generation
        self.samplefitness = zeros(self.batchSize * 2) # the fitness of the samples
        self.samplefitness2 = zeros(self.batchSize * 2) # the fitness of the samples during the re-test used to compute the iav measure
        self.samples = None                      # the random samples
        self.m = zeros(self.nparams)             # Adam: momentum vector 
        self.v = zeros(self.nparams)             # Adam: second momentum vector (adam)
        self.epsilon = 1e-08                     # Adam: To avoid numerical issues with division by zero...
        self.beta1 = 0.9                         # Adam: beta1
        self.beta2 = 0.999                       # Adam: beta2
        self.bestgfit = -99999999                # the best generalization fitness
        self.bfit = 0                            # the fitness of the best sample
        self.gfit = 0                            # the postevaluation fitness of the best sample of last generation
        self.rs = None                           # random number generator
        self.inormepisodes = self.batchSize * 2 * self.policy.ntrials / 100.0 # number of normalization episode for generation (1% of generation episodes)
        self.tnormepisodes = 0.0                 # total epsidoes in which normalization data should be collected so far
        self.normepisodes = 0                    # numer of episodes in which normalization data has been actually collected so far
        self.normalizationdatacollected = False  # whether we collected data for updating the normalization vector

    def savedata(self):
        self.save()             # save the best agent so far, the best postevaluated agent so far, and progress data across generations
        fname = self.filedir + "/S" + str(self.seed) + ".fit"
        fp = open(fname, "w")   # save summary
        fp.write('Seed %d (%.1f%%) gen %d msteps %d bestfit %.2f bestgfit %.2f bestsam %.2f avgfit %.2f paramsize %.2f \n' %
             (self.seed, self.steps / float(self.maxsteps) * 100, self.cgen, self.steps / 1000000, self.bestfit, self.bestgfit, self.bfit, self.avgfit, self.avecenter))
        fp.close()

 
    def evaluate(self):
        cseed = self.seed + self.cgen * self.batchSize  # Set the seed for current generation (master and workers have the same seed)
        self.rs = np.random.RandomState(cseed)
        self.samples = self.rs.randn(self.batchSize, self.nparams)
        self.cgen += 1

        # evaluate samples
        candidate = np.arange(self.nparams, dtype=np.float64)
        for b in range(self.batchSize):               
            for bb in range(2):
                if (bb == 0):
                    candidate = self.center + self.samples[b,:] * self.noiseStdDev
                else:
                    candidate = self.center - self.samples[b,:] * self.noiseStdDev
                self.policy.set_trainable_flat(candidate)
                self.policy.nn.normphase(0) # normalization data is collected during the post-evaluation of the best sample of he previous generation
                eval_rews, eval_length = self.policy.rollout(self.policy.ntrials, seed=(self.seed + (self.cgen * self.batchSize) + b))
                self.samplefitness[b*2+bb] = eval_rews
                self.steps += eval_length

                # we re-evaluate the individuals to estimate the iev measure
                if (((self.cgen - 1) % 1) == 0): #- changing for evaluating them at each generation
                    eval_rews, eval_length = self.policy.rollout(self.policy.ntrials, seed=(self.seed + (self.cgen * self.batchSize) + b + 999))  
                    self.samplefitness2[b*2+bb] = eval_rews

        fitness, self.index = ascendent_sort(self.samplefitness)       # sort the fitness
        self.avgfit = np.average(fitness)                         # compute the average fitness                   

        self.bfit = fitness[(self.batchSize * 2) - 1]
        bidx = self.index[(self.batchSize * 2) - 1]  

        if ((bidx % 2) == 0):                                     # regenerate the genotype of the best samples
            bestid = int(bidx / 2)
            self.bestsol = self.center + self.samples[bestid] * self.noiseStdDev  
        else:
            bestid = int(bidx / 2)
            self.bestsol = self.center - self.samples[bestid] * self.noiseStdDev
        
        self.updateBest(self.bfit, self.bestsol)                  # Stored if it is the best obtained so far 
                
        # postevaluate best sample of the last generation
        # in openaiesp.py this is done the next generation, move this section before the section "evaluate samples" to produce identical results
        gfit = 0
        if self.bestsol is not None:            
            self.policy.set_trainable_flat(self.bestsol)
            self.tnormepisodes += self.inormepisodes
            #post-evaluate on the standard environment variaton                
            currentRandInitLow = self.policy.env.robot.randInitLow
            currentRandInitHigh = self.policy.env.robot.randInitHigh
            self.policy.env.robot.randInitLow = self.defaultRandInitLow
            self.policy.env.robot.randInitHigh = self.defaultRandInitHigh
                        
            
                for t in range(self.policy.nttrials):
                    if self.policy.normalize == 1 and self.normepisodes < self.tnormepisodes:
                        self.policy.nn.normphase(1)
                        self.normepisodes += 1  # we collect normalization data
                        self.normalizationdatacollected = True
                    else:
                        self.policy.nn.normphase(0)
                    
                    
                    eval_rews, eval_length = self.policy.rollout(1, seed=(self.seed + 100000 + t))                
                    gfit += eval_rews               
                    self.steps += eval_length
            gfit /= self.policy.nttrials    
            self.updateBestg(gfit, self.bestsol)
        #reset the experimental environmental variation
        self.policy.env.robot.randInitLow = currentRandInitHigh
        self.policy.env.robot.randInitHigh = currentRandInitHigh
        # we compute the iev measure
        if (((self.cgen - 1) % 1) == 0):
           fitness2, index2 = ascendent_sort(self.samplefitness2)
           popsize = self.batchSize * 2
           utilities = zeros(popsize)
           utilities2 = zeros(popsize)
           for i in range(popsize):
              utilities[self.index[i]] = i
           utilities /= (popsize - 1)
           for i in range(popsize):
              utilities2[index2[i]] = i
           utilities2 /= (popsize - 1)
           iev = 0
           for i in range(popsize):
               iev += abs(utilities[i] - utilities2[i])
            
           print(f" =*=*=* GEN {self.cgen} - IEV = {iev/popsize} =*=*=*")
           self.ievReg.append(iev/popsize)
           
           #code for resetting the center when stagnation occurs - based on the IEV
           """gen = 250
           win = int(gen/10)
           if((self.cgen-1)!=0 and ((self.cgen-1)%gen)==0):
                print(f"{type(win)} - {win}")
                print(f"MOVING AVERAGE IEV = {np.mean(self.ievReg[-win:])} - {(self.cgen-1)} {((self.cgen-1)%gen)}")
                if np.mean(self.ievReg[-win:])>0.3 and self.bfit<1300:
                    print(f'Lenght ievReg={len(self.ievReg)} -2*winSize={-2*win} -win={-win}')                    
                    if(self.cgen<=2*gen or np.mean(self.ievReg[-2*win:-win])>0.30):
                        print(f'------> BAD IEV - last {np.mean(self.ievReg[-win:])} previous {np.mean(self.ievReg[-2*win:-win])}: restarting the center <------')
                        self.policy.nn.initWeights()
                        if (self.policy.normalize == 1):
                            self.policy.nn.resetNormalizationVectors() 
                        self.center = np.copy(self.policy.get_trainable_flat())
                        self.center = self.center[:self.nparams]
                    else:
                        print(f'NOT RESETING CENTER BECAUSE MOVING AVERAGE ABOVE THRESHOLD TWICE {np.mean(self.ievReg[-win:])} {np.mean(self.ievReg[-2*win:-win])} bfit {self.bfit}')
           else:
               print(f'MOVING AVERAGE IS OK last {0 if self.cgen<gen else np.mean(self.ievReg[-win:])} - NOT RESTARTING')"""


    def optimize(self):
            
        popsize = self.batchSize * 2                              # compute a vector of utilities [-0.5,0.5]
        utilities = zeros(popsize)
        for i in range(popsize):
            utilities[self.index[i]] = i
        utilities /= (popsize - 1)
        utilities -= 0.5
        
        weights = zeros(self.batchSize)                           # Assign the weights (utility) to samples on the basis of their fitness rank
        for i in range(self.batchSize):
            idx = 2 * i
            weights[i] = (utilities[idx] - utilities[idx + 1])    # merge the utility of symmetric samples

        g = 0.0
        i = 0
        while i < self.batchSize:                                 # Compute the gradient (the dot product of the samples for their utilities)
            gsize = -1
            if self.batchSize - i < 500:                          # if the popsize is larger than 500, compute the gradient for multiple sub-populations
                gsize = self.batchSize - i
            else:
                gsize = 500
            g += dot(weights[i:i + gsize], self.samples[i:i + gsize,:]) 
            i += gsize
        g /= popsize                                              # normalize the gradient for the popsize
        
        if self.wdecay == 1:
            globalg = -g + 0.005 * self.center                    # apply weight decay
        else:
            globalg = -g

        # adam stochastic optimizer
        a = self.stepsize * sqrt(1.0 - self.beta2 ** self.cgen) / (1.0 - self.beta1 ** self.cgen)
        self.m = self.beta1 * self.m + (1.0 - self.beta1) * globalg
        self.v = self.beta2 * self.v + (1.0 - self.beta2) * (globalg * globalg)
        dCenter = -a * self.m / (sqrt(self.v) + self.epsilon)
        
        self.center += dCenter                                    # move the center in the direction of the momentum vectors
        self.avecenter = np.average(np.absolute(self.center))      


    def run(self):

        self.setProcess()                           # initialize class variables
        start_time = time.time()
        last_save_time = start_time
        elapsed = 0
        self.steps = 0
        print("Salimans: seed %d maxmsteps %d batchSize %d stepsize %lf noiseStdDev %lf wdecay %d symseed %d nparams %d" % (self.seed, self.maxsteps / 1000000, self.batchSize, self.stepsize, self.noiseStdDev, self.wdecay, self.symseed, self.nparams))
        self.policy.nn.setMinParamNoise(-0.5)
        self.defaultRandInitLow = self.policy.env.robot.randInitLow
        self.defaultRandInitHigh = self.policy.env.robot.randInitHigh

        #applying the initial environmental variation        
        self.policy.env.robot.randInitLow = self.defaultRandInitLow*self.percentual_env_var
        self.policy.env.robot.randInitHigh = self.defaultRandInitHigh*self.percentual_env_var
        print(f"####USING {self.percentual_env_var*100} of the default environmental variation - actual range = [{self.policy.env.robot.randInitLow},{self.policy.env.robot.randInitHigh}]")

        #increasing the evolution duration for using a fine tuning period
        if self.fine_tuning_period != 0:
            self.defaultmaxsteps = self.maxsteps
            self.maxsteps = self.maxsteps*(1+self.fine_tuning_period)
            self.finetuningsteps = self.maxsteps - self.defaultmaxsteps
            fineTuningStarted = False

        while (self.steps < self.maxsteps):

            self.evaluate()                           # evaluate samples  
            
            self.optimize()                           # estimate the gradient and move the centroid in the gradient direction

            self.stat = np.append(self.stat, [self.steps, self.bestfit, self.bestgfit, self.bfit, self.avgfit, self.avecenter])  # store performance across generations
            
            completion = self.steps / float(self.maxsteps)*100;

            #the if below is used for the dynamic adjustment of the environmental variation - to be parameterized to facilitate the experiments
            if len(self.stat)>=30:
                lastFive = self.stat[-26:-1:6]
                meanLF = np.mean(lastFive)
                stdLF = np.std(lastFive)
                cv = stdLF/meanLF;
                averageZ = np.mean([(x-meanLF)/stdLF for x in lastFive])                                
                #print(f"Best generation fitness on last five generations={lastFive}")
                #print(f"Average = {meanLF}; Std = {stdLF}; CV={stdLF/meanLF}; averageZ={averageZ}")                 
                multiplier=1
                if (cv < 0.1): #too few variation - increasing it
                    multiplier=1.1
                elif (cv>0.2): #too much variation - reducing it
                    multiplier=0.9

                #if(completion<=70):
                #    self.policy.env.robot.randInitLow*=multiplier
                #    self.policy.env.robot.randInitHigh*=multiplier
                #else:
                #    self.policy.env.robot.randInitLow = defaultRandInitLow
                #    self.policy.env.robot.randInitHigh = defaultRandInitHigh                
                
                print(f"Fitness Cofficient of Variation (CV) = {cv} - Environmental variation = {self.policy.env.robot.randInitLow},{self.policy.env.robot.randInitHigh}")
                #if (((self.cgen - 1) % 10) == 0):
                self.cvReg.append(cv)

            if ((time.time() - last_save_time) > (self.saveeach * 60)):
                self.savedata()                       # save data on files
                last_save_time = time.time()

            if self.normalizationdatacollected:
                self.policy.nn.updateNormalizationVectors()  # update the normalization vectors with the new data collected
                self.normalizationdatacollected = False

            
            if completion>30 and completion<60:
                self.policy.nn.setMinParamNoise(-1)
            elif completion >=60:
                self.policy.nn.setMinParamNoise(-3)

            if self.steps>self.maxsteps/(1+self.fine_tuning_period):                                
                if not fineTuningStarted:
                   print("=========== Entering the fine tuning period (default env var)============")
                   fineTuningStarted = True
                   #start with 10% of variation
                   self.policy.env.robot.randInitLow = 0.01
                   self.policy.env.robot.randInitHigh = 0.01                   
                   changeEach = 0.1; #at 10%

                if (self.increase_env_var_each == 0 and self.increase_env_var_each==0):
                    self.policy.env.robot.randInitLow = self.defaultRandInitLow
                    self.policy.env.robot.randInitHigh = self.defaultRandInitHigh
                elif (self.steps - self.defaultmaxsteps)/self.finetuningsteps > changeEach:
                    changeEach += 0.1;
                    #increase 10% more 
                    self.policy.env.robot.randInitLow -= 0.01
                    self.policy.env.robot.randInitHigh += 0.01



            print('Seed %d (%.1f%%) gen %d msteps %d bestfit %.2f bestgfit %.2f bestsam %.2f avg %.2f weightsize %.2f minParamNoise %.2f' %
                      (self.seed, completion, self.cgen, self.steps / 1000000, self.bestfit, self.bestgfit, self.bfit, self.avgfit, self.avecenter,self.policy.nn.getMinParamNoise()))

        self.savedata()# save data at the end of evolution
        np.save(self.filedir + "/S" + str(self.seed) + ".iev",self.ievReg)
        np.save(self.filedir + "/S" + str(self.seed) + ".cv",self.cvReg)
        self.ievReg = []
        self.cvReg = []

        # print simulation time
        end_time = time.time()
        print('Simulation time: %dm%ds ' % (divmod(end_time - start_time, 60)))

