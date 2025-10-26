import jwt
from jwt import InvalidTokenError
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from app.core.settings import settings
from app.services.minio_service import get_object_stream

router = APIRouter(tags=["Stream"])

def _verify_token(token: str, video_id: str, origin_hdr: str | None):
    """
    Verify JWT and enforce:
      - valid signature/claims
      - vid matches path or is "*"
      - request Origin header matches 'orig' claim (per-domain key)
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except InvalidTokenError as e:
        raise HTTPException(403, f"Invalid token: {e}")

    vid = payload.get("vid")
    if vid not in (video_id, "*"):
        raise HTTPException(403, "Token not valid for this video")

    token_origin = payload.get("orig")
    if not token_origin:
        raise HTTPException(403, "Token missing origin claim")

    # Enforce exact origin match. Browsers include the Origin header for
    # cross-origin media requests; if absent, we deny.
    if not origin_hdr or origin_hdr.strip().lower() != token_origin.strip().lower():
        raise HTTPException(403, "Origin not allowed for this token")

    return payload


@router.get("/{video_id}/master.m3u8")
def master_playlist(video_id: str, request: Request):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(401, "Missing token")

    _verify_token(token, video_id, request.headers.get("Origin"))

    variants = [
        ("v0", "800000", "426x240"),
        ("v1", "1400000", "640x360"),
        ("v2", "2000000", "842x480"),
        ("v3", "4000000", "1280x720"),
    ]
    q = f"?token={token}"
    lines = ["#EXTM3U"]
    for v, bw, res in variants:
        lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={res}")
        lines.append(f"{v}/index.m3u8{q}")
    return PlainTextResponse(
        "\n".join(lines),
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE}"},
    )


@router.get("/{video_id}/{path:path}")
def playlist_or_segment(video_id: str, path: str, request: Request):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(401, "Missing token")

    _verify_token(token, video_id, request.headers.get("Origin"))

    object_path = f"{video_id}/{path}"

    # Rewrite sub-playlists so every segment carries the same token.
    if path.endswith(".m3u8"):
        data = get_object_stream(object_path).read().decode("utf-8")
        modified = []
        for line in data.splitlines():
            if line.strip() and not line.startswith("#") and "?" not in line:
                line = f"{line}?token={token}"
            modified.append(line)
        data = "\n".join(modified)
        return PlainTextResponse(
            data,
            media_type="application/vnd.apple.mpegurl",
            headers={"Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE}"},
        )

    # Otherwise stream binary (TS/MP4)
    stream = get_object_stream(object_path)
    if path.endswith(".mp4"):
        media = "video/mp4"
    else:
        media = "video/MP2T"

    headers = {"Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE}"}

    def _iter():
        try:
            for d in stream.stream(32 * 1024):
                yield d
        finally:
            stream.close()

    return StreamingResponse(_iter(), media_type=media, headers=headers)