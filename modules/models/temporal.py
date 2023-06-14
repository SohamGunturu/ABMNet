import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from modules.models.simple import *
from modules.models.spatial import *
from modules.data.temporal import *
class TemporalModel(nn.Module):
    def __init__(self, input_size, output_size, hidden_dim, n_layers):
        super(TemporalModel, self).__init__()

        # Defining some parameters
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers

        # Defining the layers
        # RNN Layer
        self.lstm = nn.LSTM(input_size, hidden_dim, n_layers, batch_first=False)  
        # Fully connected layer
        self.fc = nn.Linear(hidden_dim, output_size)
   
    def forward(self, x, hidden):

        # Initializing hidden state for first input using method defined below
        # hidden = self.init_hidden()

        # Passing in the input and hidden state into the model and obtaining outputs
        out, hidden = self.lstm(x, hidden)

        # Reshaping the outputs such that it can be fit into the fully connected layer
        # out = out.contiguous().view(-1, self.hidden_dim)
        out = self.fc(out)
       
        return out, hidden

class TemporalComplexModel(nn.Module):
    def __init__(self, input_size, hidden_dim, n_layers, n_rates):
        super(TemporalComplexModel, self).__init__()

        # Defining some parameters
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        self.input_size = input_size
        print(type(n_layers))
        print(n_layers)
        # Defining the layers
        # RNN Layer
        self.lstm = nn.LSTM(input_size, hidden_dim, n_layers, batch_first=True)  
        # Fully connected MLP layer
        self.encoder = EncoderLayer(n_rates, hidden_dim, hidden_dim)
        
        self.fc = NeuralNetwork(hidden_dim*2, hidden_dim, depth=3, output_size=input_size)
   
    def forward(self, x, hidden, rates):

        # Initializing hidden state for first input using method defined below
        # hidden = self.init_hidden()
        # Passing in the input and hidden state into the model and obtaining outputs
        out, hidden = self.lstm(x.unsqueeze(dim=1), hidden)
        out = torch.cat((out, self.encoder(rates).repeat(out.size()[0]).reshape((out.size()[0], self.hidden_dim))), dim=1)
        # Reshaping the outputs such that it can be fit into the fully connected layer
        # out = out.contiguous().view(-1, self.hidden_dim)
        out = self.fc(out)

        return out, hidden

