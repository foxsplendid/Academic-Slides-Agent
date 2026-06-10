/** Global UI state (zustand): view routing, current job lifecycle, history, theme. */

import { create } from "zustand";
import type { Ingested, JobMeta, OutlineItem } from "./api";

export type View = "generate" | "approval" | "result";
export type Stage = "parse" | "outline" | "generate" | "critic" | "review" | "compile" | "done";

export interface RunState {
  jobId: string;
  title: string;
  ingested: Ingested | null;
  warnings: string[];
  stage: Stage;
  done: number;
  total: number;
  log: string[];
  outline: OutlineItem[];
  outputPath: string | null;
  busy: boolean;
  error: string | null;
}

const emptyRun = (): RunState => ({
  jobId: "",
  title: "",
  ingested: null,
  warnings: [],
  stage: "parse",
  done: 0,
  total: 0,
  log: [],
  outline: [],
  outputPath: null,
  busy: false,
  error: null,
});

interface Store {
  view: View;
  run: RunState;
  history: JobMeta[];
  theme: "light" | "dark";
  setView: (v: View) => void;
  patchRun: (p: Partial<RunState>) => void;
  appendLog: (line: string) => void;
  resetRun: () => void;
  setHistory: (h: JobMeta[]) => void;
  toggleTheme: () => void;
}

const initialTheme = (): "light" | "dark" => {
  const saved = localStorage.getItem("asa-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

export const useStore = create<Store>((set) => ({
  view: "generate",
  run: emptyRun(),
  history: [],
  theme: initialTheme(),
  setView: (view) => set({ view }),
  patchRun: (p) => set((s) => ({ run: { ...s.run, ...p } })),
  appendLog: (line) => set((s) => ({ run: { ...s.run, log: [...s.run.log.slice(-199), line] } })),
  resetRun: () => set({ run: emptyRun(), view: "generate" }),
  setHistory: (history) => set({ history }),
  toggleTheme: () =>
    set((s) => {
      const theme = s.theme === "dark" ? "light" : "dark";
      localStorage.setItem("asa-theme", theme);
      return { theme };
    }),
}));
