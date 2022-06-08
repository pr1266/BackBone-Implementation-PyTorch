import torch
import  torch.nn as nn

#! agha leNet tasvir 32*32 migire
#! too laye conv aval: 28 * 28 * 6 (kernel size 5, padding 0, stride 1)
#! baad average pooling  layer ba kernel size 2 va stride 2
#! ke size ro mikone 14 * 14 * 6 (too pooling layer tedad channel ha sabete)
#! conv 2vom ein e conv aval kernel size 5, padding 0 va stride 1
#! ke size ro mikone 10 * 10 * 16
#! dobare avg pooling zade shode 5 * 5 * 16
#! baad conv zade 120 ta channel dare 1 * 1 baad flatten mizane o miad
#! roo FC va tamam. kheili simple :)

class leNet(nn.Module):

    def __init__(self):
        super(leNet, self).__init__()
        self.relu = nn.ReLU()
        self.pool = nn.AvgPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.conv1 = nn.Conv2d(
            in_channels=1, 
            out_channels=6, 
            kernel_size=(5, 5), 
            stride=(1, 1), 
            padding=(0, 0)
        )        
        self.conv2 = nn.Conv2d(
            in_channels=6, 
            out_channels=16, 
            kernel_size=(5, 5), 
            stride=(1, 1), 
            padding=(0, 0)
        )
        self.conv3 = nn.Conv2d(
            in_channels=16, 
            out_channels=120, 
            kernel_size=(5, 5), 
            stride=(1, 1), 
            padding=(0, 0)
        )
        self.linear1 = nn.Linear(
            in_features=120, 
            out_features=84
        )
        self.linear2 = nn.Linear(
            in_features=84,
            out_features=10
        )
