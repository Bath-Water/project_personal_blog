"""Media router — upload, serve, delete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Header, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.response import error, success
from app.services.media_service import MediaError, get_upload, handle_upload, remove_upload

router = APIRouter(prefix="/api/media", tags=["Media"])

MAX_SIZE = 20 * 1024 * 1024


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file (image) with MIME + size validation."""
    if not file.filename:
        return error(400, "missing filename")
    try:
        raw = await file.read()
    except Exception as exc:
        return error(400, f"failed to read file: {exc}")
    if len(raw) > MAX_SIZE:
        return error(400, "file too large")
    try:
        info = await handle_upload(file.filename, raw)
    except MediaError as exc:
        return error(400, str(exc))
    except Exception as exc:
        return error(500, f"upload failed: {exc}")
    return success(info, "uploaded")


@router.get("/{filename}")
async def serve(filename: str):
    """Serve an uploaded file by its relative URL path."""
    # filename includes the /uploads/ prefix (e.g. /uploads/abc.png)
    rel = f"/{filename}" if not filename.startswith("/") else filename
    try:
        data = await get_upload(rel)
    except Exception as exc:
        return error(500, f"failed to read file: {exc}")
    if data is None:
        return error(404, "file not found")
    content, mime = data
    return Response(content=content, media_type=mime)


@router.delete("/{filename}")
async def delete(
    filename: str,
    current_user_header: str | None = Header(None, alias="Authorization"),
):
    """Delete an uploaded file (authenticated)."""
    if not current_user_header:
        return error(401, "missing authorization")
    rel = f"/{filename}" if not filename.startswith("/") else filename
    try:
        ok = await remove_upload(rel)
    except Exception as exc:
        return error(500, f"delete failed: {exc}")
    if not ok:
        return error(404, "file not found")
    return success(None, "deleted")