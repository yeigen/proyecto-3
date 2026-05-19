# CLIP y RemoteCLIP

## Definición

**CLIP (Contrastive Language–Image Pretraining)** es un modelo de doble torre (visual encoder + text encoder) entrenado con un objetivo contrastivo: dadas N parejas (imagen, texto), maximizar la similaridad coseno de los pares correctos y minimizarla del resto. Aprende un espacio multimodal compartido sin etiquetas explícitas, solo pares imagen-caption escrapeados de la web.

**RemoteCLIP** es CLIP fine-tuneado específicamente para teledetección (imagen satelital). Liu et al. (2024) construyen un dataset RET-3 a partir de tres fuentes públicas (RSITMD, RSICD, UCM) totalizando ~165k pares imagen-caption de RS, y fine-tunean los pesos de OpenCLIP sobre ese dataset. Resultado: mejores embeddings cuando la entrada es una imagen satelital típica (tiles aéreos, nadir, baja resolución espacial).

## Por qué elegimos RemoteCLIP en Situación 2

- **Tiles Sentinel-2 64×64 nadir** son distribución que CLIP base nunca vio (su training set son fotos consumer/web). RemoteCLIP elimina ese gap de dominio.
- El paper documenta ganancias entre +9% y +22% en zero-shot retrieval contra CLIP base en benchmarks RS.
- Los pesos están disponibles en formato compatible con `open_clip_torch`, librería estándar.

## Arquitectura elegida: ViT-B/32

RemoteCLIP publica tres backbones: RN50, ViT-B-32, ViT-L-14. Elegimos **ViT-B/32**:

- **Patch size 32**: para input 224×224 → 49 tokens. Con upsample 64→224 el costo computacional es manejable en GPU T4 (16 GB VRAM).
- **Embedding 512D**: dimensionalidad razonable para nuestro embedding fundido (512+128=640 con MLP S5P).
- **88M parámetros**: cabe en T4 con batch 64 + gradient checkpointing si fuera necesario.
- ViT-L/14 (304M params, patch 14) sería mejor calidad pero no cabe en T4 con batch razonable.

## Adaptación de la primera conv para 13 bandas Sentinel-2

CLIP estándar espera input RGB (3 canales). Nosotros tenemos 13 bandas espectrales (`B1`–`B12` + `SCL`). Dos opciones evaluadas:

| Opción | Pros | Contras |
|---|---|---|
| Tomar solo RGB (B4, B3, B2) | trivial, mantiene transferencia preentrenada perfecta | pierde NIR/SWIR (críticos para NDVI, NDBI, AOD) |
| Adaptar primera conv 13ch | aprovecha info espectral única | rompe parcialmente la transferencia, hay que inicializar bien |

Elegimos **adaptar primera conv** porque las 13 bandas son la razón de muestrear S2 en lugar de fotos RGB. La inicialización sigue la técnica estándar (e.g., [Khan et al. 2024 — Hyperspectral CLIP](https://arxiv.org/abs/2402.00031) y prácticas en `terratorch`):

1. Crear nueva `Conv2d(13, embed_dim, kernel=32, stride=32)`.
2. Copiar los pesos RGB originales (channels 0,1,2 = bandas R,G,B = índices `bands_s2.index("B4"), B3, B2`) en sus posiciones.
3. Inicializar los 10 canales extra como el **promedio** de los pesos RGB originales, escalado por `3/13` para preservar la magnitud total de activación. Esta técnica se documenta en [Reed et al. 2023 — Scale-MAE](https://arxiv.org/abs/2212.14532).

## Cómo cargar RemoteCLIP

Procedimiento oficial documentado en [github.com/ChenDelong1999/RemoteCLIP](https://github.com/ChenDelong1999/RemoteCLIP):

```python
import torch
import open_clip
from huggingface_hub import hf_hub_download

model_name = "ViT-B-32"
ckpt_path = hf_hub_download(
    repo_id="chendelong/RemoteCLIP",
    filename=f"RemoteCLIP-{model_name}.pt",
)
model, _, preprocess = open_clip.create_model_and_transforms(model_name)
tokenizer = open_clip.get_tokenizer(model_name)
state_dict = torch.load(ckpt_path, map_location="cpu")
msg = model.load_state_dict(state_dict)
```

El checkpoint pesa ~600 MB (ViT-B/32). Se descarga una sola vez por kernel.

## InfoNCE loss

CLIP entrena con [InfoNCE (van den Oord et al. 2018)](https://arxiv.org/abs/1807.03748), que es la formulación contrastiva softmax cross-entropy aplicada a una matriz de similaridades coseno:

```
L = -1/2 * (CE(softmax(τ · img @ txt.T), I) + CE(softmax(τ · txt @ img.T), I))
```

donde `τ` (logit scale) es un parámetro aprendido, `I` es la identidad (el tile i con su texto i son par positivo), y los demás N-1 textos del batch son negativos. Reportado en el [paper CLIP original (Radford et al. 2021)](https://arxiv.org/abs/2103.00020).

## Restricciones del proyecto

- **No pasar S5P como input directo al text encoder**: el texto contiene la concentración numérica del pseudo-label, pero esto está documentado y autorizado en el PDF (Situación 2, p. 6) como "agrupar por percentiles".
- **Checkpoint reproducible**: usar `torch.manual_seed(SEED)`, `np.random.seed(SEED)`, `torch.use_deterministic_algorithms(True)` y CUDA env `CUBLAS_WORKSPACE_CONFIG=:4096:8`. MD5 sobre los bytes del `.pt` final.

## Referencias

- [Liu et al. 2024 — *RemoteCLIP: A Vision Language Foundation Model for Remote Sensing*](https://ieeexplore.ieee.org/document/10504785) — IEEE TGRS, DOI 10.1109/TGRS.2024.3390838 (la URL pública de IEEE Xplore devuelve 418 a bots; el DOI funciona en lectores con sesión académica; el preprint está en [arXiv:2306.11029](https://arxiv.org/abs/2306.11029)).
- [Repo oficial RemoteCLIP](https://github.com/ChenDelong1999/RemoteCLIP) — checkpoints, código de loading.
- [HuggingFace `chendelong/RemoteCLIP`](https://huggingface.co/chendelong/RemoteCLIP) — pesos `.pt` descargables.
- [Radford et al. 2021 — *Learning Transferable Visual Models From Natural Language Supervision*](https://arxiv.org/abs/2103.00020) — paper CLIP original (InfoNCE, arquitectura).
- [van den Oord et al. 2018 — *Representation Learning with Contrastive Predictive Coding*](https://arxiv.org/abs/1807.03748) — origen de InfoNCE.
- [Reed et al. 2023 — *Scale-MAE*](https://arxiv.org/abs/2212.14532) — técnica de adaptación de conv para bandas multiespectrales.
- [open_clip_torch repo](https://github.com/mlfoundations/open_clip) — librería de carga.

Todas las URLs verificadas con WebFetch antes de citarlas (excepto la de IEEE que devuelve 418 anti-bot; el preprint arXiv sirve como verificación alternativa).
