"""
ml/models/efficientnet.py
--------------------------
EfficientNet-B3 backbone adapted for lithology classification.

Architecture:
  EfficientNet-B3 (pretrained on ImageNet)
    └─ AdaptiveAvgPool2d  (built-in)
    └─ Custom head:
         Linear(1536 → 512) → BN → SiLU → Dropout
         Linear(512  → 256) → BN → SiLU → Dropout
         Linear(256  → num_classes)
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import EfficientNet_B3_Weights

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------

class LithologyEfficientNet(nn.Module):
    """
    EfficientNet-B3 fine-tuned for lithology / rock-type classification.

    Parameters
    ----------
    num_classes : int
        Number of output classes.
    pretrained : bool
        Load ImageNet pre-trained weights for the backbone.
    dropout_rate : float
        Dropout probability applied in the classification head.
    freeze_backbone : bool
        If True, freeze all backbone parameters during the first warm-up
        phase. Call `unfreeze_backbone()` to release them.
    """

    # EfficientNet-B3 final feature dimension before the classifier
    _BACKBONE_OUT_FEATURES: int = 1536

    def __init__(
        self,
        num_classes: int = 15,
        pretrained: bool = True,
        dropout_rate: float = 0.4,
        freeze_backbone: bool = False,
    ) -> None:
        super().__init__()

        self.num_classes = num_classes
        self.dropout_rate = dropout_rate

        # ------------------------------------------------------------------ #
        # Backbone                                                             #
        # ------------------------------------------------------------------ #
        weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = models.efficientnet_b3(weights=weights)

        # Keep only the feature-extraction part (everything except the
        # original EfficientNet classifier head).
        self.features = backbone.features        # Conv + MBConv blocks
        self.avgpool = backbone.avgpool          # AdaptiveAvgPool2d(1)

        if freeze_backbone:
            self._freeze_backbone()

        # ------------------------------------------------------------------ #
        # Custom classification head                                           #
        # ------------------------------------------------------------------ #
        self.classifier = nn.Sequential(
            # Block 1
            nn.Linear(self._BACKBONE_OUT_FEATURES, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            # Block 2
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.SiLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            # Output
            nn.Linear(256, num_classes),
        )

        self._init_head()
        logger.info(
            "LithologyEfficientNet | classes=%d | pretrained=%s | dropout=%.2f",
            num_classes, pretrained, dropout_rate,
        )

    # ---------------------------------------------------------------------- #
    # Helpers                                                                  #
    # ---------------------------------------------------------------------- #

    def _init_head(self) -> None:
        """Kaiming-initialise all Linear layers in the custom head."""
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def _freeze_backbone(self) -> None:
        """Freeze all backbone parameters."""
        for param in self.features.parameters():
            param.requires_grad = False
        logger.info("Backbone frozen.")

    def unfreeze_backbone(self, unfreeze_from_block: int = 0) -> None:
        """
        Unfreeze backbone layers progressively.

        Parameters
        ----------
        unfreeze_from_block : int
            Unfreeze all MBConv blocks at index >= this value (0 = all).
        """
        for name, param in self.features.named_parameters():
            # features is nn.Sequential; first token of name is the block index
            try:
                block_idx = int(name.split(".")[0])
                if block_idx >= unfreeze_from_block:
                    param.requires_grad = True
            except ValueError:
                param.requires_grad = True
        logger.info("Backbone unfrozen from block %d.", unfreeze_from_block)

    # ---------------------------------------------------------------------- #
    # Forward                                                                  #
    # ---------------------------------------------------------------------- #

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        x : torch.Tensor  shape (B, 3, H, W)

        Returns
        -------
        logits : torch.Tensor  shape (B, num_classes)
        """
        x = self.features(x)           # (B, 1536, h, w)
        x = self.avgpool(x)            # (B, 1536, 1, 1)
        x = torch.flatten(x, 1)       # (B, 1536)
        x = self.classifier(x)        # (B, num_classes)
        return x

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Return feature map (before global pooling) for Grad-CAM."""
        return self.features(x)

    # ---------------------------------------------------------------------- #
    # Info                                                                     #
    # ---------------------------------------------------------------------- #

    def get_num_parameters(self, trainable_only: bool = True) -> int:
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())

    def __repr__(self) -> str:
        return (
            f"LithologyEfficientNet("
            f"num_classes={self.num_classes}, "
            f"backbone=efficientnet_b3, "
            f"params={self.get_num_parameters():,})"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_efficientnet_model(
    num_classes: int = 15,
    pretrained: bool = True,
    dropout_rate: float = 0.4,
    freeze_backbone: bool = False,
    checkpoint_path: Optional[str] = None,
    device: Optional[torch.device] = None,
) -> LithologyEfficientNet:
    """
    Build and (optionally) restore a LithologyEfficientNet.

    Parameters
    ----------
    num_classes : int
        Number of rock-type classes.
    pretrained : bool
        Use ImageNet pre-trained backbone weights.
    dropout_rate : float
        Head dropout probability.
    freeze_backbone : bool
        Freeze backbone on instantiation.
    checkpoint_path : str, optional
        Path to a saved ``state_dict`` to restore.
    device : torch.device, optional
        Move model to this device after loading.

    Returns
    -------
    LithologyEfficientNet
    """
    model = LithologyEfficientNet(
        num_classes=num_classes,
        pretrained=pretrained,
        dropout_rate=dropout_rate,
        freeze_backbone=freeze_backbone,
    )

    if checkpoint_path is not None:
        _load_weights(model, checkpoint_path, device)

    if device is not None:
        model = model.to(device)

    return model


# Alias for backwards compat
get_model = get_efficientnet_model


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_weights(
    model: LithologyEfficientNet,
    path: str,
    device: Optional[torch.device] = None,
) -> None:
    """Load a checkpoint file into *model* in-place."""
    map_location = device if device is not None else torch.device("cpu")
    checkpoint = torch.load(path, map_location=map_location)

    # Support both raw state_dict and our trainer checkpoint format
    if isinstance(checkpoint, dict):
        state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint))
    else:
        state_dict = checkpoint

    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        logger.warning("Missing keys when loading checkpoint: %s", missing)
    if unexpected:
        logger.warning("Unexpected keys when loading checkpoint: %s", unexpected)
    logger.info("Loaded EfficientNet weights from '%s'.", path)
