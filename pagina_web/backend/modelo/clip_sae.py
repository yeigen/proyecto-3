import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from backend.config import CHECKPOINT_CLIP, METRICS_CLIP, BAND_STATS
from backend.config import TILES_NPZ, INDICES_BANDAS_S2  # needed for first-time band stats calc

logger = logging.getLogger(__name__)


class QuickGELU(nn.Module):
    def forward(self, x):
        return x * torch.sigmoid(1.702 * x)


class ResidualAttentionBlock(nn.Module):
    def __init__(self, d_model: int, n_head: int):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_head, batch_first=True)
        self.ln_1 = nn.LayerNorm(d_model)
        self.mlp = type('MLP', (), {})()
        self.mlp.c_fc = nn.Linear(d_model, d_model * 4)
        self.mlp.gelu = QuickGELU()
        self.mlp.c_proj = nn.Linear(d_model * 4, d_model)
        self.ln_2 = nn.LayerNorm(d_model)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x), self.ln_1(x), self.ln_1(x))[0]
        x = x + self.mlp.c_proj(self.mlp.gelu(self.mlp.c_fc(self.ln_2(x))))
        return x


class Transformer(nn.Module):
    def __init__(self, width: int, layers: int, heads: int):
        super().__init__()
        self.resblocks = nn.ModuleList(
            [ResidualAttentionBlock(width, heads) for _ in range(layers)]
        )

    def forward(self, x):
        for block in self.resblocks:
            x = block(x)
        return x


class VisualEncoder(nn.Module):
    def __init__(self, input_channels: int = 12):
        super().__init__()
        self.class_embedding = nn.Parameter(torch.empty(768))
        self.positional_embedding = nn.Parameter(torch.empty(50, 768))
        self.ln_pre = nn.LayerNorm(768)
        self.transformer = Transformer(768, 12, 12)
        self.ln_post = nn.LayerNorm(768)
        self.proj = nn.Parameter(torch.empty(768, 512))
        self.conv1 = nn.Conv2d(input_channels, 768, 32, 32, bias=False)

    def forward(self, x):
        b = x.shape[0]
        x = self.conv1(x)
        x = x.reshape(b, 768, -1).permute(0, 2, 1)
        cls = self.class_embedding.view(1, 1, 768).expand(b, -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = x + self.positional_embedding[:x.shape[1]]
        x = self.ln_pre(x)
        x = self.transformer(x)
        x = x[:, 0, :]
        x = self.ln_post(x)
        x = x @ self.proj
        return x


def _merge_lora(state_dict: dict, rank: int = 16) -> dict:
    merged = {}
    lora_bases = set()
    for k in state_dict:
        if k.endswith('.A'):
            lora_bases.add(k[:-2])
        elif k.endswith('.B'):
            lora_bases.add(k[:-2])

    for k, v in state_dict.items():
        if k.endswith('.A') or k.endswith('.B'):
            continue
        if k in lora_bases:
            a_key = k + '.A'
            b_key = k + '.B'
            if a_key in state_dict and b_key in state_dict:
                merged[k] = v + (state_dict[a_key] @ state_dict[b_key]) * (1.0 / rank)
                continue
        merged[k] = v
    return merged


def _calcular_band_stats() -> tuple:
    if not BAND_STATS.exists():
        logger.info("Calculando band_mean/band_std desde tiles_train.npz (una vez)")
        tiles = np.load(TILES_NPZ)["data"]
        tiles_12b = tiles[:, list(INDICES_BANDAS_S2)]
        flat = tiles_12b.reshape(len(tiles_12b), 12, -1)
        band_mean = flat.mean(axis=(0, 2)).astype(np.float32)
        band_std = flat.std(axis=(0, 2)).astype(np.float32) + 1e-6
        BAND_STATS.parent.mkdir(parents=True, exist_ok=True)
        with open(BAND_STATS, "w") as f:
            json.dump({"band_mean": band_mean.tolist(), "band_std": band_std.tolist()}, f)
        logger.info(f"band_stats guardado en {BAND_STATS}")
    else:
        with open(BAND_STATS) as f:
            stats = json.load(f)
        band_mean = stats["band_mean"]
        band_std = stats["band_std"]
        logger.info(f"band_stats cargado desde {BAND_STATS}")

    return band_mean, band_std


def cargar_modelo(device: str = "cpu"):
    if not CHECKPOINT_CLIP.exists():
        raise FileNotFoundError(f"Checkpoint no encontrado: {CHECKPOINT_CLIP}")

    logger.info(f"Cargando checkpoint: {CHECKPOINT_CLIP}")

    ckpt = torch.load(str(CHECKPOINT_CLIP), map_location="cpu", weights_only=True)
    clip_sd = ckpt["clip"]

    visual = VisualEncoder(input_channels=12)
    visual_sd = {}
    for k, v in clip_sd.items():
        if k.startswith("visual."):
            visual_sd[k[7:]] = v

    visual_sd = _merge_lora(visual_sd)
    visual.load_state_dict(visual_sd, strict=False)
    visual.to(device)
    visual.eval()
    logger.info("Encoder visual cargado")

    fusion = nn.Linear(512, 512)
    fusion.load_state_dict({
        "weight": ckpt["fusion"]["proj.weight"],
        "bias": ckpt["fusion"]["proj.bias"],
    })
    fusion.to(device)
    fusion.eval()
    logger.info("Proyeccion fusion cargada")

    band_mean, band_std = _calcular_band_stats()

    return visual, fusion, band_mean, band_std


def generar_embedding(visual, fusion, tile_tensor: torch.Tensor, device: str = "cpu"):
    tile_tensor = tile_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        emb_512 = visual(tile_tensor)
        emb = fusion(emb_512)
        emb = F.normalize(emb, dim=-1)

    return emb.cpu()


def cargar_metrics() -> dict:
    if not METRICS_CLIP.exists():
        return {}
    with open(METRICS_CLIP) as f:
        return json.load(f)
