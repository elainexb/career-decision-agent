# Career run contract

One Agent selects Skills. The harness stores immutable inputs and results, not another editable fact library. JSON hashes use UTF-8, sorted keys, compact separators and unescaped Unicode. Source hashes use original bytes. Use hashes returned by tools; do not invent them.

Submit artifact objects as JSON text. Obtain the relevant Skill context before each module. Dependencies may be submitted together or reused within the same run. Accepted artifacts cannot be overwritten; rejected attempts remain visible. Changed inputs or rules require a new run.

## JD workflow

1. `jd`: current extraction schema. Use input source IDs and original paths from context. Preserve all visible wording, including conditions. Mark uncertain regions; exclude UI overlays. Completeness is a visual review claim, not a schema guarantee.
2. `analysis`: current analysis schema. Every responsibility, requirement, preference and employment/compensation item must be referenced. Split compound capability/condition clauses into requirements as needed, retaining the **complete** original item quote in each split. `jd_text` is the full quotes joined with newline, in `jd_item_ids` order. Importance is authoritative for downstream matching. Unknown importance is `Unclear`; explain what would resolve it. Hiring motives are hypotheses or supported inferences unless explicitly stated.
3. `fit`: requirement-match schema. Cover each **capability requirement** exactly once, with `requirement_id`, full quote and unchanged importance/reason. Conditions belong to decision, not skill gaps. Use `/evidence/N` refs and the pinned Evidence hash. Positive fit needs actual contribution evidence; absence alone is Unknown, not Gap. Strong requires comparable work, responsibility and scope, with no missing dimensions. All fit classifications are inferences. Pending data permits Preliminary analysis only. Resume changes reference requirement IDs; unsupported wording stays empty.
4. `decision`: current decision schema. Bind JD, analysis, fit, Evidence and current preferences. Priority precedence: confirmed hard blocker -> Low Priority; otherwise decision-changing unknown -> Insufficient Information; otherwise Critical Gap -> Low Priority; otherwise High Priority gates or Selective. Preferences come from read-only `confirmed_preferences` in the runtime configuration (default empty). Model-supplied options must match. Each hard preference names explicit rejected `condition_ids`; all confirmed matching conditions must be retained as blockers. Configuration is operator-controlled, not a human identity authentication mechanism. Known external conditions must be explicit JD facts. Company risk remains Unknown in this offline profile. Missing public finances alone need not block an actionable decision. Cite requirements, JD items or Evidence record refs; references do not establish semantic entailment.

Get context again after each accepted stage to obtain canonical output hashes. `career_inspect_run` returns final state and paths. `validated_pending_review` means deterministic checks passed, not factual verification, semantic acceptance or application submission.

## Other workflows

- `proposal`: evidence-proposal schema for evidence-maintain or case-maintain. Inspect existing facts for duplicates/conflicts. Changes cite actual new input sources and existing targets where applicable. Save precise proposals and impacts; never apply changes, assign formal IDs or fabricate approval. Merge/split lineage and multi-source STAR changes remain proposals.
- `candidate_evidence`: existing Evidence schema, produced by resume-intake from actual input. All extracted facts and Profile stay pending; IDs and approval refs stay null. Save as a candidate artifact; canonical data stays unchanged. This POC checks schema, approval boundaries and input source hashes; full intake source/STAR semantic checks require the existing intake helper and review.
- `draft`: actual resume text requested by the caller, followed by `review`. Pending wording must be labelled preliminary. Do not edit the supplied resume. `review` uses the existing review schema and covers every nonblank line of the actual saved draft or sole input TXT. Respect the caller's Excerpt/Full resume scope. Without a JD, alignment is Not assessed. Pending facts cannot support a formal Pass. Visual PDF/Word layout is outside this version.

Inputs up to 20 MB; PDF up to 10 pages; full context up to the configured character limit. Oversized or unreadable inputs fail explicitly. PDF text and rendered page images are delivered together. This plugin is not an OS sandbox. No model API or generic file-write tool is implemented here.

## Context delivery

Matching, tailoring and review use a derived view of the same pinned Evidence: complete contributions, original primary quotes, STAR, responsibility, metrics, Profile and source metadata. Raw extraction arrays are not repeated. Only needed accepted artifacts are returned. Record paths still refer to the canonical snapshot, not view offsets. The response is limited to 85,000 characters to stay below the installed host's 100,000-character result spillover threshold. Over-limit contexts fail explicitly; this POC has no paging or arbitrary file-read fallback.

`hashes.preferences` is the canonical preferences hash for decision output. Unresolved or stale hard-preference condition IDs must be listed as material unknowns; they cannot silently disappear or become confirmed blockers. Rebinding is an operator review step.

## Readable support reports

Current fit version is requirement-match-0.3.0. candidate-fit separately assesses direct_support and transfer_support using its support rubric. Keep original requirement IDs and importance. Python groups/counts these assessments; it does not invent them. The overview includes Critical+Important capability IDs, counts Unresolved in its denominator and separately shows Critical. Optional, Unclear and employment conditions are outside that denominator and remain visible. Percentages never change decision precedence.

Completed JD runs generate report.html and a concise report.md. The HTML is offline and contains source/STAR details, no external requests. Main labels use analyzed interpretation, not the whole composite source quote. Unknown is not low ability; high transfer does not erase an unconfirmed requirement or formal gate. Historical reports remain immutable.

## Role context

Analysis jd-analysis-0.2.0 adds role_context (industry, business scenario, work nature, decision rights, accountability and separate people management). Fit requirement-match-0.3.0 adds context_fit for independent industry/scenario comparisons. Both use current source IDs/Evidence refs and existing hash bindings. Known context needs sources; Unknown target cannot establish known similarity. Owner types need rights and accountability; explicit people management needs explicit posting evidence. Validation checks bindings/consistency, not semantic entailment. These fields never enter capability counts or create hard preferences. Old artifacts stay immutable; revisions require a new run.
