# Goyai

An LLM-accelerated Augmentative and Alternative Communication (AAC) tile board for Urdu-speaking users with severe motor-speech impairment.

## About

People who cannot speak intelligibly often use AAC boards, where every word takes a separate physical selection. English-language studies show that large language models can cut that effort a lot by predicting the full sentence a user is building. No published system does this for Urdu or any other South Asian language.

Goyai is a tablet-based tile board that:

- lets users pick one to three icon or word tiles (needs, people, feelings, actions)
- suggests a short ranked list of complete Urdu sentences, including Urdu-English code-mixed ones
- speaks a sentence with Urdu text-to-speech only after the user taps to confirm it

The research question is whether the motor-action savings reported for English AAC users carry over to Urdu, including code-mixed input, and whether users still feel the messages are in their own words.

See [proposal.pdf](proposal.pdf) for the full proposal.

## Status

Early stage. The tech stack and project structure have not been decided yet.

## Eye-tracking experiment (`experiment/eye-tracking` branch)

A standalone prototype exploring gaze as a selection method for the tile board: a browser
captures the webcam feed and streams it to a Python backend, which estimates where on
screen the person is looking and sends a point back to draw.

- `backend/`: FastAPI server, WebSocket endpoint at `/ws/gaze`, face/eye detection and gaze
  estimation.
- `frontend/`: plain HTML/CSS/JS, no build step. Shows the camera preview with detection
  boxes drawn on it, and a dot over the predicted gaze point.
- `third_party/`: git-ignored clones of external repositories, currently
  [CSAILVision/GazeCapture](https://github.com/CSAILVision/GazeCapture). The gaze model
  currently loaded by the backend is its pretrained iTracker checkpoint. GazeCapture's
  licence is research-use only.

### Setup

```bash
mkdir -p third_party
git clone https://github.com/CSAILVision/GazeCapture.git third_party/GazeCapture

cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[ml]"
```

`GAZECAPTURE_DIR` overrides where the backend looks for the GazeCapture clone, if not
`third_party/GazeCapture`.

### Run

```bash
cd backend
.venv/bin/uvicorn app.main:app
```

Open http://localhost:8000, allow camera access. The page shows the camera preview with
the detected face (green) and eye crops (blue/orange) boxed, a HUD with fps/latency, and a
dot that follows the predicted gaze point.

If the dot's direction looks mirrored or the eyes look swapped, restart with:

```bash
GAZE_MIRROR_INPUT=1 .venv/bin/uvicorn app.main:app    # left/right flipped
GAZE_SWAP_EYES=1 .venv/bin/uvicorn app.main:app       # eye crops swapped
```

No camera frames or predictions are written to disk.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
