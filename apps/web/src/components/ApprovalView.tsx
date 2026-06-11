import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, RefreshCcw, RotateCcw, ShieldCheck } from "lucide-react";
import { approveJob, buildPreview, listJobs, previewUrl, streamJob } from "../api";
import { useStore } from "../store";
import { Lightbox } from "./Lightbox";

export function ApprovalView() {
  const { run, patchRun, appendLog, setView, setHistory } = useStore();
  const [count, setCount] = useState(0);
  const [bust, setBust] = useState(0);
  const [rendering, setRendering] = useState(true);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const [approving, setApproving] = useState(false);
  const renderBusy = useRef(false); // dedupe React StrictMode double-mounted effects

  async function render() {
    if (renderBusy.current) return;
    renderBusy.current = true;
    setRendering(true);
    setRenderError(null);
    try {
      const n = await buildPreview(run.jobId);
      setCount(n);
      setBust(Date.now());
    } catch (e) {
      setRenderError(String((e as Error).message ?? e));
    } finally {
      renderBusy.current = false;
      setRendering(false);
    }
  }

  useEffect(() => {
    void render();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run.jobId]);

  async function approve() {
    setApproving(true);
    try {
      const out = await approveJob(run.jobId);
      patchRun({ outputPath: out, stage: "done" });
      listJobs().then(setHistory);
      setView("result");
    } catch (e) {
      patchRun({ error: String(e) });
    } finally {
      setApproving(false);
    }
  }

  function reject() {
    if (!feedback.trim()) return;
    setRejecting(true);
    patchRun({ stage: "outline", busy: true });
    appendLog(`退回重做: ${feedback}`);
    streamJob(
      run.jobId,
      {
        onUpdate: (node, phase) => appendLog(`节点 ${node}${phase ? ` · ${phase}` : ""}`),
        onProgress: (p) => {
          if (p.phase === "slide") patchRun({ stage: "generate", done: p.done ?? 0, total: p.total ?? 0 });
          appendLog(p.total ? `${p.phase} ${p.done ?? ""}/${p.total}` : p.phase);
        },
        onAwaitingApproval: (outline) => {
          patchRun({ outline, stage: "review", busy: false });
          setRejecting(false);
          setFeedback("");
          void render(); // fresh thumbnails for the revised deck
        },
        onDone: (out) => {
          patchRun({ outputPath: out, busy: false });
          setRejecting(false);
          setView("result");
        },
        onError: (msg) => {
          patchRun({ error: msg, busy: false });
          setRejecting(false);
        },
      },
      { feedback },
    );
  }

  if (rejecting) {
    return (
      <div className="card flex flex-col items-center gap-3 py-16 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm font-medium">已退回,正在按你的意见重新规划…</p>
        <p className="text-xs text-slate-400">
          {run.stage === "generate" && run.total > 0 ? `逐页生成 ${run.done}/${run.total}` : "规划骨架中"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold">
            <ShieldCheck className="h-5 w-5 text-amber-500" /> 审阅大纲(Hard-Stop)
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            以下是真实渲染预览。模型可能有语义错误——确认无误后批准编译,或写明问题退回重做。
          </p>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
          {run.outline.length} 页待审
        </span>
      </header>

      {rendering && (
        <div className="card flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin text-primary" /> 正在渲染逐页预览…
        </div>
      )}

      {renderError && (
        <div className="card border-amber-300 dark:border-amber-700">
          <p className="flex items-center gap-1.5 text-sm text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-4 w-4" /> {renderError} —— 以下退化为文字大纲审批。
            <button className="btn-ghost ml-2 px-2 py-1 text-xs" onClick={() => void render()}>
              <RefreshCcw className="h-3.5 w-3.5" /> 重试预览
            </button>
          </p>
          <ol className="mt-3 space-y-1.5">
            {run.outline.map((s, i) => (
              <li key={s.slide_id} className="flex items-center gap-2 text-sm">
                <span className="w-6 text-right text-xs text-slate-400">{i + 1}.</span>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500 dark:bg-slate-800">
                  {s.layout_type}
                </span>
                {s.title}
              </li>
            ))}
          </ol>
        </div>
      )}

      {!rendering && !renderError && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {Array.from({ length: count }, (_, i) => {
            const o = run.outline[i];
            return (
              <figure
                key={i}
                className="card cursor-zoom-in p-2 transition-shadow hover:shadow-md"
                onClick={() => setLightbox(i + 1)}
              >
                <img
                  src={previewUrl(run.jobId, i + 1, bust)}
                  alt={`slide ${i + 1}`}
                  className="aspect-video w-full rounded border border-slate-100 object-contain dark:border-slate-800"
                  loading="lazy"
                />
                <figcaption className="mt-1.5 flex items-center gap-1.5 px-1 text-xs">
                  <span className="font-bold text-slate-400">{i + 1}</span>
                  {o && (
                    <>
                      <span className="rounded bg-slate-100 px-1 py-0.5 text-[10px] text-slate-500 dark:bg-slate-800">
                        {o.layout_type}
                      </span>
                      <span className="truncate" title={o.title}>
                        {o.title}
                      </span>
                    </>
                  )}
                </figcaption>
              </figure>
            );
          })}
        </section>
      )}

      {/* decision bar */}
      <section className="card sticky bottom-4 border-primary/30 shadow-lg">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="field-label">退回意见(退回时必填)</label>
            <textarea
              className="field min-h-[60px]"
              placeholder="例:第 3 页与第 4 页重复,合并;结果页缺少与传统方法的对比……"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
          <div className="flex shrink-0 gap-2">
            <button className="btn-ghost" disabled={!feedback.trim() || approving} onClick={reject}>
              <RotateCcw className="h-4 w-4" /> 退回重做
            </button>
            <button className="btn-primary" disabled={approving} onClick={approve}>
              {approving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              批准并编译
            </button>
          </div>
        </div>
      </section>

      {/* lightbox */}
      {lightbox !== null && (
        <Lightbox
          jobId={run.jobId}
          index={lightbox}
          count={count}
          bust={bust}
          onNavigate={setLightbox}
          onClose={() => setLightbox(null)}
        />
      )}
    </div>
  );
}
