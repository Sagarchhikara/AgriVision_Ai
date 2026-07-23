"""
models/model.py

EfficientNet-B0 classifier wrapper for crop disease diagnosis, built via `timm`
so we get ImageNet-pretrained weights and a clean way to swap the classifier head.

Design notes
------------
- timm is used instead of torchvision.models because it exposes `num_classes`
  directly in `create_model`, so we don't have to manually inspect and replace
  the final layer (different for every architecture) — this also makes it
  trivial to swap in ResNet50 or MobileViT later for the comparison models
  mentioned in the roadmap, by changing one string.
- freeze_backbone/unfreeze_backbone implement the two-stage transfer learning
  strategy from the plan:
    Stage 1: freeze backbone, train only the classifier head (fast, stabilizes
             the new head before touching pretrained features)
    Stage 2: unfreeze everything, fine-tune end-to-end at a lower LR
- get_trainable_params() is used by main.py to build the optimizer, so the
  optimizer only ever sees params that currently require grad.
"""

import timm
import torch.nn as nn


class CropDiseaseModel(nn.Module):
    def __init__(self, model_name: str = "efficientnet_b0", num_classes: int = 15, pretrained: bool = True):
        super().__init__()
        self.model_name = model_name
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=num_classes,
        )

    def forward(self, x):
        return self.backbone(x)

    def freeze_backbone(self):
        """
        Freeze all parameters except the final classifier layer.
        timm models expose the classifier via get_classifier(); we freeze
        everything, then explicitly re-enable grad on the classifier's params.
        """
        for param in self.backbone.parameters():
            param.requires_grad = False
        classifier = self.backbone.get_classifier()
        for param in classifier.parameters():
            param.requires_grad = True

    def unfreeze_backbone(self):
        """Unfreeze all parameters for end-to-end fine-tuning (Stage 2)."""
        for param in self.backbone.parameters():
            param.requires_grad = True

    def get_trainable_params(self):
        """Return only params with requires_grad=True, for optimizer construction."""
        return [p for p in self.backbone.parameters() if p.requires_grad]

    def get_target_layer(self):
        """
        Returns the last convolutional layer, needed later for Grad-CAM (Phase 2).
        For EfficientNet in timm, this is backbone.conv_head.
        """
        return self.backbone.conv_head


def build_model(config: dict, num_classes: int) -> CropDiseaseModel:
    """
    Build a CropDiseaseModel from config.yaml's `model` section.

    Example config.yaml:
        model:
          name: efficientnet_b0
          pretrained: true
    """
    return CropDiseaseModel(
        model_name=config["model"]["name"],
        num_classes=num_classes,
        pretrained=config["model"]["pretrained"],
    )