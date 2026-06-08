## ADDED Requirements

### Requirement: Optional composite-figure splitting
When enabled (`ASA_SPLIT_FIGURES`), ingestion SHALL detect full-span near-white gutters in a figure and
emit each sub-panel as a sibling `figure` asset (keeping the whole figure), using a deterministic,
license-clean (Pillow-only) method that conservatively avoids splitting single-panel images. When
disabled it SHALL emit only the whole figure.

#### Scenario: A multi-panel figure splits into panels
- **WHEN** a 2×2-panel figure is ingested with `ASA_SPLIT_FIGURES` enabled
- **THEN** the result contains the whole figure plus four panel figure assets

#### Scenario: A single-panel figure is not split
- **WHEN** a single-panel image is processed
- **THEN** no panel assets are produced
