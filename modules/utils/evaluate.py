import torch
import time
from modules.models.temporal import *
from modules.models.spatial import *
from modules.models.simple import *



# return MSE metric of moments for simple MLPs
# %%
def evaluate(model, dataset, use_gpu = False):
    
    criterion = nn.MSELoss()
    if tc.cuda.is_available() and use_gpu:
        device = tc.device("cuda")
        model = model.cuda()
        criterion = criterion.cuda()
        using_gpu = True
    else:
        device = tc.device("cpu")
        using_gpu = False

    print(f"Using GPU: {using_gpu}")
    model.eval()
    loss = 0
    start_time = time.time()
    predicted = []
    tested = []
    for ex in range(len(dataset)):
        sample = dataset[ex]
        input = sample[0]
        output = sample[1]
        prediction = model.forward(input.to(device))
        loss += criterion(prediction.squeeze(), output.squeeze().to(device))
        tested.append(output.cpu().detach().numpy())
        predicted.append(prediction.cpu().detach().numpy())
        
    return loss.cpu().detach().numpy() / len(dataset), time.time() - start_time, np.array(predicted), np.array(tested)


def evaluate_temporal(data, model : TemporalComplexModel, criterion, device):
    predicted = []
    truth = []
    test_dataloader = torch.utils.data.DataLoader(data, batch_size=None, shuffle=False)
    test_loss = 0
    model.eval()
    with torch.no_grad():
        hidden = (torch.zeros(model.n_layers, model.hidden_dim).detach(), torch.zeros(model.n_layers, model.hidden_dim).detach())
        for rates, input, output in test_dataloader:
            out, hidden = model(input.to(device).float(), (hidden[0].detach().to(device), hidden[1].detach().to(device)), rates.to(device).float())
            test_loss += criterion(out.squeeze(), output.to(device)).cpu().detach()
            predicted.append(out.cpu().numpy())
            truth.append(output.cpu().numpy())
    
    
    return test_loss.cpu().detach().numpy(), np.array(truth), np.array(predicted)
    

# Given the first t_observed inputs, generate future trajectories using its own predictions. Then compare and contrast.
# returns a matrix of predicted sequences, the mse, and the ground truth sequence, the times used as input for generation.
def generate_temporal(data, model : TemporalComplexModel, criterion, device, t_observed):
    predicted = []
    truth = []
    test_dataloader = torch.utils.data.DataLoader(data, batch_size=None, shuffle=False)
    test_loss = 0
    model.eval()
    i = 1
    with torch.no_grad():
        time_start = time.time()
        for rates, input, output in test_dataloader:
            pred, loss = generate_temporal_single(input, rates, output, model, criterion, device, t_observed)
            truth.append(output.cpu().numpy()) # matrix of just ground truths.
            test_loss += loss / len(data)
            predicted.append(pred)
            if i % 10 == 0:
                print("Time For 10 Sequences of Generation:", time.time() - time_start)
                time_start = time.time()
            i += 1
    return test_loss.cpu().detach().numpy(), np.array(truth), np.array(predicted)


# recursively generates data and computes a loss
def generate_temporal_single(input, rates, output, model, criterion, device, t_observed):
    test_loss = 0
    predicted = []
    truth = [] # let's actually make our lives easier by simply just returning the matching truth element
    hidden = (torch.zeros(model.n_layers, model.hidden_dim).detach(), torch.zeros(model.n_layers, model.hidden_dim).detach())
    # feed it first t_observed time points
    # print(input[:t_observed].size())
    curr = input[:t_observed].to(device).float() # current input of time points that the RNN might see.
    out, hidden = model(curr, (hidden[0].detach().to(device), hidden[1].detach().to(device)), rates.to(device).float())
    test_loss += criterion(out.squeeze(), output[:t_observed].to(device)).cpu().detach()
    # print("out:", out.size())
    predicted.append(out[-1].cpu().numpy())
    # now let's recursively generate given the new out and hidden units until we run out of space. Keep in mind, this only works for the output here.
    # note we need to offset by 1 to make sure the MSEs are aligned
    for t in range(1, output.size()[0] - t_observed + 1): # account for the missing one.
        # print(curr.size())
        # print(out[-1].size())
        curr = torch.cat([curr[1:],out[-1]])
        out, hidden = model(curr.float().squeeze(), (hidden[0].detach().to(device), hidden[1].detach().to(device)), rates.to(device).float())
        predicted.append(out[-1].cpu().numpy()) # so I can keep track of all the predictions
        test_loss += criterion(out.squeeze(), output[t:t+t_observed].to(device)).cpu().detach()

    # print(predicted)
    predicted = np.array(predicted)
    predicted = predicted.flatten()
    return predicted, test_loss 
    
    
