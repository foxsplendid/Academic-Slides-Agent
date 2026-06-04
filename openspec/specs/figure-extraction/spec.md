# figure-extraction Specification

## Purpose
TBD - created by archiving change add-figure-extraction. Update Purpose after archive.
## Requirements
### Requirement: Caption-anchored figure rendering
Ingestion SHALL detect `Fig. N` / `Figure N` captions in a PDF, infer each figure's region from the
caption's horizontal band, and render that region to an image file using a permissively-licensed
engine (PDFium via pypdfium2 — never PyMuPDF). Each rendered figure SHALL become an `EvidenceAsset`
of kind `figure` whose `content_ref` points at the image and whose `locator` carries the caption and
page.

#### Scenario: A figure caption yields a rendered figure asset
- **WHEN** a PDF page containing a `Fig. 1` caption above a chart is ingested with a workspace
- **THEN** the result contains a `figure` asset whose `content_ref` is an existing non-empty image file
  and whose `locator` includes the caption text and page number

#### Scenario: No captions yields no figure assets
- **WHEN** a PDF has no figure captions
- **THEN** no `figure` assets are produced

