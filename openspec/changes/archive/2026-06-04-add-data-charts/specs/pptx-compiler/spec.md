## ADDED Requirements

### Requirement: Native chart rendering
The compiler SHALL render a `ChartBlock` as a native, editable PowerPoint chart (not an image),
mapping bar/line/pie to a category chart and scatter to an XY chart, tolerating a series/category
length mismatch.

#### Scenario: A chart block becomes a native chart
- **WHEN** a slide with a `chart` block is compiled
- **THEN** the slide contains a graphic-frame chart (an editable chart object)
