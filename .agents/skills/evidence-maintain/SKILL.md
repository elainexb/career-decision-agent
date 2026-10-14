---
name: evidence-maintain
description: Inspect existing Evidence and propose factual revisions, duplicate resolution, or ID changes without modifying the authoritative data.
---

# Evidence Maintain

Input: one [Evidence document](../resume-intake/references/output-contract.md), actual supplementary materials, and a maintenance request. Output: a source-backed proposal and impact list under the caller's proposal contract. This version is proposal-only.

Read [maintenance rules](../career-decision/references/library-maintenance.md). Search existing Evidence, cases, and sources before proposing changes. Duplicate identity means the same real fact, responsibility, and scope. Different contributions in one project can remain separate; similar wording alone is not grounds to merge.

Display the exact change, supporting source, reason, baseline version/hash, affected cases/reports, conflicts, and proposed old-reference handling. Formal Evidence IDs require separate explicit approval and are never reused for another experience. Leave candidate facts pending; do not invent an approval record.

Do not modify the authoritative document, allocate formal IDs, or invoke legacy library apply tools. Formal commit, merge/split lineage, and transactions require a separately defined update contract. Use case-maintain for detailed STAR/event refinement rather than building a second fact store.

Use the [proposal contract](schemas/proposal.schema.json) for proposal-only harness runs.
