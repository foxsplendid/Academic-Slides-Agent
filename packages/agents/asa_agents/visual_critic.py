"""Opt-in VLM visual critic: render the compiled deck to images, check a CLOSED defect taxonomy,
emit IR-level repair findings.

Free-form aesthetic critique is deliberately out of scope (unreliable — Design2Code showed VLM
self-revision can regress); the VLM only confirms enumerated, checkable defects and suggests
IR-level fixes (switch layout / split slide / shorten bullets). Disabled unless a vision-capable
LLM is injected (server gates on ``ASA_VLM_CRITIC``). Rendering prefers LibreOffice headless
(license-clean subprocess) -> pypdfium2; falls back to PowerPoint COM on a Windows dev box.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from slide_ir import SlideIR

_SYSTEM = """你是幻灯片版面缺陷检查器。逐页检查渲染图,只报告下列**封闭清单**内的缺陷:
- text_overflow:文字溢出文本框/被裁切
- element_overlap:元素相互遮挡
- figure_too_small:配图小到无法辨认
- slide_too_dense:内容塞得过满、无留白
- slide_too_empty:大面积空白且内容单薄
只输出 JSON 数组:[{"slide_index": <1起算的页码>, "defect": "<清单内的缺陷名>", "suggestion": "<IR 级修复建议:如 换版式 big_figure / 拆成两页 / 精简 bullets / 删去一个 block>"}]
没有缺陷输出 []。不要美学评论,不要建议改颜色或字体,不要输出清单之外的缺陷。"""

_DEFECTS = {"text_overflow", "element_overlap", "figure_too_small", "slide_too_dense", "slide_too_empty"}


@runtime_checkable
class VisionLLM(Protocol):
    def complete_vision(self, prompt: str, *, images: list[Path], system: Optional[str] = None) -> str: ...


def _render_via_soffice(pptx: Path, out_dir: Path) -> Optional[list[Path]]:
    soffice = shutil.which("soffice")
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
            check=True, capture_output=True, timeout=120,
        )
        pdf = out_dir / (pptx.stem + ".pdf")
        if not pdf.is_file():
            return None
        import pypdfium2 as pdfium  # BSD/Apache — already a project dependency (ingestion)

        doc = pdfium.PdfDocument(str(pdf))
        out: list[Path] = []
        for i in range(len(doc)):
            img = doc[i].render(scale=1.5).to_pil()
            p = out_dir / f"slide_{i + 1:03d}.png"
            img.save(str(p))
            out.append(p)
        return out
    except Exception:
        return None


def _render_via_powerpoint_com(pptx: Path, out_dir: Path) -> Optional[list[Path]]:
    """Windows dev-box fallback (PowerPoint COM via PowerShell). Never use server-side."""
    if sys.platform != "win32":
        return None
    script = (
        "$pp=New-Object -ComObject PowerPoint.Application;"
        f"$p=$pp.Presentations.Open('{pptx}', $true, $false, $false);"
        f"$p.Export('{out_dir}','PNG',1280,720);$p.Close();$pp.Quit()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True, capture_output=True, timeout=180)
        pngs = sorted(out_dir.glob("*.PNG")) or sorted(out_dir.glob("*.png"))
        # PowerPoint names exports Slide1.PNG..SlideN.PNG — sort numerically.
        pngs.sort(key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
        return pngs or None
    except Exception:
        return None


def render_pptx_images(pptx: str | Path, out_dir: str | Path) -> list[Path]:
    """Render every slide to PNG; [] when no renderer is available (the critic then skips)."""
    pptx, out_dir = Path(pptx), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return _render_via_soffice(pptx, out_dir) or _render_via_powerpoint_com(pptx, out_dir) or []


def visual_critique(
    slides: list[SlideIR], pptx_path: str | Path, vlm: VisionLLM, workspace: str | Path, *, max_slides: int = 16
) -> list[str]:
    """Render + VLM-check the deck; findings are repair-routable (``slide '<id>': ...``)."""
    images = render_pptx_images(pptx_path, Path(workspace))
    if not images:
        return []
    images = images[:max_slides]
    prompt = f"这是一份 {len(images)} 页的学术幻灯片逐页渲染图(按顺序)。请按系统指令检查并输出 JSON。"
    try:
        raw = vlm.complete_vision(prompt, images=images, system=_SYSTEM)
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        items = json.loads(m.group(0)) if m else []
    except Exception:
        return []
    findings: list[str] = []
    for it in items if isinstance(items, list) else []:
        try:
            idx = int(it.get("slide_index", 0)) - 1
            defect = str(it.get("defect", ""))
            if 0 <= idx < len(slides) and defect in _DEFECTS:
                sug = str(it.get("suggestion", "")).strip()
                findings.append(f"slide '{slides[idx].slide_id}': visual {defect}{' — ' + sug if sug else ''}")
        except Exception:
            continue
    return findings
