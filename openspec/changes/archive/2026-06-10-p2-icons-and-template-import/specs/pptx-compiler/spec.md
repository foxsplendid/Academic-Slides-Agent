## ADDED Requirements

### Requirement: Whitelisted icon rendering
The compiler SHALL render card icons through an injectable resolver and SHALL skip unknown or
unresolvable icons silently (a hallucinated icon never breaks a render).

#### Scenario: Unknown icon skips
- **WHEN** a callout names an icon outside the whitelist
- **THEN** the slide renders without an icon and without error

### Requirement: Imported template styles
A custom style extracted from a user .pptx SHALL be registerable and resolvable by name, and
compiling with it SHALL inherit the template's master (theme, layouts, slide size) natively.

#### Scenario: Master inherited
- **WHEN** a deck compiles with an imported template style
- **THEN** the output presentation carries the template's slide size and theme
