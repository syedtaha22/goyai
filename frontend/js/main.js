import { startCamera, makeFrameGrabber } from "./camera.js";
import { openGazeSocket } from "./socket.js";

const TARGET_FPS = 20;

const video = document.getElementById("preview");
const overlay = document.getElementById("overlay");
const overlayCtx = overlay.getContext("2d");
const dot = document.getElementById("dot");
const statusEl = document.getElementById("status");
const fpsEl = document.getElementById("fps");
const latencyEl = document.getElementById("latency");

let sentAt = 0;
let frames = 0;
let inFlight = false;

const BOX_COLOURS = { face: "#3ddc84", eye_left: "#4aa8ff", eye_right: "#ffb02e" };

// Boxes arrive as [x, y, w, h] in 0..1 of the camera frame.
function drawBoxes(boxes = {}) {
  overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
  overlayCtx.lineWidth = 3;
  for (const [name, [x, y, w, h]] of Object.entries(boxes)) {
    overlayCtx.strokeStyle = BOX_COLOURS[name] ?? "#fff";
    overlayCtx.strokeRect(x * overlay.width, y * overlay.height, w * overlay.width, h * overlay.height);
  }
}

function onGaze(msg) {
  inFlight = false;
  latencyEl.textContent = Math.round(performance.now() - sentAt);
  frames += 1;
  drawBoxes(msg.boxes);
  if (msg.type !== "gaze") {
    dot.hidden = true;
    statusEl.textContent = msg.type;
    return;
  }
  statusEl.textContent = "tracking";
  dot.hidden = false;
  dot.style.left = `${msg.x * window.innerWidth}px`;
  dot.style.top = `${msg.y * window.innerHeight}px`;
}

async function main() {
  await startCamera(video);
  const grab = makeFrameGrabber(video);
  const ws = await openGazeSocket(onGaze);
  statusEl.textContent = "connected";

  // One frame in flight at a time, so latency never builds up a backlog.
  setInterval(async () => {
    if (inFlight || ws.readyState !== WebSocket.OPEN) return;
    inFlight = true;
    const blob = await grab();
    sentAt = performance.now();
    ws.send(blob);
  }, 1000 / TARGET_FPS);

  setInterval(() => {
    fpsEl.textContent = frames;
    frames = 0;
  }, 1000);
}

main().catch((err) => {
  statusEl.textContent = `error: ${err.message}`;
});
