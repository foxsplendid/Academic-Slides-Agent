## ADDED Requirements

### Requirement: Redundancy and layout findings
The critic SHALL flag a `title`/`section` divider that carries content blocks as a repair-routable
finding (naming the slide for in-place relayout), and SHALL flag near-duplicate content-slide titles as
a non-repair-routable finding (so the human, not the in-place repair loop, resolves the redundancy).

#### Scenario: Divider with content is repair-routable
- **WHEN** a `section` slide carries a bullet block
- **THEN** the finding names the slide so the repair loop can relayout it

#### Scenario: Duplicate-title finding is human-facing
- **WHEN** two content slides have near-duplicate titles
- **THEN** the finding names both slides but is not phrased to trigger the in-place repair loop
