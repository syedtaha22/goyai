const WIDTH = 640;
const HEIGHT = 480;
const JPEG_QUALITY = 0.7;

export async function startCamera(video) {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: WIDTH, height: HEIGHT, facingMode: "user" },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
}

// Returns a function that grabs the current video frame as a JPEG Blob.
export function makeFrameGrabber(video) {
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH;
  canvas.height = HEIGHT;
  const ctx = canvas.getContext("2d");
  return () => {
    ctx.drawImage(video, 0, 0, WIDTH, HEIGHT);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY));
  };
}
