import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSprites, fetchFolders, deleteSprite, spriteFileUrl, Sprite } from "../api";

export default function Gallery() {
  const [sprites, setSprites] = useState<Sprite[]>([]);
  const [folders, setFolders] = useState<string[]>([]);
  const [folder, setFolder] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  const [fileType, setFileType] = useState("");

  const load = () => {
    const params: Record<string, string> = {};
    if (folder) params.folder = folder;
    if (createdBy) params.created_by = createdBy;
    if (fileType) params.file_type = fileType;
    fetchSprites(params).then(setSprites);
  };

  useEffect(() => {
    fetchFolders().then(setFolders);
  }, []);

  useEffect(() => { load(); }, [folder, createdBy, fileType]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this sprite?")) return;
    await deleteSprite(id);
    load();
  };

  return (
    <div>
      <nav>
        <h1>Pixel Art Studio</h1>
        <Link to="/new"><button className="primary">+ New Sprite</button></Link>
      </nav>
      <div style={{ display: "flex", minHeight: "calc(100vh - 57px)" }}>
        {/* sidebar */}
        <aside style={{ width: 200, borderRight: "1px solid var(--border)", padding: 16 }}>
          <div style={{ marginBottom: 12, fontWeight: 600 }}>Folders</div>
          <div
            style={{ cursor: "pointer", padding: "4px 0", color: folder === "" ? "var(--accent)" : "var(--text)" }}
            onClick={() => setFolder("")}
          >All</div>
          {folders.map(f => (
            <div
              key={f}
              style={{ cursor: "pointer", padding: "4px 0", color: folder === f ? "var(--accent)" : "var(--text)" }}
              onClick={() => setFolder(f)}
            >{f}</div>
          ))}
        </aside>

        {/* main */}
        <main style={{ flex: 1, padding: 24 }}>
          {/* filters */}
          <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
            <select value={createdBy} onChange={e => setCreatedBy(e.target.value)}>
              <option value="">All creators</option>
              <option value="agent">Agent</option>
              <option value="manual">Manual</option>
            </select>
            <select value={fileType} onChange={e => setFileType(e.target.value)}>
              <option value="">All types</option>
              <option value="png">PNG</option>
              <option value="gif">GIF</option>
            </select>
          </div>

          {/* grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 16 }}>
            {sprites.map(s => (
              <div key={s.id} style={{ background: "var(--surface)", borderRadius: 8, overflow: "hidden", border: "1px solid var(--border)" }}>
                <div style={{ background: "#222", display: "flex", justifyContent: "center", padding: 8, minHeight: 120 }}>
                  <img
                    src={spriteFileUrl(s.id)}
                    alt={s.name}
                    style={{ imageRendering: "pixelated", maxHeight: 112, maxWidth: "100%", objectFit: "contain" }}
                  />
                </div>
                <div style={{ padding: 8 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>
                    {s.width}×{s.height} · {s.file_type.toUpperCase()} · {s.created_by}
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Link to={`/edit/${s.id}`}><button style={{ fontSize: 12, padding: "3px 8px" }}>Edit</button></Link>
                    <button style={{ fontSize: 12, padding: "3px 8px", color: "var(--accent)" }} onClick={() => handleDelete(s.id)}>Del</button>
                  </div>
                </div>
              </div>
            ))}
            {sprites.length === 0 && (
              <div style={{ color: "var(--muted)", gridColumn: "1/-1", textAlign: "center", marginTop: 60 }}>
                No sprites yet. Ask an agent to draw one, or create one manually.
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
