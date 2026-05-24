import torch

modelo_global = {}
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
