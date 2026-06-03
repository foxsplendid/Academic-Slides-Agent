# Academic-Slides-Agent

> Turn hard-science papers (PDF / LaTeX + supplementary data) into **rigorous,
> native-editable `.pptx`** for academic group meetings and conferences.

Unlike business-deck generators (Gamma, Tome), this tool targets the "hard science"
bottlenecks: heavy LaTeX math & chemistry, high-density experimental tables, strict
institutional templates, and unpublished-data privacy (local / self-hosted).

**Status:** 🚧 early scaffold. Architecture is locked; implementation starting from the
deterministic compiler (risk-first). See [`docs/SPEC.md`](docs/SPEC.md) — the authoritative
architecture constitution.

## Core idea (one line)

The LLM only ever emits a validated **Slide-IR** (structured JSON); a deterministic,
AI-free **compiler** renders it into native `python-pptx` objects. Orchestrated by
**LangGraph** (human Hard-Stop + streaming + resume). Frontend is **export-first** in v1.

```
Evidence Pool ─▶ Agents (LangGraph) ─▶ Slide-IR (JSON) ─▶ Compiler ─▶ native .pptx
   (papers +        outline → IR,          ▲ human审批         ▲ deterministic, no AI
    attachments)    Critic loop          (Hard-Stop)          ▲ native tables/formulas
```

## License

**Apache-2.0** (see [`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). Clean-room design — no AGPL/GPL
code. Inspired by MIT projects only (ppt-master, Auto-Slides, markitdown).

## Development workflow

This repo uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven,
AI-agent development. Each feature starts as a reviewed change proposal:

```
/opsx:propose "<idea>"   # draft proposal.md + design.md + tasks.md + specs/
#   ↳ human review (the Hard-Stop of the dev process)
/opsx:apply              # implement the approved tasks
/opsx:archive            # archive the completed change (changelog trail)
```

The first proposal — `add-slide-ir` — lives in `openspec/changes/add-slide-ir/`.
