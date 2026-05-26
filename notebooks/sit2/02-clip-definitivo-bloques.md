# Bloques para `02-clip-definitivo.ipynb`

## Bloque 0 - Setup reproducible

```python
!pip install -q open_clip_torch factor_analyzer semopy
```

```python
import os
import json
import math
import random
import hashlib
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

import open_clip
from tqdm.auto import tqdm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report
from transformers import AutoTokenizer, AutoModel

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

SEED = 42

def seed_everything(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

seed_everything(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Dispositivo: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

```python
RUTA_DATASET = Path("/kaggle/input/datasets/edwardsx/geovision-tiles-v2-2021-2024")
RUTA_SALIDA = Path("/kaggle/working/geovision_clip_sit2")
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

TILE_SIZE = 64
CHANNELS_S2 = 13
CONTRASTIVE_DIM = 256
SAE_DICT_DIM = 512
TEMP_INIT = 0.07

BATCH_SIZE = 32
EPOCHS = 30
GRAD_ACCUM = 2
LEARNING_RATE = 8e-5
WEIGHT_DECAY = 5e-4
ALPHA_SAE = 0.1
SAE_L1_REG = 2e-3
AUX_CLS_WEIGHT = 0.15
LABEL_SMOOTHING = 0.03
TRAIN_LAST_BLOCKS = 1
TABULAR_DROPOUT = 0.30
SAE_HIDDEN_VISUAL = 2048
SAE_HIDDEN_TEXT = 1024
SAE_SPARSE_DIM = 256

SAE_DEAD_THRESHOLD = 1e-3
SPARSITY_KPI_THRESH = 0.01
NUM_WORKERS = 0

print("Configuración lista")
print(f"Salida: {RUTA_SALIDA}")
```

## Bloque 1 - Carga y auditoría del dataset v2

```python
meta_df = pd.read_parquet(RUTA_DATASET / "tiles_meta.parquet")

with np.load(RUTA_DATASET / "tiles_train.npz") as data:
    images_raw = data["data"]
    bands = list(data["bands"])

print(f"Metadata: {meta_df.shape}")
print(f"Imágenes: {images_raw.shape}")
print(f"Bandas: {bands}")
```

```python
CLASES_ORDENADAS = [
    "contaminacion_alta_NO2",
    "contaminacion_alta_SO2",
    "ozono_anomalo",
    "suelo_urbano",
    "vegetacion_densa",
]

conteo_clases = meta_df["clase"].value_counts().reindex(CLASES_ORDENADAS)
print("Conteo por clase")
print(conteo_clases)

assert images_raw.shape == (1150, 13, 64, 64), "Forma inesperada en tiles_train.npz"
assert meta_df.shape[0] == images_raw.shape[0], "Metadata e imágenes no coinciden"
assert set(meta_df["clase"].unique()) == set(CLASES_ORDENADAS), "Clases inesperadas"
assert conteo_clases.min() == conteo_clases.max() == 230, "Dataset no está balanceado"
assert bands == ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "SCL"], "Bandas inesperadas"

print("Auditoría estructural superada")
```

```python
cols_auditoria = ["ndvi", "ndbi", "scl_pct", "no2", "so2", "o3", "modis_AOD_047", "modis_AOD_055", "modis_WV"]
cols_auditoria = [c for c in cols_auditoria if c in meta_df.columns]

resumen_clase = meta_df.groupby("clase")[["ndvi", "ndbi", "scl_pct"]].agg(["mean", "min", "max"]).round(4)
display(resumen_clase)

nulos = meta_df[cols_auditoria].isna().mean().sort_values(ascending=False).mul(100).round(2)
print("Nulos porcentuales")
print(nulos[nulos > 0])
```

```python
urbano = meta_df[meta_df["clase"] == "suelo_urbano"]
vegetacion = meta_df[meta_df["clase"] == "vegetacion_densa"]

print("Chequeo suelo urbano corregido")
print(f"NDVI urbano medio: {urbano['ndvi'].mean():.4f}")
print(f"NDBI urbano medio: {urbano['ndbi'].mean():.4f}")
print(f"NDVI vegetación medio: {vegetacion['ndvi'].mean():.4f}")
print(f"NDBI vegetación medio: {vegetacion['ndbi'].mean():.4f}")

assert urbano["ndvi"].mean() < 0.30, "Suelo urbano no parece suficientemente estricto por NDVI"
assert urbano["ndbi"].mean() > 0.05, "Suelo urbano no parece suficientemente estricto por NDBI"
assert vegetacion["ndvi"].mean() > 0.60, "Vegetación densa no parece suficientemente verde"

print("Auditoría óptica superada")
```

```python
plt.figure(figsize=(10, 5))
sns.countplot(data=meta_df, y="clase", order=CLASES_ORDENADAS, hue="clase", palette="viridis", legend=False)
plt.title("Balance de clases del dataset v2")
plt.xlabel("Muestras")
plt.ylabel("Clase")
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, col in zip(axes, ["ndvi", "ndbi", "scl_pct"]):
    sns.boxplot(data=meta_df, x="clase", y=col, hue="clase", order=CLASES_ORDENADAS, palette="viridis", ax=ax, legend=False)
    ax.set_title(col)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()
```

## Bloque 2 - Dataset, split y prompts múltiples

```python
PROMPTS_BASE = {
    "contaminacion_alta_NO2": [
        "Clase contaminacion_alta_NO2. Tile Sentinel-2 de Cali con señal antropogénica asociada a dióxido de nitrógeno alto.",
        "Clase NO2 alto. Recorte urbano o periurbano con vegetación intermedia y presión vial compatible con contaminación por NO2.",
        "Etiqueta contaminacion_alta_NO2. Imagen multiespectral con patrón mixto urbano vegetal y carga troposférica de NO2 elevada.",
    ],
    "contaminacion_alta_SO2": [
        "Clase contaminacion_alta_SO2. Tile Sentinel-2 de Cali con dióxido de azufre alto y entorno regional industrial.",
        "Clase SO2 alto. Recorte con vegetación alta o borde periurbano asociado a transporte regional de emisiones de azufre.",
        "Etiqueta contaminacion_alta_SO2. Imagen multiespectral con baja densidad construida relativa y señal de SO2 elevada.",
    ],
    "ozono_anomalo": [
        "Clase ozono_anomalo. Tile Sentinel-2 de Cali con ozono O3 anómalo por dinámica fotoquímica regional.",
        "Clase O3 anómalo. Recorte con mezcla urbano vegetal y patrón atmosférico distinto a NO2 y SO2.",
        "Etiqueta ozono_anomalo. Imagen multiespectral con condición regional de ozono elevada o atípica.",
    ],
    "suelo_urbano": [
        "Clase suelo_urbano. Tile Sentinel-2 con concreto, asfalto, infraestructura densa, bajo NDVI y alto NDBI.",
        "Clase urbana. Imagen satelital de superficie impermeable con vegetación baja y construcción dominante.",
        "Etiqueta suelo_urbano. Recorte multiespectral de Cali con baja vegetación y alta respuesta urbana.",
    ],
    "vegetacion_densa": [
        "Clase vegetacion_densa. Tile Sentinel-2 con alto NDVI, bajo NDBI y cobertura vegetal continua.",
        "Clase vegetación densa. Imagen satelital verde con baja urbanización y respuesta alta en infrarrojo cercano.",
        "Etiqueta vegetacion_densa. Recorte multiespectral de Cali dominado por vegetación sana y continua.",
    ],
}

FEATURES_TABULARES = [
    "ndvi", "ndbi", "scl_pct",
    "era5_T2m", "era5_Td2m", "era5_u10", "era5_v10",
    "era5_BLH", "era5_RH850", "era5_psurf", "era5_precip",
    "modis_AOD_047", "modis_AOD_055", "modis_WV",
]

FEATURES_TABULARES = [c for c in FEATURES_TABULARES if c in meta_df.columns]
FEATURES_NO_LEAK = [c for c in FEATURES_TABULARES if c not in ["no2", "so2", "o3"]]

print(f"Features tabulares sin leakage: {FEATURES_NO_LEAK}")
```

```python
stats_clase = meta_df.groupby("clase")[["ndvi", "ndbi", "scl_pct"]].mean().round(3)

def descriptor_clase(clase):
    s = stats_clase.loc[clase]
    return f"perfil medio NDVI {s['ndvi']:.3f}, NDBI {s['ndbi']:.3f}, SCL valido {s['scl_pct']:.3f}"


def construir_texto(row, variante=0):
    clase = row["clase"]
    base = PROMPTS_BASE[clase][variante % len(PROMPTS_BASE[clase])]
    return f"{base} Contexto de clase: {descriptor_clase(clase)}."

meta_df = meta_df.reset_index(drop=True).copy()
meta_df["texto"] = [construir_texto(row, i) for i, row in meta_df.iterrows()]

print(meta_df[["clase", "texto"]].head())
```

```python
indices = np.arange(len(meta_df))
labels = meta_df["clase"].values

train_idx, temp_idx = train_test_split(
    indices,
    test_size=0.30,
    stratify=labels,
    random_state=SEED,
)

val_idx, test_idx = train_test_split(
    temp_idx,
    test_size=0.50,
    stratify=labels[temp_idx],
    random_state=SEED,
)

print(f"Train: {len(train_idx)}")
print(f"Val:   {len(val_idx)}")
print(f"Test:  {len(test_idx)}")

for nombre, idx in [("train", train_idx), ("val", val_idx), ("test", test_idx)]:
    print(f"\n{nombre}")
    print(meta_df.iloc[idx]["clase"].value_counts().reindex(CLASES_ORDENADAS))
```

```python
class GeoVisionClipDataset(Dataset):
    def __init__(self, images, metadata, indices, tabular_cols, class_list, scaler=None, fit_scaler=False):
        self.images = images
        self.metadata = metadata.iloc[indices].reset_index(drop=True).copy()
        self.indices = np.asarray(indices)
        self.tabular_cols = tabular_cols
        self.class_to_idx = {c: i for i, c in enumerate(class_list)}

        tab = self.metadata[tabular_cols].copy()
        for col in tab.columns:
            tab[col] = tab[col].fillna(tab[col].median())

        if scaler is None:
            scaler = StandardScaler()
        self.scaler = scaler
        self.tabular = scaler.fit_transform(tab) if fit_scaler else scaler.transform(tab)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        raw_idx = self.indices[idx]
        img = torch.tensor(self.images[raw_idx], dtype=torch.float32)
        tab = torch.tensor(self.tabular[idx], dtype=torch.float32)
        label = self.class_to_idx[self.metadata.loc[idx, "clase"]]
        text = self.metadata.loc[idx, "texto"]
        return img, tab, label, text

train_dataset = GeoVisionClipDataset(images_raw, meta_df, train_idx, FEATURES_NO_LEAK, CLASES_ORDENADAS, fit_scaler=True)
val_dataset = GeoVisionClipDataset(images_raw, meta_df, val_idx, FEATURES_NO_LEAK, CLASES_ORDENADAS, scaler=train_dataset.scaler)
test_dataset = GeoVisionClipDataset(images_raw, meta_df, test_idx, FEATURES_NO_LEAK, CLASES_ORDENADAS, scaler=train_dataset.scaler)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, drop_last=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

print("DataLoaders listos")
```

```python
TEXTOS_CANDIDATOS = []
TEXTOS_CANDIDATOS_LABELS = []

for clase in CLASES_ORDENADAS:
    row_ref = meta_df[meta_df["clase"] == clase].iloc[0]
    for i in range(len(PROMPTS_BASE[clase])):
        TEXTOS_CANDIDATOS.append(construir_texto(row_ref, i))
        TEXTOS_CANDIDATOS_LABELS.append(CLASES_ORDENADAS.index(clase))

TEXTOS_CANDIDATOS_LABELS = torch.tensor(TEXTOS_CANDIDATOS_LABELS, dtype=torch.long)

print(f"Textos candidatos para retrieval: {len(TEXTOS_CANDIDATOS)}")
for texto, label in zip(TEXTOS_CANDIDATOS[:5], TEXTOS_CANDIDATOS_LABELS[:5]):
    print(f"[{CLASES_ORDENADAS[label]}] {texto}")
```

## Bloque 3 - Arquitectura GeoVision-CLIP híbrida

```python
class BandProjector(nn.Module):
    def __init__(self, in_channels=13, out_channels=3, image_size=224):
        super().__init__()
        self.image_size = image_size
        self.proj = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=1),
            nn.GELU(),
            nn.Conv2d(32, out_channels, kernel_size=1),
        )
        self.register_buffer("mean", torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(1, 3, 1, 1))

    def forward(self, x):
        x = x / 10000.0
        x = torch.clamp(x, 0.0, 1.5)
        x = self.proj(x)
        x = F.interpolate(x, size=(self.image_size, self.image_size), mode="bilinear", align_corners=False)
        x = torch.sigmoid(x)
        return (x - self.mean) / self.std
```

```python
class SparseAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=2048, sparse_dim=256):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, sparse_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(sparse_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x):
        z = self.encoder(x)
        recon = self.decoder(z)
        return z, recon

    @torch.no_grad()
    def resample_dead_neurons(self, x, z, threshold=1e-3):
        active = (z > 0).float().mean(dim=0)
        dead = active < threshold
        n_dead = int(dead.sum().item())
        return n_dead


class ProjectionHead(nn.Module):
    def __init__(self, input_dim=256, out_dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, input_dim),
            nn.GELU(),
            nn.LayerNorm(input_dim),
            nn.Dropout(0.10),
            nn.Linear(input_dim, out_dim),
        )

    def forward(self, x):
        return F.normalize(self.net(x), dim=-1)
```

```python
def set_visual_trainable(visual_encoder, train_last_blocks=1):
    for p in visual_encoder.parameters():
        p.requires_grad = False

    if train_last_blocks > 0 and hasattr(visual_encoder, "transformer") and hasattr(visual_encoder.transformer, "resblocks"):
        for block in visual_encoder.transformer.resblocks[-train_last_blocks:]:
            for p in block.parameters():
                p.requires_grad = True

    for name in ["ln_post", "proj"]:
        module_or_param = getattr(visual_encoder, name, None)
        if isinstance(module_or_param, nn.Module):
            for p in module_or_param.parameters():
                p.requires_grad = True
        elif isinstance(module_or_param, nn.Parameter):
            module_or_param.requires_grad = True


def mean_pool_text(outputs, attention_mask):
    token_embeddings = outputs.last_hidden_state
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * mask, dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)
```

```python
class GeoVisionCLIP(nn.Module):
    def __init__(self, n_tabular, n_classes):
        super().__init__()
        clip_model, _, _ = open_clip.create_model_and_transforms(
            "ViT-B-32",
            pretrained="laion2b_s34b_b79k",
        )

        self.band_projector = BandProjector(in_channels=CHANNELS_S2, out_channels=3, image_size=224)
        self.visual_encoder = clip_model.visual
        set_visual_trainable(self.visual_encoder, train_last_blocks=TRAIN_LAST_BLOCKS)

        self.text_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.text_tokenizer = AutoTokenizer.from_pretrained(self.text_model_name)
        self.text_encoder = AutoModel.from_pretrained(self.text_model_name)
        for p in self.text_encoder.parameters():
            p.requires_grad = False

        self.sae_visual = SparseAutoencoder(input_dim=512, hidden_dim=SAE_HIDDEN_VISUAL, sparse_dim=SAE_SPARSE_DIM)
        self.sae_text = SparseAutoencoder(input_dim=384, hidden_dim=SAE_HIDDEN_TEXT, sparse_dim=SAE_SPARSE_DIM)
        self.proj_visual = ProjectionHead(input_dim=SAE_SPARSE_DIM, out_dim=CONTRASTIVE_DIM)
        self.proj_text = ProjectionHead(input_dim=SAE_SPARSE_DIM, out_dim=CONTRASTIVE_DIM)

        self.tabular_gate = nn.Sequential(
            nn.Linear(n_tabular, 128),
            nn.GELU(),
            nn.Dropout(TABULAR_DROPOUT),
            nn.Linear(128, SAE_SPARSE_DIM),
            nn.Sigmoid(),
        )

        self.classifier = nn.Sequential(
            nn.LayerNorm(CONTRASTIVE_DIM),
            nn.Linear(CONTRASTIVE_DIM, n_classes),
        )

        self.logit_scale = nn.Parameter(torch.tensor(math.log(1 / TEMP_INIT)))

    def encode_image_raw(self, images):
        x = self.band_projector(images)
        return self.visual_encoder(x).float()

    def encode_text_raw(self, texts):
        tokens = self.text_tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=96,
            return_tensors="pt",
        ).to(next(self.parameters()).device)
        with torch.no_grad():
            outputs = self.text_encoder(**tokens)
        return mean_pool_text(outputs, tokens["attention_mask"]).float()

    def encode_image(self, images, tabular):
        raw = self.encode_image_raw(images)
        z, recon = self.sae_visual(raw)
        gate = self.tabular_gate(tabular)
        z = z * (0.75 + 0.5 * gate)
        emb = self.proj_visual(z)
        logits_cls = self.classifier(emb)
        return emb, z, recon, raw, logits_cls

    def encode_text_features(self, raw_text):
        z, recon = self.sae_text(raw_text)
        emb = self.proj_text(z)
        return emb, z, recon

    def encode_text(self, texts):
        raw = self.encode_text_raw(texts)
        emb, z, recon = self.encode_text_features(raw)
        return emb, z, recon, raw

    def forward(self, images, tabular, texts):
        img_emb, z_img, recon_img, raw_img, logits_cls = self.encode_image(images, tabular)
        txt_emb, z_txt, recon_txt, raw_txt = self.encode_text(texts)
        return {
            "img_emb": img_emb,
            "txt_emb": txt_emb,
            "z_img": z_img,
            "z_txt": z_txt,
            "recon_img": recon_img,
            "recon_txt": recon_txt,
            "raw_img": raw_img,
            "raw_txt": raw_txt,
            "logits_cls": logits_cls,
        }
```

```python
model = GeoVisionCLIP(
    n_tabular=len(FEATURES_NO_LEAK),
    n_classes=len(CLASES_ORDENADAS),
).to(device)

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"Parámetros totales: {total:,}")
print(f"Parámetros entrenables: {trainable:,}")
print(f"Porcentaje entrenable: {100 * trainable / total:.2f}%")
print(f"Temperatura inicial: {model.logit_scale.exp().item():.4f}")
```

```python
imgs, tabs, labels_batch, texts = next(iter(train_loader))
imgs = imgs.to(device)
tabs = tabs.to(device)

model.eval()
with torch.no_grad():
    out = model(imgs, tabs, texts)

print("Prueba forward")
print(f"img_emb:   {tuple(out['img_emb'].shape)}")
print(f"txt_emb:   {tuple(out['txt_emb'].shape)}")
print(f"z_img:     {tuple(out['z_img'].shape)}")
print(f"recon_img: {tuple(out['recon_img'].shape)}")
print(f"logits:    {tuple(out['logits_cls'].shape)}")
```

## Bloque 4 - Entrenamiento híbrido

```python
def multipositive_infonce(img_emb, txt_emb, labels, text_labels, logit_scale):
    logits = logit_scale.exp().clamp(max=100.0) * img_emb @ txt_emb.t()
    pos_mask = labels[:, None].eq(text_labels[None, :]).float()
    log_den = torch.logsumexp(logits, dim=1)
    log_num = torch.logsumexp(logits.masked_fill(pos_mask == 0, -1e9), dim=1)
    return -(log_num - log_den).mean()


def sae_loss(recon, raw, z):
    recon_loss = F.mse_loss(recon, raw)
    sparse_loss = torch.norm(z, p=1, dim=-1).mean() * SAE_L1_REG
    return recon_loss + sparse_loss, recon_loss


@torch.no_grad()
def recall_at_k_from_logits(logits, labels, text_labels, k):
    topk = logits.topk(k, dim=1).indices
    pred_labels = text_labels[topk]
    return pred_labels.eq(labels[:, None]).any(dim=1).float().mean().item()


@torch.no_grad()
def late_fusion_logits(clip_logits, class_logits, text_labels, beta=0.25):
    class_scores = F.log_softmax(class_logits, dim=1)
    class_by_text = class_scores[:, text_labels]
    return clip_logits + beta * class_by_text
```

```python
def evaluar_retrieval(model, loader, candidate_texts, candidate_labels, fusion_betas=(0.0, 0.15, 0.25, 0.35)):
    model.eval()
    candidate_labels = candidate_labels.to(device)

    with torch.no_grad():
        txt_emb, z_txt, recon_txt, raw_txt = model.encode_text(candidate_texts)

    total_loss = 0.0
    total_n = 0
    all_logits = []
    all_labels = []
    all_z_img = []
    all_raw_img = []
    all_recon_img = []
    all_cls_logits = []

    with torch.no_grad():
        for imgs, tabs, labels, _ in loader:
            imgs = imgs.to(device)
            tabs = tabs.to(device)
            labels = labels.to(device)

            img_emb, z_img, recon_img, raw_img, logits_cls = model.encode_image(imgs, tabs)
            loss_nce = multipositive_infonce(img_emb, txt_emb, labels, candidate_labels, model.logit_scale)
            loss_img, _ = sae_loss(recon_img, raw_img, z_img)
            loss_txt, _ = sae_loss(recon_txt, raw_txt, z_txt)
            loss_cls = F.cross_entropy(logits_cls, labels, label_smoothing=LABEL_SMOOTHING)
            loss = loss_nce + ALPHA_SAE * (loss_img + loss_txt) + AUX_CLS_WEIGHT * loss_cls

            logits = model.logit_scale.exp().clamp(max=100.0) * img_emb @ txt_emb.t()
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())
            all_z_img.append(z_img.cpu())
            all_raw_img.append(raw_img.cpu())
            all_recon_img.append(recon_img.cpu())
            all_cls_logits.append(logits_cls.cpu())

            bs = labels.size(0)
            total_loss += loss.item() * bs
            total_n += bs

    all_logits = torch.cat(all_logits)
    all_labels = torch.cat(all_labels)
    all_z_img = torch.cat(all_z_img)
    all_raw_img = torch.cat(all_raw_img)
    all_recon_img = torch.cat(all_recon_img)
    all_cls_logits = torch.cat(all_cls_logits)
    candidate_labels_cpu = candidate_labels.cpu()

    metrics = {
        "loss": total_loss / total_n,
        "recall1": recall_at_k_from_logits(all_logits, all_labels, candidate_labels_cpu, 1),
        "recall5": recall_at_k_from_logits(all_logits, all_labels, candidate_labels_cpu, 5),
        "sparsity": (all_z_img < SPARSITY_KPI_THRESH).float().mean().item(),
        "mse": F.mse_loss(all_recon_img, all_raw_img).item(),
    }

    best_beta = 0.0
    best_r1 = metrics["recall1"]
    best_r5 = metrics["recall5"]

    for beta in fusion_betas:
        fused = late_fusion_logits(all_logits, all_cls_logits, candidate_labels_cpu, beta=beta)
        r1 = recall_at_k_from_logits(fused, all_labels, candidate_labels_cpu, 1)
        r5 = recall_at_k_from_logits(fused, all_labels, candidate_labels_cpu, 5)
        metrics[f"recall1_fusion_beta_{beta}"] = r1
        metrics[f"recall5_fusion_beta_{beta}"] = r5
        if r1 > best_r1:
            best_beta = beta
            best_r1 = r1
            best_r5 = r5

    metrics["best_beta"] = best_beta
    metrics["recall1_fusion"] = best_r1
    metrics["recall5_fusion"] = best_r5
    return metrics
```

```python
param_groups = [
    {"params": model.band_projector.parameters(), "lr": 1e-4, "weight_decay": 1e-4},
    {"params": [p for p in model.visual_encoder.parameters() if p.requires_grad], "lr": 1e-5, "weight_decay": 1e-2},
    {"params": model.sae_visual.parameters(), "lr": 3e-4, "weight_decay": 1e-4},
    {"params": model.sae_text.parameters(), "lr": 3e-4, "weight_decay": 1e-4},
    {"params": model.proj_visual.parameters(), "lr": 5e-4, "weight_decay": 1e-4},
    {"params": model.proj_text.parameters(), "lr": 5e-4, "weight_decay": 1e-4},
    {"params": model.classifier.parameters(), "lr": 3e-4, "weight_decay": 1e-4},
    {"params": model.tabular_gate.parameters(), "lr": 1e-4, "weight_decay": 1e-4},
    {"params": [model.logit_scale], "lr": 1e-3, "weight_decay": 0.0},
]

optimizer = torch.optim.AdamW(param_groups, betas=(0.9, 0.98), eps=1e-6)

total_steps = math.ceil(len(train_loader) / GRAD_ACCUM) * EPOCHS
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=[g["lr"] for g in param_groups],
    total_steps=total_steps,
    pct_start=0.10,
    anneal_strategy="cos",
    div_factor=25.0,
    final_div_factor=1e4,
)

TEXTOS_CANDIDATOS_LABELS = TEXTOS_CANDIDATOS_LABELS.to(device)

historial = []
best_score = -1.0
best_val_loss = float("inf")
best_epoch = 0
paciencia = 8
ckpt_path = RUTA_SALIDA / "best_geovision_clip_sit2.pt"
```

```python
for epoch in range(1, EPOCHS + 1):
    model.train()
    train_loss = 0.0
    train_nce = 0.0
    train_sae_img = 0.0
    train_sae_txt = 0.0
    train_cls = 0.0
    train_n = 0

    optimizer.zero_grad(set_to_none=True)
    pbar = tqdm(train_loader, desc=f"Epoca {epoch}/{EPOCHS}")
    for step, (imgs, tabs, labels, texts) in enumerate(pbar, start=1):
        imgs = imgs.to(device)
        tabs = tabs.to(device)
        labels = labels.to(device)

        out = model(imgs, tabs, texts)
        txt_bank_emb, z_txt_bank, recon_txt_bank, raw_txt_bank = model.encode_text(TEXTOS_CANDIDATOS)

        loss_nce = multipositive_infonce(
            out["img_emb"],
            txt_bank_emb,
            labels,
            TEXTOS_CANDIDATOS_LABELS,
            model.logit_scale,
        )
        loss_img, mse_img = sae_loss(out["recon_img"], out["raw_img"], out["z_img"])
        loss_txt, mse_txt = sae_loss(recon_txt_bank, raw_txt_bank, z_txt_bank)
        loss_cls = F.cross_entropy(out["logits_cls"], labels, label_smoothing=LABEL_SMOOTHING)
        loss = loss_nce + ALPHA_SAE * (loss_img + loss_txt) + AUX_CLS_WEIGHT * loss_cls
        loss_to_backprop = loss / GRAD_ACCUM

        loss_to_backprop.backward()

        if step % GRAD_ACCUM == 0 or step == len(train_loader):
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], max_norm=1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            model.logit_scale.data.clamp_(max=math.log(100.0))

        model.sae_visual.resample_dead_neurons(out["raw_img"].detach(), out["z_img"].detach(), threshold=SAE_DEAD_THRESHOLD)
        model.sae_text.resample_dead_neurons(raw_txt_bank.detach(), z_txt_bank.detach(), threshold=SAE_DEAD_THRESHOLD)

        bs = labels.size(0)
        train_loss += loss.item() * bs
        train_nce += loss_nce.item() * bs
        train_sae_img += loss_img.item() * bs
        train_sae_txt += loss_txt.item() * bs
        train_cls += loss_cls.item() * bs
        train_n += bs

        pbar.set_postfix({
            "loss": f"{loss.item():.3f}",
            "nce": f"{loss_nce.item():.3f}",
            "cls": f"{loss_cls.item():.3f}",
        })

    val_metrics = evaluar_retrieval(model, val_loader, TEXTOS_CANDIDATOS, TEXTOS_CANDIDATOS_LABELS)
    train_row = {
        "epoch": epoch,
        "train_loss": train_loss / train_n,
        "train_info_nce": train_nce / train_n,
        "train_sae_img": train_sae_img / train_n,
        "train_sae_txt": train_sae_txt / train_n,
        "train_cls": train_cls / train_n,
        "val_loss": val_metrics["loss"],
        "val_recall1": val_metrics["recall1"],
        "val_recall5": val_metrics["recall5"],
        "val_recall1_fusion": val_metrics["recall1_fusion"],
        "val_recall5_fusion": val_metrics["recall5_fusion"],
        "best_beta": val_metrics["best_beta"],
        "val_sparsity": val_metrics["sparsity"],
        "val_mse": val_metrics["mse"],
        "temperature": model.logit_scale.exp().item(),
    }
    historial.append(train_row)

    print(
        f"Epoca {epoch:02d} | "
        f"loss={train_row['train_loss']:.4f} | "
        f"val_loss={train_row['val_loss']:.4f} | "
        f"R@1={train_row['val_recall1']:.4f} | "
        f"R@1_fusion={train_row['val_recall1_fusion']:.4f} | "
        f"beta={train_row['best_beta']:.2f} | "
        f"R@5={train_row['val_recall5']:.4f} | "
        f"sparsity={train_row['val_sparsity']:.4f} | "
        f"mse={train_row['val_mse']:.4f}"
    )

    improved = (train_row["val_recall1_fusion"] > best_score) or (
        train_row["val_recall1_fusion"] == best_score and train_row["val_loss"] < best_val_loss
    )

    if improved:
        best_score = train_row["val_recall1_fusion"]
        best_val_loss = train_row["val_loss"]
        best_epoch = epoch
        torch.save({
            "epoch": epoch,
            "model_state": model.state_dict(),
            "config": {
                "classes": CLASES_ORDENADAS,
                "features": FEATURES_NO_LEAK,
                "contrastive_dim": CONTRASTIVE_DIM,
                "sae_sparse_dim": SAE_SPARSE_DIM,
                "sae_hidden_visual": SAE_HIDDEN_VISUAL,
                "sae_hidden_text": SAE_HIDDEN_TEXT,
                "temp_init": TEMP_INIT,
                "seed": SEED,
                "learning_rate": LEARNING_RATE,
                "weight_decay": WEIGHT_DECAY,
                "aux_cls_weight": AUX_CLS_WEIGHT,
                "label_smoothing": LABEL_SMOOTHING,
                "sae_l1_reg": SAE_L1_REG,
                "train_last_blocks": TRAIN_LAST_BLOCKS,
                "tabular_dropout": TABULAR_DROPOUT,
                "best_beta": train_row["best_beta"],
            },
            "candidate_texts": TEXTOS_CANDIDATOS,
            "candidate_labels": TEXTOS_CANDIDATOS_LABELS.cpu(),
            "history": historial,
        }, ckpt_path)

    if epoch - best_epoch >= paciencia:
        print(f"Early stopping en epoca {epoch}. Mejor epoca: {best_epoch}")
        break
```

```python
hist_df = pd.DataFrame(historial)
hist_df.to_csv(RUTA_SALIDA / "historial_entrenamiento.csv", index=False)
display(hist_df.tail())

fig, axes = plt.subplots(1, 3, figsize=(18, 4))
axes[0].plot(hist_df["epoch"], hist_df["train_loss"], label="train")
axes[0].plot(hist_df["epoch"], hist_df["val_loss"], label="val")
axes[0].set_title("Loss total")
axes[0].legend()

axes[1].plot(hist_df["epoch"], hist_df["val_recall1"], label="Recall@1 CLIP")
axes[1].plot(hist_df["epoch"], hist_df["val_recall1_fusion"], label="Recall@1 fusion")
axes[1].plot(hist_df["epoch"], hist_df["val_recall5_fusion"], label="Recall@5 fusion")
axes[1].axhline(0.45, linestyle="--", color="gray", label="mínimo R@1")
axes[1].set_title("Retrieval validación")
axes[1].legend()

axes[2].plot(hist_df["epoch"], hist_df["val_sparsity"], label="sparsity")
axes[2].plot(hist_df["epoch"], hist_df["val_mse"], label="mse")
axes[2].axhline(0.70, linestyle="--", color="gray", label="mínimo sparsity")
axes[2].set_title("SAE validación")
axes[2].legend()

plt.tight_layout()
plt.savefig(RUTA_SALIDA / "curvas_entrenamiento.png", dpi=160, bbox_inches="tight")
plt.show()
```

## Bloque 5 - Guardar modelo como artefacto reutilizable

```python
ARTEFACTO_DIR = Path("/kaggle/working/geovision_clip_model_dataset")
ARTEFACTO_DIR.mkdir(parents=True, exist_ok=True)

checkpoint = torch.load(ckpt_path, map_location="cpu")
modelo_path = ARTEFACTO_DIR / "geovision_clip_sit2_best.pt"
torch.save(checkpoint, modelo_path)

hist_df = pd.DataFrame(checkpoint["history"])
hist_df.to_csv(ARTEFACTO_DIR / "historial_entrenamiento.csv", index=False)

pd.DataFrame({
    "texto": checkpoint["candidate_texts"],
    "label_idx": checkpoint["candidate_labels"].numpy(),
    "clase": [CLASES_ORDENADAS[i] for i in checkpoint["candidate_labels"].numpy()],
}).to_csv(ARTEFACTO_DIR / "textos_candidatos.csv", index=False)

with open(ARTEFACTO_DIR / "config_modelo.json", "w", encoding="utf-8") as f:
    json.dump(checkpoint["config"], f, ensure_ascii=False, indent=2)

print(f"Artefacto guardado en: {ARTEFACTO_DIR}")
print(f"Checkpoint: {modelo_path}")
```

```python
def calcular_md5(path, chunk_size=1024 * 1024):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()

md5_modelo = calcular_md5(modelo_path)

with open(ARTEFACTO_DIR / "MD5SUMS.txt", "w", encoding="utf-8") as f:
    f.write(f"{md5_modelo}  {modelo_path.name}\n")

print(f"MD5 checkpoint: {md5_modelo}")
```

```python
manifest_modelo = {
    "nombre": "geovision_clip_sit2_best",
    "archivo": modelo_path.name,
    "md5": md5_modelo,
    "ruta_kaggle_working": str(modelo_path),
    "dataset_base": str(RUTA_DATASET),
    "clases": CLASES_ORDENADAS,
    "features_no_leak": FEATURES_NO_LEAK,
    "best_epoch": int(checkpoint["epoch"]),
    "best_beta": float(checkpoint["config"].get("best_beta", 0.0)),
    "seed": SEED,
    "nota": "Artefacto listo para crear Kaggle Dataset desde /kaggle/working/geovision_clip_model_dataset",
}

with open(ARTEFACTO_DIR / "manifest_modelo.json", "w", encoding="utf-8") as f:
    json.dump(manifest_modelo, f, ensure_ascii=False, indent=2)

print(json.dumps(manifest_modelo, ensure_ascii=False, indent=2))
```

## Bloque 5.1 - Crear Kaggle Dataset por código

```python
DATASET_SLUG = "edwardsx/geovision-clip-sit2-model"

metadata_kaggle = {
    "title": "GeoVision CLIP Sit2 Model",
    "id": DATASET_SLUG,
    "licenses": [{"name": "CC0-1.0"}],
}

with open(ARTEFACTO_DIR / "dataset-metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata_kaggle, f, ensure_ascii=False, indent=2)

print("Archivos listos para Kaggle Dataset")
for p in sorted(ARTEFACTO_DIR.iterdir()):
    print(f"{p.name}: {p.stat().st_size / 1024**2:.2f} MB")
```

```python
import subprocess

cmd_create = [
    "kaggle",
    "datasets",
    "create",
    "-p",
    str(ARTEFACTO_DIR),
    "--public",
]

resultado = subprocess.run(cmd_create, capture_output=True, text=True)
print("STDOUT:")
print(resultado.stdout)
print("STDERR:")
print(resultado.stderr)

if resultado.returncode != 0:
    raise RuntimeError("Falló la creación del dataset. Si ya existe, usa la celda de versionado.")

print(f"Dataset creado: https://www.kaggle.com/datasets/{DATASET_SLUG}")
```

```python
cmd_version = [
    "kaggle",
    "datasets",
    "version",
    "-p",
    str(ARTEFACTO_DIR),
    "-m",
    "Actualiza modelo GeoVision-CLIP Sit2",
]

resultado = subprocess.run(cmd_version, capture_output=True, text=True)
print("STDOUT:")
print(resultado.stdout)
print("STDERR:")
print(resultado.stderr)

if resultado.returncode != 0:
    raise RuntimeError("Falló la actualización del dataset.")

print(f"Dataset actualizado: https://www.kaggle.com/datasets/{DATASET_SLUG}")
```

## Bloque 6 - Evaluación final en test

```python
checkpoint = torch.load(modelo_path, map_location=device)
model.load_state_dict(checkpoint["model_state"])
model.to(device)
model.eval()

TEXTOS_EVAL = checkpoint["candidate_texts"]
LABELS_EVAL = checkpoint["candidate_labels"].to(device)
BETA_EVAL = float(checkpoint["config"].get("best_beta", 0.0))

print(f"Checkpoint cargado desde: {modelo_path}")
print(f"Época seleccionada: {checkpoint['epoch']}")
print(f"Beta Late Fusion: {BETA_EVAL:.2f}")
```

```python
@torch.no_grad()
def evaluar_test_detallado(model, loader, candidate_texts, candidate_labels, beta):
    model.eval()
    candidate_labels = candidate_labels.to(device)
    txt_emb, z_txt, recon_txt, raw_txt = model.encode_text(candidate_texts)

    all_clip_logits = []
    all_fused_logits = []
    all_labels = []
    all_z_img = []
    all_raw_img = []
    all_recon_img = []
    all_cls_logits = []

    for imgs, tabs, labels, _ in loader:
        imgs = imgs.to(device)
        tabs = tabs.to(device)
        labels = labels.to(device)

        img_emb, z_img, recon_img, raw_img, cls_logits = model.encode_image(imgs, tabs)
        clip_logits = model.logit_scale.exp().clamp(max=100.0) * img_emb @ txt_emb.t()
        fused_logits = late_fusion_logits(clip_logits, cls_logits, candidate_labels, beta=beta)

        all_clip_logits.append(clip_logits.cpu())
        all_fused_logits.append(fused_logits.cpu())
        all_labels.append(labels.cpu())
        all_z_img.append(z_img.cpu())
        all_raw_img.append(raw_img.cpu())
        all_recon_img.append(recon_img.cpu())
        all_cls_logits.append(cls_logits.cpu())

    all_clip_logits = torch.cat(all_clip_logits)
    all_fused_logits = torch.cat(all_fused_logits)
    all_labels = torch.cat(all_labels)
    all_z_img = torch.cat(all_z_img)
    all_raw_img = torch.cat(all_raw_img)
    all_recon_img = torch.cat(all_recon_img)
    all_cls_logits = torch.cat(all_cls_logits)
    candidate_labels_cpu = candidate_labels.cpu()

    pred_text_idx = all_fused_logits.argmax(dim=1)
    pred_labels = candidate_labels_cpu[pred_text_idx]

    return {
        "clip_logits": all_clip_logits,
        "fused_logits": all_fused_logits,
        "labels": all_labels,
        "pred_labels": pred_labels,
        "z_img": all_z_img,
        "raw_img": all_raw_img,
        "recon_img": all_recon_img,
        "cls_logits": all_cls_logits,
        "candidate_labels": candidate_labels_cpu,
        "recall1_clip": recall_at_k_from_logits(all_clip_logits, all_labels, candidate_labels_cpu, 1),
        "recall5_clip": recall_at_k_from_logits(all_clip_logits, all_labels, candidate_labels_cpu, 5),
        "recall1_fusion": recall_at_k_from_logits(all_fused_logits, all_labels, candidate_labels_cpu, 1),
        "recall5_fusion": recall_at_k_from_logits(all_fused_logits, all_labels, candidate_labels_cpu, 5),
        "sparsity": (all_z_img < SPARSITY_KPI_THRESH).float().mean().item(),
        "mse": F.mse_loss(all_recon_img, all_raw_img).item(),
    }

test_eval = evaluar_test_detallado(model, test_loader, TEXTOS_EVAL, LABELS_EVAL, BETA_EVAL)
```

```python
metricas_rubrica = pd.DataFrame([
    {
        "KPI": "Recall@1 imagen-texto",
        "valor": test_eval["recall1_fusion"],
        "minimo": 0.45,
        "excelente": 0.65,
        "cumple": test_eval["recall1_fusion"] >= 0.45,
    },
    {
        "KPI": "Recall@5 imagen-texto",
        "valor": test_eval["recall5_fusion"],
        "minimo": 0.70,
        "excelente": 0.85,
        "cumple": test_eval["recall5_fusion"] >= 0.70,
    },
    {
        "KPI": "Sparsity ratio SAE visual",
        "valor": test_eval["sparsity"],
        "minimo": 0.70,
        "excelente": 0.85,
        "cumple": test_eval["sparsity"] >= 0.70,
    },
    {
        "KPI": "Loss reconstrucción SAE",
        "valor": test_eval["mse"],
        "minimo": 0.05,
        "excelente": 0.02,
        "cumple": test_eval["mse"] <= 0.05,
    },
])

metricas_rubrica.to_csv(ARTEFACTO_DIR / "metricas_test_rubrica.csv", index=False)
display(metricas_rubrica)

print(f"Recall@1 CLIP puro: {test_eval['recall1_clip']:.4f}")
print(f"Recall@5 CLIP puro: {test_eval['recall5_clip']:.4f}")
print(f"Recall@1 fusion:    {test_eval['recall1_fusion']:.4f}")
print(f"Recall@5 fusion:    {test_eval['recall5_fusion']:.4f}")
print(f"Sparsity SAE:       {test_eval['sparsity']:.4f}")
print(f"MSE reconstrucción: {test_eval['mse']:.4f}")
print(f"MD5 checkpoint:     {md5_modelo}")
```

```python
cm = confusion_matrix(
    test_eval["labels"].numpy(),
    test_eval["pred_labels"].numpy(),
    labels=list(range(len(CLASES_ORDENADAS))),
)

cm_df = pd.DataFrame(cm, index=CLASES_ORDENADAS, columns=CLASES_ORDENADAS)
cm_df.to_csv(ARTEFACTO_DIR / "matriz_confusion_test.csv")

plt.figure(figsize=(9, 7))
sns.heatmap(cm_df, annot=True, fmt="d", cmap="Blues", cbar=False)
plt.title("Matriz de confusión test - GeoVision-CLIP Late Fusion")
plt.xlabel("Predicción")
plt.ylabel("Clase real")
plt.tight_layout()
plt.savefig(ARTEFACTO_DIR / "matriz_confusion_test.png", dpi=160, bbox_inches="tight")
plt.show()

print(classification_report(
    test_eval["labels"].numpy(),
    test_eval["pred_labels"].numpy(),
    target_names=CLASES_ORDENADAS,
    digits=4,
))
```

## Bloque 6.1 - Diagnóstico de errores por clase

```python
def construir_df_errores(eval_dict, metadata, test_indices):
    df = metadata.iloc[test_indices].reset_index(drop=True).copy()
    labels_np = eval_dict["labels"].numpy()
    pred_np = eval_dict["pred_labels"].numpy()

    df["label_idx"] = labels_np
    df["pred_idx"] = pred_np
    df["clase_real"] = [CLASES_ORDENADAS[i] for i in labels_np]
    df["clase_pred"] = [CLASES_ORDENADAS[i] for i in pred_np]
    df["acierto"] = df["label_idx"] == df["pred_idx"]

    probs_cls = F.softmax(eval_dict["cls_logits"], dim=1).numpy()
    for i, clase in enumerate(CLASES_ORDENADAS):
        df[f"prob_cls_{clase}"] = probs_cls[:, i]

    fused = eval_dict["fused_logits"]
    clip = eval_dict["clip_logits"]
    candidate_labels = eval_dict["candidate_labels"]

    for clase_idx, clase in enumerate(CLASES_ORDENADAS):
        mask = candidate_labels.eq(clase_idx)
        df[f"score_fusion_{clase}"] = fused[:, mask].max(dim=1).values.numpy()
        df[f"score_clip_{clase}"] = clip[:, mask].max(dim=1).values.numpy()

    return df

df_errores = construir_df_errores(test_eval, meta_df, test_idx)
df_errores.to_csv(ARTEFACTO_DIR / "diagnostico_errores_test.csv", index=False)

print("Errores por clase real")
print(pd.crosstab(df_errores["clase_real"], df_errores["clase_pred"], margins=True))
```

```python
for clase in CLASES_ORDENADAS:
    sub = df_errores[df_errores["clase_real"] == clase]
    print(f"\nClase real: {clase}")
    print(f"Aciertos: {sub['acierto'].sum()} / {len(sub)}")
    print("Predicciones:")
    print(sub["clase_pred"].value_counts())
```

```python
so2 = df_errores[df_errores["clase_real"] == "contaminacion_alta_SO2"].copy()
cols_so2 = [
    "clase_real", "clase_pred", "acierto", "ndvi", "ndbi", "scl_pct",
    "score_clip_contaminacion_alta_SO2",
    "score_clip_contaminacion_alta_NO2",
    "score_clip_ozono_anomalo",
    "score_clip_suelo_urbano",
    "score_clip_vegetacion_densa",
    "prob_cls_contaminacion_alta_SO2",
    "prob_cls_contaminacion_alta_NO2",
    "prob_cls_ozono_anomalo",
    "prob_cls_suelo_urbano",
    "prob_cls_vegetacion_densa",
]

cols_so2 = [c for c in cols_so2 if c in so2.columns]
display(so2[cols_so2].sort_values("prob_cls_contaminacion_alta_SO2", ascending=False).head(15))
```

```python
resumen_scores = []
for clase in CLASES_ORDENADAS:
    sub = df_errores[df_errores["clase_real"] == clase]
    fila = {"clase_real": clase, "n": len(sub), "accuracy": sub["acierto"].mean()}
    for pred in CLASES_ORDENADAS:
        fila[f"score_clip_{pred}_mean"] = sub[f"score_clip_{pred}"].mean()
        fila[f"prob_cls_{pred}_mean"] = sub[f"prob_cls_{pred}"].mean()
    resumen_scores.append(fila)

resumen_scores = pd.DataFrame(resumen_scores)
resumen_scores.to_csv(ARTEFACTO_DIR / "resumen_scores_por_clase.csv", index=False)
display(resumen_scores.round(4))
```

```python
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sns.boxplot(
    data=df_errores,
    x="clase_real",
    y="score_clip_contaminacion_alta_SO2",
    hue="acierto",
    ax=axes[0],
)
axes[0].set_title("Score CLIP hacia SO2 por clase real")
axes[0].tick_params(axis="x", rotation=45)

sns.boxplot(
    data=df_errores,
    x="clase_real",
    y="prob_cls_contaminacion_alta_SO2",
    hue="acierto",
    ax=axes[1],
)
axes[1].set_title("Probabilidad auxiliar SO2 por clase real")
axes[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig(ARTEFACTO_DIR / "diagnostico_so2_scores.png", dpi=160, bbox_inches="tight")
plt.show()
```
