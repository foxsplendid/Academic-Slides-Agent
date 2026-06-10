## 1. Detached + durable
- [x] 1.1 _JobRun event log + tail + keepalives; runs detached from connections
- [x] 1.2 SqliteSaver checkpointer + persisted initial states; statuses running/interrupted

## 2. Resume + robustness
- [x] 2.1 Stream attach/replay/checkpoint-resume/fresh-start ladder; error events
- [x] 2.2 Repair vocabulary + table title normalization + fail-open repair

## 3. Frontend + verification
- [x] 3.1 followJob shared; auto-reconnect; sidebar resume entries
- [x] 3.2 Tests (cross-restart approve, replay, error event); live kill-restart-approve drill
