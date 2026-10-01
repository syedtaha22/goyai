"""
Runtime settings, overridable with environment variables.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The iTracker checkpoint and mean images that GazeEstimator (app/infer.py) loads.
GAZECAPTURE_PYTORCH_DIR = Path(
    os.environ.get("GAZECAPTURE_DIR", ROOT / "third_party" / "GazeCapture" / "pytorch")
)

# Live-camera conventions that must be checked by eye (look left, does the dot go left?).
MIRROR_INPUT = os.environ.get("GAZE_MIRROR_INPUT", "0") == "1"
SWAP_EYES = os.environ.get("GAZE_SWAP_EYES", "0") == "1"

# GazeEstimator outputs centimeters (cm) relative to the camera (x right, y up, so y is negative
# below the camera). These ranges are stretched over the viewport.
RANGE_X_CM = (-8.0, 8.0)
RANGE_Y_CM = (-18.0, -1.0)
