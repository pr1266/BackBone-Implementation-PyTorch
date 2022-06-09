import torch
import torch.nn as nn
import math

class PrintLayer(nn.Module):
    def __init__(self, type, index):
        super(PrintLayer, self).__init__()
        self.type = type
        self.index = index

    def forward(self, x):
        print(f'size of {self.type} layer {self.index} : {x.size()}')
        return x

base_model = [
    #! expand_ratio, channels, repeats, stride, kernel_size
    [1, 16, 1, 1, 3],
    [6, 24, 2, 2, 3],
    [6, 40, 2, 2, 5],
    [6, 80, 3, 2, 3],
    [6, 112, 3, 1, 5],
    [6, 192, 4, 2, 5],
    [6, 320, 1, 1, 3],
]

phi_values = {
    #! tuple of: (phi_value, resolution, drop_rate)
    "b0": (0, 224, 0.2),  #! alpha, beta, gamma, depth = alpha ** phi
    "b1": (0.5, 240, 0.2),
    "b2": (1, 260, 0.3),
    "b3": (2, 300, 0.3),
    "b4": (3, 380, 0.4),
    "b5": (4, 456, 0.4),
    "b6": (5, 528, 0.5),
    "b7": (6, 600, 0.5),
}

class CnnBlock(nn.Module):
    #! agha age group=1 bashe cnn mamoolie
    #! age be andaze in_channels bashe, mishe DepthWise conv
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, groups=1):
        super(CnnBlock, self).__init__()
        self.cnn = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, groups=groups)
        self.bn = nn.BatchNorm2d(out_channels)
        self.silu = nn.SiLU()

    def forward(self, x):
        return self.silu(self.bn(self.cnn(x)))

class SqueezeExcitation(nn.Module):

    def __init__(self,):
        super().__init__()

class InvertdResidualBlock(nn.Module):

    def __init__(self):
        super().__init__()

class EfficientNet(nn.Module):

    def __init__(self):
        super().__init__()