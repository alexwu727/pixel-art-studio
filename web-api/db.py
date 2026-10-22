import os
import psycopg2
import psycopg2.extras
from typing import Optional

_DSN = (
    f"host={os.getenv('POSTGRES_HOST','localhost')} "
    f"port={os.getenv('POSTGRES_PORT','5432')} "
    f"dbname={os.getenv('POSTGRES_DB','pixelart')} "
    f"user={os.getenv('POSTGRES_USER','pixelart')} "
    f"password={os.getenv('POSTGRES_PASSWORD','pixelart')}"
)


def _conn():
    return psycopg2.connect(_DSN, cursor_factory=psycopg2.extras.RealDictCursor)


def get_sprites(
    folder: Optional[str] = None,
    tags: Optional[list[str]] = None,
    created_by: Optional[str] = None,
    file_type: Optional[str] = None,
) -> list[dict]:
    where, params = [], []
    if folder is not None:
        where.append("folder = %s")
        params.append(folder)
    if tags:
        where.append("tags @> %s::text[]")
        params.append(tags)
    if created_by:
        where.append("created_by = %s")
        params.append(created_by)
    if file_type:
        where.append("file_type = %s")
        params.append(file_type)
    sql = "SELECT * FROM sprites" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY updated_at DESC"
    with _conn() as con, con.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def get_sprite(sprite_id: str) -> Optional[dict]:
    with _conn() as con, con.cursor() as cur:
        cur.execute("SELECT * FROM sprites WHERE id = %s", (sprite_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_sprite(path: str, name: str, folder: str, file_type: str,
                  width: int, height: int, palette: Optional[str],
                  frame_count: int, tags: list[str], created_by: str) -> dict:
    sql = """
        INSERT INTO sprites (path, name, folder, file_type, width, height, palette, frame_count, tags, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (path) DO UPDATE SET
            name=EXCLUDED.name, folder=EXCLUDED.folder, width=EXCLUDED.width,
            height=EXCLUDED.height, palette=EXCLUDED.palette,
            frame_count=EXCLUDED.frame_count, tags=EXCLUDED.tags,
            updated_at=now()
        RETURNING *
    """
    with _conn() as con, con.cursor() as cur:
        cur.execute(sql, (path, name, folder, file_type, width, height, palette, frame_count, tags, created_by))
        con.commit()
        return dict(cur.fetchone())


def patch_sprite(sprite_id: str, updates: dict):
    sets = ["updated_at = now()"]
    params = []
    if "name" in updates:
        sets.append("name = %s")
        params.append(updates["name"])
    if "tags" in updates:
        sets.append("tags = %s::text[]")
        params.append(updates["tags"])
    params.append(sprite_id)
    with _conn() as con, con.cursor() as cur:
        cur.execute(f"UPDATE sprites SET {', '.join(sets)} WHERE id = %s", params)
        con.commit()


def delete_sprite(sprite_id: str):
    with _conn() as con, con.cursor() as cur:
        cur.execute("DELETE FROM sprites WHERE id = %s", (sprite_id,))
        con.commit()


def get_folders() -> list[str]:
    with _conn() as con, con.cursor() as cur:
        cur.execute("SELECT DISTINCT folder FROM sprites WHERE folder != '' ORDER BY folder")
        return [r["folder"] for r in cur.fetchall()]
