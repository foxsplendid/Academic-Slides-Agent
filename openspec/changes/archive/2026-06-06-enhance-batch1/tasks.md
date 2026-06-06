## 1. Critic relax (E1)

- [x] 1.1 `two_column_table` satisfied by table OR chart OR diagram
- [x] 1.2 Test: a chart on a `two_column_table` slide is not flagged

## 2. msgpack allowlist (E2)

- [x] 2.1 Default checkpointer uses `JsonPlusSerializer(allowed_msgpack_modules=<all slide_ir.models types>)`
- [x] 2.2 Test: resume produces no msgpack "Deserializing/Blocked" output and still compiles

## 3. Interpretation required (E3)

- [x] 3.1 Expand prompt makes the final "→ …" interpretation bullet mandatory

## 4. Verify

- [x] 4.1 Full suite green
