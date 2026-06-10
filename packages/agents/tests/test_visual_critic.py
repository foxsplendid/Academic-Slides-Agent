"""VLM visual critic tests — offline via fake renderer + fake vision LLM.

Maps to openspec/changes/add-quality-loop/specs/critic/spec.md.
"""

from __future__ import annotations

import json

from slide_ir import BulletBlock, LayoutType, SlideIR

import asa_agents.visual_critic as vc


def _slides():
    return [
        SlideIR(slide_id="s1", layout_type=LayoutType.BULLET_EVIDENCE, title="A", blocks=[BulletBlock(items=["x"])]),
        SlideIR(slide_id="s2", layout_type=LayoutType.BULLET_EVIDENCE, title="B", blocks=[BulletBlock(items=["y"])]),
    ]


class _FakeVLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def complete_vision(self, prompt, *, images, system=None):
        self.calls += 1
        return self.payload


def test_findings_mapped_to_slide_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "render_pptx_images", lambda p, o: [tmp_path / "a.png", tmp_path / "b.png"])
    payload = json.dumps(
        [
            {"slide_index": 2, "defect": "slide_too_dense", "suggestion": "拆成两页"},
            {"slide_index": 1, "defect": "not_in_taxonomy", "suggestion": "x"},  # filtered out
            {"slide_index": 99, "defect": "text_overflow", "suggestion": "x"},  # out of range
        ]
    )
    findings = vc.visual_critique(_slides(), tmp_path / "d.pptx", _FakeVLM(payload), tmp_path)
    assert findings == ["slide 's2': visual slide_too_dense — 拆成两页"]  # repair-routable, taxonomy-filtered


def test_skips_when_no_renderer(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "render_pptx_images", lambda p, o: [])
    fake = _FakeVLM("[]")
    assert vc.visual_critique(_slides(), tmp_path / "d.pptx", fake, tmp_path) == []
    assert fake.calls == 0  # never called the model


def test_garbage_vlm_output_fails_open(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "render_pptx_images", lambda p, o: [tmp_path / "a.png"])
    assert vc.visual_critique(_slides(), tmp_path / "d.pptx", _FakeVLM("not json at all"), tmp_path) == []
