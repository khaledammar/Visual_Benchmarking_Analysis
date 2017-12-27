import ast

def string_to_list(all_lines):
    output_list = []

    for line in all_lines:
        if line != '\n':

            new_line = line.rstrip()
            print(new_line)
            new_line = ast.literal_eval(new_line)
            output_list.append(new_line)

    return output_list

def my_string_to_list(all_lines):
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
                line[index] = line[index].split(', ')

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
    for param in output_list[0]:
        if type(param) == list:
            for num in param:
                print(num, 'inside a list', type(num))
        else:
            print(param, type(param))



def find_values(nested_list, index):
    ocurance_list = []
    for line in nested_list:
        if line != '\n' and line[index not in ocurance_list]:
            ocurance_list.append(line[index])

    return ocurance_list




infile = open('summary.txt', 'r')
all_lines = infile.readlines()
infile.close()

my_string_to_list(all_lines)

'''
list_all_lines = string_to_list(all_lines)
all_values = find_values(list_all_lines, int(0))
print(all_values)
'''
