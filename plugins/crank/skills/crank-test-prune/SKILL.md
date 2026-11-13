---
name: crank-test-prune
description: Prune a test suite for utility — verdict every test KEEP, DELETE, REFACTOR, or MERGE so only behavior-pinning tests survive.
argument-hint: "[scope, default: the whole test tree]"
disable-model-invocation: true
---

# Test Prune

Read [TEST-PRUNE.md](TEST-PRUNE.md) and follow it, with the argument as its scope. The prune's rules, verdicts, and flow live in that file alone (per project decision: crank-execute and lite-execute dispatch the same prune from gate-held copies of it, so both plugins prune by one set of rules).

## References

### Subagents

This skill spawns verdict subagents at the **standard** tier — resolve it per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md): a loaded instruction file's preference first, its harness models only as the fallback.

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) defines the terms TEST-PRUNE.md's verdicts lean on.
