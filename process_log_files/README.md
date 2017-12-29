#Log Files Processing


##How to run?
The main command you need to run is:
`python common.py $log_directory`

### Process:
1- This code generates a summary file that summarizes each run of each cluster/workload/dataset/system
2- Then, it combines these runs and compute confidence intervals
3- After that, it generates different type of Tekzi figures as .tex files. These files could be added into papers directly. 
4- The summary file could also be used by the flask server to serve an interactive analysis. 

##Setup
The `$log_directory` bash variable has a path to the directory which includes all log files. This directory has a directory for each cluster size (e.g. 16, 32, 64, 128). Each one of these directories has a directory for each evaluated system, such as HaLoop, Giraph, GraphLab, etc.


###Log files
Each run generates a log file starts by the workload name, and ends by _time.txt

