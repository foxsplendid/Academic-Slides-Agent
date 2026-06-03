## ADDED Requirements

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
