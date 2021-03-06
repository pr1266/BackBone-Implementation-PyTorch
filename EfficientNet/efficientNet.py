import torch
import torch.nn as nn
from math import ceil
import os

#! inja chand ta estelah darim aval:
#! depth scaling: agha ghabool darim harchi depth network
#! bishtar bashe va layer haye bishtari dashte bashim
#! accuracy mire bala tar pas age depth shabake ro bishtar konim
#! mishe depth scaling, hamoon tor ke too resNet dashtim (gradient vanishing)
#! hala ma layer hamoon ziade, dar natije, parameter hamoonam ziade
#! dar natije computation cost ziadi darim hala ino chetor hal konim?
#! efficient net mige ma faghat depth ro scale nemikonim, 1- depth, 2- width
#! va 3- resolution ro scale mikonim. roo resolution idashoon chie?
#! mige vaghti resolution ro bebarim bala detail e ghabel e extract
#! az tasvir mire bala. be ebarati more pixels more information and
#! complex features ## ye chi in vasat bezaram: DPI -> dots per inch:)
#! hala resolution ke mire bala bayad depth bere bala ke betoone khoob
#! feature extract kone. baad migim khob hala ma resolution ro x ta ziad
#! kardim, depth cheghad ziad she ke motanaseb bashe? in soalo dashte bashid felan (**1**)
#! width scaling chie? mige man channel haye conv ro bishtar mikonam va channel haro
#! wide tar mikonam. too paper behesh feature map ham gofte. khob tabiie
#! alan channel haro ziad tar konim dataye bishtar va feature haye bishtari
#! az tasvir mitoonim dararim. chera ino ziad mikonim? chon az oonvar resolution
#! rafte bala. hala width ro cheghadr ziad konim? inam soal 2vom(**2**)
#! hala asan efficientNet bar asas e in 2 ta soal va in 3 ta mafhoom dorost shode
#! efficient net ye series az model hast az b0 ta b7 ke b0 baseline model e
#! in b0 ba NAS be dast oomade neural architucture search ke nemidoonam chie
#! dar vaghea mige az rooye yek seri neural network dige sakhte shode
#! khob baraye pasokh dadan be in soal miaim barresi mikonim:
#! 4 ta parameter darim tooye in paper:
#! phi, alpha, beta va gamma
#? alpha -> depth scaling factor
#? beta -> width scaling factor
#? gamma -> resolution sacling factor
#! va ye scale factor darim : alpha . beta ^ phi . gamma ^ phi
#! in factor ha ba grid search dar miad
#! in phi ham compound scale factor ham behesh migan
#! hala fargh implementesh ine ke miad az inverted residual block
#! estefade mikone, in Inverted Residual Block chie?
#! too resNet va residual block ye feature map e Wide darim
#! ke ba conv miad laghar mishe (compress) va dar nahayat ba kernel size 1 channel
#! hasho dobare wide mikardim ta beshe size avalish
#! ama inja fargh dare. miad az narrow -> wide -> narrow estefade mikone
#! yani chi? miad channel haro ziad mikone, tahesh dobare kamesh mikone
#! va F(x) ro ba x jam mikone

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
    #! drop rate hamoon zarib e drop out e
    "b0": (0, 224, 0.2),
    "b1": (0.5, 240, 0.2),
    "b2": (1, 260, 0.3),
    "b3": (2, 300, 0.3),
    "b4": (3, 380, 0.4),
    "b5": (4, 456, 0.4),
    "b6": (5, 528, 0.5),
    "b7": (6, 600, 0.5),
}

#! inke cnnBlocke asan hichi
class CnnBlock(nn.Module):
    #! agha age group=1 bashe cnn mamoolie
    #! age be andaze in_channels bashe, mishe DepthWise conv
    #! hala depth wise conv chie?
    #! mige agha man miam be jaye inke hame filter haro ba kernel ha
    #! conv konam sigma begiram khorooji begiram, miam be tedad e filter ha
    #! ke mishe hamoon input depth, kernel dar nazar migirim, va nazir be nazir conv
    #! mikonim, inotri be shedat hajm mohasebat miad paiin
    #! in group ham dastanesh hamine darvaghe ba group tooye layer ha connection bein e input ha
    #! va weight haro control mikonim. age group == in_channel bashe
    #! har input ba ye set az kernel ha ke tedadeshoon barabar e ba out/in hast
    #! convolve mishan. va vaghti in va out yeki bashan daghighan mishe depthwise
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, groups=1):
        super(CnnBlock, self).__init__()
        self.cnn = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, groups=groups, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        #! activation function:
        self.silu = nn.SiLU()

    def forward(self, x):
        #! inam vazehe dige
        return self.silu(self.bn(self.cnn(x)))

#! az in squeeze Excitation too inverted residual block estefade mikonim:
#! in miad az filter ha ye seri etelaat global estekhraj mikone baad miad
#! ye seri computation anjam mide oon scaler value haro radif mikone baad miad
#! too input zarb mikone be onvan e khorooji
#! dar vaghe ba in kar darim channel haro scale mikonim
#! az har channel ye numeric value mashti dar miarim baad too
#! khod e filter ha zarb mikonim ta scale she
#! albate too paper SEnet az fully connected va relu estefade karde
#! in dashemoon az Conv nemidoonam chera
class SqueezeExcitation(nn.Module):

    def __init__(self, in_channels, reduced_dim):
        super(SqueezeExcitation, self).__init__()
        self.se = nn.Sequential(
            #! inja avg har filter ro migirim:
            nn.AdaptiveAvgPool2d(1), #! C * H * W ==> C * 1 * 1
            #! hala reduce mikonim (down sampling):
            nn.Conv2d(in_channels, reduced_dim, kernel_size=1),
            #! activation mizanim: (non-linearity effect)
            nn.SiLU(),
            #! va upsampling feature map ha:
            nn.Conv2d(reduced_dim, in_channels, 1),
            #! tahsham sigmoid
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        return x * self.se(x)

class InvertdResidualBlock(nn.Module):
    #! che mikone? ba 1*1 miad expand mikone (up-sampling)
    #! baad miad depthWise mizane
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, expand_ratio, reduction=4, survival_prob=0.8):
        super(InvertdResidualBlock, self).__init__()
        self.survival_prob = survival_prob
        #! shart residual block:
        self.use_residual = in_channels == out_channels and stride == 1
        hidden_dim = in_channels * expand_ratio
        self.expand = in_channels != hidden_dim
        reduced_dim = int(in_channels / reduction)

        if self.expand:
            self.expand_conv = CnnBlock(
                in_channels, hidden_dim, kernel_size=3, stride=1, padding=1,
            )

        self.conv = nn.Sequential(
            #! inja depthWise
            CnnBlock(
                hidden_dim, hidden_dim, kernel_size, stride, padding, groups=hidden_dim,
            ),
            #! inja squeeze Excitation:
            SqueezeExcitation(hidden_dim, reduced_dim),
            nn.Conv2d(hidden_dim, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
        )

    #! ye survival prob dar nazar migirim barsh
    #! baad ye random tolid mikonim
    #! age kamtar az prob bood oon residual block kolan drop mishe
    #! ein e drop out vali rooye kol e building block emal mishe
    def stochastic_depth(self, x):

        if not self.training:
            return x
        binary_tensor = torch.rand(x.shape[0], 1, 1, 1, device=x.device) < self.survival_prob
        return torch.div(x, self.survival_prob) * binary_tensor

    def forward(self, inputs):
        x = self.expand_conv(inputs) if self.expand else inputs

        if self.use_residual:
            return self.stochastic_depth(self.conv(x)) + inputs
        else:
            return self.conv(x)
    
class EfficientNet(nn.Module):
    def __init__(self, version, num_classes):
        super(EfficientNet, self).__init__()
        width_factor, depth_factor, dropout_rate = self.calculate_factors(version)
        last_channels = ceil(1280 * width_factor)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.features = self.create_features(width_factor, depth_factor, last_channels)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(last_channels, num_classes),
        )
    
    def calculate_factors(self, version, alpha=1.2, beta=1.1):
        #! aval miaim parameter haro az roo alpha va beta va phi hesab mikonim:
        phi, res, drop_rate = phi_values[version]
        depth_factor = alpha ** phi
        width_factor = beta ** phi
        return width_factor, depth_factor, drop_rate

    def create_features(self, width_factor, depth_factor, last_channels):
        channels = int(32 * width_factor)
        features = [CnnBlock(3, channels, 3, stride=2, padding=1)]
        in_channels = channels

        for expand_ratio, channels, repeats, stride, kernel_size in base_model:
            out_channels = 4*ceil(int(channels*width_factor) / 4)
            layers_repeats = ceil(repeats * depth_factor)
            #! be tedad e repeat ha tooye jadval e paper repeat darim:
            for layer in range(layers_repeats):
                features.append(
                    InvertdResidualBlock(
                        in_channels,
                        out_channels,
                        expand_ratio=expand_ratio,
                        stride = stride if layer == 0 else 1,
                        kernel_size=kernel_size,
                        padding=kernel_size//2, #! if k=1:pad=0, k=3:pad=1, k=5:pad=2
                    )
                )
                in_channels = out_channels

        features.append(
            CnnBlock(in_channels, last_channels, kernel_size=1, stride=1, padding=0)
        )

        return nn.Sequential(*features)

    def forward(self, x):
        x = self.pool(self.features(x))
        return self.classifier(x.view(x.shape[0], -1))


def test():
    os.system('cls')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    version = "b0"
    phi, res, drop_rate = phi_values[version]
    num_examples, num_classes = 4, 10
    x = torch.randn((num_examples, 3, res, res)).to(device)
    model = EfficientNet(
        version=version,
        num_classes=num_classes,
    ).to(device)
    print(model)

test()