"""Clean-room LaTeX -> OMML converter tests.

Maps to openspec/changes/add-native-formula/specs/formula-rendering/spec.md.
"""

from __future__ import annotations

import pytest
from lxml import etree

from formula_render.latex_omml import MATH_NS, latex_to_omml

_M = f"{{{MATH_NS}}}"

SUPPORTED = [
    "x^2",
    "a_i",
    "x_i^2",
    r"\frac{a+b}{c}",
    r"\sqrt{x+1}",
    r"\alpha + \beta",
    "E = mc^2",
    "r = 0.938",
    r"\sigma^{2}_{n}",
    "H_2O",
    r"\Delta T \geq 0",
]

UNSUPPORTED = [
    r"\ce{H2O}",
    r"\begin{matrix}a&b\\c&d\end{matrix}",
    r"\int_0^1 x dx",
    r"\sum_{i=1}^n i",
    r"\unknowncmd{x}",
    "{",
    "x^",
    "",
]


@pytest.mark.parametrize("latex", SUPPORTED)
def test_supported_produces_wellformed_omml(latex):
    omml = latex_to_omml(latex)
    assert omml is not None
    root = etree.fromstring(omml)  # well-formed + namespaced
    assert root.tag == f"{_M}oMath"


@pytest.mark.parametrize("latex", UNSUPPORTED)
def test_unsupported_returns_none(latex):
    assert latex_to_omml(latex) is None  # conservative -> caller falls back to image


def test_fraction_structure():
    root = etree.fromstring(latex_to_omml(r"\frac{1}{2}"))
    frac = root.find(f"{_M}f")
    assert frac is not None
    assert frac.find(f"{_M}num") is not None and frac.find(f"{_M}den") is not None


def test_subsup_structure():
    root = etree.fromstring(latex_to_omml("x_i^2"))
    assert root.find(f"{_M}sSubSup") is not None


def test_greek_is_unicode():
    assert "α" in latex_to_omml(r"\alpha")
