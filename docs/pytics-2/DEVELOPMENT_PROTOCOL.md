# Development protocol

Status: **Accepted** ([DEC-028](DECISIONS.md#dec-028)).

This protocol applies to every future Pytics 2.0 implementation slice. It is a project rule, not a suggestion.

## Slice procedure

1. Identify the relevant specification requirement (`REQ-###`).
2. Define scope.
3. Define acceptance criteria.
4. Implement only that slice.
5. Add or update tests.
6. Run the relevant tests.
7. Run broader regression tests when appropriate.
8. Verify behavior against the specification.
9. Update [PROGRESS.md](PROGRESS.md).
10. Record any architectural decision or change in [DECISIONS.md](DECISIONS.md).
11. Report exactly what changed.
12. Stop before starting the next unapproved slice.

## Constraints

- No silent scope expansion.
- No unregistered architectural changes.
- No "while I was here" refactors unless explicitly approved.
- If implementation reveals that an accepted specification is technically problematic, stop and report the issue. Do not silently change the product.
- Do not choose dependencies, freeze public APIs, or promote an `OPEN-###` item to **Accepted** inside an implementation slice. Those require their own decision.
- The end state is replacement of the implementation inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). Do not casually rewrite 1.1.5 while implementing 2.0. Build in place, and keep each 1.1.5 component until its replacement is specified, implemented, tested, and verified ([DEC-063](DECISIONS.md#dec-063)). Do not add a permanent second package.

## What "approved" means

A slice is approved only when its scope and acceptance criteria are stated against existing requirement IDs, and that approval is recorded before coding. The existence of a requirement in the specification is not approval to implement it.

No implementation slice was approved at the time this protocol was recorded. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 were approved later, on 2026-10-03. Their scope and verification are in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [PROGRESS.md](PROGRESS.md). This protocol still applies to every later slice. TSK-010 does not approve a later slice. The semantic-foundation consolidation recorded the same day, DEC-064 through DEC-076, is documentation only. It does not approve a later slice.
