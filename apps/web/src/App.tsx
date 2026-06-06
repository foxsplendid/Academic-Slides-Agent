import { useState } from "react";
import { approveJob, downloadUrl, streamJob, uploadJob } from "./api";
import type { Ingested, OutlineItem, Progress } from "./api";

type Phase = "idle" | "uploading" | "streaming" | "review" | "compiling" | "done" | "error";
type Stage = "parse" | "outline" | "generate" | "critic";

const STEPS = ["解析 PDF", "规划大纲", "生成幻灯片", "质量检查", "审阅大纲", "编译导出", "完成"];
const STEP_OF: Record<Stage, number> = { parse: 0, outline: 1, generate: 2, critic: 3 };

export function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [stage, setStage] = useState<Stage>("parse");
  const [prog, setProg] = useState<Progress | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [ingested, setIngested] = useState<Ingested | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const busy = phase === "uploading" || phase === "streaming" || phase === "compiling";

  let active = -1;
  if (phase === "uploading") active = 0;
  else if (phase === "streaming") active = STEP_OF[stage];
  else if (phase === "review") active = 4;
  else if (phase === "compiling") active = 5;
  else if (phase === "done") active = 6;

  async function start() {
    setError(null);
    setLog([]);
    setOutline([]);
    setProg(null);
    setIngested(null);
    setWarnings([]);
    setStage("parse");
    setPhase("uploading");
    try {
      const { jobId: id, ingested: ing, warnings: warn } = await uploadJob(files);
      setJobId(id);
      setIngested(ing);
      setWarnings(warn);
      setStage("outline");
      setPhase("streaming");
      streamJob(
        id,
        (node, ph) => {
          if (node === "critic") setStage("critic");
          else if (node === "plan") setStage((s) => (s === "critic" ? s : "outline"));
          setLog((l) => [...l, ph ? `${node} · ${ph}` : node]);
        },
        (ol) => {
          setOutline(ol);
          setPhase("review");
        },
        (msg) => {
          setError(msg);
          setPhase("error");
        },
        (p) => {
          setProg(p);
          if (p.phase === "slide") setStage("generate");
          else if (p.phase.startsWith("skeleton")) setStage("outline");
          setLog((l) => [...l, p.total ? `${p.phase} ${p.done ?? ""}/${p.total}` : p.phase]);
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
      <p className="sub">论文 + 数据 &rarr; 严谨、原生可编辑的 .pptx</p>

      <section className="card">
        <h2>主论文 PDF + 补充材料(Excel / CSV / zip / 图)</h2>
        <p className="sub">可一次选多个文件:主论文 PDF,加上补充数据表、图、压缩包。</p>
        <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
        <button disabled={busy || files.length === 0} onClick={start}>
          {busy ? "生成中…" : "生成幻灯片"}
        </button>
        {ingested && (
          <p className="hint">
            已摄取:{ingested.files} 个文件 · {ingested.text_pages} 页正文 · {ingested.tables} 张数据表 ·{" "}
            {ingested.figures} 张图
          </p>
        )}
        {warnings.map((w, i) => (
          <p className="warn" key={i}>
            &#9888; {w}
          </p>
        ))}
      </section>

      {active >= 0 && (
        <section className="card">
          <ol className="stepper">
            {STEPS.map((label, i) => {
              const state = i < active ? "done" : i === active ? "active" : "todo";
              const counter =
                i === 2 && i === active && prog?.phase === "slide" && prog.total
                  ? ` ${prog.done}/${prog.total}`
                  : "";
              return (
                <li key={label} className={`step ${state}`}>
                  <span className="dot">{i < active ? "✓" : i + 1}</span>
                  <span className="label">
                    {label}
                    {counter}
                  </span>
                </li>
              );
            })}
          </ol>
          {busy && (
            <p className="hint">
              {active === 0 && "正在用 MinerU 解析论文(文本 / 公式 / 表格 / 配图)…"}
              {active === 1 && "正在规划大纲骨架…"}
              {active === 2 && `正在逐页并行生成内容${prog?.total ? `(${prog.done}/${prog.total})` : ""}…`}
              {active === 3 && "正在做确定性质量检查(溢出 / 空页 / 悬空引用)…"}
              {active === 5 && "正在编译为原生 .pptx…"}
            </p>
          )}
        </section>
      )}

      {phase === "review" && (
        <section className="card">
          <h2>审阅大纲（Hard-Stop · 人工确认）</h2>
          <p className="sub">确认无误后批准；模型可能有语义错误，这一步可拦下。</p>
          <ol className="outline">
            {outline.map((s) => (
              <li key={s.slide_id}>
                <span className="lt">{s.layout_type}</span> {s.title}
              </li>
            ))}
          </ol>
          <button onClick={approve}>批准并编译</button>
        </section>
      )}

      {phase === "done" && jobId && (
        <section className="card">
          <h2>完成 ✅</h2>
          <a className="download" href={downloadUrl(jobId)}>
            下载 .pptx
          </a>
        </section>
      )}

      {log.length > 0 && (
        <details className="card details">
          <summary>详细日志（{log.length}）</summary>
          <ul className="log">
            {log.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </details>
      )}

      {error && <p className="error">&#9888; {error}</p>}
    </main>
  );
}
