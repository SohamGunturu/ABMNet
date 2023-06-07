from modules.data.temporal import *
from modules.models.temporal import *
from modules.utils.train import *
from modules.utils.evaluate import *
from sklearn.model_selection import KFold
import torch


data = TemporalDataset("data/time_series/indrani.pickle")
print(len(data))
# REMINDER: no cross-validation just yet, we will cross-validate next week!!
# NEED TO REMIND OURSELVES TO WRITE MORE MODULAR CODE SUCH THAT IT IS EASY FOR US TO RUN CROSSVALIDATION

hidden_sizes = [64, 128, 256]
lrs = [0.01, 0.001, 0.0001]
range_epochs = [25, 50, 75]
range_layers = [2,3,5]

# hidden_sizes = [64]
# lrs=[0.01]
# range_epochs = [25]
# range_layers = [2]

# original just to test parameters
# hidden_size=128
# lr=0.001
# n_epochs=50
# n_layers=3
K = 3
kf = KFold(n_splits=K, shuffle=True, random_state=42) # seed it, shuffle it again, and n splits it.
best_hidden_size = 0
best_lr = 0
best_epochs = 0
best_layers = 0

# split into train and test
train_size = int(0.8 * len(data))
test_size = len(data) - train_size
train_data, test_data = tc.utils.data.random_split(data, [train_size, test_size])


min_val_loss = 2114218412401248 # cheap max
for hidden_size in hidden_sizes:
    for lr in lrs:
        for n_epochs in range_epochs:
            for n_layers in range_layers:
                k_val_loss = 0
                for fold, (train_index, test_index) in enumerate(kf.split(train_data)):
                    k_train = tc.utils.data.Subset(train_data, train_index)
                    k_val = tc.utils.data.Subset(train_data, test_index)
                    model, device = train_temporal_model(k_train, data.input_size, data.n_rates, hidden_size, lr, n_epochs, n_layers, path="")
                    criterion = torch.nn.MSELoss().to(device)
                    # evaluate on test_data and see how much error we get. In particular, we want to 
                    # display the average and standard deviation of error of each time-series in the test-dataset
                    val_loss, truth, predicted = evaluate_temporal(k_val, model, criterion, device)
                    k_val_loss += val_loss / K
                    
                if k_val_loss  < min_val_loss:
                    print("New Minimum Average Test Loss:", k_val_loss)
                    print("For hsize, lr, n_epochs, n_layers")
                    print(hidden_size, " ",lr , " ",n_epochs, " ", n_layers)
                    best_hidden_size = hidden_size
                    best_lr = lr 
                    best_epochs = n_epochs
                    best_layers = n_layers
                    plot_time_series_errors(truth, predicted, data.times[1:], path="graphs/temporal/validation/errors_h" + str(hidden_size) +"lr" + str(lr) + "nEpc" + str(n_epochs) +"nlay" +str(n_layers) +".png")

# do some final training
model, device = train_temporal_model(train_data, best_hidden_size, best_lr, best_epochs, best_layers, "model/indrani_crossed.pt")
# now we evaluate!

