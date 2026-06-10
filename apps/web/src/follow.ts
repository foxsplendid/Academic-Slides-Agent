/** Shared job-stream follower: starts/attaches/resumes a job's SSE stream and drives the store.
 * Used by GenerateView (after upload), Sidebar (re-open an in-progress job), ApprovalView (reject). */

import { listJobs, streamJob } from "./api";
import { useStore } from "./store";

export function followJob(jobId: string, reject?: { feedback: string }): () => void {
  const { patchRun, appendLog, setView, setHistory } = useStore.getState();
  patchRun({ jobId, busy: true, error: null });
  return streamJob(
    jobId,
    {
      onUpdate: (node, phase) => appendLog(`节点 ${node}${phase ? ` · ${phase}` : ""}`),
      onProgress: (p) => {
        if (p.phase === "slide") patchRun({ stage: "generate", done: p.done ?? 0, total: p.total ?? 0 });
        else if (p.phase.startsWith("skeleton")) patchRun({ stage: "outline", total: p.total ?? 0 });
        else if (p.phase === "repair") patchRun({ stage: "critic" });
        appendLog(p.total ? `${p.phase} ${p.done ?? ""}/${p.total}` : p.phase);
      },
      onAwaitingApproval: (outline) => {
        patchRun({ outline, stage: "review", busy: false });
        listJobs().then(setHistory);
        setView("approval");
      },
      onDone: (outputPath) => {
        patchRun({ outputPath, stage: "done", busy: false });
        listJobs().then(setHistory);
        setView("result");
      },
      onError: (msg) => patchRun({ error: msg, busy: false }),
    },
    reject,
  );
}
