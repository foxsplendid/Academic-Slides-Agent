"""Few-shot canvas exemplars (MIT, see canvas_exemplars/README.md): pick ONE full-page SVG whose
composition matches the slide's intent and hand it to the canvas authoring prompt as a style
reference. The craft transfers; colors/data are overridden by the prompt contract."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

_DIR = Path(__file__).parent / "canvas_exemplars"

# Order matters: first keyword hit wins.
_ROUTES: list[tuple[tuple[str, ...], str]] = [
    (("相关", "散点", "回归", "拟合", "预测值", "观测"), "scatter_chart"),
    (("趋势", "随时间", "演化", "变化曲线", "时序"), "line_chart"),
    (("流程", "步骤", "工作流", "管线", "pipeline"), "process_flow"),
    (("时间线", "历程", "里程碑", "年代"), "timeline"),
    (("对照表", "对比表", "方法对比", "前人", "基线对比"), "comparison_table"),
    (("矩阵", "象限", "权衡", "取舍"), "matrix_2x2"),
    (("热图", "矩阵图", "相关矩阵"), "heatmap_chart"),
    (("分布", "箱线", "四分位"), "box_plot_chart"),
    (("区间", "误差棒", "置信", "前后对比"), "dumbbell_chart"),
    (("构成", "占比", "堆叠"), "stacked_bar_chart"),
    (("指标", "性能", "成果", "亮点", "关键数值"), "kpi_cards"),
    (("对比", "比较", "组间"), "grouped_bar_chart"),
]


def pick_exemplar(*hints: Optional[str]) -> Optional[tuple[str, str]]:
    """Return (name, svg) for the first route whose keyword appears in the joined hints."""
    text = " ".join(h for h in hints if h)
    for keys, name in _ROUTES:
        if any(k in text for k in keys):
            f = _DIR / f"{name}.svg"
            if f.is_file():
                return name, f.read_text(encoding="utf-8")
    return None
