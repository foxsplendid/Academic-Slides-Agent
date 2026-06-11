import { useCallback, useEffect } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { previewUrl } from "../api";

/** Full-screen slide viewer with prev/next arrows and keyboard navigation — no need to close and
 * reopen to flip through the deck. */
export function Lightbox({
  jobId,
  index,
  count,
  bust,
  onNavigate,
  onClose,
}: {
  jobId: string;
  index: number; // 1-based
  count: number;
  bust: number;
  onNavigate: (idx: number) => void;
  onClose: () => void;
}) {
  const prev = useCallback(() => onNavigate(index > 1 ? index - 1 : count), [index, count, onNavigate]);
  const next = useCallback(() => onNavigate(index < count ? index + 1 : 1), [index, count, onNavigate]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") prev();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next, onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-8" onClick={onClose}>
      <button
        className="absolute right-4 top-4 text-white/80 hover:text-white"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        aria-label="关闭"
      >
        <X className="h-6 w-6" />
      </button>
      <button
        className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white/80 hover:bg-black/60 hover:text-white"
        onClick={(e) => {
          e.stopPropagation();
          prev();
        }}
        aria-label="上一页"
      >
        <ChevronLeft className="h-7 w-7" />
      </button>
      <img
        src={previewUrl(jobId, index, bust)}
        alt={`slide ${index}`}
        className="max-h-full max-w-full rounded-lg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
      <button
        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white/80 hover:bg-black/60 hover:text-white"
        onClick={(e) => {
          e.stopPropagation();
          next();
        }}
        aria-label="下一页"
      >
        <ChevronRight className="h-7 w-7" />
      </button>
      <span className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-3 py-1 text-xs text-white/90">
        {index} / {count}
      </span>
    </div>
  );
}
