from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('reader_main.html')

@app.route('/display', methods=['POST','GET'])
def read():
    file_name = request.form['file_box']
    infile = open(file_name, 'r')
    numbers = infile.readlines()
    infile.close()
    string = ''
    
    data = find_occurance(numbers)
    data = processable_list_conversion(data)
    print(type(data))
    for num in numbers:
        string += num.rstrip() + ', '
    
  
    #return render_template('reader_histogram.html', numbers=string, number_data = map(json.dumps, data))
    return render_template('reader_histogram.html', numbers=string, number_data = data)
    

def find_occurance(list):
    """Takes in a list of numbers that are represented through either strings or numbers.
    It will return dictionary, where the key is a number and the value is an integer that
    represents the occurance of that number in the list."""
    
    occurances = {}
    for num in list:
        if num in occurances:
	    occurances[num] += 1
        else:
            occurances[num] = 1

    return occurances

def processable_list_conversion(dict):
    """Takes in a dictionary, where key is a number and value is occurance of that number.
    This will return a list with nested dictionaries with eaching containing only two keys
    x, and y. This is so that it can be processed in the html file.

    Example
    { 1 : 4, 2 : 4, 3 : 5} --> [{x:1, y:4}, {x:2:, y:4}, {x:3, y:5}]"""
        
    processed_list = []
    
    for num in dict:
	processed_list.append({'x':int(num), 'y':dict[num]})
    
    return processed_list

   
if __name__ == '__main__':
    app.run(debug=True)
