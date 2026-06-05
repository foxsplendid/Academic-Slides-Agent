export const API_BASE = (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";

export interface OutlineItem {
  slide_id: string;
  layout_type: string;
  title: string;
}

export interface Ingested {
  files: number;
  tables: number;
  figures: number;
  text_pages: number;
}

export async function uploadJob(files: File[]): Promise<{ jobId: string; ingested: Ingested }> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${API_BASE}/jobs/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`upload failed: ${res.status}`);
  const data = await res.json();
  return { jobId: data.job_id as string, ingested: data.ingested as Ingested };
}

export interface Progress {
  phase: string;
  done?: number;
  total?: number;
}

export function streamJob(
  jobId: string,
  onUpdate: (node: string, phase: string) => void,
  onAwaitingApproval: (outline: OutlineItem[]) => void,
  onError: (message: string) => void,
  onProgress?: (p: Progress) => void,
): () => void {
  const es = new EventSource(`${API_BASE}/jobs/${jobId}/stream`);
  es.addEventListener("progress", (ev) => {
    onProgress?.(JSON.parse((ev as MessageEvent).data) as Progress);
  });
  es.addEventListener("update", (ev) => {
    const data = JSON.parse((ev as MessageEvent).data) as Record<string, { phase?: string }>;
    for (const node of Object.keys(data)) onUpdate(node, data[node]?.phase ?? "");
  });
  es.addEventListener("awaiting_approval", (ev) => {
    const data = JSON.parse((ev as MessageEvent).data) as { outline?: OutlineItem[] };
    onAwaitingApproval(data.outline ?? []);
    es.close();
  });
  es.onerror = () => {
    onError("stream error");
    es.close();
  };
  return () => es.close();
}

export async function approveJob(jobId: string, edits?: unknown): Promise<string | null> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: true, edits: edits ?? null }),
  });
  if (!res.ok) throw new Error(`approve failed: ${res.status}`);
  return ((await res.json()).output_path as string) ?? null;
}

export function downloadUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/download`;
}
