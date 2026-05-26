import torch
import torch.nn as nn


class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size):
        super().__init__()
        self.hidden_dim = hidden_dim
        padding = kernel_size // 2
        self.conv = nn.Conv2d(
            input_dim + hidden_dim, 4 * hidden_dim,
            kernel_size, padding=padding,
        )

    def forward(self, x, h, c):
        combined = torch.cat([x, h], dim=1)
        gates = self.conv(combined)
        i, f, o, g = torch.chunk(gates, 4, dim=1)
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        o = torch.sigmoid(o)
        g = torch.tanh(g)
        c_next = f * c + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next


class ConvLSTM(nn.Module):
    def __init__(self, input_dim=256, hidden_dim=128, kernel_size=3, num_layers=2):
        super().__init__()
        self.num_layers = num_layers
        cells = []
        for i in range(num_layers):
            in_dim = input_dim if i == 0 else hidden_dim
            cells.append(ConvLSTMCell(in_dim, hidden_dim, kernel_size))
        self.cells = nn.ModuleList(cells)

    def forward(self, x):
        batch, seq, c, h, w = x.shape
        h_states = []
        for t in range(seq):
            xt = x[:, t]
            for layer in range(self.num_layers):
                if t == 0:
                    h = torch.zeros(batch, self.cells[layer].hidden_dim, h, w, device=x.device)
                    c = torch.zeros_like(h)
                h, c = self.cells[layer](xt, h, c)
                xt = h
            h_states.append(h)
        return torch.stack(h_states, dim=1)


class GeoConvLSTM(nn.Module):
    def __init__(self, input_dim=256, hidden_dim=128, kernel_size=3,
                 num_layers=2, num_horizontes=3, num_contaminantes=3):
        super().__init__()
        self.convlstm = ConvLSTM(input_dim, hidden_dim, kernel_size, num_layers)
        self.head = nn.Sequential(
            nn.Conv2d(hidden_dim, 64, kernel_size=1),
            nn.ReLU(),
            nn.Conv2d(64, num_horizontes * num_contaminantes, kernel_size=1),
        )

    def forward(self, x):
        out = self.convlstm(x)
        ultimo = out[:, -1]
        pred = self.head(ultimo)
        b, c, h, w = pred.shape
        pred = pred.view(b, 3, 3, h, w)
        return pred


def cargar_checkpoint(ruta: str, device: str = "cpu") -> GeoConvLSTM:
    modelo = GeoConvLSTM()
    estado = torch.load(ruta, map_location=device, weights_only=True)
    modelo.load_state_dict(estado)
    modelo.to(device)
    modelo.eval()
    return modelo
