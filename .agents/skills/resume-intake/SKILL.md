---
name: resume-intake
description: Extract a real resume into traceable personal Evidence with profile, STAR contributions, responsibility, metrics, and review status.
---

# Resume Intake

Input: actual resume, optionally existing Evidence. Output: one candidate Evidence document under the [output contract](references/output-contract.md) and [schema](schemas/evidence.schema.json), plus omissions and review questions. The caller supplies data/output locations.

Read all discernible content, preserve original text and locations, and mark unreadable areas. For PDF, use available extraction and page-level visual checks. Do not fill personal facts from examples or previous analyses.

Organize complete, checkable contributions using STAR. Preserve personal responsibility, execution scope, metric bounds, and Unknowns. Separate skill declarations, learning exercises, and demonstrated work. A job title or tool name does not establish hands-on implementation.

Keep extracted facts pending and formal evidence_id null. If Evidence already exists, compare duplicates/conflicts and produce a candidate proposal instead of overwriting it. Fact approval and ID approval are separate from intake permission.

Use [evidence_tools.py](scripts/evidence_tools.py) for supported structural, source, and metric checks. Report unavailable checks. Validation does not establish that an experience is true or that every semantic interpretation is correct.
