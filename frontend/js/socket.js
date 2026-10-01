export function openGazeSocket(onMessage) {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${scheme}://${location.host}/ws/gaze`);
  ws.binaryType = "arraybuffer";
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return new Promise((resolve, reject) => {
    ws.onopen = () => resolve(ws);
    ws.onerror = reject;
  });
}
