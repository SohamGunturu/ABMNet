import pandas as pd 
import numpy as np
import os 
import torch
import pickle

import re
def is_number_less_than_threshold(string, threshold):
    # Extract the number from the string using regular expressions
    number = re.findall(r'\d+', string)
    # print(number)
    if number:
        isLess = True
        for num in number:
            num = int(num)  # Convert the extracted number to an integer
            isLess = isLess and  num < threshold and len(number) > 1
        # print(isLess)
        return isLess
    else:
        return False  # If no number is found in the string


def extract_number(string):
    # Extract the number from the string using regular expressions
    number = int(re.findall(r'\d+', string)[1])
    return number

def sort_strings_with_numbers(strings):
    # Sort the strings based on the extracted numbers
    sorted_strings = sorted(strings, key=extract_number)
    return sorted_strings

# from modules.data.spatial import *
def write_array_to_csv(array, column_labels, file_path):
    # Create a DataFrame from the array and column labels
    df = pd.DataFrame(data=array, columns=column_labels)

    # Write the DataFrame to a CSV file
    df.to_csv(file_path, index=False)

pso_steps = 9
parent_dir = "data/l3p_pso"
output_path = "data/static/l3p_pso_s" +str(pso_steps) + ".csv"
# parent_dir = "data/John_Indrani_data/zeta/training_kon_koff"
parameter_dirs = [os.path.join(parent_dir,x) for x in os.listdir(parent_dir)]
# print(parameter_dirs)

rates = []
output = []
# keep one vector of the time steps too just in case.
times = []
# basically check to make sure that the number inside of the dir name is less than 5.
moms = []
params = []
for dir in parameter_dirs:
    if dir != parent_dir and ".csv" in dir and is_number_less_than_threshold(dir,pso_steps):
        print(dir)

        data = np.loadtxt(dir, delimiter=",")
        if "_moms" in dir:
            moms.append(dir)
            # for i in range(data.shape[0]):
                # output.append(data[i])
        elif "_params" in dir:
            params.append(dir) 
            # for i in range(data.shape[0]):
                # rates.append(data[i])
        
print("---------------")
moms = sort_strings_with_numbers(moms)
params = sort_strings_with_numbers(params)

for n in range(len(moms)):
    print(moms[n])
    print(params[n])
    moments = np.loadtxt(moms[n], delimiter=",")
    param = np.loadtxt(params[n], delimiter=",") 
    for i in range(moments.shape[0]):
        output.append(moments[i])
        rates.append(param[i])
        
        # if len(times) < 1:
        #     times = data[1:,0] # keep for plotting

# save into tensors and a dictionary
# tosave = {}
# rates_tensors = []
# output_tensors  = []
# for i in range(len(rates)):
#     if np.sum(output[i]) > 0:
#         rates_tensors.append(torch.from_numpy(rates[i]))
#         output_tensors.append(torch.from_numpy(output[i]))    
# tosave["rates"] = rates_tensors
# tosave["outputs"] = output_tensors
# tosave["time_points"] = times
# with open(output_path, 'wb') as handle:
#     pickle.dump(tosave, handle, protocol=pickle.HIGHEST_PROTOCOL)


rates = np.array(rates)
output = np.array(output)
# now let us create a dictionary for the dataset where each entity in the list is some time-series evolution 
print(rates.shape)
print(output.shape)

# # for simplicity, we'll just do counts for now, and save into a specific dataset
# output_file = "data/static/indrani_t400.csv"
# time_point = 400
# matrix with inputs and outputs
labels = []
for i in range(1, rates.shape[1] + 1):
    labels.append("k" + str(i))

for o in range(1, output.shape[1] + 1):
    labels.append("o" + str(o))

output_data = np.zeros((rates.shape[0], rates.shape[1] + output.shape[1]))
output_data[:,:rates.shape[1]] = rates
output_data[:,rates.shape[1]:] = output   
write_array_to_csv(output_data, labels, output_path) 