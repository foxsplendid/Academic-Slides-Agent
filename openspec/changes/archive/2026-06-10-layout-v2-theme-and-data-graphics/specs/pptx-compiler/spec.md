## ADDED Requirements

### Requirement: Multi-region layout templates
The compiler SHALL render each layout as a multi-region composition when the slide's block
composition matches the layout's template (figure-led layouts place the figure beside the text
column; `two_content` splits 50/50; `figure_grid` arranges 2-4 figures in a grid; `big_figure`
dominates the slide), and SHALL degrade to the weighted vertical stack when the composition does not
match, never failing the render.

#### Scenario: figure_caption renders side by side
- **WHEN** a `figure_caption` slide carries one figure and one bullets block
- **THEN** the figure renders in a right column beside (not below) the text

#### Scenario: Unmatched composition degrades gracefully
- **WHEN** a slide's blocks do not fit its layout's template
- **THEN** the blocks render in the vertical-stack fallback

### Requirement: Token-styled data graphics
The compiler SHALL style native charts (series palette, axis/legend typography, data labels on small
single-series charts, bottom legend) and tables (header-row fill with white header text, zebra
banding, highlighted cells in the emphasis color) from the StyleProfile design tokens.

#### Scenario: Chart series use the palette
- **WHEN** a bar chart compiles with the default profile
- **THEN** its first series is filled with the profile's first palette color

#### Scenario: Table highlight cells are emphasized
- **WHEN** a table block marks a cell in `highlight.cells`
- **THEN** that cell's text renders bold in the emphasis color

### Requirement: Deck chrome
The compiler SHALL render theme chrome from profile tokens: an accent rule under slide titles and a
page number on non-cover slides, with the cover carrying no page number.

#### Scenario: Content slide chrome
- **WHEN** a content slide compiles with the default profile
- **THEN** it carries an accent-colored rule and its page number
