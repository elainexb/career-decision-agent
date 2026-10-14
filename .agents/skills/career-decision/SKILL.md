---
name: career-decision
description: Classify application priority from JD fit, employment conditions, company evidence, career goals, and material unknowns.
---

# Career Decision

Input: analyzed JD, requirement-level fit, explicitly supplied goals/constraints, and available company sources. Output: risks, 24–36-month career value, application priority, reasons, and next checks under the caller's current decision contract.

Read [provenance](references/source-contract.md), [decision policy](references/decision-policy.md), and [risk classification](references/risk-classification.md). Apply confirmed hard blockers, decision-changing unknowns, and decisive Critical gaps before considering other strengths. Use High Priority, Selective, Low Priority, or Insufficient Information; no opaque total score.

Use analyzed work nature/authority and the two context-fit comparisons when explaining adaptation, Ownership risk and career value. Do not regenerate these classifications, infer industry from AI, or favor owner roles over execution without an explicit goal. Context similarity cannot override decision gates.

For career value, read [growth criteria](references/career-growth.md). Tie opportunities to actual responsibilities and stated goals; identify ownership, budget, adoption, or team prerequisites. Do not promise promotion.

When company research is requested and available, read [research rules](references/company-research.md), resolve the actual employer, and cite dated sources. Otherwise label unverified company claims Unknown and state whether research was deferred or unavailable. JD terms establish what the posting says, not a verified employment contract. Outsourcing is a hard blocker only when both the condition and the user's constraint are confirmed.

Keep Verified Fact, Supported Inference, Hypothesis, and Unknown distinct. Reference exact JD items, analyzed requirement IDs, Evidence snapshots, and external sources. Validate against the supplied contract before rendering; legacy library/report validators do not validate current personal Evidence.

Use the [decision contract](schemas/decision.schema.json) for the current Evidence pipeline.
