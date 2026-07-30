"""
utils/gradcam.py

Grad-CAM (Gradient-weighted Class Activation Mapping) visual interpretability tool.
Provides heatmaps highlighting image regions driving model predictions.
"""

import os
import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

from models.model import build_model


def get_default_transform(image_size: int = 224):
    """Standard evaluation image preprocessing pipeline."""
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def load_model_for_gradcam(checkpoint_path: str, config: dict, num_classes: int, device: torch.device):
    """Loads model from checkpoint and sets to eval mode."""
    model = build_model(config, num_classes=num_classes).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


class GradCAMExplainer:
    def __init__(self, model, target_layer=None, device=None, image_size: int = 224):
        """
        Grad-CAM Explainer wrapper.
        Args:
            model: CropDiseaseModel or PyTorch module
            target_layer: layer object for CAM targeting. If None, uses model.get_target_layer()
            device: torch device
            image_size: size to resize input image
        """
        self.model = model
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

        if target_layer is None:
            if hasattr(self.model, "get_target_layer"):
                self.target_layer = self.model.get_target_layer()
            else:
                self.target_layer = self.model.backbone.conv_head
        else:
            self.target_layer = target_layer

        self.target_layers = [self.target_layer]
        self.transform = get_default_transform(image_size)
        self.image_size = image_size

    def explain(self, image_path: str, target_category: int = None):
        """
        Generate Grad-CAM heatmap for an image.
        Returns:
            dict containing:
                - 'cam_image': uint8 RGB image with CAM overlay (224x224x3)
                - 'rgb_image': float32 RGB original image (224x224x3, values 0..1)
                - 'grayscale_cam': 2D float numpy array heatmap (224x224, values 0..1)
                - 'pred_class_idx': Predicted class index
                - 'confidence': Prediction confidence score
        """
        pil_img = Image.open(image_path).convert("RGB")
        resized_img = pil_img.resize((self.image_size, self.image_size))
        rgb_np = np.array(resized_img, dtype=np.float32) / 255.0

        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        # Forward pass to determine top predicted class and confidence
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.softmax(outputs, dim=1)
            conf, pred_idx = probs.max(dim=1)
            pred_class_idx = pred_idx.item()
            confidence = conf.item()

        chosen_target = target_category if target_category is not None else pred_class_idx
        targets = [ClassifierOutputTarget(chosen_target)]

        with GradCAM(model=self.model, target_layers=self.target_layers) as cam:
            grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0, :]
            cam_image = show_cam_on_image(rgb_np, grayscale_cam, use_rgb=True)

        return {
            "cam_image": cam_image,
            "rgb_image": rgb_np,
            "grayscale_cam": grayscale_cam,
            "pred_class_idx": pred_class_idx,
            "confidence": confidence,
        }
