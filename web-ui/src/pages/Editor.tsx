import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { fetchSprite, fetchPalettes, uploadSpriteFile, patchSprite, Sprite } from "../api";

type Tool = "pencil" | "fill" | "eraser";
type RGB = [number, number, number];

function hexToRgb(hex: string): RGB {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgbToHex([r, g, b]: RGB): string {
  return "#" + [r, g, b].map(v => v.toString(16).padStart(2, "0")).join("");
}

export default function Editor() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const nav = useNavigate();
  const isNew = id === "new";
  const newState = isNew ? (location.state as any) : null;

  const [sprite, setSprite] = useState<Sprite | null>(null);
  const [pixels, setPixels] = useState<RGB[][]>([]);
  const [width, setWidth] = useState(16);
  const [height, setHeight] = useState(16);
  const [tool, setTool] = useState<Tool>("pencil");
  const [color, setColor] = useState<RGB>([255, 0, 77]);
  const [palettes, setPalettes] = useState<Record<string, RGB[]>>({});
  const [activePalette, setActivePalette] = useState<string>("pico8");
  const [zoom, setZoom] = useState(16);
  const [drawing, setDrawing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const initPixels = (w: number, h: number, fill: RGB = [0, 0, 0]): RGB[][] =>
    Array.from({ length: h }, () => Array.from({ length: w }, () => [...fill] as RGB));

  useEffect(() => {
    fetchPalettes().then(p => setPalettes(p as any));
  }, []);

  useEffect(() => {
    if (isNew && newState) {
      setWidth(newState.width);
      setHeight(newState.height);
      setPixels(initPixels(newState.width, newState.height));
      if (newState.palette) setActivePalette(newState.palette);
    } else if (id && !isNew) {
      fetchSprite(id).then(s => {
        setSprite(s);
        setWidth(s.width);
        setHeight(s.height);
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.src = `/api/sprites/${id}/file`;
        img.onload = () => {
          const tmp = document.createElement("canvas");
          tmp.width = s.width;
          tmp.height = s.height;
          const ctx = tmp.getContext("2d")!;
          ctx.drawImage(img, 0, 0, s.width, s.height);
          const d = ctx.getImageData(0, 0, s.width, s.height).data;
          const px = initPixels(s.width, s.height);
          for (let y = 0; y < s.height; y++)
            for (let x = 0; x < s.width; x++) {
              const i = (y * s.width + x) * 4;
              px[y][x] = [d[i], d[i + 1], d[i + 2]];
            }
          setPixels(px);
        };
      });
    }
  }, [id]);

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || pixels.length === 0) return;
    const ctx = canvas.getContext("2d")!;
    for (let y = 0; y < height; y++)
      for (let x = 0; x < width; x++) {
        const [r, g, b] = pixels[y][x];
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x * zoom, y * zoom, zoom, zoom);
      }
    if (zoom >= 8) {
      ctx.strokeStyle = "rgba(255,255,255,0.08)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x <= width; x++) { ctx.beginPath(); ctx.moveTo(x * zoom, 0); ctx.lineTo(x * zoom, height * zoom); ctx.stroke(); }
      for (let y = 0; y <= height; y++) { ctx.beginPath(); ctx.moveTo(0, y * zoom); ctx.lineTo(width * zoom, y * zoom); ctx.stroke(); }
    }
  }, [pixels, width, height, zoom]);

  useEffect(() => { render(); }, [render]);

  const floodFill = (px: RGB[][], x: number, y: number, newColor: RGB, oldColor: RGB): RGB[][] => {
    if (x < 0 || x >= width || y < 0 || y >= height) return px;
    const same = (a: RGB, b: RGB) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
    if (same(oldColor, newColor)) return px;
    const next = px.map(row => row.map(c => [...c] as RGB));
    const stack = [[x, y]];
    while (stack.length) {
      const [cx, cy] = stack.pop()!;
      if (cx < 0 || cx >= width || cy < 0 || cy >= height) continue;
      if (!same(next[cy][cx], oldColor)) continue;
      next[cy][cx] = [...newColor] as RGB;
      stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
    }
    return next;
  };

  const applyAt = (px: RGB[][], x: number, y: number): RGB[][] => {
    if (x < 0 || x >= width || y < 0 || y >= height) return px;
    const next = px.map(row => row.map(c => [...c] as RGB));
    if (tool === "fill") return floodFill(px, x, y, color, px[y][x]);
    next[y][x] = tool === "eraser" ? [0, 0, 0] : [...color] as RGB;
    return next;
  };

  const getCell = (e: React.MouseEvent<HTMLCanvasElement>): [number, number] => {
    const r = canvasRef.current!.getBoundingClientRect();
    return [Math.floor((e.clientX - r.left) / zoom), Math.floor((e.clientY - r.top) / zoom)];
  };

  const onMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setDrawing(true);
    const [x, y] = getCell(e);
    setPixels(prev => applyAt(prev, x, y));
  };
  const onMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing || tool === "fill") return;
    const [x, y] = getCell(e);
    setPixels(prev => applyAt(prev, x, y));
  };

  const exportBlob = (): Promise<Blob> => new Promise(resolve => {
    const tmp = document.createElement("canvas");
    tmp.width = width; tmp.height = height;
    const ctx = tmp.getContext("2d")!;
    for (let y = 0; y < height; y++)
      for (let x = 0; x < width; x++) {
        const [r, g, b] = pixels[y][x];
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, y, 1, 1);
      }
    tmp.toBlob(b => resolve(b!), "image/png");
  });

  const handleSave = async () => {
    const blob = await exportBlob();
    if (isNew && newState) {
      const fd = new FormData();
      fd.append("file", blob, "sprite.png");
      const meta = {
        name: newState.name,
        folder: newState.folder,
        width,
        height,
        palette: newState.palette,
        file_type: "png",
        tags: [],
        created_by: "manual",
        path: `${newState.folder}/${newState.name}.png`,
      };
      const r = await fetch("/api/sprites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(meta),
      });
      if (r.ok) {
        const created = await r.json();
        await uploadSpriteFile(created.id, blob);
        nav(`/edit/${created.id}`);
      }
    } else if (sprite) {
      await uploadSpriteFile(sprite.id, blob);
      alert("Saved!");
    }
  };

  const paletteColors = palettes[activePalette] ?? [];

  return (
    <div>
      <nav>
        <h1>Pixel Art Studio</h1>
        <button onClick={() => nav("/")}>← Gallery</button>
        <button className="primary" onClick={handleSave}>Save</button>
      </nav>
      <div style={{ display: "flex", height: "calc(100vh - 57px)" }}>
        <aside style={{ width: 180, borderRight: "1px solid var(--border)", padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Tool</div>
            {(["pencil", "fill", "eraser"] as Tool[]).map(t => (
              <button key={t} onClick={() => setTool(t)} style={{ width: "100%", marginBottom: 6, background: tool === t ? "var(--accent)" : undefined }}>{t}</button>
            ))}
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Color</div>
            <input type="color" value={rgbToHex(color)} onChange={e => setColor(hexToRgb(e.target.value))}
              style={{ width: "100%", height: 36, cursor: "pointer", border: "none", background: "none" }} />
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>
              Palette
              <select value={activePalette} onChange={e => setActivePalette(e.target.value)} style={{ marginLeft: 8, fontSize: 11 }}>
                {Object.keys(palettes).map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 3 }}>
              {paletteColors.map((c, i) => (
                <div key={i} title={rgbToHex(c)} onClick={() => setColor(c)}
                  style={{ width: "100%", aspectRatio: "1", background: rgbToHex(c), borderRadius: 2, cursor: "pointer", border: color === c || (color[0] === c[0] && color[1] === c[1] && color[2] === c[2]) ? "2px solid white" : "2px solid transparent" }} />
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Zoom: {zoom}×</div>
            <input type="range" min={4} max={32} value={zoom} onChange={e => setZoom(+e.target.value)} style={{ width: "100%" }} />
          </div>
        </aside>

        <main style={{ flex: 1, overflow: "auto", display: "flex", alignItems: "flex-start", justifyContent: "center", padding: 32, background: "#111" }}>
          <canvas
            ref={canvasRef}
            width={width * zoom}
            height={height * zoom}
            style={{ imageRendering: "pixelated", cursor: tool === "fill" ? "crosshair" : "default" }}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={() => setDrawing(false)}
            onMouseLeave={() => setDrawing(false)}
          />
        </main>
      </div>
    </div>
  );
}
