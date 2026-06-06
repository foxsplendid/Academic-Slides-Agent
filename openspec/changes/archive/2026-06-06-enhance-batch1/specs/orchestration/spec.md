## ADDED Requirements

### Requirement: Resume-safe checkpoint serialization
The default graph checkpointer SHALL register the project's `slide_ir` types with the serializer so
resuming a checkpoint neither emits the unregistered-type warning nor is blocked by future strict
msgpack handling.

#### Scenario: Resume produces no unregistered-type warning
- **WHEN** a graph is run to the Hard-Stop and then resumed
- **THEN** deserializing the checkpoint produces no "Deserializing unregistered type"/"Blocked" output
  and the run still compiles
