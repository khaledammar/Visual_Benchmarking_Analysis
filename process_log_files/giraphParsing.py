
import os
import glob
from datetime import datetime

BYTE_PER_GB = 1024*1024*1024.0

class giraphParsing(object):
    '''
    classdocs
    '''
    mainDirectory = ''

    def __init__(self, params):
        '''
        Constructor
        '''
        giraphParsing.mainDirectory = params

    def listFiles(self):
        for myFile in os.listdir(giraphParsing.mainDirectory):
                print(myFile)

    
    def processTimeFile(self, fileName):
        '''
        Analyze the time file for giraph 
        
        Return a tuple of [loadingTime, execution, saving, Total_time, sum(timing),timing,sum(shuffleBytes)/BYTE_PER_GB]
        '''
        os.chdir(giraphParsing.mainDirectory)
        fileName = glob.glob(fileName + '_time.txt')
        if len(fileName) == 0 :
            print("ERROR: time file was not found")
            return
        else:
            fileName = fileName[0]
    
        iterationTime = []
        loadingTime = 0
        runningTime = 0
        savingTime = 0
        initializeTime = 0
        shutdownTime = 0
        #print("######################  Giraph Timing  #####################")
        #print(fileName)
        for line in open(fileName).readlines():
            line = line[:-1]
            if "Superstep" in line and "Input" not in line and "(milliseconds)" in line:
                #print(fileName)
                #print(line)
                #print(line.split())
                #print(line.split()[6])
                iterationTime.append([int(line.split()[5]),float(line.split()[6].split("=")[1])/1000])
            elif "Setup (milliseconds)" in line:
                #print(line)
                initializeTime=float(line.split()[5].split("=")[1])/1000
            elif "Total (milliseconds)" in line:
                #print(line)
                runningTime = float(line.split()[5].split("=")[1])/1000
            elif "Input superstep" in line:
                loadingTime = float(line.split()[6].split("=")[1])/1000
            elif "Shutdown (milliseconds)" in line:
                shutdownTime = float(line.split()[5].split("=")[1])/1000
        
        
        #print("job timing = "+str(timing))
        #print("pure total running time ="+ str(sum(timing)))
        #print("total running time ="+ str(runningTime))


        #
        # I got this from a giraph group mail. The writer is also the developer of time stats. Note this talks about newer version.
        #
        #Initialize = the time spent by job waiting for resources. 
        #In a shared pool the job you launch may not get all the machines needed to start the job. 
        #So, for instance you want to run a job with 200 workers, giraph does not 
        #start until all the workers have are allocated & register with the master.
        
        #Setup = once you have all the machines allocated, how much time it takes before starting to read input

        #Shutdown = once you have written your output howmuch time it takes to 
        #stop verify that everything is done & shutdown resources & notify user. 
        #For instance wait for all network connections to close, all threads to join, etc.

        #Total = sum of input time + sum of time in all supersteps i.e., actual time taken to run by your 
        #application after it got all the resources (does not include time waiting to get resources which is initialize or shutdown time)
        
        #print(iterationTime)
#        print(zip(*iterationTime)[1])
#        print(iterationTime)
        totalIteration = 0
        if len(iterationTime) > 1 :
            savingTime = runningTime - sum(zip(*iterationTime)[1]) - initializeTime - loadingTime
            totalIteration = sum(zip(*iterationTime)[1])
            
        finalResult = [loadingTime, savingTime, runningTime, totalIteration, 
                       iterationTime, initializeTime, shutdownTime] 
        
        #print(finalResult)
        return finalResult


    def processTimeFile_1_1_0(self, fileName):
        '''
        Analyze the time file for giraph 
        
        Return a tuple of [loadingTime, savingTime, runningTime, sum(timing),timing,sum(shuffleBytes)/BYTE_PER_GB]
        '''
        os.chdir(giraphParsing.mainDirectory)
        fileName = glob.glob(fileName + '_time.txt')
        if len(fileName) == 0 :
            print("ERROR: time file was not found")
            return
        else:
            fileName = fileName[0]
    
        iterationTime = []
        loadingTime = 0
        runningTime = 0
        savingTime = 0
        initializeTime = 0
        shutdownTime = 0
        totalTime = 0
        #print("######################  Giraph Timing  #####################")
        #print(fileName)
        for line in open(fileName).readlines():
            line = line[:-1]
            if "Superstep" in line and "Input" not in line and ("(ms)" in line or "(milliseconds)" in line):
                #print(fileName)
                #print(line)
                #print(line.split())
                #print(line.split()[6])
                try:
                    iterationTime.append([int(line.split()[5]),float(line.split()[6].split("=")[1])/1000])
                except IndexError:
                    # in case the class name show up
                    iterationTime.append([int(line.split()[5]),float(line.split()[7].split("=")[1])/1000])
                
            elif "Setup (ms)" in line or "Setup (milliseconds)" in line :
                #print(line)
                initializeTime=float(line.split()[5].split("=")[1])/1000
            elif "Total (ms)" in line or "Total (milliseconds)" in line :
                #print(line)
                runningTime = float(line.split()[5].split("=")[1])/1000
            
            elif "Input superstep" in line:
                #print(line)
                loadingTime = float(line.split()[6].split("=")[1])/1000
            elif "Shutdown (ms)" in line or "Shutdown (milliseconds)" in line:
                shutdownTime = float(line.split()[5].split("=")[1])/1000
                #print(line)
            elif "totalTiming" in line:
                totalTime = float(line.split()[1])
                
        #print("job timing = "+str(timing))
        #print("pure total running time ="+ str(sum(timing)))
        #print("total running time ="+ str(runningTime))


        #
        # I got this from a giraph group mail. The writer is also the developer of time stats. Note this talks about newer version.
        #
        #Initialize = the time spent by job waiting for resources. 
        #In a shared pool the job you launch may not get all the machines needed to start the job. 
        #So, for instance you want to run a job with 200 workers, giraph does not 
        #start until all the workers have are allocated & register with the master.
        
        #Setup = once you have all the machines allocated, how much time it takes before starting to read input

        #Shutdown = once you have written your output howmuch time it takes to 
        #stop verify that everything is done & shutdown resources & notify user. 
        #For instance wait for all network connections to close, all threads to join, etc.

        #Total = sum of input time + sum of time in all supersteps i.e., actual time taken to run by your 
        #application after it got all the resources (does not include time waiting to get resources which is initialize or shutdown time)
        
        #print(iterationTime)
#        print(zip(*iterationTime)[1])
#        print(iterationTime)
        totalIteration = 0
        if len(iterationTime) > 1 :
            savingTime = runningTime - sum(zip(*iterationTime)[1]) - initializeTime - loadingTime
            totalIteration = sum(zip(*iterationTime)[1])
        
        if totalTime ==0:
           totalTime=runningTime
 
        finalResult = [loadingTime, totalIteration, savingTime, totalTime,  
                       iterationTime, initializeTime, shutdownTime] 
        
        #print(finalResult)
        return finalResult
