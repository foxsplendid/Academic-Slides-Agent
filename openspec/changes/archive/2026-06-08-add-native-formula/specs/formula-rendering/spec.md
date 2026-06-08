## ADDED Requirements

### Requirement: Optional native-editable OMML for the simple subset
The renderer SHALL optionally (opt-in, default off) convert a simple LaTeX formula to native OMML using
a clean-room converter that introduces no proprietary stylesheet, and SHALL return nothing for any
formula outside the supported subset so the caller falls back to the image tier. When OMML is produced
the compiler SHALL embed it as an editable equation wrapped with a text fallback, never emitting a
blank or corrupt slide.

#### Scenario: A simple formula becomes an editable equation
- **WHEN** native OMML is enabled and a supported formula is compiled
- **THEN** the slide contains an `m:oMath` equation with a text fallback that survives save and reopen

#### Scenario: An unsupported formula falls back to image
- **WHEN** a formula outside the supported subset is compiled
- **THEN** no OMML is produced and the image renderer is used
