## ADDED Requirements

### Requirement: Bullet auto-fit
The compiler SHALL estimate whether bullet text fits its region and SHALL shrink the font size (down to
a floor) so dense text does not overflow the slide ("measure, then place").

#### Scenario: Dense bullets shrink
- **WHEN** a slide's bullet region must hold much more text than another's
- **THEN** its rendered font size is smaller (but not below the floor)
