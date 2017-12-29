
import os
import glob
from datetime import datetime

BYTE_PER_GB = 1024*1024*1024.0

class GraphLabParsing(object):
    '''
    classdocs
    '''


    mainDirectory = ''

    def __init__(self, params):
        '''
        Constructor
        '''
        GraphLabParsing.mainDirectory = params

    def listFiles(self):
        for myFile in os.listdir(GraphLabParsing.mainDirectory):
                print(myFile)

    
    def processTimeFile(self, fileName):
        '''
        Analyze the time file for graphLab 
        
        Return a tuple of [loadingTime, savingTime, runningTime, sum(timing),timing,sum(shuffleBytes)/BYTE_PER_GB]
        '''
        os.chdir(GraphLabParsing.mainDirectory)
        fileName = glob.glob(fileName + '_time.txt')
        if len(fileName) == 0 :
            print("ERROR: time file was not found")
            return
        else:
            fileName = fileName[0]
    
        iterationTime = []
        loadingTime = []
        runningTime = 0
        totalTime = 0
        savingTime = 0
        cancelFile = 0
        finalizeTime = 0
        internalTotal = 0
        realLoding=0
        print(fileName)
        for line in open(fileName).readlines():
            line = line[:-1]
            if "totalTiming" in line:
                #print(line)
                totalTime=float(line.split()[1])
            elif "Finished Running engine" in line:
                #print(line)
                runningTime = float(line.split()[4])
            elif "Graph finalized in" in line:
                #print(line)
                #loadingTime.append(float(line.split()[5]))
                continue
            elif "Finalization in" in line:
                #loadingTime.append(float(line.split()[2]))
                continue
            elif ("BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES" in line) or ( "callback returned error status" in line):
                cancelFile = 1
            elif "loadingTime=" in line:
                loadingTime.append(float(line.split()[1]))
                realLoding=float(line.split()[1])
            elif "savingTime=" in line:
                savingTime = float(line.split()[1])
                print(savingTime)
            elif "executingTime=" in line:
                runningTime = float(line.split()[1])
            elif "finalizingTime=" in line:
                finalizeTime = float(line.split()[1])
            elif "internalTotal=" in line:
                internalTotal = float((line.split()[1]).split("INFO:")[0])
            elif "Timing for (loading , finalize, executing(all), all)" in line:
                loadingTime.append( float(line.split("=")[1].strip().split()[0])) 
                finalizeTime = float(line.split("=")[1].strip().split()[1])
                savingTime = float(line.split("=")[1].strip().split()[2]) - runningTime
                internalTotal = float(line.split("=")[1].strip().split()[3])
                
            
        if savingTime < 0:
            s = savingTime + internalTotal - realLoding - finalizeTime - runningTime
            if s < 0:
                print("======== review savingTime correctness==============")
                print(savingTime)
                print(internalTotal)
                print(realLoding)
                print(finalizeTime)
                print(runningTime)
                print(s)
                print("--------- done")
            else:
                savingTime=s
        
        if cancelFile == 1:
            print("\t file cancelled")
            return None
    
    
        #print(fileName)
        #print(loadingTime)
        print(fileName)
        loadingTime = max(loadingTime)
        

        # I know that iterationTime is an empty set
        finalResult = [loadingTime+finalizeTime, runningTime, savingTime, totalTime, iterationTime , loadingTime, internalTotal] 
        #print(finalResult)
        #print("testing")
        return finalResult
    
