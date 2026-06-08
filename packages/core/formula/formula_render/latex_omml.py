"""Clean-room LaTeX → OMML (Office Math) converter for the common subset.

Produces native, *editable* PowerPoint equations for simple math (identifiers, sub/superscripts,
fractions, roots, Greek letters, common operators). This is a from-scratch implementation — it does
NOT use Microsoft's proprietary ``MML2OMML.XSL`` — so it is Apache-clean.

Coverage is deliberately conservative: anything it cannot convert with confidence (chemistry ``\\ce``,
matrices/environments, integrals/sums with limits, ``\\left``/``\\right``, unknown commands) makes
`latex_to_omml` return ``None`` so the caller falls back to the image renderer. It never emits partial
or malformed OMML.
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# Constructs we do not support — bail out early so we never emit half-converted OMML.
_ADVANCED = ("\\begin", "\\end", "\\ce", "\\int", "\\sum", "\\prod", "\\oint", "\\iint",
             "\\left", "\\right", "\\matrix", "\\binom", "\\over", "\\\\", "&", "\\lim_")

_SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ",
    "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ",
    "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "times": "×", "cdot": "·", "pm": "±", "mp": "∓", "div": "÷", "ast": "∗", "star": "⋆",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠", "approx": "≈",
    "sim": "∼", "simeq": "≃", "equiv": "≡", "propto": "∝", "rightarrow": "→", "to": "→",
    "leftarrow": "←", "Rightarrow": "⇒", "Leftarrow": "⇐", "infty": "∞", "partial": "∂",
    "nabla": "∇", "circ": "∘", "prime": "′", "ll": "≪", "gg": "≫", "subset": "⊂",
    "supset": "⊃", "subseteq": "⊆", "in": "∈", "notin": "∉", "cup": "∪", "cap": "∩",
    "angle": "∠", "perp": "⊥", "cdots": "⋯", "ldots": "…", "dot": "˙",
}
_FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "lim", "max", "min", "det", "dim", "arg"}
_SPACES = {"\\,", "\\;", "\\:", "\\ ", "\\quad", "\\qquad"}

_TOKEN = re.compile(r"\\[a-zA-Z]+|\\[,;: ]|[{}^_]|[^\s]")


class _Err(Exception):
    pass


def _tokenize(s: str) -> list[str]:
    return [m.group(0) for m in _TOKEN.finditer(s)]


class _Parser:
    def __init__(self, toks: list[str]) -> None:
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expr(self, stop=None) -> str:
        parts = []
        while True:
            t = self.peek()
            if t is None or t == stop:
                break
            if t in ("}", "_", "^"):  # stray script/close at this level
                raise _Err()
            parts.append(self.element())
        return "".join(parts)

    def element(self) -> str:
        base = self.atom()
        sub = sup = None
        for _ in range(2):
            t = self.peek()
            if t == "_" and sub is None:
                self.next()
                sub = self.atom()
            elif t == "^" and sup is None:
                self.next()
                sup = self.atom()
            else:
                break
        if sub is not None and sup is not None:
            return f"<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>"
        if sub is not None:
            return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"
        if sup is not None:
            return f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"
        return base

    def atom(self) -> str:
        t = self.peek()
        if t is None:
            raise _Err()
        if t == "{":
            self.next()
            inner = self.expr(stop="}")
            if self.peek() != "}":
                raise _Err()
            self.next()
            return inner or _run("")
        if t == "\\frac":
            self.next()
            return f"<m:f><m:num>{self.atom()}</m:num><m:den>{self.atom()}</m:den></m:f>"
        if t == "\\sqrt":
            self.next()
            return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{self.atom()}</m:e></m:rad>'
        if t.startswith("\\"):
            if t in _SPACES:
                self.next()
                return _run(" ")
            name = t[1:]
            if name in _SYMBOLS:
                self.next()
                return _run(_SYMBOLS[name])
            if name in _FUNCS:
                self.next()
                return _run(name, upright=True)
            raise _Err()  # unknown command -> fall back to image
        if t in ("}", "_", "^"):
            raise _Err()
        self.next()
        return _run(t)


def _run(text: str, *, upright: bool = False) -> str:
    body = f"<m:t>{escape(text)}</m:t>"
    if upright:
        return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr>{body}</m:r>'
    return f"<m:r>{body}</m:r>"


def latex_to_omml(latex: str) -> str | None:
    """Return an ``<m:oMath>`` string (math namespace declared), or ``None`` if unsupported."""
    if not latex or not latex.strip():
        return None
    if any(marker in latex for marker in _ADVANCED):
        return None
    try:
        parser = _Parser(_tokenize(latex.strip()))
        body = parser.expr()
        if parser.peek() is not None or not body:  # leftover tokens => incomplete parse
            return None
        return f'<m:oMath xmlns:m="{MATH_NS}">{body}</m:oMath>'
    except _Err:
        return None
    except Exception:
        return None
