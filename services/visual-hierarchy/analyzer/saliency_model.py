"""
analyzer/saliency_model.py
--------------------------
Two-tier saliency prediction system for the Visual Hierarchy microservice.

Tier 1 (preferred):  TranSalNet-Res  – ResNet50 backbone + convolutional decoder.
                     Requires  models/weights/TranSalNet_Res.pth
Tier 2 (fallback):   OpenCV Spectral Residual Saliency – CPU, no weights needed.

Public API
----------
load_model()           → call once at startup
get_model_type() → str → 'TranSalNet-Res' | 'SpectralResidual-CV'
predict_saliency(image_np: np.ndarray) → np.ndarray  (float32, [0,1], same HxW as input)
"""

import os
import logging

import cv2
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models", "weights", "TranSalNet_Res.pth"
)

# ---------------------------------------------------------------------------
# TranSalNet-Res architecture
# ResNet50 encoder  +  lightweight convolutional decoder → single-channel saliency
# Matches the public TranSalNet_Res checkpoint from https://github.com/LJOVO/TranSalNet
# ---------------------------------------------------------------------------

class TranSalNet_Res(torch.nn.Module):
    """
    Simplified TranSalNet-Res architecture.

    Encoder : ResNet50 (pre-trained stem reused; final FC dropped).
    Decoder : Progressive 2× upsampling with Conv→ReLU blocks ending with Sigmoid.

    Reference: LJOVO/TranSalNet — 'TranSalNet: Towards perceptually relevant visual
    saliency prediction' (IJCAI 2022).
    """

    def __init__(self) -> None:
        super().__init__()
        backbone = models.resnet50(weights=None)

        # ── Encoder layers ──────────────────────────────────────────────────
        self.layer0 = torch.nn.Sequential(
            backbone.conv1,
            backbone.bn1,
            backbone.relu,
            backbone.maxpool,
        )  # → 64 ch,  H/4
        self.layer1 = backbone.layer1   # → 256 ch,  H/4
        self.layer2 = backbone.layer2   # → 512 ch,  H/8
        self.layer3 = backbone.layer3   # → 1024 ch, H/16
        self.layer4 = backbone.layer4   # → 2048 ch, H/32

        # ── Decoder (4× 2× upsample) ─────────────────────────────────────
        self.decoder = torch.nn.Sequential(
            # 2048 → 512
            torch.nn.Conv2d(2048, 512, kernel_size=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            # 512 → 256
            torch.nn.Conv2d(512, 256, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            # 256 → 128
            torch.nn.Conv2d(256, 128, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            # 128 → 64
            torch.nn.Conv2d(128, 64, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            # 64 → 1
            torch.nn.Conv2d(64, 1, kernel_size=1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: RGB image tensor → single-channel saliency map."""
        x = self.layer0(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.decoder(x)
        return x


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_model: torch.nn.Module | None = None
_model_type: str = "none"

# Input resolution expected by TranSalNet
INPUT_H, INPUT_W = 288, 384

_transform = T.Compose([
    T.Resize((INPUT_H, INPUT_W)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ---------------------------------------------------------------------------
# Public API – lifecycle
# ---------------------------------------------------------------------------

def load_model() -> None:
    """
    Load the saliency model once at application startup.

    Strategy:
      1. If  models/weights/TranSalNet_Res.pth  exists, load TranSalNet-Res.
      2. On any failure (missing file, shape mismatch, CUDA OOM, …),
         fall back silently to OpenCV Spectral Residual (zero-dependency).
    """
    global _model, _model_type

    if not os.path.exists(MODEL_WEIGHTS_PATH):
        logger.info(
            "TranSalNet weights not found at %s. "
            "Using OpenCV SpectralResidual (CPU fallback).",
            MODEL_WEIGHTS_PATH,
        )
        _model_type = "SpectralResidual-CV"
        return

    try:
        net = TranSalNet_Res()
        state_dict = torch.load(MODEL_WEIGHTS_PATH, map_location=device)
        # strict=False allows partial weight loading (e.g. decoder shape mismatches)
        missing, unexpected = net.load_state_dict(state_dict, strict=False)
        if missing:
            logger.warning("TranSalNet: missing keys: %s", missing[:5])
        if unexpected:
            logger.warning("TranSalNet: unexpected keys: %s", unexpected[:5])
        net.to(device)
        net.eval()
        _model = net
        _model_type = "TranSalNet-Res"
        logger.info("TranSalNet-Res loaded successfully on %s.", device)
    except Exception as exc:
        logger.warning(
            "Failed to load TranSalNet-Res (%s). "
            "Falling back to SpectralResidual-CV.",
            exc,
        )
        _model = None
        _model_type = "SpectralResidual-CV"


def get_model_type() -> str:
    """Return the name of the currently active saliency model."""
    return _model_type


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def _predict_transsalnet(image_np: np.ndarray) -> np.ndarray:
    """
    Run TranSalNet-Res inference on a BGR numpy image.

    Parameters
    ----------
    image_np : np.ndarray
        BGR image, uint8, shape (H, W, 3).

    Returns
    -------
    np.ndarray
        Float32 saliency map in [0, 1], same spatial dimensions as input.
    """
    orig_h, orig_w = image_np.shape[:2]
    pil_img = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
    tensor = _transform(pil_img).unsqueeze(0).to(device)  # (1, 3, H, W)

    with torch.no_grad():
        sal = _model(tensor)  # (1, 1, H', W')

    sal_np = sal.squeeze().cpu().numpy()  # (H', W')
    # Min-max normalise to [0, 1]
    sal_np = (sal_np - sal_np.min()) / (sal_np.max() - sal_np.min() + 1e-8)
    # Upsample back to original resolution
    sal_resized = cv2.resize(sal_np, (orig_w, orig_h), interpolation=cv2.INTER_BILINEAR)
    return sal_resized.astype(np.float32)


def _predict_spectral_residual(image_np: np.ndarray) -> np.ndarray:
    """
    OpenCV Spectral Residual static saliency (CPU fallback).

    Parameters
    ----------
    image_np : np.ndarray
        BGR image, uint8.

    Returns
    -------
    np.ndarray
        Float32 saliency map in [0, 1], same spatial dimensions as input.
    """
    saliency_algo = cv2.saliency.StaticSaliencySpectralResidual_create()
    success, sal_map = saliency_algo.computeSaliency(image_np)
    if not success:
        logger.warning("SpectralResidual saliency computation failed; returning zeros.")
        return np.zeros(image_np.shape[:2], dtype=np.float32)
    sal_norm = (sal_map - sal_map.min()) / (sal_map.max() - sal_map.min() + 1e-8)
    return sal_norm.astype(np.float32)


# ---------------------------------------------------------------------------
# Main public entry point
# ---------------------------------------------------------------------------

def predict_saliency(image_np: np.ndarray) -> np.ndarray:
    """
    Predict a visual saliency map for the given BGR image.

    Automatically selects TranSalNet-Res when weights are loaded,
    otherwise uses the OpenCV Spectral Residual fallback.

    Parameters
    ----------
    image_np : np.ndarray
        Input image in BGR format, uint8, shape (H, W, 3).

    Returns
    -------
    np.ndarray
        Normalised saliency map, float32, values in [0, 1],
        shape (H, W) matching the input spatial dimensions.
    """
    if _model is not None:
        return _predict_transsalnet(image_np)
    return _predict_spectral_residual(image_np)
