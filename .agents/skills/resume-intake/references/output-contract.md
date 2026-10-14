# Evidence Output Contract

Maintain one authoritative Evidence document. The caller supplies locations. Derived views and immutable source/run archives are not separate editable fact stores. Full types are in [evidence.schema.json](../schemas/evidence.schema.json).

## Contents

- **profile:** identity, education, employment intervals, original skill declarations, and learning practice. Missing fields/dates remain null; preserve "present" wording without inventing an end month. Do not double-count overlapping employment.
- **sources:** actual originals, source nature, hashes, complete text, and locatable source units. Source IDs and record paths are not formal Evidence IDs.
- **evidence:** complete checkable contributions with role_ref, responsibility_scope, STAR, metrics, source_unit_id, review, evidence_id, id_approval_ref, case_refs, and unknowns. Responsibility, depth, and scope inform fit; titles and keywords do not prove them.
- **cases:** sourced event context linked through evidence_refs. Reference existing actions/results instead of duplicating them; new context requires its own source.
- **metadata:** schema_version, revision, updated_at, and limitations. JD-specific judgments are outputs, not permanent personal attributes.

## STAR and Metrics

Situation records stated context and initial conditions. Task records personal responsibility and acceptance targets. Action records actual methods/actions/collaboration. Result records supported outputs, adoption, or outcomes. Each dimension has statements, metric_refs, and unknowns. STAR organization is an interpretation and does not approve facts.

Do not move targets into achieved results, treat responsibility as implementation, or turn coverage into quality improvement. Metrics preserve original text, value/comparator/unit, object/scope, target/result nature, deadline, and before/after values. Keep approximations, bounds, denominator, and measurement scope; unmeasured outcomes remain Unknown.

## Review and References

Source nature and review.status (pending/approved/retired) are separate. Pending facts support explicitly limited Preliminary comparison. Personal fact support needs specific approval; approved self-report is not independent employer verification.

Keep evidence_id null until explicit ID approval. Formal IDs need id_approval_ref; facts need review.approval_ref. Record paths plus version/hash locate pending facts but are not stable cross-version IDs. Never fabricate approval records or silently alter historical references.

Classify conclusions as Verified Fact, Supported Inference, Hypothesis, or Unknown. A valid reference does not establish semantic support. Missing information is not a Gap, and skill declarations do not establish Strong hands-on fit.

## Validation Limits

[evidence_tools.py](../scripts/evidence_tools.py) uses PyYAML/jsonschema to check supported structure, source/hash/text location, roles/dates, metric bounds, references, and pending restrictions. Its check/view/render commands belong to intake; legacy match-check/review-check additionally use consumer schemas. It does not authenticate the approving person, compare all revisions, perform semantic deduplication, or prove arbitrary language entailment/business impact.

The current schema binds each contribution's STAR to a primary source paragraph. Cases can add separately sourced context. Multi-paragraph STAR fusion or formal ID replacement lineage needs a separately approved contract; do not force it into current fields. Disclose unsupported or unexecuted checks.
