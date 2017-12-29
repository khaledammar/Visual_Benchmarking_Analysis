
import os
import glob
from datetime import datetime


BYTE_PER_GB = 1024*1024*1024.0

class Haloop(object):
    '''
    classdocs
    '''
    mainDirectory = ''

    def __init__(self, params):
        '''
        Constructor
        '''
        #print("HALOOP")
        Haloop.mainDirectory = params
                
    def listFiles(self):
        for myFile in os.listdir(Haloop.mainDirectory):
                print(myFile)
                
    def processTimeFile(self, fileName):
        '''
        Analyze the time file for hadoop/haloop 
        
        Return a tuple of [loadingTime, execution, saving, Total_time, sum(timing),timing,sum(shuffleBytes)/BYTE_PER_GB]
        '''
        os.chdir(Haloop.mainDirectory)
        fileName = glob.glob(fileName + '_time.txt')
        if len(fileName) == 0 :
            print("ERROR: time file was not found")
            return
        else:
            fileName = fileName[0]
    
        shuffleBytes = []
        
        startRead = []
        endRead = []
        ReadStarted = False
        finishTime = ''
        lastTime = ''
        startTime = []
        endTime = []
        runningTime = 0
        ended = True
        #print(fileName)
        for line in open(fileName).readlines():
            line = line[:-1]
            if "map 0%" in line:
                #print(line)
                startTime.append(line.split()[1])
                startRead.append(line.split()[1])
                ReadStarted = True
                if ended == False:
                    endTime.append(line.split()[1])
                else:
                    ended = False
                    
            elif "map 100%" in line:
                if ReadStarted:
                    endRead.append(line.split()[1])
                    ReadStarted=False
            elif "reduce 100%" in line:
                #print(line)
                endTime.append(line.split()[1])
                ended = True
            elif "Reduce shuffle bytes" in line:
                #print(line)
                shuffleBytes.append(int(line[line.find("Reduce shuffle bytes")+21:]))
            elif ("running time" in line and "attempt" not in line):
                #print(fileName)
                #print(line)
                runningTime = int(line.split()[2][:-1])
            elif "Map-Reduce Framework" in line:
                finishTime = line.split()[1]
                runningTime = (datetime.strptime(finishTime, '%H:%M:%S') - datetime.strptime(startTime[0], '%H:%M:%S')).seconds 
            elif "INFO mapred.JobClient" in line:
                lastTime = line.split()[1]
        
        #print(startTime)
        #print(endTime)
        
#        if finishTime =='':
#            finishTime=lastTime         
        
        if len(endTime) < len(startTime):
            print finishTime
            endTime.append(finishTime)
              
        print(startTime)
        print(endTime)
        
        timing = [(datetime.strptime(b, '%H:%M:%S') - datetime.strptime(a, '%H:%M:%S')).seconds for a,b in zip(startTime, endTime)]
        
        readTiming = [(datetime.strptime(b, '%H:%M:%S') - datetime.strptime(a, '%H:%M:%S')).seconds for a,b in zip(startRead, endRead)]
        
        #print("job timing = "+str(timing))
        #print("pure total running time ="+ str(sum(timing)))
        #print("total running time ="+ str(runningTime))
        #print("total shuffle bytes = "+ str(sum(shuffleBytes)/BYTE_PER_GB))
        
        # Haloop/Hadoop does not load or save data
        loadingTime = sum(readTiming)
        savingTime = 0
        shuffleBytes = [s/BYTE_PER_GB for s in shuffleBytes]
    #    if len(shuffleBytes)!=len(timing):
    #        print("ERROR: the number of iteration should be identical shuffling="+str(len(shuffleBytes)+", while timing="+str(len(timing))))        
        #runningTime could be zero if we interrupted the program. We still want to use the execution time
        if sum(timing) > runningTime and runningTime != 0:
            print("################################################################################")
            print("ERROR: running time("+str(sum(timing))+") cannot be more than total time ("+str(runningTime)+")")
            print(startTime)
            print(endTime)
            print(timing)
            

        finalResult = [loadingTime, sum(timing)-loadingTime, savingTime, runningTime ,timing, len(timing), sum(shuffleBytes), shuffleBytes] 
        print(fileName)   
        print('Start',startTime)
        print('End-Read',endRead)
        print('End-All',endTime)
        #print(timing)
        print('Execution=',sum(timing)-sum(readTiming),'\tLoading=',loadingTime,'\tOverhead=',runningTime - sum(timing))

        #print(finalResult)
        return finalResult



