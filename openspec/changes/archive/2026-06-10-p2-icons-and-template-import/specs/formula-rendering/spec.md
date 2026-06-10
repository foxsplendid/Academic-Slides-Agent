## ADDED Requirements

### Requirement: Icon sidecar
The Node sidecar SHALL render whitelisted Tabler icons to tinted PNGs (cached) and report
unavailability cleanly so callers fail open.

#### Scenario: Sidecar absent
- **WHEN** Node or the icon corpus is unavailable
- **THEN** the default icon renderer is None and decks render without icons
