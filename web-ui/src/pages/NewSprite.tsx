import { useState } from "react";
import { useNavigate } from "react-router-dom";

const SIZES = [8, 16, 32, 64];
const PALETTES = ["none", "pico8", "gameboy", "cga", "db16"];

export default function NewSprite() {
  const nav = useNavigate();
  const [name, setName] = useState("untitled");
  const [folder, setFolder] = useState("sprites");
  const [width, setWidth] = useState(16);
  const [height, setHeight] = useState(16);
  const [palette, setPalette] = useState("pico8");

  const handleCreate = () => {
    nav("/edit/new", { state: { name, folder, width, height, palette: palette === "none" ? null : palette } });
  };

  return (
    <div>
      <nav>
        <h1>Pixel Art Studio</h1>
        <button onClick={() => nav("/")}>← Gallery</button>
      </nav>
      <div style={{ maxWidth: 400, margin: "60px auto", background: "var(--surface)", borderRadius: 10, padding: 32, border: "1px solid var(--border)" }}>
        <h2 style={{ marginBottom: 24 }}>New Sprite</h2>
        <label style={{ display: "block", marginBottom: 16 }}>
          <div style={{ marginBottom: 6, fontSize: 13 }}>Name</div>
          <input value={name} onChange={e => setName(e.target.value)} style={{ width: "100%" }} />
        </label>
        <label style={{ display: "block", marginBottom: 16 }}>
          <div style={{ marginBottom: 6, fontSize: 13 }}>Folder</div>
          <input value={folder} onChange={e => setFolder(e.target.value)} style={{ width: "100%" }} placeholder="sprites/hero" />
        </label>
        <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
          <label style={{ flex: 1 }}>
            <div style={{ marginBottom: 6, fontSize: 13 }}>Width</div>
            <select value={width} onChange={e => setWidth(+e.target.value)} style={{ width: "100%" }}>
              {SIZES.map(s => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label style={{ flex: 1 }}>
            <div style={{ marginBottom: 6, fontSize: 13 }}>Height</div>
            <select value={height} onChange={e => setHeight(+e.target.value)} style={{ width: "100%" }}>
              {SIZES.map(s => <option key={s}>{s}</option>)}
            </select>
          </label>
        </div>
        <label style={{ display: "block", marginBottom: 24 }}>
          <div style={{ marginBottom: 6, fontSize: 13 }}>Palette</div>
          <select value={palette} onChange={e => setPalette(e.target.value)} style={{ width: "100%" }}>
            {PALETTES.map(p => <option key={p}>{p}</option>)}
          </select>
        </label>
        <button className="primary" style={{ width: "100%" }} onClick={handleCreate}>Create &amp; Edit</button>
      </div>
    </div>
  );
}
