# pptx-compiler Specification

## Purpose
TBD - created by archiving change add-pptx-compiler. Update Purpose after archive.
## Requirements
### Requirement: Compile a deck to a native PPTX
The compiler SHALL render a `Deck` to a `.pptx` file containing one slide per `SlideIR`, using
native PowerPoint objects (not page images). The output SHALL be a valid PPTX readable by
python-pptx.

#### Scenario: One slide per Slide-IR
- **WHEN** a Deck with N slides is compiled
- **THEN** the output presentation has exactly N slides

#### Scenario: Output is a valid PPTX
- **WHEN** the output file is reopened with python-pptx
- **THEN** it loads without error

### Requirement: Native editable tables
A `TableBlock` SHALL be rendered as a native PowerPoint table (a table graphic frame), never as
an image, with one header row from `columns` and one row per data row.

#### Scenario: TableBlock becomes a native table
- **WHEN** a slide with a TableBlock of C columns and R data rows is compiled
- **THEN** the rendered slide contains a native table shape with C columns and R+1 rows

### Requirement: Native bullet text
A `BulletBlock` SHALL be rendered as editable text, one paragraph per item, inside a text frame.

#### Scenario: BulletBlock items become paragraphs
- **WHEN** a slide with a BulletBlock of K items is compiled
- **THEN** the rendered slide contains a text frame whose text includes all K items

### Requirement: Formula rendering is pluggable with a text fallback
The compiler SHALL render a `FormulaBlock` via an injectable formula renderer. When no renderer
produces an image, the compiler SHALL fall back to placing the LaTeX as editable text, so the
compiler never hard-fails on formulas before the image pipeline exists.

#### Scenario: Fallback to LaTeX text when no image renderer
- **WHEN** a FormulaBlock is compiled with the null renderer
- **THEN** the rendered slide contains the LaTeX string as text

#### Scenario: Image embedded when a renderer provides one
- **WHEN** a FormulaBlock is compiled with a renderer that returns an image path
- **THEN** the rendered slide contains a picture shape

### Requirement: Template theme inheritance
When a `.pptx` template is supplied, the compiler SHALL use it as the base presentation so the
output inherits the template's theme, fonts, and slide size.

#### Scenario: Output inherits template slide size
- **WHEN** a deck is compiled against a template with a known slide size
- **THEN** the output presentation reports that same slide size

### Requirement: Deterministic structure
Compiling the same deck twice SHALL produce the same slide count and the same per-slide shape
structure.

#### Scenario: Stable structure across runs
- **WHEN** the same deck is compiled twice
- **THEN** both outputs have identical slide counts and identical per-slide shape-type sequences

