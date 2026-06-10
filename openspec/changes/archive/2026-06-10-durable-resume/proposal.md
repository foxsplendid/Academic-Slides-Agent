## Why

A user's run died with "连接中断" and the job was unrecoverable: SSE silence during long LLM calls let
the connection idle out, generation was COUPLED to the connection (a drop aborted the run mid-graph),
checkpoints lived in memory (a restart lost everything), generation exceptions were silent connection
drops, and repair failures hard-killed whole runs.

## What Changes

- **Detached execution**: each run executes on a background thread writing to a replayable per-job
  event log; the SSE endpoint *tails* it. Client disconnects never abort generation; reconnects replay
  the log; idle periods emit keepalive comments (defeats idle timeouts).
- **Durable checkpoints**: `durable_checkpointer` (SqliteSaver + our slide_ir serde) wired by the
  server; initial job states persisted to disk — jobs survive server restarts.
- **Resume semantics in the stream endpoint**: live attach → awaiting-approval replay → stranded-
  mid-run checkpoint resume (`stream(None)`) → done replay → fresh start from persisted state.
  Status gains `running` and `interrupted` (resumable).
- **Errors surfaced**: generation exceptions emit an `error` SSE event with the real message.
- **Repair hardening**: `_REPAIR_SYSTEM` now enumerates the legal block vocabulary (models invented
  a "column" container); table `title`→`caption` normalization pre-validation; a repair that exhausts
  retries keeps the original slide (fail open to the Hard-Stop) instead of killing the run.
- **Frontend**: shared `followJob`; EventSource auto-reconnect tolerated (server replays) with a
  give-up message after repeated failures; sidebar opens running/interrupted/awaiting jobs (attach /
  resume / approve).

## Capabilities

### Modified Capabilities
- `api`: detached runs, attach/resume stream, error events, persisted states, new statuses.
- `orchestration`: durable sqlite checkpointer helper.
- `outline-agent`: repair vocabulary + normalization + fail-open repair.
- `web-ui`: reconnect UX + resumable history entries.

## Impact

Verified end-to-end on the live server: errored job resumed from its checkpoint (plan not re-run),
reached the Hard-Stop, backend KILLED, restarted, status persisted as awaiting_approval, approved
across the restart, downloaded. 4 new tests incl. the cross-restart approve. New dep:
langgraph-checkpoint-sqlite (MIT).
