#!/usr/bin/env python3
"""License hygiene gate (SPEC §2): fail the build on any GPL/AGPL dependency.

This project is Apache-2.0 and forbids GPL/AGPL of *any* kind so it can stay
open-core (see docs/SPEC.md §2). LGPL is allowed but must stay isolated behind a
boundary (e.g. the optional ``svglib`` raster fallback), so it is *not* flagged
here. A few distributions are banned by name regardless of how their packaged
metadata reads:

  - PyMuPDF / fitz (AGPL)   -> use pypdfium2 / pdfplumber instead
  - marker-pdf / marker (GPL)
  - PPTist (AGPL) is a JS project, never a Python dist; listed for completeness.

The scan reads the *installed* environment via ``importlib.metadata``, so it
also covers transitive dependencies. Dry-run locally against your dev venv:

    python scripts/license_scan.py
"""

from __future__ import annotations

import re
import sys
from importlib import metadata

# Distributions banned by name (normalized, case-insensitive), independent of
# whatever their packaged metadata claims.
BANNED_NAMES = {"pymupdf", "pymupdfb", "fitz", "pymupdf-fonts", "marker-pdf", "marker", "pptist"}

# Forbidden license families: GPL and AGPL, in acronym or full-name form. The
# negative lookbehind plus the LGPL mask below keep "LGPL" / "Lesser General
# Public License" from matching, since LGPL is allowed.
FORBIDDEN = re.compile(r"(?<![a-z])a?gpl|affero|gnu general public", re.IGNORECASE)
LGPL = re.compile(r"lgpl|lesser general public", re.IGNORECASE)


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _structured_license_ids(dist: metadata.Distribution) -> list[str]:
    """Authoritative, machine-readable license signals: the SPDX
    ``License-Expression`` and the Trove ``License ::`` classifiers."""
    md = dist.metadata
    ids: list[str] = []
    expr = md.get("License-Expression")
    if expr and expr.strip().upper() != "UNKNOWN":
        ids.append(expr)
    for classifier in md.get_all("Classifier") or []:
        if classifier.startswith("License ::"):
            ids.append(classifier)
    return ids


def _freeform_license_id(dist: metadata.Distribution) -> str | None:
    """The free-text ``License`` field, trusted only when it reads as a short
    *identifier* (e.g. "AGPL-3.0-or-later"), never a full agreement body.

    Permissive packages dump entire license texts into this field, and some —
    like matplotlib — concatenate the licenses of their *bundled* third-party
    components (matplotlib 3.11's 64 KB ``License`` field includes FreeType's
    "FTL OR GPL-2.0-or-later" notice). Substring-scanning that body flags a
    BSD/PSF package as GPL. Copyleft dists that declare a real classifier or SPDX
    expression are still caught by :func:`_structured_license_ids`; dists whose
    metadata lies outright are caught by ``BANNED_NAMES``.
    """
    val = dist.metadata.get("License")
    if not val:
        return None
    val = val.strip()
    if not val or val.upper() == "UNKNOWN" or "\n" in val or len(val) > 100:
        return None
    return val


def _forbidden_reason(dist: metadata.Distribution) -> str | None:
    candidates = _structured_license_ids(dist)
    freeform = _freeform_license_id(dist)
    if freeform:
        candidates.append(freeform)
    for text in candidates:
        # Mask LGPL tokens first so the GPL pattern can't catch the substring.
        masked = LGPL.sub("", text)
        if FORBIDDEN.search(masked):
            return text
    return None


def main() -> int:
    violations: list[tuple[str, str, str]] = []  # (name, version, reason)
    seen: set[str] = set()
    for dist in metadata.distributions():
        name = dist.metadata.get("Name") or "<unknown>"
        norm = _normalize(name)
        if norm in seen:  # editable installs can surface a dist twice
            continue
        seen.add(norm)
        version = dist.version
        if norm in BANNED_NAMES:
            violations.append((name, version, "banned by name (GPL/AGPL)"))
            continue
        reason = _forbidden_reason(dist)
        if reason:
            violations.append((name, version, f"license: {reason.strip()}"))

    print(f"license-scan: checked {len(seen)} installed distributions")
    if violations:
        print("\nFORBIDDEN GPL/AGPL dependencies found:")
        for name, version, reason in sorted(violations):
            print(f"  - {name} {version}  ->  {reason}")
        print("\nSPEC section 2 forbids GPL/AGPL of any kind. Replace these dependencies.")
        return 1
    print("license-scan: OK - no GPL/AGPL dependencies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
