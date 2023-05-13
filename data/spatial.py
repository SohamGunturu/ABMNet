# problem with the code is that the spatial data can only be run on the cluster, because it's so massive, which means we can't run anything locally
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from pathlib import Path
from textwrap import wrap
import sys
import os
import pickle
import torch 
from torch_geometric.data import Data 
from scipy import spatial

# each spatial object has 3 specific components
# 1 set of rate constants that generated the data
# a initial set of conditions (sample)
# a final set of conditions (sample)
# input: directory name
class SpatialObj():
    # dirname = parameters_x_y_z_f
    def get_rates(dirname : str):
        prefix = "parameters"
        separator = "_"
        path_separated = dirname.split('/')
        rates_string = ""
        for word in path_separated:
            if prefix in word:
                rates_string = word[word.rindex(prefix):]
        
        rates = rates_string.split(separator)
        return np.array([float(i) for i in rates[1:]])
    
    # list where each entity is a tuple of 2 time pts (for now and simplicity).
    def get_time_data(dirname : str):
        sample_dirs = [os.path.join(dirname, x) for x in os.listdir(dirname)]
        data = []
        for dir in sample_dirs:
            file_i = os.path.join(dir, "dump.2D_model.0")
            file_t = os.path.join(dir, "dump.2D_model.1")
            if dirname != dir and os.path.isfile(file_t) and os.path.isfile(file_i):
                # dump 
                dump_i = SpatialObj.process_dump_file(file_i)
                dump_t = SpatialObj.process_dump_file(file_t)
                # translate
                data_i = SpatialObj.translate_to_img(dump_i)
                data_t = SpatialObj.translate_to_img(dump_t)
                # append
                data.append((data_i, data_t))
            
        # return
        return data
            
    def process_dump_file(file):
        # eliminate all 11 lines until the matrix
        f = open(file, "r")
        lines = f.readlines()
        lines = lines[11:]
        # load remaining matrix into numpy
        data = np.array([np.fromstring(i, sep=" ") for i in lines])
        f.close()
        # return
        return data
        
    #Pixel, Cytotoxic CD8+ T Cells, Cancer, Exhausted CD8+ T Cells, Dead Cancer Cells, Ignore, Ignore, TAMs, Ignore
    #  matrix[x,y,feature]
    def translate_to_img(matrix, width=100, features=9):
        # convert indices in far left column to 
        # get some tensor feature
        organized = np.zeros((width, width, features))
        for i in range(matrix.shape[0]):
            column = (i+1) % width
            row = int((i) / width)
            organized[row,column] = matrix[i,1:]
        
        return organized
        
    def __init__(self, dirname : str):
        self.dir = dirname
        self.rates = SpatialObj.get_rates(dirname)
        self.data = SpatialObj.get_time_data(os.path.join(dirname,"06RD_responder/")) 
        self.n_samples = len(self.data)
        

class GiuseppeSpatialDataProcessor():
    def __init__(self, path, single_initial_cond = True):
        # each spatial object contains a set of parameters 
        self.path = path
        self.spatialData = GiuseppeSpatialDataProcessor.get_spatial_objs(path)
        
    def get_spatial_objs(path : str, single_initial_cond = True):
        parameter_dirs = [os.path.join(path,x) for x in os.listdir(path)]
        spatialObjs = []
        for dir in parameter_dirs:
            print(dir)
            if dir != path and "parameter" in dir:
                obj = SpatialObj(dir)
                spatialObjs.append(obj)
        return spatialObjs    
    
    # it will convert all of the objects in the data structure into a dictionary, and then save as a pickle file once done. 
    # Probably should've been done this way originally we can keep things clean.
    def convert_to_pickle(self, path="file.pickle"):
        dictionary = {} # every key will be the set of rate constants and every value is a list of 30 tuples of (in, out)
        for obj in self.spatialData:
            dictionary[obj.rates.tobytes()] = obj.data
        with open(path, 'wb') as handle:
            pickle.dump(dictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)

# come back to this once we can create a pickle file/ dictionary for Pytorch Geometric
class GiuseppeSurrogateGraphData():
    def __init__(self, single_initial_cond = True):
        self.input_graphs = [] # list of torch array of all features row by row, each row a node
        self.output_graphs = [] # list of torch array with each row a node as well.
        self.edges = [] # torch array of all edges 
        self.rates = []# list of rates we care about in torch
        self.single_init = single_initial_cond
    
    # lattice is a WxHxF tensor where F is the feature dimension size
    # return a python list of nodes
    def convert_lattice_to_node(lattice):
        nodes = [] # torch.zeros((lattice.shape[0] * lattice.shape[1], lattice.shape[2]))
        i = 0
        for r in range(lattice.shape[0]):
            for c in range(lattice.shape[1]):
                nodes.append(lattice[r,c])
        # bad code inbound
        nodes = np.array(nodes)
        return torch.from_numpy(nodes)
    
    def delaunay_edges_and_data(self, dictionary):
        for key in dictionary.keys():
            rates = np.frombuffer(key)
            lattice_shape = dictionary[key][0][0].shape
            
            coords = np.zeros((lattice_shape[0] * lattice_shape[1], 2))
            i = 0
            for r in range(lattice_shape[0]):
                for c in range(lattice_shape[1]):
                    # create array of 2D coordinates for triangulation
                    coords[i,0] = r
                    coords[i,1] = c
                    i+=1
            
            # now get the edges from delaunay triangulation that will be reused across all things
            tri = spatial.Delaunay(coords)
            edges = []
            for triangle in range(tri.simplices.shape[0]):
                # basically now need to go through each of simplices rows and convert them into 
                # edges are two-way, so have to re-iterate twice through.
                for coordinateIndex in range (tri.simplices.shape[1]):
                    for secondCoordinateIndex in range(coordinateIndex + 1, tri.simplices.shape[1]):
                        if coordinateIndex != secondCoordinateIndex:
                            edges.append([tri.simplices[triangle, coordinateIndex], tri.simplices[triangle, secondCoordinateIndex]]) # use same set of edges each time
            
            self.edges = torch.FloatTensor(edges)      
            # now append all of the graphs in order with respect to the input and output data
            for sample in dictionary[key]: 
                initial_lattice = sample[0]
                final_lattice = sample[1]
                self.rates.append(torch.from_numpy(rates)) # yes there will be duplicate rates, but we need to stay consistent with indexing.
                self.input_graphs.append(GiuseppeSurrogateGraphData.convert_lattice_to_node(initial_lattice))
                self.output_graphs.append(GiuseppeSurrogateGraphData.convert_lattice_to_node(final_lattice))
                        
        if self.single_init: # what if we only need one of the initial conditions
            self.input_graphs = self.input_graphs[0]

    # create a pickle data structure for all the Y stuff
    # since we are not memory constrained just yet, we can simply load it on the cluster no need 
    # to do fileIO for now. 
    def save(self, path):
        print("Saving Graph Data to PKL")

parent_data_dir = "../../share/Giuseppe_John/training_data_with_dump_files_ParamSweep_11-03-2023_30_samples/"
# parent_data_dir = "data/spatial/"

# test = GiuseppeSpatialDataProcessor(parent_data_dir)
# print(test.spatialData[0].rates)
# print(test.spatialData[1].rates)
# print(test.spatialData[0].data[0][0])
# test.convert_to_pickle("../gdag_test.pickle")
loadedDict = pickle.load(open("../gdag_test.pickle","rb"))
testDataConverted = GiuseppeSurrogateGraphData()
testDataConverted.delaunay_edges_and_data(loadedDict)

# loadedDict = pickle.load(open("data/spatial/test.pickle","rb"))
# for keys in loadedDict.keys():
#     print(np.frombuffer(keys))

# load one set of parameter rate constants in, 



# Currently data looks something a little like this, 
# parent_data_dir
#    parameters_xyz_
#       06rd thing
#           -t=0 matrix file (with need to calculate coordinates and convert into a separate matrix)
#           -t=1 matrix file
#           


# need to figure out how to convert it all into one ginormous data .csv file for sake of being used to the format (??)
# 