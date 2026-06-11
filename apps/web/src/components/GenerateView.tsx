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
import { listJobs, listTemplates, uploadJob, uploadTemplate, type CustomTemplate } from "../api";
import { followJob } from "../follow";
import { useStore, type Stage } from "../store";
import { useEffect } from "react";

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
  const { run, patchRun, appendLog, setHistory } = useStore();
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [styleName, setStyleName] = useState("academic");
  const [templates, setTemplates] = useState<CustomTemplate[]>([]);
  const tplInputRef = useRef<HTMLInputElement>(null);
  const [parser, setParser] = useState("auto");
  const [detail, setDetail] = useState("auto");

  useEffect(() => {
    listTemplates().then(setTemplates);
  }, []);

  async function importTemplate(list: FileList | null) {
    if (!list || list.length === 0) return;
    try {
      const t = await uploadTemplate(list[0]);
      setTemplates((prev) => [...prev.filter((x) => x.style_name !== t.style_name), t]);
      setStyleName(t.style_name);
    } catch (e) {
      patchRun({ error: String(e) });
    }
  }
  const inputRef = useRef<HTMLInputElement>(null);

  const stageIdx = STAGES.findIndex((s) => s.key === run.stage);

  function addFiles(list: FileList | null) {
    if (!list) return;
    setFiles((prev) => [...prev, ...Array.from(list)]);
  }

  async function start() {
    patchRun({ busy: true, error: null, log: [], stage: "parse", done: 0, total: 0 });
    try {
      const res = await uploadJob(files, { styleName, parser, detail });
      patchRun({ jobId: res.job_id, title: res.title, ingested: res.ingested, warnings: res.warnings, stage: "outline" });
      appendLog(`已摄取 ${res.ingested.files} 个文件 · ${res.ingested.text_pages} 页正文 · ${res.ingested.tables} 表 · ${res.ingested.figures} 图`);
      listJobs().then(setHistory);
      followJob(res.job_id);
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
            <div className="flex gap-2">
              <select className="field" value={styleName} onChange={(e) => setStyleName(e.target.value)}>
                <option value="academic">Academic(黑体 + Times,红色强调)</option>
                <option value="modern_teal">Modern Teal(雅黑 + Calibri,青色)</option>
                {templates.map((t) => (
                  <option key={t.style_name} value={t.style_name}>
                    模板:{t.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn-ghost shrink-0 px-3 text-xs"
                title="导入 .pptx 模板(提取主题字体/配色并继承母版)"
                onClick={() => tplInputRef.current?.click()}
              >
                导入模板
              </button>
              <input
                ref={tplInputRef}
                type="file"
                accept=".pptx"
                className="hidden"
                onChange={(e) => importTemplate(e.target.files)}
              />
            </div>
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
              <option value="auto">自动(模型按论文内容自定页数,推荐)</option>
              <option value="brief">简洁(约 5-7 内容页)</option>
              <option value="normal">标准(约 8-11 内容页)</option>
              <option value="high">详尽(约 12-15 内容页)</option>
            </select>
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-400">
          子图拆分、视觉质检、精品构图、原生公式均已默认启用,遇到问题会自动回退,无需配置。
        </p>
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
