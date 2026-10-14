---
name: resume-review
description: Review actual resume text against Evidence for factual support, metric scope, timeline, JD alignment, and text structure.
---

# Resume Review

Input: actual resume text, one [Evidence document](../resume-intake/references/output-contract.md), and optionally a JD. Output: the [review schema](schemas/review.schema.json) and readable issues.

Review the text itself, not only proposed changes. Cover every nonempty line with original text, line number, concrete Evidence/Profile references, input hashes, classification, and reason. Headings without factual claims are Not a claim. Check personal responsibility, metric type/scope, dates, roles, and education; an existing reference does not prove semantic support.

Distinguish Full resume from Excerpt. Supported requires specifically approved facts. Pending facts allow Preliminary comparison but cannot support a formal Pass. Use Revise for required changes and Insufficient Evidence for unsupported claims. Transferable ability must not become direct experience; targets must not become achieved results.

Without a JD, set jd_alignment to Not assessed. With a JD, distinguish weak presentation, real gaps, and unknowns against important requirements. Check clarity, repetition, and emphasis; this module does not assess PDF/Word visual layout or approve an application decision.

Use [review-check](../resume-intake/scripts/evidence_tools.py) for line coverage, references, snapshots, and status constraints. Disclose checks not executed and separate technical validation, semantic review, fact confirmation, and user acceptance.
