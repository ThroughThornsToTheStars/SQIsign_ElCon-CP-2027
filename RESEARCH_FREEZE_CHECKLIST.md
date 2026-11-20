# Research freeze checklist

The object of review is the reference code at 6d55a8fd75adc47abc8a2b266a3adfd8f4d8a20c. The exact data-generating revisions for the three experiments are listed separately in [the validation report](FINAL_RESEARCH_VALIDATION.md). A documentation commit or subsequent integration commit has a separate identity.

## Completion criteria

- [x] Confirmed upstream, v3 and review heads. Reviewed the difference from upstream, including symmetric call sites, entropy handling and public API error paths. The starting clone was clean.
- [x] Identified the independent work in [PR 1](https://github.com/handofgod666/SQIsign_ElCon-CP-2027/pull/1). A trial merge-tree with its recorded head preserves its five blobs. Its public transcript reproduces.
- [x] Checked the two substitutions individually and together on all three parameter sets. Matched the modified public hash and streams against a separate library, and the typed scalar against an independent transcript construction.
- [x] Exercised release interoperability, malformed signatures, a changed message, empty inputs, entropy failure and stream boundaries. The original baseline corpus covers all three parameter sets.
- [x] Verified exact-implementation GitHub Actions logs and artifacts, including a working positive leak control in every sanitizer job. Local execution and broader arithmetic-suite coverage are recorded separately in the validation report.
- [x] Traced the original host, revisions, build metadata and sampling units. Independently recomputed the three primary contrasts from raw data. Reproduced controlled tables, plot inputs and memory summaries. Retained the three series separately.
- [x] Checked the relevant Russian hash, HMAC, generator and key-derivation documents. Identified what the research construction adds. Recorded the applicable SQIsign proof assumptions and the measured backend's secret-dependent table accesses.
- [x] Checked Hypericum's selected encodings against its specification and reference headers, its per-key budgets and the authors' published latency conditions. The literature timings belong to the earlier prototype.
- [x] Checked the registered abstract against the available scope. Existing evidence covers functional integration, compatibility, selected parameter sets, time and process-level memory. The size example in the comparison illustrates transmitted bytes under its stated assumptions.

## Decision boundaries

**BLOCKER.** No unresolved defect was found that invalidates the experimental claims in [the claim table](SCIENTIFIC_CLAIMS.md).

**REQUIRED CAVEAT.** Name each native series and revision, report the uncertainty and identify the timing unit. Distinguish primitive throughput from whole-operation latency. RSS includes the process and libraries. Report the original SQIsign categories as upstream targets. State the additional hash and stream assumptions, dependence on fresh operating-system entropy, deterministic seed reuse, compromise consequences, counter cap, high-level retry limitation and table-based backend leakage. Report Hypericum with its own parameter labels and usage budgets.

**OPTIONAL or outside the experimental scope.**

- [ ] Generalize performance to other machines, benchmark Hypericum on a matched host, or measure algorithm-specific memory peaks.
- [ ] Establish a formal reduction for the concrete composition, quantify leakage on deployment hardware, or prove high-level sampler termination on artificial exhaustion.
- [ ] Establish assurance for production or regulated deployment. The present evidence supports a research prototype.

**Integration.** The authors may review the freeze PR and PR 1 independently. Recheck both heads before integration. Proposed tag after approval: `sqisign-v3-ru-research-2026-11-21`. Creating the tag and merging are separate maintainer decisions.

**READY FOR MANUSCRIPT.** The evidence and limits for this decision are listed in the [validation report](FINAL_RESEARCH_VALIDATION.md).
