"""Render a Deck to human-readable Markdown — a per-run artifact for comparing agent modes."""

from __future__ import annotations

from slide_ir import Deck


def deck_to_markdown(deck: Deck) -> str:
    lines: list[str] = [f"# {deck.deck_id}", ""]
    for i, s in enumerate(deck.slides, 1):
        lines.append(f"## {i}. {s.title}  `[{s.layout_type.value}]`")
        for b in s.blocks:
            if b.type == "bullets":
                lines.extend(f"- {item}" for item in b.items)
            elif b.type == "figure":
                lines.append(f"- _[figure: {b.asset_id}]_ {b.caption or ''}".rstrip())
            elif b.type == "chart":
                lines.append(f"- _[chart: {b.chart_type}]_ {b.title or ''} categories={b.categories}".rstrip())
            elif b.type == "table":
                lines.append(f"- _[table]_ columns={b.columns} ({len(b.rows)} rows)")
            elif b.type == "formula":
                lines.append(f"- _[formula]_ `{b.latex}`")
            elif b.type == "diagram":
                names = ", ".join(n.label for n in b.nodes)
                lines.append(f"- _[diagram: {b.diagram_type}]_ {b.title or ''} nodes=({names})".rstrip())
        if s.speaker_notes:
            lines.append(f"> 讲稿: {s.speaker_notes}")
        lines.append("")
    return "\n".join(lines)
