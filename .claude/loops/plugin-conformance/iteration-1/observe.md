# Observe

Record each cycle:

- **Which phase this cycle was in**, and which rule or plugin it touched.
- **The rule count**: total rules, how many pass, how many fail, how many are still unchecked. These four numbers exist nowhere else — the artifact is rewritten in place and carries no history — so a cycle that omits them makes the next cycle blind.
- **What moved** since the previous cycle, and what moved it.
- **Every rule added**, with its source: specification, or convention plus the evidence for it.
- Any assumption that changed.

## Goal check

The goal is met when **every rule has been checked against the files and every rule either passes or has been fixed.** No rule may sit unchecked, and no failure may sit unfixed without being recorded as a deliberate exception with a reason.

- **Met** — report the final rule table, anything left as a deliberate exception, and what changed in APEX. The loop ends.
- **Not met** — report and write the next action: the single next rule to extract, audit, or fix.
- **Flat** — a cycle that adds no rule, checks no rule and fixes no rule means the loop has stalled. Report what it was trying to do and stop. Do not run another variant.

## What must not happen

**A rule that cannot be failed is not a rule.** If a candidate rule cannot be checked by pointing at a file and saying yes or no, it is an opinion. Either sharpen it until it names a file, or drop it and record that it was dropped.

**Preference is not evidence.** A convention-derived rule carries its source — an Anthropic example, or a count of real repositories doing the same thing. A rule whose only backing is that it seems tidier does not go in the list.

**Nothing in APEX changes before phase 3 is complete.** The audit is a measurement, and measuring after fixing destroys the reading.

**Path changes keep `marketplace.json` in lockstep.** The three plugins are live and installed at `ref: master`. A moved plugin whose manifest still points at the old path breaks every consumer on their next update.
