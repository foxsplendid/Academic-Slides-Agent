## ADDED Requirements

### Requirement: Native bullet, callout, and stat rendering
The compiler SHALL render bullets with real PowerPoint bullet formatting (per-level glyph and
hanging indent), callout blocks as tinted cards with an accent edge, and stat blocks as side-by-side
big-number cards styled by the profile.

#### Scenario: Nested bullets indent
- **WHEN** a bullets block contains a child item
- **THEN** the child paragraph carries a deeper left indent than its parent

#### Scenario: Stat cards render side by side
- **WHEN** a stat block has three items
- **THEN** three cards render at distinct horizontal positions
