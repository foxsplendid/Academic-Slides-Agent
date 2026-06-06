## ADDED Requirements

### Requirement: Selectable style profile
The compiler SHALL accept a `StyleProfile` that parameterizes fonts, type sizes, emphasis color, and
diagram colors, defaulting to an `academic` profile so existing output is unchanged; selecting a
different profile SHALL change the rendered look.

#### Scenario: A different profile changes the rendered fonts
- **WHEN** the same deck is compiled with two different style profiles
- **THEN** the rendered run fonts (or colors) differ between the two outputs

#### Scenario: Default profile is unchanged
- **WHEN** a deck is compiled without specifying a style
- **THEN** it renders with the `academic` profile (the established tokens)
