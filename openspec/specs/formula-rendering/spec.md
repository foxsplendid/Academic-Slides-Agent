# formula-rendering Specification

## Purpose
TBD - created by archiving change add-formula-rendering. Update Purpose after archive.
## Requirements
### Requirement: Render LaTeX math to an image
The renderer SHALL convert a parseable LaTeX math expression into an image file on disk and
return its path.

#### Scenario: Parseable expression yields an image file
- **WHEN** `to_image("E=mc^2")` is called
- **THEN** it returns a path to an existing image file

### Requirement: Graceful fallback on unparseable input
The renderer SHALL return `None` when the expression cannot be parsed, so the compiler falls
back to editable text instead of failing.

#### Scenario: Unsupported expression returns None
- **WHEN** `to_image` is called with an expression mathtext cannot parse (e.g. mhchem `\ce{...}`)
- **THEN** it returns `None`

### Requirement: Conforms to the FormulaRenderer interface
The renderer SHALL expose `to_image(latex: str) -> Path | None` so it is usable wherever the
compiler expects a `FormulaRenderer`.

#### Scenario: Compiler embeds a rendered formula as a picture
- **WHEN** a deck with a FormulaBlock is compiled using this renderer
- **THEN** the rendered slide contains a picture shape rather than the raw LaTeX text

### Requirement: Caching
The renderer SHALL cache results so the same expression (same dpi and color) is rendered once
and reused.

#### Scenario: Repeated expression reuses the cached image
- **WHEN** `to_image` is called twice with the same expression
- **THEN** both calls return the same path and the image is not re-rendered

### Requirement: Common academic math is supported
The renderer SHALL render common academic notation: isotope super/subscripts, mineral
subscripts, fractions, Greek letters, sums, and roots.

#### Scenario: Representative academic expressions render
- **WHEN** `to_image` is called with isotope, subscript, fraction, and Greek expressions
- **THEN** each returns a path to an existing image file

### Requirement: High-fidelity formula tier
The formula renderer SHALL provide a tiered `to_image(latex)` that renders advanced constructs
(chemistry/mhchem, matrices, alignment) via a MathJax Node sidecar when available, and simple math via
matplotlib, falling back to the other backend, and to text only when neither can render.

#### Scenario: Advanced formula routes to MathJax when available
- **WHEN** the auto-renderer is given a `\ce{…}` chemistry formula and the MathJax tier is available
- **THEN** it renders via the MathJax backend (not the matplotlib one)

#### Scenario: Simple math uses matplotlib
- **WHEN** the auto-renderer is given a simple expression like `x^2`
- **THEN** it renders via the matplotlib backend

### Requirement: Optional native-editable OMML for the simple subset
The renderer SHALL optionally (opt-in, default off) convert a simple LaTeX formula to native OMML using
a clean-room converter that introduces no proprietary stylesheet, and SHALL return nothing for any
formula outside the supported subset so the caller falls back to the image tier. When OMML is produced
the compiler SHALL embed it as an editable equation wrapped with a text fallback, never emitting a
blank or corrupt slide.

#### Scenario: A simple formula becomes an editable equation
- **WHEN** native OMML is enabled and a supported formula is compiled
- **THEN** the slide contains an `m:oMath` equation with a text fallback that survives save and reopen

#### Scenario: An unsupported formula falls back to image
- **WHEN** a formula outside the supported subset is compiled
- **THEN** no OMML is produced and the image renderer is used

### Requirement: Icon sidecar
The Node sidecar SHALL render whitelisted Tabler icons to tinted PNGs (cached) and report
unavailability cleanly so callers fail open.

#### Scenario: Sidecar absent
- **WHEN** Node or the icon corpus is unavailable
- **THEN** the default icon renderer is None and decks render without icons

