## ADDED Requirements

### Requirement: Subtitle chrome and overflow margin
The compiler SHALL render cover/divider subtitles centered under the title, content subtitles as a
kicker line above the accent rule, a footer breadcrumb naming the current section on content slides,
and SHALL apply a bottom safety margin when fitting bullet text so it cannot spill into the region
below.

#### Scenario: Kicker and breadcrumb render
- **WHEN** a content slide with a subtitle follows a section divider
- **THEN** the kicker line and the section breadcrumb both render
