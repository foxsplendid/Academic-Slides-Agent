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

### Requirement: Widescreen, CJK-ready styling
A freshly compiled deck (no template) SHALL use a 16:9 slide size and apply CJK-aware fonts so Chinese
text renders correctly, with distinct title/body/caption sizes.

#### Scenario: Fresh deck is 16:9
- **WHEN** a deck is compiled without a template
- **THEN** the presentation's slide size has a 16:9 aspect ratio

### Requirement: Emphasis runs
The compiler SHALL render `**…**` spans in titles and bullet text as bold, red emphasis runs while
the surrounding text stays default.

#### Scenario: Marked span becomes a red bold run
- **WHEN** a bullet item contains a `**…**` span
- **THEN** the rendered paragraph contains a bold run colored red for that span

### Requirement: Figure asset resolution
The compiler SHALL accept an `asset_resolver` mapping a `figure` block's `asset_id` to an image file
path and embed that image natively; an unresolved `asset_id` SHALL fall back to the text placeholder.

#### Scenario: Resolved asset_id is embedded as a picture
- **WHEN** a deck has a `figure` block whose `asset_id` resolves to an existing image via the resolver
- **THEN** the compiled slide contains a picture shape for that image

### Requirement: Aspect-preserving figure layout
The compiler SHALL render a figure image fitted within its region preserving aspect ratio (no
distortion, no overflow) and centered, and SHALL allocate more of a slide's content area to a figure
block than to a text block.

#### Scenario: A figure is contained and centered
- **WHEN** a slide with a resolvable figure is compiled
- **THEN** the picture's width does not exceed the content width and its height does not exceed its
  allocated region, and it is horizontally centered

#### Scenario: A figure gets more room than bullets
- **WHEN** a slide has one figure block and one bullets block
- **THEN** the figure's region is taller than the bullets' region

### Requirement: Native chart rendering
The compiler SHALL render a `ChartBlock` as a native, editable PowerPoint chart (not an image),
mapping bar/line/pie to a category chart and scatter to an XY chart, tolerating a series/category
length mismatch.

#### Scenario: A chart block becomes a native chart
- **WHEN** a slide with a `chart` block is compiled
- **THEN** the slide contains a graphic-frame chart (an editable chart object)

### Requirement: Deterministic native diagram rendering
The compiler SHALL render a `DiagramBlock` by computing layout deterministically (no LLM coordinates)
and emitting native, editable PowerPoint shapes — rounded-rectangle nodes with text and connectors for
edges — for each supported `diagram_type`.

#### Scenario: A diagram becomes native shapes
- **WHEN** a slide with a `diagram` block of N nodes is compiled
- **THEN** the slide contains at least N native node shapes (and connectors for a flow's edges)

### Requirement: Bullet auto-fit
The compiler SHALL estimate whether bullet text fits its region and SHALL shrink the font size (down to
a floor) so dense text does not overflow the slide ("measure, then place").

#### Scenario: Dense bullets shrink
- **WHEN** a slide's bullet region must hold much more text than another's
- **THEN** its rendered font size is smaller (but not below the floor)

