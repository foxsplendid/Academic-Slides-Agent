import { useRef, useState } from "react";
import {
  AlertTriangle,
  FileText,
  Images,
  ListChecks,
  Loader2,
  Play,
  ScanSearch,
  Sparkles,
  Table2,
  UploadCloud,
} from "lucide-react";
import { listJobs, streamJob, uploadJob } from "../api";
import { useStore, type Stage } from "../store";

const STAGES: { key: Stage; label: string }[] = [
  { key: "parse", label: "解析论文" },
  { key: "outline", label: "规划骨架" },
  { key: "generate", label: "逐页生成" },
  { key: "critic", label: "质量检查" },
  { key: "review", label: "人工审批" },
  { key: "compile", label: "编译导出" },
  { key: "done", label: "完成" },
];

export function GenerateView() {
  const { run, patchRun, appendLog, setView, setHistory } = useStore();
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [styleName, setStyleName] = useState("academic");
  const [parser, setParser] = useState("auto");
  const [detail, setDetail] = useState("normal");
  const [splitFigures, setSplitFigures] = useState(false);
  const [vlmCritic, setVlmCritic] = useState(false);
  const [nativeFormula, setNativeFormula] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const stageIdx = STAGES.findIndex((s) => s.key === run.stage);

  function addFiles(list: FileList | null) {
    if (!list) return;
    setFiles((prev) => [...prev, ...Array.from(list)]);
  }

  async function start() {
    patchRun({ busy: true, error: null, log: [], stage: "parse", done: 0, total: 0 });
    try {
      const res = await uploadJob(files, { styleName, parser, detail, splitFigures, vlmCritic, nativeFormula });
      patchRun({ jobId: res.job_id, title: res.title, ingested: res.ingested, warnings: res.warnings, stage: "outline" });
      appendLog(`已摄取 ${res.ingested.files} 个文件 · ${res.ingested.text_pages} 页正文 · ${res.ingested.tables} 表 · ${res.ingested.figures} 图`);
      listJobs().then(setHistory);
      streamJob(res.job_id, {
        onUpdate: (node, phase) => appendLog(`节点 ${node}${phase ? ` · ${phase}` : ""}`),
        onProgress: (p) => {
          if (p.phase === "slide") patchRun({ stage: "generate", done: p.done ?? 0, total: p.total ?? 0 });
          else if (p.phase.startsWith("skeleton")) patchRun({ stage: "outline", total: p.total ?? 0 });
          else if (p.phase === "repair") patchRun({ stage: "critic" });
          appendLog(p.total ? `${p.phase} ${p.done ?? ""}/${p.total}` : p.phase);
        },
        onAwaitingApproval: (outline) => {
          patchRun({ outline, stage: "review", busy: false });
          setView("approval");
        },
        onDone: (outputPath) => {
          patchRun({ outputPath, stage: "done", busy: false });
          setView("result");
        },
        onError: (msg) => patchRun({ error: msg, busy: false }),
      });
    } catch (e) {
      patchRun({ error: String(e), busy: false });
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-xl font-bold">生成学术幻灯片</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          上传论文 PDF 与补充材料,经解析 → 规划 → 质检 → 人工审批 → 编译为原生可编辑 .pptx
        </p>
      </header>

      {/* upload zone */}
      <section className="card">
        <div
          className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragging ? "border-primary bg-primary/5" : "border-slate-300 dark:border-slate-700"
          }`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles(e.dataTransfer.files);
          }}
        >
          <UploadCloud className="mb-2 h-8 w-8 text-primary" />
          <p className="text-sm font-medium">拖拽或点击选择文件</p>
          <p className="mt-1 text-xs text-slate-400">主论文 PDF + 补充数据(Excel / CSV / zip / 图片),可多选</p>
          <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
        </div>
        {files.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-2">
            {files.map((f, i) => (
              <li key={i} className="flex items-center gap-1 rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                {f.name}
                <button className="ml-1 text-slate-400 hover:text-red-500" onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* config panel */}
      <section className="card">
        <h2 className="mb-3 flex items-center gap-1.5 text-sm font-bold">
          <Sparkles className="h-4 w-4 text-primary" /> 生成配置
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="field-label">设计风格</label>
            <select className="field" value={styleName} onChange={(e) => setStyleName(e.target.value)}>
              <option value="academic">Academic(黑体 + Times,红色强调)</option>
              <option value="modern_teal">Modern Teal(雅黑 + Calibri,青色)</option>
            </select>
          </div>
          <div>
            <label className="field-label">PDF 解析器</label>
            <select className="field" value={parser} onChange={(e) => setParser(e.target.value)}>
              <option value="auto">自动(MinerU → 兜底级联)</option>
              <option value="mineru">MinerU 云解析(高保真)</option>
              <option value="pdfplumber">pdfplumber(本地,无需网络)</option>
            </select>
          </div>
          <div>
            <label className="field-label">详细程度</label>
            <select className="field" value={detail} onChange={(e) => setDetail(e.target.value)}>
              <option value="brief">简洁(6-8 页,要点精简)</option>
              <option value="normal">标准(8-12 页)</option>
              <option value="high">详尽(12-16 页,深入展开)</option>
            </select>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
          {[
            { label: "大图二次切割", desc: "复合图拆为子面板", val: splitFigures, set: setSplitFigures },
            { label: "VLM 视觉评审", desc: "渲染后视觉缺陷检查", val: vlmCritic, set: setVlmCritic },
            { label: "原生公式(实验)", desc: "简单公式可编辑 OMML", val: nativeFormula, set: setNativeFormula },
          ].map((t) => (
            <label
              key={t.label}
              className={`flex cursor-pointer items-start gap-2 rounded-lg border p-3 text-xs transition-colors ${
                t.val ? "border-primary/50 bg-primary/5" : "border-slate-200 dark:border-slate-700"
              }`}
            >
              <input type="checkbox" className="mt-0.5" checked={t.val} onChange={(e) => t.set(e.target.checked)} />
              <span>
                <span className="block font-semibold">{t.label}</span>
                <span className="text-slate-400">{t.desc}</span>
              </span>
            </label>
          ))}
        </div>
        <div className="mt-4">
          <button className="btn-primary" disabled={run.busy || files.length === 0} onClick={start}>
            {run.busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {run.busy ? "生成中…" : "开始生成"}
          </button>
        </div>
      </section>

      {/* ingest stats */}
      {run.ingested && (
        <section className="card">
          <div className="grid grid-cols-4 gap-3 text-center">
            {[
              { icon: FileText, label: "文件", value: run.ingested.files },
              { icon: ScanSearch, label: "正文页", value: run.ingested.text_pages },
              { icon: Table2, label: "数据表", value: run.ingested.tables },
              { icon: Images, label: "图", value: run.ingested.figures },
            ].map((s) => (
              <div key={s.label}>
                <s.icon className="mx-auto mb-1 h-4 w-4 text-primary" />
                <div className="text-lg font-bold">{s.value}</div>
                <div className="text-xs text-slate-400">{s.label}</div>
              </div>
            ))}
          </div>
          {run.warnings.map((w, i) => (
            <p key={i} className="mt-2 flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5" /> {w}
            </p>
          ))}
        </section>
      )}

      {/* progress stages */}
      {(run.busy || run.stage !== "parse") && (
        <section className="card">
          <ol className="flex items-center justify-between">
            {STAGES.map((s, i) => {
              const state = i < stageIdx ? "done" : i === stageIdx ? "active" : "todo";
              return (
                <li key={s.key} className="flex flex-1 flex-col items-center gap-1">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      state === "done"
                        ? "bg-emerald-500 text-white"
                        : state === "active"
                          ? "bg-primary text-white"
                          : "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
                    }`}
                  >
                    {state === "done" ? "✓" : i + 1}
                  </span>
                  <span className={`text-[11px] ${state === "active" ? "font-bold text-primary" : "text-slate-400"}`}>
                    {s.label}
                    {s.key === "generate" && state === "active" && run.total > 0 && ` ${run.done}/${run.total}`}
                  </span>
                </li>
              );
            })}
          </ol>
          {run.log.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-slate-400">
                <ListChecks className="mr-1 inline h-3.5 w-3.5" />
                详细日志({run.log.length})
              </summary>
              <pre className="mt-2 max-h-48 overflow-y-auto rounded bg-slate-50 p-2 text-[11px] leading-relaxed text-slate-500 dark:bg-slate-950 dark:text-slate-400">
                {run.log.join("\n")}
              </pre>
            </details>
          )}
        </section>
      )}

      {run.error && (
        <p className="flex items-center gap-1 text-sm text-red-500">
          <AlertTriangle className="h-4 w-4" /> {run.error}
        </p>
      )}
    </div>
  );
}
