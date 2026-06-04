## ADDED Requirements

### Requirement: Figure asset resolution
The compiler SHALL accept an `asset_resolver` mapping a `figure` block's `asset_id` to an image file
path and embed that image natively; an unresolved `asset_id` SHALL fall back to the text placeholder.

#### Scenario: Resolved asset_id is embedded as a picture
- **WHEN** a deck has a `figure` block whose `asset_id` resolves to an existing image via the resolver
- **THEN** the compiled slide contains a picture shape for that image
