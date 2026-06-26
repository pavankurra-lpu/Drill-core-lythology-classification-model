"""
ml/models/resnet.py
--------------------
ResNet-50 backbone adapted for lithology classification.

Architecture:
  ResNet-50 (pretrained on ImageNet)
    └─ AdaptiveAvgPool2d  (built-in)
    └─ Custom head:
         Linear(2048 → 512) → BN → ReLU → Dropout
         Linear(512  → 256) → BN → ReLU → Dropout
         Linear(256  → num_classes)
"""

from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import ResNet50_Weights

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------

class LithologyResNet(nn.Module):
    """
    ResNet-50 fine-tuned for lithology / rock-type classification.

    Parameters
    ----------
    num_classes : int
        Number of output classes.
    pretrained : bool
        Load ImageNet pre-trained weights for the backbone.
    dropout_rate : float
        Dropout probability applied in the classification head.
    freeze_backbone : bool
        If True, freeze all backbone parameters initially.
        Call `unfreeze_backbone()` to release them.
    """

    _BACKBONE_OUT_FEATURES: int = 2048  # ResNet-50 layer4 output channels

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
        weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        backbone = models.resnet50(weights=weights)

        # Strip the original fully-connected head; keep everything else.
        self.backbone = nn.Sequential(
            backbone.conv1,
            backbone.bn1,
            backbone.relu,
            backbone.maxpool,
            backbone.layer1,
            backbone.layer2,
            backbone.layer3,
            backbone.layer4,
        )
        self.avgpool = backbone.avgpool     # AdaptiveAvgPool2d(1, 1)

        if freeze_backbone:
            self._freeze_backbone()

        # ------------------------------------------------------------------ #
        # Custom classification head                                           #
        # ------------------------------------------------------------------ #
        self.classifier = nn.Sequential(
            # Block 1
            nn.Linear(self._BACKBONE_OUT_FEATURES, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            # Block 2
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            # Output
            nn.Linear(256, num_classes),
        )

        self._init_head()
        logger.info(
            "LithologyResNet | classes=%d | pretrained=%s | dropout=%.2f",
            num_classes, pretrained, dropout_rate,
        )

    # ---------------------------------------------------------------------- #
    # Helpers                                                                  #
    # ---------------------------------------------------------------------- #

    def _init_head(self) -> None:
        """Kaiming-initialise Linear layers and reset BatchNorm in the head."""
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def _freeze_backbone(self) -> None:
        """Freeze all backbone (convolutional) parameters."""
        for param in self.backbone.parameters():
            param.requires_grad = False
        logger.info("ResNet-50 backbone frozen.")

    def unfreeze_backbone(self, unfreeze_layers: Optional[int] = None) -> None:
        """
        Unfreeze backbone layers.

        Parameters
        ----------
        unfreeze_layers : int, optional
            Number of top-level Sequential children to unfreeze (from the end).
            None = unfreeze everything.
        """
        children = list(self.backbone.children())
        if unfreeze_layers is None:
            targets = children
        else:
            targets = children[-unfreeze_layers:]

        for layer in targets:
            for param in layer.parameters():
                param.requires_grad = True

        logger.info(
            "ResNet-50 backbone unfrozen (%s layers).",
            "all" if unfreeze_layers is None else unfreeze_layers,
        )

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
        x = self.backbone(x)           # (B, 2048, h, w)
        x = self.avgpool(x)            # (B, 2048, 1, 1)
        x = torch.flatten(x, 1)       # (B, 2048)
        x = self.classifier(x)        # (B, num_classes)
        return x

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Return spatial feature maps (before pooling) — used for Grad-CAM."""
        return self.backbone(x)

    # ---------------------------------------------------------------------- #
    # Info                                                                     #
    # ---------------------------------------------------------------------- #

    def get_num_parameters(self, trainable_only: bool = True) -> int:
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())

    def __repr__(self) -> str:
        return (
            f"LithologyResNet("
            f"num_classes={self.num_classes}, "
            f"backbone=resnet50, "
            f"params={self.get_num_parameters():,})"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_resnet_model(
    num_classes: int = 15,
    pretrained: bool = True,
    dropout_rate: float = 0.4,
    freeze_backbone: bool = False,
    checkpoint_path: Optional[str] = None,
    device: Optional[torch.device] = None,
) -> LithologyResNet:
    """
    Build and (optionally) restore a LithologyResNet.

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
        Path to a saved ``state_dict`` or trainer checkpoint.
    device : torch.device, optional
        Move model to this device after loading.

    Returns
    -------
    LithologyResNet
    """
    model = LithologyResNet(
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


# Alias
get_model = get_resnet_model


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_weights(
    model: LithologyResNet,
    path: str,
    device: Optional[torch.device] = None,
) -> None:
    """Load a checkpoint file into *model* in-place."""
    map_location = device if device is not None else torch.device("cpu")
    checkpoint = torch.load(path, map_location=map_location)

    if isinstance(checkpoint, dict):
        state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint))
    else:
        state_dict = checkpoint

    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        logger.warning("Missing keys when loading checkpoint: %s", missing)
    if unexpected:
        logger.warning("Unexpected keys when loading checkpoint: %s", unexpected)
    logger.info("Loaded ResNet-50 weights from '%s'.", path)
