## ADDED Requirements

### Requirement: Deterministic redundancy and layout normalization
The detailed builder SHALL drop near-duplicate skeleton slides before expansion (similarity on
normalized title+focus, keeping the first) and SHALL relayout any `title`/`section` divider that
carries content blocks to a content layout. The prompts SHALL instruct the planner not to produce two
slides on the same point and to use divider layouts only for content-free pages.

#### Scenario: Near-duplicate slides are removed before expansion
- **WHEN** the skeleton yields two near-duplicate plans
- **THEN** only one is kept and the dropped plan is never expanded

#### Scenario: A divider carrying content is relayout
- **WHEN** an expanded `section` slide contains content blocks
- **THEN** its layout becomes `bullet_evidence`
