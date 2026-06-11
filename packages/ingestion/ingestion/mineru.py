"""High-fidelity PDF parsing via the MinerU cloud API (mineru.net/api/v4).

MinerU is called as an **arms-length HTTP service** (request upload URL -> PUT file -> poll batch
results -> download a result zip), so our Apache code never links MinerU and stays license-clean. We
implement our own thin client against MinerU's public API docs; the structured ``content_list.json`` is
mapped into the Evidence Pool. Uses only the stdlib (urllib/zipfile/json) — no new dependencies.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

_FIG_CAPTION = re.compile(r"^(?:Fig\.?|Figure)\s*\.?\s*\d", re.IGNORECASE)

from slide_ir import EvidenceAsset, TableBlock

from .models import IngestResult, add_table, is_low_quality_table

DEFAULT_API_URL = "https://mineru.net/api/v4"


# --------------------------------------------------------------------------- #
# Pure parser: MinerU content_list -> Evidence Pool (unit-tested, no network)  #
# --------------------------------------------------------------------------- #


class _TableHTMLParser(HTMLParser):
    """Minimal <table> -> rows[list[str]] extractor."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: Optional[list[str]] = None
        self._cell: Optional[list[str]] = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


# Real paper figures (rendered ~200 DPI) are far larger than publisher badges/logos/icons.
_MIN_FIG_SIDE_PX = 100
_MIN_FIG_AREA_PX = 40_000


def _is_junk_image(path: Path) -> bool:
    """Publisher badges ("Check for updates"), logos and icons are tiny — filter them out so they
    never enter the Evidence Pool (a planner once illustrated a slide with the journal badge)."""
    try:
        from PIL import Image

        with Image.open(str(path)) as im:
            w, h = im.size
        return min(w, h) < _MIN_FIG_SIDE_PX or (w * h) < _MIN_FIG_AREA_PX
    except Exception:
        return False  # unreadable -> keep; downstream placement is defensive anyway


def _clean_caption(caption: str) -> str:
    """Caption hygiene: strip a stray leading panel letter ("B Fig. 4. ..." -> "Fig. 4. ...") and
    drop captions that are ONLY a panel letter ("A") — they are noise, not figure captions."""
    caption = re.sub(r"^[A-Za-z]\s+(?=(?:Fig\.?|Figure)\b)", "", caption).strip()
    if re.fullmatch(r"[A-Za-z]", caption):
        return ""
    return caption


def _html_table_to_block(html: str, caption: Optional[str]) -> Optional[TableBlock]:
    p = _TableHTMLParser()
    try:
        p.feed(html or "")
    except Exception:
        return None
    rows = [r for r in p.rows if any(c.strip() for c in r)]
    if not rows:
        return None
    ncol = max(len(r) for r in rows)
    header = (rows[0] + [""] * (ncol - len(rows[0])))[:ncol]
    columns = [(h.strip() or f"col{i + 1}") for i, h in enumerate(header)]
    data = [(r + [""] * (ncol - len(r)))[:ncol] for r in rows[1:]]
    return TableBlock(columns=columns, rows=data, caption=caption, needs_human_check=True)


def parse_mineru_content_list(
    blocks: list[dict], assets_dir: str | Path, source: str, workspace: str | Path, stem: str
) -> IngestResult:
    """Map MinerU's ``content_list`` blocks into the Evidence Pool. Pure (filesystem only)."""
    assets_dir = Path(assets_dir)
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    result = IngestResult()
    page_text: dict[int, list[str]] = {}
    fig_i = 0

    # Pre-pass: collect "Fig. N" caption texts per page so figures with no explicit caption can borrow one.
    fig_captions: dict[int, list[str]] = {}
    for b in blocks:
        if b.get("type") in ("text", "title"):
            txt = (b.get("text") or "").strip()
            if _FIG_CAPTION.match(txt):
                fig_captions.setdefault(int(b.get("page_idx", 0) or 0), []).append(txt[:200])

    for b in blocks:
        btype = b.get("type")
        page = int(b.get("page_idx", 0) or 0)
        if btype in ("text", "title"):
            txt = (b.get("text") or "").strip()
            if not txt:
                continue
            level = b.get("text_level")
            prefix = ("#" * int(level) + " ") if level else ""
            page_text.setdefault(page, []).append(prefix + txt)
        elif btype in ("equation", "interline_equation", "inline_equation"):
            tex = (b.get("text") or "").strip()
            if tex:
                page_text.setdefault(page, []).append(f"[formula] {tex}")
        elif btype == "table":
            caption = " ".join(b.get("table_caption") or []).strip() or None
            tb = _html_table_to_block(b.get("table_body") or "", caption)
            if tb is not None and not is_low_quality_table(tb):
                add_table(
                    result,
                    tb,
                    asset_id=f"{stem}:p{page}:t{len(result.tables)}",
                    source=source,
                    locator={"page": page + 1, "caption": caption or ""},
                )
        elif btype in ("image", "chart"):  # MinerU renders figures/plots as "chart"
            rel = b.get("img_path")
            if not rel:
                continue
            src_img = assets_dir / rel
            if not src_img.is_file():
                continue
            if _is_junk_image(src_img):  # publisher badges / logos / icons — not paper figures
                continue
            fig_i += 1
            dst = workspace / f"{stem}_mineru_fig{fig_i}{src_img.suffix or '.jpg'}"
            shutil.copyfile(src_img, dst)
            caption = " ".join(b.get("image_caption") or b.get("chart_caption") or []).strip()
            caption = _clean_caption(caption)
            if not caption:  # borrow a same-page "Fig. N" caption when MinerU left it empty
                queue = fig_captions.get(page)
                if queue:
                    caption = queue.pop(0)
            # Short, echo-safe id: the LLM must repeat ids verbatim, and 100+ char filename-based
            # ids get abbreviated into nonexistent ones ("fig3"). 2-char stem digest keeps ids
            # unique when multiple PDFs are ingested into one job.
            import hashlib as _hl

            _h2 = _hl.sha1(stem.encode("utf-8", "ignore")).hexdigest()[:2]
            parent_id = f"fig{fig_i}_p{page}_{_h2}"
            try:
                from PIL import Image as _Img

                _pw, _ph = _Img.open(dst).size
            except Exception:
                _pw = _ph = 0
            result.assets.append(
                EvidenceAsset(
                    asset_id=parent_id,
                    kind="figure",
                    content_ref=str(dst),
                    source=source,
                    locator={"page": page + 1, "caption": caption[:600], "px": [_pw, _ph]},
                )
            )
            if os.environ.get("ASA_SPLIT_FIGURES", "").lower() in ("1", "true", "yes"):
                from .panels import split_composite  # lazy: only when opt-in

                for j, panel in enumerate(split_composite(dst, workspace, f"{stem}_fig{fig_i}")):
                    try:
                        from PIL import Image as _Img

                        _qw, _qh = _Img.open(panel).size
                    except Exception:
                        _qw = _qh = 0
                    result.assets.append(
                        EvidenceAsset(
                            asset_id=f"{parent_id}{chr(97 + (j % 26))}",  # fig3_p4_ab -> panels a/b/c
                            kind="figure",
                            content_ref=str(panel),
                            source=source,
                            locator={
                                "page": page + 1,
                                "caption": caption[:600],
                                "panel": j,
                                "parent": parent_id,
                                "px": [_qw, _qh],
                            },
                        )
                    )

    _propagate_panel_captions(result.assets)

    for page in sorted(page_text):
        result.assets.append(
            EvidenceAsset(
                asset_id=f"{stem}:p{page}",
                kind="section_text",
                content_ref="\n".join(page_text[page]),
                source=source,
                locator={"page": page + 1},
            )
        )
    return result


_FIG_NUM = re.compile(r"(?:Fig(?:ure)?\.?|图)\s*0*(\d+)", re.IGNORECASE)
_PANEL_ONLY = re.compile(r"^\(?\s*[a-z]\s*\)?\b.{0,12}$", re.IGNORECASE)  # "(b)", "a)P [GPa]" — fragment


def _propagate_panel_captions(assets: list) -> None:
    """When MinerU extracts a multi-panel figure as separate same-page images, only one fragment
    carries the full "FIGURE N | ..." caption and the siblings get stubs like "(b)". Without this,
    the planner fabricates per-panel captions. Here: if a page has exactly ONE figure with a real
    "FIGURE N" caption and the rest are fragments, propagate that caption + a panel index to all of
    them so the menu shows the truth and the model labels them 图N-a/图N-b honestly."""
    by_page: dict[int, list] = {}
    for a in assets:
        if a.kind == "figure" and isinstance(a.locator, dict) and a.locator.get("panel") is None:
            by_page.setdefault(a.locator.get("page"), []).append(a)
    for page, figs in by_page.items():
        if len(figs) < 2:
            continue
        leads = [f for f in figs if _FIG_NUM.search(f.locator.get("caption", "") or "")]
        frags = [f for f in figs if _PANEL_ONLY.match((f.locator.get("caption", "") or "").strip())]
        # exactly one full caption + the others fragmentary -> they are panels of the same figure
        if len(leads) == 1 and len(frags) >= 1 and len(leads) + len(frags) == len(figs):
            full = leads[0].locator.get("caption", "")
            m = _FIG_NUM.search(full)
            fig_no = int(m.group(1)) if m else 0
            for idx, f in enumerate(figs):  # keep extraction order as panel order
                f.locator["caption"] = full
                f.locator["panel"] = idx
                f.locator["fig_no"] = fig_no


# --------------------------------------------------------------------------- #
# Network flow                                                                 #
# --------------------------------------------------------------------------- #


def _request(url: str, *, method: str, headers: dict, data: Optional[bytes] = None, timeout: int = 60):
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _put_file(url: str, data: bytes, timeout: int = 600) -> None:
    """PUT raw bytes to a presigned URL with NO Content-Type — urllib would force
    ``application/x-www-form-urlencoded`` and break the OSS signature (403). Mirrors ``curl -T``."""
    import http.client
    import urllib.parse

    u = urllib.parse.urlparse(url)
    conn = http.client.HTTPSConnection(u.netloc, timeout=timeout)
    try:
        path = u.path + (f"?{u.query}" if u.query else "")
        conn.request("PUT", path, body=data, headers={"Content-Length": str(len(data))})
        resp = conn.getresponse()
        body = resp.read()
        if resp.status not in (200, 201, 204):
            raise RuntimeError(f"MinerU upload failed: HTTP {resp.status} {body[:200]!r}")
    finally:
        conn.close()


def ingest_pdf_mineru(
    path: str | Path,
    *,
    api_key: str,
    workspace: str | Path,
    api_url: str = DEFAULT_API_URL,
    timeout: int = 600,
    poll_interval: int = 6,
) -> IngestResult:
    """Parse ``path`` via the MinerU cloud API and return an Evidence Pool. Raises on failure so the
    caller can fall back to the pdfplumber backend."""
    path = Path(path)
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    auth = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 1) request a presigned upload URL + batch id
    body = json.dumps(
        {
            "enable_formula": True,
            "enable_table": True,
            "language": os.environ.get("ASA_MINERU_LANG", "en"),
            "files": [{"name": path.name, "data_id": path.stem}],
        }
    ).encode()
    out = json.loads(_request(f"{api_url}/file-urls/batch", method="POST", headers=auth, data=body))
    data = out.get("data") or {}
    batch_id = data.get("batch_id")
    file_urls = data.get("file_urls") or []
    if not batch_id or not file_urls:
        raise RuntimeError(f"MinerU upload-url request failed: {out}")

    # 2) PUT the file bytes to the presigned URL (no auth / no content-type)
    _put_file(file_urls[0], path.read_bytes(), timeout=timeout)

    # 3) poll the batch until the file is done
    deadline = time.time() + timeout
    zip_url = None
    while time.time() < deadline:
        res = json.loads(
            _request(f"{api_url}/extract-results/batch/{batch_id}", method="GET", headers=auth)
        )
        results = (res.get("data") or {}).get("extract_result") or []
        state = results[0].get("state") if results else None
        if state == "done":
            zip_url = results[0].get("full_zip_url")
            break
        if state in ("failed", "error"):
            raise RuntimeError(f"MinerU extraction failed: {results[0].get('err_msg')}")
        time.sleep(poll_interval)
    if not zip_url:
        raise TimeoutError("MinerU extraction timed out")

    # 4) download + unzip, locate content_list.json
    out_dir = workspace / f"mineru_{batch_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "result.zip"
    zip_path.write_bytes(_request(zip_url, method="GET", headers={}, timeout=timeout))
    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
    content_list = next(iter(out_dir.rglob("*_content_list.json")), None) or next(
        iter(out_dir.rglob("content_list.json")), None
    )
    if content_list is None:
        raise RuntimeError("MinerU result missing content_list.json")
    blocks = json.loads(content_list.read_text(encoding="utf-8"))
    return parse_mineru_content_list(blocks, content_list.parent, path.name, workspace, path.stem)
