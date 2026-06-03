## ADDED Requirements

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
