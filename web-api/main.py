from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io

from db import get_sprites, get_sprite, upsert_sprite, delete_sprite, patch_sprite, get_folders
from storage import upload_file, download_file, delete_file, get_presigned_url
from palettes import PALETTES

app = FastAPI(title="Pixel Art Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SpritePatch(BaseModel):
    name: Optional[str] = None
    tags: Optional[list[str]] = None


class SpriteCreate(BaseModel):
    path: str
    name: str
    folder: str
    file_type: str = "png"
    width: int
    height: int
    palette: Optional[str] = None
    frame_count: int = 1
    tags: list[str] = []
    created_by: str = "manual"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sprites", status_code=201)
def create_sprite(body: SpriteCreate):
    return upsert_sprite(
        path=body.path, name=body.name, folder=body.folder,
        file_type=body.file_type, width=body.width, height=body.height,
        palette=body.palette, frame_count=body.frame_count,
        tags=body.tags, created_by=body.created_by,
    )


@app.get("/sprites")
def list_sprites(
    folder: Optional[str] = None,
    tags: Optional[str] = Query(None, description="comma-separated"),
    created_by: Optional[str] = None,
    file_type: Optional[str] = None,
):
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return get_sprites(folder=folder, tags=tag_list, created_by=created_by, file_type=file_type)


@app.get("/sprites/{sprite_id}")
def get_sprite_meta(sprite_id: str):
    row = get_sprite(sprite_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@app.get("/sprites/{sprite_id}/file")
def get_sprite_file(sprite_id: str):
    row = get_sprite(sprite_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    data = download_file(row["path"])
    content_type = "image/gif" if row["file_type"] == "gif" else "image/png"
    return StreamingResponse(io.BytesIO(data), media_type=content_type)


@app.put("/sprites/{sprite_id}/file")
async def put_sprite_file(sprite_id: str, file: UploadFile = File(...)):
    row = get_sprite(sprite_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    data = await file.read()
    upload_file(data, row["path"], file.content_type or "image/png")
    patch_sprite(sprite_id, {})  # bumps updated_at
    return {"path": row["path"]}


@app.patch("/sprites/{sprite_id}")
def update_sprite(sprite_id: str, body: SpritePatch):
    row = get_sprite(sprite_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    patch_sprite(sprite_id, updates)
    return get_sprite(sprite_id)


@app.delete("/sprites/{sprite_id}")
def remove_sprite(sprite_id: str):
    row = get_sprite(sprite_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    delete_file(row["path"])
    delete_sprite(sprite_id)
    return {"deleted": sprite_id}


@app.get("/folders")
def list_folders():
    return get_folders()


@app.get("/palettes")
def list_palettes():
    return {name: [list(c) for c in colors] for name, colors in PALETTES.items()}
