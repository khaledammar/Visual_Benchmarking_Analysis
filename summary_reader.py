 #\\\Build Notes\\\
'''Things that need to be done and assumptions
Assuming
- That the x-axis will always have be the variable of system
- That the y-axis is always going to be time
- That there will always need to have atleast one parameter searched

Things that need to be done
- The dropdown menu #DONE
- Radial button for to determine what will be the x-axis
- The GUI issue if the everything is determined except for the cluster type 
- Converting the string representation of a list into a list #nan problem DONE
- Adapting the previous algorithms to componsate for the extra seventh parameter #DONE
- Creating a way to make multple of histograms with different parameters.

Problems that were found
- The dropdown menu cannot be centered, the drop down portion of the button #ALERTNATIVE SOLUTION FOUND
- the [nan, nan, nan] problem.'''


import os.path
from flask import Flask, render_template, request, url_for
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
app = Flask(__name__)

search_parameters = []
df = None
x_axis = 0
graph_type = ""
display_count = [0]

@app.route('/', methods = ['POST','GET'] )
def index():
    return render_template('get_summary.html', warning = 'False')


@app.route('/display', methods = ['POST','GET'])
def main():
    global search_parameters, df, x_axis, graph_type, display_count
    display_count = [0]
    graph_type = request.form.get('graph_type')
    file_name = request.form.get('file_box')
     
    if not os.path.isfile(file_name):
        return render_template('error.html')
        
    infile = open(file_name, 'r')
    all_lines = infile.readlines()
    infile.close()
      
    param_list = {"Workload Name": request.form['workload'], "Dataset":request.form['dataset'], "Cluster Size": request.form['cluster'], "System Name" : request.form['system']}
    
    x_axis = request.form["x_axis"]

    x_axis = int(x_axis)


    if not check_param_none(param_list):
	return render_template('get_summary.html', warning = 'True')


    data_list = string_to_list_converter(all_lines)
    df = create_data_frame(data_list)
    search_parameters = create_param_list(param_list)
    display_count.append(find_histogram_num(search_parameters, x_axis))
   
    if graph_type == "solid":
	histogram_values, display_labels, table_string = generate_histogram(df, search_parameters, display_count[0])
	return render_template('summary_histogram.html', histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])
    elif graph_type == "stack":
        histogram_values, display_labels, table_string = generate_stacked_histogram(df, search_parameters, display_count[0])
	return render_template("summary_stacked_histogram.html", histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])




def create_data_frame(data_list):
    '''Takes a nested list, which will create a data frame using that data.'''

    horizontal_labels  = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name', 'Number of Execution', 'Run Times', 'Etc Numbers']
    vertical_labels = []

    for test_num in range(len(data_list)):
        vertical_labels.append('Test ' + str(test_num + 1))

    df = pd.DataFrame(data_list, index = vertical_labels, columns = horizontal_labels)
    return df




def generate_histogram(df, search_parameters, histogram_number):
    '''Searches through the parameter list, and data frame to format the desired data into a dictionary formatted
    in such a way to be readable so it can create a histogram.
    '''
    global x_axis

    labels_for_display = find_search_labels(search_parameters, x_axis, histogram_number)
    modified_df, search_parameters = search_df(df, search_parameters, x_axis, histogram_number)    
    sums_dict = count_times(modified_df, x_axis)
    table_string = ""
    if x_axis == 0:
        table_string = create_table(sums_dict)
	sums_dict = system_label_change(sums_dict)
    histogram_values = create_histogram_format(sums_dict)

    return histogram_values, labels_for_display, table_string




def generate_stacked_histogram(df, search_parameters, histogram_number):
    '''Searches throug the parameter list, and data frame to format the desired data into a dictionary formatted
    in such a way that app can create a stacked column histogram.
    '''
    global x_axis
    labels_for_display = find_search_labels(search_parameters, x_axis, histogram_number)
    modified_df, search_parameters = search_df(df, search_parameters, x_axis, histogram_number)
    sums_dict =  stack_count_times (modified_df, x_axis)
    table_string = ""
    if x_axis == 0:
        table_string = create_table(sums_dict)
	sums_dict = system_label_change(sums_dict)
    histogram_values = create_stacked_format(sums_dict, x_axis)

    return histogram_values, labels_for_display, table_string



def create_table(sums_dict):
    '''Creates a string that is in the format of a html table to represents which what each of the system abbreviations means
    '''
    global graph_type

    alternate_label_dict = {"graphlab-sync-auto-itr":"GL-S-A-I", "graphlab-sync-random-itr":"GL-S-A-I", "graphlab-sync-random-itr":"GL-S-R-I", "graphlab-async-random-tol":"GL-A-R-T", "graphlab-sync-random-tol":"GL-S-R-T", "graphlab-sync-auto-tol":"GL-S-A-T", "graphlab-async-auto-tol":"GL-A-A-T", "graphlab-sync-auto": "GL-S-A", "graphlab-sync-random":"GL-S-R", "spark-itr": "S-I", "spark-tol" : "S-T", "giraph":"G", "blogel-Vertex":"B-V", "vertica":"V"}

    table_string = "<p>Legend</p><tr><th>Symbol</th><th>System Name</th></tr>"
    if graph_type == "solid":
	for key in sums_dict:
	    table_string = table_string + "<tr><th>" + alternate_label_dict[key] + "</th>" + "<th>" + key + "</th></tr>"
    else:
	for key in sums_dict:
	    if key[:-1] not in table_string:
	        table_string = table_string + "<tr><th>" + alternate_label_dict[key[:-1]] + "</th>" + "<th>" + key[:-1] + "</th></tr>"
            
    return table_string

def find_search_labels(search_parameters, x_axis, histogram_number):
    '''Takes in a diciontary where the values are either keys of strings or strings, these represetnt the search parameters.
    It also takes a integer value (x_axis) that represents which of the parameters is going to be represented on the x-axis
    of the histogram. This will return a list parameters that were searched for the current iteration of the histogram displayed
    '''
    parameter_display = []
    x_label = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name']

    for key in search_parameters:
	if x_label[x_axis] != key:
	    if type(search_parameters[key]) == list:
	        parameter_display.append(search_parameters[key][histogram_number])
	    else:
	        parameter_display.append(search_parameters[key]) 

    return parameter_display



def find_histogram_num(search_parameters, x_axis):
    '''Takes in a dictonary where the values are iether keys o f a stirng or strings, these represent the search parameters.
    It also takes an integer value (x_axis) that represents which ofht eparameters is going to be represented on teh x-axis
    of the isotgram. This will return the number of times histogram will have to be diplayed to show all version of it.
    '''
    x_labels = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name']
    for key in search_parameters:
	if x_labels[x_axis] != key and type(search_parameters[key]) == list:
	    return len(search_parameters[key]) - 1

    return 0





def search_df(df, search_parameters, x_axis, histogram_number):
    '''Goes through the inputted data frame, and returns a modified data frame that only contains
    the values that were quested upon in search_parameters
    '''
    modified_df = df
    x_axis_labels = ["System Name", "Cluster Size", "Dataset", "Workload Name"]

    for key in search_parameters:
	if type(search_parameters[key]) != list:
	    modified_df = modified_df[modified_df[key] == search_parameters[key]] 
        else:
	    if key == x_axis_labels[x_axis]:
		pass
	    else:
	        search_length = len(search_parameters)
	    	single_filter = search_parameters[key][histogram_number]
            	modified_df = modified_df[modified_df[key] == single_filter]
    return modified_df, search_parameters





def system_label_change(sums_dict):
    '''Changes the label for the system names to abbreviated version, to make it fit better when displayed on
    the histogram.
    '''
    global graph_type
    alternate_label_dict = {"graphlab-sync-auto-itr":" GL-S-A-I ", "graphlab-sync-random-itr":" GL-S-A-I ", "graphlab-sync-random-itr":" GL-S-R-I ", "graphlab-async-random-tol":" GL-A-R-T ", "graphlab-sync-random-tol":" GL-S-R-T ", "graphlab-sync-auto-tol":" GL-S-A-T ", "graphlab-async-auto-tol":" GL-A-A-T ", "graphlab-sync-auto": " GL-S-A ", "graphlab-sync-random":" GL-S-R ", "spark-itr": "  S-I  ", "spark-tol" : "  S-T  ", "giraph":"   G   ", "blogel-Vertex":"  B-V  ", "vertica":"   V   "}

    new_sums_dict = {}

    if graph_type == 'solid':
        for key in sums_dict:
	    new_sums_dict[alternate_label_dict[key]] = sums_dict[key]
    else:
	for key in sums_dict:
	    new_sums_dict[alternate_label_dict[key[:-1]] + key[-1]] = sums_dict[key]

    return new_sums_dict







def count_times(df, x_axis):
    '''Retruns a dictionary in the form {Name:value, Name:value} 
    where value is the time it took for the program to run. Name is the label that will
    used on the x-axis
    '''
    sums_dict = {}

    all_rows = df.values
    for row in all_rows:
	if row[-2][0] != 'nan':
            if row[0] in sums_dict:
	        sums_dict[row[x_axis]] += round( sum(row[-2]),3 )
	    else:
	        sums_dict[row[x_axis]] = round( sum(row[-2]),3)

    return sums_dict





def stack_count_times(df, x_axis):
    '''Retruns a dictionary in the form {Name:value, Name:value} 
    where value is the time it took for the program to run. Name is the label that will
    used on the 
    '''
    sums_dict = {}
    all_rows = df.values

    for row in all_rows:
	if row[-2][0] != 'nan':
	    for index in range(len(row[-2])):

		if row[x_axis] + str(index) in sums_dict:
		    sums_dict[row[x_axis] + str(index)] += round(row[-2][index], 2)
		else:
	 	    sums_dict[row[x_axis] + str(index)] = round(row[-2][index],2)

    return sums_dict




def create_histogram_format(sums_dict):
    '''Takes a dicitonary where the keys are the labels of the histogram, while the value
    is to the total time. It returns a list of dictionary where each dictionary follows
    [{"x":"label", "y":time}]
    '''

    histogram_values = []

    for key in sums_dict:
	histogram_values.append({"x":key, "y":sums_dict[key]})

    return histogram_values




def create_stacked_format(sums_dict, x_axis):
    '''Takes a dictionary where the keys are the labels of the histogram, while the value is the total
    time it took to run a part of hte program. It returns a list of dictionaries where ach dictionary follows;
    [{"x-axis":blogel-vertex, "time":23.2, "time_type": "execute"}] 
    '''

    all_systems = [" GL-S-A-I "," GL-S-R-I ", " GL-A-R-T ", " GL-S-R-T ", " GL-S-A-T "," GL-A-A-T ", " GL-S-A ", " GL-S-R ", "  S-I  ", "  S-T  ", "   G   ", "  B-V  ", "   V   "]
    all_clusters = ['16','32','64','128'] 
    all_datasets = ['twitter','world-road','uk0705','clueweb']
    all_workloads = ['pagerank','wcc','sssp','khop']
    
    all_labels = [ all_systems, all_clusters, all_datasets, all_workloads]

    histogram_values = []
    running_states = ['load', 'execute', 'save', 'misc']

    for index in range(len(running_states)-1, -1, -1):
	for label in all_labels[x_axis]:
	    for key in sums_dict:
		if key == label + str(index):
		    histogram_values.append( {"x-axis": label, "time": sums_dict[key], "time_type": running_states[index]} )
		    break

    return histogram_values 




def create_param_list(param_list):
    '''Returns a dictionary of search values which will depend on what is inputted in the get_summary.html
    '''
    all_systems = ['graphlab-sync-auto-itr','graphlab-sync-random-itr','graphlab-async-random-tol','graphlab-sync-random-tol','graphlab-sync-auto-tol','graphlab-async-auto-tol','graphlab-sync-auto', 'graphlab-sync-random', 'spark-itr', 'spark-tol', 'giraph', 'blogel-Vertex','vertica']
    all_clusters = ['16','32','64','128'] 
    all_datasets = ['twitter','world-road','uk0705','clueweb']
    all_workloads = ['pagerank','wcc','sssp','khop']
    
    all_parameter_search = {"Workload Name": all_workloads, "Dataset": all_datasets, "Cluster Size": all_clusters, "System Name": all_systems}

    for key in all_parameter_search:
	if param_list[key] != "None":
	    all_parameter_search[key] = param_list[key]

    return all_parameter_search
	


def check_param_none(param_list):
    '''Checks to see if the list contains no more than two None value, if there is 2 None parameter it will return True
    Otherwise it will return False'''
    none_count = 0

    for key in param_list:
	if param_list[key] == 'None':
	    none_count += 1


    if none_count <= 2:
	return True
    return False



def string_to_list_converter(all_lines): #THE ONE THAT I WILL BE USING
    '''Takes in a list where each index represents each line. It converts the text version fo the text into a list data type'''

    output_list = []
    
    for line in all_lines:
	if line != '\n':
	    nested_list = []
	    line.rstrip()
	    line = line[1:-2]
            line = line.split(', [')
            line[1] = line[1][:-1]
            line[2] = line[2][:-1]
            for index in range(len(line)):
		line[index] =  line[index].split(', ')

	    for index in range(len(line[0])):
		nested_list.append(ast.literal_eval(line[0][index]))
	    for index in range(len(line[1])):
		if line[1][index] != 'nan':
		    line[1][index] = ast.literal_eval(line[1][index])
	    nested_list.append(line[1])

	    for index in range(len(line[2])):
		if line[2][index] != 'nan':
		    line[2][index] = ast.literal_eval(line[2][index])

	    nested_list.append(line[2])
            output_list.append(nested_list)

    return output_list
           


def calculate_total_time(line_list):

    total_dict = {}
    for data_line in line_list:
        total_time = sum(data_line[-2])      

	if data_line[0] in total_dict:
	    total_dict[data_line[0]] += total_time 
	else:
	    total_dict[data_line[0]] = total_time

    return total_dict



@app.route("/next", methods = ["POST","GET"])
def next_main():
    global search_parameters, df, graph_type, display_count

    display_count[0] += 1



    if graph_type == "solid":

	histogram_values, display_labels, table_string = generate_histogram(df, search_parameters, display_count[0])
	return render_template("summary_histogram.html", histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])
    elif graph_type == "stack":

        histogram_values, display_labels, table_string = generate_stacked_histogram(df, search_parameters, display_count[0])
	return render_template("summary_stacked_histogram.html", histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])

@app.route("/previous", methods=["POST", "GET"])
def previous_main():
    global search_parameters, df, graph_type, display_count

    display_count[0] -= 1


    if graph_type == "solid":

	histogram_values, display_labels, table_string = generate_histogram(df, search_parameters, display_count[0])
	return render_template("summary_histogram.html", histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])
    elif graph_type == "stack":

        histogram_values, display_labels, table_string = generate_stacked_histogram(df, search_parameters, display_count[0])
	return render_template("summary_stacked_histogram.html", histogram_data = histogram_values, search_list = search_parameters, display_count = display_count, display_labels = display_labels, table_values = [table_string])


#============================================Old Functions that do not work==========================================

def staasdasdcked_label_change(sums_dict):
    '''Changes the label for the system names ot abbreviated version, to make it fit bettwe when
    displayed on a stacked column histogram.
    '''
    alternate_label_dict = {"graphlab-sync-auto-itr":" GL-S-A-I ", "graphlab-sync-random-itr":" GL-S-R-I ", "graphlab-async-random-tol":" GL-A-R-T ", "graphlab-sync-random-tol":" GL-S-R-T ", "graphlab-sync-auto-tol":" GL-S-A-T ", "graphlab-async-auto-tol":" GL-A-A-T ", "graphlab-sync-auto": " GL-S-A ", "graphlab-sync-random":" GL-S-R ", "spark-itr": "  S-I  ", "spark-tol" : "  S-T  ", "giraph":"   G   ", "blogel-Vertex":"  B-V  ", "vertica":"   V   "}

    new_sums_dict = {}
    for key in sums_dict:
	new_sums_dict[alternate_label_dict[key[:-1]] + key[-1]] = sums_dict[key]
    return new_sums_dict




def create_total_time_treeNotInUse(data_tree):

    children = data_tree.children

    if type(children[0]) != Tree:
	values = child[0].values
      	if values[-2][0] == 'nan':
		pass
	else:
	    graph_data = []
	    #Calls the values from the data frame and also the labels along the top
            data_lines = child[0].values()
	 
            total_time_dict = calculate_total_time(data_lines)
            all_keys = total_time_dict.keys()
	    for key in all_keys:
		grap_data.append({'x':key, 'y':total_time_dict[key]})
            
            data_tree.children = graph_data 
			    
    else:
	for child in children:
	    create_total_time(child)






def create_frame_treeNotInUse(df, search_param):

    data_frame_tree = Tree('HEAD')

    all_workloads = search_param[0]
    all_datasets = search_param[1]
    all_clusters = search_param[2]
    all_systems = search_param[3]


    for workload in all_workloads:
        modified_df = df[df["Workload Names"] == workload]

	work_tree = Tree(workload)
	data_frame_tree.append(work_tree)

	for data in all_datasets:
	    modified_df = modified_df[modified_df["Dataset"] == data]

	    data_tree = Tree(data)
            work_tree.append(data_tree)

	    for cluster in all_clusters:
		modified_df = modified_df[modified_df["Cluster Size"] == cluster]

	        cluster_tree =Tree(cluster)
		data_tree.append(cluster_tree)

		for system in all_clusters:
		    if system != 'None':
		    	modified_df = modified_df[modified_df["System Name"] == system]

		    	system_tree = Tree(system)
			system_tree.append(modified_df)
			cluster_tree.append(system_tree)
		    else:
		        cluster_tree.append(modified_df)	    
		   
    return data_frame_tree

def search_data_frame_NotInUse(df, search_keys, search_values):
    '''Takes a data frame and creates alist of different versions of that data frame, depending on teh search values
    inputted. Returns a list of different variations of a data frame.'''
    
    output_list = []
    for index in range(len(key_list)):
	if value_list[index] != '':
	    df = df[df[Key_list[index]] == value_list[index]]
    return df

def new_search_data_frame_NotInUse(df, search_list):
    
    output_list = []
    
    for workload in search_list[0]:
	new_df = df[df["Workload Name"] == workload]
	
	for dataset in search_list[1]:
	    before_data_search = new_df
	    new_df = df[df["Dataset"] == dataset]
 	    
	    for cluster in search_list[2]:
		before_cluster_search = new_df
		new_df = df[df["Cluster Size"] == cluster]

		for system in search_list[3]:
		    previous_df = new_df 
		    new_df = df[df["System Name"] == system]
		    output_list.append(new_df)

		    new_df = previous_df
		new_df = before_cluster_search
	    new_df = before_data_search     
        new_df = df
		    
    return output_list		    

def calculate_total_time_NotInUse(df_list): #OLD VERSION
    '''Takes a list of data frames, this will calculate the total time it took to run a test. Then
    it will return a list nested with dictonaries formatted so taht it is possible to make histograms'''

    histogram_list = []
    test_names = df.index
    test_times = df.values
    for df in df_list:
	for index in range(len(test_names)):
	    times_sum = 0
	    for num in test_times[index][-2]:
		times_sum += int(num)
	    histogram_list.append({'x' : test_names[index], 'y' : times_sum})
    return histogram_list

def new_calculate_total_time_NotInUse(df_list): 
    '''Takes a list of data frames, this will calculate the total time it took to run a test. Then
    it will return a list with nested dictonaries where the key are the x-axis and values are the total test times'''
    histogram_list = []

    for df in df_list:
        histogram_dict = {}
	horizontal_labels = df.index
	result_values = df.values

        for index in range(len(test_labels)):
	    total_time = sum(result_values[index][-2]) #Creates a total time for the current dataframe
	    
	    if horizontal_labels[index] in histogram_dict:
		histogram_dict[horizontal_labels[index]] = total_time
	    else:
		histogram_dict[horizontal_labels[index]] += total_time
            
        histogram_list.append(histogram_dict)

    return(histogram_list)


def create_histogram_dictonary_NotInUse(histogram_list):
    '''histogram_list which is a list nested with dictionaries. The function will return another
    list nested lested with list which will be in the form of such that a histogram can be created'''

    output_list = [] 
    for diction in histogram_list:
        current_histgram = []
	all_keys = diction.keys()
	for key in all_keys:
	    pass
#	    current_histogram.append( {'x' : key}, 'y' : diction[key]} ) #This line doesn't work syntax error
        output_list.append(current_histogram)
    
    return output_list
		
	    


    
if __name__ == '__main__':
    app.run(debug=True)
