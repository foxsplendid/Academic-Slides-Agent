# Academic-Slides-Agent

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-264_passing-brightgreen.svg)](#开发)
[![Spec](https://img.shields.io/badge/SPEC-v0.5.3-informational.svg)](docs/SPEC.md)

[English](README.md) · **简体中文**

> 一次上传,把硬科学论文(PDF + 补充数据)转成**严谨、原生可编辑的 `.pptx`**,用于组会与会议报告。

与商业演示生成器(Gamma、Tome)不同,Academic-Slides-Agent 专攻*硬科学*的痛点:繁重的 LaTeX
数学与化学公式、高密度实验表格、**直接取自论文的真实图件**、严格的学术叙事,以及自带模型、保护未发表
数据隐私的部署。它产出的每一页都是**真正的 PowerPoint 对象**——可编辑文本、原生表格、原生图表、矢量
图形,而非截图。

---

## 与众不同之处

唯一的架构铁律:**LLM 永远只输出经 Pydantic 校验的 `Slide-IR`**(封闭词汇的结构化 JSON);一个独立的
**确定性、无 AI 的编译器**把 IR 渲染成原生 `python-pptx` 对象。模型只提供*语义*,几何由确定性引擎计算。

| | Academic-Slides-Agent | 让 LLM 写 SVG/坐标的工具 |
|---|---|---|
| 图件/图表 | 原生、可编辑、不会坏 | 经常渲染成空白/错标/重叠 |
| 失败模式 | 渲染前就被 schema 拒绝 | 坐标与溢出幻觉 |
| 可复现 | 同一 IR → 永远同一份 `.pptx` | 每次随机 |
| 编辑 | 真正的 PPT 形状与表格 | 压平的矢量/图片 |

"绝不让模型写坐标"这一论点经过了**实证验证**:在与某 AGPL agent 模式生成器的盲测(同论文、同渲染器、
A/B)中,评委反复独立指出对方的**自绘图表**是复发性致命伤(无坐标轴的 SHAP 图、空面板、文字重叠),而
本项目的 deck **零损坏图件**。六轮迭代中,偏好从 0/4 演进到 3/4 胜出——当确定性的统一外壳补齐了最后的
机械一致性短板之后。

```
论文 +   ─▶ 摄取 ─▶ 证据池 ─▶ 智能体(LangGraph)─▶ Slide-IR ─▶ 编译器 ─▶ 原生
附件        级联             骨架→扩写→评审         (JSON)      (无 AI)    .pptx
          +缓存  (溯源)      ▲ 人工审批(Hard-Stop)        ▲ 表格/图表/图件/公式/图/画布
```

## 它能做什么

**摄取** — 多文件输入(PDF + Excel/CSV/zip/图片)。质量门控的解析级联:**MinerU** 云 API(高保真
文本/公式/表格/图件)→ **Docling**(MIT,可选)→ **pdfplumber**(始终可用的本地兜底)。内容寻址解析
缓存;按运行隔离;复合图面板检测与同页面板分组——保证多面板图不会被当成整图误用。

**规划** — 两阶段规划器(骨架 → 逐页聚焦扩写,每页只看自己那部分证据的全分辨率),并行扩写。学术组会
叙事,逐页讲稿、结果页一条解读要点、术语原样保留、文献引用保留,每张图都锚定到真实的证据池 asset
id——无虚构引用。**页数与密度默认由模型决定**(论文内容驱动篇幅);可选简洁/标准/详尽档位。

**评审 + 人工门** — 确定性、无 AI 的评审器检出空白/溢出页、悬空图引用、断裂的图件边、版式误选、近重复
标题、目录↔章节不一致、重复用图与稀疏页;结果进入有限的修复循环。LangGraph 的 `interrupt()`
**Hard-Stop** 让人工在编译前审批(或带反馈退回)大纲——**按页码退回某一页,就只重做那一页**。

**编译器(原生、完全可编辑)** — Slide-IR → 原生 python-pptx:
- **要点 / 表格**:CJK 感知字体 + `**…**` 强调
- **图表**(`bar`/`line`/`scatter`/`pie`)→ 原生、可双击编辑的 PPT 图表,含"预测 vs 参考"一致性散点 +
  自动 1:1 对角线
- **图件**(`flow`/`tree`/`cycle`/`comparison`/`pyramid`/`timeline`)— 模型只给语义节点 + 边(无坐标),
  确定性布局引擎生成原生形状 + 连接线
- **图片**:通用构图引擎按图的长宽比定列宽(消除"小图配大片留白")
- **公式**:分层图像渲染(matplotlib → MathJax + mhchem Node 边车)+ 实验性原生可编辑 **OMML** 档
- **整体外壳**:带本章预览的编号章节分隔页、样式化 kicker 结论横条、每页统一页眉 + 编号页脚面包屑、
  统计芯片
- **精品档 VisualCanvas**:对最有价值的结果/机制页,模型可创作整页受约束 SVG(自由构图);封闭禁项
  守卫 + 确定性几何 lint + vendored 的 MIT SVG→DrawingML 引擎把它转成**可编辑矢量 + 文本**(非截图),
  任何失败都自动回退到确定性版式

**交付** — FastAPI 服务(SSE 流式、可断点续跑的后台任务)+ React 导出优先 Web UI(上传 → 实时进度 →
大纲审批 → 下载),含全屏翻页看图。

## 快速开始

**一键启动(Windows):** 双击 [`start-dev.bat`](start-dev.bat) —— 自动检查 `.venv`/npm,首次安装前端
依赖,在各自窗口启动后端(`:8000`)与 Vite 开发服务器(`:5173`)(已运行则复用),并打开浏览器。

**手动安装:**

```bash
# 1) Python 依赖 —— 工作区包的可编辑安装(推荐 uv,pip 亦可)
uv venv && . .venv/bin/activate
uv pip install -e packages/core/ir -e packages/core/compiler -e packages/core/formula \
               -e packages/ingestion -e packages/agents -e packages/vendor/svg2pptx \
               -e "packages/providers[openai]" -e apps/api

# 2) 配置 —— 复制模板并填入你自己的密钥
cp .env.example .env        # 编辑 .env(已 gitignore,切勿提交真实密钥)

# 3) 启动 API
python -m asa_api           # http://127.0.0.1:8000

# 4) 启动 Web UI(另开终端)
cd apps/web && npm install && npm run dev   # http://localhost:5173
```

也可直接调 API:`POST /jobs/upload`(摄取输入)→ `GET /jobs/{id}/stream`(SSE)→ 审阅大纲 →
`POST /jobs/{id}/approve` → `GET /jobs/{id}/download`。

## 配置

全部通过环境变量配置(本地、已 gitignore 的 `.env`)。完整带注释列表见 [`.env.example`](.env.example)。
核心项:

| 变量 | 用途 |
|---|---|
| `ASA_LLM_PROVIDER` | `openai` \| `deepseek` \| `anthropic` |
| `ASA_<PROVIDER>_API_KEY` / `_BASE_URL` / `_MODEL` | 各家密钥、私有网关 URL、模型覆盖 |
| `MINERU_API_KEY` | MinerU 云解析(可选,arms-length HTTP);未配则回退 pdfplumber |
| `ASA_PDF_PARSER` | `auto` \| `mineru` \| `pdfplumber` \| `docling` |
| `ASA_STYLE` | `academic`(默认)\| `modern_teal` |
| `ASA_VLM_CRITIC` / `ASA_VLM_MODEL` | 可选的渲染后视觉评审 |
| `ASA_HOST` / `ASA_PORT` / `ASA_CORS_ORIGINS` / `ASA_OUT_DIR` | 服务主机/端口/CORS/输出目录 |

> **隐私:** 密钥只存在本地 `.env`。把 `ASA_OPENAI_BASE_URL` 指向本地 Ollama/vLLM,可让未发表数据完全
> 留在自己的硬件上。

## 项目结构

```
packages/
  core/ir/slide_ir            # Slide-IR 契约(Pydantic)—— 唯一的架构不变量
  core/compiler/pptx_compiler # 确定性 IR → 原生 python-pptx(块/布局/图件/样式/画布)
  core/formula/formula_render # 分层公式渲染(matplotlib / MathJax 边车 / OMML)+ 图标
  ingestion                   # 解析级联、缓存、图/面板处理、补充数据
  agents/asa_agents           # 大纲 + 两阶段规划器、确定性评审、LangGraph 编排
  providers/asa_providers     # LLM 适配器(OpenAI 兼容、Anthropic)+ 命名档位
  vendor/svg2pptx             # vendored 的 MIT SVG→DrawingML 引擎(来源见其 README)
apps/
  api/asa_api                 # FastAPI 服务(SSE、上传、审批、下载、断点续跑)
  web                         # React 导出优先 UI
docs/SPEC.md                  # 架构宪法(活文档 + 变更日志)
openspec/                     # 规范驱动开发:specs/(现行)+ changes/archive/(历史)
```

## 开发

通过 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 规范驱动:每项能力先作为评审过的变更提案,实现后
归档进现行规范与变更日志。

```
提案  →  人工评审(开发流程的 Hard-Stop)  →  应用  →  归档
```

仓库根目录运行测试:`python -m pytest -q`(264 passing)。
[`docs/SPEC.md`](docs/SPEC.md) 是权威架构宪法。

## 许可与署名

**Apache-2.0**(见 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE))。

核心(Slide-IR、智能体、确定性编译器)是净室独立实现,**不含任何 AGPL/GPL 代码**。`packages/vendor/svg2pptx`
与 `packages/agents/asa_agents/canvas_exemplars` 两个组件**仅** vendored 自 `CRui5in/paper-ppt-agent`
在 commit `6f679fc`(2026-05-15,转 AGPL 之前)的 **MIT 许可快照**;完整来源见
`packages/vendor/svg2pptx/README.md`。重型工具均以 arms-length 方式使用(MinerU 云 API、MathJax Node
子进程、可选 Docling 插件)。这为 open-core 路线留出空间。

## 路线图

位置/标签感知的图↔图注对齐;更丰富的图表与图件覆盖;在 PowerPoint 中验证原生 OMML(化学、矩阵);
基于母版继承的模板市场;更多样式档位。
