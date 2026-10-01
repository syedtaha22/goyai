"""
Find the face with a classical OpenCV Haar cascade and cut the crops the gaze model needs.
"""

from dataclasses import dataclass

import cv2
import numpy as np

GRID = 25

_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Haar boxes are tighter than the face boxes GazeCapture was labelled with, so grow them.
FACE_SCALE = 1.2
FACE_SHIFT_UP = 0.08  # fraction of box height, to include the forehead

# Eye crops are squares cut out of the face crop at fixed proportions.
EYE_SIDE = 0.42  # fraction of face crop width
EYE_CENTER_Y = 0.40  # fraction of face crop height
EYE_CENTER_X = (0.30, 0.70)  # left and right of the crop, as seen in the image


@dataclass
class FaceCrops:
    face: np.ndarray  # RGB uint8
    eye_left: np.ndarray
    eye_right: np.ndarray
    grid: np.ndarray  # float32, GRID*GRID, row-major
    # Pixel boxes (x, y, w, h) in the source frame, for drawing debug overlays.
    boxes: dict[str, tuple[int, int, int, int]]


def _crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    """
    Crop a region from an image, repeating edge pixels for any part outside its bounds.
    """
    height, width = image.shape[:2]
    pad = max(0, -x, -y, x + w - width, y + h - height)
    if pad:
        image = np.pad(image, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        x, y = x + pad, y + pad
    return image[y : y + h, x : x + w]


def _face_grid(fx: int, fy: int, fw: int, fh: int, width: int, height: int) -> np.ndarray:
    grid = np.zeros((GRID, GRID), np.float32)
    x0 = round(fx * GRID / width)
    y0 = round(fy * GRID / height)
    x1 = x0 + round(fw * GRID / width)
    y1 = y0 + round(fh * GRID / height)
    grid[max(0, y0) : min(GRID, y1), max(0, x0) : min(GRID, x1)] = 1.0
    return grid.reshape(-1)


def find_face(frame_bgr: np.ndarray) -> FaceCrops | None:
    gray = cv2.equalizeHist(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY))
    boxes = _cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(80, 80))
    if len(boxes) == 0:
        return None
    x, y, w, h = max(boxes, key=lambda b: b[2] * b[3])  # largest face

    side_w, side_h = round(w * FACE_SCALE), round(h * FACE_SCALE)
    fx = round(x + w / 2 - side_w / 2)
    fy = round(y + h / 2 - side_h / 2 - h * FACE_SHIFT_UP)

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    face = _crop(rgb, fx, fy, side_w, side_h)

    eye = round(side_w * EYE_SIDE)
    cy = round(side_h * EYE_CENTER_Y)
    eye_boxes = [(round(side_w * cx) - eye // 2, cy - eye // 2, eye, eye) for cx in EYE_CENTER_X]
    left, right = (_crop(face, *box) for box in eye_boxes)
    height, width = frame_bgr.shape[:2]
    boxes = {
        "face": (fx, fy, side_w, side_h),
        "eye_left": (fx + eye_boxes[0][0], fy + eye_boxes[0][1], eye, eye),
        "eye_right": (fx + eye_boxes[1][0], fy + eye_boxes[1][1], eye, eye),
    }
    return FaceCrops(face, left, right, _face_grid(fx, fy, side_w, side_h, width, height), boxes)
