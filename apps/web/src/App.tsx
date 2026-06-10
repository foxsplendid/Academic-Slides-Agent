import { useEffect } from "react";
import { listJobs } from "./api";
import { Sidebar } from "./components/Sidebar";
import { GenerateView } from "./components/GenerateView";
import { ApprovalView } from "./components/ApprovalView";
import { ResultView } from "./components/ResultView";
import { useStore } from "./store";

export function App() {
  const { view, theme, setHistory } = useStore();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    listJobs().then(setHistory);
  }, [setHistory]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6">
          {view === "generate" && <GenerateView />}
          {view === "approval" && <ApprovalView />}
          {view === "result" && <ResultView />}
        </div>
      </main>
    </div>
  );
}
