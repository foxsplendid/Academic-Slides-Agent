## ADDED Requirements

### Requirement: Title color token
The `StyleProfile` SHALL carry an optional title color applied to slide/section/cover titles; when unset
the title uses the theme default, so the default profile is unchanged.

#### Scenario: A profile's title color is applied
- **WHEN** a deck is compiled with a profile whose `title_rgb` is set
- **THEN** the rendered slide-title runs use that color
