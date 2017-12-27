from flask import Flask, render_template, request, redirect, url_for

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
    #payload = {}
    #for index in range(len(numbers)):
    #     payload['key'+str(index)] = numbers[index].rstrip()
    for number in numbers:
        string += number.rstrip() + ', '
    return render_template('reader_output.html', paragraph=string)

if __name__ == '__main__':
    app.run(debug=True)
