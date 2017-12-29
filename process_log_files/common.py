#!/usr/local/bin/python2.7

from __future__ import print_function
import sys
import os
import glob
import string
import matplotlib.pyplot as plt
import operator
import numpy as np
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from haloop import Haloop
from sparkParsing import SparkParsing
from giraphParsing import giraphParsing
from graphLabParsing import GraphLabParsing
from blogelParsing import BlogelParsing
from numpy import average
import math
from numpy import median

import scipy as sp
import scipy.stats



__all__ = []
__version__ = 0.1
__date__ = '2015-03-30'
__updated__ = '2015-03-30'

DEBUG = 0
TESTRUN = 0
PROFILE = 1

SummaryFile = "summary.txt"
ConsolidatedTimeFile = "consolidatedSummary-time.txt"
DisplayFiguresFile = "allFiles.tex"

# my Constants

BYTE_PER_GB = 1024*1024*1024.0
KB_PER_GB = 1024*1024.0
MS_PER_SEC = 1000.0

FIGURE_PREFIX = "~/benchmarking/figures/"

ignoredSystems = ('vertica')

SYSTEMS = ('giraph', 'haloop', 'spark', 'graphlab', 'blogel')
SYS_GIRAPH, SYS_HALOOP, SYS_SPARK, SYS_GRAPHLAB, SYS_BLOGEL = SYSTEMS

WORKLOAD = ('pagerank', 'wcc', 'sssp', 'khop')
PAGERANK, WCC, SSSP, KHOP = WORKLOAD

DATASET = ('twitter', 'uk0705')


load_color = "black, fill=gray"
execute_color = "black, fill= cyan, postaction={nomorepostaction,pattern=north east lines}"
save_color = "black, fill=red"
overhead_color = "black, fill=green, postaction={nomorepostaction,pattern=north west lines}"


def mem_parser(logFiles):
    if len(logFiles) == 0:
        return (0,0,0)
    
    else: 
        if len(logFiles) == 1 and logFiles[0].find('_0_mem.txt') > 0:
            pass
        else:
            pass

    def parse(log):
        mems = [float(line.split()[2]) for line in open(log).readlines()]
        return (max(mems) - min(mems))/KB_PER_GB
            
    mems = [parse(log) for log in logFiles]
    # A tuple (minimum mem, avg mem, maximum mem)
    return (min(mems), sum(mems)/len(mems), max(mems))

        




def cpu_parser(logFiles):
    if len(logFiles) == 0:
        return (0, 0, 0, 0, 0 , 0)
    
    else: 
        if len(logFiles) == 1 and logFiles[0].find('_0_cpu.txt') > 0:
            pass
        else:
            pass

    def parse(log):
        cpus = []
        lines = open(log).readlines()
        for line in lines:
            if string.find(line,"CPU") == -1 and len(line) > 23:
                line = line[23:] 
                cpus.append([float(n) for n in line.split()])
        
        cpus = zip(*cpus)
        return (max(cpus[0]), max(cpus[1]), max(cpus[2]), max(cpus[3]), max(cpus[4]), max(cpus[5]))
            
    cpus = [parse(log) for log in logFiles]
    cpus = zip(*cpus)
    # (max %user, max %nice, max %system, max %iowait, max %steal, max %idle )
    return (max(cpus[0]), max(cpus[1]), max(cpus[2]), max(cpus[3]), max(cpus[4]), max(cpus[5]))
        


    















def ctt_parser(logFiles):

    if len(logFiles) == 0:
        return [0, 0, 0, 0, 0]
    

    def parse(log):
        cpus = []
        lines = open(log).readlines()
        if len(lines) == 1:
            cpus =[(0, 0, 0, 0, 0)]
        
        for line in lines:
                cpus.append([float(n) for n in line[5:].split()])
        
        
        cpus = zip(*cpus)
        diffCPU = [max(cpus[0])-min(cpus[0]), max(cpus[1])-min(cpus[1]), max(cpus[2])-min(cpus[2]), max(cpus[4])-min(cpus[4]), max(cpus[3])-min(cpus[3])]
        return(diffCPU)
    


    if len(logFiles) == 2 and (logFiles[0].find('_0_ctt.txt') > 0 or logFiles[0].find('__ctt.txt') > 0):
        cpus = [parse(log) for log in logFiles]
        before = cpus[0]
        after = cpus[1]
        cpus = [abs(x-y) for x,y in zip(after,before)]
        
    else:
        cpus = [parse(log) for log in logFiles]
        cpus = zip(*cpus)
    
    cpus=[(average(cpus[0]), average(cpus[1]), average(cpus[2]), average(cpus[3]), average(cpus[4]))]
    cpus = cpus[0]
    cpus = [(c*100)/sum(cpus) for c in cpus]
    #(avg %user, avg %nice, avg %system, avg %iowait, avg %idle )
    return (cpus)


def net_parser(logFiles):
    def parse(log):
        recv = 0
        sent = 0

        for line in open(log).readlines():
            if "eth0" in line:
                recv = float(line.split()[1]) - recv
                sent = float(line.split()[9]) - sent
        return (recv/BYTE_PER_GB, sent/BYTE_PER_GB)


    if len(logFiles) == 0:
        return (0,0)
    
    else: 
        # master has two files _0_nbt.txt and __nbt.txt
        if len(logFiles) == 2 and (logFiles[0].find('_0_nbt.txt') > 0 or logFiles[0].find('__nbt.txt') > 0):
            #print("master machine = "+str(len(logFiles)))
            eth = [parse(log) for log in logFiles]
            eth = zip(*eth)
            return(abs(eth[0][0]-eth[0][1]), abs(eth[0][0]-eth[0][1]))
        else:
            eth = [parse(log) for log in logFiles]
            eth = zip(*eth)
            return (sum(eth[0]), sum(eth[1]))




def printLogFileName(logName):
    return logName.replace(".txt","").replace("-edge","").replace("-long","").replace("-block","").replace("-adj","").replace("_"," ").replace("world road", "world-road")

def getSystemName(inPath, prefix):
    systemName = inPath.split("/").pop()
    if systemName=="spark":
        if printLogFileName(prefix).split()[3]=="0":
            return "spark-itr"
        else:
            return "spark-tol"
    elif systemName=="giraph":
        if printLogFileName(prefix).split()[3]=="0":
            return "giraph"
        else:
            return "giraph-HashMap"
    elif systemName=="blogel":
        if printLogFileName(prefix).split()[3]=="0":
            return "blogel-Vertex"
        else:
            return "blogel-Block"
    elif systemName=="haloop":
        print (printLogFileName(prefix))
        if printLogFileName(prefix).split()[3]=="0":
            if "ADJ" in printLogFileName(prefix).split()[4]:
                return "haloop-ADJ"
            else:
                return "haloop"
        else:
            if "ADJ" in printLogFileName(prefix).split()[4]:
                return "hadoop-ADJ"
            else:
                return "hadoop"
    elif systemName=="graphlab": # this is for GraphLab
        initial= systemName+"-"+printLogFileName(prefix).split()[3]+"-"+printLogFileName(prefix).split()[4]
        if printLogFileName(prefix).split()[0]==PAGERANK:
            if float(printLogFileName(prefix).split()[5]) > 1:
                if 'async' in initial:
                    initial = string.replace(initial, 'async', 'sync')
                return initial+"-itr"
            else:
                return initial+"-tol"
        else:
            return initial
    
    else:
        print("ERROR: Unrecognized system name ---",systemName)
        return 'ERROR'
    pass



# I got this from stackOverFlow
def get_confidence_interval(data, confidence=0.95):
    
    a = 1.0*np.array(list(data))
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t._ppf((1+confidence)/2., n-1)
    
    conf_int = scipy.stats.norm.interval(confidence, loc=m, scale=se / np.sqrt(n))
    h = conf_int[1] - m
    return h


def mergeConsolidatedFiles(originalPath):
    
    allPaths =  getPaths(originalPath)
    
    os.chdir(originalPath)
    mergedFile = open(SummaryFile, 'w')
     
    for p in allPaths:
        consolidatedFile = p+"/"+ConsolidatedTimeFile
        print(consolidatedFile)
        for line in open(consolidatedFile).readlines():
           print(line, file=mergedFile)
        
    return

def getTotalFromConsolidateTime(line):
    return str(float(line.split(", ")[5].translate(None, "[]'"))+
               float(line.split(", ")[6].translate(None, "[]'"))+
               float(line.split(", ")[7].translate(None, "[]'"))+
               float(line.split(", ")[8].translate(None, "[]'")))




def makeTekziLineDatasetSystem(originalPath, dataset , system):


   
    fileName = "TekziLineDatasetWorkload-"+dataset+"-"+system
    os.chdir(originalPath)
    
    allFigures = open(DisplayFiguresFile, 'a')
    #print("% adding all figures", file=allFigures)
    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" + dataset+"-"+system  + "}", file=allFigures)
    print("\\end{figure}", file=allFigures)
    
    allFigures.close()

    fileName = open(fileName+".tex", 'w')
    
    print("\\begin{tikzpicture}",file=fileName)
    print("\\begin{axis}[legend style={at={(0.5,-0.2)},anchor=north},",file=fileName)
    print("    xmin=0, ymin=0, xtick={0,16,32,64,120},",file=fileName)
    print("    log ticks with fixed point,",file=fileName)
    print("     xlabel={Cluster Size},",file=fileName)
    print("     ylabel={Time ($sec$)}",file=fileName)
    print("]",file=fileName)


    workloadNames = []
    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if system in l
        and dataset in l]

    # these might be needed if the process is very slow
    #graphlabSubset = [l for l in subset if "graphlab" in l]
    #giraphSubset = [l for l in subset if "giraph" in l]
    #blogelSubset = [l for l in subset if "blogel" in l]
    #graphxSubset = [l for l in subset if "spark" in l]
    myWorkloads = list(set([r.split(", ")[3].translate(None, "[]'") for r in subset]))

    fail= "F"
    
    for s in myWorkloads:
        value_16 = fail
        value_32 = fail
        value_64 = fail
        value_128= fail
        workloadNames.append(s)
        for line in subset:
            if s in line and line.split(", ")[1].translate(None, "[]'") == "16":
               value_16 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "32":
               value_32 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "64":
               value_64 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "128":
               value_128 = getTotalFromConsolidateTime(line)

        print("\\addplot table{", file=fileName)
        if value_16 != fail:
            print("   16 " +value_16   ,  file=fileName)

        if value_32 != fail:
            print("   32 " +value_32   ,  file=fileName)

        if value_64 != fail:
            print("   64 " +value_64   ,  file=fileName)
        
        if value_128 != fail: 
            print("   128 "+value_128  ,  file=fileName)

        print("};"  ,  file=fileName)

    # legends
    print("\\legend{"+", ".join(workloadNames) +"}",file=fileName)
    print("\\legend{"+", ".join(workloadNames) +"}")
    # closing
    print("\\end{axis}",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)
    return                                      



def makeTekziLineDatasetWorkload(originalPath, dataset , workload):

    fileName = "TekziLineDatasetWorkload-"+dataset+"-"+workload

    print("Preparing figure file in: ",originalPath)
    print("Figure file: ", fileName)
    
    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')

    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" + dataset+" - "+workload + "}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()

    fileName = open(fileName+".tex", 'w')



    print("\\begin{tikzpicture}",file=fileName)
    print("\\begin{axis}[legend style={at={(0.5,-0.2)},anchor=north},",file=fileName)
    print("    xmin=0, ymin=0, xtick={0,16,32,64,120},",file=fileName)
    print("    log ticks with fixed point,",file=fileName)
    print("     xlabel={Cluster Size},",file=fileName)
    print("     ylabel={Time ($sec$)}",file=fileName)
    print("]",file=fileName)



    systemNames = []


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]


    mySystems = list(set([r.split(", ")[0].translate(None, "[]'") for r in subset]))


    fail = "F"
    for s in mySystems:
        value_16 = fail
        value_32 = fail
        value_64 = fail
        value_128= fail
        systemNames.append(s)
        for line in subset:
            if s in line and line.split(", ")[1].translate(None, "[]'") == "16":
               value_16 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "32":
               value_32 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "64":
               value_64 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "128":
               value_128 = getTotalFromConsolidateTime(line)


        print("\\addplot table{", file=fileName)
        if value_16 != fail:
            print("   16 " +value_16   ,  file=fileName)

        if value_32 != fail:
            print("   32 " +value_32   ,  file=fileName)

        if value_64 != fail:
            print("   64 " +value_64   ,  file=fileName)

        if value_128 != fail:
            print("   128 "+value_128  ,  file=fileName)
        print("};"  ,  file=fileName)


    # legends
    # \legend{GraphLab,Giraph, Blogel-V, GraphX}
    print("\\legend{"+", ".join(systemNames) +"}",file=fileName)
    print("\\legend{"+", ".join(systemNames) +"}")

    # closing
    print("\\end{axis}",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)


    return


def getUnique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]



def getStackedNumbers(mySystems, subset):

    myResults = []
    for i in range(0,len(mySystems)):
	myResults.append([0,0,0,0])    


    for line in subset:
        systemName = line.split(", ")[0].translate(None, "[]'")
        systemName = translateSystemName4Tikzi(systemName)
        if systemName not in mySystems:
            continue
        combinedResults = line.split(", [")[1].translate(None, "[]'").split(", ")
        #print(line)
        #print(combinedResults)
        (value_read,value_exec,value_save,value_misc) = combinedResults
        myResults[mySystems.index(systemName)] =[value_read,value_exec,value_save,value_misc]


    myResults = zip (*myResults)

    return myResults






def getMaxStackedNumber(subset):

    maximum = 0.0
    for line in subset:
        combinedResults = line.split(", [")[1].translate(None, "[]'").split(", ")
	combinedResults = [float(l) for l in combinedResults]
        if maximum < sum(combinedResults):
           maximum = sum(combinedResults)

    
    maximum = int(math.ceil(maximum / 100.0)) * 100
    return maximum


def getReasonableMaxStackedNumber(subset):

    maximum = 0.0
    medianValue = 0.0
    sum_all = []
    for line in subset:
        combinedResults = line.split(", [")[1].translate(None, "[]'").split(", ")
        combinedResults = [float(l) for l in combinedResults]
        sum_all.append(sum(combinedResults))
     
    
    sum_all = getUnique(sum_all)
    sum_all = sorted(sum_all)
    
    maximum = sum_all[-1]
    medianValue = median(sum_all)
    
    if maximum > medianValue*4:
        maximum = medianValue*4
        #print(sum_all)
        #maximum = sum_all[-3]
        #print(maximum)
        
    maximum = int(math.ceil(maximum / 100.0)) * 100
    return maximum





def translateSystemName4Tikzi(systemName):

    if systemName == "blogel-Vertex":
        systemName = "BV"
    elif systemName == "blogel-Block":
        systemName = "BB"
    elif systemName == "giraph":
	systemName = "G"
    elif "graphlab" in systemName:
	tmpName = "GL"
    
        if "async" in systemName:
	      tmpName = tmpName +"-A"
	else:
              tmpName = tmpName +"-S"

	if "auto" in systemName:
	      tmpName = tmpName +"-A"
	else:
              tmpName = tmpName +"-R"

	if "tol" in systemName:
	      tmpName = tmpName +"-T"
	else:
              tmpName = tmpName +"-I"
        systemName = tmpName
                 
    elif "spark" in systemName:
	systemName = "S"
    elif "hadoop" in systemName:
        systemName = "HD"
    elif "haloop" in systemName:
        systemName = "HL"
	
    return systemName










def makeTekziGroupStackDataset(originalPath, dataset):

    fileName = "TekziStackGroupDataset-"+dataset

    print("Directory: ",originalPath)
    print("File: ",fileName+".tex")
    
    

    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')

    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" +dataset + "}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()

    fileName = open(fileName+".tex", 'w')




    print("\\makeatletter",file=fileName)
    print("\\pgfplotsset{",file=fileName)
    print("	groupplot xlabel/.initial={}, every tick label/.append style={font=\tiny},",file=fileName)
    print("	every groupplot x label/.style={",file=fileName)
    print("		at={($({group c1r\\pgfplots@group@rows.west}|-{group c1r\\pgfplots@group@rows.outer south})!0.5!({group c\\pgfplots@group@columns r\\pgfplots@group@rows.east}|-{group c\\pgfplots@group@columns r\\pgfplots@group@rows.outer south})$)},",file=fileName)
    print("		anchor=north,",file=fileName)
    print("	},",file=fileName)
    print("	groupplot ylabel/.initial={},",file=fileName)
    print("	every groupplot y label/.style={",file=fileName)
    print("		rotate=90,",file=fileName)
    print("		at={($({group c1r1.north}-|{group c1r1.outer",file=fileName)
    print("				west})!0.5!({group c1r\\pgfplots@group@rows.south}-|{group c1r\\pgfplots@group@rows.outer west})$)},",file=fileName)
    print("		anchor=south",file=fileName)
    print("	},",file=fileName)
    print("	execute at end groupplot/.code={%",file=fileName)
    print("		\\node [/pgfplots/every groupplot x label]",file=fileName)
    print("		{\\pgfkeysvalueof{/pgfplots/groupplot xlabel}};  ",file=fileName)
    print("		\\node [/pgfplots/every groupplot y label] ",file=fileName)
    print("		{\\pgfkeysvalueof{/pgfplots/groupplot ylabel}};",file=fileName)  
    print("	},",file=fileName)
    print("	group/only outer labels/.style =",file=fileName)
    print("	{",file=fileName)
    print("		group/every plot/.code = {%",file=fileName)
    print("			\\ifnum\\pgfplots@group@current@row=\\pgfplots@group@rows\\else%",file=fileName)
    print("			\\pgfkeys{xticklabels = {}, xlabel = {}}\\fi%",file=fileName)
    print("			\\ifnum\\pgfplots@group@current@column=1\\else%",file=fileName)
    print("			\\pgfkeys{yticklabels = {}, ylabel = {}}\\fi%",file=fileName)
    print("		}",file=fileName)
    print("	}",file=fileName)
    print("}",file=fileName)

    print("\\def\\endpgfplots@environment@groupplot{%",file=fileName)
    print("	\\endpgfplots@environment@opt%",file=fileName)
    print("	\\pgfkeys{/pgfplots/execute at end groupplot}%",file=fileName)
    print("	\\endgroup%",file=fileName)
    print("}",file=fileName)
    print("\\tikzset{nomorepostaction/.code=\\let\\tikz@postactions\\pgfutil@empty}",file=fileName)
    print("\\makeatother",file=fileName)

    print("\\begin{tikzpicture}",file=fileName)

    print("\\pgfplotsset{%",file=fileName)
    print("     tiny,samples=10,",file=fileName)
    print("	width=3cm,",file=fileName)
    print("	height=2cm,",file=fileName)
    print("	scale only axis,",file=fileName)
    print("%	xmajorgrids,",file=fileName)
    print("%	xminorgrids,",file=fileName)
    print("	ymajorgrids,",file=fileName)
    print("	yminorgrids",file=fileName)
    print("}",file=fileName)


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if dataset in l and WCC in l]

    mySystems = []
    for line in subset:
        systemName = line.split(", ")[0].translate(None, "[]'")
        systemName = translateSystemName4Tikzi(systemName)
        if systemName not in ignoredSystems:
            mySystems.append(systemName)

        
    mySystems = getUnique(mySystems)
    mySystems = sorted(mySystems)


   

    print("%\\pgfplotsset{tiny,samples=10}",file=fileName)
    print("   \\begin{groupplot}[",file=fileName)
    print("         group style = {group size = 4 by 3, ",file=fileName)
    print("         	horizontal sep = 5pt,",file=fileName)
    print("         	vertical sep = 5pt}, ",file=fileName)
    print("         groupplot ylabel={Time ($sec$)},",file=fileName)
    print("         groupplot xlabel={Systems},",file=fileName)
    print("         group/only outer labels, ",file=fileName)
    print("         ybar stacked, /pgf/bar width=1, /pgf/bar shift=0pt,",file=fileName)
    print("         area legend,  ymin=0,    xtick=data,xticklabels={"+str(mySystems).translate(None, "[]'()")+"},",file=fileName)
    print("         scaled ticks=false, xtick style={draw=none},  x tick label style={rotate=45,anchor=east}",file=fileName)
    print("]",file=fileName)


    
 
    #all workloads: PAGERANK, WCC, SSSP, KHOP
    workload = KHOP
    # Twitter
    #dataset = "world-road"    
   

    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    
    TwitterMax = getReasonableMaxStackedNumber(subset)
    #TwitterMax = getMaxStackedNumber(subset)    

    print("      \\nextgroupplot[ title = {16 machines}, ",file=fileName)
    print("      legend style = { column sep = 10pt, legend columns = 4, legend to name = grouplegend,}, ymax="+str(TwitterMax)+", ylabel={"+workload+"}] ",file=fileName)




	


    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)


    
    print(myResults[0])
    #myResults=sorted(myResults, key=operator.itemgetter(0))
    #print(myResults)

    #print(myResults)
    #myResults = zip (*myResults)
    #print(myResults)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Load}"  ,  file=fileName)
           

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Execute}"  ,  file=fileName)


    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Save}"  ,  file=fileName)



    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Overhead}"  ,  file=fileName)








    print("      \\nextgroupplot[ title = {32 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[ title = {64 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[ title = {128 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)















    #all workloads: PAGERANK, WCC, SSSP, KHOP
    workload = WCC
    #dataset = "uk0705"    

    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    UKMax = getReasonableMaxStackedNumber(subset)    



    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+", ylabel={"+workload+"}] ",file=fileName)


    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)






    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)




















    #all workloads: PAGERANK, WCC, SSSP, KHOP
    workload = SSSP
    #dataset = "twitter"    


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    WorldMax = getReasonableMaxStackedNumber(subset)    




    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(WorldMax)+", ylabel={"+workload+"}] ",file=fileName)



    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)






    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)


    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)



    print("\\makeatletter",file=fileName)
    print("\\end{groupplot}",file=fileName)
    print("\\node at ($(group c2r1) + (0,2.1cm)$) {\\ref{grouplegend}};",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)


    return








    

















def makeTekziGroupStack(originalPath, workload):


    fileName = "TekziStackGroupWorkload-"+workload

    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')

    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" +workload + "}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()

    fileName = open(fileName+".tex", 'w')




    print("\\makeatletter",file=fileName)
    print("\\pgfplotsset{",file=fileName)
    print("	groupplot xlabel/.initial={}, every tick label/.append style={font=\tiny},",file=fileName)
    print("	every groupplot x label/.style={",file=fileName)
    print("		at={($({group c1r\\pgfplots@group@rows.west}|-{group c1r\\pgfplots@group@rows.outer south})!0.5!({group c\\pgfplots@group@columns r\\pgfplots@group@rows.east}|-{group c\\pgfplots@group@columns r\\pgfplots@group@rows.outer south})$)},",file=fileName)
    print("		anchor=north,",file=fileName)
    print("	},",file=fileName)
    print("	groupplot ylabel/.initial={},",file=fileName)
    print("	every groupplot y label/.style={",file=fileName)
    print("		rotate=90,",file=fileName)
    print("		at={($({group c1r1.north}-|{group c1r1.outer",file=fileName)
    print("				west})!0.5!({group c1r\\pgfplots@group@rows.south}-|{group c1r\\pgfplots@group@rows.outer west})$)},",file=fileName)
    print("		anchor=south",file=fileName)
    print("	},",file=fileName)
    print("	execute at end groupplot/.code={%",file=fileName)
    print("		\\node [/pgfplots/every groupplot x label]",file=fileName)
    print("		{\\pgfkeysvalueof{/pgfplots/groupplot xlabel}};  ",file=fileName)
    print("		\\node [/pgfplots/every groupplot y label] ",file=fileName)
    print("		{\\pgfkeysvalueof{/pgfplots/groupplot ylabel}};",file=fileName)  
    print("	},",file=fileName)
    print("	group/only outer labels/.style =",file=fileName)
    print("	{",file=fileName)
    print("		group/every plot/.code = {%",file=fileName)
    print("			\\ifnum\\pgfplots@group@current@row=\\pgfplots@group@rows\\else%",file=fileName)
    print("			\\pgfkeys{xticklabels = {}, xlabel = {}}\\fi%",file=fileName)
    print("			\\ifnum\\pgfplots@group@current@column=1\\else%",file=fileName)
    print("			\\pgfkeys{yticklabels = {}, ylabel = {}}\\fi%",file=fileName)
    print("		}",file=fileName)
    print("	}",file=fileName)
    print("}",file=fileName)

    print("\\def\\endpgfplots@environment@groupplot{%",file=fileName)
    print("	\\endpgfplots@environment@opt%",file=fileName)
    print("	\\pgfkeys{/pgfplots/execute at end groupplot}%",file=fileName)
    print("	\\endgroup%",file=fileName)
    print("}",file=fileName)
    print("\\tikzset{nomorepostaction/.code=\\let\\tikz@postactions\\pgfutil@empty}",file=fileName)
    print("\\makeatother",file=fileName)

    print("\\begin{tikzpicture}",file=fileName)

    print("\\pgfplotsset{%",file=fileName)
    print("     tiny,samples=10,",file=fileName)
    print("	width=3cm,",file=fileName)
    print("	height=2cm,",file=fileName)
    print("	scale only axis,",file=fileName)
    print("%	xmajorgrids,",file=fileName)
    print("%	xminorgrids,",file=fileName)
    print("	ymajorgrids,",file=fileName)
    print("	yminorgrids",file=fileName)
    print("}",file=fileName)


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l]

    mySystems = []
    for line in subset:
        systemName = line.split(", ")[0].translate(None, "[]'")
        systemName = translateSystemName4Tikzi(systemName)
        if systemName not in ignoredSystems:
            mySystems.append(systemName)

    mySystems = getUnique(mySystems)
    mySystems = sorted(mySystems)


   

    print("%\\pgfplotsset{tiny,samples=10}",file=fileName)
    print("   \\begin{groupplot}[",file=fileName)
    print("         group style = {group size = 4 by 3, ",file=fileName)
    print("         	horizontal sep = 5pt,",file=fileName)
    print("         	vertical sep = 5pt}, ",file=fileName)
    print("         groupplot ylabel={Time ($sec$)},",file=fileName)
    print("         groupplot xlabel={Systems},",file=fileName)
    print("         group/only outer labels, ",file=fileName)
    print("         ybar stacked, /pgf/bar width=1, /pgf/bar shift=0pt,",file=fileName)
    print("         area legend,  ymin=0,    xtick=data,xticklabels={"+str(mySystems).translate(None, "[]'()")+"},",file=fileName)
    print("         scaled ticks=false, xtick style={draw=none},  x tick label style={rotate=45,anchor=east}",file=fileName)
    print("]",file=fileName)




    # Twitter
    dataset = "world-road"    


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    TwitterMax = getReasonableMaxStackedNumber(subset)    

    print("      \\nextgroupplot[ title = {16 machines}, ",file=fileName)
    print("      legend style = { column sep = 10pt, legend columns = 4, legend to name = grouplegend,}, ymax="+str(TwitterMax)+", ylabel={World RN}] ",file=fileName)




	


    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)


    
    #print(myResults)
    #myResults=sorted(myResults, key=operator.itemgetter(0))
    #print(myResults)

    #print(myResults)
    #myResults = zip (*myResults)
    #print(myResults)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Load}"  ,  file=fileName)
           

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Execute}"  ,  file=fileName)


    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Save}"  ,  file=fileName)



    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
    print("\\addlegendentry{Overhead}"  ,  file=fileName)








    print("      \\nextgroupplot[ title = {32 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[ title = {64 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[ title = {128 machines}, ",file=fileName)
    print("      ymax="+str(TwitterMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
















    dataset = "uk0705"    

    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    UKMax = getReasonableMaxStackedNumber(subset)    



    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+", ylabel={UK0705}] ",file=fileName)


    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)






    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(UKMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)




















    dataset = "twitter"    


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    WorldMax = getReasonableMaxStackedNumber(subset)    




    print("      \\nextgroupplot[ ",file=fileName)
    print("      ymax="+str(WorldMax)+", ylabel={Twitter}] ",file=fileName)



    clusterSize = 16


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)






    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)



    clusterSize = 32


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)







    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)


    clusterSize = 64


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)

    
    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)








    print("      \\nextgroupplot[  ",file=fileName)
    print("      ymax="+str(WorldMax)+"] ",file=fileName)




    clusterSize = 128


    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    myResults = getStackedNumbers(mySystems, subset)


    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[0]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+str(v)+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)



    print("\\makeatletter",file=fileName)
    print("\\end{groupplot}",file=fileName)
    print("\\node at ($(group c2r1) + (0,2.1cm)$) {\\ref{grouplegend}};",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)


    return












 

def makeTekziGroup(originalPath, workload):


    fileName = "TekziLineGroupWorkload-"+workload

    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')

    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" +workload + "}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()

    fileName = open(fileName+".tex", 'w')


 #   \pgfplotsset{tiny,samples=10}
 #   \begin{groupplot}[group style = {group size = 3 by 1, horizontal sep = 50pt}, width = 6.0cm, height = 5.0cm]
 #       \nextgroupplot[ title = {$k=1$},
 #           legend style = { column sep = 10pt, legend columns = -1, legend to name = grouplegend,}]
 #           \addplot {x};   \addlegendentry{$(x+0)^k$}%
 #           \addplot {x+1}; \addlegendentry{$(x+1)^k$}
 #           \addplot {x+2}; \addlegendentry{$(x+2)^k$}
 #           \addplot {x+3}; \addlegendentry{$(x+3)^k$}
 #       \nextgroupplot[title = {$k=2$},]
 #           \addplot {x^2};
 #           \addplot {(x+1)^2};
 #           \addplot {(x+2)^2};
 #           \addplot {(x+3)^2};
 #       \nextgroupplot[title = {$k=3$},]
 #           \addplot {x^3};
 #           \addplot {(x+1)^3};
 #           \addplot {(x+2)^3};
 #           \addplot {(x+3)^3};
 #   \end{groupplot}
 #   \node at ($(group c2r1) + (0,-4.0cm)$) {\ref{grouplegend}};
#\end{tikzpicture}

    
    print("\\begin{tikzpicture}",file=fileName)
    print("\\pgfplotsset{tiny,samples=10}",file=fileName)
    print("   \\begin{groupplot}[group style = {group size = 3 by 1, horizontal sep = 50pt}, width = 6.0cm, height = 5.0cm,",file=fileName)
    print("    xmin=0, ymin=0, xtick={0,16,32,64,120},",file=fileName)
    print("     xlabel={Cluster Size},",file=fileName)
    print("     ylabel={Time ($sec$)}",file=fileName)
    print("]",file=fileName)

    # Twitter
    dataset = "twitter"    

    print("      \\nextgroupplot[ title = {Twitter}, ",file=fileName)
    print("      legend style = { column sep = 10pt, legend columns = 3, legend to name = grouplegend,}] ",file=fileName)
    
    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    mySystems = list(set([r.split(", ")[0].translate(None, "[]'") for r in subset]))
    mySystems=sorted(mySystems)

    systemNames = []
    fail = "F"
    for s in mySystems:
        value_16 = fail
        value_32 = fail
        value_64 = fail
        value_128= fail
        systemNames.append(s)
        for line in subset:
            if s in line and line.split(", ")[1].translate(None, "[]'") == "16":
               value_16 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "32":
               value_32 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "64":
               value_64 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "128":
               value_128 = getTotalFromConsolidateTime(line)

        print("\\addplot table{", file=fileName)
        if value_16 != fail:
            print("   16 " +value_16   ,  file=fileName)
        if value_32 != fail:
            print("   32 " +value_32   ,  file=fileName)
        if value_64 != fail:
            print("   64 " +value_64   ,  file=fileName)
        if value_128 != fail:
            print("   128 "+value_128  ,  file=fileName)
        print("};"  ,  file=fileName)
        print("\\addlegendentry{"+s+"}"  ,  file=fileName)

    # legends
    # \legend{GraphLab,Giraph, Blogel-V, GraphX}
    #print("\\legend{"+", ".join(systemNames) +"}",file=fileName)
    #print("\\legend{"+", ".join(systemNames) +"}")


    # Twitter
    dataset = "uk0705"

    print("      \\nextgroupplot[ title = {UK0705}, ]",file=fileName)

    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    mySystems = list(set([r.split(", ")[0].translate(None, "[]'") for r in subset]))
    mySystems=sorted(mySystems)
    fail = "F"
    for s in mySystems:
        value_16 = fail
        value_32 = fail
        value_64 = fail
        value_128= fail
        systemNames.append(s)
        for line in subset:
            if s in line and line.split(", ")[1].translate(None, "[]'") == "16":
               value_16 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "32":
               value_32 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "64":
               value_64 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "128":
               value_128 = getTotalFromConsolidateTime(line)

        print("\\addplot table{", file=fileName)
        if value_16 != fail:
            print("   16 " +value_16   ,  file=fileName)
        if value_32 != fail:
            print("   32 " +value_32   ,  file=fileName)
        if value_64 != fail:
            print("   64 " +value_64   ,  file=fileName)
        if value_128 != fail:
            print("   128 "+value_128  ,  file=fileName)
        print("};"  ,  file=fileName)


    # Twitter
    dataset = "world-road"

    print("      \\nextgroupplot[ title = {World Road Network}, ]",file=fileName)

    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l]

    mySystems = list(set([r.split(", ")[0].translate(None, "[]'") for r in subset]))
    mySystems=sorted(mySystems)
    fail = "F"
    for s in mySystems:
        value_16 = fail
        value_32 = fail
        value_64 = fail
        value_128= fail
        systemNames.append(s)
        for line in subset:
            if s in line and line.split(", ")[1].translate(None, "[]'") == "16":
               value_16 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "32":
               value_32 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "64":
               value_64 = getTotalFromConsolidateTime(line)
            elif s in line and line.split(", ")[1].translate(None, "[]'") == "128":
               value_128 = getTotalFromConsolidateTime(line)

        print("\\addplot table{", file=fileName)
        if value_16 != fail:
            print("   16 " +value_16   ,  file=fileName)
        if value_32 != fail:
            print("   32 " +value_32   ,  file=fileName)
        if value_64 != fail:
            print("   64 " +value_64   ,  file=fileName)
        if value_128 != fail:
            print("   128 "+value_128  ,  file=fileName)
        print("};"  ,  file=fileName)



    print("\\end{groupplot}",file=fileName)
    print("\\node at ($(group c2r1) + (0,-4.0cm)$) {\\ref{grouplegend}};",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)


    return











def makeTekziStackDatasetWorkload(originalPath, dataset , workload, clusterSize):

    
    print(workload + " " + dataset + " " + str(clusterSize))
    print(originalPath+'/'+SummaryFile)
    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if workload in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    print(subset)

    if len(subset) == 0:
        return
    
    fileName = "StackDatasetWorkload-"+dataset+"-"+workload+"-"+str(clusterSize)

    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')
     
    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" + dataset+" - "+workload + " - " + str(clusterSize) +"}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()
    
    fileName = open(fileName+".tex", 'w')
    
    myResults = []
    for line in subset:
        systemName = line.split(", ")[0].translate(None, "[]'")
        combinedResults = line.split(", [")[1].translate(None, "[]'").split(", ")
        print(line)
        print(combinedResults)
        (value_read,value_exec,value_save,value_misc) = combinedResults
        myResults.append([systemName, value_read,value_exec,value_save,value_misc])

    
    #print(myResults)
    myResults=sorted(myResults, key=operator.itemgetter(0))
    #print(myResults)

    #print(myResults)
    myResults = zip (*myResults)
    #print(myResults)


    #introduction
    #print("\\documentclass{article}",file=fileName)
    #print("\\usepackage{pgfplots}",file=fileName)
    #print("\\pgfplotsset{compat=newest}",file=fileName)
    #print("\\pagestyle{empty}",file=fileName)
    #print("\\begin{document}",file=fileName)

    print("\\makeatletter",file=fileName)
    print("\\tikzset{nomorepostaction/.code=\\let\\tikz@postactions\\pgfutil@empty}",file=fileName)
    print("\\makeatother",file=fileName)


    print("\\begin{tikzpicture}",file=fileName)
    #print("\\begin{axis}[legend style={at={(0.5,-0.2)},anchor=north},",file=fileName)
    print("\\begin{axis}[",file=fileName)
    print("    xmin=1, ymin=0, bar width=1, bar shift=0pt, ybar stacked,",file=fileName)
    print("    width=8cm,height=7cm, enlarge x limits={abs=0.5}, ytick pos=left, xtick pos=left, area legend,",file=fileName)
    print("	xlabel={Cluster Size}, ",file=fileName)
    print("	ylabel={Time ($sec$)},",file=fileName)
    print("     xtick=data,xticklabels={"+str(myResults[0]).translate(None, "[]'()")+"},",file=fileName)
    print("     scaled ticks=false, xtick style={draw=none}, x tick label style={rotate=45,anchor=east}",file=fileName)
    print("]",file=fileName)

   
#x tick label style={rotate=90,anchor=east}
#,xtick=data
#,xticklabels={Test A,Test B,Test C,Test D}

#symbolic x coords={tool1, tool2, tool3, tool4, tool5, tool6, tool7},
#    xtick=data,
#i    x tick label style={rotate=45,anchor=east},

    
                   
#\addplot[fill=orange, fill opacity=0.75]
#coordinates{
#    (1,222898.050000000)
#    (2,235072.800000000)
#    (3,241192.450000000)
#    (4,156585.700000000)
#    (5,44232.0500000000)
#    (6,7846.75000000000)
#    (7,1653.35000000000)};
 

    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[4]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)




    # legends
    # \legend{GraphLab,Giraph, Blogel-V, GraphX}
    print("\\legend{Read, Execute, Save, Others}",file=fileName)
    #print("\\legend{"+", ".join(systemNames) +"}")

    # closing
    print("\\end{axis}",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)

    
    return






def makeTekziStackDatasetSystem(originalPath, dataset , system, clusterSize=128):

    
    
    print(system + " " + dataset + " " + str(clusterSize))
    print(originalPath+'/'+SummaryFile)
    subset = [l for l in open(originalPath+'/'+SummaryFile).readlines()
        if system in l
        and dataset in l
        and str(clusterSize) == l.split(", ")[1].translate(None, "[]'")]


    print(subset)

    if len(subset) == 0:
        return
    
    fileName = "StackDatasetSystem-"+dataset+"-"+system+"-"+str(clusterSize)

    os.chdir(originalPath)
    allFigures = open(DisplayFiguresFile, 'a')
     
    print("\\begin{figure}",file=allFigures)
    print("\\centering",file=allFigures)
    print("\\input{"+fileName+"}", file=allFigures)
    print("\\caption{" + dataset+" - "+system + " - " + str(clusterSize) +"}", file=allFigures)
    print("\\end{figure}", file=allFigures)

    allFigures.close()
    
    fileName = open(fileName+".tex", 'w')
    
    myResults = []
    for line in subset:
        workLoad = line.split(", ")[3].translate(None, "[]'")
        combinedResults = line.split(", [")[1].translate(None, "[]'").split(", ")
        #print(line)
        #print(combinedResults)
        (value_read,value_exec,value_save,value_misc) = combinedResults
        myResults.append([workLoad, value_read,value_exec,value_save,value_misc])

    
    #print(myResults)
    myResults=sorted(myResults, key=operator.itemgetter(0))
    #print(myResults)

    #print(myResults)
    myResults = zip (*myResults)
    #print(myResults)


    #introduction
    #print("\\documentclass{article}",file=fileName)
    #print("\\usepackage{pgfplots}",file=fileName)
    #print("\\pgfplotsset{compat=newest}",file=fileName)
    #print("\\pagestyle{empty}",file=fileName)
    #print("\\begin{document}",file=fileName)

    print("\\makeatletter",file=fileName)
    print("\\tikzset{nomorepostaction/.code=\\let\\tikz@postactions\\pgfutil@empty}",file=fileName)
    print("\\makeatother",file=fileName)


    print("\\begin{tikzpicture}",file=fileName)
    print("\\begin{axis}[legend style={at={(0.5,1.2)},anchor=north}, column sep = 10pt, legend columns = 4, ",file=fileName)
    #print("\\begin{axis}[",file=fileName)
    print("    xmin=1, ymin=0, bar width=1, bar shift=0pt, ybar stacked,",file=fileName)
    print("    width=8cm,height=7cm, enlarge x limits={abs=0.5}, ytick pos=left, xtick pos=left, area legend,",file=fileName)
    print("	xlabel={Workloads}, ",file=fileName)
    print("	ylabel={Time ($sec$)},",file=fileName)
    print("     xtick=data,xticklabels={"+str(myResults[0]).translate(None, "[]'()")+"},",file=fileName)
    print("     scaled ticks=false, xtick style={draw=none}",file=fileName)
    print("]",file=fileName)

   
    
                   

    print("\\addplot+[ybar] ["+load_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[1]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)
        

    print("\\addplot+[ybar] ["+execute_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[2]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)

    print("\\addplot+[ybar] ["+save_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[3]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)


    print("\\addplot+[ybar] ["+overhead_color+"] coordinates{", file=fileName)
    index=1
    for v in myResults[4]: # this is a list of READ numbers
        print("   (" +str(index)+", "+v+")" ,  file=fileName)
        index=index+1

    print("};"  ,  file=fileName)




    # legends
    # \legend{GraphLab,Giraph, Blogel-V, GraphX}
    print("\\legend{Read, Execute, Save, Others}",file=fileName)
    #print("\\legend{"+", ".join(systemNames) +"}")

    # closing
    print("\\end{axis}",file=fileName)
    print("\\end{tikzpicture}",file=fileName)
    #print("\\end{document}",file=fileName)

    
    return


def consolidateTime(fileName, workload, dataset, consolidatedFile=None, feature='Time', machineType='All'):    
    finalResult = []
    errorBars = []

    #print(fileName)
    summaryFile = glob.glob(fileName)
    
    
    clusterSize = fileName.split("/")[::-1][3]
    #print(clusterSize)
    
    
    print(summaryFile[0]+" : "+workload+" - "+dataset)
    results = [l for l in open(summaryFile[0]).readlines() 
        if l.split()[1]==workload
        and dataset==l.split()[2]
        #and machines==l.split()[3]
        and feature in l
        and machineType in l]
    
    print(results)
    
    #for l in results:
    #    print(l)
    
    # there are interesting results
    if len(results)!= 0:
        systemNames = list(set([r.split(" ")[0] for r in results]))
        
        for s in systemNames:
            
            
            systemResults = [r.split("[")[1].split(", ") for r in results
                             if s in r]

            print("-----------------------------")
            print(str(systemResults))
            for g in systemResults:
                g[3]=str(float(g[3])-float(g[0])-float(g[1])-float(g[2]))
            print(str(systemResults))

            systemResults = zip(*systemResults)
            
            
            myResults = [sum(float(f) for f in systemResults[0])/len(systemResults[0]), 
                            sum(float(f) for f in systemResults[1])/len(systemResults[1]), 
                            sum(float(f) for f in systemResults[2])/len(systemResults[2]), 
                            sum(float(f) for f in systemResults[3])/len(systemResults[3])]
            
            myError = [get_confidence_interval(float(f) for f in systemResults[0]),
                         get_confidence_interval(float(f) for f in systemResults[1]),
                         get_confidence_interval(float(f) for f in systemResults[2]),
                         get_confidence_interval(float(f) for f in systemResults[3])]
            
            finalResult.append([s, clusterSize, dataset, workload, len(systemResults[0]), myResults, myError])
            errorBars.append([s, myError])
    
    labels = ['Loading', 'Execution', 'Saving', 'Total']
    
    for l in finalResult:
        print(l, file=consolidatedFile)
    
    
    return
    
        


def consolidateSummaryFiles(paths):
    
    print("=====================================")
    print(paths)

        

    for inpath in paths:
        os.chdir(inpath)
        summaryFile = inpath + '/' + SummaryFile
        consolidatedFileTime = open(ConsolidatedTimeFile, 'w')
        
    
        for workload in WORKLOAD:
            for dataset in DATASET:    
                consolidateTime(summaryFile, workload, dataset, consolidatedFileTime)
    return
        
            
            



def generateSummaryFiles(paths):
    """parse directories, list log files in each and then generate one summary file for each directory.

    Arguments:
    paths  -- list of directories that include log files. directory names are expected to be equivelant to system names

    Returns:
    It does not return any thing but instead generate a summary file for each directory.
    """

    for inpath in paths:
        ### do something with inpath ###
        print("=====================================")
        print(inpath)
        os.chdir(inpath)
        summaryFile = open("summary.txt", 'w')
        
        
        # find every necessary log_prefix for each run
            # workloads 
            # datasets            
            # machines
            # mode
            # source (in case of SSSP or KHOP)
            # k (in case of KHOP)
        
        # I am using "__nbt.txt" because it is not created unless the job is finished
        logPotentialRuns = [f[:-9] for f in os.listdir(inpath) if "__nbt.txt" in f]
        
    
        for log_prefix in logPotentialRuns:
            timing = [0,0,0,0, []]
            
            if inpath.find(SYS_HALOOP) >= 0:
                print("------- HALOOOP------------")    
                timing = Haloop(inpath).processTimeFile(log_prefix)
            elif inpath.find(SYS_SPARK) >= 0:
                timing = SparkParsing(inpath).processTimeFile(log_prefix)
            elif inpath.find(SYS_GIRAPH) >= 0:
                timing = giraphParsing(inpath).processTimeFile_1_1_0(log_prefix)
            elif inpath.find(SYS_GRAPHLAB) >= 0:
                timing = GraphLabParsing(inpath).processTimeFile(log_prefix)
            elif inpath.find(SYS_BLOGEL) >= 0:
                timing = BlogelParsing(inpath).processTimeFile(log_prefix)
                
            if timing==None:
                continue
            else:
                print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" All Time "+str(timing), 
                      file=summaryFile)
            
            
            # compute system metrics now
            masterCPUfile = glob.glob(log_prefix + '_0_cpu.txt')
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Master cpuMax "+ str(cpu_parser(masterCPUfile)), 
                  file=summaryFile)
            
            #print("test", file=summaryFile)
            
            workerCPUfiles = [f for f in glob.glob(log_prefix + '_*_cpu.txt') if "_0_cpu.txt" not in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Worker cpuMax "+ str(cpu_parser(workerCPUfiles)), 
                  file=summaryFile)
                            
            masterCPUfile = [f for f in glob.glob(log_prefix + '_*_ctt.txt') if "_0_ctt.txt" in f or "__ctt.txt" in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Master cpuAve "+ str(ctt_parser(masterCPUfile)), 
                  file=summaryFile)
            
            workerCPUfiles = [f for f in glob.glob(log_prefix + '_*_ctt.txt') 
                              if "_0_ctt.txt" not in f and "__ctt.txt" not in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Worker cpuAve "+ str(ctt_parser(workerCPUfiles)), 
                  file=summaryFile)
            
            masterMemoryFile = glob.glob(log_prefix + '_0_mem.txt')
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Master Memory "+ str(mem_parser(masterMemoryFile)), 
                  file=summaryFile)
            
            #print("############")
            #print(masterMemoryFile)
            
        
            masterNetworkFile = [f for f in glob.glob(log_prefix + '_*_nbt.txt') if "_0_nbt.txt" in f or "__nbt.txt" in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Master Network "+ str(net_parser(masterNetworkFile)), 
                  file=summaryFile)
            
            #print("############")
            #print(masterNetworkFile)
            
            workerMemoryFiles = [f for f in glob.glob(log_prefix + '_*_mem.txt') if "_0_mem.txt" not in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Worker Memory "+ str(mem_parser(workerMemoryFiles)), 
                  file=summaryFile)

            #print("############")
            #print(workerMemoryFiles)
            
            workerNetworkFiles = [f for f in glob.glob(log_prefix + '_*_nbt.txt') if "_0_nbt.txt" not in f and "__nbt.txt" not in f]
            print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" Worker Network "+ str(net_parser(workerNetworkFiles)), 
                  file=summaryFile)
            
            #print("############")
            #print(workerNetworkFiles)            
        
            
            #elif inpath.find(SYS_BLOGEL) >= 0:
            #    print(getSystemName(inpath, log_prefix)+" "+printLogFileName(log_prefix)+" All Time "+str(BlogelParsing(inpath).processTimeFile(log_prefix)), file=summaryFile)

            
        
        summaryFile.close()            
    return 0

def systemColor(systemName):
    
    #print("==============================")
    #print(systemName)

    if "spark" in systemName:
        return "#ff7f00" # orange
    elif "haloop" in systemName:
        if "ADJ" in systemName:
            #print("ADJ")
            return "#550088"
        else:
            return "#0000ff" #blue

    elif "giraph" in systemName:
        return "g" #green
    elif "graphlab" in systemName:
        return "y" #yellow
    elif "blogel" in systemName:
        return "#ff00ff" #pink
    elif "hadoop" in systemName:
        if "ADJ" in systemName:
            return "#880055"
        else:
            return "#ff0000" #red
    else:
        return "#000000" #black


def makeFigure(finalResult, errorBars, figureTitle, labels, yAxis, xAxis, stackedFlag=0):
    
    
    #print(finalResult)
    
    if stackedFlag==1:
        finalResult = zip(*finalResult)
        finalResult[1] = zip(*finalResult[1])
        n_groups = len(finalResult[0])
    else:
        n_groups = len(finalResult[0][1])  
    fig, ax = plt.subplots()

    index = np.arange(n_groups)
    bar_width = 0.05

    opacity = 0.4
    error_config = {'ecolor': '0.3'}
    
    stackBottom = 0
    
    if stackedFlag==1:
        bar_width = 0.4
        labelColors = ["#ff0000","#ff00ff","#0000ff","#00ff00","#ffff00","#00ffff",]
        for i in range(0,len(finalResult[1])):
            values = [zip(*finalResult[1])[j][i] for j in range (0,len(finalResult[0]))]    
            ax.bar(index, values, bar_width,
                     alpha=opacity,
                     #yerr=errorBars[i][1],
                     error_kw=error_config,
                     bottom=stackBottom,
                     color=labelColors[i],
                     label=labels[i])
            if(i==0):
                stackBottom = [zip(*finalResult[1])[j][i] for j in range (0,len(finalResult[0]))]
            else:
                stackBottom = [x + y for x, y in zip(stackBottom, values)]
        plt.xticks(index + bar_width/2, finalResult[0])
        for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(10) 
                # specify integer or one of preset strings, e.g.
                #tick.label.set_fontsize('x-small') 
                #tick.label.set_rotation('vertical')
                #tick.label.set_rotation('30')
                
    else:        
        for i in range(0,len(finalResult)):
            ax.bar(index+i*bar_width, finalResult[i][1], bar_width,
                     alpha=opacity,
                     yerr=errorBars[i][1],
                     error_kw=error_config,
                     bottom=stackBottom,
                     color=systemColor(finalResult[i][0]),
                     label=finalResult[i][0])
    
        plt.xticks(index + ((len(finalResult)-1)*n_groups*bar_width)/2, labels)
        plt.tight_layout()
        for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(10) 
                
    plt.ylabel(yAxis, horizontalalignment='left', verticalalignment='top')
    plt.xlabel(xAxis)
    ax.set_title(figureTitle) 
    noColumns = 2
    ax.legend(loc='best',fontsize=10, ncol=noColumns)
    
    
    fig.savefig(FIGURE_PREFIX+figureTitle.replace(" ","-")+".pdf")
    return ax
    #plt.show()



def HALOOPfullAnalysis(path, dataset, machines):
        
    summaryFile = glob.glob(path + '/summary.txt')
    print(summaryFile)
    feature = "Time"
    finalResult = []
    errorBars = []        
    machineType = "All"
    
    iterationResult = []
    shuffleResult = []
    shuffleErrorBars = []

    index = 0
    fig, ax = plt.subplots()
    fig = plt.figure(figsize=(12, 6))
    
    for w in WORKLOAD:
        print(w)
        finalResult = []
        errorBars = []
        iterationResult = []
        shuffleResult = []
        shuffleErrorBars = []

        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==w
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
        
        print(results)
        
    
        if len(results)!= 0:
            #print(str(results))
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                print("------------ "+s+" -------------- really")
                
                timingResults = [r.split("[")[1].split(", ") for r in results
                                 if s in r]
                
                iterationTiming = [r.split("[")[2].split("]")[0].split(", ") for r in results
                                 if s in r]
                
                shufflingBytes = [r.split("[")[3].split("]")[0].split(", ") for r in results
                                 if s in r]
                
                iterationTiming = iterationTiming[0]
                shufflingBytes = shufflingBytes[0]
                if shufflingBytes == ['']:
                    shufflingBytes = ['0']
                
                print("===============================")
                print(iterationTiming)
                print(shufflingBytes)
                shufflingBytes = [float(f) for f in shufflingBytes]
                print(shufflingBytes)
                
                #print(str(systemResults))
                timingResults = zip(*timingResults)
                #print("-----------------------------")
                #print(systemResults)
            
                timingResults = [sum(float(f) for f in timingResults[0])/len(timingResults[0]), 
                                sum(float(f) for f in timingResults[1])/len(timingResults[1]), 
                                sum(float(f) for f in timingResults[3])/len(timingResults[3]), 
                                sum(float(f) for f in timingResults[2])/len(timingResults[2])]
                systemErrors = [0, 0, 0, 0]
                finalResult.append([s, timingResults])
                errorBars.append([s, systemErrors])
                
                
                print("##########################################")
                print(s)
                print(iterationTiming)
                iterationResult.append([s, iterationTiming])
                print(iterationResult)
                shuffleErrors = 0
                shuffleErrorBars.append([s, shuffleErrors])
                shuffleResult.append([s, [sum(shufflingBytes)]])
                
                print(shuffleResult)
                
                
                
            # timing figure
            print("making timing figures")
            labels = ['Loading', 'Saving', 'Execution', 'Total']
            makeFigure(finalResult, errorBars, w+"-"+dataset+"-"+machineType+' Time Analysis-TESTHALOOP', labels, 'seconds', '')
            

            # shuffling figure
            print("making shuffling figures")
            labels = ['Shuffled Bytes']
            makeFigure(shuffleResult, shuffleErrorBars, w+"-"+dataset+"-"+' Shuffled Bytes', labels, 'GB', '')

            printResult([path], w, dataset, machines)
            
        else:
            finalResult.append([path.split("/").pop(), [0,0,0,0]])
            errorBars.append([path.split("/").pop(), [0,0,0,0]])
            
    return    
    


def showMaxCPUfigures(Paths, workload, dataset, machines, machineType):
    
    feature = "cpuMax"
    finalResult = []
    errorBars = []
    for inPath in Paths:
        summaryFile = glob.glob(inPath + '/summary.txt')
        #print(summaryFile)
        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==workload
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
                
        if len(results)!=0 :
            #print(str(results))
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                systemResults = [r.split("(")[1].replace(")\n","").split(", ") 
                                 for r in results if s in r]
                #print(str(systemResults))
                systemResults = zip(*systemResults)
                #print(systemResults)
                systemResults = [sum(float(f) for f in systemResults[0])/len(systemResults[0]),
                                 sum(float(f) for f in systemResults[3])/len(systemResults[3]), 
                                 sum(float(f) for f in systemResults[5])/len(systemResults[5])]
                systemErrors = [0,0, 0]
                finalResult.append([s, systemResults])
                errorBars.append([s, systemErrors])
                #print(str(systemResults))
        else:
            finalResult.append([inPath.split("/").pop(), [0,0, 0]])
            errorBars.append([inPath.split("/").pop(), [0,0, 0]])
    #print(finalResult)
    
    labels = ['User', 'IO waiting','Idle']
    return makeFigure(finalResult, errorBars, workload+"-"+dataset+"-"+machineType+' Max CPU utilization', labels, 'percentage(%)', '')
    

def showAverageCPUfigures(Paths, workload, dataset, machines, machineType, stackFlag=0):
    
    feature = "cpuAve"
    finalResult = []
    errorBars = []
    for inPath in Paths:
        summaryFile = glob.glob(inPath + '/summary.txt')
        #print(summaryFile)
        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==workload
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
                
        if len(results)!=0 :
            #print(str(results))
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                #print(results)
                systemResults = [r.split("[")[1].replace("]\n","").split(", ") 
                                 for r in results if s in r]
                #print("Test before print")
                #print(systemResults[0])
                test = [float(r) for r in systemResults[0]]
                #print(sum(test))

                systemResults = zip(*systemResults)
                #print(systemResults)
                systemResults = [sum(float(f) for f in systemResults[0])/len(systemResults[0]),
#                                 sum(float(f) for f in systemResults[1])/len(systemResults[1]),
                                 sum(float(f) for f in systemResults[2])/len(systemResults[2]),
                                 sum(float(f) for f in systemResults[3])/len(systemResults[3]), 
                                 sum(float(f) for f in systemResults[4])/len(systemResults[4])]
                systemErrors = [0,0, 0, 0 ]
                finalResult.append([s, systemResults])
                errorBars.append([s, systemErrors])
                #print(str(systemResults))
        else:
            finalResult.append([inPath.split("/").pop(), [0,0, 0,  0]])
            errorBars.append([inPath.split("/").pop(), [0,0, 0, 0]])
    #print(finalResult)
    
    labels = ['User', 'System','IO waiting','Idle']
    figureTitle = workload+"-"+dataset+"-"+machineType+' Average CPU utilization'
    if stackFlag == 1:
        figureTitle = figureTitle+"(stacked)"
    return makeFigure(finalResult, errorBars, figureTitle, labels, 'percentage(%)', '', stackFlag)



def showMemoryfigures(Paths, workload, dataset, machines, machineType):
    
    feature = "Memory"
    finalResult = []
    errorBars = []
    for inPath in Paths:
        summaryFile = glob.glob(inPath + '/summary.txt')
        #print(summaryFile)
        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==workload
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
                
        if len(results)!=0:
            #print(str(results))
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                systemResults = [r.split("(")[1].replace(")\n","").split(", ") 
                                 for r in results if s in r]
                #print(str(systemResults))
                systemResults = zip(*systemResults)
                #print(systemResults)
                systemResults = [sum(float(f) for f in systemResults[0])/len(systemResults[0]), 
                                 sum(float(f) for f in systemResults[1])/len(systemResults[1]), 
                                 sum(float(f) for f in systemResults[2])/len(systemResults[2])]
                systemErrors = [0,0,0]
                finalResult.append([s, systemResults])
                errorBars.append([s, systemErrors])
            #print(str(systemResults))
        else:
            finalResult.append([inPath.split("/").pop(), [0,0,0]])
            errorBars.append([inPath.split("/").pop(), [0,0,0]])
        
    #print(finalResult)
    
    labels = ['Min', 'Avg', 'Max']
    return makeFigure(finalResult, errorBars, workload+"-"+dataset+"-"+machineType+' Memory Utilization', labels, 'GB', '')

def showNetworkfigures(Paths, workload, dataset, machines, machineType):
    
    feature = "Network"
    finalResult = []
    errorBars = []
    for inPath in Paths:
        summaryFile = glob.glob(inPath + '/summary.txt')
        #print(summaryFile)
        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==workload
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
        
        if len(results)!= 0:
            #print(str(results))
            #results = sorted(results)
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                systemResults = [r.split("(")[1].replace(")\n","").split(", ") 
                                 for r in results if s in r]
                #print(str(systemResults))
                systemResults = zip(*systemResults)
                #print(systemResults)
                systemResults = [sum(float(f) for f in systemResults[0])/len(systemResults[0]), 
                                 sum(float(f) for f in systemResults[1])/len(systemResults[1])]
                systemErrors = [0,0]
                finalResult.append([s, systemResults])
                errorBars.append([s, systemErrors])
        else:
            finalResult.append([inPath.split("/").pop(), [0,0]])
            errorBars.append([inPath.split("/").pop(), [0,0]])
        #print(str(systemResults))
        
    #print(finalResult)
    
    labels = ['Received', 'Sent']
    return makeFigure(finalResult, errorBars, workload+"-"+dataset+"-"+machineType+' Network Utilization', labels, 'GB', '')





def showTimefigures(Paths, workload, dataset, machines):
    
    machineType = "All"
    feature = "Time"
    finalResult = []
    errorBars = []
    for inPath in Paths:
        summaryFile = glob.glob(inPath + '/summary.txt')
        #print(summaryFile)
        results = [l for l in open(summaryFile[0]).readlines() if l.split()[1]==workload
                   and dataset==l.split()[2]
                   and machines==l.split()[3]
                   and feature in l
                   and machineType in l]
        
        if len(results)!= 0:
            #print(str(results))
            systemNames = list(set([r.split(" ")[0] for r in results]))
            for s in systemNames:
                systemResults = [r.split("[")[1].split(", ") for r in results
                                 if s in r]
                #print(str(systemResults))
                systemResults = zip(*systemResults)
                #print("-----------------------------")
                #print(systemResults)
            
                systemResults = [#sum(float(f) for f in systemResults[0])/len(systemResults[0]), 
                                #sum(float(f) for f in systemResults[1])/len(systemResults[1]), 
                                sum(float(f) for f in systemResults[3])/len(systemResults[3]), 
                                sum(float(f) for f in systemResults[2])/len(systemResults[2])]
                systemErrors = [#0, 0, 
                                0, 0]
                finalResult.append([s, systemResults])
                errorBars.append([s, systemErrors])
        else:
            finalResult.append([inPath.split("/").pop(), [#0,0,
                                                          0,0]])
            errorBars.append([inPath.split("/").pop(), [#0,0,
                                                        0,0]])
    
    labels = [#'Loading', 'Saving', 
              'Execution', 'Total']
    return makeFigure(finalResult, errorBars, workload+"-"+dataset+"-"+machineType+' Time Analysis', labels, 'seconds', '')

        

def printResult(Paths, workload, dataset, machines):
    
    stacked=1
    
    
    
    
    showTimefigures(Paths, workload, dataset, machines)
    
    showMaxCPUfigures(Paths, workload, dataset, machines, "Master")
    #showAverageCPUfigures(Paths, workload, dataset, machines, "Master")
    showAverageCPUfigures(Paths, workload, dataset, machines, "Master", stacked)
    showNetworkfigures(Paths, workload, dataset, machines, "Master")
    showMemoryfigures(Paths, workload, dataset, machines, "Master")
    
    showMaxCPUfigures(Paths, workload, dataset, machines, "Worker")
    showAverageCPUfigures(Paths, workload, dataset, machines, "Worker", stacked)
    #showAverageCPUfigures(Paths, workload, dataset, machines, "Worker")
    showNetworkfigures(Paths, workload, dataset, machines, "Worker")
    showMemoryfigures(Paths, workload, dataset, machines, "Worker")
    
    


def printResultSubFig(Paths, workload, dataset, machines):
    
    stacked=1
    
    plt.close('all')

    
    f, (maxCPU, avgCPU) = plt.subplots(2, sharey=True)
    
    #showTimefigures(Paths, workload, dataset, machines)
    
    #showMaxCPUfigures(Paths, workload, dataset, machines, "Master")
    #showAverageCPUfigures(Paths, workload, dataset, machines, "Master")
    #showAverageCPUfigures(Paths, workload, dataset, machines, "Master", stacked)
    #showNetworkfigures(Paths, workload, dataset, machines, "Master")
    #showMemoryfigures(Paths, workload, dataset, machines, "Master")

    #showNetworkfigures(Paths, workload, dataset, machines, "Worker")
    #showMemoryfigures(Paths, workload, dataset, machines, "Worker")
    
    maxCPU = showMaxCPUfigures(Paths, workload, dataset, machines, "Worker")
    avgCPU = showAverageCPUfigures(Paths, workload, dataset, machines, "Worker", stacked)
    #showAverageCPUfigures(Paths, workload, dataset, machines, "Worker")
    
    
    plt.show()
    



class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg















def getPaths(directory):
    
    paths = [directory+"/"+myFile+"/logs/" for myFile in os.listdir(directory)]
    
    finalPaths = []
    tmpPaths = []
    
    for subDirectory in paths:
        try:
            tmpPaths = [subDirectory+folder for folder in os.listdir(subDirectory)]
            for p in tmpPaths:
                finalPaths.append(p)
        except (OSError, RuntimeError, TypeError, NameError):
            pass
        
    print(finalPaths)
    return finalPaths


def findFather(paths):
    myFolder = paths[0]
    
    fathers = [line.split()[0] for line in open(myFolder+"/potential").readlines()]
    
    potentialFathers = [line.split()[1] for line in open(myFolder+"/khop_1_i1").readlines()]
    
    print(fathers)
    print(len(potentialFathers))
    
    for f in fathers:
        potentialFathers = [line for line in open(myFolder+"/khop_0_i1").readlines() if f in line]
        if len(potentialFathers) != 0:
            print(f+" : "+str(potentialFathers))


def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2015 organization_name. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))



    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="paths", help="path to the log folder [default: %(default)s]", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        # I get a directory like X, such that sub directories look like:
        # X/<# machines>/logs/<system Name>/....
        #paths = args.paths
        
        paths = getPaths(args.paths[0])

        test = True
        if test:
            # Already generated
            #generateSummaryFiles(paths)
            #consolidateSummaryFiles(paths)
            #mergeConsolidatedFiles(args.paths[0])
                    
            makeTekziGroupStackDataset(args.paths[0],"twitter")
            makeTekziGroupStack(args.paths[0],PAGERANK)
        
            #Multiple systems and all cluster sizes
            #makeTekziLineDatasetWorkload(args.paths[0],"twitter",PAGERANK)

            return


        # Generate a sumary file for each system
        generateSummaryFiles(paths)
        consolidateSummaryFiles(paths)
        mergeConsolidatedFiles(args.paths[0])

        os.chdir(args.paths[0])

        stackedFile = "Stacked_"+DisplayFiguresFile

        fileName = open(stackedFile, 'w')
        print("\\documentclass{article}",file=fileName)
        print("\\usepackage{pgfplots}",file=fileName)
        print("\\usepackage{tikz}",file=fileName)
        print("\\usetikzlibrary{patterns}",file=fileName)

        print("\\usetikzlibrary{pgfplots.groupplots}",file=fileName)
        #print("\\usepackage{pgfplots}",file=fileName)
        print("\\pgfplotsset{compat=newest}",file=fileName)
        

        print("\\pagestyle{empty}",file=fileName)
        print("\\begin{document}",file=fileName)

        fileName.close()


        #for data in DATASET:
            #for w in WORKLOAD:
                #makeTekziStackDatasetWorkload(args.paths[0],data,w,16)
                #makeTekziStackDatasetWorkload(args.paths[0],data,w,32)
                #makeTekziStackDatasetWorkload(args.paths[0],data,w,64)
 
        os.chdir(args.paths[0])
        fileName = open(DisplayFiguresFile, 'a')
        print("\\end{document}",file=fileName)
        fileName.close()



        lineFile = DisplayFiguresFile
 
        fileName = open(lineFile, 'w')
        print("\\documentclass{article}",file=fileName)
        print("\\usepackage{pgfplots}",file=fileName)
        print("\\pgfplotsset{compat=newest}",file=fileName)
	print("\\usetikzlibrary{pgfplots.groupplots}",file=fileName)
        print("\\usepackage{tikz}",file=fileName)
        print("\\usetikzlibrary{patterns}",file=fileName)

        print("\\pagestyle{empty}",file=fileName)
        print("\\begin{document}",file=fileName)        
        
        fileName.close()
        
        #makeTekziStackDatasetSystem(args.paths[0], "clueweb" , "blogel")   

	makeTekziGroupStack(args.paths[0], "pagerank")
	makeTekziGroupStack(args.paths[0], "wcc")
	makeTekziGroupStack(args.paths[0], "sssp")
	makeTekziGroupStack(args.paths[0], "khop")

        os.chdir(args.paths[0])
        fileName = open(DisplayFiguresFile, 'a')
	print("\clearpage",file=fileName)
        fileName.close()

        makeTekziGroup(args.paths[0], "pagerank")
        makeTekziGroup(args.paths[0], "sssp")
        makeTekziGroup(args.paths[0], "wcc")
        makeTekziGroup(args.paths[0], "khop")   


        os.chdir(args.paths[0])
        fileName = open(DisplayFiguresFile, 'a')
	print("\clearpage",file=fileName)
        fileName.close()


        

        for data in DATASET:
            for w in WORKLOAD:
                makeTekziLineDatasetWorkload(args.paths[0],data,w)
                
                makeTekziStackDatasetWorkload(args.paths[0],data,w,16)
                makeTekziStackDatasetWorkload(args.paths[0],data,w,32)
                makeTekziStackDatasetWorkload(args.paths[0],data,w,64)
                makeTekziStackDatasetWorkload(args.paths[0],data,w,128)
#        makeTekziStackedDatasetWorkloadClusterSize(Twitter,PageRank, 32)
        
        os.chdir(args.paths[0])
        fileName = open(DisplayFiguresFile, 'a')
        print("\clearpage",file=fileName)
        fileName.close()
 
 
        for data in DATASET:
            for s in ['giraph','spark','graphlab-sync-auto-itr','graphlab-sync-auto-tol','graphlab-async-auto',
			'graphlab-sync-random-itr','graphlab-sync-random-tol','graphlab-async-random','blogel-V','blogel-B']:
                makeTekziLineDatasetSystem(args.paths[0], data , s)
                

        os.chdir(args.paths[0])
        fileName = open(DisplayFiguresFile, 'a')
        print("\\end{document}",file=fileName)
        fileName.close()
 
 
        #printResult(paths, "sssp", "orkut", "20")
        
        return
        
        clusterSize = "16" # "10"
        #dataset = "orkut" # "orkut"
        
        print(paths)
        
        #for path in paths:
        #    print(SYS_HALOOP)
        #    print(path)
        #    if SYS_HALOOP in path:
        #        print("Testing Haloop")
        #        HALOOPfullAnalysis(path, dataset, clusterSize)
        #    else:
        #        print("Haloop does not exist")
        
        #return 0
        
        
        for dataset in DATASET:
            for query in WORKLOAD:
                for clusterSize in ["16","32","64"]:
                    printResult(paths, query, dataset, clusterSize)
            
            #printResult(paths, "sssp", dataset, clusterSize)
            #printResult(paths, "wcc", dataset, clusterSize)
            #printResult(paths, "khop", dataset, clusterSize)
        
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    #except Exception, e:
    #    if DEBUG or TESTRUN:
    #        raise(e)
    #    indent = len(program_name) * " "
    #    sys.stderr.write(program_name + ": " + repr(e) + "\n")
    #    sys.stderr.write(indent + "  for help use --help")
    #    return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'parsing.commonArgParse_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
