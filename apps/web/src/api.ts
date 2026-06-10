/** API client for the Academic-Slides-Agent backend. */

export const API_BASE = (import.meta.env.VITE_API_BASE as string) || "http://127.0.0.1:8000";

export interface Ingested {
  files: number;
  tables: number;
  figures: number;
  text_pages: number;
}

export interface OutlineItem {
  slide_id: string;
  layout_type: string;
  title: string;
}

export interface Progress {
  phase: string;
  done?: number;
  total?: number;
}

export interface JobMeta {
  job_id: string;
  title: string;
  created_at: string;
  style: string;
  status: "created" | "awaiting_approval" | "done" | "expired";
}

export interface GenOptions {
  styleName: string;
  parser: string;
  splitFigures: boolean;
  vlmCritic: boolean;
  nativeFormula: boolean;
}

export async function uploadJob(files: File[], opts: GenOptions) {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  form.append("style_name", opts.styleName);
  form.append("parser", opts.parser);
  form.append("split_figures", String(opts.splitFigures));
  form.append("vlm_critic", String(opts.vlmCritic));
  form.append("native_formula", String(opts.nativeFormula));
  const res = await fetch(`${API_BASE}/jobs/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`上传失败: ${res.status}`);
  return (await res.json()) as {
    job_id: string;
    title: string;
    ingested: Ingested;
    warnings: string[];
  };
}

export function streamJob(
  jobId: string,
  handlers: {
    onUpdate: (node: string, phase?: string) => void;
    onProgress: (p: Progress) => void;
    onAwaitingApproval: (outline: OutlineItem[]) => void;
    onDone: (outputPath: string | null) => void;
    onError: (msg: string) => void;
  },
  reject?: { feedback: string },
): () => void {
  const url = reject
    ? `${API_BASE}/jobs/${jobId}/stream?reject=1&feedback=${encodeURIComponent(reject.feedback)}`
    : `${API_BASE}/jobs/${jobId}/stream`;
  const es = new EventSource(url);
  es.addEventListener("update", (e) => {
    const data = JSON.parse((e as MessageEvent).data) as Record<string, { phase?: string }>;
    for (const [node, v] of Object.entries(data)) handlers.onUpdate(node, v.phase);
  });
  es.addEventListener("progress", (e) => {
    handlers.onProgress(JSON.parse((e as MessageEvent).data) as Progress);
  });
  es.addEventListener("awaiting_approval", (e) => {
    const data = JSON.parse((e as MessageEvent).data) as { outline: OutlineItem[] };
    es.close();
    handlers.onAwaitingApproval(data.outline ?? []);
  });
  es.addEventListener("done", (e) => {
    const data = JSON.parse((e as MessageEvent).data) as { output_path: string | null };
    es.close();
    handlers.onDone(data.output_path);
  });
  es.onerror = () => {
    es.close();
    handlers.onError("连接中断");
  };
  return () => es.close();
}

export async function buildPreview(jobId: string): Promise<number> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/preview`, { method: "POST" });
  if (!res.ok)
    throw new Error(
      res.status === 503 ? "本机无可用渲染器(需 PowerPoint 或 LibreOffice)" : `预览失败: ${res.status}`,
    );
  return ((await res.json()) as { count: number }).count;
}

export function previewUrl(jobId: string, idx: number, bust?: number): string {
  return `${API_BASE}/jobs/${jobId}/preview/${idx}${bust ? `?t=${bust}` : ""}`;
}

export async function approveJob(jobId: string): Promise<string | null> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: true }),
  });
  if (!res.ok) throw new Error(`批准失败: ${res.status}`);
  return ((await res.json()) as { output_path: string | null }).output_path;
}

export async function listJobs(): Promise<JobMeta[]> {
  try {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) return [];
    return ((await res.json()) as { jobs: JobMeta[] }).jobs;
  } catch {
    return [];
  }
}

export async function deleteJob(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
}

export function downloadUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/download`;
}
