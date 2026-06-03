import { useState } from "react";
import { approveJob, downloadUrl, streamJob, uploadJob } from "./api";
import type { OutlineItem } from "./api";

type Phase = "idle" | "uploading" | "streaming" | "review" | "compiling" | "done" | "error";

export function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const busy = phase === "uploading" || phase === "streaming" || phase === "compiling";

  async function start() {
    setError(null);
    setLog([]);
    setOutline([]);
    setPhase("uploading");
    try {
      const id = await uploadJob(files);
      setJobId(id);
      setPhase("streaming");
      streamJob(
        id,
        (node, ph) => setLog((l) => [...l, ph ? `${node} · ${ph}` : node]),
        (ol) => {
          setOutline(ol);
          setPhase("review");
        },
        (msg) => {
          setError(msg);
          setPhase("error");
        },
      );
    } catch (e) {
      setError(String(e));
      setPhase("error");
    }
  }

  async function approve() {
    if (!jobId) return;
    setPhase("compiling");
    try {
      await approveJob(jobId);
      setPhase("done");
    } catch (e) {
      setError(String(e));
      setPhase("error");
    }
  }

  return (
    <main className="app">
      <h1>Academic-Slides-Agent</h1>
      <p className="sub">Paper + data &rarr; rigorous, native-editable .pptx</p>

      <section className="card">
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
        />
        <button disabled={busy} onClick={start}>
          Generate outline
        </button>
      </section>

      {log.length > 0 && (
        <section className="card">
          <h2>Progress</h2>
          <ul className="log">
            {log.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}

      {phase === "review" && (
        <section className="card">
          <h2>Review outline (Hard-Stop)</h2>
          <ol className="outline">
            {outline.map((s) => (
              <li key={s.slide_id}>
                <span className="lt">{s.layout_type}</span> {s.title}
              </li>
            ))}
          </ol>
          <button onClick={approve}>Approve &amp; compile</button>
        </section>
      )}

      {phase === "done" && jobId && (
        <section className="card">
          <h2>Done</h2>
          <a className="download" href={downloadUrl(jobId)}>
            Download .pptx
          </a>
        </section>
      )}

      {error && <p className="error">&#9888; {error}</p>}
    </main>
  );
}
