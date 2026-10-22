const BASE = "/api";

export interface Sprite {
  id: string;
  path: string;
  name: string;
  folder: string;
  file_type: "png" | "gif";
  width: number;
  height: number;
  palette: string | null;
  frame_count: number;
  tags: string[];
  created_by: "agent" | "manual";
  created_at: string;
  updated_at: string;
}

export async function fetchSprites(params: Record<string, string> = {}): Promise<Sprite[]> {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`${BASE}/sprites${qs ? "?" + qs : ""}`);
  return r.json();
}

export async function fetchSprite(id: string): Promise<Sprite> {
  const r = await fetch(`${BASE}/sprites/${id}`);
  return r.json();
}

export function spriteFileUrl(id: string): string {
  return `${BASE}/sprites/${id}/file`;
}

export async function patchSprite(id: string, body: Partial<Sprite>): Promise<Sprite> {
  const r = await fetch(`${BASE}/sprites/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}

export async function uploadSpriteFile(id: string, blob: Blob): Promise<void> {
  const fd = new FormData();
  fd.append("file", blob);
  await fetch(`${BASE}/sprites/${id}/file`, { method: "PUT", body: fd });
}

export async function deleteSprite(id: string): Promise<void> {
  await fetch(`${BASE}/sprites/${id}`, { method: "DELETE" });
}

export async function fetchFolders(): Promise<string[]> {
  const r = await fetch(`${BASE}/folders`);
  return r.json();
}

export async function fetchPalettes(): Promise<Record<string, [number, number, number][]>> {
  const r = await fetch(`${BASE}/palettes`);
  return r.json();
}
