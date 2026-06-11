import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Download, FilePlus2, Loader2, RefreshCcw } from "lucide-react";
import { buildPreview, downloadUrl, previewUrl } from "../api";
import { Lightbox } from "./Lightbox";
import { useStore } from "../store";

export function ResultView() {
  const { run, resetRun } = useStore();
  const [count, setCount] = useState(0);
  const [bust, setBust] = useState(0);
  const [rendering, setRendering] = useState(true);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<number | null>(null);
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

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" /> 生成完成
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{run.title || run.jobId}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={resetRun}>
            <FilePlus2 className="h-4 w-4" /> 新任务
          </button>
          <a className="btn-primary" href={downloadUrl(run.jobId)}>
            <Download className="h-4 w-4" /> 下载 .pptx
          </a>
        </div>
      </header>

      {rendering && (
        <div className="card flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin text-primary" /> 正在渲染成品预览…
        </div>
      )}
      {renderError && (
        <p className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
          {renderError}(不影响下载)
          <button className="btn-ghost px-2 py-1 text-xs" onClick={() => void render()}>
            <RefreshCcw className="h-3.5 w-3.5" /> 重试预览
          </button>
        </p>
      )}

      {!rendering && !renderError && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {Array.from({ length: count }, (_, i) => (
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
              <figcaption className="mt-1 px-1 text-center text-xs text-slate-400">{i + 1}</figcaption>
            </figure>
          ))}
        </section>
      )}

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
