
import os
import glob
from datetime import datetime
from numpy import double
from pip.locations import running_under_virtualenv


BYTE_PER_GB = 1024*1024*1024.0


class SparkParsing(object):
    '''
    classdocs
    '''
    mainDirectory = ''

    def __init__(self, params):
        SparkParsing.mainDirectory = params
        
        
    def listFiles(self):
        
        for myFile in os.listdir(SparkParsing.mainDirectory):
            pass
            #print(myFile)
            
    def processTimeFile(self, fileName):
        """Parses the spark time file for a single run.

        Returns: a tuple that includes  (loadingTime, savingTime, runningTime, execution time(as sum of iteration),iterations).
        """

        os.chdir(SparkParsing.mainDirectory)
        fileName = glob.glob(fileName + '_time.txt')
        if len(fileName) == 0 :
            print("ERROR: time file was not found")
            return
        else:
            fileName = fileName[0]
    
        shuffleBytes = []
        iterationTime = []
        runningTime = []
        savingTime = 0
        loadingTime = 0
        totalTime = 0
        cancelFile = 0
        print("============== SPARK =====================")
        print(fileName)
        for line in open(fileName).readlines():
            line = line[:-1]
            if ("SparkContext: Running Spark version" in line):
                #print("1 "+line)
                runningTime.append(line.split()[0]+" "+line.split()[1])
            elif ("Stopping DAGScheduler" in line):
                #print("2 "+line)
                runningTime.append(line.split()[0]+" "+line.split()[1])
            elif ("INFO GraphLoader: It took" in line):
                loadingTime = double(line.split()[6])/1000
                #print("3 "+line+" "+str(loadingTime))
            elif ("finished iteration" in line):
                #print("4 "+line)
                iterationTime.append(line.split()[0]+" "+line.split()[1])
            elif ("finished: saveAsTextFile" in line and "took" in line):
                savingTime = double(line.split()[11])
                #print("5 "+line+" "+str(savingTime))
            elif ("Starting job: count at GraphLoader.scala" in line or 
                  "SparkContext: Starting job" in line or
                  "Starting job: saveAsTextFile" in line or
                  "Job complete:" in line ):
                    pass
                #print("6 "+line)
            elif "Reduce shuffle bytes" in line:
                pass
                #print("7 "+line)
                #shuffleBytes.append(int(line[line.find("Reduce shuffle bytes")+21:]))
            elif "running time" in line:
                pass
                #print("8 "+line)
                #runningTime = int(line.split()[2][:-1])
            elif "totalTiming" in line:
                totalTime = float(line.split()[1])
            elif "killed intentionally" in line:
                cancelFile = 1    
        
        if cancelFile==1:
            return
        
        #print("Loading Time= "+str(loadingTime))
        #print("Saving Time= "+str(savingTime))
        #print(runningTime)

        if len(runningTime)==2:
            runningTime = (datetime.strptime(runningTime[1], '%y/%m/%d %H:%M:%S') - datetime.strptime(runningTime[0], '%y/%m/%d %H:%M:%S')).seconds        
        else:
            runningTime = 0
        
        #print("Running Time= "+str(runningTime))
        #print("iterationTime")
        
        #print(iterationTime)
        iterations = []
        for i in range(1 , len(iterationTime)):
            iterations.append((datetime.strptime(iterationTime[i], '%y/%m/%d %H:%M:%S') - datetime.strptime(iterationTime[i-1], '%y/%m/%d %H:%M:%S')).seconds)
        
        if totalTime == 0:
            totalTime = runningTime
        
        #print(iterations)
        finalResult = [loadingTime, sum(iterations), savingTime, totalTime, iterations] 
        #print(finalResult)
        return finalResult
        #print(endTime)
        #timing = [(datetime.strptime(b, '%H:%M:%S') - datetime.strptime(a, '%H:%M:%S')).seconds for a,b in zip(startTime, endTime)]
        