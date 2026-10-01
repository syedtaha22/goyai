"""
Gaze server: serves the frontend and answers camera frames over a WebSocket.

Frames are decoded in memory and never written to disk.
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

from . import config
from .detect import find_face
from .infer import GazeEstimator, cm_to_viewport
from .smoothing import OneEuroFilter

FRONTEND_DIR = config.ROOT / "frontend"

estimator: GazeEstimator | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global estimator
    estimator = GazeEstimator()
    yield


app = FastAPI(title="goyai gaze", lifespan=lifespan)


def _normalise_boxes(crops, width: int, height: int) -> dict[str, list[float]]:
    """
    Boxes as [x, y, w, h] in 0..1 of the original (unflipped) frame.
    """
    out = {}
    for name, (x, y, w, h) in crops.boxes.items():
        nx = 1 - (x + w) / width if config.MIRROR_INPUT else x / width
        out[name] = [round(nx, 4), round(y / height, 4), round(w / width, 4), round(h / height, 4)]
    return out


def process_frame(frame: np.ndarray) -> dict | None:
    """
    Gaze in 0..1 viewport units plus debug boxes, or None if no face was found.
    """
    height, width = frame.shape[:2]
    if config.MIRROR_INPUT:
        frame = cv2.flip(frame, 1)
    crops = find_face(frame)
    if crops is None:
        return None
    x_cm, y_cm = estimator.predict_cm(crops)
    x, y = cm_to_viewport(x_cm, y_cm)
    return {"x": x, "y": y, "cm": [round(x_cm, 2), round(y_cm, 2)],
            "boxes": _normalise_boxes(crops, width, height)}


@app.websocket("/ws/gaze")
async def gaze_socket(ws: WebSocket) -> None:
    await ws.accept()
    filter_x, filter_y = OneEuroFilter(), OneEuroFilter()
    last = time.monotonic()
    try:
        while True:
            data = await ws.receive_bytes()
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                await ws.send_json({"type": "error", "message": "bad frame"})
                continue
            result = await run_in_threadpool(process_frame, frame)
            if result is None:
                filter_x.reset()
                filter_y.reset()
                await ws.send_json({"type": "no_face", "boxes": {}})
                continue
            now = time.monotonic()
            dt, last = now - last, now
            await ws.send_json(
                {
                    "type": "gaze",
                    "x": filter_x(result["x"], dt),
                    "y": filter_y(result["y"], dt),
                    "cm": result["cm"],
                    "boxes": result["boxes"],
                }
            )
    except WebSocketDisconnect:
        pass


# Mounted last so it does not shadow the WebSocket route.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
