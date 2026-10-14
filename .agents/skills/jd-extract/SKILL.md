---
name: jd-extract
description: Extract complete JD text from screenshots or documents, preserving wording, source anchors, overlap, and unreadable regions.
---

# JD Extract

Input: actual JD images or text. Output: JSON following the [JD schema](../career-decision/schemas/jd.schema.json), with original sources and extraction limitations.

Read [extraction rules](../career-decision/references/jd-extraction.md). Inspect every image. Capture visible company/title, duties, qualifications, employment terms, compensation, benefits, and other conditions. Preserve original language and wording; exclude platform controls and unrelated overlays.

Each item retains jd_item_id, exact_text, source_ids, section, uncertainty, and source-specific location anchors. Merge overlapping duplicates while retaining supported source links. A cropped image does not support words visible only in a complete image. Never reconstruct hidden text from a typical JD.

Use Complete, Partial, or Unreadable per image with issues and unreadable_regions. Missing company/title is Unknown. Record uncertain symbols or cut-off text locally. Python may validate structure, but does not perform semantic image reading. If image reading is unavailable, report the extraction gap and request text. Do not assign fit or application priority here.
