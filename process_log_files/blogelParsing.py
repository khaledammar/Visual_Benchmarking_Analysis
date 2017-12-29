
import os
import glob
from datetime import datetime



class BlogelParsing(object):

    mainDirectory = ''

    def __init__(self, params):
        '''
        Constructor
        '''
        BlogelParsing.mainDirectory = params

    def listFiles(self):
        for myFile in os.listdir(BlogelParsing.mainDirectory):
                print(myFile)

    
    def processTimeFile(self, fileName):
        '''
        Analyze the time file for Blogel 
        
        Return a tuple of [loadingTime, savingTime, runningTime, sum(timing),some other metrics]
        '''
        os.chdir(BlogelParsing.mainDirectory)
        fileNames = glob.glob(fileName + '_time.txt*') 
        print(fileNames)
        
        if len(fileNames) == 0 :
            print("ERROR: time file was not found")
            return None
        
            
    
        communicationTime = []
        iterationTime = []
        loadingTime = []
        runningTime = []
        savingTime = []
        totalTime = 0
        #print("================ Blogel Time =========================")
        cancelFile = 0
        
        for f in fileNames:
            print(f)
            for line in open(f).readlines():
                line = line[:-1]
                if "Superstep" in line and "Round" not in line :
                    #print(fileName)
                    #print(line)
                    #print(line.split())
                    #print(line.split()[6])
                    iterationTime.append([int(line.split()[1]),float(line.split()[5])])
                elif "Total Computational Time" in line:
                    #print(line)
                    runningTime.append(float(line.split()[4]))
                elif "Load Time" in line:
                    #print(line)
                    loadingTime.append(float(line.split()[3]))
                elif "Communication Time" in line:
                    #print(line)
                    communicationTime.append(float(line.split()[3]))
                elif "Dump Time" in line:
                    #print(line)
                    savingTime.append(float(line.split()[3]))
                elif ("BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES" in line) or ( "callback returned error status" in line):
                    cancelFile = 1
                elif "totalTiming" in line:
                    #print(line)
                    totalTime=float(line.split()[1])

            if cancelFile == 1:
                print("\t file cancelled")
                return None


        if len(loadingTime) == 2:
            # Block Mode
            loadingTime = sum(loadingTime) + runningTime[0] + communicationTime[0]+ savingTime[0]
            savingTime = savingTime[1]
            communicationTime = communicationTime[1]
            runningTime = runningTime[1]
        elif len(loadingTime) == 1:
            # There is one entry any way
            runningTime = sum(runningTime)
            savingTime  = sum(savingTime)
            communicationTime = sum(communicationTime)
            loadingTime = sum(loadingTime)
        elif len(loadingTime) == 0:
            finalResult = [0, 0, 0, 0,[[1,0]],0]
            return finalResult
        else:
            print(loadingTime)
            print("ERROR: BLOGEL log file should have maximum two executions only")
            
        #totalTime = runningTime + loadingTime + savingTime + communicationTime
        finalResult = [loadingTime, runningTime, savingTime, totalTime,   
                       iterationTime, communicationTime] 
        #print("---------- Results :")
        #print(finalResult)
        return finalResult
    
    