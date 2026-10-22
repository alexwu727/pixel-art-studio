from __future__ import annotations
import os
import psycopg2
from mcp.server.fastmcp import FastMCP

from canvas import CanvasState
from palettes import PALETTES, PALETTE_INFO
import export as exp

mcp = FastMCP("pixel-art", stateless_http=False)

_canvases: dict[str, CanvasState] = {}


def _get(canvas_id: str) -> CanvasState:
    if canvas_id not in _canvases:
        raise ValueError(f"Canvas '{canvas_id}' not found. Call create_canvas first.")
    return _canvases[canvas_id]


@mcp.tool()
def create_canvas(
    canvas_id: str,
    width: int,
    height: int,
    palette: str | None = None,
    bg_color: str = "#000000",
) -> str:
    """Create or replace a named canvas."""
    _canvases[canvas_id] = CanvasState.create(canvas_id, width, height, palette, bg_color)
    return f"Canvas '{canvas_id}' created ({width}x{height}, palette={palette or 'none'})."


@mcp.tool()
def list_canvases() -> str:
    """List all active in-memory canvases."""
    if not _canvases:
        return "No active canvases."
    rows = [
        f"  {cid}: {c.width}x{c.height}, palette={c.palette_name or 'none'}, frames={len(c.frames)}"
        for cid, c in _canvases.items()
    ]
    return "Active canvases:\n" + "\n".join(rows)


@mcp.tool()
def set_pixels(canvas_id: str, pixels: list[dict]) -> str:
    """
    Batch-set pixels. Each item: {"x": int, "y": int, "color": str}.
    Color formats: "#RRGGBB", "pico8:7", [r,g,b], CSS name.
    """
    _get(canvas_id).set_pixels(pixels)
    return f"Set {len(pixels)} pixel(s) on '{canvas_id}'."


@mcp.tool()
def fill_rect(canvas_id: str, x: int, y: int, w: int, h: int, color: str) -> str:
    """Fill a rectangle on the canvas."""
    _get(canvas_id).fill_rect(x, y, w, h, color)
    return f"Filled rect ({x},{y} {w}x{h}) on '{canvas_id}'."


@mcp.tool()
def flood_fill(canvas_id: str, x: int, y: int, color: str) -> str:
    """Bucket-fill from (x, y) replacing contiguous same-color pixels."""
    _get(canvas_id).flood_fill(x, y, color)
    return f"Flood-filled from ({x},{y}) on '{canvas_id}'."


@mcp.tool()
def render_from_grid(canvas_id: str, grid: list[list[str]], palette: str | None = None) -> str:
    """
    One-shot: set canvas pixels from a 2D color array.
    grid[y][x] = color string. Creates the canvas if it doesn't exist.
    """
    h = len(grid)
    w = max(len(row) for row in grid) if grid else 0
    if canvas_id not in _canvases:
        _canvases[canvas_id] = CanvasState.create(canvas_id, w, h, palette)
    c = _get(canvas_id)
    c.render_from_grid(grid)
    return f"Rendered {w}x{h} grid onto '{canvas_id}'."


@mcp.tool()
def add_frame(canvas_id: str) -> str:
    """Snapshot the current canvas state as the next animation frame."""
    c = _get(canvas_id)
    c.add_frame()
    return f"Frame {len(c.frames)} added to '{canvas_id}'."


@mcp.tool()
def get_preview(canvas_id: str) -> str:
    """Return a Unicode block-art preview of the canvas (agent 'vision')."""
    c = _get(canvas_id)
    info = f"Canvas '{canvas_id}' ({c.width}x{c.height}, palette={c.palette_name or 'none'}, frames={len(c.frames)}):\n"
    return info + c.text_preview()


@mcp.tool()
def export_png(canvas_id: str, path: str, scale: int = 8, tags: list[str] | None = None) -> str:
    """
    Export canvas as PNG to MinIO and record metadata in PostgreSQL.
    path: relative object path, e.g. 'sprites/hero/idle.png'
    """
    c = _get(canvas_id)
    url = exp.export_png(c, path, scale, tags)
    return f"PNG exported to {url}"


@mcp.tool()
def export_gif(
    canvas_id: str,
    path: str,
    frame_delay_ms: int = 150,
    scale: int = 8,
    tags: list[str] | None = None,
) -> str:
    """
    Export canvas frames as animated GIF to MinIO.
    Requires at least one add_frame call first.
    path: relative object path, e.g. 'sprites/hero/walk.gif'
    """
    c = _get(canvas_id)
    url = exp.export_gif(c, path, frame_delay_ms, scale, tags)
    return f"GIF exported to {url} ({len(c.frames)} frames)"


@mcp.tool()
def list_saved(folder: str | None = None, tags: list[str] | None = None, created_by: str | None = None) -> str:
    """Query saved sprites from PostgreSQL."""
    try:
        with psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "pixelart"),
            user=os.environ.get("POSTGRES_USER", "pixelart"),
            password=os.environ.get("POSTGRES_PASSWORD", "pixelart"),
        ) as conn:
            with conn.cursor() as cur:
                conditions, params = [], []
                if folder:
                    conditions.append("folder LIKE %s")
                    params.append(f"{folder}%")
                if tags:
                    conditions.append("tags @> %s")
                    params.append(tags)
                if created_by:
                    conditions.append("created_by = %s")
                    params.append(created_by)
                where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
                cur.execute(
                    f"SELECT path, file_type, width, height, palette, frame_count, tags, created_by FROM sprites {where} ORDER BY updated_at DESC LIMIT 100",
                    params,
                )
                rows = cur.fetchall()
    except Exception as e:
        return f"DB error: {e}"
    if not rows:
        return "No sprites found."
    lines = [f"  {r[0]} ({r[1]}, {r[2]}x{r[3]}, palette={r[4]}, frames={r[5]}, tags={r[6]}, by={r[7]})" for r in rows]
    return f"{len(rows)} sprite(s):\n" + "\n".join(lines)


@mcp.tool()
def list_named_palettes() -> str:
    """Return available built-in palette names and their sizes."""
    lines = [f"  {name}: {info}" for name, info in PALETTE_INFO.items()]
    return "Available palettes:\n" + "\n".join(lines)


if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", "8001"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
