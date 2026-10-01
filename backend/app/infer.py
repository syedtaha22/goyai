"""
Loads an iTracker model checkpoint and predicts a gaze point, in centimeters
relative to the camera, from face and eye crops.
"""

import importlib.util

import cv2
import numpy as np
import scipy.io
import torch

from . import config
from .detect import FaceCrops

IM_SIZE = 224


def _load_module(name: str, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GazeEstimator:
    def __init__(self, device: str | None = None) -> None:
        # The model definition and checkpoint are read from config.GAZECAPTURE_PYTORCH_DIR.
        root = config.GAZECAPTURE_PYTORCH_DIR
        if not (root / "checkpoint.pth.tar").is_file():
            raise FileNotFoundError(f"iTracker checkpoint not found in {root}. Set GAZECAPTURE_DIR.")
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        model = _load_module("ITrackerModel", root / "ITrackerModel.py").ITrackerModel()
        state = torch.load(root / "checkpoint.pth.tar", map_location="cpu", weights_only=True)
        model.load_state_dict(state["state_dict"])
        self.model = model.to(self.device).eval()

        def mean(name: str) -> np.ndarray:
            return scipy.io.loadmat(root / name)["image_mean"].astype(np.float32) / 255.0

        self.mean_face = mean("mean_face_224.mat")
        self.mean_left = mean("mean_left_224.mat")
        self.mean_right = mean("mean_right_224.mat")

    def _prepare(self, rgb: np.ndarray, mean: np.ndarray) -> torch.Tensor:
        image = cv2.resize(rgb, (IM_SIZE, IM_SIZE), interpolation=cv2.INTER_LINEAR)
        image = image.astype(np.float32) / 255.0 - mean
        return torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0).to(self.device)

    @torch.inference_mode()
    def predict_cm(self, crops: FaceCrops) -> tuple[float, float]:
        """
        Gaze target in cm relative to the camera (x right, y up).
        """
        left, right = crops.eye_left, crops.eye_right
        if config.SWAP_EYES:
            left, right = right, left
        out = self.model(
            self._prepare(crops.face, self.mean_face),
            self._prepare(left, self.mean_left),
            self._prepare(right, self.mean_right),
            torch.from_numpy(crops.grid).unsqueeze(0).to(self.device),
        )
        x, y = out[0].tolist()
        return x, y


def cm_to_viewport(x_cm: float, y_cm: float) -> tuple[float, float]:
    """
    Stretch the model's cm output range over the viewport, clamped to 0..1.
    """
    (x0, x1), (y0, y1) = config.RANGE_X_CM, config.RANGE_Y_CM
    x = (x_cm - x0) / (x1 - x0)
    y = 1.0 - (y_cm - y0) / (y1 - y0)  # y_cm grows upward, the viewport grows downward
    return min(1.0, max(0.0, x)), min(1.0, max(0.0, y))
