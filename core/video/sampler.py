import os
import tempfile

def extract_frames(video_path: str, fps: int = 3) -> list[bytes]:
    try:
        import subprocess
        frames = []
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "frame_%03d.jpg")
            subprocess.run([
                "ffmpeg", "-i", video_path,
                "-vf", f"fps={fps}",
                "-q:v", "5", out,
                "-loglevel", "quiet"
            ], check=True)
            for fname in sorted(os.listdir(tmp)):
                if fname.endswith(".jpg"):
                    with open(os.path.join(tmp, fname), "rb") as f:
                        frames.append(f.read())
        return frames[:5]
    except Exception as e:
        print(f"Frame extraction error: {e}")
        return []