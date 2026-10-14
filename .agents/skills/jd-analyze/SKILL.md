---
name: jd-analyze
description: Analyze a JD's mission, role context, hiring intent, and requirement importance with source links.
---

# JD Analyze

Input: extracted JD items or locatable original text. Output: mission, hiring intent, role context, and complete analyzed requirements under the [analysis contract](schemas/analysis.schema.json).

Read [importance definitions](../career-decision/references/hiring-priority.md) and [provenance](../career-decision/references/source-contract.md). Give each requirement a stable requirement_id, kind, original jd_item_ids, source links, exact quote, importance, and reason. Cover responsibilities, qualifications, scope, and employment conditions. Split independent capability/condition components without losing their original-item link.

Describe industry, business scenario, responsibility type, decision rights, accountability, and people management using the [role-context definitions](references/role-context.md). Keep this context separate from requirement counts.

Critical needs an explicit gate or a reason it is indispensable to the stated mission. A Requirements heading does not make every item equally important. Optional needs supporting preferred/bonus wording; insufficient evidence means Unclear. Do not judge the candidate here.

Use kind capability or condition; conditions include role scope and employment terms. Explain hiring intent as Supported Inference or Hypothesis unless explicitly stated. A roadmap responsibility cannot establish new headcount, approved budget, or company strategy. Retain decision-changing unknowns for downstream analysis; do not investigate the company in this module.
