# Chronology Splice

## Examiner's note

A disputed record often proves only that one event preceded another. It rarely proves a perfect timeline. This contract preserves that distinction.

The examiner names the events and supplies independently hosted records. The auditor invokes consensus, which returns attributed precedence edges and explicit conflicts. Deterministic code builds a layered partial order. A cycle or a sourced contradiction produces `CONFLICT`; only a conflict-free reconstruction can be filed.

## Invariants

- Every edge cites at least one source index.
- Source hosts cannot repeat inside a docket.
- Consensus is rerun by validators over the fetched material.
- Topological layers are calculated outside the model.
- Filing is examiner-only and replay-safe.

## Reproduce

```text
python -m pytest -q
genvm-lint lint contracts/contract.py
```
