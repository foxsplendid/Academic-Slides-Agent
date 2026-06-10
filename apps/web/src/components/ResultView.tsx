import { useEffect, useState } from "react";
import { CheckCircle2, Download, FilePlus2, Loader2, X } from "lucide-react";
import { buildPreview, downloadUrl, previewUrl } from "../api";
import { useStore } from "../store";

export function ResultView() {
  const { run, resetRun } = useStore();
  const [count, setCount] = useState(0);
  const [bust, setBust] = useState(0);
  const [rendering, setRendering] = useState(true);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    setRendering(true);
    setRenderError(null);
    buildPreview(run.jobId)
      .then((n) => {
        if (!alive) return;
        setCount(n);
        setBust(Date.now());
      })
      .catch((e) => alive && setRenderError(String((e as Error).message ?? e)))
      .finally(() => alive && setRendering(false));
    return () => {
      alive = false;
    };
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
      {renderError && <p className="text-sm text-amber-600 dark:text-amber-400">{renderError}(不影响下载)</p>}

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
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-8"
          onClick={() => setLightbox(null)}
        >
          <button className="absolute right-4 top-4 text-white/80 hover:text-white">
            <X className="h-6 w-6" />
          </button>
          <img
            src={previewUrl(run.jobId, lightbox, bust)}
            alt={`slide ${lightbox}`}
            className="max-h-full max-w-full rounded-lg shadow-2xl"
          />
        </div>
      )}
    </div>
  );
}
