import os.path
from flask import Flask, render_template, request, url_for
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('get_file.html')




@app.route('/display', methods=['POST','GET'])
def process():
    file = request.form['file_box']

    search_list_values = [request.form['system_box'], request.form['dataset_box'], request.form['cluster_box'], request.form['workload_box']]
    search_list_keys = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name']
#When the text boxes are blank it causes a 400 error need to think of a fix for this
    
#    search_list['system'] = request.form['system_box']
#    search_list['dataset'] = request.form['dataset_box']
#    search_list['dataset'] = '32'
#    search_list['cluster'] = request.form['cluster_box']
#    search_list['workload_box'] = request.form['workload_box']    

    if not os.path.isfile(file):
	return render_template('error.html')
    
    infile = open(file, 'r')
    file_lines = infile.readlines()
    infile.close()
    print(file_lines)
    print('______________________________________________________________________')
    parameter_list = create_parameter_list(file_lines)
    print(parameter_list)
    print('______________________________________________________________________') 
    new_parameter_list = convert_to_df_list(parameter_list)
    print(new_parameter_list)
    print('______________________________________________________________________') 
    #df = create_data_frame(parameter_list) would crash if there was more test than there was parameters
    df = create_data_frame(new_parameter_list)
    print(df)
    print('______________________________________________________________________') 

    df = search_data_frame(df, search_list_keys, search_list_values)
    print(df)
    print('______________________________________________________________________') 

    histogram_list = calculate_total_time(df)
    print(histogram_list)    
    print('______________________________________________________________________') 


    return render_template('histogram.html', data = histogram_list)
    

#Old version    
def create_parameter_list1(file_lines):
    '''Takes in a list where each index is a single line in a text, file where each line represent the full set of data.
    It will return a nested list where each index represents an entire row of in the data frame'''
 


    output_list = []

    for line in file_lines:
	data_list = line.split()
        
        output_list.append([data_list])


    return output_list

#New version This is to convert parameter ot have it's on list where index corrispond to a single test
def create_parameter_list(file_lines):
    '''Takes in a list where each index represents a line in text file. On each line it will have parameters of a test case
    each parameter will be seperated by a space. This will put each value of a the same parameter in a list. returns
    a nested list where each index is a parameter list'''

    output_list = []

    for line in file_lines:
	data_list = line.split()
        data_list[-1] = data_list[-1].split('/')
	if output_list == []:
	    for index in range(len(data_list)):
		output_list.append([data_list[index]]) 
	else:
	    for index in range(len(data_list)):
		output_list[index].append(data_list[index])
    
    return output_list

def convert_to_df_list(parameter_list):
    '''Parameter_list is a nested list where each index is a parameter or infomation of a test that was done.
    This will make it so that it is easier to just put the program into one thing'''
    
    output_list = []
    for index in range(len(parameter_list[0])):
	test_list = []
	for parameter in parameter_list:
	    test_list.append(parameter[index])
        output_list.append(test_list)

    return output_list

#Will crash if ther are more test than there are parameters
def create_data_frame(data_list):
    '''Takes a nested list, which will create a data frame using that data.'''
    
    horizontal_labels  = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name', 'Number of Execution', 'Run Times']
    vertical_labels = []
    for test_num in range(len(data_list)):
	vertical_labels.append('Test ' + str(test_num + 1))


    df = pd.DataFrame(data_list, index = vertical_labels, columns = horizontal_labels)
    return df

def create_data_frame_hello(data_list):
    '''Takes a nested list, which will create a data frame, using that data.'''
    horizontal_labels  = ['System Name', 'Cluster Size', 'Dataset', 'Workload Name', 'Number of Execution', 'Run Times']
    
    vertical_labels = []
    for test_num in range(len(data_list)):
        vertical_labels.append('Test ' + str(test_num + 1))

    df = pd.DataFrame(data_list, index = vertical_labels , columns = horizontal_labels)


#This one is not being used as it, scripted for dicitonaries which don't work for some reason
def search_data_frameoutofuse(df,search_dict):
    '''Takes in a data frame object, and a dictionary where the key is the column and the value is what the user is looking
    for. If the value of the a certian key is a null string it will not search of a null stiring. Returns altered Data
    Frame.'''
    
    for key in search_dict:
	if search_dict[key] != '':
	    
	    df = df[df[key] == search_dict[key]]
    print(df)
    return df

#This one is scripted for list
def search_data_frame(df, key_list, value_list):
    '''Takes in two key_list contains columns to search by, and value_list contains what values of those columns to search by.
    Returns a data frame that only contains the desired values'''
    for index in range(len(key_list)):
	if value_list[index] != '':
	    df = df[df[key_list[index]] == value_list[index]]
    print(df)
    return df

def calculate_total_time(df):
    '''Takes in a data frame object. It will take the last column of each of the test in the data frame which is an arrary of times
    it will calculate the total time it too to run the test and output into a form so that it can be represented as a
    histogram'''
    
    histogram_list = []
    test_names = df.index
    test_times = df.values
    print(test_names)
    print(test_times)
    for index in range(len(test_names)):
	#times_sum = sum(test_times[index][-1])	#adds all of the values in the time portion of the data frame///Change this doesn't work because the numbers are still strings
        
        times_sum = 0
        for num in test_times[index][-1]:
	    times_sum += int(num)

        histogram_list.append({'x':test_names[index], 'y':times_sum})
    print(histogram_list)    
    return histogram_list     

if __name__ == '__main__':
    app.run(debug=True)
