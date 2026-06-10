import { CheckCircle2, Clock3, FilePlus2, Moon, Presentation, Sun, Trash2 } from "lucide-react";
import { deleteJob, listJobs, type JobMeta } from "../api";
import { useStore } from "../store";

const STATUS_BADGE: Record<JobMeta["status"], { label: string; cls: string }> = {
  done: { label: "完成", cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300" },
  awaiting_approval: { label: "待审批", cls: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300" },
  created: { label: "进行中", cls: "bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300" },
  expired: { label: "已过期", cls: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400" },
};

export function Sidebar() {
  const { history, setHistory, theme, toggleTheme, resetRun, patchRun, setView, run } = useStore();

  async function refresh() {
    setHistory(await listJobs());
  }

  async function openJob(job: JobMeta) {
    if (job.status === "done") {
      patchRun({ jobId: job.job_id, title: job.title, outputPath: "disk", error: null });
      setView("result");
    }
  }

  async function remove(e: React.MouseEvent, jobId: string) {
    e.stopPropagation();
    await deleteJob(jobId);
    await refresh();
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-4 dark:border-slate-800">
        <Presentation className="h-6 w-6 text-primary" />
        <div>
          <div className="text-sm font-bold leading-tight">Academic Slides</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">论文 → 原生可编辑 PPT</div>
        </div>
      </div>

      <div className="px-3 pt-3">
        <button className="btn-primary w-full justify-center" onClick={resetRun}>
          <FilePlus2 className="h-4 w-4" /> 新建任务
        </button>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto px-3 pb-3">
        <div className="mb-2 flex items-center justify-between px-1">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">历史任务</span>
          <button className="text-xs text-slate-400 hover:text-primary" onClick={refresh}>
            刷新
          </button>
        </div>
        <ul className="space-y-1.5">
          {history.map((j) => {
            const badge = STATUS_BADGE[j.status] ?? STATUS_BADGE.expired;
            const active = run.jobId === j.job_id;
            return (
              <li
                key={j.job_id}
                onClick={() => openJob(j)}
                className={`group cursor-pointer rounded-lg border px-3 py-2 transition-colors ${
                  active
                    ? "border-primary/40 bg-primary/5"
                    : "border-transparent hover:border-slate-200 hover:bg-slate-50 dark:hover:border-slate-700 dark:hover:bg-slate-800/60"
                }`}
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="truncate text-xs font-medium" title={j.title}>
                    {j.title}
                  </span>
                  <button
                    className="hidden text-slate-400 hover:text-red-500 group-hover:block"
                    onClick={(e) => remove(e, j.job_id)}
                    title="删除任务"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="mt-1 flex items-center justify-between">
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${badge.cls}`}>
                    {j.status === "done" ? (
                      <CheckCircle2 className="mr-0.5 inline h-3 w-3" />
                    ) : (
                      <Clock3 className="mr-0.5 inline h-3 w-3" />
                    )}
                    {badge.label}
                  </span>
                  <span className="text-[10px] text-slate-400">{j.created_at.slice(5, 16)}</span>
                </div>
              </li>
            );
          })}
          {history.length === 0 && (
            <li className="px-1 py-2 text-xs text-slate-400">暂无历史任务</li>
          )}
        </ul>
      </div>

      <div className="border-t border-slate-200 p-3 dark:border-slate-800">
        <button className="btn-ghost w-full justify-center text-xs" onClick={toggleTheme}>
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {theme === "dark" ? "浅色模式" : "深色模式"}
        </button>
      </div>
    </aside>
  );
}
