import tempfile, subprocess, uuid, os
from typing import Dict, List
from app.core.settings import settings
from .minio_service import upload_dir

def _variant_map() -> List[dict]:
    out = []
    for spec in settings.HLS_VARIANTS.split(","):
        spec = spec.strip()
        wh, br = spec.split("_")
        w, h = wh.split("x")
        out.append({"w": int(w), "h": int(h), "br": br})
    return out

def package_to_hls(file_bytes: bytes, original_filename: str) -> Dict:
    work_id = uuid.uuid4().hex[:12]
    tmp_root = tempfile.mkdtemp(prefix="hls_")
    src_path = os.path.join(tmp_root, f"src_{work_id}.mp4")
    with open(src_path, "wb") as f: f.write(file_bytes)

    out_dir = os.path.join(tmp_root, "out")
    os.makedirs(out_dir, exist_ok=True)

    variants = _variant_map()
    for i, v in enumerate(variants):
        rend_dir = os.path.join(out_dir, f"v{i}")
        os.makedirs(rend_dir, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-i", src_path,
            "-filter:v", f"scale=w={v['w']}:h={v['h']}:force_original_aspect_ratio=decrease",
            "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
            "-c:v", "h264", "-profile:v", "main", "-crf", "20",
            "-sc_threshold", "0", "-g", "48", "-keyint_min", "48",
            "-b:v", v["br"], "-maxrate", v["br"], "-bufsize", "2M",
            "-hls_time", str(settings.HLS_SEGMENT_SECONDS),
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", os.path.join(rend_dir, "seg_%04d.ts"),
            os.path.join(rend_dir, "index.m3u8")
        ]
        subprocess.run(cmd, check=True)

    meta = {
        "original": original_filename,
        "variants": [
            {"path": "v0/index.m3u8", "bandwidth": "800000",  "resolution": "426x240"},
            {"path": "v1/index.m3u8", "bandwidth": "1400000", "resolution": "640x360"},
            {"path": "v2/index.m3u8", "bandwidth": "2000000", "resolution": "842x480"},
            {"path": "v3/index.m3u8", "bandwidth": "4000000", "resolution": "1280x720"},
        ],
        "segment_seconds": settings.HLS_SEGMENT_SECONDS,
    }
    return {"out_dir": out_dir, "meta": meta}

def upload_hls_dir(out_dir: str, video_id: str):
    upload_dir(out_dir, video_id)