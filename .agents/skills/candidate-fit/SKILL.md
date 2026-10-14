---
name: candidate-fit
description: Compare JD requirements with personal Evidence, explaining capability fit, industry/scenario similarity, missing support, and resume priorities.
---

# Candidate Fit

Input: extracted JD, analyzed requirements, and one [Evidence document](../resume-intake/references/output-contract.md). Output: requirement-level matches under the current contract supplied by the caller or harness.

Read [fit definitions](../career-decision/references/candidate-fit.md). Compare actual work, personal responsibility, execution depth, and scope. Cover every capability requirement, retaining its ID, original quote, importance, and source links from JD analysis. Assess employment conditions separately; a contract term is not a skill Gap. Do not silently change requirement importance.

Use Strong, Transferable, Partial, Gap, or Unknown with a reason and missing dimensions. Assess direct_support and transfer_support independently under the [support rubric](references/support-rubric.md). Do not derive these fields from a previous Partial or Unknown label. Tool names, acceptance criteria, and product ownership do not prove personal technical implementation. Absence from a resume does not prove a Gap. Critical gaps cannot be offset by Optional strengths.

Compare industry and business scenario separately under the [context-fit definitions](references/context-fit.md), using the analyzed role context and actual Evidence. Keep these comparisons outside capability distributions.

Bind references to the Evidence version/hash and record paths. Keep unapproved formal IDs null. Preliminary results disclose pending/self-reported facts; Personal results use specifically approved facts. Fit judgments remain inferences.

Prioritize resume changes by requirement importance and available evidence. Separate weak presentation, actual gaps, and missing information; Need evidence must not generate a factual claim. The [legacy standalone match schema](schemas/match.schema.json) and [match-check helper](../resume-intake/scripts/evidence_tools.py) support item-based compatibility only; use the current pipeline validator for analysis-bound results.

For analyzed JD inputs, use the [requirement-match contract](schemas/requirement-match.schema.json). Keep authoritative requirement IDs and importance, and bind the analysis hash.
