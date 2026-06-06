## ADDED Requirements

### Requirement: High-fidelity formula tier
The formula renderer SHALL provide a tiered `to_image(latex)` that renders advanced constructs
(chemistry/mhchem, matrices, alignment) via a MathJax Node sidecar when available, and simple math via
matplotlib, falling back to the other backend, and to text only when neither can render.

#### Scenario: Advanced formula routes to MathJax when available
- **WHEN** the auto-renderer is given a `\ce{…}` chemistry formula and the MathJax tier is available
- **THEN** it renders via the MathJax backend (not the matplotlib one)

#### Scenario: Simple math uses matplotlib
- **WHEN** the auto-renderer is given a simple expression like `x^2`
- **THEN** it renders via the matplotlib backend
