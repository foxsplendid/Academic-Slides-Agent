[English](README.md) | 中文

# Academic-Slides-Agent

> 一次上传,把硬科学论文(PDF + 补充数据)转成严谨、原生可编辑的 `.pptx`。

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-275_passing-brightgreen.svg)](#状态)
[![Spec](https://img.shields.io/badge/SPEC-v0.5.5-informational.svg)](docs/SPEC.md)

## 相关文档

[README](README.md) · [中文 README.zh](README.zh.md) · [CLAUDE](CLAUDE.md) · [docs/SPEC](docs/SPEC.md)

**套件:** [scriptorium-spec](https://github.com/scriptorium-suite/scriptorium-spec)(契约 SSoT)· [steward](https://github.com/scriptorium-suite/steward) · [Provenance](https://github.com/foxsplendid/Provenance) · [Academic-Slides-Agent / Lectern](https://github.com/foxsplendid/Academic-Slides-Agent) · [.github](https://github.com/scriptorium-suite/.github)
> 契约事实以 **scriptorium-spec/README** 为准;其他仓库镜像,绝不另立分叉。

## 概述

Academic-Slides-Agent(又名 *Lectern*)把一篇硬科学论文——或一个 Scriptorium `handoff/1.x` 包——转成
用于组会与会议报告的演示文稿。与商业演示生成器(Gamma、Tome)不同,它专攻硬科学的痛点:繁重的 LaTeX
数学与化学公式、高密度实验表格、直接取自论文的真实图件、严格的学术叙事,以及自带模型、保护未发表数据
隐私的部署。

唯一的架构铁律:**LLM 永远只输出经 Pydantic 校验的 `Slide-IR`**(封闭词汇的结构化 JSON);一个独立的
**确定性、无 AI 的编译器**把 IR 渲染成原生 `python-pptx` 对象。模型只提供*语义*,几何由确定性引擎计算,
因此它产出的每一页都是真正的 PowerPoint 对象——可编辑文本、原生表格、原生图表、矢量图形,而非截图。

```
论文 +   ─▶ 摄取 ─▶ 证据池 ─▶ 智能体(LangGraph)─▶ Slide-IR ─▶ 编译器 ─▶ 原生
附件        级联             骨架→扩写→评审         (JSON)      (无 AI)    .pptx
          +缓存  (溯源)      ▲ 人工审批(Hard-Stop)
```

## 功能特性

- **摄取** — 多文件输入(PDF + Excel/CSV/zip/图片)或 Scriptorium `handoff/1.x` 包(含 `meta.json` +
  PDF 的目录)。质量门控的解析级联:**MinerU** 云 API → **Docling**(MIT,可选)→ **pdfplumber**(始终
  可用的本地兜底)。内容寻址解析缓存、按运行隔离、复合图面板检测,保证多面板图不会被当成整图误用。
- **规划** — 两阶段规划器(骨架 → 逐页聚焦扩写,并行扩写),产出学术组会叙事,带逐页讲稿、保留文献
  引用,每张图都锚定到真实的证据池 asset id。页数与密度默认由模型决定,另有可选的简洁/标准/详尽档位。
- **评审 + 人工门** — 确定性、无 AI 的评审器检出空白/溢出页、悬空图引用、断裂的图件边、近重复标题、
  目录↔章节不一致,并进入有限的修复循环。LangGraph 的 `interrupt()` **Hard-Stop** 让人工在编译前审批
  或退回大纲——按页码退回某一页,就只重做那一页。
- **原生编译器(完全可编辑)** — Slide-IR → 原生 python-pptx:CJK 感知的要点/表格;原生
  `bar`/`line`/`scatter`/`pie` 图表(含"预测 vs 参考"散点 + 自动 1:1 对角线);图件
  (`flow`/`tree`/`cycle`/`comparison`/`pyramid`/`timeline`)由语义节点+边生成(无坐标);按长宽比定列宽
  的图片布局;分层公式渲染(matplotlib → MathJax + mhchem Node 边车 → 实验性原生可编辑 OMML);整体外壳
  (章节分隔页、结论横条、统一页眉/页脚);以及精品档 **VisualCanvas**(受约束 SVG → 经 vendored 的 MIT
  SVG→DrawingML 引擎转为可编辑矢量,任何失败都自动回退到确定性版式)。
- **交付** — FastAPI 服务(SSE 流式、可断点续跑的后台任务)+ React 导出优先 Web UI(上传 → 实时进度 →
  大纲审批 → 下载),含全屏翻页看图。
- **隐私** — 密钥只存在本地、已 gitignore 的 `.env`;把 OpenAI 兼容的 base URL 指向本地 Ollama/vLLM,
  可让未发表数据完全留在自己的硬件上。

## 安装

一个由可编辑工作区包(位于 `packages/` 与 `apps/`)+ React Web UI 组成的 Python monorepo。需要
**Python 3.12+** 与 Node.js(用于 Web UI 及 MathJax 公式边车)。

```bash
# 1) Python 依赖 —— 工作区包的可编辑安装(推荐 uv,pip 亦可)
uv venv && . .venv/bin/activate          # 或:python -m venv .venv && source .venv/bin/activate
uv pip install -e packages/core/ir -e packages/core/compiler -e packages/core/formula \
               -e packages/ingestion -e packages/agents -e packages/vendor/svg2pptx \
               -e "packages/providers[openai]" -e apps/api     # 或 providers[anthropic]

# 2) 配置 —— 复制模板并填入你自己的密钥
cp .env.example .env        # 编辑 .env(已 gitignore,切勿提交真实密钥)
```

**一键启动(Windows):** 双击 [`start-dev.bat`](start-dev.bat) —— 自动检查 `.venv`/npm,首次安装前端
依赖,在各自窗口启动后端(`:8000`)与 Vite 开发服务器(`:5173`),并打开浏览器。

## 使用

```bash
# 启动 API
python -m asa_api           # http://127.0.0.1:8000

# 启动 Web UI(另开终端)
cd apps/web && npm install && npm run dev   # http://localhost:5173
```

也可直接调 API:`POST /jobs/upload`(摄取输入)→ `GET /jobs/{id}/stream`(SSE)→ 审阅大纲 →
`POST /jobs/{id}/approve` → `GET /jobs/{id}/download`。

配置通过环境变量进行(完整带注释列表见 [`.env.example`](.env.example))。核心项:

| 变量 | 用途 |
|---|---|
| `ASA_LLM_PROVIDER` | `openai` \| `deepseek` \| `anthropic` |
| `ASA_<PROVIDER>_API_KEY` / `_BASE_URL` / `_MODEL` | 各家密钥、私有网关 URL、模型覆盖 |
| `MINERU_API_KEY` | MinerU 云解析(可选);未配则回退 pdfplumber |
| `ASA_PDF_PARSER` | `auto` \| `mineru` \| `pdfplumber` \| `docling` |
| `ASA_STYLE` | `academic`(默认)\| `modern_teal` |
| `ASA_VLM_CRITIC` / `ASA_VLM_MODEL` | 可选的渲染后视觉评审 |
| `ASA_HOST` / `ASA_PORT` / `ASA_CORS_ORIGINS` / `ASA_OUT_DIR` | 服务主机/端口/CORS/输出目录 |

## 项目结构

```
packages/
  core/ir            # asa-slide-ir:Slide-IR 契约(Pydantic)—— 唯一的架构不变量
  core/compiler      # asa-pptx-compiler:确定性 IR → 原生 python-pptx(块/布局/图件/样式/画布)
  core/formula       # asa-formula:分层公式渲染(matplotlib / MathJax 边车 / OMML)+ 图标
  ingestion          # asa-ingestion:解析级联、缓存、图/面板处理、补充数据
  agents             # asa-agents:大纲 + 两阶段规划器、确定性评审、LangGraph 编排
  providers          # asa-providers:LLM 适配器(OpenAI 兼容、Anthropic)+ 命名档位
  vendor/svg2pptx    # asa-svg2pptx:vendored 的 MIT SVG→DrawingML 引擎(来源见其 README)
apps/
  api                # asa-api:FastAPI 服务(SSE、上传、审批、下载、断点续跑)
  web                # asa-web:React + Vite + Tailwind 导出优先 UI
docs/SPEC.md         # 架构宪法(活文档 + 变更日志)
openspec/            # 规范驱动开发:specs/(现行)+ changes/archive/(历史)
templates/           # 样式/模板资源
start-dev.bat        # Windows 一键开发启动脚本
```

## 状态

活跃开发中。SPEC 版本 **v0.5.5**;工作区包为 `0.1.0`(Web UI `0.2.0`)。通过
[OpenSpec](https://github.com/Fission-AI/OpenSpec) 规范驱动:每项能力先作为评审过的变更提案,实现后
归档进现行规范与变更日志。仓库根目录运行测试:`python -m pytest -q`(276 项;275 通过,1 跳过)。
[`docs/SPEC.md`](docs/SPEC.md) 是权威架构宪法。

## 许可证

**Apache-2.0** —— 见 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE)。

核心(Slide-IR、智能体、确定性编译器)是净室独立实现,不含任何 AGPL/GPL 代码。`packages/vendor/svg2pptx`
与 `packages/agents/asa_agents/canvas_exemplars` 两个组件**仅** vendored 自 `CRui5in/paper-ppt-agent`
在 commit `6f679fc`(2026-05-15,转 AGPL 之前)的 **MIT 许可快照**;完整来源见
`packages/vendor/svg2pptx/README.md`。重型工具均以 arms-length 方式使用(MinerU 云 API、MathJax Node
子进程、可选 Docling 插件)。
